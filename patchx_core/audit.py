# -*- coding: utf-8 -*-
"""Kiểm tra kiến trúc patch và nâng cấp tự động.

Nguyên tắc: chỉ tự sửa những phần an toàn (metadata, thẻ đóng, trùng lặp,
chuẩn hóa định dạng, zip lồng nhau); nội dung regex/smali giữ nguyên gốc để
không làm thay đổi cấu trúc và gây lỗi.
"""

import io
import os
import re
import zipfile

from .model import Patch
from .optimizer import dedupe_sections, render_patch_text, rebuild_patch
from .parser import parse_patch_file, parse_text, _decode

LEVEL_INFO = "thông-tin"
LEVEL_WARN = "cảnh-báo"
LEVEL_ERROR = "lỗi"

# Các đường dẫn target hợp lệ (so khớp tiền tố)
SAFE_TARGET_ROOTS = ("AndroidManifest.xml", "smali", "res", "assets", "lib",
                     "classes", "resources.arsc")

VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
GROUP_RE = re.compile(r"\$\{GROUP(\d+)\}")
ASSIGN_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$")


class Finding:
    def __init__(self, code, level, message, fixable=False):
        self.code = code
        self.level = level
        self.message = message
        self.fixable = fixable

    def to_dict(self):
        return {"code": self.code, "level": self.level,
                "message": self.message, "fixable": self.fixable}


def audit_patch(patch):
    """Trả về danh sách Finding cho một patch."""
    findings = []
    labels = set()

    # A01 — metadata
    if not patch.min_engine_ver:
        findings.append(Finding("A01", LEVEL_WARN,
                                "Thiếu [MIN_ENGINE_VER] — thêm mặc định 2",
                                fixable=True))
    if not patch.author:
        findings.append(Finding("A01", LEVEL_WARN,
                                "Thiếu [AUTHOR] — thêm mặc định patchx",
                                fixable=True))
    if not patch.package:
        findings.append(Finding("A01", LEVEL_WARN,
                                "Thiếu [PACKAGE] — thêm mặc định *",
                                fixable=True))
    if patch.min_engine_ver:
        try:
            if int(patch.min_engine_ver) < 2:
                findings.append(Finding("A14", LEVEL_INFO,
                                        "MIN_ENGINE_VER=%s cũ hơn khuyến nghị 2"
                                        % patch.min_engine_ver))
        except ValueError:
            findings.append(Finding("A14", LEVEL_WARN,
                                    "MIN_ENGINE_VER không phải số: %s"
                                    % patch.min_engine_ver))

    for sec in patch.sections:
        t = sec.type
        if t in ("MIN_ENGINE_VER", "AUTHOR", "PACKAGE"):
            continue

        # A02 — thẻ đóng
        if not sec.closed:
            findings.append(Finding("A02", LEVEL_WARN,
                                    "[%s] thiếu thẻ đóng [/%s] (khối %d)"
                                    % (t, t, sec.order), fixable=True))

        # A04 — khóa bắt buộc
        for key in ("TARGET", "MATCH"):
            if t in ("MATCH_REPLACE", "MATCH_ASSIGN", "MATCH_GOTO") \
                    and key not in sec.body:
                findings.append(Finding("A04", LEVEL_ERROR,
                                        "[%s] thiếu khóa %s (khối %d)"
                                        % (t, key, sec.order)))
            elif key in sec.body and not sec.get(key).strip() and t != "GOTO":
                findings.append(Finding("A04", LEVEL_WARN,
                                        "[%s] %s rỗng (khối %d)"
                                        % (t, key, sec.order)))
        if t == "MATCH_REPLACE" and "REPLACE" not in sec.body:
            findings.append(Finding("A04", LEVEL_ERROR,
                                    "[MATCH_REPLACE] thiếu khóa REPLACE (khối %d)"
                                    % sec.order))
        elif t == "MATCH_REPLACE" and not sec.get("REPLACE").strip():
            findings.append(Finding("A15", LEVEL_INFO,
                                    "[MATCH_REPLACE] REPLACE rỗng (khối %d) — "
                                    "có thể là thao tác xóa có chủ đích" % sec.order))
        if t == "ADD_FILES" and "SOURCE" not in sec.body:
            findings.append(Finding("A04", LEVEL_ERROR,
                                    "[ADD_FILES] thiếu SOURCE (khối %d)" % sec.order))
        if t == "REPLACE_FILES" and "SOURCE" not in sec.body:
            findings.append(Finding("A04", LEVEL_ERROR,
                                    "[REPLACE_FILES] thiếu SOURCE (khối %d)"
                                    % sec.order))
        if t == "REPLACE_FILES" and not (sec.get("TARGET") or "").strip():
            findings.append(Finding("A04", LEVEL_ERROR,
                                    "[REPLACE_FILES] thiếu TARGET (khối %d)"
                                    % sec.order))
        if t == "SET_BOOL":
            for key in ("TARGET", "MATCH", "VALUE"):
                if key not in sec.body:
                    findings.append(Finding("A04", LEVEL_ERROR,
                                            "[SET_BOOL] thiếu khóa %s (khối %d)"
                                            % (key, sec.order)))
            value = sec.get("VALUE").strip().lower()
            if value and value not in ("true", "false", "1", "0", "0x0", "0x1"):
                findings.append(Finding("A04", LEVEL_ERROR,
                                        "[SET_BOOL] VALUE không hợp lệ: %r "
                                        "(khối %d)" % (value, sec.order)))
        if t == "INIT" and "CODE" not in sec.body:
            findings.append(Finding("A04", LEVEL_ERROR,
                                    "[INIT] thiếu khóa CODE (khối %d)" % sec.order))
        if t == "HOOK_SCRIPT" and "SOURCE" not in sec.body:
            findings.append(Finding("A04", LEVEL_ERROR,
                                    "[HOOK_SCRIPT] thiếu khóa SOURCE (khối %d)"
                                    % sec.order))
        if t in ("TRACE", "API_LOG"):
            for key in ("TARGET", "MATCH"):
                if key not in sec.body:
                    findings.append(Finding("A04", LEVEL_ERROR,
                                            "[%s] thiếu khóa %s (khối %d)"
                                            % (t, key, sec.order)))
        if t == "REMOTE_CONFIG" and "CONFIG_URL" not in sec.body:
            findings.append(Finding("A04", LEVEL_ERROR,
                                    "[REMOTE_CONFIG] thiếu khóa CONFIG_URL "
                                    "(khối %d)" % sec.order))
        if t in ("ADD_FILES", "REPLACE_FILES", "MERGE", "EXECUTE_DEX",
                 "HOOK_SCRIPT"):
            src = sec.get("SOURCE") or sec.get("SCRIPT")
            if src and src.strip() and src.strip() not in patch.assets:
                if not patch.asset_root or not os.path.isfile(
                    os.path.join(patch.asset_root, src.strip())):
                    findings.append(Finding("A09", LEVEL_WARN,
                                            "[%s] tham chiếu tài nguyên không "
                                            "có trong patch: %s (khối %d)"
                                            % (t, src.strip(), sec.order)))

        # A05 — regex không biên dịch được
        if t in ("MATCH_REPLACE", "MATCH_ASSIGN", "MATCH_GOTO",
                 "LAUNCHER_ACTIVITIES", "ACTIVITIES", "APPLICATION",
                 "SET_BOOL", "TRACE", "API_LOG"):
            if sec.get("REGEX", "").strip().lower() in ("true", "1") \
                    and sec.get("MATCH").strip():
                try:
                    flags = re.DOTALL if sec.get("DOTALL", "").strip().lower() \
                        in ("true", "1") else 0
                    re.compile(sec.get("MATCH"), flags)
                except re.error as e:
                    findings.append(Finding("A05", LEVEL_ERROR,
                                            "[%s] regex lỗi (khối %d): %s"
                                            % (t, sec.order, e)))
            # A11 — GROUP vượt quá số nhóm của mẫu
            if sec.get("REGEX", "").strip().lower() in ("true", "1") \
                    and sec.get("MATCH").strip():
                try:
                    n_groups = re.compile(sec.get("MATCH")).groups
                    for g in set(GROUP_RE.findall(sec.get("REPLACE"))
                                 + GROUP_RE.findall(sec.get("ASSIGN"))):
                        if int(g) > n_groups:
                            findings.append(Finding("A11", LEVEL_WARN,
                                                    "[%s] ${GROUP%s} vượt quá "
                                                    "số nhóm %d của mẫu (khối %d)"
                                                    % (t, g, n_groups, sec.order)))
                except re.error:
                    pass

        # A13 — target ngoài vùng chuẩn
        target = sec.get("TARGET").strip()
        if target and t not in ("GOTO", "DUMMY"):
            pseudo = target.startswith("[") and target.endswith("]")
            safe = any(target == r or target.startswith(r + "/")
                       or target.startswith(r) and "*" in target
                       for r in SAFE_TARGET_ROOTS)
            if not pseudo and not safe and not target.startswith("["):
                findings.append(Finding("A13", LEVEL_WARN,
                                        "[%s] TARGET ngoài vùng chuẩn: %s "
                                        "(khối %d)" % (t, target, sec.order)))

        # Nhãn cho GOTO
        if sec.name:
            labels.add(sec.name)
        if t == "DUMMY" and sec.get("NAME").strip():
            labels.add(sec.get("NAME").strip())

    # A06 — GOTO trỏ nhãn không tồn tại
    for sec in patch.sections:
        if sec.type in ("GOTO", "MATCH_GOTO"):
            label = sec.get("GOTO").strip()
            if label and label not in labels:
                findings.append(Finding("A06", LEVEL_ERROR,
                                        "GOTO trỏ nhãn không tồn tại: %s"
                                        % label, fixable=False))

    # A07/A08 — biến ASSIGN
    assigned = set()
    for sec in patch.sections:
        for part in sec.get("ASSIGN").splitlines():
            m = ASSIGN_RE.match(part)
            if m:
                assigned.add(m.group(1))
    used = set()
    for sec in patch.sections:
        for v in VAR_RE.findall(sec.get("REPLACE") + "\n" + sec.get("ASSIGN")
                                + "\n" + sec.get("GOTO")):
            if v.startswith("GROUP"):
                continue
            used.add(v)
    for v in sorted(used - assigned):
        findings.append(Finding("A07", LEVEL_WARN,
                                "Biến ${%s} được dùng nhưng chưa được gán" % v))
    for v in sorted(assigned - used):
        findings.append(Finding("A08", LEVEL_INFO,
                                "Biến ${%s} được gán nhưng không dùng tới" % v))

    # A10 — trùng lặp khối trong cùng patch
    _, removed = dedupe_sections(patch)
    if removed:
        findings.append(Finding("A10", LEVEL_INFO,
                                "Có %d khối trùng lặp — có thể gộp" % removed,
                                fixable=True))

    # A12 — chuẩn hóa định dạng
    raw = getattr(patch, "_raw_text", "")
    if "\r" in raw:
        findings.append(Finding("A12", LEVEL_INFO,
                                "Tệp dùng CRLF — chuẩn hóa về LF", fixable=True))
    if raw.startswith("\ufeff"):
        findings.append(Finding("A12", LEVEL_INFO,
                                "Tệp có BOM — loại bỏ", fixable=True))
    return findings


def upgrade_patch(patch, header=None):
    """Nâng cấp patch: metadata đủ, thẻ đóng đủ, gộp trùng, định dạng chuẩn."""
    new_patch = rebuild_patch(patch, header=header)
    sections, _ = dedupe_sections(new_patch)
    new_patch.sections = sections
    _convert_literal_regex(new_patch)
    return new_patch


def _convert_literal_regex(patch):
    """Chuyển rule regex thuần literal sang REGEX=false để quét nhanh.

    Chỉ chuyển khi MATCH hoàn toàn là chuỗi literal (re.escape không đổi
    nội dung) — khi đó text.count cho kết quả giống hệt re.findall, nên
    scanner đi đường literal nhanh (rg -F) mà không đổi hành vi.
    """
    for sec in patch.sections:
        if sec.type not in ("MATCH_REPLACE", "MATCH_ASSIGN", "MATCH_GOTO"):
            continue
        if sec.get("REGEX", "").strip().lower() not in ("true", "1"):
            continue
        m = sec.get("MATCH", "").strip()
        if m and re.escape(m) == m:
            sec.body["REGEX"] = "false"


def parse_nested_zip(path):
    """Trường hợp zip ngoài không có patch.txt nhưng chứa zip con có patch.txt."""
    found = []
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            if name.lower().endswith(".zip"):
                try:
                    inner = zipfile.ZipFile(io.BytesIO(zf.read(name)))
                except zipfile.BadZipFile:
                    continue
                patch_entry = None
                for n in inner.namelist():
                    if n.lower() == "patch.txt" \
                            or n.lower().endswith("/patch.txt"):
                        patch_entry = n
                        break
                if patch_entry is None:
                    continue
                text = _decode(inner.read(patch_entry))
                p = parse_text(text)
                p.source = os.path.join(path, name)
                p.assets = {n: inner.read(n) for n in inner.namelist()
                            if n != patch_entry and not n.endswith("/")}
                found.append(p)
    return found


def upgrade_zip(path, out_dir, dry_run=False, header=None):
    """Tạo bản nâng cấp cho một zip patch; xử lý cả zip lồng nhau."""
    results = []
    try:
        patch = parse_patch_file(path)
        new_patch = upgrade_patch(patch, header=header)
        out_name = os.path.splitext(os.path.basename(path))[0] + ".zip"
        results.append((path, new_patch, out_name))
    except ValueError:
        # Không có patch.txt trực tiếp — thử zip lồng nhau
        nested = parse_nested_zip(path)
        for p in nested:
            new_patch = upgrade_patch(p, header=header)
            inner_name = os.path.splitext(os.path.basename(p.source))[0]
            out_name = "%s_%s.zip" % (os.path.splitext(os.path.basename(path))[0],
                                      inner_name)
            results.append((path, new_patch, out_name))
        if not nested:
            raise
    if dry_run:
        return results
    os.makedirs(out_dir, exist_ok=True)
    for src, new_patch, out_name in results:
        out_path = os.path.join(out_dir, out_name)
        text = render_patch_text(new_patch, header=header)
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("patch.txt", text)
            for name, data in new_patch.assets.items():
                zf.writestr(name, data)
    return results
