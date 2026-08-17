# -*- coding: utf-8 -*-
"""T4 — thông minh (học + đề xuất): kho combo thành công, gợi ý theo danh
mục APK, và khung patch theo ý định mod (người dùng duyệt trước khi áp)."""

import json
import os
import re
import time

from .optimizer import (CAP_LABELS, find_conflicts, merge_patches,
                        patch_capabilities)
from .session import load_patch_map


CATEGORY_KEYWORDS = [
    ("game", ("unity", "garena", "supercell", "riot", "vng", "game",
              "com.tencent", "miHoYo", "hoyoverse")),
    ("ngân hàng/tài chính", ("bank", "vpbank", "timo", "momo", "zalopay",
                             "vnptpay", "pay", "finance")),
    ("mạng xã hội", ("facebook", "zalo", "messenger", "tiktok", "whatsapp",
                     "telegram", "social")),
    ("mua sắm", ("shopee", "lazada", "tiki", "sendo", "amazon", "shopping")),
]

INTENT_KEYWORDS = {
    "bypass-license": ("vip", "license", "bản quyền", "khoá", "premium",
                       "pro", "unlock", "mở khoá"),
    "purchase": ("mua hàng", "iap", "in-app", "billing", "giả lập mua"),
    "ads": ("quảng cáo", "ads", "advert", "chặn quảng cáo"),
    "shell": ("shell", "vỏ", "token"),
    "integrity": ("toàn vẹn", "integrity", "signature", "chữ ký",
                  "sigcheck", "xác thực"),
    "google": ("google", "play protect", "play protect"),
    "root-hide": ("root", "magisk", "ẩn root", "quyền root"),
    "ssl-pinning": ("ssl", "pinning", "chứng chỉ", "bắt gói", "proxy",
                    "certificate"),
    "anti-debug": ("debug", "gỡ lỗi", "debugger"),
    "frida-hide": ("frida", "kiểm tra frida", "ẩn frida"),
    "emulator": ("máy ảo", "emulator", "giả lập máy"),
    "trace": ("truy vết", "trace", "theo dõi", "dữ liệu"),
    "anonymity": ("ẩn danh", "anonym", "giấu"),
}


def success_store_path(root):
    return os.path.join(root, "combos_success.json")


def record_success(root, entry):
    """Ghi combo/chuỗi patch áp thành công vào kho (kèm danh mục app)."""
    path = success_store_path(root)
    data = []
    if os.path.isfile(path):
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception:
            data = []
    data.append(dict(entry, ts=time.strftime("%Y-%m-%d %H:%M:%S")))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    return path


def categorize(package_name):
    pkg = (package_name or "").lower()
    for cat, pats in CATEGORY_KEYWORDS:
        if any(p.lower() in pkg for p in pats):
            return cat
    return "chung"


def intent_capabilities(intent_text):
    """Từ mô tả ý định → tập năng lực (keyword đơn giản, cục bộ)."""
    low = (intent_text or "").lower()
    caps = set()
    for cap, kws in INTENT_KEYWORDS.items():
        if any(k.lower() in low for k in kws):
            caps.add(cap)
    if not caps:
        caps.add("bypass-license")  # mặc định: ý định mod thường là bypass
    return caps


def suggest_by_intent(intent_text, patches, caps=None):
    """Chọn patch theo ý định — trả list dict {patch, năng_lực}."""
    caps = caps or intent_capabilities(intent_text)
    scored = []
    for name, p in patches.items():
        pcaps = patch_capabilities(p)
        hit = pcaps & caps
        if hit:
            scored.append({"patch": name, "năng_lực": sorted(hit),
                           "khớp_ý_định": len(hit)})
    scored.sort(key=lambda x: -x["khớp_ý_định"])
    return scored, caps


def build_skeleton(patches, selected_names, name):
    """Gộp các patch đã chọn thành một khung patch (combo) tự chứa."""
    sel = [patches[n] for n in selected_names if n in patches]
    merged = merge_patches(sel, name)
    conflicts = len(find_conflicts(sel))
    return merged, conflicts


def suggest_plan(tree, collection, top=8):
    """Gợi ý chuỗi patch cho APK thật: coverage + danh mục + combo thành công."""
    from .advisor import coverage_patch
    from .smali_sem import entry_classes
    patches = load_patch_map(collection)
    app, launchers = entry_classes(tree)
    cat = categorize((app or launchers[0] if launchers else ""))
    scored = []
    for name, p in patches.items():
        try:
            cov = coverage_patch(p, tree)
        except Exception:
            continue
        if cov["quy_tắc_khớp"] > 0:
            scored.append({"patch": name,
                           "tỷ_lệ": cov["tỷ_lệ"],
                           "khớp": cov["quy_tắc_khớp"],
                           "năng_lực": sorted(patch_capabilities(p))})
    scored.sort(key=lambda x: (-x["tỷ_lệ"], -x["khớp"]))
    store = success_store_path(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    history = []
    if os.path.isfile(store):
        try:
            history = [e for e in json.load(open(store, encoding="utf-8"))
                       if e.get("danh_mục") == cat]
        except Exception:
            history = []
    return {"package": app or (launchers[0] if launchers else ""),
            "danh_mục": cat,
            "khớp": scored[:top],
            "combo_đã_thành_công": history[-5:],
            "gợi_ý": "Chuỗi khuyến nghị: " + ", ".join(
                s["patch"] for s in scored[:3]) if scored else
            "Không có patch khớp APK này."}
