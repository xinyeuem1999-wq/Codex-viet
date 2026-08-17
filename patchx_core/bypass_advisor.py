# -*- coding: utf-8 -*-
"""Bypass Advisor — phân tích dữ liệu quét APK thành báo cáo triển khai.

Nhận kết quả coverage (đã quét) + cache nội dung cây APK, sinh:
  - danh sách điểm bypass cụ thể (tệp, khối, số khớp, biến thể mở rộng);
  - cách làm và công cụ cho từng năng lực patch;
  - các lớp bảo vệ phát hiện được trong APK (root, SafetyNet, pinning, ...);
  - phương án triển khai từng bước + đề xuất tăng khả năng thành công;
  - ước lượng tỷ lệ thành công (%).

Mọi thông báo bằng tiếng Việt; chuỗi kỹ thuật giữ nguyên gốc.
"""

import re

# --- Ưu tiên năng lực (càng khó/giá trị càng cao) ---
CAP_PRIORITY = {
    "bypass-license": 1.00, "integrity": 0.95, "google": 0.90,
    "purchase": 0.88, "token": 0.85, "api": 0.80, "trace": 0.75,
    "shell": 0.70, "ssl-pinning": 0.68, "root-hide": 0.65,
    "anonymity": 0.60, "anti-debug": 0.57, "frida-hide": 0.56,
    "id-spoof": 0.55, "ads": 0.50, "network": 0.45, "emulator": 0.42,
    "permission": 0.35,
    "installer": 0.30, "save": 0.25, "ui": 0.20, "font": 0.10,
}

# --- Cách làm + công cụ theo năng lực ---
CAP_TOOLING = {
    "bypass-license": {
        "cách": "Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, "
                "nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra "
                "bằng Frida/LSPosed.",
        "công_cụ": ["patchx apply", "apktool", "apksigner", "Frida", "LSPosed"],
        "xác_minh": "Mở tính năng VIP; xem logcat tìm log trạng thái license.",
    },
    "purchase": {
        "cách": "Giả lập mua hàng trong app: vô hiệu hoá lời gọi "
                "queryPurchases/getBuyIntent (MATCH_REPLACE), hoặc trả trạng "
                "thái đã mua qua SET_BOOL/MATCH_ASSIGN như Lucky Patcher.",
        "công_cụ": ["patchx apply", "apktool", "Lucky Patcher"],
        "xác_minh": "Bấm mua trong app và xác nhận thành công không trừ tiền.",
    },
    "integrity": {
        "cách": "Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) "
                "hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).",
        "công_cụ": ["patchx apply", "apktool", "apksigner"],
        "xác_minh": "Xoá báo lỗi 'signature mismatch'/'app modified' khi mở ứng dụng.",
    },
    "google": {
        "cách": "Bỏ kiểm tra Google Play Services/SafetyNet: gỡ hoặc bỏ qua khối "
                "attestation, thay bằng kết quả giả.",
        "công_cụ": ["patchx apply", "apktool", "LSPosed"],
        "xác_minh": "Mở ứng dụng khi không có Google Play đầy đủ; kiểm tra logcat.",
    },
    "root-hide": {
        "cách": "Vô hiệu hoá kiểm tra root: comment lời gọi isRooted/RootBeer "
                "và gán kết quả false (MATCH_REPLACE), hoặc hook hàm kiểm tra "
                "bằng Frida/Magisk DenyList.",
        "công_cụ": ["patchx apply", "apktool", "Frida", "Magisk"],
        "xác_minh": "Mở app trên máy đã root, xác nhận không bị chặn.",
    },
    "ssl-pinning": {
        "cách": "Bỏ khoá chứng chỉ: comment lời gọi checkServerTrusted trong "
                "X509TrustManager hoặc vô hiệu hoá CertificatePinner, sau đó "
                "dùng proxy (mitmproxy/Charles) bắt gói.",
        "công_cụ": ["patchx apply", "apktool", "Frida", "objection",
                    "mitmproxy"],
        "xác_minh": "Bắt được HTTPS qua proxy không báo lỗi chứng chỉ.",
    },
    "anti-debug": {
        "cách": "Chống phát hiện gỡ lỗi: gán kết quả isDebuggerConnected về "
                "false, xoá kiểm tra TracerPid bằng MATCH_REPLACE/SET_BOOL.",
        "công_cụ": ["patchx apply", "apktool"],
        "xác_minh": "Chạy app trong trình gỡ lỗi mà không tự thoát.",
    },
    "frida-hide": {
        "cách": "Ẩn dấu vết Frida: thay chuỗi 'frida' bằng giá trị giả, comment "
                "lời gọi checkFrida/findFrida, tránh phát hiện gadget.",
        "công_cụ": ["patchx apply", "apktool"],
        "xác_minh": "Mở app khi có Frida trong bộ nhớ, xác nhận không bị chặn.",
    },
    "emulator": {
        "cách": "Bỏ kiểm tra máy ảo: gán kết quả isEmulator/findBinary về "
                "false, sửa Build.FINGERPRINT trả về thiết bị thật.",
        "công_cụ": ["patchx apply", "apktool", "Frida"],
        "xác_minh": "Mở app trên máy ảo, xác nhận không bị chặn.",
    },
    "token": {
        "cách": "Quét và vô hiệu hoá endpoint lấy token: chặn MATCH_REPLACE chuỗi "
                "token/khóa, thay bằng chuỗi giả hoặc hook trả token hợp lệ.",
        "công_cụ": ["patchx apply", "Frida", "logcat", "tcpdump"],
        "xác_minh": "Bắt mạng (tcpdump/Frida) xem token gửi đi sau khi patch.",
    },
    "api": {
        "cách": "Tìm API thật bằng log API_LOG/TRACE, sau đó thay domain/endpoint "
                "trong MATCH_REPLACE hoặc chặn tại class xử lý mạng.",
        "công_cụ": ["patchx apply", "Frida", "logcat"],
        "xác_minh": "Theo dõi log chứa endpoint sau khi kích hoạt chức năng.",
    },
    "trace": {
        "cách": "Bật truy vết dữ liệu: chèn TRACE/API_LOG vào method mục tiêu để "
                "đọc tham số và phản hồi trước khi quyết định patch.",
        "công_cụ": ["patchx apply", "logcat"],
        "xác_minh": "Đọc logcat thấy dữ liệu mong muốn in ra.",
    },
    "shell": {
        "cách": "Chèn khởi tạo mod qua INIT/HOOK_SCRIPT: chạy lệnh/script khi app "
                "mở để bơm biến hoặc gọi hàm nội bộ.",
        "công_cụ": ["patchx apply", "apktool", "Frida"],
        "xác_minh": "Kiểm tra hiệu lực mod ngay sau khi app khởi động.",
    },
    "ads": {
        "cách": "Chặn quảng cáo: thay URL ad network bằng chuỗi rỗng hoặc bỏ qua "
                "khối hiển thị quảng cáo.",
        "công_cụ": ["patchx apply", "apktool"],
        "xác_minh": "Chạy app và xác nhận không còn banner/interstitial.",
    },
    "id-spoof": {
        "cách": "Giả mạo ID thiết bị: sửa MATCH_REPLACE chuỗi trả về device id, "
                "hoặc hook hàm lấy ID bằng Frida.",
        "công_cụ": ["patchx apply", "Frida"],
        "xác_minh": "Đối chiếu ID app đọc được sau khi patch.",
    },
    "anonymity": {
        "cách": "Ẩn danh: vô hiệu hoá thu thập định danh (analytics), thay chuỗi "
                "identifiers bằng giá trị giả.",
        "công_cụ": ["patchx apply", "apktool"],
        "xác_minh": "Xem log/bắt mạng không còn dữ liệu định danh thật.",
    },
    "permission": {
        "cách": "Điều chỉnh quyền: sửa AndroidManifest.xml (thêm/bớt quyền, "
                "debuggable, backup).",
        "công_cụ": ["patchx apply", "apktool"],
        "xác_minh": "Cài APK, kiểm tra danh sách quyền hiển thị.",
    },
    "network": {
        "cách": "Điều khiển mạng: chặn/gỡ giới hạn mạng hoặc thay endpoint bằng "
                "server giả lập.",
        "công_cụ": ["patchx apply", "Frida", "tcpdump"],
        "xác_minh": "Bắt mạng xác nhận request đến endpoint mong muốn.",
    },
    "installer": {
        "cách": "Bỏ kiểm tra nguồn cài đặt: sửa luồng kiểm tra installer "
                "(getInstallerPackageName) trả về giá trị hợp lệ.",
        "công_cụ": ["patchx apply", "apktool"],
        "xác_minh": "Mở app ngay sau khi cài từ file APK.",
    },
    "save": {
        "cách": "Gỡ giới hạn lưu trữ: bỏ khoá tính năng lưu, thay điều kiện "
                "trả true (SET_BOOL) hoặc bỏ qua khối giới hạn.",
        "công_cụ": ["patchx apply", "apktool"],
        "xác_minh": "Thử lưu/nâng cấp trong app.",
    },
    "ui": {
        "cách": "Điều chỉnh giao diện: sửa văn bản/màu/bố cục trong res/XML.",
        "công_cụ": ["patchx apply", "apktool"],
        "xác_minh": "Mở app xác nhận thay đổi hiển thị.",
    },
    "font": {
        "cách": "Thay font chữ trong res/font.",
        "công_cụ": ["patchx apply", "apktool"],
        "xác_minh": "Mở app xác nhận font mới.",
    },
}

# --- Dấu hiệu lớp bảo vệ trong APK (quét nhanh trên nội dung đã đọc) ---
PROTECTION_PATTERNS = [
    ("root", ["isRooted", "RootBeer", "checkForRoot", "findBinary",
              "DetectRoot", "RootCheck", "su -c"]),
    ("safetynet", ["SafetyNet", "PlayIntegrity", "attestation",
                   "DeviceCheck", "integrity verdict"]),
    ("frida", ["frida", "gum-js-loop", "frida-server", "checkFrida",
               "findFrida", "ioctl", "ptrace"]),
    ("signature", ["checkSignature", "signature check", "checkSigning",
                   "PackageManager.SIGNATURE"]),
    ("anti-debug", ["isDebuggerConnected", "anti-debug", "Debug.isDebugger",
                    "TracerPid"]),
    ("pinning", ["CertificatePinner", "ssl pinning", "X509TrustManager",
                 "checkServerTrusted"]),
    ("emulator", ["isEmulator", "goldfish", "generic", "Genymotion",
                  "Build.FINGERPRINT"]),
    ("root-hide", ["Magisk", "hide root", "detect magisk", "SafetyNet",
                   "ctsProfileMatch"]),
    ("tamper", ["getPackageInfo", "ApplicationInfo.FLAG_DEBUGGABLE",
                "checkIntSig", "verifySignature"]),
]
# Mức phạt (% điểm) cho mỗi lớp bảo vệ xuất hiện
PROTECTION_PENALTY = {
    "root": 12.0, "safetynet": 18.0, "signature": 20.0,
    "anti-debug": 10.0, "pinning": 15.0, "emulator": 8.0, "root-hide": 10.0,
    "frida": 10.0, "tamper": 8.0,
}

# Khối thực thi hiện đại đã kiểm chứng (đáng tin hơn khi dự đoán)
MODERN_BLOCKS = ("SET_BOOL", "INIT", "HOOK_SCRIPT", "TRACE", "API_LOG",
                 "REMOTE_CONFIG")


def detect_protections(texts):
    """Quét nhanh dấu hiệu bảo vệ trong cache nội dung cây APK."""
    if not texts:
        return []
    hits = {name: {"loại": name, "tên": name, "lần": 0, "tệp": set()}
            for name, _ in PROTECTION_PATTERNS}
    for rel, text in texts.items():
        for name, keywords in PROTECTION_PATTERNS:
            for kw in keywords:
                if kw in text:
                    hits[name]["lần"] += 1
                    hits[name]["tệp"].add(rel)
    found = []
    for h in hits.values():
        if h["lần"]:
            h["tệp"] = sorted(h["tệp"])[:5]
            found.append(h)
    return sorted(found, key=lambda x: -x["lần"])


def detect_protections_fast(tree_root, cache=None):
    """Quét nhanh dấu hiệu bảo vệ bằng rg (không nạp toàn bộ text vào RAM).

    `lần` là số tệp chứa dấu hiệu — bằng chứng đo được từ dữ liệu thật.
    """
    from .advisor import ScanCache
    sc = cache if cache is not None else ScanCache(tree_root)
    keywords = [kw for _name, kws in PROTECTION_PATTERNS for kw in kws]
    sc.ensure(keywords)
    found = []
    for name, kws in PROTECTION_PATTERNS:
        files = set()
        for kw in kws:
            files |= sc.candidates(kw) or set()
        if files:
            found.append({"loại": name, "tên": name,
                          "lần": len(files), "tệp": sorted(files)[:5]})
    return sorted(found, key=lambda x: -x["lần"])


def _cap_priority(caps):
    if not caps:
        return 0.05
    return max(CAP_PRIORITY.get(c, 0.05) for c in caps)


def estimate_success(cov, caps, protections, modern_ratio=0.0):
    """Ước lượng tỷ lệ thành công (%) và giải thích các yếu tố ảnh hưởng."""
    matches = sum(d.get("khớp", 0) for d in cov.get("chi_tiết", []))
    quy_tắc = max(1, cov.get("quy_tắc", 0))
    phan = 100.0 * (
        0.45 * cov.get("tỷ_lệ", 0.0)
        + 0.20 * min(1.0, matches / 25.0)
        + 0.15 * min(1.0, cov.get("quy_tắc_khớp", 0) / quy_tắc)
        + 0.10 * _cap_priority(caps)
        + 0.10 * min(1.0, modern_ratio)
    )
    factors = [
        ("Bao phủ quy tắc khớp %.0f%%" % (cov.get("tỷ_lệ", 0.0) * 100),
         0.45 * cov.get("tỷ_lệ", 0.0) * 100),
        ("Số lần khớp %d (tối đa 25)" % matches,
         0.20 * min(1.0, matches / 25.0) * 100),
        ("Khối khớp %d/%d" % (cov.get("quy_tắc_khớp", 0), quy_tắc),
         0.15 * min(1.0, cov.get("quy_tắc_khớp", 0) / quy_tắc) * 100),
        ("Độ ưu tiên năng lực %.2f" % _cap_priority(caps),
         0.10 * _cap_priority(caps) * 100),
    ]
    if modern_ratio:
        factors.append(("Tỷ lệ khối hiện đại %.0f%%" % (modern_ratio * 100),
                        0.10 * modern_ratio * 100))
    penalties = []
    for p in protections:
        pen = PROTECTION_PENALTY.get(p["loại"], 10.0)
        penalties.append((p["loại"], pen))
        phan -= pen
    rate = max(0.0, min(100.0, phan))
    return {
        "tỷ_lệ": round(rate, 1),
        "yếu_tố": [{"tên": n, "điểm": round(v, 1)} for n, v in factors],
        "phạt": [{"loại": n, "điểm": round(v, 1)} for n, v in penalties],
    }


def _modern_ratio(patch):
    """Tỷ lệ khối thực thi hiện đại trong patch (0..1)."""
    if not getattr(patch, "sections", None):
        return 0.0
    types = [s.type for s in patch.sections if s.type]
    if not types:
        return 0.0
    return sum(1 for t in types if t in MODERN_BLOCKS) / float(len(types))


def _tooling_for(caps):
    """Gộp cách làm + công cụ từ danh sách năng lực."""
    seen = []
    tools = []
    for c in caps:
        t = CAP_TOOLING.get(c)
        if not t or c in seen:
            continue
        seen.append(c)
        for tool in t["công_cụ"]:
            if tool not in tools:
                tools.append(tool)
    return {
        "cách": [CAP_TOOLING[c]["cách"] for c in seen],
        "công_cụ": tools,
        "xác_minh": [CAP_TOOLING[c]["xác_minh"] for c in seen],
    }


def _bypass_points(cov):
    """Liệt kê điểm bypass cụ thể từ chi tiết coverage."""
    points = []
    for d in cov.get("chi_tiết", []):
        if not d.get("khớp"):
            continue
        points.append({
            "khối": d.get("khối"), "loại": d.get("loại"),
            "target": d.get("target"),
            "khớp": d.get("khớp"),
            "tệp_trúng": d.get("tệp_trúng", [])[:10],
            "biến_thể": d.get("biến_thể", [])[:3],
        })
    return points


def _suggestions(cov):
    """Đề xuất tăng khả năng thành công dựa trên dữ liệu quét."""
    sug = []
    for d in cov.get("chi_tiết", []):
        if d.get("biến_thể"):
            sug.append("Mở rộng MATCH khối %s: %s"
                       % (d.get("khối"), d.get("biến_thể")[0]))
        if d.get("ngoài_target"):
            rel, n = d["ngoài_target"][0]
            sug.append("Chuỗi khối %s còn xuất hiện ngoài target (%s, %d lần) — "
                       "cân nhắc bổ sung class-link"
                       % (d.get("khối"), rel, n))
        if not d.get("khớp") and d.get("target"):
            sug.append("Khối %s trượt target %s — cập nhật TARGET theo "
                       "class-link thật của APK" % (d.get("khối"),
                                                    d.get("target")))
    return sug[:6]


def build_bypass_report(tree, scored, combos, texts=None, limit=10,
                        protections=None):
    """Sinh báo cáo bypass từ dữ liệu quét (scored patches + combos)."""
    if protections is None:
        protections = detect_protections(texts or {})
    items = []
    for x in scored[:limit]:
        cov = {
            "quy_tắc": x.get("rules", 0),
            "quy_tắc_khớp": x.get("rules_matched", 0),
            "tỷ_lệ": x.get("coverage", 0.0),
            "chi_tiết": x.get("chi_tiết", []),
        }
        rate = estimate_success(cov, x.get("capabilities", []),
                                protections, x.get("modern_ratio", 0.0))
        items.append({
            "patch": x["patch"],
            "điểm": x.get("score", 0.0),
            "tỷ_lệ_thành_công": rate["tỷ_lệ"],
            "phân_tích": rate,
            "năng_lực": x.get("capabilities", []),
            "điểm_bypass": _bypass_points(cov),
            "cách_công_cụ": _tooling_for(x.get("capabilities", [])),
            "đề_xuất": _suggestions(cov),
        })
    combo_items = []
    for c in combos[:limit]:
        a = next((i for i in items if i["patch"] == c["patches"][0]), None)
        b = next((i for i in items if i["patch"] == c["patches"][1]), None)
        if not a or not b:
            continue
        rate = round(min(100.0, (a["tỷ_lệ_thành_công"]
                                 + b["tỷ_lệ_thành_công"]) / 2.0
                         + min(len(c.get("support", [])), 6) * 0.8), 1)
        combo_items.append({
            "patches": c["patches"],
            "tỷ_lệ_thành_công": rate,
            "năng_lực": c.get("capabilities", []),
            "bổ_trợ": c.get("support", []),
        })
    best = items[0] if items else None
    best_combo = combo_items[0] if combo_items else None
    plan = _deploy_plan(best, best_combo, protections)
    return {
        "tree": tree,
        "protections": protections,
        "top_patches": items,
        "top_combos": combo_items,
        "plan": plan,
    }


def _deploy_plan(best, best_combo, protections):
    """Đề xuất phương án triển khai theo bước + cách tăng khả năng thành công."""
    if not best:
        return None
    patches = [best["patch"]]
    label = best["patch"]
    if best_combo and best_combo["patches"][0] == best["patch"]:
        patches = list(best_combo["patches"])
        label = " + ".join(patches)
    steps = [
        "Chuẩn bị cây APK (apk-prepare) hoặc dùng cây đã giải mã.",
        "Áp patch: python3 patchx apply %s <cây-apk>" % " ".join(patches),
        "Chuẩn hoá resource chứa `$`: python3 patchx_toolkit.py apk-fix-res",
        "Build: apktool b <cây> -o out.apk --aapt <aapt2-thật>",
        "Zipalign + ký: zipalign -f 4 && apksigner sign",
        "Cài APK, xác minh động bằng logcat/Frida theo mục xác_minh.",
    ]
    risks = []
    for p in protections:
        risks.append("APK có dấu hiệu %s (%d lần) — trừ ~%.0f%% điểm dự đoán; "
                     "ưu tiên patch integrity/token xử lý lớp này."
                     % (p["loại"], p["lần"],
                        PROTECTION_PENALTY.get(p["loại"], 10.0)))
    return {
        "phương_án": label,
        "tỷ_lệ_dự_đoán": best["tỷ_lệ_thành_công"],
        "steps": steps,
        "rủi_ro": risks[:4],
        "tăng_khả_năng": best.get("đề_xuất", []),
    }


def render_markdown(report):
    """Dựng báo cáo Markdown từ dict báo cáo."""
    lines = ["# Báo cáo quét chi tiết — phương án bypass", "",
             "- Cây APK: `%s`" % report["tree"], ""]
    if report["protections"]:
        lines += ["## Lớp bảo vệ phát hiện", "",
                  "| Loại | Số lần | Tệp ví dụ |",
                  "|------|-------:|-----------|"]
        for p in report["protections"]:
            files = ", ".join("`%s`" % f for f in p["tệp"])
            lines.append("| %s | %d | %s |" % (p["loại"], p["lần"], files))
        lines.append("")
    lines += ["## Patch đơn — điểm bypass, công cụ, tỷ lệ thành công", "",
              "| Hạng | Patch | Điểm | Thành công | Khớp | Năng lực |",
              "|------|-------|-----:|-----------:|-----:|----------|"]
    for i, it in enumerate(report["top_patches"], 1):
        lines.append("| %d | %s | %.3f | %.0f%% | %d | %s |" % (
            i, it["patch"], it["điểm"], it["tỷ_lệ_thành_công"],
            sum(p["khớp"] for p in it["điểm_bypass"]),
            ", ".join(sorted(it.get("năng_lực", [])))))
    for it in report["top_patches"]:
        lines += ["", "### %s — dự đoán %.0f%%" % (it["patch"],
                                                   it["tỷ_lệ_thành_công"])]
        if it["cách_công_cụ"]["cách"]:
            lines.append("")
            for c in it["cách_công_cụ"]["cách"]:
                lines.append("- Cách: %s" % c)
            lines.append("- Công cụ: %s"
                         % ", ".join("`%s`" % t
                                     for t in it["cách_công_cụ"]["công_cụ"]))
        if it["điểm_bypass"]:
            lines += ["", "Điểm bypass cụ thể:"]
            for p in it["điểm_bypass"][:8]:
                files = ", ".join("`%s`" % f for f in p["tệp_trúng"][:4])
                lines.append("- Khối %s (%s) target `%s`: %d khớp — %s"
                             % (p["khối"], p["loại"], p["target"],
                                p["khớp"], files))
        if it["đề_xuất"]:
            lines += ["", "Đề xuất tăng khả năng thành công:"]
            for s in it["đề_xuất"]:
                lines.append("- %s" % s)
    if report["top_combos"]:
        lines += ["", "## Combo bổ trợ", "",
                  "| Patch 1 | Patch 2 | Thành công | Bổ trợ |",
                  "|---------|---------|-----------:|--------|"]
        for c in report["top_combos"]:
            lines.append("| %s | %s | %.0f%% | %s |" % (
                c["patches"][0], c["patches"][1], c["tỷ_lệ_thành_công"],
                ", ".join("%s→%s" % s for s in c["bổ_trợ"][:3])))
    if report["plan"]:
        pl = report["plan"]
        lines += ["", "## Phương án triển khai đề xuất", "",
                  "- Phương án: %s" % pl["phương_án"],
                  "- Tỷ lệ thành công dự đoán: %.0f%%" % pl["tỷ_lệ_dự_đoán"],
                  ""]
        for i, s in enumerate(pl["steps"], 1):
            lines.append("%d. %s" % (i, s))
        if pl["rủi_ro"]:
            lines += ["", "Rủi ro:"]
            for r in pl["rủi_ro"]:
                lines.append("- %s" % r)
        if pl["tăng_khả_năng"]:
            lines += ["", "Đề xuất nâng tỷ lệ:"]
            for s in pl["tăng_khả_năng"]:
                lines.append("- %s" % s)
    return "\n".join(lines)
