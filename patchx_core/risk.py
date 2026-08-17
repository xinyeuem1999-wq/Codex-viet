# -*- coding: utf-8 -*-
"""T5 — cờ rủi ro chuỗi cung ứng: phát hiện hành vi nguy hiểm trong patch
(gửi dữ liệu ra ngoài, tắt bảo mật hệ thống) → cảnh báo trong báo cáo.

Lưu ý: chỉ là phát hiện tĩnh theo quy tắc — không phán quyết pháp lý.
"""

import re


RISK_RULES = [
    ("gửi-dữ-liệu",
     "URL http/https trong nội dung patch — có thể gửi dữ liệu ra ngoài",
     re.compile(r"https?://", re.I)),
    ("gửi-dữ-liệu",
     "gọi HttpURLConnection / Socket / OkHttp / Retrofit trong smali",
     re.compile(r"(HttpURLConnection|Ljava/net/Socket|okhttp|Retrofit)",
                re.I)),
    ("tắt-bảo-mật",
     "vô hiệu hoá kiểm tra (sigcheck/verify) hoặc bật debuggable/cleartext",
     re.compile(r"(sigcheck|verify\s*\(|allowBackup=\"true\"|"
                r"usesCleartextTraffic=\"true\"|debuggable=\"true\")", re.I)),
    ("quyền-hệ-thống",
     "cấp quyền hệ thống (pm grant / setComponentEnabledSetting)",
     re.compile(r"(pm grant|setComponentEnabledSetting|grantUriPermission)",
                re.I)),
    ("thu-thập",
     "đọc dữ liệu nhạy cảm (IMEI / device id / tài khoản / oauth)",
     re.compile(r"(getDeviceId|IMEI|getSubscriberId|getAccounts|oauth)", re.I)),
    ("mạng-ngầm",
     "REMOTE_CONFIG / CONFIG_URL — tải cấu hình từ xa",
     re.compile(r"CONFIG_URL|REMOTE_CONFIG")),
]


def _section_text(sec):
    keys = ("MATCH", "REPLACE", "ASSIGN", "GOTO", "CODE", "VALUE", "SOURCE",
            "SCRIPT", "TARGET", "METHOD", "CONFIG_URL")
    parts = []
    for k in keys:
        v = sec.get(k)
        if v:
            parts.append(str(v))
    return "\n".join(parts)


def risk_findings(patch):
    """Quét patch — trả list dict {mức, loại, nội_dung, khối}."""
    out = []
    for sec in patch.sections:
        text = _section_text(sec)
        for loại, desc, rx in RISK_RULES:
            if rx.search(text):
                out.append({"mức": "rủi-ro", "loại": loại,
                            "nội_dung": desc, "khối": sec.order})
    # Gộp trùng (nhiều khối cùng quy tắc → 1 cảnh báo)
    seen = set()
    uniq = []
    for f in out:
        key = f["loại"]
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return uniq
