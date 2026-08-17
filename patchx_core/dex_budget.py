# -*- coding: utf-8 -*-
"""P5 — DEX Resource Manager.

Ước lượng số method/field/class refs của cây APK đã giải mã (từ smali),
dự báo delta khi áp patch, và phân loại mức an toàn theo giới hạn 64K
của method_ids.

Mức: SAFE / WATCH / HIGH / CRITICAL / BLOCK.
"""

import os
import re
from concurrent.futures import ThreadPoolExecutor

DEX_METHOD_MAX = 65536  # giới hạn method_ids của một dex (64K)

_METHOD_DECL_RE = re.compile(r"^\.method\b[^\n]*", re.M)
_FIELD_DECL_RE = re.compile(r"^\.field\b[^\n]*", re.M)
_INVOKE_RE = re.compile(
    r"\binvoke-(?:static|virtual|direct|super|interface|"
    r"static/range|virtual/range|direct/range|super/range|"
    r"interface/range|polymorphic|polymorphic/range)"
    r"\s*\{[^}]*\},\s*(L[^;]+;)->", re.M)
_FIELD_REF_RE = re.compile(
    r"\b(?:s|i)(?:get|put)(?:-boolean|-byte|-char|-short|-int|-long|"
    r"-float|-double|-object|-wide)?\s+[vp\d]+,\s*(L[^;]+;)->", re.M)
_STRING_RE = re.compile(r"const-string(?:/jumbo)?\s+[vp\d]+,\s*\"", re.M)
_NEW_INSTANCE_RE = re.compile(r"new-instance\s+[vp\d]+,\s*(L[^;]+;)", re.M)

# Ước lượng delta method refs theo LOẠI khối patch (giá trị thận trọng)
BLOCK_DELTA_EST = {
    "TRACE": 2,          # Log.d + marker class
    "API_LOG": 2,
    "INIT": 2,           # invoke class helper
    "HOOK_SCRIPT": 3,    # class helper + invoke-static
    "REMOTE_CONFIG": 3,  # helper + init
    "EXECUTE_DEX": 10,   # không biết trước — mặc định thận trọng
    "MERGE": 5,
    "ADD_FILES": 5,
    "REPLACE_FILES": 2,
    "SET_BOOL": 0,       # chỉ sửa literal
    "MATCH_REPLACE": 0,
    "MATCH_ASSIGN": 0,
    "MATCH_GOTO": 0,
    "REMOVE_FILES": -1,  # xóa thường giảm refs
    "GOTO": 0,
    "DUMMY": 0,
    "MIN_ENGINE_VER": 0,
    "AUTHOR": 0,
    "PACKAGE": 0,
}


def _iter_smali(tree_root):
    for dirpath, _dirs, files in os.walk(tree_root):
        for fn in files:
            if fn.endswith(".smali"):
                yield os.path.join(dirpath, fn)


def _scan_one(path):
    """Quét 1 tệp smali — trả (methods, fields, strings)."""
    methods = set()
    fields = set()
    strings = 0
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return methods, fields, 0
    for m in _METHOD_DECL_RE.finditer(text):
        methods.add(m.group(0))
    for m in _INVOKE_RE.finditer(text):
        methods.add(m.group(0))
    for m in _FIELD_DECL_RE.finditer(text):
        fields.add(m.group(0))
    for m in _FIELD_REF_RE.finditer(text):
        fields.add(m.group(0))
    strings = len(_STRING_RE.findall(text))
    return methods, fields, strings


def analyze_tree(tree_root, max_files=None, workers=1):
    """Quét smali*/*.smali — trả dict used refs ước lượng.

    - classes:  số tệp .smali (mỗi tệp khai báo 1 class);
    - methods:  khai báo .method + tham chiếu invoke (union);
    - fields:   khai báo .field + tham chiếu get/put (union);
    - strings:  tổng const-string;
    - files:    số tệp đã quét.
    - workers > 1: song song bằng ThreadPoolExecutor (P20).
    """
    paths = []
    for path in _iter_smali(tree_root):
        if max_files and len(paths) >= max_files:
            break
        paths.append(path)
    classes = len(paths)
    methods = set()
    fields = set()
    strings = 0
    if workers and workers > 1 and len(paths) > 1:
        with ThreadPoolExecutor(max_workers=min(workers, 16)) as ex:
            for m, f, st in ex.map(_scan_one, paths):
                methods |= m
                fields |= f
                strings += st
    else:
        for m, f, st in (_scan_one(p) for p in paths):
            methods |= m
            fields |= f
            strings += st
    return {
        "classes": classes,
        "methods": len(methods),
        "fields": len(fields),
        "strings": strings,
        "files": classes,
    }


def estimate_delta(sections):
    """Ước lượng tổng delta method refs từ danh sách khối patch."""
    delta = 0
    per_type = {}
    for sec in sections:
        t = sec.type
        d = BLOCK_DELTA_EST.get(t, 0)
        delta += d
        per_type[t] = per_type.get(t, 0) + d
    return delta, per_type


def classify(used, delta=0, max_refs=DEX_METHOD_MAX):
    """Phân loại mức an toàn + còn lại (remaining)."""
    total = used + delta
    remaining = max_refs - total
    if total >= max_refs:
        return "BLOCK", remaining, total
    ratio = total / max_refs
    if ratio >= 0.95:
        return "CRITICAL", remaining, total
    if ratio >= 0.85:
        return "HIGH", remaining, total
    if ratio >= 0.70:
        return "WATCH", remaining, total
    return "SAFE", remaining, total


def budget_report(tree_root, sections=None, max_refs=DEX_METHOD_MAX,
                  max_files=None, workers=1):
    """Báo cáo đầy đủ: used / delta / mức / remaining."""
    used = analyze_tree(tree_root, max_files=max_files, workers=workers)
    delta, per_type = estimate_delta(sections or [])
    level, remaining, total = classify(used["methods"], delta, max_refs)
    return {
        "used": used,
        "delta": delta,
        "per_type": per_type,
        "total": total,
        "remaining": remaining,
        "level": level,
        "max_refs": max_refs,
    }


STRATEGY_ORDER = ("AGGRESSIVE", "EAGER", "BALANCED", "CONSERVATIVE",
                  "LOCKED")


def strategy_for(rep):
    """P6 — DEX Strategy: chọn chiến lược áp patch theo mức budget.

    - AGGRESSIVE : dư nhiều, tự do áp mọi khối;
    - EAGER      : áp bình thường, theo dõi delta;
    - BALANCED   : chỉ khối delta thấp, ưu tiên 0-delta;
    - CONSERVATIVE: chỉ khối 0-delta, cảnh báo mạnh;
    - LOCKED     : không áp (BLOCK).
    """
    level = rep["level"]
    remaining = rep["remaining"]
    max_refs = rep["max_refs"]
    used = rep["used"]["methods"]
    if level == "BLOCK":
        strategy = "LOCKED"
        risk = "HIGH"
        confidence = 99
        reason = ("DEX đã vượt giới hạn method refs (%d/%d) — phải "
                  "giảm refs trước khi áp patch." % (rep["total"], max_refs))
    elif level == "CRITICAL":
        strategy = "CONSERVATIVE"
        risk = "HIGH"
        confidence = 95
        reason = ("Còn rất ít chỗ (%d refs) — chỉ cho phép khối không làm "
                  "tăng method refs." % remaining)
    elif level == "HIGH":
        strategy = "BALANCED"
        risk = "MEDIUM"
        confidence = 90
        reason = ("Còn %d refs — chỉ áp khối delta thấp, ưu tiên khối "
                  "0-delta." % remaining)
    elif level == "WATCH":
        strategy = "EAGER"
        risk = "LOW"
        confidence = 85
        reason = ("Còn %d refs — áp bình thường, theo dõi delta sau khi "
                  "áp." % remaining)
    else:
        strategy = "AGGRESSIVE"
        risk = "LOW"
        confidence = 80
        reason = ("DEX dư nhiều (còn %d refs) — tự do áp, vẫn chạy "
                  "validation sau apply." % remaining)
    return {
        "strategy": strategy,
        "estimated_delta": rep["delta"],
        "risk": risk,
        "confidence": confidence,
        "reason": reason,
        "remaining": remaining,
        "used": used,
    }
