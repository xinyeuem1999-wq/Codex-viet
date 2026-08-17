# -*- coding: utf-8 -*-
"""Phân tích ngữ nghĩa smali (trục T1 — từ khớp chuỗi sang hiểu code).

Gồm: parser method-level, coverage theo method, nhận diện packer, phát hiện
nghi mã hóa chuỗi, và call-graph từ entry (launcher/application) để xếp hạng
target thật sự được gọi.
"""

import os
import re
import hashlib
from collections import defaultdict, deque


def extract_methods(smali_text):
    """Tách các khối `.method ... .end method` trong một file smali.

    Trả list dict: name, signature, body, line (số dòng bắt đầu).
    """
    methods = []
    lines = smali_text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.lstrip().startswith(".method"):
            start = i
            sig = line.strip()
            j = i + 1
            while j < n and not lines[j].lstrip().startswith(".end method"):
                j += 1
            body = "\n".join(lines[i + 1:j])
            name = ""
            m = re.search(r"\.method(?:\s+\w+)*\s+([^\s(]+)", sig)
            if m:
                name = m.group(1)
            methods.append({"name": name, "signature": sig, "body": body,
                            "line": start + 1})
            i = j + 1
        else:
            i += 1
    return methods


def find_method_matches(smali_text, pattern, is_regex):
    """Tìm method nào chứa pattern — trả list dict {method, lần}.

    pattern là chuỗi (literal hoặc regex) như trong khối MATCH_*.
    """
    if not pattern:
        return []
    if is_regex:
        try:
            rx = re.compile(pattern)
        except re.error:
            rx = None
    out = []
    for meth in extract_methods(smali_text):
        if is_regex:
            if rx is None:
                continue
            hits = len(rx.findall(meth["body"]))
        else:
            hits = meth["body"].count(pattern)
        if hits:
            out.append({"method": meth["name"], "signature": meth["signature"],
                        "line": meth["line"], "lần": hits})
    return out


PACKER_LIBS = [
    ("libjiagu.so", "jiagu/360"),
    ("libDexHelper.so", "jiagu/360 (DexHelper)"),
    ("libshell*.so", "bangcle"),
    ("libprotect*.so", "bangcle"),
    ("libtprt.so", "tencent"),
    ("libnesec.so", "tencent"),
    ("libmobisec*.so", "tencent"),
    ("libexec*.so", "tencent"),
    ("libnqshield.so", "netqin"),
    ("libsecexe.so", "ali"),
    ("libsgmain.so", "ali"),
    ("libaliprotect.so", "ali"),
    ("libtosprotection.so", "bytedance"),
    ("libmsaoaidsec.so", "baidu"),
    ("libbaiduprotect.so", "baidu"),
    ("libegis.so", "netease/egis"),
    ("libnesec*.so", "tencent/nesec"),
]

PACKER_SMALI_HINTS = [
    ("Lcom/qihoo/util/", "360 jiagu"),
    ("Lcom/qihoo360/", "360 jiagu"),
    ("Lcom/secneo/", "secneo/360"),
    ("Lcom/tencent/stub/", "tencent stub"),
    ("Lcom/tencent/mobisec/", "tencent mobisec"),
    ("Lcom/bangcle/", "bangcle"),
    ("Lcom/baidu/protect/", "baidu protect"),
    ("Lcom/aliyun/security/", "ali yun security"),
    ("Lcom/sijla/", "sijla/jiagu"),
]


def detect_packers(tree):
    """Quét lib/*.so và smali tìm dấu hiệu packer — trả list dict."""
    found = []
    lib_dir = os.path.join(tree, "lib")
    if os.path.isdir(lib_dir):
        for root, _dirs, files in os.walk(lib_dir):
            for fname in files:
                if not fname.endswith(".so"):
                    continue
                for pat, name in PACKER_LIBS:
                    if re.fullmatch(pat.replace("*", ".*"), fname):
                        found.append({"loại": "lib", "tệp": fname,
                                      "nghi_ngờ": name,
                                      "đường_dẫn": os.path.relpath(
                                          os.path.join(root, fname), tree)})
    smali_dirs = [os.path.join(tree, "smali")]
    if not os.path.isdir(smali_dirs[0]):
        smali_dirs = []
    for d in list(smali_dirs):
        if not os.path.isdir(d):
            smali_dirs.remove(d)
    if smali_dirs:
        for root, _dirs, files in os.walk(smali_dirs[0]):
            for fname in files:
                if not fname.endswith(".smali"):
                    continue
                path = os.path.join(root, fname)
                try:
                    text = open(path, encoding="utf-8",
                                errors="replace").read()
                except OSError:
                    continue
                for hint, name in PACKER_SMALI_HINTS:
                    if hint in text:
                        found.append({"loại": "smali", "tệp": fname,
                                      "nghi_ngờ": name,
                                      "đường_dẫn": os.path.relpath(
                                          path, tree)})
    # Gộp trùng theo (loại, tệp, nghi_ngờ)
    seen = set()
    uniq = []
    for f in found:
        key = (f["loại"], f["tệp"], f["nghi_ngờ"])
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return uniq


def detect_string_encryption(tree, limit=10):
    """Heuristic phát hiện nghi mã hóa chuỗi trong smali.

    Dấu hiệu: chuỗi base64 dài / chuỗi \\uXXXX dồn dập; lời gọi method tên
    gợi ý giải mã (decrypt/decode/aes/rc4/base64/...). Trả list dict.
    """
    suspects = []
    base64_re = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")
    unicode_run_re = re.compile(r"(?:\\u[0-9a-fA-F]{4}){4,}")
    crypt_names = re.compile(
        r"(?i)\b(decrypt|encode|decode|aes|rc4|des|base64|unpack|"
        r"deobfuscate|getstring|frombytes)\b")
    smali_dir = os.path.join(tree, "smali")
    if not os.path.isdir(smali_dir):
        return []
    counted = 0
    for root, _dirs, files in os.walk(smali_dir):
        for fname in files:
            if not fname.endswith(".smali"):
                continue
            path = os.path.join(root, fname)
            try:
                text = open(path, encoding="utf-8",
                            errors="replace").read()
            except OSError:
                continue
            b64 = len(base64_re.findall(text))
            unir = len(unicode_run_re.findall(text))
            crypt = len(crypt_names.findall(text))
            score = b64 * 2 + unir * 2 + (1 if crypt else 0)
            if score >= 3:
                suspects.append({
                    "tệp": os.path.relpath(path, tree),
                    "điểm": score, "chuỗi_base64_dài": b64,
                    "chuỗi_unicode_dồn": unir, "lời_gọi_giải_mã": crypt})
                counted += 1
                if counted >= limit:
                    break
        if counted >= limit:
            break
    suspects.sort(key=lambda x: -x["điểm"])
    return suspects


def _resolve_class(name, package):
    """Tên class trong manifest có thể dạng `.Main` → package.Main."""
    name = (name or "").strip()
    if not name:
        return ""
    if name.startswith("."):
        return (package + name).lstrip(".")
    if "." not in name:
        return (package + "." + name).lstrip(".")
    return name


def entry_classes(tree):
    """Đọc AndroidManifest.xml (đã decode text) — trả (application, launchers)."""
    man_path = os.path.join(tree, "AndroidManifest.xml")
    if not os.path.isfile(man_path):
        return "", []
    try:
        text = open(man_path, encoding="utf-8", errors="replace").read()
    except OSError:
        return "", []
    pkg = ""
    m = re.search(r'package="([^"]+)"', text)
    if m:
        pkg = m.group(1)
    app = ""
    m = re.search(r"<application[^>]*\bname=\"([^\"]+)\"", text)
    if m:
        app = _resolve_class(m.group(1), pkg)
    launchers = []
    # Khối activity + intent-filter MAIN/LAUNCHER
    for block in re.finditer(
            r"<activity\b([^>]*?)(?:/>|>.*?</activity>)", text, re.S):
        body = block.group(0)
        if ("android.intent.action.MAIN" in body
                and "android.intent.category.LAUNCHER" in body):
            m = re.search(r'<activity\b[^>]*\bname="([^"]+)"', body)
            if m:
                launchers.append(_resolve_class(m.group(1), pkg))
    return app, launchers


INVOKE_RE = re.compile(
    r"\binvoke-(?:virtual|super|direct|static|interface|range|"
    r"virtual/range|super/range|direct/range|static/range|"
    r"interface/range)\s*\{[^}]*\},\s*(L[^;]+;)->")

# Giữ đủ chữ ký lời gọi để mô hình không phải suy luận từ tên tệp.  Biểu thức
# này cố ý không dùng tên method để tạo dấu vân tay: R8/ProGuard thường chỉ
# đổi tên, còn kiểu, cấu trúc lệnh và quan hệ gọi vẫn là bằng chứng hữu ích.
INVOKE_FULL_RE = re.compile(
    r"\binvoke-[^\s]+\s*\{(?P<registers>[^}]*)\},\s*"
    r"(?P<target>L[^;]+;->[^\s(]+\([^)]*\)[^\s]+)")
_CLASS_RE = re.compile(r"^\.class\s+.+?\s+(L[^;]+;)", re.M)
_FIELD_READ_RE = re.compile(r"\b(?:sget|iget)(?:-[\w/]+)?\s+[^,]+(?:,\s*[^,]+)?,\s*(L[^;]+;->[^\s]+)")
_FIELD_WRITE_RE = re.compile(r"\b(?:sput|iput)(?:-[\w/]+)?\s+[^,]+(?:,\s*[^,]+)?,\s*(L[^;]+;->[^\s]+)")
_STRING_RE = re.compile(r'\bconst-string(?:/jumbo)?\s+[^,]+,\s+"((?:\\.|[^"\\])*)"')


def _method_types(signature):
    """Trả kiểu tham số và kiểu trả về từ dòng .method.

    Đây là parser DEX nhỏ, đủ cho descriptor smali; nó không phụ thuộc tên
    method nên an toàn khi code bị obfuscate.
    """
    m = re.search(r"\(([^)]*)\)(\S+)", signature)
    if not m:
        return [], ""
    raw = m.group(1)
    params = []
    i = 0
    while i < len(raw):
        start = i
        while i < len(raw) and raw[i] == '[':
            i += 1
        if i < len(raw) and raw[i] == 'L':
            end = raw.find(';', i)
            i = len(raw) if end < 0 else end + 1
        else:
            i += 1
        params.append(raw[start:i])
    return params, m.group(2)


def method_fingerprint(method):
    """Dấu vân tay hành vi ổn định trước việc đổi tên lớp/phương thức.

    Nó không khẳng định hai method cùng ý nghĩa; nó cung cấp bằng chứng cấu
    trúc để tầng nhận diện xếp hạng và bắt buộc preflight xác minh thêm.
    """
    params, ret = _method_types(method["signature"])
    ops = []
    for raw in method["body"].splitlines():
        line = raw.strip()
        if not line or line.startswith((".", ":", "#")):
            continue
        # invoke-* và const-* được chuẩn hóa theo họ lệnh, không chứa tên.
        op = line.split(None, 1)[0]
        ops.append(op.split("/", 1)[0])
    calls = [x.group("target").split("->", 1)[1]
             for x in INVOKE_FULL_RE.finditer(method["body"])]
    payload = {
        "params": params, "return": ret, "ops": ops,
        "branches": sum(1 for op in ops if op.startswith("if-")),
        "calls": sorted(calls),
        "strings": sorted(_STRING_RE.findall(method["body"])),
    }
    canonical = repr(payload).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:24]


def build_app_model(tree, include_bodies=False):
    """Xây mô hình trung gian của APK từ tất cả thư mục smali.

    Mô hình tách nhận diện khỏi thay đổi: mỗi method có cấu trúc, dấu vân tay,
    cạnh gọi, nguồn/đích dữ liệu sơ bộ và điểm quyết định. Không có thao tác
    ghi nào lên cây APK.
    """
    methods = []
    callers = defaultdict(list)
    for root in _smali_roots(tree):
        for base, _dirs, files in os.walk(root):
            for fname in sorted(files):
                if not fname.endswith(".smali"):
                    continue
                path = os.path.join(base, fname)
                try:
                    text = open(path, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                cm = _CLASS_RE.search(text)
                cls = cm.group(1) if cm else ""
                rel = os.path.relpath(path, tree)
                for meth in extract_methods(text):
                    params, ret = _method_types(meth["signature"])
                    calls = [m.group("target") for m in INVOKE_FULL_RE.finditer(meth["body"])]
                    reads = _FIELD_READ_RE.findall(meth["body"])
                    writes = _FIELD_WRITE_RE.findall(meth["body"])
                    branches = sum(1 for line in meth["body"].splitlines()
                                   if line.strip().startswith("if-"))
                    key = "%s->%s" % (cls, re.search(r"([^\s(]+\([^)]*\)\S+)", meth["signature"]).group(1)) if cls and re.search(r"([^\s(]+\([^)]*\)\S+)", meth["signature"]) else "%s:%d" % (rel, meth["line"])
                    record = {
                        "id": key, "class": cls, "file": rel,
                        "line": meth["line"], "signature": meth["signature"],
                        "parameters": params, "return_type": ret,
                        "fingerprint": method_fingerprint(meth),
                        "calls": calls, "field_reads": reads,
                        "field_writes": writes, "strings": _STRING_RE.findall(meth["body"]),
                        "branch_count": branches,
                        "decision_point": ret == "Z" or branches > 0,
                    }
                    if include_bodies:
                        record["body"] = meth["body"]
                    methods.append(record)
                    for target in calls:
                        callers[target].append(key)
    for method in methods:
        method["called_by"] = sorted(callers.get(method["id"], []))
        # Luồng dữ liệu mức bảo thủ: nguồn và sink được ghi riêng, không tự
        # suy diễn def-use liên method khi chưa có chứng cứ register đầy đủ.
        method["data_flow"] = {
            "sources": ([{"type": "field_read", "value": x} for x in method["field_reads"]] +
                        [{"type": "constant_string", "value": x} for x in method["strings"]]),
            "sinks": [{"type": "invoke", "value": x} for x in method["calls"]],
        }
    edges = [{"from": m["id"], "to": target}
             for m in methods for target in m["calls"]]
    return {
        "schema": "patchx.app-model/v1", "tree": os.path.abspath(tree),
        "smali_roots": [os.path.relpath(p, tree) for p in _smali_roots(tree)],
        "methods": methods, "call_edges": edges,
        "summary": {"methods": len(methods), "call_edges": len(edges),
                    "decision_points": sum(1 for m in methods if m["decision_point"]),
                    "data_sources": sum(len(m["data_flow"]["sources"]) for m in methods)},
    }


def _normalized_method_body(body):
    """Chuẩn hóa thân method cho identity exact có thể tái lập.

    Bỏ metadata/debug và khoảng trắng không mang ngữ nghĩa; giữ nguyên operand
    để identity này chỉ dùng nhận diện thay đổi chính xác, không dùng ghép APK
    đã obfuscate.
    """
    lines = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ".line", ".local", ".param",
                                        ".prologue", ".epilogue")):
            continue
        lines.append(" ".join(line.split()))
    return "\n".join(lines)


def _sha24(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _descriptor_types(descriptor):
    """Tách tham số/return từ descriptor gọi method, không lấy tên method."""
    m = re.search(r"\(([^)]*)\)(\S+)$", descriptor or "")
    if not m:
        return [], ""
    return _method_types("(" + m.group(1) + ")" + m.group(2))


def _invoke_shape(target):
    """Đặc trưng lời gọi chịu được đổi tên class/method nội bộ.

    API nền tảng Android/Java được giữ class để tăng bằng chứng ngữ nghĩa;
    lời gọi app nội bộ chỉ giữ prototype. Đây là đặc trưng xếp hạng, không phải
    bằng chứng độc lập để thực thi thay đổi.
    """
    cls, _, member = (target or "").partition("->")
    params, ret = _descriptor_types(member)
    prefix = cls if cls.startswith(("Landroid/", "Ljava/", "Lkotlin/")) else "Lapp;"
    return "%s(%s)%s" % (prefix, "".join(params), ret)


def _opcode_histogram(body):
    hist = defaultdict(int)
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith((".", ":", "#")):
            continue
        op = line.split(None, 1)[0]
        hist[op.split("/", 1)[0]] += 1
    return dict(sorted(hist.items()))


def build_app_model_v2(tree, include_bodies=False):
    """Xây ``patchx.app-model/v2`` chỉ-đọc, song song model V1.

    V2 bổ sung ba identity (exact/structural/semantic), quan hệ caller/callee
    và khoảng cách ngắn nhất từ Application/launcher. Hàm không sửa cây APK,
    không tạo patch và không được dùng để gọi Engine.apply.
    """
    methods = []
    by_id = {}
    for root in _smali_roots(tree):
        for base, _dirs, files in os.walk(root):
            for fname in sorted(files):
                if not fname.endswith(".smali"):
                    continue
                path = os.path.join(base, fname)
                try:
                    text = open(path, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                cm = _CLASS_RE.search(text)
                cls = cm.group(1) if cm else ""
                rel = os.path.relpath(path, tree)
                for meth in extract_methods(text):
                    sig_match = re.search(r"([^\s(]+\([^)]*\)\S+)", meth["signature"])
                    method_sig = sig_match.group(1) if sig_match else ""
                    method_id = "%s->%s" % (cls, method_sig) if cls and method_sig else "%s:%d" % (rel, meth["line"])
                    params, ret = _method_types(meth["signature"])
                    calls = [m.group("target") for m in INVOKE_FULL_RE.finditer(meth["body"])]
                    reads = _FIELD_READ_RE.findall(meth["body"])
                    writes = _FIELD_WRITE_RE.findall(meth["body"])
                    strings = _STRING_RE.findall(meth["body"])
                    ops = _opcode_histogram(meth["body"])
                    branches = sum(v for op, v in ops.items() if op.startswith("if-"))
                    structural = {
                        "parameters": params, "return_type": ret,
                        "opcode_histogram": ops, "branch_count": branches,
                        "invoke_shapes": sorted(_invoke_shape(x) for x in calls),
                    }
                    semantic = {
                        "parameters": params, "return_type": ret,
                        "platform_calls": sorted(_invoke_shape(x) for x in calls
                                                 if x.startswith(("Landroid/", "Ljava/", "Lkotlin/"))),
                        "strings": sorted(strings),
                        "field_read_types": sorted(x.rsplit(":", 1)[-1] for x in reads),
                    }
                    record = {
                        "id": method_id, "class": cls, "file": rel,
                        "line": meth["line"], "signature": meth["signature"],
                        "features": {"return_type": ret, "parameters": params,
                                     "opcode_histogram": ops, "branch_count": branches,
                                     "strings": strings, "calls": calls,
                                     "field_reads": reads, "field_writes": writes},
                        "identity": {
                            "exact": _sha24(_normalized_method_body(meth["body"])),
                            "structural": _sha24(repr(structural)),
                            "semantic": _sha24(repr(semantic)),
                        },
                        "relations": {"callers": [], "callees": calls,
                                      "entry_distance": None},
                        "evidence": {"source_file": rel, "line": meth["line"],
                                     "extractor_version": "model/v2"},
                    }
                    if include_bodies:
                        record["body"] = meth["body"]
                    methods.append(record)
                    by_id[method_id] = record

    callers = defaultdict(list)
    edges = []
    for method in methods:
        for target in method["relations"]["callees"]:
            callers[target].append(method["id"])
            edges.append({"from": method["id"], "to": target})
    for method in methods:
        method["relations"]["callers"] = sorted(callers.get(method["id"], []))

    app, launchers = entry_classes(tree)
    entry_classes_desc = set()
    for name in [app] + launchers:
        if name:
            entry_classes_desc.add("L%s;" % name.replace(".", "/"))
    queue = deque((m["id"], 0) for m in methods if m["class"] in entry_classes_desc)
    visited = set()
    while queue:
        method_id, distance = queue.popleft()
        if method_id in visited:
            continue
        visited.add(method_id)
        method = by_id.get(method_id)
        if not method:
            continue
        method["relations"]["entry_distance"] = distance
        for target in method["relations"]["callees"]:
            if target in by_id and target not in visited:
                queue.append((target, distance + 1))

    return {
        "schema": "patchx.app-model/v2", "tree": os.path.abspath(tree),
        "smali_roots": [os.path.relpath(p, tree) for p in _smali_roots(tree)],
        "entry_classes": sorted(entry_classes_desc), "methods": methods,
        "call_edges": edges,
        "summary": {
            "methods": len(methods), "call_edges": len(edges),
            "reachable_from_entry": sum(1 for m in methods
                                        if m["relations"]["entry_distance"] is not None),
            "decision_points": sum(1 for m in methods
                                   if m["features"]["return_type"] == "Z"
                                   or m["features"]["branch_count"] > 0),
        },
    }


def call_graph_rank(tree, entries, depth=3, top=15):
    """Dựng call-graph từ các class entry — xếp hạng target được gọi.

    entries: list class descriptor dạng `Lcom/foo/Bar;`. Trả list dict
    {class, lần, độ_sâu} của các class trong cây được gọi từ entry.
    """
    def to_path(desc):
        return desc.strip("L;").replace("/", os.sep) + ".smali"

    entry_descs = []
    for e in entries:
        e = (e or "").strip()
        if not e:
            continue
        if e.startswith("L") and e.endswith(";"):
            entry_descs.append(e)
        else:
            entry_descs.append("L%s;" % e.replace(".", "/"))
    rank = defaultdict(int)
    queue = deque((d, 0) for d in entry_descs)
    visited = set()
    smali_dir = os.path.join(tree, "smali")
    file_cache = {}
    while queue:
        desc, d = queue.popleft()
        if d > depth or desc in visited:
            continue
        visited.add(desc)
        path = os.path.join(smali_dir, to_path(desc))
        if not os.path.isfile(path):
            # thử tìm đuôi .smali ở bất kỳ vị trí nào (cây smali_*)
            path = None
            for base in _smali_roots(tree):
                cand = os.path.join(base, to_path(desc))
                if os.path.isfile(cand):
                    path = cand
                    break
            if not path:
                continue
        if path not in file_cache:
            try:
                file_cache[path] = open(path, encoding="utf-8",
                                        errors="replace").read()
            except OSError:
                file_cache[path] = ""
        text = file_cache[path]
        for m in INVOKE_RE.finditer(text):
            target = m.group(1)
            if target in entry_descs or target in visited:
                continue
            rank[target] += 1
            queue.append((target, d + 1))
    ranked = [{"class": c, "lần": n}
              for c, n in sorted(rank.items(), key=lambda x: -x[1])]
    return ranked[:top]


def _smali_roots(tree):
    """Các thư mục chứa smali trong cây apktool (smali, smali_classes2, ...)."""
    roots = []
    try:
        for name in sorted(os.listdir(tree)):
            full = os.path.join(tree, name)
            if os.path.isdir(full) and (name == "smali"
                                        or name.startswith("smali_")):
                roots.append(full)
    except OSError:
        pass
    return roots


def method_coverage_for_file(smali_text, pattern, is_regex):
    """Bao quát theo method cho một pattern trên một file — tiện cho CLI."""
    return find_method_matches(smali_text, pattern, is_regex)


def build_semantic_report(tree, top=15):
    """Báo cáo ngữ nghĩa tổng hợp cho một cây APK đã giải mã."""
    app, launchers = entry_classes(tree)
    entries = [e for e in [app] + launchers if e]
    graph = call_graph_rank(tree, entries, depth=3, top=top)
    packers = detect_packers(tree)
    enc = detect_string_encryption(tree)
    return {
        "application": app,
        "launchers": launchers,
        "call_graph_top": graph,
        "packers": packers,
        "string_encryption_suspects": enc,
        "gợi_ý_điểm_chèn": (
            "Có packer — patch cần chèn trước khi pack (vd INIT/HOOK_SCRIPT "
            "vào Application#attachBaseContext) hoặc dùng hook tầng thấp." if
            packers else "Không phát hiện packer — chèn smali thông thường "
            "áp dụng được."),
    }
