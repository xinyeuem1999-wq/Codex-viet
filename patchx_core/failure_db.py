# -*- coding: utf-8 -*-
"""P15 — Failure Intelligence: DB lỗi + sinh regression test.

Mỗi lỗi có ERROR_ID, STAGE, pattern (regex khớp thông báo), nguyên nhân,
cách xử lý và test hồi quy. `classify_failure` gắn ERROR_ID cho lỗi mới;
`gen_regression_test` sinh test tự động từ một entry.
"""

import json
import os
import re
import time

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "failure_db.json")

DEFAULT_FAILURES = [
    {
        "error_id": "F-BUILD-001",
        "stage": "BUILD",
        "pattern": r"Syntax error: \"\(\" unexpected",
        "cause": ("Wrapper aapt2 của Termux bị lỗi shell (tệp tạm aapt2_*.tmp "
                  "không chạy được)."),
        "fix": ("Dùng aapt2 thật: apktool b CÂY -o OUT.apk "
                "--aapt /data/data/com.termux/files/usr/bin/aapt2"),
        "regression": "test_golden_rebuild",
    },
    {
        "error_id": "F-BUILD-002",
        "stage": "BUILD",
        "pattern": r"has invalid entry name",
        "cause": "Tên resource chứa ký tự '$' làm aapt2 báo entry name lỗi.",
        "fix": ("Chạy apk-fix-res để chuẩn hóa tên resource, rồi cập nhật "
                "tham chiếu public.xml/drawable."),
        "regression": "test_resource_fix_sach_tham_chieu",
    },
    {
        "error_id": "F-BUILD-003",
        "stage": "SIGN",
        "pattern": r"e_type",
        "cause": "Zipalign báo lỗi e_type (ELF 32/64 bit không khớp).",
        "fix": "Bỏ qua zipalign (fallback) hoặc dùng zipalign đúng kiến trúc; "
               "apksigner verify v1/v2/v3 vẫn đạt.",
        "regression": "test_package_gioi_han_3_ban",
    },
    {
        "error_id": "F-DEX-001",
        "stage": "PREFLIGHT",
        "pattern": r"method refs.*vượt|DEX.*(BLOCK|overflow)|65536",
        "cause": "Cây APK vượt giới hạn 64K method refs của một dex.",
        "fix": "Không apply; giảm refs (xóa code/khối REMOVE_FILES) hoặc "
               "chia multi-dex trước khi patch.",
        "regression": "test_dex_budget",
    },
    {
        "error_id": "F-DEX-002",
        "stage": "BUILD",
        "pattern": (r"Unsigned short value out of range|"
                    r"Invalid or truncated dex file|"
                    r"Failed to open dex file|"
                    r"class has already been interned"),
        "cause": ("Apktool/smali để lại classes*.dex dở dang khi build fail "
                  "hoặc bị retry dùng cache cũ: header DEX zero/thiếu; "
                  "thường gặp khi method_ids đã chạm 64K rồi patch thêm "
                  "method ref."),
        "fix": ("Xoá tree/build trước mỗi lần build/retry (đã có trong "
                "_build_apktool); nếu vẫn báo Unsigned short out of range "
                "thì tách bớt smali sang smali_classesN để mỗi dex dưới 64K, "
                "rồi apk-fix-res + build lại."),
        "regression": "test_failure_dex_cache_p15",
    },
    {
        "error_id": "F-PATCH-001",
        "stage": "APPLY",
        "pattern": r"lỗi nén|Bad CRC|Corrupt|ZipFile|invalid entry",
        "cause": "Zip patch nguồn hỏng (entry nén lỗi) — ví dụ "
                 "SignatureHack_arm64.zip entry libfrida-gadget.so.",
        "fix": "Thay bản lành từ Modder Hub; quét dupes theo hash; sao lưu "
               "bản hỏng trước khi thay.",
        "regression": "test_corrupt_zip",
    },
    {
        "error_id": "F-RUNTIME-001",
        "stage": "RUNTIME_M2",
        "pattern": r"FATAL EXCEPTION|ANR in",
        "cause": "App crash/ANR khi chạy (runtime M2 thất bại).",
        "fix": "Đọc crash_lines/anr_lines trong runtime_report.json, sửa "
               "patch gây lỗi, build lại và verify lại.",
        "regression": "test_runtime_status_p13",
    },
    {
        "error_id": "F-ENV-001",
        "stage": "ENV",
        "pattern": r"Address already in use|Errno 98",
        "cause": "Cổng server webui đã có tiến trình khác chiếm giữ.",
        "fix": "Tắt server cũ (pkill -f webui/server.py) hoặc đổi --port.",
        "regression": "test_report_dashboard",
    },
    {
        "error_id": "F-SCAN-001",
        "stage": "SCAN",
        "pattern": r"MemoryError|RecursionError|Killed",
        "cause": "APK cây lớn (hàng trăm MB) làm regex toàn cây tốn bộ nhớ.",
        "fix": "Dùng fast scanner (rg/hash/index + cache theo hash APK), "
               "roadmap thay vì quét toàn cây, giới hạn mẫu.",
        "regression": "test_bench_scan",
    },
    {
        "error_id": "F-SEM-001",
        "stage": "PLAN",
        "pattern": r"AMBIGUOUS_TARGET",
        "cause": ("Semantic-plan V2 có nhiều ứng viên đạt chính sách; chọn "
                  "ứng viên đứng đầu sẽ là dương tính giả tiềm ẩn."),
        "fix": ("Không tự chọn: siết selector.all/near_entry, tăng min_score "
                "hoặc trình người dùng chọn đúng một ứng viên."),
        "regression": "test_semantic_evidence_v2",
    },
    {
        "error_id": "F-SEM-002",
        "stage": "PLAN",
        "pattern": r"INSUFFICIENT_EVIDENCE",
        "cause": ("Thiếu app-model/V2 hoặc thiếu dữ liệu cần thiết để đánh "
                  "giá selector của semantic-plan V2."),
        "fix": ("Sinh model V2 bằng `patchx model CÂY --v2` trước, rồi chạy "
                "lại `patchx semantic-plan CÂY PLAN`."),
        "regression": "test_semantic_evidence_v2",
    },
    {
        "error_id": "F-SEM-003",
        "stage": "PREFLIGHT",
        "pattern": r"cây APK đã thay đổi",
        "cause": ("Draft V2 khóa hash cây APK, nhưng cây đã bị sửa sau khi "
                  "compile plan — evidence không còn đúng."),
        "fix": ("Không áp draft: chạy lại semantic-plan + plan-compile trên "
                "cây hiện tại để khóa evidence mới."),
        "regression": "test_semantic_evidence_v2",
    },
    {
        "error_id": "F-SEM-004",
        "stage": "PLAN",
        "pattern": r"NO_CONFIDENT_TARGET",
        "cause": ("Không có ứng viên đạt min_score: selector quá chặt hoặc "
                  "mã đích đã đổi cấu trúc/ngữ nghĩa."),
        "fix": ("Nới selector có kiểm soát hoặc dùng version-map/knowledge V2 "
                "để tìm ứng viên tương đồng rồi đánh giá lại."),
        "regression": "test_semantic_evidence_v2",
    },
]


def _ensure_db_path(db_path):
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    return os.path.abspath(db_path)


def load_db(db_path=None):
    """Đọc DB — hợp nhất entry mặc định + entry tùy chỉnh (nếu có)."""
    path = _ensure_db_path(db_path)
    entries = list(DEFAULT_FAILURES)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                extra = json.load(fh)
            if isinstance(extra, list):
                entries.extend(extra)
        except (OSError, ValueError):
            pass
    return entries


def save_db(entries, db_path=None):
    path = _ensure_db_path(db_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, ensure_ascii=False, indent=2)
    return path


def add_failure(entry, db_path=None):
    """Thêm entry — ERROR_ID phải duy nhất; trả entry đã thêm."""
    eid = str(entry.get("error_id", "")).strip()
    if not eid:
        raise ValueError("error_id không được để trống")
    if not entry.get("pattern"):
        raise ValueError("pattern không được để trống")
    entries = load_db(db_path)
    if any(e.get("error_id") == eid for e in entries):
        raise ValueError("error_id đã tồn tại: %s" % eid)
    for key in ("stage", "cause", "fix", "regression"):
        entry.setdefault(key, "")
    entries.append(entry)
    path = save_db(entries, db_path)
    return entry, path


def classify_failure(message, stage=None, db_path=None):
    """Tìm entry khớp thông báo — trả entry đầu tiên (hoặc None)."""
    if not message:
        return None
    for e in load_db(db_path):
        if stage and e.get("stage") != stage:
            continue
        try:
            if re.search(e["pattern"], message, re.I):
                return e
        except re.error:
            continue
    return None


def render_report(db_path=None):
    entries = load_db(db_path)
    lines = ["# Failure Intelligence (P15)", "",
             "| ERROR_ID | Stage | Pattern | Nguyên nhân | Xử lý | Regression |",
             "|----------|-------|---------|-------------|-------|------------|"]
    for e in entries:
        lines.append("| %s | %s | `%s` | %s | %s | %s |"
                     % (e.get("error_id"), e.get("stage"), e.get("pattern"),
                        e.get("cause"), e.get("fix"),
                        e.get("regression")))
    lines.append("")
    lines.append("Tổng: %d lỗi trong DB." % len(entries))
    return "\n".join(lines)


def gen_regression_test(entry, test_name=None):
    """Sinh mã test Python từ entry — trả chuỗi nguồn test."""
    eid = entry.get("error_id", "F-XXX")
    stage = entry.get("stage", "")
    pattern = entry["pattern"]
    test_name = test_name or ("test_failure_" + re.sub(r"[^A-Za-z0-9]", "_",
                                                       eid).lower())
    return (
        f"def {test_name}():\n"
        f"    \"\"\"P15 — Regression cho {eid} (stage {stage}).\"\"\"\n"
        f"    from patchx_core.failure_db import classify_failure\n"
        f"    hit = classify_failure({pattern!r}, stage={stage!r})\n"
        f"    check(\"P15: {eid} phân loại đúng\",\n"
        f"          hit is not None and hit[\"error_id\"] == {eid!r},\n"
        f"          str(hit.get(\"error_id\") if hit else None))\n"
    )
