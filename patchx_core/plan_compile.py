# -*- coding: utf-8 -*-
"""Biên dịch semantic-plan/V2 thành transaction *nháp*, không thực thi."""

import hashlib
import os

from .semantic_plan import SCHEMA_V2, evaluate_plan_v2, validate_plan_v2


def tree_evidence_hash(tree):
    """Hash nội dung có thứ tự của manifest + Smali, dùng khóa evidence."""
    digest = hashlib.sha256()
    paths = []
    for root, dirs, files in os.walk(tree):
        dirs[:] = sorted(d for d in dirs if d not in {"build", "original", ".patchx"})
        for name in sorted(files):
            if name.endswith(".smali") or name == "AndroidManifest.xml":
                paths.append(os.path.join(root, name))
    for path in sorted(paths):
        rel = os.path.relpath(path, tree).replace(os.sep, "/")
        digest.update(rel.encode("utf-8") + b"\0")
        try:
            with open(path, "rb") as fh:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    digest.update(chunk)
        except OSError:
            digest.update(b"<unreadable>")
    return "sha256:" + digest.hexdigest()


def compile_plan_v2(plan, model, tree):
    """Tạo draft bất biến; không chứa Smali, patch hay lệnh thực thi.

    Chỉ compile khi selector trả đúng một ứng viên cho từng target. Hash cây
    là điều kiện bắt buộc ở preflight của bước thực thi tương lai.
    """
    if validate_plan_v2(plan):
        raise ValueError("semantic-plan/V2 không hợp lệ")
    if model.get("schema") != "patchx.app-model/v2":
        raise ValueError("plan-compile cần patchx.app-model/v2")
    verdict = evaluate_plan_v2(plan, model)
    if verdict["verdict"] != "READY_FOR_PREFLIGHT":
        raise ValueError("plan-compile bị chặn: " + verdict["verdict"])
    selected = []
    for target in verdict["targets"]:
        accepted = target["accepted"]
        if len(accepted) != 1:
            raise ValueError("plan-compile cần đúng một ứng viên: " + target["name"])
        item = accepted[0]
        selected.append({"target": target["name"], "method": item["method"],
                         "file": item["file"], "line": item["line"],
                         "identity": item.get("identity", {}),
                         "evidence": item["evidence"]})
    return {"schema": "patchx.transaction-draft/v1", "goal": plan["goal"],
            "status": "DRAFT_REQUIRES_APPROVAL",
            "tree": os.path.abspath(tree),
            "tree_evidence_hash": tree_evidence_hash(tree),
            "plan_schema": SCHEMA_V2,
            "plan": plan,
            "selected_targets": selected,
            "operation_intent": plan["operation_intent"],
            "required_gates": ["approval", "preflight", "validate", "build", "runtime"],
            "executable": False}


def verify_draft_evidence(draft, tree):
    """Gate chỉ-đọc: chặn draft nếu hash cây khác lúc compile."""
    if draft.get("schema") != "patchx.transaction-draft/v1":
        return {"status": "BLOCKED", "reason": "schema draft không hợp lệ"}
    if draft.get("status") != "DRAFT_REQUIRES_APPROVAL" or draft.get("executable"):
        return {"status": "BLOCKED", "reason": "draft không an toàn"}
    actual = tree_evidence_hash(tree)
    expected = draft.get("tree_evidence_hash", "")
    return {"status": "READY_FOR_APPROVAL" if actual == expected else "BLOCKED",
            "expected_hash": expected, "actual_hash": actual,
            "reason": "evidence khớp" if actual == expected else "cây APK đã thay đổi"}


def revalidate_draft(draft, tree):
    """Khi hash cây thay đổi, đánh giá lại plan V2 trên cây mới.

    Không tự áp: chỉ sinh draft mới khi verdict vẫn ``READY_FOR_PREFLIGHT``;
    nếu mơ hồ/không đủ bằng chứng thì trả BLOCKED và yêu cầu người dùng siết
    selector.
    """
    report = verify_draft_evidence(draft, tree)
    if report["status"] != "BLOCKED" or report.get("reason") != "cây APK đã thay đổi":
        return {"status": report["status"], "reason": report["reason"],
                "recompiled": False}
    plan = draft.get("plan")
    if not isinstance(plan, dict) or plan.get("schema") != SCHEMA_V2:
        return {"status": "BLOCKED", "reason":
                "draft không mang semantic-plan/V2 để đánh giá lại",
                "recompiled": False}
    from .smali_sem import build_app_model_v2
    model = build_app_model_v2(tree)
    verdict = evaluate_plan_v2(plan, model)
    if verdict["verdict"] != "READY_FOR_PREFLIGHT":
        return {"status": "BLOCKED",
                "reason": "đánh giá lại plan trên cây mới: " + verdict["verdict"],
                "verdict": verdict["verdict"], "recompiled": False}
    new_draft = compile_plan_v2(plan, model, tree)
    return {"status": "READY_FOR_APPROVAL",
            "reason": "đã đánh giá lại plan và khóa evidence mới",
            "recompiled": True, "draft": new_draft}
