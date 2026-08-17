# -*- coding: utf-8 -*-
"""Bảng lệnh dễ nhớ — chỉ tham chiếu hàm đã có."""

from patchx_core.cli import (
    cmd_analyze,
    cmd_model,
    cmd_semantic_plan,
    cmd_plan_compile,
    cmd_plan_preflight,
    cmd_preflight,
    cmd_validate,
    cmd_baseline,
    cmd_apply,
    cmd_audit,
    cmd_knowledge,
    cmd_failure,
    cmd_test,
)

LENH = {
    "mat": {
        "analyze": cmd_analyze,
        "model": cmd_model,
    },
    "bo_nao": {
        "semantic-plan": cmd_semantic_plan,
        "plan-compile": cmd_plan_compile,
    },
    "kiem_tra": {
        "preflight": cmd_preflight,
        "plan-preflight": cmd_plan_preflight,
        "validate": cmd_validate,
        "baseline": cmd_baseline,
    },
    "nguoi_tho": {
        "apply": cmd_apply,
        "audit": cmd_audit,
    },
    "bo_nho": {
        "knowledge": cmd_knowledge,
        "failure": cmd_failure,
        "test": cmd_test,
    },
}
