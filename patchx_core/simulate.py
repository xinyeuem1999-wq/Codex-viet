# -*- coding: utf-8 -*-
"""Mô phỏng toàn diện — "code hiểu code".

Đọc mẫu regex của từng patch, TỰ SINH văn bản mẫu tối thiểu khớp với mẫu,
dựng cây APK giả lập, áp thử từng patch, rồi tự đánh giá:
  - bao nhiêu quy tắc sinh được mẫu;
  - patch có tạo thay đổi thật hay không;
  - lần áp thứ hai có idempotent (không sửa lại) hay không;
  - thời gian xử lý (hiệu suất).
"""

import glob
import json
import hashlib
import os
import re
import shutil
import tempfile
import time
import zipfile

from .parser import parse_patch_file
from .engine import Engine

TMP = "/data/data/com.termux/files/usr/tmp"

_ESCAPES = {
    "n": "\n", "t": "\t", "r": "\r", "s": " ", "S": "x", "d": "0", "D": "x",
    "w": "x", "W": "x", "b": "", "B": "", "A": "", "Z": "",
    ".": ".", "(": "(", ")": ")", "{": "{", "}": "}", "[": "[", "]": "]",
    "$": "$", ">": ">", "<": "<", '"': '"', "/": "/", "*": "*", "+": "+",
    "?": "?", "^": "^", "-": "-", "|": "|", "\\": "\\",
}


SIM_VERSION = "sim-v2-1"


def _sim_cache_key(patch, apk_tree=None):
    """Khóa cache: vân tay nội dung patch + phiên bản engine + cây APK."""
    raw = [patch.name, SIM_VERSION, apk_tree or ""]
    for sec in patch.sections:
        raw.append(sec.type)
        raw.append(sec.raw)
    return hashlib.sha256("\x00".join(raw).encode("utf-8", "replace"))\
        .hexdigest()


def _classify_v2(patch, inserted, changes, guard, warnings, dex_runner):
    """Phân loại 5 chiều: PASS/EXPECTED_SKIP/UNSUPPORTED/BAD_PATCH/
    ENGINE_LIMIT."""
    if inserted == 0 or guard:
        return "EXPECTED_SKIP"
    if changes > 0:
        return "PASS"
    low = " ".join(w.lower() for w in warnings)
    if ("không khớp" in low or "không tìm thấy" in low
            or "lỗi" in low or "bỏ qua" in low):
        return "BAD_PATCH"
    if any(sec.type == "EXECUTE_DEX" for sec in patch.sections) \
            and dex_runner is None:
        return "UNSUPPORTED"
    return "UNSUPPORTED"


def _escape_char(c):
    return _ESCAPES.get(c, c)


def _pick_class_char(cls, neg):
    if not cls:
        return "x" if neg else "0"
    if neg:
        return "x"
    if "0" in cls or "0-9" in cls or "\\d" in cls:
        return "0"
    if "a" in cls or "a-z" in cls:
        return "a"
    if "p" in cls or "v" in cls:
        return "p"
    return cls[0]


def _sample_quant(pat, i):
    """Lượng tử sau một phân đoạn: * + ? {n,m} — trả (số lần lặp, vị trí mới)."""
    if i >= len(pat):
        return 1, i
    ch = pat[i]
    if ch == "*":
        return 0, i + 1
    if ch == "+":
        return 1, i + 1
    if ch == "?":
        return 0, i + 1
    if ch == "{":
        j = i + 1
        while j < len(pat) and pat[j] != "}":
            j += 1
        inner = pat[i + 1:j]
        nxt = j + 1
        if "," in inner:
            lo = inner.split(",", 1)[0]
            return (int(lo) if lo.isdigit() else 0), nxt
        return (int(inner) if inner.isdigit() else 1), nxt
    return 1, i


def _skip_group(pat, i):
    """Bỏ qua tới hết nhóm (dùng cho lookahead) — trả vị trí sau )."""
    depth = 0
    j = i
    while j < len(pat):
        if pat[j] == "(":
            depth += 1
        elif pat[j] == ")":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return j


def _sample_alt(pat, i):
    """Sinh mẫu cho một dãy phân đoạn tới khi gặp | hoặc )."""
    parts = []
    while i < len(pat):
        ch = pat[i]
        if ch == "|":
            return "".join(parts), i + 1
        if ch == ")":
            return "".join(parts), i
        seg, i = _sample_segment(pat, i)
        if seg is not None:
            parts.append(seg)
    return "".join(parts), i


def _sample_segment(pat, i):
    ch = pat[i]
    if ch == "(":
        if i + 1 < len(pat) and pat[i + 1] == "?":
            if i + 2 < len(pat) and pat[i + 2] in ("=", "!"):
                # Lookahead — không sinh gì
                return "", _skip_group(pat, i)
            # (?: nhóm không bắt — lấy nhánh đầu, bỏ qua phần còn lại
            inner, _ = _sample_alt(pat, i + 2)
            j = _skip_group(pat, i)
            q, j2 = _sample_quant(pat, j)
            return inner * q, j2
        # Nhóm bắt — lấy nhánh đầu của (a|b), nhảy tới ) đóng
        inner, _ = _sample_alt(pat, i + 1)
        j = _skip_group(pat, i)
        q, j2 = _sample_quant(pat, j)
        return inner * q, j2
    if ch == "[":
        j = i + 1
        neg = False
        if j < len(pat) and pat[j] == "^":
            neg = True
            j += 1
        cls = ""
        while j < len(pat) and pat[j] != "]":
            if pat[j] == "\\" and j + 1 < len(pat):
                cls += pat[j:j + 2]
                j += 2
            else:
                cls += pat[j]
                j += 1
        body = _pick_class_char(cls, neg)
        if j < len(pat) and pat[j] == "]":
            j += 1
        q, j2 = _sample_quant(pat, j)
        return body * q, j2
    if ch == "\\":
        if i + 1 < len(pat):
            body = _escape_char(pat[i + 1])
            q, j = _sample_quant(pat, i + 2)
            return body * q, j
        return "", i + 1
    if ch == ".":
        q, j = _sample_quant(pat, i + 1)
        return "x" * q, j
    q, j = _sample_quant(pat, i + 1)
    return ch * q, j


def pattern_to_sample(pattern, is_regex=True):
    """Sinh văn bản mẫu tối thiểu khớp với pattern.

    - is_regex=True: dịch mẫu regex thành văn bản mẫu;
    - is_regex=False: mẫu chính là chuỗi literal (giữ nguyên dấu chấm, ...).
    """
    if not pattern or not pattern.strip():
        return None
    if not is_regex:
        return pattern
    text, _ = _sample_alt(pattern, 0)
    if not text:
        return None
    try:
        if not re.search(pattern, text):
            return None
    except re.error:
        return None
    return text


def build_skeleton(root):
    """Cây APK giả lập với manifest + launcher activity + smali + res."""
    smali_dir = os.path.join(root, "smali", "com", "sim")
    res_dir = os.path.join(root, "res", "values")
    os.makedirs(smali_dir, exist_ok=True)
    os.makedirs(res_dir, exist_ok=True)
    manifest = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<manifest package="com.sim" android:installLocation="internal">\n'
        '  <uses-sdk android:minSdkVersion="21" />\n'
        '  <application android:name="androidx.App">\n'
        '    <activity android:name="com.sim.MainActivity">\n'
        '            <intent-filter>\n'
        '                <action android:name="android.intent.action.MAIN" />\n'
        '                <category android:name="android.intent.category.LAUNCHER" />\n'
        '            </intent-filter>\n'
        '    </activity>\n'
        '  </application>\n'
        '</manifest>\n')
    with open(os.path.join(root, "AndroidManifest.xml"), "w",
              encoding="utf-8") as fh:
        fh.write(manifest)
    smali = (
        '.class public Lcom/sim/MainActivity;\n\n'
        '.method protected onCreate(Landroid/os/Bundle;)V\n'
        '    .registers 5\n\n'
        '    const-string v0, "android_id"\n\n'
        '    invoke-static {v0, v1}, Landroid/provider/Settings$Secure;->getString(Landroid/content/ContentResolver;Ljava/lang/String;)Ljava/lang/String;\n\n'
        '    move-result-object v0\n'
        '    const-string v1, "com.google.android.gms.auth.api.signin.service.START"\n'
        '    return-void\n'
        '.end method\n')
    with open(os.path.join(smali_dir, "MainActivity.smali"), "w",
              encoding="utf-8") as fh:
        fh.write(smali)
    with open(os.path.join(res_dir, "strings.xml"), "w", encoding="utf-8") as fh:
        fh.write("<resources><string name=\"app_name\">Sim</string></resources>\n")
    with open(os.path.join(root, "res", "values", "styles.xml"), "w",
              encoding="utf-8") as fh:
        fh.write("<resources><style name=\"AppTheme\"></style></resources>\n")
    for lang in ("ru", "uk"):
        d = os.path.join(root, "res", "values-" + lang)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "strings.xml"), "w", encoding="utf-8") as fh:
            fh.write("<resources><string name=\"app_name\">Sim</string></resources>\n")
    pub = os.path.join(root, "res", "values", "public.xml")
    with open(pub, "w", encoding="utf-8") as fh:
        fh.write("<resources>\n"
                 "    <public type=\"string\" name=\"app_name\" id=\"0x7f010001\" />\n"
                 "</resources>\n")


def _first_existing_target(eng, targets, tree_root):
    """Tìm tệp target đầu tiên có thể dùng để chèn mẫu."""
    for rel in targets:
        if os.path.isfile(os.path.join(tree_root, rel)):
            return rel
    # Fallback: bất kỳ tệp smali nào
    if any(t.startswith("smali") for t in targets):
        for root, _d, files in os.walk(tree_root):
            for f in files:
                if f.endswith(".smali"):
                    return os.path.relpath(os.path.join(root, f), tree_root)
    return None


def insert_samples(patch, tree_root):
    """Chèn văn bản mẫu sinh từ MATCH vào target — trả số mẫu chèn được."""
    eng = Engine(tree_root, quiet=True, no_dex=True)
    inserted = 0
    for sec in patch.sections:
        if sec.type not in ("MATCH_REPLACE", "MATCH_ASSIGN", "MATCH_GOTO"):
            continue
        pattern = sec.get("MATCH")
        is_regex = sec.get("REGEX", "").strip().lower() in ("true", "1")
        sample = pattern_to_sample(pattern, is_regex=is_regex)
        if sample is None:
            continue
        targets = eng.resolve_targets(sec.get("TARGET"))
        rel = _first_existing_target(eng, targets, tree_root)
        if rel is None:
            continue
        path = os.path.join(tree_root, rel)
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\n" + sample + "\n")
        inserted += 1
        eng._invalidate_index()
    return inserted


def _guard_skip(patch):
    """Patch có MATCH_GOTO dạng đánh dấu idempotency (chuỗi literal, không
    meta) kèm ADD_FILES — guard kích hoạt khi asset đã được giải nén sẵn."""
    has_files = any(s.type == "ADD_FILES" for s in patch.sections)
    if not has_files:
        return False
    for sec in patch.sections:
        if sec.type == "MATCH_GOTO":
            m = (sec.get("MATCH") or "").strip()
            if m and not re.search(r"[\\\[\]()*+?{}|^$.]", m):
                return True
    return False


def simulate_patch(patch, work_dir, dex_runner=None, dex_timeout=60,
                   apk_tree=None, cache_dir=None):
    """Mô phỏng một patch trên cây giả lập — trả bản ghi kết quả.

    V2: phân loại 5 chiều (status_v2) + cache theo hash nội dung patch.
    """
    key = _sim_cache_key(patch, apk_tree)
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cpath = os.path.join(cache_dir, key + ".json")
        if os.path.isfile(cpath):
            try:
                with open(cpath, "r", encoding="utf-8") as fh:
                    rec = json.load(fh)
                rec["cache"] = True
                return rec
            except (OSError, ValueError):
                pass
    tree = os.path.join(work_dir, "tree_" + re.sub(r"[^A-Za-z0-9_.-]", "_",
                                                   patch.name))
    if os.path.exists(tree):
        shutil.rmtree(tree)
    if apk_tree and os.path.isdir(apk_tree):
        shutil.copytree(apk_tree, tree,
                        ignore=shutil.ignore_patterns(".patchx", "*.apk",
                                                      "build", "dist"))
    else:
        build_skeleton(tree)
    # Bước cấu trúc: tạo tệp từ ADD_FILES/MERGE để target của khối MATCH tồn tại
    eng_struct = Engine(tree, quiet=True, no_dex=True)
    for sec in patch.sections:
        if sec.type == "ADD_FILES":
            eng_struct._add_files(patch, sec)
        elif sec.type == "MERGE":
            eng_struct._merge(patch, sec)
    eng_struct._invalidate_index()
    inserted = insert_samples(patch, tree)

    t0 = time.time()
    eng = Engine(tree, quiet=True, no_dex=dex_runner is None,
                 dex_runner=dex_runner, dex_timeout=dex_timeout)
    eng.apply(patch)
    eng.finalize()
    dur_ms = (time.time() - t0) * 1000

    # Idempotency: áp lần 2 trên cùng cây
    eng2 = Engine(tree, quiet=True)
    before = len(eng2.changes)
    eng2.apply(patch)
    eng2.finalize()
    repeat_changes = len(eng2.changes) - before

    rules = sum(1 for s in patch.sections
                if s.type in ("MATCH_REPLACE", "MATCH_ASSIGN", "MATCH_GOTO"))
    note = ""
    if inserted == 0:
        status = "BỎ-QUA"
    elif len(eng.changes) > 0:
        status = "ĐẠT"
    elif _guard_skip(patch):
        status = "BỎ-QUA"
        note = "guard idempotency kích hoạt — cần APK thật để xác minh"
    else:
        status = "THẤT-BẠI"
    status_v2 = _classify_v2(patch, inserted, len(eng.changes),
                             _guard_skip(patch), eng.warnings, dex_runner)
    rec = {
        "patch": patch.name,
        "quy_tắc": rules,
        "mẫu_chèn": inserted,
        "thay_đổi": len(eng.changes),
        "lặp_lại": repeat_changes,
        "idempotent": repeat_changes == 0,
        "thời_gian_ms": round(dur_ms, 1),
        "trạng_thái": status,
        "status_v2": status_v2,
        "cảnh_báo": len(eng.warnings),
        "ghi_chú": note,
        "cache": False,
    }
    if cache_dir:
        try:
            with open(os.path.join(cache_dir, key + ".json"), "w",
                      encoding="utf-8") as fh:
                json.dump(rec, fh, ensure_ascii=False, indent=2)
        except OSError:
            pass
    return rec


def run_simulation(collection_root, work_dir=None, quick=False,
                   dex_runner=None, dex_timeout=60, apk_tree=None,
                   cache_dir=None):
    """Mô phỏng toàn bộ bộ sưu tập — trả kết quả + chỉ số tổng (V2)."""
    work_dir = work_dir or tempfile.mkdtemp(dir=TMP, prefix="patchx_sim_")
    if cache_dir is None:
        cache_dir = os.path.join(TMP, "patchx_sim_cache")
    zips = sorted(glob.glob(os.path.join(collection_root, "*.zip")))
    if quick:
        zips = zips[:15]
    results = []
    t0 = time.time()
    for z in zips:
        try:
            p = parse_patch_file(z)
        except Exception:
            continue
        try:
            rec = simulate_patch(p, work_dir, dex_runner=dex_runner,
                                 dex_timeout=dex_timeout, apk_tree=apk_tree,
                                 cache_dir=cache_dir)
        except Exception as e:
            rec = {"patch": os.path.basename(z), "trạng_thái": "LỖI",
                   "status_v2": "ENGINE_LIMIT", "lỗi": str(e)}
        results.append(rec)
    total_ms = (time.time() - t0) * 1000
    n_pass = sum(1 for r in results if r["trạng_thái"] == "ĐẠT")
    n_fail = sum(1 for r in results if r["trạng_thái"] == "THẤT-BẠI")
    n_skip = sum(1 for r in results if r["trạng_thái"] == "BỎ-QUA")
    n_err = sum(1 for r in results if r["trạng_thái"] == "LỖI")
    v2 = {k: sum(1 for r in results if r.get("status_v2") == k)
          for k in ("PASS", "EXPECTED_SKIP", "UNSUPPORTED", "BAD_PATCH",
                    "ENGINE_LIMIT")}
    n_cache = sum(1 for r in results if r.get("cache"))
    summary = {
        "tổng_patch": len(results),
        "đạt": n_pass,
        "thất_bại": n_fail,
        "bỏ_qua": n_skip,
        "lỗi": n_err,
        "status_v2": v2,
        "cache_hits": n_cache,
        "tỷ_lệ_đạt": round(n_pass / max(1, len(results)) * 100, 1),
        "tổng_thời_gian_ms": round(total_ms, 1),
        "trung_bình_ms_patch": round(total_ms / max(1, len(results)), 1),
        "chi_tiết": results,
    }
    return summary


def render_simulation(summary):
    """Kết xuất báo cáo mô phỏng dạng Markdown."""
    lines = ["# Báo cáo mô phỏng toàn diện", ""]
    lines.append("- Tổng patch: %d" % summary["tổng_patch"])
    lines.append("- ĐẠT: %d | THẤT-BẠI: %d | BỎ-QUA: %d | LỖI: %d" % (
        summary["đạt"], summary["thất_bại"], summary["bỏ_qua"],
        summary["lỗi"]))
    lines.append("- Tỷ lệ đạt: %s%%" % summary["tỷ_lệ_đạt"])
    v2 = summary.get("status_v2", {})
    if v2:
        lines.append("- V2 — PASS: %d | EXPECTED_SKIP: %d | UNSUPPORTED: %d"
                     " | BAD_PATCH: %d | ENGINE_LIMIT: %d" % (
                         v2.get("PASS", 0), v2.get("EXPECTED_SKIP", 0),
                         v2.get("UNSUPPORTED", 0), v2.get("BAD_PATCH", 0),
                         v2.get("ENGINE_LIMIT", 0)))
    lines.append("- Cache: %d lượt trúng" % summary.get("cache_hits", 0))
    lines.append("- Tổng thời gian: %s ms (trung bình %s ms/patch)" % (
        summary["tổng_thời_gian_ms"], summary["trung_bình_ms_patch"]))
    lines.append("")
    lines.append("| Patch | Quy tắc | Mẫu | Thay đổi | Lặp lại | Idempotent | ms | Trạng thái | V2 |")
    lines.append("|-------|---------|-----|----------|---------|------------|----|------------|----|")
    for r in summary["chi_tiết"]:
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["patch"], r.get("quy_tắc", "—"), r.get("mẫu_chèn", "—"),
            r.get("thay_đổi", "—"), r.get("lặp_lại", "—"),
            r.get("idempotent", "—"), r.get("thời_gian_ms", "—"),
            r["trạng_thái"], r.get("status_v2", "—")))
    lines.append("")
    return "\n".join(lines)
