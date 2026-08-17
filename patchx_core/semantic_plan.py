# -*- coding: utf-8 -*-
"""Kế hoạch thay đổi theo mục tiêu + điều kiện (Đợt B).

Định dạng này là lớp kế hoạch an toàn nằm trước patch.txt/Engine: nó chỉ tìm,
chấm điểm và xác minh ứng viên. Không hàm nào trong mô-đun này ghi vào cây APK
hay gọi Engine.apply; mọi thay đổi vẫn cần người dùng duyệt và qua preflight.
"""

import json


SCHEMA = "patchx.semantic-plan/v1"
SCHEMA_V2 = "patchx.semantic-plan/v2"
ALLOWED_OPERATIONS = {"RETURN_CONSTANT", "INSERT_HOOK", "REPLACE_FROM_REFERENCE",
                      "SET_FIELD", "TRACE"}
REQUIRED_VERIFY = {"preflight", "validate", "build", "runtime"}


def load_plan(path):
    """Nạp và kiểm tra cấu trúc cơ bản của kế hoạch JSON."""
    with open(path, encoding="utf-8") as fh:
        plan = json.load(fh)
    errors = validate_plan_v2(plan) if plan.get("schema") == SCHEMA_V2 else validate_plan(plan)
    if errors:
        raise ValueError("Kế hoạch không hợp lệ: " + "; ".join(errors))
    return plan


def validate_plan(plan):
    """Trả danh sách lỗi; cố tình chặt để plan không thành patch ẩn."""
    errors = []
    if not isinstance(plan, dict) or plan.get("schema") != SCHEMA:
        return ["schema phải là %s" % SCHEMA]
    if not str(plan.get("goal", "")).strip():
        errors.append("thiếu goal")
    targets = plan.get("targets")
    if not isinstance(targets, list) or not targets:
        errors.append("cần ít nhất một target")
    for i, target in enumerate(targets or []):
        if not isinstance(target, dict) or not isinstance(target.get("conditions"), dict):
            errors.append("target %d thiếu conditions" % (i + 1))
    for op in plan.get("operations", []):
        if not isinstance(op, dict) or op.get("type") not in ALLOWED_OPERATIONS:
            errors.append("operation không được hỗ trợ: %r" % op)
    verify = set(plan.get("verification", []))
    unknown = verify - REQUIRED_VERIFY
    if unknown:
        errors.append("verification không hợp lệ: %s" % ", ".join(sorted(unknown)))
    return errors


def _validate_intent(intent):
    """Không cho operation_intent trở thành patch Smali ẩn trong plan V2."""
    if not isinstance(intent, dict) or intent.get("type") not in ALLOWED_OPERATIONS:
        return "operation_intent không được hỗ trợ: %r" % intent
    forbidden = {"body", "smali", "content", "match", "replace", "target_file"}
    present = forbidden & set(intent)
    if present:
        return "operation_intent chứa nội dung thực thi bị cấm: %s" % ", ".join(sorted(present))
    if not isinstance(intent.get("target", ""), str) or not intent.get("target", "").strip():
        return "operation_intent cần target là tên target logic"
    return ""


def validate_plan_v2(plan):
    """Kiểm tra chặt schema V2; V2 chỉ mô tả ý định và chính sách chọn target."""
    errors = []
    if not isinstance(plan, dict) or plan.get("schema") != SCHEMA_V2:
        return ["schema phải là %s" % SCHEMA_V2]
    if not str(plan.get("goal", "")).strip():
        errors.append("thiếu goal")
    targets = plan.get("targets")
    if not isinstance(targets, list) or not targets:
        errors.append("cần ít nhất một target")
    names = set()
    for i, target in enumerate(targets or []):
        where = "target %d" % (i + 1)
        if not isinstance(target, dict):
            errors.append(where + " phải là object")
            continue
        name = target.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(where + " thiếu name")
        elif name in names:
            errors.append(where + " trùng name: " + name)
        else:
            names.add(name)
        selector = target.get("selector")
        if not isinstance(selector, dict) or not isinstance(selector.get("all"), list) or not selector["all"]:
            errors.append(where + " cần selector.all không rỗng")
        else:
            for atom in selector["all"]:
                if not isinstance(atom, dict) or len(atom) != 1:
                    errors.append(where + " selector.all chỉ nhận object một điều kiện")
                    continue
                key, value = next(iter(atom.items()))
                if key not in {"return_type", "parameters", "min_branch_count",
                               "requires_call", "requires_caller",
                               "requires_string", "requires_field_read",
                               "requires_field_write"}:
                    errors.append(where + " điều kiện không hỗ trợ: " + str(key))
                elif key == "parameters" and not isinstance(value, list):
                    errors.append(where + " parameters phải là list")
                elif key == "min_branch_count" and (not isinstance(value, int) or value < 0):
                    errors.append(where + " min_branch_count phải là số nguyên không âm")
                elif key.startswith("requires_") and not isinstance(value, str):
                    errors.append(where + " " + key + " phải là chuỗi")
        near = (selector or {}).get("near_entry") if isinstance(selector, dict) else None
        if near is not None and (not isinstance(near, dict)
                                 or not isinstance(near.get("max_distance"), int)
                                 or near["max_distance"] < 0):
            errors.append(where + " near_entry.max_distance phải là số nguyên không âm")
        policy = target.get("policy")
        if not isinstance(policy, dict):
            errors.append(where + " thiếu policy")
        else:
            score = policy.get("min_score")
            maximum = policy.get("max_accepted")
            if not isinstance(score, (int, float)) or not 0 <= score <= 100:
                errors.append(where + " policy.min_score phải trong 0..100")
            if not isinstance(maximum, int) or maximum < 1:
                errors.append(where + " policy.max_accepted phải >= 1")
            if policy.get("on_ambiguous") != "STOP":
                errors.append(where + " policy.on_ambiguous phải là STOP")
    intents = plan.get("operation_intent")
    if not isinstance(intents, list) or not intents:
        errors.append("cần ít nhất một operation_intent")
    else:
        for intent in intents:
            err = _validate_intent(intent)
            if err:
                errors.append(err)
            elif intent["target"] not in names:
                errors.append("operation_intent target không tồn tại: " + intent["target"])
    verify = set(plan.get("verification", []))
    if verify != REQUIRED_VERIFY:
        errors.append("verification V2 phải đủ: " + ", ".join(sorted(REQUIRED_VERIFY)))
    return errors


def _matches(method, conditions):
    """So khớp bảo thủ một method với điều kiện cấu trúc/ngữ nghĩa."""
    evidence, missing = [], []
    checks = (
        ("return_type", method.get("return_type")),
        ("fingerprint", method.get("fingerprint")),
    )
    for key, actual in checks:
        wanted = conditions.get(key)
        if wanted is None:
            continue
        if actual == wanted:
            evidence.append(key)
        else:
            missing.append(key)
    if "parameters" in conditions:
        if method.get("parameters") == conditions["parameters"]:
            evidence.append("parameters")
        else:
            missing.append("parameters")
    if "min_branch_count" in conditions:
        if method.get("branch_count", 0) >= int(conditions["min_branch_count"]):
            evidence.append("min_branch_count")
        else:
            missing.append("min_branch_count")
    for key, values in (("requires_calls", method.get("calls", [])),
                        ("requires_field_reads", method.get("field_reads", [])),
                        ("requires_strings", method.get("strings", []))):
        required = conditions.get(key, [])
        for item in required:
            if item in values:
                evidence.append(key + ":" + item)
            else:
                missing.append(key + ":" + item)
    total = len(evidence) + len(missing)
    score = round((len(evidence) / total * 100) if total else 0.0, 1)
    return score, evidence, missing


def evaluate_plan(plan, model):
    """Tìm ứng viên theo plan trong app-model và trả bằng chứng đầy đủ."""
    errors = validate_plan(plan)
    if errors:
        raise ValueError("Kế hoạch không hợp lệ: " + "; ".join(errors))
    results = []
    for target in plan["targets"]:
        candidates = []
        for method in model.get("methods", []):
            score, evidence, missing = _matches(method, target["conditions"])
            if evidence:
                candidates.append({"method": method["id"], "file": method["file"],
                                   "line": method["line"], "score": score,
                                   "evidence": evidence, "missing": missing,
                                   "fingerprint": method["fingerprint"]})
        candidates.sort(key=lambda x: (-x["score"], x["method"]))
        min_score = float(target.get("min_score", 70))
        accepted = [x for x in candidates if x["score"] >= min_score]
        rejected = [x for x in candidates if x["score"] < min_score]
        results.append({"name": target.get("name", "target"), "min_score": min_score,
                        "candidates": candidates, "accepted": accepted,
                        "rejected": rejected})
    ok = all(item["accepted"] for item in results)
    return {"schema": SCHEMA, "goal": plan["goal"], "verdict":
            "READY_FOR_PREFLIGHT" if ok else "NO_CONFIDENT_TARGET",
            "targets": results, "operations": plan.get("operations", []),
            "verification": plan.get("verification", [])}


def _matches_v2(method, selector):
    """Chấm từng atom selector trên model V2 và luôn trả evidence âm/dương."""
    features = method.get("features", {})
    relations = method.get("relations", {})
    evidence, missing = [], []
    for atom in selector.get("all", []):
        key, wanted = next(iter(atom.items()))
        actual = {
            "return_type": features.get("return_type"),
            "parameters": features.get("parameters"),
            "min_branch_count": features.get("branch_count", 0),
            "requires_call": features.get("calls", []),
            "requires_caller": relations.get("callers", []),
            "requires_string": features.get("strings", []),
            "requires_field_read": features.get("field_reads", []),
            "requires_field_write": features.get("field_writes", []),
        }[key]
        ok = actual >= wanted if key == "min_branch_count" else wanted in actual if key.startswith("requires_") else actual == wanted
        (evidence if ok else missing).append(key + (":" + str(wanted) if key.startswith("requires_") else ""))
    near = selector.get("near_entry")
    if near is not None:
        distance = relations.get("entry_distance")
        ok = distance is not None and distance <= near["max_distance"]
        (evidence if ok else missing).append("near_entry<=%d" % near["max_distance"])
    total = len(evidence) + len(missing)
    return round(100 * len(evidence) / total, 1) if total else 0.0, evidence, missing


def evaluate_plan_v2(plan, model):
    """Đánh giá plan V2, chặn ambiguity và không gọi code thực thi."""
    errors = validate_plan_v2(plan)
    if errors:
        raise ValueError("Kế hoạch không hợp lệ: " + "; ".join(errors))
    if model.get("schema") != "patchx.app-model/v2":
        return {"schema": SCHEMA_V2, "goal": plan["goal"],
                "verdict": "INSUFFICIENT_EVIDENCE", "reason":
                "semantic-plan/v2 cần patchx.app-model/v2", "targets": [],
                "operation_intent": plan["operation_intent"],
                "verification": plan["verification"]}
    results, any_ambiguous = [], False
    for target in plan["targets"]:
        candidates = []
        for method in model.get("methods", []):
            score, evidence, missing = _matches_v2(method, target["selector"])
            candidates.append({"method": method["id"], "file": method["file"],
                               "line": method["line"], "score": score,
                               "evidence": evidence, "missing": missing,
                               "identity": method.get("identity", {}),
                               "entry_distance": method.get("relations", {}).get("entry_distance")})
        candidates.sort(key=lambda x: (-x["score"], x["method"]))
        policy = target["policy"]
        accepted = [x for x in candidates if x["score"] >= policy["min_score"]]
        rejected = [x for x in candidates if x["score"] < policy["min_score"]]
        ambiguous = len(accepted) > policy["max_accepted"]
        any_ambiguous = any_ambiguous or ambiguous
        results.append({"name": target["name"], "policy": policy,
                        "candidates": candidates, "accepted": accepted,
                        "rejected": rejected,
                        "ambiguous": ambiguous})
    if any_ambiguous:
        verdict = "AMBIGUOUS_TARGET"
    elif all(item["accepted"] for item in results):
        verdict = "READY_FOR_PREFLIGHT"
    else:
        verdict = "NO_CONFIDENT_TARGET"
    return {"schema": SCHEMA_V2, "goal": plan["goal"], "verdict": verdict,
            "targets": results, "operation_intent": plan["operation_intent"],
            "verification": plan["verification"]}


def suggest_selector_fix(plan, result):
    """Gợi ý siết/nới selector từ kết quả đánh giá (vòng học từ thất bại).

    Không tự sửa plan. Trả danh sách gợi ý để người dùng chọn; mọi thay đổi
    vẫn phải chạy lại ``semantic-plan`` và qua preflight.
    """
    tips = []
    for idx, target in enumerate(plan.get("targets", [])):
        item = result.get("targets", [])[idx] if idx < len(result.get("targets", [])) else {}
        if item.get("ambiguous"):
            tips.append({"target": target.get("name"), "kind": "ambiguous",
                         "advice": [
                             "Tăng policy.min_score hoặc giảm policy.max_accepted.",
                             "Thêm requires_caller/requires_call/requires_string "
                             "để tách ứng viên trùng điểm.",
                             "Siết near_entry.max_distance về đúng khoảng cách mục tiêu."]})
        elif item.get("accepted"):
            continue
        else:
            missing = {}
            rejected = item.get("rejected", [])
            for cand in rejected:
                for atom in cand.get("missing", []):
                    missing[atom] = missing.get(atom, 0) + 1
            common = [atom for atom, count in sorted(missing.items())
                      if rejected and count == len(rejected)]
            tips.append({"target": target.get("name"), "kind": "no_confident",
                         "common_missing": common,
                         "advice": [
                             "Kiểm tra selector.all: các atom chung bị thiếu có thể quá chặt.",
                             "Dùng version-map/knowledge suggest-plan để tìm ứng viên tương đồng.",
                             "Nới từng atom một và chạy lại; không gộp nhiều thay đổi cùng lúc."]})
    return tips


def plan_from_model_diff(original_model, modified_model, goal="Thay đổi rút ra từ APK mẫu"):
    """Rút kế hoạch tham chiếu từ hai app-model, không sinh patch thực thi.

    Method có cùng định danh nhưng fingerprint đổi được ghi thành target với
    fingerprint của bản gốc; operation chỉ là REPLACE_FROM_REFERENCE để người
    dùng duyệt/chuyển đổi thành patch tương thích ở bước sau.
    """
    before = {m["id"]: m for m in original_model.get("methods", [])}
    after = {m["id"]: m for m in modified_model.get("methods", [])}
    targets = []
    for mid in sorted(set(before) & set(after)):
        a, b = before[mid], after[mid]
        if a["fingerprint"] == b["fingerprint"]:
            continue
        conditions = {"return_type": a["return_type"],
                      "parameters": a["parameters"],
                      "fingerprint": a["fingerprint"]}
        targets.append({"name": "target_%d" % (len(targets) + 1),
                        "conditions": conditions, "min_score": 100,
                        "reference": {"original": mid, "modified": mid,
                                      "modified_fingerprint": b["fingerprint"]}})
    return {"schema": SCHEMA, "goal": goal, "targets": targets,
            "operations": ([{"type": "REPLACE_FROM_REFERENCE",
                             "note": "Chỉ tham chiếu APK mẫu; cần người dùng duyệt"}]
                           if targets else []),
            "verification": ["preflight", "validate", "build", "runtime"]}


def plan_v2_from_version_map(version_map, original_model, modified_model,
                             goal="Kế hoạch tham chiếu từ bản đồ phiên bản"):
    """Sinh semantic-plan/V2 chỉ-đọc từ các ghép method *duy nhất*.

    Hàm này không suy diễn thao tác thay đổi và không gọi engine. Mỗi target
    chỉ mang selector lấy từ model gốc cùng evidence của ghép version-map;
    khi đánh giá trên APK khác, policy ``max_accepted=1`` vẫn bắt buộc dừng
    nếu selector trở nên mơ hồ.
    """
    if version_map.get("schema") != "patchx.version-match/v1":
        raise ValueError("cần patchx.version-match/v1")
    if original_model.get("schema") != "patchx.app-model/v2" or \
            modified_model.get("schema") != "patchx.app-model/v2":
        raise ValueError("cần hai patchx.app-model/v2")
    before = {m["id"]: m for m in original_model.get("methods", [])}
    after = {m["id"]: m for m in modified_model.get("methods", [])}
    targets, intents = [], []
    for row in version_map.get("matches", []):
        if row.get("status") not in {"exact", "structural", "semantic"}:
            continue
        source, destination = before.get(row.get("before")), after.get(row.get("after"))
        if not source or not destination:
            continue
        f = source.get("features", {})
        selector = {"all": [
            {"return_type": f.get("return_type", "V")},
            {"parameters": f.get("parameters", [])},
            {"min_branch_count": f.get("branch_count", 0)},
        ]}
        calls = f.get("calls", [])
        if calls:
            selector["all"].append({"requires_call": calls[0]})
        distance = source.get("relations", {}).get("entry_distance")
        if distance is not None:
            selector["near_entry"] = {"max_distance": distance}
        name = "version_target_%d" % (len(targets) + 1)
        targets.append({
            "name": name, "selector": selector,
            "policy": {"min_score": 100, "max_accepted": 1,
                       "on_ambiguous": "STOP"},
            "reference": {
                "source_method": source["id"], "target_method": destination["id"],
                "match_level": row["status"],
                "identity_matches": row.get("identity_matches", []),
                "source_identity": source.get("identity", {}),
                "target_identity": destination.get("identity", {}),
                "source_evidence": source.get("evidence", {}),
                "target_evidence": destination.get("evidence", {}),
            },
        })
        intents.append({"type": "TRACE", "target": name,
                        "note": "Chỉ tham chiếu version-map; cần người dùng duyệt."})
    return {"schema": SCHEMA_V2, "goal": goal, "targets": targets,
            "operation_intent": intents,
            "verification": ["preflight", "validate", "build", "runtime"],
            "provenance": {"source": "patchx.version-match/v1",
                           "recommendation_only": True}}
