# -*- coding: utf-8 -*-
"""Baseline & đo lường (PHASE 0 — PATCHX V2).

Đóng băng thước đo cố định: baseline/metrics.json + so sánh hồi quy.
Mọi thay đổi phải được so với baseline trước khi chấp nhận
(Rule 5: không tối ưu trước khi có baseline).
"""

import json
import os
import platform
import re
import subprocess
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BASELINE_DIR = os.path.join(BASE_DIR, "baseline")

# Định nghĩa các chỉ số: trend = "higher" (càng cao càng tốt) hay
# "lower" (càng thấp càng tốt); threshold = độ xấu đi cho phép trước
# khi bị coi là hồi quy (đơn vị của chính chỉ số; 0 = mọi xấu đi đều chặn).
METRICS = {
    "test_pass": {"name": "Số kiểm tra đạt", "unit": "kiểm tra",
                  "trend": "higher", "threshold": 0,
                  "nguồn": "python3 patchx test"},
    "test_total": {"name": "Tổng số kiểm tra", "unit": "kiểm tra",
                   "trend": "higher", "threshold": 0,
                   "nguồn": "python3 patchx test"},
    "test_ratio": {"name": "Tỷ lệ kiểm tra đạt", "unit": "%",
                   "trend": "higher", "threshold": 0.5,
                   "nguồn": "test_pass / test_total"},
    "simulate_pass": {"name": "Simulate đạt", "unit": "patch",
                      "trend": "higher", "threshold": 0,
                      "nguồn": "python3 patchx simulate upgraded"},
    "simulate_total": {"name": "Tổng simulate", "unit": "patch",
                       "trend": "higher", "threshold": 0,
                       "nguồn": "python3 patchx simulate upgraded"},
    "simulate_ratio": {"name": "Tỷ lệ simulate đạt", "unit": "%",
                       "trend": "higher", "threshold": 0.5,
                       "nguồn": "simulate_pass / simulate_total"},
    "simulate_time_s": {"name": "Thời gian simulate 60 patch", "unit": "giây",
                        "trend": "lower", "threshold": 5.0,
                        "nguồn": "python3 patchx simulate upgraded (cache ấm)"},
    "golden_build_pass": {"name": "Golden build đạt", "unit": "bộ",
                          "trend": "higher", "threshold": 0,
                          "nguồn": "tests golden"},
    "golden_build_total": {"name": "Tổng golden build", "unit": "bộ",
                           "trend": "higher", "threshold": 0,
                           "nguồn": "tests golden"},
    "scan_time_s": {"name": "Thời gian quét APK lớn", "unit": "giây",
                    "trend": "lower", "threshold": 5.0,
                    "nguồn": "bench-scan (553M)"},
    "plan_time_s": {"name": "Thời gian lập kế hoạch", "unit": "giây",
                    "trend": "lower", "threshold": 5.0,
                    "nguồn": "apk-plan"},
    "apply_time_s": {"name": "Thời gian áp patch", "unit": "giây",
                     "trend": "lower", "threshold": 5.0,
                     "nguồn": "apply_report.json"},
    "validate_time_s": {"name": "Thời gian xác thực", "unit": "giây",
                        "trend": "lower", "threshold": 30.0,
                        "nguồn": "apk-debug/apk-build"},
    "build_time_s": {"name": "Thời gian build", "unit": "giây",
                     "trend": "lower", "threshold": 60.0,
                     "nguồn": "build_report.json"},
    "method_refs": {"name": "Method refs (dex chạm trần)", "unit": "refs",
                    "trend": "lower", "threshold": 100,
                    "nguồn": "phân tích dex"},
    "method_count": {"name": "Số method (cây mẫu)", "unit": "method",
                     "trend": "higher", "threshold": 0,
                     "nguồn": "validate tree"},
    "file_count": {"name": "Số tệp (cây mẫu)", "unit": "tệp",
                   "trend": "higher", "threshold": 0,
                   "nguồn": "validate tree"},
    "changed_files": {"name": "Tệp bị sửa", "unit": "tệp",
                      "trend": "lower", "threshold": 20,
                      "nguồn": "apply_report.json"},
    "new_refs": {"name": "Method ref mới thêm", "unit": "refs",
                 "trend": "lower", "threshold": 50,
                 "nguồn": "phân tích dex trước/sau"},
    "errors": {"name": "Lỗi", "unit": "lỗi", "trend": "lower",
               "threshold": 0, "nguồn": "báo cáo pipeline"},
    "warnings": {"name": "Cảnh báo", "unit": "cảnh báo", "trend": "lower",
                 "threshold": 5, "nguồn": "báo cáo pipeline"},
}


def load_metrics(path):
    """Nạp metrics.json — trả dict rỗng nếu chưa có."""
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_metrics(path, metrics):
    """Ghi metrics.json (đẹp, tiếng Việt giữ nguyên)."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(metrics, fh, ensure_ascii=False, indent=2)
    return path


def capture_environment():
    """Chụp môi trường chạy (để so sánh công bằng khi máy khác tải)."""
    try:
        load = os.getloadavg()
    except (OSError, AttributeError):
        load = []
    return {
        "captured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count() or 0,
        "loadavg_1_5_15": [round(x, 2) for x in load],
        "machine": platform.machine(),
    }


def capture_metrics(overrides=None, baseline_dir=DEFAULT_BASELINE_DIR):
    """Thu thập metrics hiện tại.

    - overrides: dict do người dùng cung cấp (--set key=value hoặc inputs.json).
    - Tự động tìm các báo cáo đã có (apply/build/runtime) để bổ sung.
    Trả dict metrics + environment.
    """
    metrics = {k: None for k in METRICS}
    if overrides:
        for k, v in overrides.items():
            if k in METRICS and v is not None:
                try:
                    metrics[k] = float(v) if isinstance(v, str) else v
                except ValueError:
                    metrics[k] = v
    # Bổ sung từ báo cáo đã có trong kho (nếu chưa bị ghi đè)
    _fill_from_reports(metrics, baseline_dir)
    env = capture_environment()
    env["load_note"] = ("Máy dùng chung có thể nhiễu; ghi lại loadavg để "
                        "so sánh tương đối.")
    return metrics, env


def _fill_from_reports(metrics, baseline_dir):
    """Tìm các report JSON gần nhất để điền số liệu thật."""
    candidates = []
    roots = [os.path.join(BASE_DIR, "real_apk_test"),
             os.path.join(BASE_DIR, "toolkit_out"),
             os.path.join(BASE_DIR, "bench_out"),
             os.path.join(BASE_DIR, "apk_full_out")]
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, _, files in os.walk(root):
            for fn in files:
                if fn.endswith(("build_report.json", "apply_report.json",
                                "runtime_report.json", "bench_report.json",
                                "apk_build_report.json")):
                    candidates.append(os.path.join(dirpath, fn))
    for cpath in sorted(candidates, key=lambda p: os.path.getmtime(p),
                        reverse=True)[:12]:
        try:
            with open(cpath, encoding="utf-8") as fh:
                r = json.load(fh)
        except (OSError, ValueError):
            continue
        base = os.path.basename(cpath)
        if "build" in base and metrics["build_time_s"] is None:
            metrics["build_time_s"] = r.get("build_seconds")
            if metrics["method_refs"] is None:
                metrics["method_refs"] = (r.get("method_refs") or
                                          r.get("method_refs_before"))
        elif "apply" in base and metrics["apply_time_s"] is None:
            metrics["apply_time_s"] = r.get("apply_seconds")
            if metrics["changed_files"] is None:
                metrics["changed_files"] = r.get("changed_files")
            if metrics["errors"] is None:
                metrics["errors"] = (r.get("errors") or
                                     r.get("validate_total_errors"))
        elif "runtime" in base and metrics["errors"] is None:
            metrics["errors"] = r.get("errors") or (
                0 if r.get("m2") in (True, "PASS", "M2_PASS") else None)
        elif "bench" in base and metrics["scan_time_s"] is None:
            metrics["scan_time_s"] = r.get("scan_seconds") or r.get("seconds")
    # Chỉ số phái sinh
    if metrics["test_pass"] is not None and metrics["test_total"]:
        metrics["test_ratio"] = round(
            100.0 * metrics["test_pass"] / metrics["test_total"], 2)


def capture_full(overrides=None, baseline_dir=DEFAULT_BASELINE_DIR):
    """Chụp baseline đầy đủ: test suite + simulate 60 patch + báo cáo có sẵn."""
    metrics, env = capture_metrics(overrides, baseline_dir)
    test_script = os.path.join(BASE_DIR, "tests", "run_tests.py")
    if os.path.isfile(test_script):
        try:
            proc = subprocess.run(
                [sys.executable, test_script], cwd=BASE_DIR, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
            m = re.search(r"Kết quả:\s*(\d+)/(\d+)", proc.stdout or "")
            if m:
                metrics["test_pass"] = int(m.group(1))
                metrics["test_total"] = int(m.group(2))
                metrics["test_ratio"] = round(
                    100.0 * metrics["test_pass"] / max(1, metrics["test_total"]), 2)
        except Exception:
            pass
    upgraded = os.path.join(BASE_DIR, "upgraded")
    if os.path.isdir(upgraded):
        try:
            from .simulate import run_simulation
            sim = run_simulation(upgraded)
            metrics["simulate_pass"] = sim.get("đạt")
            metrics["simulate_total"] = sim.get("tổng_patch")
            if metrics["simulate_total"]:
                metrics["simulate_ratio"] = round(
                    100.0 * metrics["simulate_pass"] / metrics["simulate_total"], 2)
            metrics["simulate_time_s"] = round(
                (sim.get("tổng_thời_gian_ms") or 0) / 1000.0, 3)
        except Exception:
            pass
    golden_gate = os.path.join(BASE_DIR, "toolkit_out", "golden_gate.json")
    if os.path.isfile(golden_gate):
        try:
            with open(golden_gate, encoding="utf-8") as fh:
                gate = json.load(fh)
            if metrics["golden_build_pass"] is None:
                metrics["golden_build_pass"] = gate.get("golden_build_pass")
            if metrics["golden_build_total"] is None:
                metrics["golden_build_total"] = gate.get("golden_build_total")
        except (OSError, ValueError):
            pass
    return metrics, env


def compare_metrics(baseline, new, warnings=True):
    """So sánh baseline với kết quả mới.

    Trả: items (chi tiết từng chỉ số) + verdict ("ACCEPT"/"BLOCK")
         + reasons (danh sách hồi quy).
    """
    items = []
    reasons = []
    for key, meta in METRICS.items():
        b = baseline.get(key)
        n = new.get(key)
        if b is None or n is None:
            continue
        b_f, n_f = float(b), float(n)
        delta = n_f - b_f
        if meta["trend"] == "higher":
            worse = delta < -meta["threshold"]
        else:
            worse = delta > meta["threshold"]
        status = "WORSE" if worse else ("BETTER" if abs(delta) > 1e-9
                                        else "OK")
        if worse:
            reasons.append("%s: %s → %s (xấu hơn %s %s, cho phép %s)"
                          % (key, b, n, abs(delta), meta["unit"],
                             meta["threshold"]))
        items.append({"chỉ_số": key, "tên": meta["name"], "baseline": b,
                      "mới": n, "đơn_vị": meta["unit"],
                      "xu_hướng": meta["trend"], "trạng_thái": status})
    verdict = "BLOCK" if reasons else "ACCEPT"
    return {"verdict": verdict, "reasons": reasons,
            "so_sánh_lúc": time.strftime("%Y-%m-%d %H:%M:%S"),
            "items": items}


def render_compare(result, indent="  "):
    """In bảng so sánh ra text."""
    lines = ["Kết luận: %s" % ("✅ ACCEPT" if result["verdict"] == "ACCEPT"
                               else "🚫 BLOCK (hồi quy)")]
    for it in result["items"]:
        mark = {"OK": "·", "BETTER": "↑", "WORSE": "↓"}.get(
            it["trạng_thái"], "?")
        lines.append("%s%s %-18s %-8s %s → %s %s" % (
            indent, mark, it["chỉ_số"], it["trạng_thái"],
            it["baseline"], it["mới"], it["đơn_vị"]))
    for r in result["reasons"]:
        lines.append("%s⚠ %s" % (indent, r))
    return "\n".join(lines)


def write_baseline(baseline_dir=DEFAULT_BASELINE_DIR, overrides=None):
    """Chụp và lưu baseline chuẩn. Trả đường dẫn metrics.json."""
    os.makedirs(baseline_dir, exist_ok=True)
    metrics, env = capture_metrics(overrides, baseline_dir)
    mpath = os.path.join(baseline_dir, "metrics.json")
    save_metrics(mpath, metrics)
    with open(os.path.join(baseline_dir, "environment.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(env, fh, ensure_ascii=False, indent=2)
    return mpath


def run_compare(new_path, baseline_dir=DEFAULT_BASELINE_DIR):
    """So sánh new metrics với baseline. Trả (verdict, result)."""
    base = load_metrics(os.path.join(baseline_dir, "metrics.json"))
    new = load_metrics(new_path)
    result = compare_metrics(base, new)
    return result["verdict"], result
