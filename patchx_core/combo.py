# -*- coding: utf-8 -*-
"""Gộp combo — ghép các patch có năng lực hỗ trợ nhau thành một combo tối ưu.

Ví dụ điển hình: patch bypass VIP + patch mod shell + patch kiểm tra toàn vẹn
-> combo "Bypass-VIP/License + Mod-Shell + Check-Toàn-Vẹn".

Nguyên tắc an toàn:
  - chỉ gộp các patch không xung đột (cùng MATCH khác REPLACE phải tách);
  - nhãn GOTO/NAME được đặt tiền tố theo từng patch khi gộp;
  - mỗi combo kèm danh sách nguồn và số khối lệnh.
"""

import glob
import json
import os
import time

from .optimizer import (patch_capabilities, CAP_LABELS, CAP_ORDER, SYNERGY,
                        merge_patches, find_conflicts, render_patch_text)
from .parser import parse_patch_file
from .audit import parse_nested_zip


def pack_non_conflicting(patches):
    """Gói các patch KHÔNG xung đột vào cùng nhóm; xung đột tách riêng."""
    conflicts = find_conflicts(patches)
    conf_sets = [set(c["patches"]) for c in conflicts]

    def clashes(p, group):
        for q in group:
            if any(p.name in cs and q.name in cs for cs in conf_sets):
                return True
        return False

    groups = []
    for p in patches:
        placed = False
        for g in groups:
            if not clashes(p, g):
                g.append(p)
                placed = True
                break
        if not placed:
            groups.append([p])
    return groups, conflicts


def collect_patches(root, recursive=True):
    """Nạp mọi patch .zip; quét đệ quy thư mục con nếu cần."""
    patches = []
    if recursive:
        for r, dirs, _files in os.walk(root):
            if "_patchx" in r.split(os.sep):
                continue
            for f in sorted(os.listdir(r)):
                if not f.lower().endswith(".zip"):
                    continue
                path = os.path.join(r, f)
                try:
                    patches.append(parse_patch_file(path))
                except ValueError:
                    patches.extend(parse_nested_zip(path))
                except Exception:
                    pass
    else:
        for z in sorted(glob.glob(os.path.join(root, "*.zip"))):
            try:
                patches.append(parse_patch_file(z))
            except ValueError:
                patches.extend(parse_nested_zip(z))
            except Exception:
                pass
    return patches


def combo_label(caps):
    return "+".join(CAP_LABELS.get(c, c) for c in caps)


def build_combos(patches, only=None):
    """Xây danh sách combo.

    only: danh sách năng lực bắt buộc, ví dụ
          ["bypass-license", "shell", "integrity"].
    Mặc định: combo ví dụ (bypass + shell + toàn vẹn) và mọi cặp synergy.
    """
    by_cap = {}
    for p in patches:
        for c in patch_capabilities(p):
            by_cap.setdefault(c, []).append(p)

    combos = []

    def add_combo(caps):
        selected = []
        for c in caps:
            selected.extend(by_cap.get(c, []))
        if not selected:
            return
        # Loại trùng tên patch, giữ thứ tự năng lực ưu tiên
        unique = []
        seen = set()
        for c in caps:
            for p in by_cap.get(c, []):
                if p.name not in seen:
                    seen.add(p.name)
                    unique.append(p)
        packs, conflicts = pack_non_conflicting(unique)
        for i, pack in enumerate(packs):
            merged = merge_patches(pack, "+".join(caps))
            label = combo_label(caps)
            file_label = label.replace("/", "-").replace("\\", "-")
            suffix = "" if len(packs) == 1 else "_%d" % (i + 1)
            combos.append({
                "caps": caps,
                "label": label,
                "file": file_label + suffix + ".patch",
                "patches": [p.name for p in pack],
                "sections": len(merged.sections),
                "conflicts": len(conflicts),
                "merged": merged,
            })

    if only:
        add_combo(only)
    else:
        add_combo(["bypass-license", "shell", "integrity"])
        add_combo(["trace", "api", "token", "integrity"])
        for c in CAP_ORDER:
            for partner in SYNERGY.get(c, ()):
                if c < partner:
                    add_combo([c, partner])
    return combos


def render_combo_report(combos, total_patches):
    """Kết xuất báo cáo combo dạng Markdown."""
    lines = ["# Báo cáo gộp combo", "",
             "- Tổng patch đầu vào: %d" % total_patches,
             "- Số combo tạo được: %d" % len(combos), ""]
    for cb in combos:
        lines.append("## %s" % cb["label"])
        lines.append("- File: `%s`" % cb["file"])
        lines.append("- Số khối: %d | Xung đột tách: %d" % (
            cb["sections"], cb["conflicts"]))
        lines.append("- Nguồn (%d patch):" % len(cb["patches"]))
        for n in cb["patches"]:
            lines.append("  - %s" % n)
        lines.append("")
    return "\n".join(lines)
