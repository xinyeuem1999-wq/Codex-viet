# -*- coding: utf-8 -*-
"""P12 — Fuzz / Chaos: sinh dữ liệu ngẫu nhiên tấn công parser + engine.

5 invariant (vi phạm bất kỳ đều tính là lỗi):
  1. PARSER_SAFE   — parse_text/parse_patch_file không bao giờ exception;
  2. ENGINE_SAFE   — engine.apply không exception (trừ RuntimeError vòng GOTO);
  3. STATE_VALID   — .patchx/state.json (nếu có) luôn là JSON hợp lệ;
  4. TREE_CONTAINED— không tạo tệp mới ngoài cây APK;
  5. VALIDATE_SAFE — validate_tree_v2 không bao giờ exception trên cây sau fuzz.
"""

import json
import os
import random
import shutil
import tempfile

from .engine import Engine
from .model import Patch, Section
from .parser import parse_text
from .smali_validate import validate_tree_v2

INVARIANTS = ("PARSER_SAFE", "ENGINE_SAFE", "STATE_VALID",
              "TREE_CONTAINED", "VALIDATE_SAFE")

_SMALI_BOILER = (
    ".class public Lfuzz/F%d;\n"
    ".super Ljava/lang/Object;\n\n"
    ".field public static x:I\n\n"
    ".method public static m%d()V\n"
    "    .registers 2\n\n"
    "    const-string v0, \"fuzz%d\"\n\n"
    "    sget v1, Lfuzz/F%d;->x:I\n\n"
    "    return-void\n"
    ".end method\n"
)

_BLOCK_TEMPLATES = [
    # MATCH_REPLACE literal
    "[MATCH_REPLACE]\nTARGET:\n%(target)s\nMATCH:\n%(match)s\n"
    "REGEX:\nfalse\nREPLACE:\n%(replace)s\n[/MATCH_REPLACE]\n",
    # MATCH_REPLACE regex (có thể lỗi regex)
    "[MATCH_REPLACE]\nTARGET:\n%(target)s\nMATCH:\n%(regex)s\n"
    "REGEX:\ntrue\nREPLACE:\n%(replace)s\n[/MATCH_REPLACE]\n",
    # SET_BOOL (VALUE có thể không hợp lệ)
    "[SET_BOOL]\nTARGET:\n%(target)s\nMATCH:\nconst/4 v0, 0x0\n"
    "VALUE:\n%(value)s\n[/SET_BOOL]\n",
    # TRACE
    "[TRACE]\nTARGET:\n%(target)s\nMATCH:\nreturn-void\n"
    "TAG:\nfuzz\n[/TRACE]\n",
    # ADD_FILES
    "[ADD_FILES]\nSOURCE:\nasset.txt\nTARGET:\n%(target)s\n[/ADD_FILES]\n",
    # REMOVE_FILES
    "[REMOVE_FILES]\nTARGET:\n%(target)s\n[/REMOVE_FILES]\n",
    # DUMMY
    "[DUMMY]\nNAME:\nl%(label)d\n[/DUMMY]\n",
    # MIN_ENGINE_VER ngẫu nhiên
    "[MIN_ENGINE_VER]\n%(ver)s\n[/MIN_ENGINE_VER]\n",
    # GOTO (có thể gây RuntimeError — xử lý riêng)
    "[GOTO]\nGOTO:\n%(label)s\n[/GOTO]\n",
    # MERGE
    "[MERGE]\nSOURCE:\nmerge.zip\nTARGET:\nsmali\n[/MERGE]\n",
]

_TARGETS = [
    "smali/com/demo/MainActivity.smali",
    "smali/com/demo/Util.smali",
    "AndroidManifest.xml",
    "smali*/*.smali",
    "smali/fuzz/F1.smali",
    "",
    "/etc/passwd",
    "../ngoai-cay.smali",
]


def _rand_text(rng, n=12, pool="abcXYZ0123 (){}[]/\\."):
    return "".join(rng.choice(pool) for _ in range(rng.randint(1, n)))


def _rand_patch_text(rng):
    """Sinh patch text ngẫu nhiên gồm 1–6 khối."""
    blocks = []
    for _ in range(rng.randint(1, 6)):
        t = rng.choice(_BLOCK_TEMPLATES)
        if "label" in t:
            blocks.append(t % {"label": rng.randint(0, 3)})
        elif "ver" in t:
            blocks.append(t % {"ver": rng.choice(["1", "2", "99", "abc"])})
        elif "value" in t:
            blocks.append(t % {"target": rng.choice(_TARGETS),
                               "value": rng.choice(
                                   ["true", "false", "0x1", "0x0", "xyz"])})
        else:
            blocks.append(t % {
                "target": rng.choice(_TARGETS),
                "match": _rand_text(rng, 8, "abcdef0123()[]{}\\\\."),
                "regex": rng.choice([r"[", r"(", r"[a-z]+", r"(a|b)+",
                                     r"\d+", r"[0-9]{1,3}"]),
                "replace": _rand_text(rng, 8),
            })
    return "\n".join(blocks)


def _make_tree(root, rng):
    """Cây APK giả nhỏ + manifest chuẩn."""
    smali = os.path.join(root, "smali", "com", "demo")
    os.makedirs(smali, exist_ok=True)
    with open(os.path.join(root, "AndroidManifest.xml"), "w",
              encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="utf-8"?>\n'
                 '<manifest xmlns:android="http://schemas.android.com/apk/'
                 'res/android" package="com.demo">\n'
                 '  <application></application>\n</manifest>\n')
    for i in range(rng.randint(1, 3)):
        with open(os.path.join(smali, "F%d.smali" % i), "w",
                  encoding="utf-8") as fh:
            fh.write(_SMALI_BOILER % (i, i, i, i))


def run_fuzz(iterations=100, seed=1, workdir=None):
    """Chạy fuzz — trả dict kết quả + danh sách vi phạm."""
    rng = random.Random(seed)
    tmp = workdir or tempfile.mkdtemp(prefix="patchx_fuzz_")
    try:
        crashes = []
        violations = []
        for it in range(iterations):
            try:
                text = _rand_patch_text(rng)
                # Invariant 1: parser
                try:
                    patch = parse_text(text)
                except Exception as e:
                    crashes.append((it, "PARSER_SAFE", "%r" % e))
                    continue
                # Invariant 4: theo dõi cây trước khi apply
                tree = os.path.join(tmp, "tree_%d" % it)
                _make_tree(tree, rng)
                before = {n for n in os.listdir(tree) if n != ".patchx"}
                eng = Engine(tree, quiet=True, strict=rng.random() < 0.3)
                try:
                    eng.apply(patch)
                except RuntimeError:
                    pass  # vòng GOTO có chủ đích — không tính là lỗi
                except Exception as e:
                    crashes.append((it, "ENGINE_SAFE", "%r" % e))
                # Invariant 3: state hợp lệ
                sf = os.path.join(tree, ".patchx", "state.json")
                if os.path.isfile(sf):
                    try:
                        json.load(open(sf, encoding="utf-8"))
                    except Exception as e:
                        violations.append((it, "STATE_VALID", "%r" % e))
                # Invariant 4: không tệp mới ngoài cây
                after = {n for n in os.listdir(tree) if n != ".patchx"}
                if after != before:
                    violations.append((it, "TREE_CONTAINED",
                                       "thư mục gốc đổi: %s" % after))
                # Invariant 5: validate không crash
                try:
                    validate_tree_v2(tree, level="FAST")
                except Exception as e:
                    violations.append((it, "VALIDATE_SAFE", "%r" % e))
                shutil.rmtree(tree, ignore_errors=True)
            except Exception as e:
                crashes.append((it, "OUTER", "%r" % e))
        return {
            "iterations": iterations,
            "seed": seed,
            "crashes": crashes,
            "violations": violations,
            "ok": not crashes and not violations,
        }
    finally:
        if workdir is None:
            shutil.rmtree(tmp, ignore_errors=True)
