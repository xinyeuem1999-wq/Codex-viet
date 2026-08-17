# -*- coding: utf-8 -*-
"""Tự phát hiện các patch bổ trợ cho nhau — phiên bản 2 (gộp theo họ thực tế).

Thiết kế mới (sau khi đánh giá phiên bản 1 không hiệu quả):
  1. GỘP THEO HỌ: mỗi patch được xếp vào các họ chức năng HẸP (ads, id-spoof,
     license, shell, toàn vẹn, google, theme, splash, toast, screen, mạng,
     ẩn danh, lưu trữ, quyền, cài đặt). Các patch cùng họ gộp thành combo,
     xung đột tự tách. KHÔNG gộp chéo họ qua chuỗi năng lực.
  2. BỔ TRỢ CLASS-LINK: patch CUNG CẤP class (ADD_FILES/asset .smali) mà patch
     khác DÙNG (MATCH/REPLACE) -> combo bổ trợ, kèm bằng chứng class.
  3. Patch không thuộc họ nào và không có class-link -> liệt kê cô lập.

Kết quả: combo thật sự có ý nghĩa (cùng mục tiêu), không bị trộn lẫn.
"""

import re

from .optimizer import merge_patches, find_conflicts
from .parser import parse_patch_file

CLASS_RE = re.compile(r"L([a-zA-Z0-9_/$]+);")
SMALI_CLASS_RE = re.compile(r"\.class\s+(?:[a-z]+\s+)*L([a-zA-Z0-9_/$]+);")
FRAMEWORK_PREFIXES = ("Landroid/", "Ljava/", "Ldalvik/", "Lkotlin/", "Lorg/",
                      "Ljunit/", "Lcom/google/android/", "Lcom/google/firebase/",
                      "Lcom/google/gms/", "Landroidx/")

# Họ chức năng hẹp — từ khóa tên patch (không gộp chéo họ)
FAMILY_RULES = [
    ("ads", ("ads", "advert", "banner", "reklama", "remove_ads",
             "antiqueclam", "anti-ads", "anti-advertising")),
    ("id-spoof", ("androidid", "android_id", "deviceid", "device_id", "imei",
                  "serial", "serialno", "bssid", "bluetooth", "wifi_mac",
                  "mac_address", "spoof-id", "sernum", "brand")),
    ("license", ("license", "vip", "premium", "activator", "ispremium",
                 "accounts_hack", "auth_vk", "billing")),
    ("signature", ("signature", "sigcheck", "bin_sig", "bypass_sig",
                   "signaturehack")),
    ("google", ("google", "gms", "gservices", "play")),
    ("shell", ("shell", "frida", "gadget", "dex", "script", "entrance",
               "hook", "inject")),
    ("token", ("token", "oauth", "session")),
    ("api", ("api", "endpoint", "retrofit", "okhttp")),
    ("trace", ("trace", "logcat", "logging", "debug", "dump", "flow",
               "ref_logging")),
    ("mạng", ("internet", "wifi", "disconnect", "nowifi", "noplaygames")),
    ("ẩn danh", ("anonymous", "anonymity", "fake", "gps", "mock", "location",
                 "nointernet", "hide", "privacy", "ẩn danh")),
    ("quyền", ("permission", "camera", "recordaudio", "sms", "contact",
               "calendar", "phone", "memory")),
    ("lưu trữ", ("save", "data_editor", "mem_editor", "duplicate")),
    ("theme", ("theme", "dark", "holo", "material", "appcompat")),
    ("splash", ("splash",)),
    ("toast", ("toast", "dialog", "notify", "alert")),
    ("screen", ("fullscreen", "orientation", "dpi", "portrait", "landscape")),
    ("cài đặt", ("install", "minsdk", "unpack", "package", "dppp")),
    ("font", ("font",)),
]

FAM_LABELS = {f: f for f, _ in FAMILY_RULES}


def patch_families(patch):
    """Họ chức năng của patch — từ tên + nội dung khối lệnh."""
    name = (patch.name or "").lower()
    text = " ".join(s.get("MATCH") + " " + s.get("REPLACE") + " "
                    + s.get("TARGET") + " " + s.get("SOURCE")
                    for s in patch.sections).lower()
    fams = set()
    for fam, keys in FAMILY_RULES:
        if any(k in name for k in keys):
            fams.add(fam)
        elif fam == "token" and any(k in text for k in
                                    ("token", "oauth", "bearer", "sessionid")):
            fams.add(fam)
        elif fam == "api" and any(k in text for k in
                                  ("http://", "https://", "landroid/net/",
                                   "lokhttp3", "lretrofit2")):
            fams.add(fam)
        elif fam == "trace" and any(k in text for k in
                                    ("logcat", "debug", "trace", "dump")):
            fams.add(fam)
        elif fam == "signature" and any(k in text for k in
                                        ("signature", "sigcheck",
                                         "verifysign")):
            fams.add(fam)
        elif fam == "ads" and any(k in text for k in
                                  ("ca-app-pub", "doubleclick", "googleads")):
            fams.add(fam)
        elif fam == "google" and any(k in text for k in
                                     ("play.google", "com.google.android.gms")):
            fams.add(fam)
    return fams


def provides(patch):
    """Class mà patch CUNG CẤP (từ ADD_FILES/asset .smali)."""
    out = set()
    for sec in patch.sections:
        if sec.type == "ADD_FILES":
            target = sec.get("TARGET").strip()
            if target.endswith(".smali"):
                cls = target[:-6].split("smali/", 1)[-1]
                out.add("L" + cls + ";")
    for name, data in patch.assets.items():
        if name.endswith(".smali"):
            try:
                text = data.decode("utf-8", errors="replace")
            except Exception:
                continue
            m = SMALI_CLASS_RE.search(text)
            if m:
                out.add("L" + m.group(1) + ";")
    return out


def uses(patch):
    """Class mà patch DÙNG (MATCH/REPLACE/TARGET), bỏ class framework."""
    out = set()
    for sec in patch.sections:
        for key in ("MATCH", "REPLACE", "TARGET"):
            for m in CLASS_RE.finditer(sec.get(key, "").replace("\n", " ")):
                full = "L" + m.group(1) + ";"
                if not full.startswith(FRAMEWORK_PREFIXES):
                    out.add(full)
    return out


def class_links(patches):
    """Cạnh class-link: A cung cấp class mà B dùng (kèm bằng chứng)."""
    info = {}
    for p in patches:
        info[p.name] = (provides(p), uses(p))
    links = []
    names = [p.name for p in patches]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            pa, ua = info[names[i]]
            pb, ub = info[names[j]]
            inter = (pa & ub) | (pb & ua)
            if inter:
                links.append({
                    "a": names[i], "b": names[j],
                    "classes": sorted(inter),
                })
    return links


def _pack_safe(patches):
    """Gói các patch không xung đột vào cùng nhóm; xung đột tách riêng."""
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


def discover_combos(patches):
    """Phiên bản 2: gộp theo họ + class-link, không gộp chéo họ qua năng lực."""
    # Bước 1: gom patch theo họ
    family_members = {}
    for p in patches:
        for f in patch_families(p):
            family_members.setdefault(f, []).append(p)

    used_pos = set()
    combos = []

    def emit(label, pack, fam, kind):
        merged = merge_patches(pack, label)
        suffix = "" if len(pack) == 1 else ""
        combos.append({
            "label": label,
            "file": label.replace("/", "-") + ".patch",
            "patches": [p.name for p in pack],
            "sections": len(merged.sections),
            "kind": kind,
            "merged": merged,
        })

    # Combo theo họ (chỉ khi >= 2 patch)
    for fam, members in sorted(family_members.items()):
        packs, _ = _pack_safe(members)
        for pi, pack in enumerate(packs):
            if len(pack) < 2:
                continue
            label = fam if len(packs) == 1 else "%s_%d" % (fam, pi + 1)
            emit(label, pack, fam, "họ")
            for p in pack:
                for i, q in enumerate(patches):
                    if q is p:
                        used_pos.add(i)

    # Bước 2: class-link cho các patch CHƯA vào họ (bổ trợ thật)
    free = [p for i, p in enumerate(patches) if i not in used_pos]
    if free:
        # đồ thị class-link
        pos = {}
        for i, p in enumerate(free):
            pos.setdefault(p.name, []).append(i)
        parent = list(range(len(free)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[ry] = rx

        links = class_links(free)
        for e in links:
            for ia in pos.get(e["a"], []):
                for ib in pos.get(e["b"], []):
                    union(ia, ib)
        comps = {}
        for i, p in enumerate(free):
            comps.setdefault(find(i), []).append(p)
        for comp in sorted(comps.values(), key=len, reverse=True):
            if len(comp) < 2:
                continue
            packs, _ = _pack_safe(comp)
            comp_links = [e for e in links
                          if e["a"] in {p.name for p in comp}
                          and e["b"] in {p.name for p in comp}]
            for pi, pack in enumerate(packs):
                if len(pack) < 2:
                    continue
                label = "Bổ-trợ-Class" if len(packs) == 1 else \
                    "Bổ-trợ-Class_%d" % (pi + 1)
                merged = merge_patches(pack, label)
                combos.append({
                    "label": label,
                    "file": label + ".patch",
                    "patches": [p.name for p in pack],
                    "sections": len(merged.sections),
                    "kind": "class-link",
                    "links": comp_links,
                    "merged": merged,
                })
                for p in pack:
                    for i, q in enumerate(patches):
                        if q is p:
                            used_pos.add(i)

    isolated = [p.name for i, p in enumerate(patches) if i not in used_pos]
    return combos, isolated


def render_auto_report(combos, isolated, total):
    """Kết xuất báo cáo combo tự phát hiện."""
    lines = ["# Báo cáo combo tự phát hiện (bổ trợ cho nhau) — v2", "",
             "- Tổng patch đầu vào: %d" % total,
             "- Combo tạo được: %d" % len(combos),
             "- Patch cô lập: %d" % len(isolated), ""]
    for cb in combos:
        lines.append("## %s" % cb["label"])
        lines.append("- Số khối: %d | Loại: %s" % (cb["sections"],
                                                   cb["kind"]))
        lines.append("- Nguồn (%d patch):" % len(cb["patches"]))
        for n in cb["patches"]:
            lines.append("  - %s" % n)
        if cb.get("links"):
            lines.append("- Class-link:")
            for e in cb["links"][:10]:
                lines.append("  - %s <-> %s: %s" % (
                    e["a"], e["b"], ", ".join(e["classes"])))
        lines.append("")
    if isolated:
        lines.append("## Patch cô lập (chưa tìm thấy bổ trợ)")
        lines.append(", ".join(sorted(isolated)))
        lines.append("")
    return "\n".join(lines)
