# -*- coding: utf-8 -*-
"""Thư viện tiện ích smali dùng chung cho patchx.

Mục đích: gom các thao tác smali lặp lại (tìm method, cấp thanh ghi an toàn,
tìm call-site, chèn invoke có kiểm tra kiểu) vào một nơi để các module khác
dùng chung, tránh sao chép logic.

Quy ước: bình luận và thông báo tiếng Việt; chuỗi smali/regex giữ nguyên gốc.
"""

import glob
import hashlib
import os
import re

# Biến thể boolean trong smali: 0x0/0x1, true/false, hoặc số nguyên 0/1
BOOL_LIT_RE = re.compile(r"\b(0x0[01]|0x[01]|true|false|[01])\b")

# Khối method smali: header + thân tới .end method
METHOD_RE = re.compile(
    r"(?m)^(\s*\.method[^\n]*?\s([A-Za-z_$<][A-Za-z0-9_$<>]*)"
    r"(\([^)]*\))[^\n]*)\n(.*?)^(\s*\.end method)",
    re.S)

# Kiểu tham số trong chữ ký smali: dùng để đếm số thanh ghi khi chuyển .locals
PARAM_TYPE_RE = re.compile(r"(\[*L[^;]*;|\[*[BCDFIJSZV])")

# Một lời gọi smali: invoke-... {registers}, Lclass;->method(...)ret
CALL_SITE_RE = re.compile(
    r"(?m)^(\s*)(invoke-(?:virtual|static|direct|super|interface|range|"
    r"custom))\s*\{([^}]*)\},\s*L([^;]+);->([^(\s]+)\(([^)]*)\)([^\n]*)")


def smali_escape(text):
    """Thoát chuỗi cho literal smali (dấu gạch chéo + nháy kép)."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def smali_quote(text):
    """Bọc chuỗi thành literal smali: "..." (đã thoát)."""
    return '"' + smali_escape(text) + '"'


def rewrite_bool(text, want_true):
    """Đổi mọi literal boolean trong vùng MATCH sang họ tương ứng với VALUE.

    0x0/0x1 giữ họ hex, 0/1 giữ họ số, true/false giữ họ từ khóa.
    """
    def repl(m):
        tok = m.group(0)
        if tok in ("0x0", "0x1"):
            return "0x1" if want_true else "0x0"
        if tok in ("1", "0"):
            return "1" if want_true else "0"
        return "true" if want_true else "false"

    return BOOL_LIT_RE.sub(repl, text)


def smali_class_descriptor(text):
    """Trích tên class từ khai báo .class — trả 'com/demo/Hook' hoặc None."""
    m = re.search(r"\.class\b[^\n]*?\bL([^;\s]+);", text)
    return m.group(1) if m else None


def smali_target_rel(tree_root, cls):
    """Đường dẫn tương đối cho class smali (Lcom/x/Y; -> smali/com/x/Y.smali).

    Ưu tiên thư mục smali* có sẵn (thường là smali/).
    """
    roots = sorted(glob.glob(os.path.join(tree_root, "smali*")))
    root = os.path.basename(roots[0]) if roots else "smali"
    return os.path.join(root, cls.replace(".", "/") + ".smali")


def find_method_block(text, method):
    """Tìm khối method theo tên — trả match của METHOD_RE hoặc None."""
    for m in METHOD_RE.finditer(text):
        if m.group(2) == method:
            return m
    return None


def first_instruction_pos(text, body_start, body_end):
    """Vị trí chèn an toàn trong thân method.

    Chèn ngay TRƯỚC lệnh đầu tiên, sau mọi directive .registers/.locals/
    .param/.annotation và chú thích.
    """
    body = text[body_start:body_end]
    m = re.search(r"(?m)^\s*[^.\s#]", body)
    return body_start + m.start() if m else body_end


def _param_count(sig, is_static):
    params = sig[sig.find("(") + 1:sig.rfind(")")]
    return len(PARAM_TYPE_RE.findall(params)) + (0 if is_static else 1)


# pX dùng làm thanh ghi: đứng sau khoảng trắng/{/phẩy, đứng trước khoảng
# trắng/,/}/:/] hoặc cuối dòng — tránh nhầm tên field Lcls;->p1:Z hay chuỗi.
PREG_RE = re.compile(r"(?<=[\s{,])p(\d+)(?=[\s,}\]:]|$)")


def rewrite_pregs(line, pregs):
    """Đổi pX thành vN tường minh theo bố cục thanh ghi GỐC (trước khi nâng
    .registers) — giữ nguyên ánh xạ của mọi lệnh hiện có khi thêm thanh ghi."""
    if not pregs:
        return line

    def repl(m):
        i = int(m.group(1))
        v = pregs.get(i)
        return "v%d" % v if v is not None else m.group(0)

    return PREG_RE.sub(repl, line)


def smali_alloc_temps(body, sig, is_static):
    """Cấp 2 thanh ghi tạm an toàn cho method smali.

    - .registers N  -> .registers N+2, dùng vN/vN+1 (cao nhất, không đụng).
    - .locals L     -> chuyển sang .registers L+P, dùng v(L+P)/v(L+P+1).
    Trả (dòng .registers mới, (v0, v1), match dòng cũ, bản đồ pX -> vN gốc)
    hoặc (None, None, None, None) khi không khai báo .registers/.locals.

    Quan trọng: nâng .registers làm DỊCH ánh xạ pX (pX = v(locals+X)) — phải
    viết lại pX thành vN tường minh theo bố cục gốc, nếu không pX trượt lên
    v16+ (vượt giới hạn opcode 4-bit) và đụng thanh ghi tạm mới.
    """
    m = re.search(r"^(\s*)\.registers\s+(\d+)(\s*)$", body, re.M)
    if m:
        n = int(m.group(2))
        p = _param_count(sig, is_static)
        pregs = {i: n - p + i for i in range(p)}
        return m.group(1) + ".registers %d" % (n + 2), (n, n + 1), m, pregs
    m = re.search(r"^(\s*)\.locals\s+(\d+)(\s*)$", body, re.M)
    if m:
        n = int(m.group(2))
        p = _param_count(sig, is_static)
        pregs = {i: n + i for i in range(p)}
        total = n + p
        return m.group(1) + ".registers %d" % (total + 2), \
            (total, total + 1), m, pregs
    return None, None, None, None


def find_call_sites(text, class_desc, method_name=None):
    """Tìm mọi call-site tới L<class>;->method(...).

    Trả danh sách dict gồm: start, end, line, registers, invoke_type, class,
    method, params, return_type.
    """
    out = []
    for m in CALL_SITE_RE.finditer(text):
        cls = m.group(4)
        method = m.group(5)
        if cls != class_desc:
            continue
        if method_name and method != method_name:
            continue
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        if line_end == -1:
            line_end = len(text)
        out.append({
            "start": m.start(),
            "end": m.end(),
            "line": text[line_start:line_end].rstrip("\r\n"),
            "registers": [r.strip() for r in m.group(3).split(",")
                          if r.strip()],
            "invoke_type": m.group(2),
            "class": cls,
            "method": method,
            "params": m.group(6),
            "return_type": m.group(7).strip(),
        })
    return out


def insert_invoke(method_text, method_name, lines, marker=None):
    """Chèn các dòng smali vào đầu thân method (sau mọi directive).

    Idempotent theo marker. Trả (new_text, ok).
    """
    if marker and marker in method_text:
        return method_text, False
    m = find_method_block(method_text, method_name)
    if not m:
        return method_text, False
    pos = first_instruction_pos(method_text, m.start(4), m.end(4))
    block = ""
    if marker:
        block += "    " + marker + "\n"
    block += "\n".join("    " + ln if ln.strip() else ln
                       for ln in lines) + "\n"
    return method_text[:pos] + block + method_text[pos:], True


def marker_for(prefix, payload):
    """Sinh marker ổn định cho idempotency."""
    return "# " + prefix + ":" + hashlib.sha1(
        payload.encode("utf-8")).hexdigest()[:12]


def modern_class_kind(descriptor):
    """Nhận diện lớp theo đầu ra D8/R8 (trục T6):
    - R$...    : lớp tài nguyên nội bộ (resource inner class)
    - -$$Lambda$... : lambda được R8 sinh
    - Lambda$...     : lambda (dex)
    - *$...     : lớp nội bộ thường
    Trả (loại, phần_mô_tả)."""
    desc = (descriptor or "").strip()
    if desc.startswith("L") and desc.endswith(";"):
        desc = desc[1:-1]
    name = desc.rsplit("/", 1)[-1]
    if name.startswith("R$") or name == "R":
        return "R-inner", name
    if "-$$Lambda$" in name or name.startswith("$$Lambda"):
        return "lambda-r8", name
    if "Lambda$" in name or "lambda$" in name:
        return "lambda", name
    if "Metadata" in name:
        return "kotlin-metadata", name
    if "$" in name:
        return "inner", name
    return "thường", name


def kotlin_metadata_present(smali_text):
    """Kiểm tra dấu hiệu Kotlin (metadata annotation) trong file smali."""
    return ("Lkotlin/Metadata;" in (smali_text or "")
            or "Lkotlin/jvm/internal/" in (smali_text or ""))


def unicode_safe_patch_name(name):
    """Tên patch nhiều ngôn ngữ (Nga/Trung/...) — giữ nguyên UTF-8, chỉ
    chuẩn hoá ký tự không an toàn cho tên tệp (trục T6)."""
    import re as _re
    safe = _re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name or "")
    return safe.strip() or "patch"


# Bí danh dấu gạch dưới để tương thích với engine cũ.
_smali_escape = smali_escape
_smali_quote = smali_quote
_rewrite_bool = rewrite_bool
_smali_class_descriptor = smali_class_descriptor
_smali_target_rel = smali_target_rel
_find_method_block = find_method_block
_first_instruction_pos = first_instruction_pos
_smali_alloc_temps = smali_alloc_temps
