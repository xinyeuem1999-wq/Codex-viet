#!/usr/bin/env python3
"""Sắp xếp PatchX an toàn.

Mặc định CHỈ lập kế hoạch (dry-run). Không xóa, không ghi đè.
Dùng --apply sau khi xem kế hoạch.

Mục tiêu: gom module patchx_core thành các nhóm dễ hiểu:
  nhin/       đọc, phân tích APK
  hieu/       model, semantic, tìm mục tiêu
  kiem-tra/   validate, preflight, audit, verify
  lam/        engine, apply, compile, optimizer
  nho/        knowledge, failure, baseline, learn
  ho-tro/     CLI, session, simulate, fuzz, báo cáo...

Script cố ý KHÔNG di chuyển file nếu phát hiện import nội bộ chưa xử lý.
Trong --apply, nó sửa import tuyệt đối nội bộ theo ánh xạ đường dẫn mới,
sau đó kiểm tra AST/import cơ bản trước khi hoàn tất.
"""
from __future__ import annotations

import argparse
import ast
import re
import shutil
from pathlib import Path

GROUPS = {
    "nhin": {
        "analyze.py", "model.py", "parser.py", "indexer.py", "diffapk.py",
        "smali_lib.py", "smali_sem.py", "runtime_scenario.py",
    },
    "hieu": {
        "semantic_plan.py", "remote_map.py", "complement.py", "knowledge.py",
    },
    "kiem-tra": {
        "audit.py", "preflight.py", "acceptance.py", "smali_validate.py",
        "risk.py", "dex_budget.py", "baseline.py",
    },
    "lam": {
        "engine.py", "plan_compile.py", "optimizer.py", "combo.py", "upgrade.py",
    },
    "nho": {
        "failure_db.py", "learn.py", "knowledge.py", "baseline.py",
    },
}

# Những module điều phối/chưa nên ép vào nhóm nghiệp vụ.
SUPPORT = {
    "__init__.py", "cli.py", "session.py", "simulate.py", "fuzz.py", "advisor.py",
    "bypass_advisor.py", "audit.py", "coverage.py", "remote_patch.py", "diffapk.py",
}


def classify(name: str) -> str:
    hits = [g for g, files in GROUPS.items() if name in files]
    if len(hits) == 1:
        return hits[0]
    # Module có nhiều vai trò: ưu tiên để nguyên ở ho-tro, tránh làm hỏng import.
    if len(hits) > 1:
        return "ho-tro"
    return "ho-tro"


def module_imports(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.level == 1 and n.module:
            out.add(n.module.split(".")[0] + ".py")
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name.startswith("patchx_core"):
                    out.add(a.name.split(".")[-1] + ".py")
    return out


def build_plan(core: Path) -> list[tuple[Path, Path]]:
    files = sorted(p for p in core.glob("*.py") if p.is_file())
    plan = []
    for src in files:
        if src.name == "__init__.py":
            continue
        group = classify(src.name)
        dst = core / group / src.name
        if dst != src:
            plan.append((src, dst))
    return plan


def check_collisions(plan):
    seen = {}
    errors = []
    for src, dst in plan:
        if dst.exists() and dst != src:
            errors.append(f"ĐÍCH ĐÃ TỒN TẠI: {dst}")
        if dst in seen:
            errors.append(f"TRÙNG ĐÍCH: {dst} <- {seen[dst].name}, {src.name}")
        seen[dst] = src
    return errors


def rewrite_imports(root: Path, plan: list[tuple[Path, Path]]):
    mapping = {src.stem: dst.parent.name + "." + dst.stem for src, dst in plan}
    for p in root.rglob("*.py"):
        text = p.read_text(encoding="utf-8")
        new = text
        for old, newmod in mapping.items():
            new = re.sub(rf"from \.{re.escape(old)} import", f"from .{newmod} import", new)
            new = re.sub(rf"from patchx_core\.{re.escape(old)} import", f"from patchx_core.{newmod} import", new)
            new = re.sub(rf"import patchx_core\.{re.escape(old)}\b", f"import patchx_core.{newmod}", new)
        if new != text:
            p.write_text(new, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Lập/áp kế hoạch sắp xếp PatchX an toàn")
    ap.add_argument("root", nargs="?", default="patchx_core", help="thư mục patchx_core")
    ap.add_argument("--apply", action="store_true", help="thực sự di chuyển và sửa import")
    ap.add_argument("--backup", action="store_true", help="tạo bản sao patchx_core trước khi sửa")
    args = ap.parse_args()

    core = Path(args.root).resolve()
    if not core.is_dir():
        raise SystemExit(f"Không tìm thấy: {core}")

    plan = build_plan(core)
    errors = check_collisions(plan)
    print(f"Thư mục: {core}")
    print(f"Số file sẽ sắp xếp: {len(plan)}")
    for src, dst in plan:
        print(f"  {src.name:28} -> {dst.parent.name}/{dst.name}")
    if errors:
        print("\nKHÔNG THỂ TIẾP TỤC:")
        print("\n".join("  " + e for e in errors))
        return 2

    if not args.apply:
        print("\nDRY-RUN: chưa thay đổi file nào.")
        print("Nếu danh sách đúng, chạy: python3 scripts/sap-xep-du-an.py patchx_core --apply --backup")
        return 0

    if args.backup:
        backup = core.parent / (core.name + ".backup-before-reorder")
        if backup.exists():
            raise SystemExit(f"Backup đã tồn tại: {backup}; không ghi đè.")
        shutil.copytree(core, backup)
        print(f"Đã backup: {backup}")

    for _, dst in plan:
        dst.parent.mkdir(parents=True, exist_ok=True)
    for src, dst in plan:
        src.rename(dst)

    # Chỉ sửa import sau khi đã có cấu trúc mới.
    rewrite_imports(core, plan)

    # Parse toàn bộ Python để bắt lỗi cú pháp ngay.
    bad = []
    for p in core.rglob("*.py"):
        try:
            ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except SyntaxError as e:
            bad.append(f"{p}: {e}")
    if bad:
        print("PHÁT HIỆN LỖI CÚ PHÁP:")
        print("\n".join(bad))
        return 3

    print("\nĐÃ SẮP XẾP. Bước tiếp theo: chạy bộ test của project và kiểm tra import.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
