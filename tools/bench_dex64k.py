# -*- coding: utf-8 -*-
"""P10/P12 — Benchmark 64K DEX: sinh cây smali lớn, đo dex-budget.

Sinh cây APK giả với N method refs, chạy analyze_tree + budget_report,
đo thời gian, kiểm tra mức phân loại (SAFE..BLOCK).

Chạy:  python3 tools/bench_dex64k.py [--out THƯ_MỤC] [--methods 70000]
"""

import argparse
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patchx_core.dex_budget import analyze_tree, budget_report, DEX_METHOD_MAX

_METHOD_TMPL = (
    ".method public static m{mi}()V\n"
    "    .registers 2\n\n"
    "    const-string v0, \"bench{mi}\"\n\n"
    "    invoke-static {{v0}}, Lbench/Ref;->use(Ljava/lang/String;)V\n\n"
    "    return-void\n"
    ".end method\n"
)


def gen_tree(root, total_methods, methods_per_file=40):
    """Sinh cây smali với đủ số method khai báo (mỗi tệp 1 class)."""
    smali = os.path.join(root, "smali", "bench")
    os.makedirs(smali, exist_ok=True)
    with open(os.path.join(root, "AndroidManifest.xml"), "w",
              encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="utf-8"?>\n'
                 '<manifest xmlns:android="http://schemas.android.com/apk/'
                 'res/android" package="com.bench">\n'
                 '  <application></application>\n</manifest>\n')
    nfiles = (total_methods + methods_per_file - 1) // methods_per_file
    made = 0
    for fi in range(nfiles):
        body = [".class public Lbench/Gen%d;" % fi,
                ".super Ljava/lang/Object;\n"]
        for mi in range(methods_per_file):
            if made >= total_methods:
                break
            body.append(_METHOD_TMPL.format(mi=fi * 100000 + mi))
            made += 1
        with open(os.path.join(smali, "Gen%d.smali" % fi), "w",
                  encoding="utf-8") as fh:
            fh.write("\n".join(body) + "\n")
    return made


def bench(target_methods, workdir, methods_per_file=40):
    tree = os.path.join(workdir, "tree_%d" % target_methods)
    t0 = time.time()
    made = gen_tree(tree, target_methods, methods_per_file)
    t_gen = time.time() - t0
    t0 = time.time()
    used = analyze_tree(tree)
    t_scan = time.time() - t0
    rep = budget_report(tree)
    return {
        "target_methods": target_methods,
        "made": made,
        "scan_seconds": round(t_scan, 3),
        "gen_seconds": round(t_gen, 3),
        "analyzed": used,
        "level": rep["level"],
        "total": rep["total"],
        "remaining": rep["remaining"],
        "max_refs": rep["max_refs"],
        "ok": made >= target_methods,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="bench_dex64k_out")
    ap.add_argument("--methods", type=int, default=70000,
                    help="Số method mục tiêu (mặc định 70000 > 64K)")
    ap.add_argument("--sizes", default="20000,56000,70000",
                    help="Các mức cần đo, phân tách bằng dấu phẩy")
    args = ap.parse_args()

    workdir = args.out
    os.makedirs(workdir, exist_ok=True)
    results = []
    for size in (int(x) for x in args.sizes.split(",") if x.strip()):
        print("[bench-dex64k] đang đo %d methods..." % size, flush=True)
        r = bench(size, workdir)
        results.append(r)
        print("  -> level=%s total=%d remaining=%d scan=%.3fs made=%d"
              % (r["level"], r["total"], r["remaining"], r["scan_seconds"],
                 r["made"]), flush=True)

    small, med, large = results[0], results[1], results[-1]
    checks = {
        "small_safe": small["level"] == "SAFE",
        "medium_high": med["level"] in ("HIGH", "CRITICAL"),
        "large_block": large["level"] == "BLOCK",
        "large_over_64k": large["total"] > DEX_METHOD_MAX,
        "gen_du": all(r["made"] >= r["target_methods"] for r in results),
    }
    ok = all(checks.values())
    report = {
        "name": "bench_dex64k",
        "results": results,
        "checks": checks,
        "ok": ok,
    }
    with open(os.path.join(workdir, "bench_dex64k_report.json"), "w",
              encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(workdir, "bench_dex64k_report.md"), "w",
              encoding="utf-8") as fh:
        fh.write("# Benchmark 64K DEX\n\n")
        fh.write("| Mục tiêu | Đã sinh | Level | Tổng | Còn lại | Quét (s) |\n")
        fh.write("|---|---|---|---|---|---|\n")
        for r in results:
            fh.write("| %d | %d | %s | %d | %d | %.3f |\n"
                     % (r["target_methods"], r["made"], r["level"],
                        r["total"], r["remaining"], r["scan_seconds"]))
        fh.write("\n## Kiểm tra\n\n")
        for k, v in checks.items():
            fh.write("- %s: %s\n" % (k, "PASS" if v else "FAIL"))
        fh.write("\n## Kết luận\n\n%s\n" % ("ĐẠT" if ok else "CHƯA ĐẠT"))
    print("[bench-dex64k] %s — xem %s/bench_dex64k_report.md"
          % ("ĐẠT" if ok else "CHƯA ĐẠT", workdir))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
