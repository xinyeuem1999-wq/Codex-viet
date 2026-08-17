# -*- coding: utf-8 -*-
"""Giao diện dòng lệnh của patchx — toàn bộ thông báo bằng tiếng Việt."""

import argparse
import glob
import json
import os
import subprocess
import sys
import time

from . import __version__
from .parser import parse_patch_file
from .engine import Engine
from .audit import (audit_patch, parse_nested_zip, upgrade_zip,
                    Finding, LEVEL_ERROR, LEVEL_WARN)
from .indexer import scan_dir, write_index, render_report
from .optimizer import (cluster_tag, find_conflicts, merge_patches,
                        render_patch_text)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_patches(root, recursive=False):
    """Nạp mọi patch (zip) trong thư mục; xử lý zip lồng nhau."""
    patches = []
    from .indexer import _iter_zips
    for z in _iter_zips(root, recursive=recursive):
        try:
            patches.append(parse_patch_file(z))
        except ValueError:
            patches.extend(parse_nested_zip(z))
        except Exception as e:
            print("[patchx] bỏ qua %s: %s" % (os.path.basename(z), e))
    return patches


def cmd_scan(args):
    records = scan_dir(args.thu_muc, recursive=args.recursive)
    dupes = [r for r in records if r.get("dupe_id")]
    if dupes:
        print("[patchx] %d file trùng nội dung (%d nhóm)" % (
            len(dupes), len({r["dupe_id"] for r in dupes})))
    print("Tổng patch: %d" % len(records))
    print("%-38s %-18s %8s %6s %6s %s" % (
        "Patch", "Nhóm", "Engine", "Khối", "Tài nguyên", "Vấn đề"))
    for r in records:
        n_sec = sum(r["sections"].values()) if r["sections"] else 0
        problems = "LỖI" if r["parse_error"] else (
            str(len(r["issues"])) if r["issues"] else "—")
        print("%-38s %-18s %8s %6d %6d %s" % (
            r["name"], r["tag"], r["engine_ver"] or "—",
            n_sec, len(r["assets"]), problems))
    if args.o:
        with open(args.o, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "patches": records}, fh, ensure_ascii=False, indent=2)
        print("Đã ghi:", args.o)


def cmd_index(args):
    ip, rp = write_index(args.thu_muc, args.o, name=args.ten,
                         recursive=args.recursive)
    print("Đã ghi:", ip)
    print("Đã ghi:", rp)


def cmd_dupes(args):
    from .indexer import scan_dir, dedupe_report
    records = scan_dir(args.thu_muc, recursive=args.recursive)
    groups = dedupe_report(records)
    out_dir = args.o or os.path.join(args.thu_muc, "_patchx")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "dupes.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump({"generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "root": args.thu_muc, "total": len(records),
                   "groups": groups}, fh, ensure_ascii=False, indent=2)
    lines = ["# Báo cáo trùng lặp nội dung", "",
             "- Tổng file: %d" % len(records),
             "- Nhóm trùng: %d" % len(groups), ""]
    if not groups:
        lines.append("Không phát hiện trùng lặp (theo hash patch.txt).")
    for g in groups:
        lines.append("## Nhóm %d — %d file (bản chuẩn: %s)" % (
            g["nhóm"], g["số_file"], g["bản_chuẩn"]))
        lines.append("")
        lines.append("- sha256: `%s`" % g["sha256"])
        lines.append("- Bản chuẩn (nhỏ nhất): `%s`" % g["bản_chuẩn"])
        for d in g["bản_trùng"]:
            lines.append("- Bản trùng: `%s`" % d)
        lines.append("")
    rp = os.path.join(out_dir, "dupes_report.md")
    with open(rp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print("[patchx] %d nhóm trùng từ %d file" % (len(groups), len(records)))
    for g in groups:
        print("  Nhóm %d: %s (+ %d bản trùng)" % (
            g["nhóm"], g["bản_chuẩn"], len(g["bản_trùng"])))
    print("Đã ghi:", os.path.join(out_dir, "dupes_report.md"))
    return 0


def cmd_manifest(args):
    from .indexer import scan_dir, dedupe_report
    root = os.path.abspath(args.thu_muc)
    records = scan_dir(root, recursive=True)
    folders = {}
    empty = []
    for d in sorted(os.listdir(root)):
        if not os.path.isdir(os.path.join(root, d)) or d.startswith("."):
            continue
        zips = [r for r in records if r["path"].startswith(d + os.sep)]
        if zips:
            folders[d] = {"files": len(zips),
                          "size": sum(r["size"] for r in zips)}
        else:
            empty.append(d)
    manifest = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": root,
        "total_files": len(records),
        "total_size": sum(r["size"] for r in records),
        "files": {r["path"]: r["sha256"] for r in records},
        "folders": folders,
        "empty_folders": empty,
        "dupe_groups": dedupe_report(records),
    }
    out = args.o or os.path.join(root, "_patchx", "MANIFEST.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print("[patchx] MANIFEST: %d file, %d thư mục, %d thư mục trống, "
          "%d nhóm trùng" % (len(records), len(folders), len(empty),
                             len(manifest["dupe_groups"])))
    return 0


def cmd_verify_manifest(args):
    """T5: xác minh kho theo MANIFEST.json — phát hiện file bị sửa/thêm/bớt."""
    from .indexer import scan_dir
    root = os.path.abspath(args.thu_muc)
    mpath = args.manifest or os.path.join(root, "_patchx", "MANIFEST.json")
    if not os.path.isfile(mpath):
        print("[patchx] Không thấy MANIFEST.json — chạy `patchx manifest` "
              "trước.")
        return 1
    old = json.load(open(mpath, encoding="utf-8"))
    old_files = old.get("files", {})
    records = scan_dir(root, recursive=True)
    cur = {r["path"]: r["sha256"] for r in records}
    added = sorted(set(cur) - set(old_files))
    removed = sorted(set(old_files) - set(cur))
    modified = sorted(p for p in set(old_files) & set(cur)
                      if old_files[p] != cur[p])
    ok = not (added or removed or modified)
    print("[patchx] verify-manifest: %d file, thêm %d, xóa %d, sửa %d%s"
          % (len(cur), len(added), len(removed), len(modified),
             "" if ok else " — ⚠ KHO ĐÃ BỊ THAY ĐỔI"))
    for p in added[:10]:
        print("  + %s" % p)
    for p in removed[:10]:
        print("  - %s" % p)
    for p in modified[:10]:
        print("  ~ %s" % p)
    return 0 if ok else 2
    if empty:
        print("  Thư mục trống: %s" % ", ".join(empty))
    print("Đã ghi:", out)
    return 0


def cmd_report(args):
    from .indexer import scan_dir, dedupe_report
    import html as html_mod
    records = scan_dir(args.thu_muc, recursive=args.recursive)
    dupes = dedupe_report(records)
    cov_apk = getattr(args, "apk", None)
    rows = []
    n_khop = 0
    for idx, r in enumerate(records):
        n_sec = sum(r["sections"].values()) if r["sections"] else 0
        issues = "LỖI: " + r["parse_error"] if r["parse_error"] \
            else "; ".join(r["issues"]) if r["issues"] else ""
        dupe = "Nhóm %d" % r["dupe_id"] if r.get("dupe_id") else ""
        preview = ""
        cov_cell = "—"
        if cov_apk:
            from .parser import parse_patch_file
            from .advisor import coverage_patch
            try:
                p = parse_patch_file(os.path.join(args.thu_muc, r["path"]))
                cov = coverage_patch(p, cov_apk)
                cov_cell = "%s%% (%d)" % (cov.get("tỷ_lệ", 0),
                                          cov.get("quy_tắc_khớp", 0))
                if cov.get("quy_tắc_khớp", 0) > 0:
                    n_khop += 1
                rules = []
                for sec in p.sections:
                    m = sec.get("MATCH")
                    if not m:
                        continue
                    rules.append((m, sec.get("REPLACE") or ""))
                    if len(rules) >= 3:
                        break
                if rules:
                    lines = []
                    for m, rp in rules:
                        lines.append('<span class="del">- %s</span><br>'
                                     '<span class="add">+ %s</span>'
                                     % (html_mod.escape(str(m)[:300]),
                                        html_mod.escape(str(rp)[:300])))
                    preview = ("<h4>Preview diff (tối đa 3 quy tắc)</h4>"
                               "<pre>%s</pre>" % "<br>".join(lines))
            except Exception as e:
                preview = ("<p class='bad'>Lỗi đọc patch: %s</p>"
                           % html_mod.escape(str(e)))
        data = " ".join([r["name"], r["tag"] or "", r["author"] or "",
                         issues, dupe, cov_cell]).lower()
        rows.append(
            '<tr class="prow" data-s="%s"><td><button class="pv" '
            'onclick="tg(%d)">Xem</button> %s</td><td>%s</td><td>%s</td>'
            "<td>%s</td><td>%d</td><td>%d</td><td>%s</td><td>%s</td></tr>"
            '<tr id="pv%d" style="display:none"><td colspan="8">%s</td></tr>'
            % (html_mod.escape(data), idx, html_mod.escape(r["name"]),
               html_mod.escape(r["tag"] or "—"),
               html_mod.escape(r["engine_ver"] or "—"),
               html_mod.escape(r["author"] or "—"), n_sec,
               len(r["assets"]), dupe, cov_cell, idx, preview))
    dupe_rows = "".join(
        "<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            g["nhóm"], g["số_file"], g["bản_chuẩn"],
            ", ".join(g["bản_trùng"])) for g in dupes)
    total_size = sum(r["size"] for r in records)
    khop_line = ("<p>Khớp APK <code>%s</code>: <b>%d</b>/%d patch</p>"
                 % (html_mod.escape(cov_apk), n_khop, len(records))
                 if cov_apk else "")
    html = """<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8">
<title>patchx — Báo cáo bộ sưu tập</title>
<style>
body{font-family:system-ui,sans-serif;margin:24px;color:#222}
table{border-collapse:collapse;width:100%%;font-size:13px}
th,td{border:1px solid #ddd;padding:6px 8px;text-align:left}
th{background:#f2f2f2}h1{font-size:22px}h2{font-size:18px;margin-top:28px}
.bad{color:#b00020}.ok{color:#0a7d32}.del{color:#b00020}
.add{color:#0a7d32}pre{background:#fafafa;padding:8px;font-size:12px;
white-space:pre-wrap;word-break:break-all}
button.pv{font-size:11px;margin-right:6px;cursor:pointer}
input#q{width:100%%;padding:8px;font-size:14px;margin-bottom:12px;
box-sizing:border-box}
</style></head><body>
<h1>patchx — Báo cáo bộ sưu tập patch</h1>
<p>Thời gian: %s · Thư mục: <code>%s</code></p>
<p>Tổng: <b>%d</b> file · <b>%s</b> · <b>%d</b> nhóm trùng nội dung</p>
%s
<input id="q" placeholder="Tìm nhanh theo tên / nhóm / tác giả / vấn đề...">
<h2>Danh sách patch</h2>
<table><tr><th>Patch</th><th>Nhóm</th><th>Engine</th><th>Tác giả</th>
<th>Khối</th><th>Tài nguyên</th><th>Trùng</th><th>Độ phủ</th></tr>
%s</table>
<h2>Nhóm trùng nội dung</h2>
<table><tr><th>Nhóm</th><th>Số file</th><th>Bản chuẩn</th><th>Bản trùng</th></tr>
%s</table>
<script>
function tg(id){var el=document.getElementById('pv'+id);
if(el){el.style.display=el.style.display==='none'?'table-row':'none';}}
var q=document.getElementById('q');
if(q){q.addEventListener('input',function(){
var t=q.value.toLowerCase();
document.querySelectorAll('tr.prow').forEach(function(tr){
tr.style.display=tr.getAttribute('data-s').indexOf(t)>-1?'':'none';});});}
</script>
</body></html>""" % (
        time.strftime("%Y-%m-%d %H:%M:%S"), html_mod.escape(args.thu_muc),
        len(records), _fmt_size(total_size), len(dupes), khop_line,
        "".join(rows), dupe_rows)
    out = args.o or os.path.join(args.thu_muc, "_patchx", "report.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    print("[patchx] Đã tạo báo cáo HTML:", out)
    return 0


def _fmt_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return "%.1f %s" % (n, unit)
        n /= 1024.0
    return "%.1f TB" % n


def cmd_ci(args):
    """T7: dây chuyền CI — audit → upgrade → optimize → combo-auto →
    simulate, xuất báo cáo trước/sau."""
    from argparse import Namespace
    from .indexer import scan_dir, dedupe_report
    from .audit import audit_patch, LEVEL_ERROR, upgrade_zip
    from .simulate import run_simulation
    root = os.path.abspath(args.thu_muc)
    wd = args.o or os.path.join(root, "_patchx", "ci")
    os.makedirs(wd, exist_ok=True)
    t0 = time.monotonic()

    def stats(d):
        recs = scan_dir(d, recursive=True)
        n_err = 0
        for z in sorted(glob.glob(os.path.join(d, "*.zip"))):
            try:
                p = parse_patch_file(z)
                for f in audit_patch(p):
                    if f.level == LEVEL_ERROR:
                        n_err += 1
            except Exception:
                n_err += 1
        return {"files": len(recs),
                "size": sum(r["size"] for r in recs),
                "audit_lỗi": n_err,
                "nhóm_trùng": len(dedupe_report(recs))}

    before = stats(root)
    up = os.path.join(wd, "upgraded")
    os.makedirs(up, exist_ok=True)
    n_up = 0
    for z in sorted(glob.glob(os.path.join(root, "*.zip"))):
        try:
            upgrade_zip(z, up, dry_run=False,
                        header="Bản nâng cấp bởi CI patchx")
            n_up += 1
        except Exception:
            pass
    after_up = stats(up)
    opt = os.path.join(wd, "optimized")
    cmd_optimize(Namespace(thu_muc=up, o=opt))
    n_opt = len(glob.glob(os.path.join(opt, "*.patch")))
    cb = os.path.join(wd, "combos_auto")
    cmd_combo(Namespace(thu_muc=up, o=cb, auto=True, only=None,
                        recursive=False, apk=None))
    n_combo = len(glob.glob(os.path.join(cb, "*.patch")))
    sim = run_simulation(up, quick=args.quick, dex_runner=None,
                         dex_timeout=60, apk_tree=None)
    sim_s = {"đạt": sim["đạt"], "thất_bại": sim["thất_bại"],
             "bỏ_qua": sim["bỏ_qua"], "lỗi": sim["lỗi"],
             "tỷ_lệ_đạt": sim["tỷ_lệ_đạt"]}
    golden_rc = None
    if getattr(args, "golden", False):
        golden_rc = cmd_golden(Namespace(o=os.path.join(wd, "golden"), fw=True))
    total_s = round(time.monotonic() - t0, 1)
    report = {
        "thời_gian": time.strftime("%Y-%m-%d %H:%M:%S"),
        "thu_muc": root, "tổng_giây": total_s,
        "trước": before, "sau_nâng_cấp": after_up,
        "số_patch_nâng_cấp": n_up,
        "số_tệp_optimize": n_opt, "số_combo_tự_động": n_combo,
        "simulate": sim_s,
        "golden_gate": (0 if golden_rc == 0 else 1) if golden_rc is not None else None,
    }
    with open(os.path.join(wd, "ci_report.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    lines = ["# Báo cáo CI patchx", "",
             "- Thời gian: %s" % report["thời_gian"],
             "- Thư mục: `%s`" % root,
             "- Tổng thời gian: %s giây" % total_s, "",
             "## Trước (kho gốc)",
             "- File: %(files)d · Dung lượng: %(size)d byte · "
             "Lỗi audit: %(audit_lỗi)d · Nhóm trùng: %(nhóm_trùng)d"
             % before, "",
             "## Sau (upgrade → optimize → combo)",
             "- File sau nâng cấp: %(files)d · Lỗi audit: %(audit_lỗi)d · "
             "Nhóm trùng: %(nhóm_trùng)d" % after_up,
             "- Patch nâng cấp: %d · Tệp optimize: %d · Combo tự động: %d"
             % (n_up, n_opt, n_combo), "",
             "## Mô phỏng (bộ nâng cấp)",
             "- ĐẠT %(đạt)d · THẤT-BẠI %(thất_bại)d · BỎ-QUA %(bỏ_qua)d · "
             "LỖI %(lỗi)d · Tỷ lệ đạt %(tỷ_lệ_đạt)s%%" % sim_s, ""]
    with open(os.path.join(wd, "ci_report.md"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write("\n".join(lines))
    print("[patchx] CI: %d file → %d file, lỗi audit %d → %d, "
          "%d combo, mô phỏng %d%% đạt (%.1fs)" % (
              before["files"], after_up["files"], before["audit_lỗi"],
              after_up["audit_lỗi"], n_combo, sim["tỷ_lệ_đạt"], total_s))
    print("Đã ghi:", os.path.join(wd, "ci_report.md"))
    ok = after_up["audit_lỗi"] == 0 and sim["thất_bại"] == 0
    if golden_rc is not None:
        ok = ok and golden_rc == 0
    return 0 if ok else 2


def cmd_golden(args):
    """P10 — Golden Build gate: chỉ chạy hai golden test, trả 1 nếu fail."""
    import importlib.util
    test_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "tests", "run_tests.py")
    if getattr(args, "fw", False):
        os.environ["PATCHX_GOLDEN_FW"] = "1"
    spec = importlib.util.spec_from_file_location("patchx_golden_tests",
                                                   test_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    start = len(mod.RESULTS)
    mod.test_golden_rebuild()
    mod.test_golden_framework_res()
    checks = mod.RESULTS[start:]
    ok = sum(1 for _, passed, _ in checks if passed)
    total = len(checks)
    report = {
        "thời_gian": time.strftime("%Y-%m-%d %H:%M:%S"),
        "golden_build_pass": ok,
        "golden_build_total": total,
        "chi_tiết": [{"tên": name, "đạt": bool(passed), "chi_tiết": detail}
                     for name, passed, detail in checks],
    }
    out_dir = args.o or os.path.join(BASE_DIR, "toolkit_out")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "golden_gate.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    for name, passed, detail in checks:
        print("  [%s] %s — %s" % ("PASS" if passed else "FAIL", name,
                                  detail or ""))
    print("[patchx] Golden gate: %d/%d đạt — %s" % (
        ok, total, "PASS" if ok == total else "FAIL"))
    return 0 if ok == total else 1


def cmd_validate(args):
    """P9 — Xác thực cây APK đã giải mã: smali/XML/manifest/DEX theo mức.

    FAST → smali; NORMAL → +manifest; FULL → +XML+DEX; RELEASE → chặn cả
    cảnh báo. Trả 0 nếu sạch, 1 nếu có lỗi.
    """
    from patchx_core.smali_validate import validate_file, validate_tree_v2

    if not args.cay:
        print("[patchx] Thiếu cây APK đã giải mã.")
        return 2
    if not os.path.isdir(args.cay):
        print("[patchx] Không phải thư mục cây: %s" % args.cay)
        return 2
    if args.files:
        bad = 0
        for rel in args.files:
            p = os.path.join(args.cay, rel)
            if not os.path.isfile(p):
                print("[FAIL] %s: không tồn tại" % rel)
                bad += 1
                continue
            with open(p, encoding="utf-8", errors="replace") as fh:
                errs, _nm = validate_file(fh.read())
            if errs:
                print("[FAIL] %s: %s" % (rel, "; ".join(errs)))
                bad += 1
            else:
                print("[PASS] %s" % rel)
        return 1 if bad else 0
    t0 = time.monotonic()
    r = validate_tree_v2(args.cay, level=args.level,
                         changed_only=args.changed_only,
                         max_files=getattr(args, "max_files", None))
    secs = time.monotonic() - t0
    print("[patchx] Xác thực [%s]: %d/%d tệp, %d method, "
          "%d lỗi, %d cảnh báo (%.1fs)%s"
          % (r["level"], r["files"], r["files"], r["methods"],
             len(r["errors"]), len(r["warnings"]), secs,
             " — chỉ tệp đổi mới" if args.changed_only else ""))
    shown = 0
    for f in r["findings"]:
        if f["mức"] != "lỗi" and args.level == "RELEASE":
            pass
        if shown >= args.limit:
            break
        shown += 1
        print("[%s] %s%s: %s"
              % ("FAIL" if f["mức"] == "lỗi" else "WARN",
                 f["loại"], (" " + f["path"]) if f["path"] else "",
                 f["nội_dung"]))
    if len(r["findings"]) > shown:
        print("[patchx] … còn %d finding nữa"
              % (len(r["findings"]) - shown))
    if r["errors"]:
        print("[patchx] %d lỗi (hiện %d)"
              % (len(r["errors"]), min(args.limit, shown)))
        return 1
    return 0


def cmd_apk_prepare(args):
    import shutil as _sh
    apktool = _sh.which("apktool")
    if not apktool:
        print("[patchx] Thiếu công cụ apktool — cài bằng: pkg install apktool")
        return 0
    out = args.o or args.apk + ".decoded"
    os.makedirs(out, exist_ok=True)
    print("[patchx] Giải mã APK bằng apktool (có thể mất vài phút)...")
    cmd = [apktool, "d", "-f", "-o", out, args.apk]
    try:
        subprocess.run(cmd, check=True, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        print("[patchx] apktool quá thời gian (%ss)" % args.timeout)
        return 1
    except (OSError, subprocess.CalledProcessError) as e:
        print("[patchx] apktool thất bại: %s" % e)
        return 1
    print("[patchx] Đã giải mã vào:", out)
    try:
        import hashlib as _hl
        cdir = os.path.join(out, ".patchx", "cache")
        os.makedirs(cdir, exist_ok=True)
        sha = _hl.sha256()
        with open(args.apk, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                sha.update(chunk)
        with open(os.path.join(cdir, "decode.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"apk_sha256": sha.hexdigest(),
                       "apk": os.path.abspath(args.apk),
                       "time": time.strftime("%Y-%m-%d %H:%M:%S")},
                      fh, ensure_ascii=False, indent=1)
    except OSError as e:
        print("[patchx] Cảnh báo: không ghi được cache decode: %s" % e)
    return 0


def cmd_audit(args):
    patches = _load_patches(args.thu_muc, recursive=args.recursive)
    out = []
    lines = ["# Báo cáo kiểm tra kiến trúc patch", "",
             "- Thời gian: %s" % time.strftime("%Y-%m-%d %H:%M:%S"),
             "- Số patch: %d" % len(patches), ""]
    n_err = n_warn = n_fix = 0
    for p in patches:
        findings = audit_patch(p)
        rec = {"patch": p.name, "source": p.source, "findings":
               [f.to_dict() for f in findings]}
        out.append(rec)
        lines.append("## %s" % p.name)
        if not findings:
            lines.append("- Không phát hiện vấn đề.")
        for f in findings:
            lines.append("- [%s] %s — %s%s" % (
                f.code, {"lỗi": "LỖI", "cảnh-báo": "CẢNH BÁO",
                         "thông-tin": "thông tin"}[f.level],
                f.message, " (tự sửa được)" if f.fixable else ""))
            if f.level == LEVEL_ERROR:
                n_err += 1
            elif f.level == LEVEL_WARN:
                n_warn += 1
            if f.fixable:
                n_fix += 1
        lines.append("")
    lines.insert(3, "- Lỗi: %d, cảnh báo: %d, vấn đề tự sửa được: %d"
                 % (n_err, n_warn, n_fix))
    out_dir = args.o or os.path.dirname(os.path.abspath(args.thu_muc))
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, "audit")
    with open(base + ".json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "total": len(patches), "errors": n_err,
                   "warnings": n_warn, "fixable": n_fix,
                   "patches": out}, fh, ensure_ascii=False, indent=2)
    with open(base + "_report.md", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print("Đã ghi:", base + ".json")
    print("Đã ghi:", base + "_report.md")


def cmd_upgrade(args):
    out_dir = args.o or os.path.join(args.thu_muc, "_patchx", "upgraded")
    header = ("Bản nâng cấp bởi patchx %s — chuẩn hóa kiến trúc, "
              "nội dung giữ nguyên gốc" % __version__)
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for z in sorted(glob.glob(os.path.join(args.thu_muc, "*.zip"))):
        try:
            res = upgrade_zip(z, out_dir, dry_run=args.dry_run, header=header)
            for src, patch, out_name in res:
                results.append({"source": src, "output": out_name,
                                "sections": len(patch.sections)})
                print("[patchx] %s -> %s (%d khối)" % (
                    os.path.basename(src), out_name, len(patch.sections)))
        except Exception as e:
            print("[patchx] LỖI khi nâng cấp %s: %s"
                  % (os.path.basename(z), e))
    if not args.dry_run:
        with open(os.path.join(out_dir, "upgrade_summary.json"), "w",
                  encoding="utf-8", newline="\n") as fh:
            json.dump({"generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "total": len(results), "results": results},
                      fh, ensure_ascii=False, indent=2)
        print("Đã nâng cấp %d patch vào %s" % (len(results), out_dir))
    else:
        print("(dry-run) Sẽ nâng cấp %d patch vào %s" % (len(results), out_dir))


def _components(patches):
    """Gói các patch KHÔNG xung đột vào cùng một nhóm (xung đột phải tách)."""
    conflicts = find_conflicts(patches)
    conf_sets = [set(c["patches"]) for c in conflicts]

    def clashes(p, group):
        for q in group:
            for cs in conf_sets:
                if p.name in cs and q.name in cs:
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


def cmd_optimize(args):
    from .optimizer import target_similarity
    patches = _load_patches(args.thu_muc)
    by_tag = {}
    for p in patches:
        by_tag.setdefault(cluster_tag(p.name), []).append(p)

    # Bước 1: chia thành phần không xung đột theo từng nhóm
    components = []
    conflicts_all = []
    for tag, group in sorted(by_tag.items()):
        comps, conflicts = _components(group)
        for comp in comps:
            components.append({"tag": tag, "patches": comp})
        conflicts_all.extend(conflicts)

    # Bước 2: ưu tiên gộp chéo các nhóm giống nhau (cùng target + cùng MATCH),
    # nhưng KHÔNG bao giờ gộp hai nhóm có xung đột chung
    global_conflicts = find_conflicts(patches)
    global_conf_sets = [set(c["patches"]) for c in global_conflicts]

    def clash(a, b):
        na = {p.name for p in a["patches"]}
        nb = {p.name for p in b["patches"]}
        return any((na & cs) and (nb & cs) for cs in global_conf_sets)

    merged_any = True
    merge_pairs = []
    while merged_any:
        merged_any = False
        best = None
        for i in range(len(components)):
            for j in range(i + 1, len(components)):
                if clash(components[i], components[j]):
                    continue
                sim = target_similarity(components[i]["patches"],
                                        components[j]["patches"])
                if sim >= 0.7 and (best is None or sim > best[0]):
                    best = (sim, i, j)
        if best:
            sim, i, j = best
            merge_pairs.append("%s + %s (độ tương đồng %.0f%%)" % (
                components[i]["tag"], components[j]["tag"], sim * 100))
            components[i]["patches"].extend(components[j]["patches"])
            components[i]["tag"] += "+" + components[j]["tag"]
            components.pop(j)
            merged_any = True

    out_dir = args.o or os.path.join(args.thu_muc, "_patchx", "optimized")
    os.makedirs(out_dir, exist_ok=True)
    total_in = sum(len(c["patches"]) for c in components)
    total_rules_in = 0
    saved_rules = 0
    stats = {"patches": total_in, "files": [], "merged_across_groups":
             merge_pairs, "saved_rules": 0}
    used_names = {}
    for idx, comp in enumerate(components, 1):
        tag = comp["tag"]
        merged = merge_patches(comp["patches"], tag)
        rules_in = sum(1 for p in comp["patches"] for s in p.sections
                       if s.type not in ("MIN_ENGINE_VER", "AUTHOR", "PACKAGE"))
        total_rules_in += rules_in
        rules_out = len(merged.sections)
        saved = rules_in - rules_out
        saved_rules += saved
        base = tag + ".patch"
        used_names[base] = used_names.get(base, 0) + 1
        if used_names[base] > 1:
            fname = "%s_%d.patch" % (tag, used_names[base])
        else:
            fname = base
        fpath = os.path.join(out_dir, fname)
        with open(fpath, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_patch_text(merged, header=(
                "Gộp tối ưu bởi patchx: %s" % tag)))
        stats["files"].append({
            "input_patches": len(comp["patches"]),
            "rules_in": rules_in, "rules_out": rules_out,
            "saved_rules": saved,
            "file": fname,
            "source_patches": [p.name for p in comp["patches"]]})
        print("[patchx] %s -> %s (%d khối từ %d patch, gộp trùng %d)" % (
            tag, fname, rules_out, len(comp["patches"]), saved))
    stats["saved_rules"] = saved_rules
    stats["conflicts"] = len(conflicts_all)
    if conflicts_all:
        with open(os.path.join(out_dir, "_conflicts.json"), "w",
                  encoding="utf-8", newline="\n") as fh:
            json.dump(conflicts_all, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "_stats.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=2)
    print("Đã gộp %d patch -> %d tệp, gộp trùng %d khối, %d xung đột tách riêng"
          % (total_in, len(components), saved_rules, len(conflicts_all)))
    if merge_pairs:
        print("Gộp chéo nhóm giống nhau (%d cặp):" % len(merge_pairs))
        for m in merge_pairs[:12]:
            print("  - " + m)
        if len(merge_pairs) > 12:
            print("  ... và %d cặp nữa" % (len(merge_pairs) - 12))


def cmd_apply(args):
    patches = [parse_patch_file(p) for p in args.patch]
    engine = Engine(args.cay_apk, dry_run=args.dry_run, backup=not args.no_backup,
                    force=args.force, no_dex=not args.dex_runner,
                    dex_runner=args.dex_runner, strict=args.strict,
                    quiet=args.quiet, reset_state=args.reset_state,
                    dex_allow_extra=args.dex_allow or ())
    for p in patches:
        print("[patchx] Áp patch: %s" % p.name)
        engine.apply(p)
    engine.finalize()
    if engine.errors and args.strict:
        return 1
    return 0


def cmd_test(args):
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    tests = os.path.join(here, "..", "tests", "run_tests.py")
    spec = importlib.util.spec_from_file_location("run_tests", tests)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main()


def cmd_dex_budget(args):
    """P5 — DEX Resource Manager: ước lượng refs + mức an toàn."""
    from .dex_budget import DEX_METHOD_MAX, budget_report, strategy_for
    from .parser import parse_patch_file, parse_text
    sections = []
    if getattr(args, "patch", None):
        p = parse_patch_file(args.patch) if os.path.isfile(args.patch) \
            else parse_text(open(args.patch, encoding="utf-8").read())
        sections = p.sections
    rep = budget_report(args.cây, sections=sections,
                        max_refs=getattr(args, "max", None) or DEX_METHOD_MAX,
                        max_files=getattr(args, "max_files", None),
                        workers=getattr(args, "workers", 1) or 1)
    u = rep["used"]
    print("[dex-budget] %s" % args.cây)
    print("  files  : %d tệp smali" % u["files"])
    print("  classes: %d" % u["classes"])
    print("  methods: %d (used)" % u["methods"])
    print("  fields : %d" % u["fields"])
    print("  strings: %d" % u["strings"])
    print("  delta  : %+d method refs (patch: %d khối)"
          % (rep["delta"], len(sections)))
    if rep["per_type"]:
        print("  theo loại:", "; ".join(
            "%s %+d" % (t, d) for t, d in sorted(rep["per_type"].items())))
    print("  tổng   : %d / %d" % (rep["total"], rep["max_refs"]))
    print("  còn lại: %d" % rep["remaining"])
    print("  MỨC    : %s" % rep["level"])
    st = strategy_for(rep)
    print("  CHIẾN LƯỢC: %s (risk=%s, confidence=%d%%)"
          % (st["strategy"], st["risk"], st["confidence"]))
    print("  lý do  : %s" % st["reason"])
    return 0 if rep["level"] in ("SAFE", "WATCH") else 1


def cmd_preflight(args):
    """P7 — Preflight: cổng kiểm tra trước khi áp patch."""
    from .parser import parse_patch_file, parse_text
    from .preflight import preflight_patch
    src = args.patch
    p = parse_patch_file(src) if os.path.isfile(src) else \
        parse_text(open(src, encoding="utf-8").read())
    rep = preflight_patch(p, args.cây,
                          max_files=getattr(args, "max_files", None))
    print("[preflight] %s → %s" % (p.name, rep["verdict"]))
    for c in rep["checks"]:
        print("  [%s] %s: %s" % (c["mức"], c["loại"], c["nội_dung"]))
    print("  %s" % rep["summary"])
    return 0 if rep["verdict"] in ("READY", "READY_WITH_WARNING") else 2


def cmd_fuzz(args):
    """P12 — Fuzz/Chaos: tấn công parser + engine bằng dữ liệu ngẫu nhiên."""
    from .fuzz import run_fuzz
    rep = run_fuzz(iterations=args.iter, seed=args.seed,
                   workdir=args.workdir)
    print("[fuzz] %d lượt (seed=%d): %s"
          % (rep["iterations"], rep["seed"],
             "SẠCH" if rep["ok"] else "CÓ VẤN ĐỀ"))
    for tag, item, detail in rep["crashes"][:10]:
        print("  [CRASH] %s %s: %s" % (item, tag, detail))
    for tag, item, detail in rep["violations"][:10]:
        print("  [VIOLATION] %s %s: %s" % (item, tag, detail))
    if len(rep["crashes"]) + len(rep["violations"]) > 10:
        print("  … còn %d vấn đề nữa"
              % (len(rep["crashes"]) + len(rep["violations"]) - 10))
    return 0 if rep["ok"] else 1




def cmd_failure(args):
    """P15 — Failure Intelligence: DB lỗi, phân loại, sinh regression test."""
    from .failure_db import (add_failure, classify_failure, gen_regression_test,
                             load_db, render_report, save_db)
    act = args.hành_động
    if act == "list":
        entries = load_db(args.db)
        print("%d lỗi trong DB:" % len(entries))
        for e in entries:
            print("  %-12s %-12s %s" % (e.get("error_id"), e.get("stage"),
                                        (e.get("pattern") or "")[:70]))
        return 0
    if act == "report":
        print(render_report(args.db))
        return 0
    if act == "lookup":
        if not args.message:
            print("Cần --message để tra cứu.")
            return 2
        hit = classify_failure(args.message, stage=args.stage, db_path=args.db)
        if not hit:
            print("[failure] Không tìm thấy entry khớp.")
            return 1
        print("ERROR_ID : %s" % hit.get("error_id"))
        print("STAGE    : %s" % hit.get("stage"))
        print("PATTERN  : %s" % hit.get("pattern"))
        print("NGUYÊN NHÂN: %s" % hit.get("cause"))
        print("XỬ LÝ    : %s" % hit.get("fix"))
        print("REGRESSION: %s" % hit.get("regression"))
        return 0
    if act == "add":
        entry = {"error_id": args.error_id, "stage": args.stage or "",
                 "pattern": args.pattern, "cause": args.cause or "",
                 "fix": args.fix or "", "regression": args.regression or ""}
        added, path = add_failure(entry, args.db)
        print("[failure] Đã thêm %s → %s" % (added["error_id"], path))
        return 0
    if act == "gen-regression":
        hit = None
        if args.error_id:
            for e in load_db(args.db):
                if e.get("error_id") == args.error_id:
                    hit = e
                    break
        elif args.message:
            hit = classify_failure(args.message, stage=args.stage,
                                   db_path=args.db)
        if not hit:
            print("Cần --error-id (hoặc --message) để sinh test.")
            return 2
        src = gen_regression_test(hit, args.test_name)
        if args.out:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)),
                        exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(src)
            print("[failure] Đã ghi %s" % args.out)
        else:
            print(src)
        return 0
    print("Hành động không hợp lệ: %s" % act)
    return 2


def cmd_baseline(args):
    """PHASE 0 — Baseline: chụp, xem, so sánh và chặn hồi quy."""
    from .baseline import (METRICS, capture_metrics, compare_metrics,
                           capture_full, load_metrics, render_compare,
                           write_baseline, run_compare, DEFAULT_BASELINE_DIR)
    bdir = getattr(args, "dir", None) or DEFAULT_BASELINE_DIR
    if args.hành_động == "capture":
        overrides = {}
        for kv in (getattr(args, "set", None) or []):
            if "=" in kv:
                k, v = kv.split("=", 1)
                overrides[k.strip()] = v.strip()
        if getattr(args, "full", False):
            metrics, env = capture_full(overrides, bdir)
            from .baseline import save_metrics
            mpath = save_metrics(os.path.join(bdir, "metrics.json"), metrics)
            with open(os.path.join(bdir, "environment.json"), "w",
                      encoding="utf-8", newline="\n") as fh:
                json.dump(env, fh, ensure_ascii=False, indent=2)
        else:
            mpath = write_baseline(bdir, overrides)
            metrics, env = capture_metrics(overrides, bdir)
        print("[patchx] Đã chụp baseline: %s" % mpath)
        print("  Môi trường: %s · Python %s · load %s" % (
            env.get("machine", "?"), env.get("python", "?"),
            env.get("loadavg_1_5_15")))
        for k, v in metrics.items():
            if v is not None:
                meta = METRICS[k]
                print("  %-18s %s %s (%s)" % (k, v, meta["unit"],
                                              meta["name"]))
        return 0
    if args.hành_động == "show":
        metrics = load_metrics(__import__("os").path.join(bdir,
                                                          "metrics.json"))
        if not metrics:
            print("[patchx] Chưa có baseline — chạy: patchx baseline capture")
            return 1
        for k, v in metrics.items():
            if v is not None:
                meta = METRICS[k]
                print("%-18s %s %s (%s)" % (k, v, meta["unit"], meta["name"]))
        return 0
    if args.hành_động == "compare":
        verdict, result = run_compare(args.metrics_mới, bdir)
        print(render_compare(result))
        print("[patchx] Cổng hồi quy: %s" % verdict)
        import json as _json
        with open(__import__("os").path.join(bdir, "compare_latest.json"),
                  "w", encoding="utf-8", newline="\n") as fh:
            _json.dump(result, fh, ensure_ascii=False, indent=2)
        return 0 if verdict == "ACCEPT" else 1
    return 1

def cmd_coverage(args):
    from .advisor import coverage_patch
    from .smali_sem import find_method_matches
    patch = parse_patch_file(args.patch)
    cov = coverage_patch(patch, args.cay_apk, mode=args.mode)
    print("[patchx] %s (mode %s): %d/%d quy tắc khớp, %d lần khớp" % (
        patch.name, cov["mode"], cov["quy_tắc_khớp"], cov["quy_tắc"], sum(
            d["khớp"] for d in cov["chi_tiết"])))
    for d in cov["chi_tiết"]:
        print("  khối %d (%s) target=%s: %d khớp%s" % (
            d["khối"], d["loại"], d["target"] or "<rỗng>", d["khớp"],
            "  TRƯỢT: " + ", ".join(d["tệp_trượt"][:5])
            if d["tệp_trượt"] and not d["khớp"] else ""))
        for v in d["biến_thể"][:3]:
            print("    - đề xuất mở rộng: " + v)
        if getattr(args, "method", False) and d["khớp"]:
            # Mức method: đọc từng tệp khớp, tìm method chứa mẫu
            sec = next((s for s in patch.sections
                        if s.order == d["khối"]), None)
            if sec is None:
                continue
            pat = (sec.get("MATCH") or "").strip()
            is_regex = sec.get("REGEX", "").strip().lower() in ("true", "1")
            for tf in d.get("tệp_trúng", [])[:10]:
                tpath = os.path.join(args.cay_apk, tf)
                if not os.path.isfile(tpath):
                    continue
                try:
                    text = open(tpath, encoding="utf-8",
                                errors="replace").read()
                except OSError:
                    continue
                for mm in find_method_matches(text, pat, is_regex)[:5]:
                    print("      method %s (dòng %d): %d lần" % (
                        mm["method"], mm["line"], mm["lần"]))
    if args.o:
        with open(args.o, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(cov, fh, ensure_ascii=False, indent=2)
        print("Đã ghi:", args.o)
    return 0


def cmd_suggest(args):
    from .advisor import suggest_patch
    from .risk import risk_findings
    patch = parse_patch_file(args.patch)
    items = suggest_patch(patch, args.cay_apk)
    risks = risk_findings(patch)
    print("[patchx] %d đề xuất cho %s:" % (len(items), patch.name))
    for it in items:
        print("  [%s] %s" % (it["mức"], it["nội_dung"]))
        print("        lý do: %s" % it["lý_do"])
    if risks:
        print("  ⚠ Cờ rủi ro (T5): %d" % len(risks))
        for r in risks:
            print("    - [%s] %s (khối %d)" % (
                r["loại"], r["nội_dung"], r["khối"]))
    if args.o:
        with open(args.o, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"patch": patch.name, "suggestions": items,
                       "risks": risks},
                      fh, ensure_ascii=False, indent=2)
        print("Đã ghi:", args.o)
    return 0


def cmd_analyze(args):
    """Phân tích ngữ nghĩa cây APK (trục T1): packer, mã hóa chuỗi,
    entry classes, call-graph xếp hạng target."""
    from .smali_sem import build_semantic_report
    report = build_semantic_report(args.cay_apk, top=args.top)
    print("[patchx] Phân tích ngữ nghĩa: %s" % args.cay_apk)
    print("  Application: %s" % (report["application"] or "(không khai báo)"))
    if report["launchers"]:
        print("  Launcher: %s" % ", ".join(report["launchers"]))
    if report["packers"]:
        print("  ⚠ Packer phát hiện: %d" % len(report["packers"]))
        for pk in report["packers"][:8]:
            print("    - %s (%s) — %s" % (pk["nghi_ngờ"], pk["tệp"],
                                          pk["đường_dẫn"]))
    else:
        print("  Packer: không phát hiện")
    if report["string_encryption_suspects"]:
        print("  ⚠ Nghi mã hóa chuỗi: %d tệp" % len(
            report["string_encryption_suspects"]))
        for s in report["string_encryption_suspects"][:8]:
            print("    - %s (điểm %d)" % (s["tệp"], s["điểm"]))
    else:
        print("  Mã hóa chuỗi: không phát hiện")
    print("  Call-graph top %d (từ entry):" % len(report["call_graph_top"]))
    for c in report["call_graph_top"][:10]:
        print("    - %s (%d lần)" % (c["class"], c["lần"]))
    print("  %s" % report["gợi_ý_điểm_chèn"])
    if args.o:
        with open(args.o, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
        print("Đã ghi:", args.o)
    return 0


def cmd_model(args):
    """Tạo mô hình ứng dụng trung gian, không thay đổi cây APK.

    Đây là điểm vào của kiến trúc mục tiêu + điều kiện: plan/preflight sẽ đọc
    JSON này thay vì quyết định chỉ từ một mẫu văn bản hoặc tên method.
    """
    import time
    from .smali_sem import build_app_model, build_app_model_v2
    builder = build_app_model_v2 if args.v2 else build_app_model
    start = time.time()
    report = builder(args.cay_apk, include_bodies=args.with_bodies)
    elapsed = time.time() - start
    s = report["summary"]
    extra = (", %d method từ entry" % s["reachable_from_entry"]
             if args.v2 else ", %d nguồn dữ liệu" % s["data_sources"])
    print("[patchx] Mô hình ứng dụng %s: %d method, %d cạnh gọi, %d điểm quyết định%s" % (
        "V2" if args.v2 else "V1", s["methods"], s["call_edges"],
        s["decision_points"], extra))
    if args.bench:
        print("[patchx] model %s cache lạnh: %.3f giây" % (
            "V2" if args.v2 else "V1", elapsed))
        return 0
    default_name = "app_model_v2.json" if args.v2 else "app_model.json"
    out = args.o or os.path.join(args.cay_apk, ".patchx", default_name)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("Đã ghi:", out)
    return 0


def cmd_semantic_plan(args):
    """Đánh giá kế hoạch mục tiêu+điều kiện trên mô hình APK, chỉ-đọc."""
    from .semantic_plan import (SCHEMA_V2, evaluate_plan, evaluate_plan_v2,
                                load_plan, suggest_selector_fix)
    from .smali_sem import build_app_model, build_app_model_v2
    plan = load_plan(args.ke_hoach)
    is_v2 = plan.get("schema") == SCHEMA_V2
    if args.model:
        with open(args.model, encoding="utf-8") as fh:
            model = json.load(fh)
    else:
        model = build_app_model_v2(args.cay_apk) if is_v2 else build_app_model(args.cay_apk)
    result = evaluate_plan_v2(plan, model) if is_v2 else evaluate_plan(plan, model)
    print("[patchx] Kế hoạch ngữ nghĩa: %s — %s" % (
        result["goal"], result["verdict"]))
    for target in result["targets"]:
        threshold = (target["policy"]["min_score"] if is_v2
                     else target["min_score"])
        suffix = " — MƠ HỒ, đã chặn" if target.get("ambiguous") else ""
        print("  %s: %d ứng viên đạt ngưỡng %.0f%%%s" % (
            target["name"], len(target["accepted"]), threshold, suffix))
        for candidate in target["accepted"][:5]:
            print("    - %s (%s:%d, %.1f%%)" % (
                candidate["method"], candidate["file"], candidate["line"],
                candidate["score"]))
        if getattr(args, "verbose", False):
            for candidate in target.get("rejected", [])[:5]:
                print("    x %s (%s:%d, %.1f%%) — thiếu: %s" % (
                    candidate["method"], candidate["file"], candidate["line"],
                    candidate["score"], ", ".join(candidate.get("missing", []))))
        elif target.get("rejected"):
            print("    (%d ứng viên dưới ngưỡng — dùng --verbose để xem lý do)"
                  % len(target["rejected"]))
    if result["verdict"] == "READY_FOR_PREFLIGHT":
        print("  Bước kế: người dùng duyệt thao tác → preflight → simulate/build.")
    elif result["verdict"] == "AMBIGUOUS_TARGET":
        print("  Không tự chọn mục tiêu: cần siết selector hoặc người dùng chọn ứng viên.")
    elif result["verdict"] == "INSUFFICIENT_EVIDENCE":
        print("  Thiếu evidence: cần sinh app-model/v2 trước khi đánh giá lại.")
    else:
        print("  Không tự áp thay đổi: cần bổ sung điều kiện hoặc APK mẫu.")
    if result["verdict"] != "READY_FOR_PREFLIGHT":
        if is_v2:
            for tip in suggest_selector_fix(plan, result):
                print("  Gợi ý cải thiện [%s] %s:" % (tip["target"], tip["kind"]))
                if tip.get("common_missing"):
                    print("    - thiếu chung: %s" % ", ".join(tip["common_missing"]))
                for line in tip.get("advice", []):
                    print("    - %s" % line)
        from .failure_db import classify_failure
        failure = classify_failure(result["verdict"], stage="PLAN")
        if failure:
            print("  Phân loại lỗi: %s — %s" % (
                failure["error_id"], failure["fix"]))
    if args.o:
        with open(args.o, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)
        print("Đã ghi:", args.o)
    return 0 if result["verdict"] == "READY_FOR_PREFLIGHT" else 2


def cmd_acceptance(args):
    """Chạy tiêu chí nghiệm thu V2 trên fixture có acceptance.json (chỉ đọc)."""
    from .acceptance import run_acceptance
    report = run_acceptance(args.fixture)
    m = report["metrics"]
    print("[patchx] Nghiệm thu V2: %s" % report["fixture"])
    print("  Tái lập model      : %.2f%% (%d/%d)" % (
        report["reproducibility"]["rate"],
        report["reproducibility"]["same"],
        report["reproducibility"]["total"]))
    if report["reidentification_rate"] is not None:
        print("  Tái nhận diện      : %.2f%%" % report["reidentification_rate"])
    variants = report.get("reidentification_variants", {})
    for name, rate in sorted(variants.items()):
        print("    Biến thể %-12s: %.2f%%" % (name, rate))
    if m["ready_total"]:
        print("  READY đúng         : %d/%d (%.2f%%)" % (
            m["ready_ok"], m["ready_total"], m["ready_rate"]))
        print("  Dương tính giả     : %.2f%%" % m["false_positive_rate"])
    if m["ambiguity_total"]:
        print("  Mơ hồ bị chặn      : %d/%d (%.2f%%)" % (
            m["ambiguity_blocked"], m["ambiguity_total"], m["ambiguity_rate"]))
    if m["no_confident_total"]:
        print("  Không tự tin bị chặn: %d/%d" % (
            m["no_confident_blocked"], m["no_confident_total"]))
    if args.o:
        with open(args.o, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
        print("Đã ghi:", args.o)
    return 0


def cmd_knowledge(args):
    """Kho tri thức: chỉ lưu outcome đã verified hoặc tìm bằng chứng tương tự."""
    from .knowledge import (load_store, query_similar, query_similar_v2,
                            record_verified, suggest_plan_v2)
    if args.hành_động == "record":
        with open(args.record, encoding="utf-8") as fh:
            record = json.load(fh)
        added, total = record_verified(args.db, record)
        print("[knowledge] %s — kho có %d bản ghi" % (
            "Đã ghi outcome đã nghiệm thu" if added else "Bản ghi đã tồn tại", total))
        return 0
    if args.hành_động == "query":
        from .smali_sem import build_app_model, build_app_model_v2
        model = build_app_model_v2(args.cay_apk) if args.v2 else build_app_model(args.cay_apk)
        rows = (query_similar_v2(args.db, model, goal=args.goal, limit=args.top)
                if args.v2 else query_similar(args.db, model, goal=args.goal, limit=args.top))
        print("[knowledge] %d trường hợp tương tự đã verified" % len(rows))
        for row in rows:
            record = row["record"]
            print("  - %s | %s | %s → %s (%s:%d)%s" % (
                record["app"]["package"], record.get("app", {}).get("version", "—"),
                record["goal"], record["outcome"], row["file"], row["line"],
                " — %.0f%%, %s" % (row["confidence"], ",".join(row["identity_matches"]))
                if args.v2 else ""))
        print("  Kết quả chỉ là tham chiếu; vẫn cần semantic-plan + preflight.")
        return 0
    if args.hành_động == "suggest-plan":
        from .smali_sem import build_app_model_v2
        model = build_app_model_v2(args.cay_apk)
        plan = suggest_plan_v2(args.db, model, goal=args.goal, limit=args.top)
        if not plan:
            print("[knowledge] Không có ứng viên verified tương tự cho APK này.")
            return 2
        with open(args.o, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(plan, fh, ensure_ascii=False, indent=2)
        print("[knowledge] Đã sinh semantic-plan/V2 tham chiếu: %s (%d target)" % (
            args.o, len(plan["targets"])))
        print("  Chỉ là ứng viên từ kho tri thức; hãy chạy `patchx semantic-plan` "
              "trên APK này và người dùng duyệt trước preflight.")
        return 0
    print("[knowledge] %d bản ghi" % len(load_store(args.db)))
    return 0


def cmd_plan_compile(args):
    """Tạo transaction nháp từ plan V2 đã chọn; không gọi Engine.apply."""
    from .semantic_plan import load_plan
    from .smali_sem import build_app_model_v2
    from .plan_compile import compile_plan_v2
    plan = load_plan(args.ke_hoach)
    if plan.get("schema") != "patchx.semantic-plan/v2":
        raise ValueError("plan-compile chỉ nhận patchx.semantic-plan/v2")
    model = build_app_model_v2(args.cay_apk)
    draft = compile_plan_v2(plan, model, args.cay_apk)
    os.makedirs(os.path.dirname(os.path.abspath(args.o)), exist_ok=True)
    with open(args.o, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(draft, fh, ensure_ascii=False, indent=2)
    print("[patchx] Transaction nháp: %s (%d target, hash evidence đã khóa)" %
          (args.o, len(draft["selected_targets"])))
    print("  Không áp APK. Bước sau: người dùng duyệt → preflight.")
    return 0


def cmd_plan_preflight(args):
    from .plan_compile import revalidate_draft
    with open(args.draft, encoding="utf-8") as fh:
        draft = json.load(fh)
    report = revalidate_draft(draft, args.cay_apk)
    suffix = " — đã đánh giá lại plan" if report.get("recompiled") else ""
    print("[patchx] Draft evidence: %s — %s%s" % (
        report["status"], report["reason"], suffix))
    if report.get("recompiled") and getattr(args, "o", None):
        with open(args.o, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report["draft"], fh, ensure_ascii=False, indent=2)
        print("Đã ghi draft mới:", args.o)
    if report["status"] == "BLOCKED":
        if report.get("verdict"):
            print("  Verdict plan trên cây mới: %s" % report["verdict"])
        from .failure_db import classify_failure
        failure = classify_failure(report["reason"], stage="PREFLIGHT")
        if failure:
            print("  Phân loại lỗi: %s — %s" % (
                failure["error_id"], failure["fix"]))
    return 0 if report["status"] == "READY_FOR_APPROVAL" else 2


def cmd_remote_map(args):
    """Lập bản đồ flag điều khiển hành vi từ xa (Tầng 2): field boolean +
    AtomicBoolean + mọi điểm đọc/ghi trong cây APK đã giải mã.

    ``--flow`` chuyển sang bản đồ luồng quyết định; ``--dataflow`` dựng bản đồ
    luồng dữ liệu có kiểu dữ liệu và độ tin cậy.
    """
    if args.dataflow:
        from .remote_map import build_data_flow, dataflow_summary_text
        flow = build_data_flow(args.cay_apk)
        print("[patchx] Bản đồ data-flow: %s" % args.cay_apk)
        print(dataflow_summary_text(flow))
        if args.o:
            import json as _json
            with open(args.o, "w", encoding="utf-8", newline="\n") as fh:
                _json.dump(flow, fh, ensure_ascii=False, indent=2)
            print("Đã ghi:", args.o)
        return 0
    if args.flow:
        from .remote_map import build_decision_flow, flow_summary_text
        flow = build_decision_flow(args.cay_apk)
        print("[patchx] Bản đồ luồng quyết định/dữ liệu: %s" % args.cay_apk)
        print(flow_summary_text(flow))
        if args.o:
            import json as _json
            with open(args.o, "w", encoding="utf-8", newline="\n") as fh:
                _json.dump(flow, fh, ensure_ascii=False, indent=2)
            print("Đã ghi:", args.o)
        return 0
    from .remote_map import build_remote_map, summary_text
    data = build_remote_map(args.cay_apk, with_atomic=not args.no_atomic)
    print("[patchx] Bản đồ flag điều khiển từ xa: %s" % args.cay_apk)
    print(summary_text(data))
    flags = data["flags"]
    n_show = args.top or 15
    rows = sorted(
        ((len(f["reads"]) + len(f["writes"]), fkey, f)
         for fkey, f in flags.items()), reverse=True)
    for score, fkey, f in rows[:n_show]:
        print("  %-45s %s  đọc=%d ghi=%d" % (
            fkey, "atomic" if f["atomic"] else "bool ",
            len(f["reads"]), len(f["writes"])))
    if args.o:
        import json as _json
        with open(args.o, "w", encoding="utf-8", newline="\n") as fh:
            _json.dump(data, fh, ensure_ascii=False, indent=2,
                       sort_keys=True)
        print("Đã ghi:", args.o)
    return 0


def cmd_remote_patch(args):
    """Sinh patch ép flag từ remote_flags.json + danh sách override."""
    import json as _json
    from .remote_map import build_force_patch
    with open(args.remote_map, "r", encoding="utf-8") as fh:
        rmap = _json.load(fh)
    overrides = {}
    if args.force:
        with open(args.force, "r", encoding="utf-8") as fh:
            overrides = _json.load(fh)
    for spec in args.set or []:
        if "=" not in spec:
            print("[patchx] bỏ qua spec thiếu '=': %r" % spec)
            continue
        fld, _, val = spec.partition("=")
        overrides[fld.strip()] = val.strip().lower() in ("true", "1", "0x1")
    if not overrides:
        print("[patchx] Chưa có override nào. Dùng --set "
              "'Lcls;->fld:Z = true' hoặc --force overrides.json")
        return 2
    try:
        text = build_force_patch(rmap, overrides, args.o)
    except ValueError as e:
        print("[patchx] Lỗi: %s" % e)
        return 2
    print("[patchx] Đã sinh patch: %s" % args.o)
    print(text)
    return 0


def cmd_diff_apk(args):
    """T2: sinh patch từ khác biệt hai APK/cây + vòng khép kín."""
    from .diffapk import (build_patch, prepare_tree, verify_rebuild,
                          write_patch_zip)
    import subprocess as _sp
    goc, goc_decoded, goc_tmp = prepare_tree(args.goc, args.keep_trees)
    mod, mod_decoded, mod_tmp = prepare_tree(args.da_mod, args.keep_trees)
    try:
        patch_text, assets, stats = build_patch(goc, mod, args.name)
        out = args.o or os.path.join(
            os.getcwd(), "diff_apk_%s.zip"
            % time.strftime("%Y%m%d-%H%M%S"))
        if out.lower().endswith(".zip"):
            write_patch_zip(out, patch_text, assets)
        else:
            with open(out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(patch_text)
            # assets kèm theo ở thư mục assets/ bên cạnh
            adir = os.path.join(os.path.dirname(out), "assets")
            for name, data in assets.items():
                full = os.path.join(adir, name[len("assets/"):])
                os.makedirs(os.path.dirname(full), exist_ok=True)
                with open(full, "wb") as fh:
                    fh.write(data)
        print("[patchx] diff-apk: thêm %d, sửa %d, xóa %d (binary đổi %d bỏ qua)"
              % (len(stats["added"]), len(stats["changed"]),
                 len(stats["removed"]), len(stats["binary_changed"])))
        print("  Đã ghi: %s" % out)
        if args.semantic_plan:
            from .smali_sem import build_app_model
            from .semantic_plan import plan_from_model_diff
            semantic = plan_from_model_diff(
                build_app_model(goc), build_app_model(mod),
                goal="Thay đổi rút ra từ %s" % args.name)
            os.makedirs(os.path.dirname(os.path.abspath(args.semantic_plan)),
                        exist_ok=True)
            with open(args.semantic_plan, "w", encoding="utf-8",
                      newline="\n") as fh:
                json.dump(semantic, fh, ensure_ascii=False, indent=2)
            print("  Kế hoạch ngữ nghĩa tham chiếu: %s (%d target)" % (
                args.semantic_plan, len(semantic["targets"])))
        if args.version_map or args.semantic_plan_v2:
            from .smali_sem import build_app_model_v2
            from .diffapk import match_app_models_v2
            from .semantic_plan import plan_v2_from_version_map
            original_v2 = build_app_model_v2(goc)
            modified_v2 = build_app_model_v2(mod)
            version_map = match_app_models_v2(original_v2, modified_v2)
            if args.semantic_plan_v2:
                semantic_v2 = plan_v2_from_version_map(
                    version_map, original_v2, modified_v2,
                    goal="Thay đổi tham chiếu từ %s" % args.name)
                os.makedirs(os.path.dirname(os.path.abspath(args.semantic_plan_v2)),
                            exist_ok=True)
                with open(args.semantic_plan_v2, "w", encoding="utf-8",
                          newline="\n") as fh:
                    json.dump(semantic_v2, fh, ensure_ascii=False, indent=2)
                print("  Kế hoạch ngữ nghĩa V2 (chỉ tham chiếu): %s (%d target)" % (
                    args.semantic_plan_v2, len(semantic_v2["targets"])))
                if not semantic_v2["targets"]:
                    print("  Không có ghép method duy nhất — không sinh target.")
            if args.version_map:
                os.makedirs(os.path.dirname(os.path.abspath(args.version_map)),
                            exist_ok=True)
                with open(args.version_map, "w", encoding="utf-8", newline="\n") as fh:
                    json.dump(version_map, fh, ensure_ascii=False, indent=2)
                s = version_map["summary"]
                print("  Bản đồ phiên bản (chỉ tham chiếu): exact=%d, structural=%d, semantic=%d, unknown=%d" % (
                    s["exact"], s["structural"], s["semantic"], s["unknown"]))
        for k in stats["added"][:5]:
            print("  + %s" % k)
        for k in stats["changed"][:5]:
            print("  ~ %s" % k)
        if not args.no_verify:
            v = verify_rebuild(goc, mod, out)
            print("[patchx] Vòng khép kín: tái sinh %s (khớp %d/%d tệp text)"
                  % (v["tỷ_lệ"], v["khớp"], v["tổng"]))
            if v["tỷ_lệ"] >= 90:
                print("  NGHIỆM THU ĐẠT (≥ 90%)")
            else:
                print("  Chưa đạt mốc 90%% — xem các tệp lệch (thường do "
                      "chuẩn hoá thứ tự/khác biệt phiên bản apktool).")
        return 0
    finally:
        import shutil
        if goc_tmp and args.keep_trees is None:
            shutil.rmtree(goc_tmp, ignore_errors=True)
        if mod_tmp and args.keep_trees is None:
            shutil.rmtree(mod_tmp, ignore_errors=True)


def cmd_suggest_apk(args):
    """T4: gợi ý chuỗi patch theo APK thật (coverage + danh mục + kho)."""
    from .learn import suggest_plan
    from .optimizer import CAP_LABELS
    plan = suggest_plan(args.cay_apk, args.thu_muc, top=args.top)
    print("[patchx] Danh mục: %s | package: %s" % (
        plan["danh_mục"], plan["package"] or "(chưa rõ)"))
    if not plan["khớp"]:
        print("  Không có patch khớp APK này.")
    for s in plan["khớp"]:
        print("  %-36s %4.0f%%  %s" % (
            s["patch"], s["tỷ_lệ"] * 100,
            ",".join(CAP_LABELS.get(c, c) for c in s["năng_lực"])))
    print("  " + plan["gợi_ý"])
    if plan["combo_đã_thành_công"]:
        print("  Combo đã thành công cùng danh mục:")
        for e in plan["combo_đã_thành_công"]:
            print("    - %s (lúc %s)" % (e.get("combo"), e.get("ts")))
    if args.o:
        os.makedirs(args.o, exist_ok=True)
        with open(os.path.join(args.o, "suggest_apk.json"), "w",
                  encoding="utf-8", newline="\n") as fh:
            json.dump(plan, fh, ensure_ascii=False, indent=2)
        print("Đã ghi:", os.path.join(args.o, "suggest_apk.json"))
    return 0


def cmd_suggest_llm(args):
    """T4: mô tả ý định → chọn patch + sinh khung combo; duyệt trước khi áp."""
    from .learn import suggest_by_intent, build_skeleton
    from .session import load_patch_map
    from .optimizer import CAP_LABELS
    patches = load_patch_map(args.thu_muc)
    scored, caps = suggest_by_intent(" ".join(args.y_dinh), patches)
    print("[patchx] Ý định → năng lực: %s" % ", ".join(
        CAP_LABELS.get(c, c) for c in caps))
    if not scored:
        print("  Không tìm thấy patch phù hợp — thử từ khóa khác "
              "(vd: vip, quảng cáo, toàn vẹn, shell).")
        return 0
    for s in scored[:args.top]:
        print("  %-36s %s" % (s["patch"], ",".join(
            CAP_LABELS.get(c, c) for c in s["năng_lực"])))
    selected = [s["patch"] for s in scored[:args.top]]
    print("Khung combo đề xuất (%d patch): %s" % (
        len(selected), ", ".join(selected)))
    if not args.approve:
        print("Chạy lại với --approve để ghi khung combo (người dùng duyệt).")
        return 0
    merged, conflicts = build_skeleton(patches, selected,
                                       "suggest_llm_%s" % time.strftime(
                                           "%Y%m%d-%H%M%S"))
    out_dir = args.o or os.path.join(os.getcwd(), "combos_llm")
    os.makedirs(out_dir, exist_ok=True)
    fname = os.path.join(out_dir, merged.name + ".zip")
    from .combo import render_patch_text
    import zipfile
    with zipfile.ZipFile(fname, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("patch.txt", render_patch_text(
            merged, header="Gợi ý LLM cục bộ (%s) — đã duyệt"
                           % " ".join(args.y_dinh)))
        for sec in merged.sections:
            if sec.type in ("ADD_FILES", "HOOK_SCRIPT", "REPLACE_FILES"):
                src = sec.get("SOURCE") or ""
                for name, data in (getattr(merged, "assets", {}) or {}).items():
                    if name == src:
                        zf.writestr(name, data)
    print("Đã ghi khung combo (đã duyệt): %s (%d xung đột tách)"
          % (fname, conflicts))
    return 0


def cmd_roadmap(args):
    from .advisor import build_roadmap, render_roadmap
    items = build_roadmap(args.thu_muc, args.cay_apk)
    out_dir = args.o or os.path.join(args.thu_muc, "_patchx")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "roadmap.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump({"generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "items": items}, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "roadmap.md"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(render_roadmap(items))
    print("[patchx] Đã sinh roadmap.md + roadmap.json cho %d patch"
          % len(items))
    for it in items[:8]:
        print("  %-32s %5.0f%%  %d khớp" % (
            it["patch"], it["tỷ_lệ"] * 100, it["lần_khớp"]))
    return 0


def cmd_simulate(args):
    from .simulate import run_simulation, render_simulation
    summary = run_simulation(args.thu_muc, quick=args.quick,
                             dex_runner=args.dex_runner,
                             dex_timeout=args.dex_timeout,
                             apk_tree=args.apk)
    out_dir = args.o or os.path.join(args.thu_muc, "_patchx")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "simulation.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "simulation_report.md"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(render_simulation(summary))
    print("[patchx] Mô phỏng %d patch: ĐẠT %d | THẤT-BẠI %d | BỎ-QUA %d | LỖI %d"
          % (summary["tổng_patch"], summary["đạt"], summary["thất_bại"],
             summary["bỏ_qua"], summary["lỗi"]))
    v2 = summary.get("status_v2", {})
    if v2:
        print("[patchx] V2 — PASS %d | EXPECTED_SKIP %d | UNSUPPORTED %d"
              " | BAD_PATCH %d | ENGINE_LIMIT %d | cache %d" % (
                  v2.get("PASS", 0), v2.get("EXPECTED_SKIP", 0),
                  v2.get("UNSUPPORTED", 0), v2.get("BAD_PATCH", 0),
                  v2.get("ENGINE_LIMIT", 0), summary.get("cache_hits", 0)))
    print("[patchx] Tỷ lệ đạt %s%% — tổng %s ms, trung bình %s ms/patch" % (
        summary["tỷ_lệ_đạt"], summary["tổng_thời_gian_ms"],
        summary["trung_bình_ms_patch"]))
    print("Đã ghi:", os.path.join(out_dir, "simulation_report.md"))
    return 0


def cmd_selfcheck(args):
    import importlib
    root = args.thu_muc
    if not root:
        suite_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for cand in (os.path.join(suite_root, "upgraded"), suite_root,
                     os.path.dirname(suite_root)):
            if glob.glob(os.path.join(cand, "*.zip")):
                root = cand
                break
        root = root or suite_root
    elif not glob.glob(os.path.join(root, "*.zip")):
        print("[patchx] CẢNH BÁO: không thấy tệp .zip trong %s" % root)
    args.thu_muc = root
    ok_mods = []
    for m in ("model", "parser", "engine", "audit", "optimizer", "advisor",
              "indexer", "simulate"):
        try:
            importlib.import_module("patchx_core." + m)
            ok_mods.append(m)
        except Exception as e:
            print("[patchx] LỖI import patchx_core.%s: %s" % (m, e))
    from .parser import parse_patch_file
    from .audit import parse_nested_zip
    total = bad = 0
    for z in sorted(glob.glob(os.path.join(args.thu_muc, "*.zip"))):
        try:
            p = parse_patch_file(z)
            total += 1
            for msg in p.issues:
                if msg.startswith("[ZIP]"):
                    print("[patchx] CẢNH BÁO %s: %s" % (os.path.basename(z), msg))
        except ValueError:
            nested = parse_nested_zip(z)
            total += len(nested)
        except Exception as e:
            bad += 1
            print("[patchx] LỖI phân tích %s: %s" % (os.path.basename(z), e))
    print("[patchx] Tự kiểm tra: %d/%d module OK, %d patch đọc được, %d lỗi"
          % (len(ok_mods), 8, total, bad))
    if args.full:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(
            os.path.dirname(__file__)))))
        import importlib.util
        tests = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "tests", "run_tests.py")
        spec = importlib.util.spec_from_file_location("run_tests", tests)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.main()
    return 0 if (len(ok_mods) == 8 and bad == 0) else 1


def cmd_combo(args):
    from .combo import collect_patches, build_combos, render_combo_report
    patches = collect_patches(args.thu_muc, recursive=args.recursive)
    if getattr(args, "apk", None):
        from .advisor import coverage_patch
        keep = []
        for p in patches:
            try:
                cov = coverage_patch(p, args.apk)
            except Exception:
                cov = None
            if cov and cov["quy_tắc_khớp"] > 0:
                keep.append(p)
        print("[patchx] combo --apk: giữ %d/%d patch khớp APK %s" % (
            len(keep), len(patches), args.apk))
        patches = keep
    if args.auto:
        from .complement import discover_combos, render_auto_report
        combos, isolated = discover_combos(patches)
        suite_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_dir = args.o or os.path.join(suite_root, "combos_auto")
        os.makedirs(out_dir, exist_ok=True)
        real_combos = combos
        summary = {"patches": len(patches), "combos": [], "isolated": isolated}
        for cb in real_combos:
            fpath = os.path.join(out_dir, cb["file"])
            header = "Combo tự phát hiện: %s (%d patch)" % (
                cb["label"], len(cb["patches"]))
            with open(fpath, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(render_patch_text(cb["merged"], header=header))
            summary["combos"].append({
                "label": cb["label"], "file": cb["file"],
                "patches": cb["patches"], "sections": cb["sections"],
                "conflicts": cb.get("conflicts", 0)})
            print("[patchx] Combo tự %s -> %s (%d khối từ %d patch%s)" % (
                cb["label"], cb["file"], cb["sections"], len(cb["patches"]),
                ", %d xung đột tách" % cb.get("conflicts", 0)
                if cb.get("conflicts", 0) else ""))
        with open(os.path.join(out_dir, "_auto_combos.json"), "w",
                  encoding="utf-8", newline="\n") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=2)
        with open(os.path.join(out_dir, "auto_combos_report.md"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(render_auto_report(combos, isolated, len(patches)))
        print("[patchx] Tự phát hiện %d combo từ %d patch "
              "(%d patch cô lập) vào %s" % (
                  len(real_combos), len(patches), len(isolated), out_dir))
        return 0
    only = [c.strip() for c in args.only.split(",")] if args.only else None
    combos = build_combos(patches, only=only)
    suite_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = args.o or os.path.join(suite_root, "combos")
    os.makedirs(out_dir, exist_ok=True)
    summary = {"patches": len(patches), "combos": []}
    for cb in combos:
        fpath = os.path.join(out_dir, cb["file"])
        header = "Combo: %s (%d patch)" % (cb["label"], len(cb["patches"]))
        with open(fpath, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_patch_text(cb["merged"], header=header))
        summary["combos"].append({
            "label": cb["label"], "file": cb["file"],
            "patches": cb["patches"], "sections": cb["sections"],
            "conflicts": cb["conflicts"]})
        print("[patchx] Combo %s -> %s (%d khối từ %d patch%s)" % (
            cb["label"], cb["file"], cb["sections"], len(cb["patches"]),
            ", %d xung đột tách" % cb["conflicts"] if cb["conflicts"] else ""))
    with open(os.path.join(out_dir, "_combos.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "combos_report.md"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(render_combo_report(combos, len(patches)))
    print("[patchx] Đã tạo %d combo từ %d patch vào %s" % (
        len(combos), len(patches), out_dir))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="patchx",
        description="Bộ script nâng cấp cho bộ sưu tập patch APK Editor "
                    "(phân tích, kiểm tra kiến trúc, nâng cấp, gộp tối ưu, "
                    "và áp patch lên cây APK đã giải mã).")
    parser.add_argument("--version", action="version",
                        version="patchx %s" % __version__)
    sub = parser.add_subparsers(dest="lệnh", metavar="LỆNH")

    p = sub.add_parser("scan", help="Quét thư mục patch và in tóm tắt")
    p.add_argument("thu_muc", help="Thư mục chứa các tệp .zip")
    p.add_argument("-o", help="Ghi kết quả JSON (tùy chọn)")
    p.add_argument("--recursive", action="store_true",
                   help="Quét cả thư mục con (bỏ qua _patchx và thư mục nội bộ)")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("index", help="Tạo index.json + report.md")
    p.add_argument("thu_muc")
    p.add_argument("-o", default=None, help="Thư mục đầu ra")
    p.add_argument("--ten", default="patchx", help="Tiền tố tên tệp")
    p.add_argument("--recursive", action="store_true",
                   help="Quét cả thư mục con")
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("dupes", help="Phát hiện patch trùng nội dung (hash)")
    p.add_argument("thu_muc")
    p.add_argument("-o", default=None, help="Thư mục đầu ra")
    p.add_argument("--recursive", action="store_true",
                   help="Quét cả thư mục con")
    p.set_defaults(func=cmd_dupes)

    p = sub.add_parser("manifest", help="Tạo MANIFEST.json cho toàn bộ cây")
    p.add_argument("thu_muc")
    p.add_argument("-o", default=None, help="Đường dẫn tệp đầu ra")
    p.set_defaults(func=cmd_manifest)

    p = sub.add_parser("verify-manifest",
                       help="Xác minh kho theo MANIFEST.json (T5 — phát hiện "
                            "file bị sửa/giả mạo)")
    p.add_argument("thu_muc", help="Thư mục kho patch")
    p.add_argument("--manifest", default=None,
                   help="Đường dẫn MANIFEST.json (mặc định "
                        "<thu_muc>/_patchx/MANIFEST.json)")
    p.set_defaults(func=cmd_verify_manifest)

    p = sub.add_parser("report", help="Tạo báo cáo HTML một file (T7)")
    p.add_argument("thu_muc")
    p.add_argument("-o", default=None, help="Đường dẫn tệp HTML đầu ra")
    p.add_argument("--recursive", action="store_true",
                   help="Quét cả thư mục con")
    p.add_argument("--apk", default=None,
                   help="Cây APK đã giải mã: đo độ phủ + preview diff")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("ci", help="Dây chuyền CI: audit → upgrade → optimize "
                                  "→ combo → simulate (T7)")
    p.add_argument("thu_muc", help="Thư mục kho patch gốc")
    p.add_argument("-o", default=None, help="Thư mục đầu ra (mặc định "
                                            "<thu_muc>/_patchx/ci)")
    p.add_argument("--quick", action="store_true",
                   help="Mô phỏng nhanh (ít mẫu)")
    p.add_argument("--golden", action="store_true",
                   help="Chạy thêm Golden Build gate sau khi simulate")
    p.set_defaults(func=cmd_ci)

    p = sub.add_parser("golden", help="P10: cổng Golden Build — chạy 2 golden "
                                      "test và trả 1 nếu fail")
    p.add_argument("-o", default=None, help="Thư mục ghi golden_gate.json")
    p.add_argument("--fw", action="store_true",
                   help="Bật PATCHX_GOLDEN_FW=1 để build đủ framework-res")
    p.set_defaults(func=cmd_golden)

    p = sub.add_parser("validate",
                       help="P9: Xác thực cây APK (smali/XML/manifest/DEX)")
    p.add_argument("cay", help="Cây APK đã giải mã")
    p.add_argument("--level", default="NORMAL",
                   choices=["FAST", "NORMAL", "FULL", "RELEASE"],
                   help="Mức xác thực (mặc định NORMAL)")
    p.add_argument("--changed-only", action="store_true",
                   help="Chỉ kiểm tra tệp đổi mới (tăng tốc vòng lặp fix→test)")
    p.add_argument("--files", nargs="*", default=None,
                   help="Chỉ kiểm tra các tệp này (đường dẫn tương đối)")
    p.add_argument("--limit", type=int, default=50,
                   help="Số lỗi in tối đa (mặc định 50)")
    p.add_argument("--max-files", type=int, default=None,
                   help="Giới hạn tệp quét DEX budget (FULL/RELEASE)")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("apk-prepare", help="Giải mã APK bằng apktool "
                                       "(chuẩn bị cây cho coverage/apply)")
    p.add_argument("apk", help="Tệp .apk")
    p.add_argument("-o", default=None, help="Thư mục giải mã đầu ra")
    p.add_argument("--timeout", type=int, default=600,
                   help="Giới hạn giây (mặc định 600)")
    p.set_defaults(func=cmd_apk_prepare)

    p = sub.add_parser("audit", help="Kiểm tra kiến trúc từng patch")
    p.add_argument("thu_muc")
    p.add_argument("-o", default=None, help="Thư mục đầu ra (mặc định: cùng thư mục)")
    p.add_argument("--recursive", action="store_true",
                   help="Quét cả thư mục con")
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser("upgrade", help="Nâng cấp patch: sửa lỗi kiến trúc an toàn")
    p.add_argument("thu_muc")
    p.add_argument("-o", default=None, help="Thư mục đầu ra")
    p.add_argument("--dry-run", action="store_true", help="Chỉ xem trước, không ghi")
    p.set_defaults(func=cmd_upgrade)

    p = sub.add_parser("optimize", help="Gộp patch theo nhóm, gộp trùng, tách xung đột")
    p.add_argument("thu_muc")
    p.add_argument("-o", default=None, help="Thư mục đầu ra")
    p.set_defaults(func=cmd_optimize)

    p = sub.add_parser("apply", help="Áp patch lên cây APK đã giải mã")
    p.add_argument("patch", nargs="+", help="Các patch (.zip/.txt/thư mục)")
    p.add_argument("cay_apk", help="Thư mục APK đã giải mã (thư mục cuối)")
    p.add_argument("--dry-run", action="store_true", help="Xem trước, không ghi")
    p.add_argument("--no-backup", action="store_true", help="Không sao lưu trước khi sửa")
    p.add_argument("--force", action="store_true", help="Áp lại kể cả đã áp trước đó")
    p.add_argument("--dex-runner", default=None, metavar="LỆNH",
                   help="Lệnh chạy EXECUTE_DEX thay vì bỏ qua")
    p.add_argument("--dex-allow", action="append", default=[],
                   help="Mở rộng danh sách cho phép EXECUTE_DEX (T5 — có "
                        "thể lặp)")
    p.add_argument("--strict", action="store_true", help="Lỗi nhẹ cũng dừng")
    p.add_argument("--quiet", action="store_true", help="In ít hơn")
    p.add_argument("--reset-state", action="store_true",
                   help="Xóa trạng thái đã áp trước đó")
    p.set_defaults(func=cmd_apply)

    p = sub.add_parser("coverage", help="Đo độ bao phủ của patch trên cây APK")
    p.add_argument("--mode", default="FAST",
                   choices=["FAST", "NORMAL", "FULL", "RELEASE"],
                   help="Chế độ quét (P16): FAST mẫu ≤300; NORMAL quét đủ; "
                        "FULL + ngoài target; RELEASE đầy đủ nhất")
    p.add_argument("patch", help="Tệp patch (.zip/.txt/thư mục)")
    p.add_argument("cay_apk", help="Thư mục APK đã giải mã")
    p.add_argument("-o", default=None, help="Ghi JSON kết quả")
    p.add_argument("--method", action="store_true",
                   help="Chi tiết theo method (ngữ nghĩa, trục T1)")
    p.set_defaults(func=cmd_coverage)

    p = sub.add_parser("suggest", help="Tự đề xuất cải tiến cho patch")
    p.add_argument("patch", help="Tệp patch (.zip/.txt/thư mục)")
    p.add_argument("cay_apk", nargs="?", default=None,
                   help="Thư mục APK đã giải mã (tùy chọn, để đo bao phủ)")
    p.add_argument("-o", default=None, help="Ghi JSON kết quả")
    p.set_defaults(func=cmd_suggest)

    p = sub.add_parser("analyze", help="Phân tích ngữ nghĩa cây APK (trục T1): "
                      "packer, mã hóa chuỗi, call-graph")
    p.add_argument("cay_apk", help="Thư mục APK đã giải mã")
    p.add_argument("-o", default=None, help="Ghi JSON kết quả")
    p.add_argument("--top", type=int, default=15,
                   help="Số class đứng đầu call-graph (mặc định 15)")
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("model", help="Tạo mô hình trung gian method/call/data-flow "
                       "(không áp patch)")
    p.add_argument("cay_apk", help="Thư mục APK đã giải mã")
    p.add_argument("-o", default=None, help="Tệp JSON đầu ra (mặc định .patchx/app_model.json)")
    p.add_argument("--with-bodies", action="store_true",
                   help="Kèm thân method; mặc định chỉ ghi metadata để tránh tệp lớn")
    p.add_argument("--v2", action="store_true",
                   help="Sinh patchx.app-model/v2 chỉ-đọc, có identity và caller/callee")
    p.add_argument("--bench", action="store_true",
                   help="Chỉ đo thời gian dựng model cache lạnh, không ghi JSON")
    p.set_defaults(func=cmd_model)

    p = sub.add_parser("semantic-plan", help="Đánh giá kế hoạch mục tiêu + điều kiện "
                       "trên app-model (không áp patch)")
    p.add_argument("cay_apk", help="Thư mục APK đã giải mã")
    p.add_argument("ke_hoach", help="Tệp JSON patchx.semantic-plan/v1 hoặc v2")
    p.add_argument("--model", default=None, help="Dùng app_model.json đã sinh thay vì quét lại")
    p.add_argument("-o", default=None, help="Ghi JSON bằng chứng/ứng viên")
    p.add_argument("--verbose", action="store_true",
                   help="In cả ứng viên bị loại và điều kiện còn thiếu")
    p.set_defaults(func=cmd_semantic_plan)

    p = sub.add_parser("acceptance", help="Chạy tiêu chí nghiệm thu V2 trên fixture "
                       "acceptance.json (chỉ đọc)")
    p.add_argument("fixture", help="Thư mục fixture chứa acceptance.json")
    p.add_argument("-o", default=None, help="Ghi báo cáo JSON")
    p.set_defaults(func=cmd_acceptance)

    p = sub.add_parser("plan-compile", help="Tạo transaction nháp từ semantic-plan/V2; không áp APK")
    p.add_argument("cay_apk", help="Cây APK đã giải mã")
    p.add_argument("ke_hoach", help="Tệp patchx.semantic-plan/v2 đã duyệt")
    p.add_argument("-o", required=True, help="JSON transaction nháp")
    p.set_defaults(func=cmd_plan_compile)

    p = sub.add_parser("plan-preflight", help="Kiểm tra hash evidence của transaction nháp; không áp APK")
    p.add_argument("cay_apk", help="Cây APK đã giải mã")
    p.add_argument("draft", help="JSON patchx.transaction-draft/v1")
    p.add_argument("-o", default=None,
                   help="Ghi draft mới nếu cây đổi nhưng plan vẫn READY")
    p.set_defaults(func=cmd_plan_preflight)

    p = sub.add_parser("knowledge", help="Kho tri thức: lưu/truy vấn outcome đã nghiệm thu")
    p.add_argument("--db", default="knowledge_base.json", help="Tệp JSON kho tri thức")
    kp = p.add_subparsers(dest="hành_động", required=True)
    k1 = kp.add_parser("record", help="Ghi một record verified=true")
    k1.add_argument("record", help="Tệp patchx.knowledge-record/v1 hoặc v2")
    k1.set_defaults(func=cmd_knowledge)
    k2 = kp.add_parser("query", help="Tìm fingerprint tương tự trong APK")
    k2.add_argument("cay_apk", help="Thư mục APK đã giải mã")
    k2.add_argument("--goal", default=None, help="Lọc đúng mục tiêu hành vi")
    k2.add_argument("--top", type=int, default=10)
    k2.add_argument("--v2", action="store_true", help="Dùng app-model/v2 và xếp hạng identity đa đặc trưng")
    k2.set_defaults(func=cmd_knowledge)
    k3 = kp.add_parser("suggest-plan", help="Sinh semantic-plan/V2 tham chiếu từ kho tri thức")
    k3.add_argument("cay_apk", help="Thư mục APK đã giải mã")
    k3.add_argument("-o", required=True, help="Ghi JSON semantic-plan/V2")
    k3.add_argument("--goal", default=None, help="Lọc đúng mục tiêu hành vi")
    k3.add_argument("--top", type=int, default=10)
    k3.set_defaults(func=cmd_knowledge)

    p = sub.add_parser("diff-apk", help="Sinh patch từ khác biệt hai APK/cây "
                       "(trục T2 — đảo pipeline)")
    p.add_argument("goc", help="APK hoặc cây gốc")
    p.add_argument("da_mod", help="APK hoặc cây đã mod")
    p.add_argument("-o", default=None,
                   help="Đầu ra patch .zip (tự chứa) hoặc .txt + assets/")
    p.add_argument("--name", default="diff_apk", help="Tên patch")
    p.add_argument("--no-verify", action="store_true",
                   help="Bỏ vòng khép kín (mặc định chạy)")
    p.add_argument("--keep-trees", default=None,
                   help="Thư mục giữ cây decode (mặc định dùng thư mục tạm)")
    p.add_argument("--semantic-plan", default=None,
                   help="Sinh thêm JSON mục tiêu+điều kiện từ khác biệt; chỉ tham chiếu, không tự áp")
    p.add_argument("--version-map", default=None,
                   help="Ghi JSON ghép method V2 giữa hai phiên bản, chỉ tham chiếu")
    p.add_argument("--semantic-plan-v2", default=None,
                   help="Sinh semantic-plan/V2 từ ghép method duy nhất; chỉ tham chiếu, không tự áp")
    p.set_defaults(func=cmd_diff_apk)

    p = sub.add_parser("suggest-apk", help="Gợi ý chuỗi patch theo APK thật "
                       "(T4 — danh mục + kho combo thành công)")
    p.add_argument("thu_muc", help="Thư mục chứa patch .zip")
    p.add_argument("cay_apk", help="Cây APK đã giải mã")
    p.add_argument("--top", type=int, default=8)
    p.add_argument("-o", default=None, help="Thư mục ghi JSON")
    p.set_defaults(func=cmd_suggest_apk)

    p = sub.add_parser("suggest-llm", help="Mô tả ý định mod → khung combo "
                       "(T4 — người dùng duyệt trước khi áp)")
    p.add_argument("thu_muc", help="Thư mục chứa patch .zip")
    p.add_argument("y_dinh", nargs="+", help="Mô tả ý định (vd: mở khoá vip, "
                   "chặn quảng cáo)")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--approve", action="store_true",
                   help="Ghi khung combo sau khi người dùng duyệt")
    p.add_argument("-o", default=None, help="Thư mục đầu ra")
    p.set_defaults(func=cmd_suggest_llm)

    p = sub.add_parser("roadmap", help="Xây lộ trình mod cho APK thật")
    p.add_argument("thu_muc", help="Thư mục chứa các patch .zip")
    p.add_argument("cay_apk", help="Thư mục APK đã giải mã")
    p.add_argument("-o", default=None, help="Thư mục đầu ra")
    p.set_defaults(func=cmd_roadmap)

    p = sub.add_parser("combo", help="Gộp combo các patch hỗ trợ nhau "
                                  "(bypass VIP + shell + toàn vẹn; truy vết + "
                                  "API + token + toàn vẹn, ...)")
    p.add_argument("thu_muc", help="Thư mục chứa các patch .zip")
    p.add_argument("--only", default=None,
                   help="Danh sách năng lực, ví dụ: "
                        "bypass-license,shell,integrity")
    p.add_argument("--recursive", action="store_true",
                   help="Quét cả thư mục con")
    p.add_argument("--auto", action="store_true",
                   help="Tự phát hiện các patch bổ trợ cho nhau "
                        "(class link, cùng target, cùng năng lực)")
    p.add_argument("--apk", default=None,
                   help="Cây APK đã giải mã — chỉ giữ patch khớp APK "
                        "(roadmap động, trục T4)")
    p.add_argument("-o", default=None, help="Thư mục đầu ra")
    p.set_defaults(func=cmd_combo)

    p = sub.add_parser("simulate", help="Mô phỏng toàn diện: tự sinh mẫu, "
                                  "áp thử từng patch, đánh giá hiệu quả")
    p.add_argument("thu_muc", help="Thư mục chứa các patch .zip")
    p.add_argument("-o", default=None, help="Thư mục đầu ra")
    p.add_argument("--quick", action="store_true", help="Chỉ chạy 15 patch đầu")
    p.add_argument("--dex-runner", default=None, metavar="LỆNH",
                   help="Chạy EXECUTE_DEX bằng lệnh (an toàn: timeout, không shell)")
    p.add_argument("--dex-timeout", type=int, default=60,
                   help="Giới hạn giây cho EXECUTE_DEX (mặc định 60)")
    p.add_argument("--apk", default=None, metavar="CÂY_APK",
                   help="Mô phỏng trên cây APK đã giải mã thay vì cây giả lập")
    p.set_defaults(func=cmd_simulate)

    p = sub.add_parser("selfcheck", help="Kiểm tra sức khỏe của chính bộ patchx")
    p.add_argument("thu_muc", default=None, nargs="?",
                   help="Thư mục patch (tự dò nếu bỏ trống)")
    p.add_argument("--full", action="store_true", help="Kèm chạy toàn bộ test")
    p.set_defaults(func=cmd_selfcheck)

    p = sub.add_parser("remote-map",
                       help="Lập bản đồ flag điều khiển hành vi từ xa: field "
                            "boolean + mọi điểm đọc/ghi trong cây APK")
    p.add_argument("cay_apk", help="Cây APK đã giải mã")
    p.add_argument("-o", default=None,
                   help="Ghi bản đồ JSON (mặc định chỉ in tóm tắt)")
    p.add_argument("--top", type=int, default=15,
                   help="Số flag nổi bật nhất cần in (mặc định 15)")
    p.add_argument("--no-atomic", action="store_true",
                   help="Bỏ qua field AtomicBoolean")
    p.add_argument("--flow", action="store_true",
                   help="Dựng bản đồ luồng quyết định/dữ liệu từ app-model/V2")
    p.add_argument("--dataflow", action="store_true",
                   help="Dựng bản đồ data-flow có kiểu dữ liệu và độ tin cậy")
    p.set_defaults(func=cmd_remote_map)

    p = sub.add_parser("remote-patch",
                       help="Sinh patch ép flag từ remote_flags.json "
                            "(FORCE tại mọi điểm READ)")
    p.add_argument("remote_map", help="Tệp remote_flags.json từ remote-map")
    p.add_argument("-o", required=True, help="Tệp patch .zip đầu ra")
    p.add_argument("--force", default=None, metavar="OVERRIDES.json",
                   help='Tệp JSON dạng {"Lcls;->fld:Z": true}')
    p.add_argument("--set", action="append", metavar="'Lcls;->fld:Z = true'",
                   help="Override trực tiếp (dùng nhiều lần)")
    p.set_defaults(func=cmd_remote_patch)


    p = sub.add_parser("baseline", help="PHASE 0: chụp/xem/so sánh baseline "
                                        "(cổng chặn hồi quy)")
    bsub = p.add_subparsers(dest="hành_động", metavar="HÀNH_ĐỘNG")
    p1 = bsub.add_parser("capture", help="Chụp baseline mới (metrics.json)")
    p1.add_argument("--set", action="append", default=[],
                    help="Ghi đè chỉ số, dạng key=value (lặp được)")
    p1.add_argument("--dir", default=None, help="Thư mục baseline")
    p1.add_argument("--full", action="store_true",
                    help="Tự chạy test suite + simulate 60 patch để lấy số thật")
    p1.set_defaults(func=cmd_baseline)
    p2 = bsub.add_parser("show", help="In baseline hiện tại")
    p2.add_argument("--dir", default=None, help="Thư mục baseline")
    p2.set_defaults(func=cmd_baseline)
    p3 = bsub.add_parser("compare", help="So sánh metrics mới với baseline; "
                                         "trả 1 nếu hồi quy (dùng trong CI)")
    p3.add_argument("metrics_mới", help="Đường dẫn metrics.json mới")
    p3.add_argument("--dir", default=None, help="Thư mục baseline")
    p3.set_defaults(func=cmd_baseline)
    p = sub.add_parser("dex-budget",
                       help="P5: ước lượng DEX refs + mức an toàn")
    p.add_argument("cây", help="Cây APK đã giải mã")
    p.add_argument("--patch", default=None,
                   help="Patch (zip/txt) để ước lượng delta")
    p.add_argument("--max", type=int, default=None,
                   help="Giới hạn method refs (mặc định 65536)")
    p.add_argument("--max-files", type=int, default=None,
                   help="Giới hạn số tệp quét (kiểm tra nhanh)")
    p.add_argument("--workers", type=int, default=1,
                   help="Số luồng song song khi quét (P20; mặc định 1)")
    p.set_defaults(func=cmd_dex_budget)
    p = sub.add_parser("preflight",
                       help="P7: cổng kiểm tra trước khi áp patch")
    p.add_argument("patch", help="Patch (zip/txt)")
    p.add_argument("cây", help="Cây APK đã giải mã")
    p.add_argument("--max-files", type=int, default=None,
                   help="Giới hạn số tệp quét DEX budget")
    p.set_defaults(func=cmd_preflight)
    p = sub.add_parser("fuzz",
                       help="P12: fuzz/chaos parser + engine (5 invariant)")
    p.add_argument("--iter", type=int, default=100,
                   help="Số lượt ngẫu nhiên (mặc định 100)")
    p.add_argument("--seed", type=int, default=1,
                   help="Seed ngẫu nhiên (mặc định 1, cố định để tái lập)")
    p.add_argument("--workdir", default=None,
                   help="Thư mục làm việc (giữ lại để điều tra)")
    p.set_defaults(func=cmd_fuzz)
    p = sub.add_parser("failure", help="P15: Failure Intelligence (DB lỗi + "
                                       "sinh regression test)")
    fsub = p.add_subparsers(dest="hành_động", metavar="HÀNH_ĐỘNG")
    f1 = fsub.add_parser("list", help="Liệt kê DB lỗi")
    f1.add_argument("--db", default=None, help="Đường dẫn DB tùy chỉnh")
    f1.set_defaults(func=cmd_failure)
    f2 = fsub.add_parser("report", help="In báo cáo MD")
    f2.add_argument("--db", default=None, help="Đường dẫn DB tùy chỉnh")
    f2.set_defaults(func=cmd_failure)
    f3 = fsub.add_parser("lookup", help="Tra cứu lỗi theo thông báo")
    f3.add_argument("--message", default=None, help="Thông báo lỗi cần tra")
    f3.add_argument("--stage", default=None, help="Lọc theo stage")
    f3.add_argument("--db", default=None, help="Đường dẫn DB tùy chỉnh")
    f3.set_defaults(func=cmd_failure)
    f4 = fsub.add_parser("add", help="Thêm entry lỗi")
    f4.add_argument("--error-id", required=True)
    f4.add_argument("--stage", default=None)
    f4.add_argument("--pattern", required=True,
                    help="Regex khớp thông báo lỗi")
    f4.add_argument("--cause", default=None)
    f4.add_argument("--fix", default=None)
    f4.add_argument("--regression", default=None,
                    help="Tên test hồi quy liên quan")
    f4.add_argument("--db", default=None, help="Đường dẫn DB tùy chỉnh")
    f4.set_defaults(func=cmd_failure)
    f5 = fsub.add_parser("gen-regression",
                         help="Sinh test hồi quy từ entry lỗi")
    f5.add_argument("--error-id", default=None)
    f5.add_argument("--message", default=None)
    f5.add_argument("--stage", default=None)
    f5.add_argument("--test-name", default=None)
    f5.add_argument("--out", default=None,
                    help="Ghi test ra tệp (mặc định in ra màn hình)")
    f5.add_argument("--db", default=None, help="Đường dẫn DB tùy chỉnh")
    f5.set_defaults(func=cmd_failure)
    p = sub.add_parser("test", help="Chạy bộ tự kiểm tra")
    p.set_defaults(func=cmd_test)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
