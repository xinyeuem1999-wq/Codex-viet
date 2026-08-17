# -*- coding: utf-8 -*-
"""Bộ phân tích cú pháp patch.txt — xử lý linh hoạt các biến thể thực tế.

Hỗ trợ:
  - khối không có thẻ đóng (kết thúc khi gặp khối mới hoặc hết tệp);
  - TARGET: [LAUNCHER_ACTIVITIES] — giá trị trông giống cú pháp khối;
  - BOM/CRLF, thẻ bị thụt lề, chú thích # ngoài giá trị;
  - tệp zip có tên entry mã hóa không phải UTF-8.
"""

import os
import re
import zlib
import zipfile

from .model import Patch, Section

# Các "component target" đặc biệt của APK Editor
PSEUDO_TARGETS = {"[APPLICATION]", "[ACTIVITIES]", "[LAUNCHER_ACTIVITIES]"}

SECTION_RE = re.compile(r"^\s*\[(/)?([A-Z][A-Z0-9_]*)\]\s*$")
KEY_RE = re.compile(r"^\s*([A-Z][A-Z0-9_]*):(.*)$")

# Danh sách khóa đã biết — chỉ dòng bắt đầu bằng khóa này mới mở giá trị mới
KNOWN_KEYS = {
    "NAME", "TARGET", "MATCH", "REGEX", "REPLACE", "ASSIGN", "GOTO", "DOTALL",
    "SOURCE", "EXTRACT", "SCRIPT", "SMALI_NEEDED", "MAIN_CLASS", "ENTRANCE",
    "PARAM", "MIN_ENGINE_VER", "AUTHOR", "PACKAGE",
    # Khối thực thi hiện đại (SET_BOOL / INIT / HOOK_SCRIPT / TRACE / API_LOG
    # / REMOTE_CONFIG)
    "VALUE", "CODE", "METHOD", "ENTRY", "TAG", "BEFORE", "AFTER",
    "CONFIG_URL", "FORCE", "HELPER",
}


def _decode(data: bytes) -> str:
    """Giải mã nội dung patch.txt; thử UTF-8 trước, rồi cp1251, cp866."""
    for enc in ("utf-8", "cp1251", "cp866"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _split_sections(text: str):
    """Chia văn bản thành danh sách [type, closed, lines]."""
    sections = []
    cur = None
    pending_target = False
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        m = SECTION_RE.match(line)
        pseudo = "[" + m.group(2) + "]" if m else None
        if m and not (pending_target and pseudo in PSEUDO_TARGETS):
            closing, name = m.groups()
            if closing:
                if cur and cur[0] == name:
                    cur[1] = True
                    sections.append(cur)
                    cur = None
                    pending_target = False
                elif cur:
                    # Thẻ đóng lệch khối — coi là nội dung để tránh mất dữ liệu
                    cur[2].append(line)
            else:
                if cur:
                    sections.append(cur)
                cur = [name, False, []]
                pending_target = False
        else:
            if cur is None:
                continue  # bỏ phần mở đầu / chú thích ngoài khối
            cur[2].append(line)
            km = KEY_RE.match(line)
            is_target_key = bool(km and km.group(1) == "TARGET"
                                 and not km.group(2).strip())
            if is_target_key:
                pending_target = True
            elif line.strip():
                pending_target = False
    if cur:
        sections.append(cur)
    return sections


def _normalize_value(lines):
    """Chuẩn hóa giá trị:
    - bỏ dòng trống ở đầu/cuối;
    - dòng đầu cắt thụt lề của tệp (chỉ để trình bày);
    - các dòng tiếp theo giữ nguyên (thụt lề smali/XML có ý nghĩa).
    """
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    if not lines:
        return ""
    first = lines[0].lstrip() if lines[0].strip() else ""
    return "\n".join([first] + lines[1:])


def _parse_body(lines) -> dict:
    """Chuyển các dòng thân khối thành dict khóa -> giá trị."""
    body = {}
    cur_key = None
    cur_lines = []
    for line in lines:
        km = KEY_RE.match(line)
        if km and km.group(1) in KNOWN_KEYS:
            if cur_key is not None:
                body[cur_key] = _normalize_value(cur_lines)
            cur_key = km.group(1)
            cur_lines = [km.group(2)]
        else:
            s = line.strip()
            if cur_key is None and (not s or s.startswith("#")):
                continue  # chú thích trước khóa đầu tiên
            cur_lines.append(line)
    if cur_key is not None:
        body[cur_key] = _normalize_value(cur_lines)
    return body


def parse_text(text: str) -> Patch:
    """Phân tích văn bản patch.txt thành Patch."""
    if text.startswith("\ufeff"):
        text = text[1:]
    patch = Patch(source="<chuỗi>")
    order = 0
    for type_, closed, lines in _split_sections(text):
        body = _parse_body(lines)
        sec = Section(type=type_, body=body, order=order, closed=closed,
                      raw="\n".join(lines))
        if body.get("NAME", "").strip():
            sec.name = body["NAME"].strip()
        patch.sections.append(sec)
        order += 1
        if type_ in ("MIN_ENGINE_VER", "AUTHOR", "PACKAGE"):
            val = "\n".join(l.strip() for l in lines
                            if l.strip() and not l.strip().startswith("#"))
            if type_ == "MIN_ENGINE_VER":
                patch.min_engine_ver = val
            elif type_ == "AUTHOR":
                patch.author = val
            else:
                patch.package = val
    _validate(patch)
    return patch


def _validate(patch: Patch):
    """Rà soát lỗi phổ biến, ghi vào patch.issues."""
    for sec in patch.sections:
        if sec.type in ("MATCH_REPLACE", "MATCH_ASSIGN", "MATCH_GOTO",
                        "REMOVE_FILES"):
            if "TARGET" not in sec.body:
                patch.issues.append("[%s] thiếu khóa TARGET (khối %d)"
                                    % (sec.type, sec.order))
            elif not sec.get("TARGET").strip():
                patch.issues.append("[%s] TARGET rỗng (khối %d)"
                                    % (sec.type, sec.order))
        if sec.type in ("MATCH_REPLACE", "MATCH_ASSIGN", "MATCH_GOTO"):
            if "MATCH" not in sec.body:
                patch.issues.append("[%s] thiếu khóa MATCH (khối %d)"
                                    % (sec.type, sec.order))
            elif not sec.get("MATCH").strip():
                patch.issues.append("[%s] MATCH rỗng (khối %d)"
                                    % (sec.type, sec.order))
        if sec.type == "MATCH_REPLACE" and "REPLACE" not in sec.body:
            patch.issues.append("[MATCH_REPLACE] thiếu khóa REPLACE (khối %d)"
                                % sec.order)
        if sec.type == "ADD_FILES" and "SOURCE" not in sec.body:
            patch.issues.append("[ADD_FILES] thiếu SOURCE (khối %d)" % sec.order)
        if sec.type == "SET_BOOL":
            for k in ("TARGET", "MATCH", "VALUE"):
                if k not in sec.body:
                    patch.issues.append("[SET_BOOL] thiếu khóa %s (khối %d)"
                                        % (k, sec.order))
        if sec.type == "INIT" and "CODE" not in sec.body:
            patch.issues.append("[INIT] thiếu khóa CODE (khối %d)" % sec.order)
        if sec.type == "HOOK_SCRIPT" and "SOURCE" not in sec.body:
            patch.issues.append("[HOOK_SCRIPT] thiếu khóa SOURCE (khối %d)"
                                % sec.order)
        if sec.type in ("TRACE", "API_LOG"):
            for k in ("TARGET", "MATCH"):
                if k not in sec.body:
                    patch.issues.append("[%s] thiếu khóa %s (khối %d)"
                                        % (sec.type, k, sec.order))
        if sec.type == "REMOTE_CONFIG" and "CONFIG_URL" not in sec.body:
            patch.issues.append("[REMOTE_CONFIG] thiếu khóa CONFIG_URL (khối %d)"
                                % sec.order)
        if not sec.closed and sec.type not in (
                "MIN_ENGINE_VER", "AUTHOR", "PACKAGE"):
            patch.issues.append("[%s] khối không có thẻ đóng (khối %d)"
                                % (sec.type, sec.order))
    if not patch.sections:
        patch.issues.append("Không có khối lệnh nào")


def _parse_zip(path: str) -> Patch:
    """Đọc patch từ tệp .zip (kèm toàn bộ tài nguyên bên trong)."""
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        patch_entry = None
        for n in names:
            if n.lower() == "patch.txt" or n.lower().endswith("/patch.txt"):
                patch_entry = n
                break
        if patch_entry is None:
            raise ValueError("Không tìm thấy patch.txt trong %s" % path)
        text = _decode(zf.read(patch_entry))
        patch = parse_text(text)
        patch.source = path
        for n in names:
            if n == patch_entry or n.endswith("/"):
                continue
            try:
                patch.assets[n] = zf.read(n)
            except (KeyError, RuntimeError, zlib.error, EOFError, OSError) as e:
                patch.issues.append("[ZIP] không đọc được asset %s: %s" % (n, e))
        return patch


def _parse_text_file(path: str, asset_root: str = None) -> Patch:
    """Đọc patch từ patch.txt trên đĩa."""
    with open(path, "rb") as fh:
        data = fh.read()
    patch = parse_text(_decode(data))
    patch.source = path
    patch.asset_root = asset_root or os.path.dirname(os.path.abspath(path))
    return patch


def parse_patch_file(path: str) -> Patch:
    """Phân tích patch từ .zip, .txt hoặc thư mục chứa patch.txt."""
    if not os.path.exists(path):
        raise FileNotFoundError("Không tìm thấy: %s" % path)
    if os.path.isdir(path):
        p = os.path.join(path, "patch.txt")
        if not os.path.isfile(p):
            raise ValueError("Không tìm thấy patch.txt trong thư mục: %s" % path)
        return _parse_text_file(p, asset_root=path)
    if path.lower().endswith(".zip"):
        return _parse_zip(path)
    if path.lower().endswith(".txt"):
        return _parse_text_file(path)
    # Không rõ loại — thử như zip, nếu thất bại thì như văn bản
    try:
        return _parse_zip(path)
    except (zipfile.BadZipFile, ValueError):
        return _parse_text_file(path)
