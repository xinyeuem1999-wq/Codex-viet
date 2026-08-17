#!/usr/bin/env python3
"""Sắp xếp dự án theo nhóm dễ hiểu.

Mặc định CHỈ xem trước, không sửa file.
Dùng --ap-dung mới thực hiện. Mọi thao tác đều ghi log và có thể hoàn tác
bằng --hoan-tac nếu chưa có thay đổi thủ công sau đó.

Thiết kế cố ý không đổi tên module Python hiện có: chỉ gom tài liệu, dữ liệu,
test/cache và công cụ phụ trợ. Module chạy chính được giữ nguyên để tránh
làm hỏng import.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RULES = {
    "tai_lieu": ["*.md", "*.txt"],
    "du_lieu": ["*.json"],
    "cong_cu": ["tools/*.py"],
    "cache": ["__pycache__/**", "patchx_core/__pycache__/**"],
}

# Chỉ di chuyển các mục an toàn; không đụng module runtime.
EXCLUDE_TOP = {
    ".git", ".github", ".codex", ".tools", "patchx_core", "tests", "tools",
    "apk_full_out", "__pycache__", "build", "dist", "venv", ".venv",
}
EXCLUDE_FILES = {"README.md", "AGENTS.md", ".gitignore", "MANIFEST.json"}
DOC_DIR = ROOT / "tai_lieu"
DATA_DIR = ROOT / "du_lieu"
CACHE_DIR = ROOT / "_cache"


def collect():
    moves = []
    for p in ROOT.iterdir():
        if p.name in EXCLUDE_TOP or p.name in EXCLUDE_FILES or p.is_dir():
            continue
        if p.suffix.lower() in {".md", ".txt"}:
            moves.append((p, DOC_DIR / p.name))
        elif p.suffix.lower() == ".json":
            moves.append((p, DATA_DIR / p.name))
    return moves


def show(moves):
    print("\nKẾ HOẠCH SẮP XẾP")
    print("=" * 60)
    if not moves:
        print("Không có file cấp gốc nào cần di chuyển.")
    for src, dst in moves:
        print(f"{src.relative_to(ROOT)}  ->  {dst.relative_to(ROOT)}")
    print("\nGiữ nguyên: patchx_core/, tests/, tools/, apk_full_out/, .git/, .codex/, .tools/")


def apply(moves):
    log = ROOT / ".sap_xep_log.json"
    records = []
    for src, dst in moves:
        if dst.exists():
            print(f"BỎ QUA (đã tồn tại): {dst.relative_to(ROOT)}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        records.append({"from": str(src.relative_to(ROOT)), "to": str(dst.relative_to(ROOT))})
        print(f"ĐÃ CHUYỂN: {src.name} -> {dst.relative_to(ROOT)}")
    log.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nĐã ghi nhật ký: {log.relative_to(ROOT)}")


def undo():
    log = ROOT / ".sap_xep_log.json"
    if not log.exists():
        print("Không có nhật ký để hoàn tác.")
        return
    records = json.loads(log.read_text(encoding="utf-8"))
    for r in reversed(records):
        src, dst = ROOT / r["to"], ROOT / r["from"]
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            print(f"HOÀN TÁC: {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
        else:
            print(f"BỎ QUA: {src.relative_to(ROOT)}")
    log.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description="Sắp xếp dự án PatchX an toàn")
    ap.add_argument("--ap-dung", action="store_true", help="thực sự di chuyển file")
    ap.add_argument("--hoan-tac", action="store_true", help="hoàn tác lần sắp xếp gần nhất")
    args = ap.parse_args()
    if args.hoan_tac:
        undo(); return
    moves = collect()
    show(moves)
    if args.ap_dung:
        print("\nĐANG ÁP DỤNG...")
        apply(moves)
    else:
        print("\nChưa thay đổi gì. Thêm --ap-dung để thực hiện.")


if __name__ == "__main__":
    main()
