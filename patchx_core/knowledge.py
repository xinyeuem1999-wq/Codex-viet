# -*- coding: utf-8 -*-
"""Kho tri thức PATCHX: kết quả đã xác minh, không phải kho patch.

Mỗi bản ghi liên kết ứng dụng/phiên bản, mục tiêu hành vi, fingerprint cấu
trúc, kế hoạch đã duyệt và outcome. Kho chỉ phục vụ tìm trường hợp tương tự;
nó không là nguồn lệnh áp patch và không vượt các cổng preflight/validate.
"""

import json
import os
import time


SCHEMA = "patchx.knowledge-record/v1"
SCHEMA_V2 = "patchx.knowledge-record/v2"
OUTCOMES = {"SUCCESS", "FAILURE", "PARTIAL"}
GATES = {"preflight", "validate", "build", "runtime"}
GATE_RESULTS = {"PASS", "FAIL", "SKIP"}


def load_store(path):
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def validate_record(record):
    errors = []
    if not isinstance(record, dict) or record.get("schema") != SCHEMA:
        return ["schema phải là %s" % SCHEMA]
    app = record.get("app")
    if not isinstance(app, dict) or not app.get("package"):
        errors.append("app.package là bắt buộc")
    if not str(record.get("goal", "")).strip():
        errors.append("goal là bắt buộc")
    target = record.get("target")
    if not isinstance(target, dict) or not target.get("fingerprint"):
        errors.append("target.fingerprint là bắt buộc")
    if record.get("outcome") not in OUTCOMES:
        errors.append("outcome phải là SUCCESS, FAILURE hoặc PARTIAL")
    if record.get("verified") is not True:
        errors.append("chỉ nhận kết quả verified=true")
    return errors


def validate_record_v2(record):
    """Record V2 lưu evidence/gate, không lưu patch hay Smali thực thi."""
    errors = []
    if not isinstance(record, dict) or record.get("schema") != SCHEMA_V2:
        return ["schema phải là %s" % SCHEMA_V2]
    app = record.get("app", {})
    if not isinstance(app, dict) or not app.get("package"):
        errors.append("app.package là bắt buộc")
    if not str(record.get("goal", "")).strip(): errors.append("goal là bắt buộc")
    target = record.get("target", {})
    identity = target.get("identity", {}) if isinstance(target, dict) else {}
    if not isinstance(identity, dict) or not any(identity.get(k) for k in ("exact", "structural", "semantic")):
        errors.append("target.identity cần ít nhất một identity")
    evidence = record.get("evidence", {})
    if not isinstance(evidence, dict) or not evidence.get("extractor_version"):
        errors.append("evidence.extractor_version là bắt buộc")
    gates = record.get("gates", {})
    if not isinstance(gates, dict) or set(gates) != GATES or any(v not in GATE_RESULTS for v in gates.values()):
        errors.append("gates phải đủ preflight/validate/build/runtime với PASS/FAIL/SKIP")
    outcome = record.get("outcome")
    if outcome not in OUTCOMES: errors.append("outcome không hợp lệ")
    elif isinstance(gates, dict):
        vals = set(gates.values())
        if outcome == "SUCCESS" and vals != {"PASS"}: errors.append("SUCCESS cần mọi gate PASS")
        if outcome == "FAILURE" and "FAIL" not in vals: errors.append("FAILURE cần ít nhất một gate FAIL")
    if record.get("verified") is not True: errors.append("chỉ nhận kết quả verified=true")
    return errors


def record_verified(store_path, record):
    """Ghi một kết quả đã nghiệm thu, tránh lặp bản ghi cùng bằng chứng."""
    is_v2 = record.get("schema") == SCHEMA_V2
    errors = validate_record_v2(record) if is_v2 else validate_record(record)
    if errors:
        raise ValueError("Bản ghi không hợp lệ: " + "; ".join(errors))
    rows = load_store(store_path)
    item = dict(record)
    item.setdefault("recorded_at", time.strftime("%Y-%m-%d %H:%M:%S"))
    marker = (item.get("target", {}).get("identity", {}).get("exact") if is_v2
              else item["target"]["fingerprint"])
    key = (item["schema"], item["app"]["package"], item.get("app", {}).get("version", ""),
           item["goal"], marker, item["outcome"])
    if any((x.get("schema"), x.get("app", {}).get("package"), x.get("app", {}).get("version", ""),
            x.get("goal"), (x.get("target", {}).get("identity", {}).get("exact")
                            if x.get("schema") == SCHEMA_V2 else x.get("target", {}).get("fingerprint")),
            x.get("outcome")) == key for x in rows):
        return False, len(rows)
    rows.append(item)
    os.makedirs(os.path.dirname(os.path.abspath(store_path)), exist_ok=True)
    with open(store_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)
    return True, len(rows)


def query_similar(store_path, model, goal=None, limit=10):
    """Tìm bản ghi cùng fingerprint trong model APK mới, kèm bằng chứng."""
    fingerprints = {m.get("fingerprint"): m for m in model.get("methods", [])}
    out = []
    for record in load_store(store_path):
        if goal and record.get("goal") != goal:
            continue
        fp = record.get("target", {}).get("fingerprint")
        method = fingerprints.get(fp)
        if not method:
            continue
        out.append({"record": record, "matched_method": method["id"],
                    "file": method["file"], "line": method["line"],
                    "confidence": 100.0})
    out.sort(key=lambda x: (x["record"].get("outcome") != "SUCCESS",
                            x["record"].get("recorded_at", "")), reverse=False)
    return out[:limit]


def query_similar_v2(store_path, model, goal=None, limit=10):
    """Xếp hạng tham chiếu V2 theo ba identity; không trả target được chọn."""
    if model.get("schema") != "patchx.app-model/v2":
        return []
    out = []
    for record in load_store(store_path):
        if record.get("schema") != SCHEMA_V2 or (goal and record.get("goal") != goal):
            continue
        wanted = record.get("target", {}).get("identity", {})
        for method in model.get("methods", []):
            actual = method.get("identity", {})
            matches = [k for k in ("exact", "structural", "semantic")
                       if wanted.get(k) and wanted.get(k) == actual.get(k)]
            if not matches: continue
            score = 100.0 if "exact" in matches else 90.0 if set(matches) == {"structural", "semantic"} else 70.0 if "structural" in matches else 55.0
            out.append({"record": record, "matched_method": method["id"],
                        "file": method["file"], "line": method["line"],
                        "confidence": score, "identity_matches": matches,
                        "recommendation_only": True})
    out.sort(key=lambda x: (-x["confidence"], x["record"].get("outcome") != "SUCCESS",
                            x["matched_method"]))
    return out[:limit]


def suggest_plan_v2(store_path, model, goal=None, limit=10):
    """Biến kết quả kho tri thức thành semantic-plan/V2 chỉ-tham chiếu.

    Không chọn target tự động: mỗi ứng viên chỉ trở thành selector với
    ``max_accepted=1`` và ``on_ambiguous=STOP``; người dùng vẫn phải chạy
    ``semantic-plan`` trên APK mới rồi qua preflight/validate/build/runtime.
    """
    if model.get("schema") != "patchx.app-model/v2":
        return None
    hits = query_similar_v2(store_path, model, goal=goal, limit=limit)
    if not hits:
        return None
    best = {}
    for hit in hits:
        mid = hit["matched_method"]
        if mid not in best or hit["confidence"] > best[mid]["confidence"]:
            best[mid] = hit
    methods = {m["id"]: m for m in model.get("methods", [])}
    targets, intents = [], []
    for idx, (mid, hit) in enumerate(sorted(best.items(),
                                            key=lambda kv: -kv[1]["confidence"]), 1):
        method = methods.get(mid)
        if not method:
            continue
        features = method.get("features", {})
        relations = method.get("relations", {})
        selector = {"all": [{"return_type": features.get("return_type", "V")},
                            {"parameters": features.get("parameters", [])}]}
        if features.get("branch_count"):
            selector["all"].append({"min_branch_count": features["branch_count"]})
        calls = features.get("calls", [])
        if calls:
            selector["all"].append({"requires_call": calls[0]})
        distance = relations.get("entry_distance")
        if distance is not None:
            selector["near_entry"] = {"max_distance": distance}
        name = "knowledge_target_%d" % idx
        targets.append({
            "name": name, "selector": selector,
            "policy": {"min_score": 100, "max_accepted": 1,
                       "on_ambiguous": "STOP"},
            "reference": {
                "record_goal": hit["record"].get("goal"),
                "outcome": hit["record"].get("outcome"),
                "confidence": hit["confidence"],
                "identity_matches": hit["identity_matches"],
                "source_identity": hit["record"].get("target", {}).get("identity", {}),
            },
        })
        intents.append({"type": "TRACE", "target": name,
                        "note": "Chỉ tham chiếu kho tri thức; cần semantic-plan + preflight."})
    if not targets:
        return None
    return {"schema": "patchx.semantic-plan/v2",
            "goal": goal or "Kế hoạch tham chiếu từ kho tri thức",
            "targets": targets, "operation_intent": intents,
            "verification": ["preflight", "validate", "build", "runtime"],
            "provenance": {"source": "patchx.knowledge-record/v2",
                           "recommendation_only": True}}
