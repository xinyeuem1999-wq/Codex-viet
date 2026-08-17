# -*- coding: utf-8 -*-
"""P14 — Runtime M3 scenario engine.

Chạy kịch bản hành vi (scenario.json) trên thiết bị/emulator:

    launch / wait / tap / swipe / input / keyevent / navigate /
    assert_pid / assert_logcat / assert_no_crash / assert_no_anr /
    screenshot

Mỗi bước ghi evidence; kết quả M3 = PASS / FAIL / SKIP theo các assert.

Scenario.json mẫu:
{
  "name": "m3-kiss",
  "steps": [
    {"type": "launch"},
    {"type": "wait", "seconds": 3},
    {"type": "assert_pid"},
    {"type": "assert_logcat",
     "expect": ["Displayed fr.neamar.kiss"],
     "forbid": ["FATAL EXCEPTION"]},
    {"type": "screenshot", "name": "home"}
  ]
}
"""

import json
import os
import re
import subprocess
import time

_NAV_KEYS = {
    "back": "KEYCODE_BACK",
    "home": "KEYCODE_HOME",
    "recent": "KEYCODE_APP_SWITCH",
    "menu": "KEYCODE_MENU",
    "enter": "KEYCODE_ENTER",
}

_STEP_TYPES = (
    "launch", "stop", "wait", "tap", "swipe", "input", "keyevent",
    "navigate", "assert_pid", "assert_logcat", "assert_no_crash",
    "assert_no_anr", "screenshot",
)


def load_scenario(path):
    """Đọc + kiểm tra scenario.json — trả dict hoặc raise ValueError."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    validate_scenario(data)
    return data


def validate_scenario(scn):
    """Kiểm tra cấu trúc scenario; raise ValueError nếu sai."""
    if not isinstance(scn, dict):
        raise ValueError("scenario phải là object JSON")
    steps = scn.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("scenario cần ít nhất 1 bước (steps)")
    for i, st in enumerate(steps):
        if not isinstance(st, dict):
            raise ValueError("bước %d không phải object" % i)
        t = st.get("type")
        if t not in _STEP_TYPES:
            raise ValueError("bước %d: type không hợp lệ '%s' (cho phép: %s)"
                             % (i, t, ", ".join(_STEP_TYPES)))
        if t == "wait":
            sec = st.get("seconds", 1)
            if not isinstance(sec, (int, float)) or sec < 0:
                raise ValueError("bước %d: seconds phải >= 0" % i)
        if t in ("tap", "swipe"):
            for k in ("x", "y"):
                v = st.get(k)
                if not isinstance(v, (int, float)):
                    raise ValueError("bước %d: cần tọa độ %s (số)" % (i, k))
        if t == "swipe":
            for k in ("x2", "y2"):
                v = st.get(k)
                if not isinstance(v, (int, float)):
                    raise ValueError("bước %d: cần tọa độ %s (số)" % (i, k))
        if t == "input":
            if not isinstance(st.get("text"), str):
                raise ValueError("bước %d: input cần text (chuỗi)" % i)
        if t == "navigate":
            key = st.get("key")
            if key not in _NAV_KEYS:
                raise ValueError("bước %d: navigate cần key ∈ %s"
                                 % (i, ", ".join(sorted(_NAV_KEYS))))
        if t == "assert_logcat":
            if not isinstance(st.get("expect", []), list) \
               or not isinstance(st.get("forbid", []), list):
                raise ValueError("bước %d: assert_logcat cần expect/forbid "
                                 "là danh sách" % i)
    return scn


def _adb(device, args, timeout=30):
    """Chạy adb -s DEVICE <args> — trả (returncode, stdout+stderr)."""
    cmd = ["adb", "-s", device] + args
    try:
        proc = subprocess.run(cmd, text=True, errors="replace",
                              capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, "adb lỗi: %r" % e
    return proc.returncode, ((proc.stdout or "") + (proc.stderr or "")).strip()


def _esc_input(text):
    """Input text qua adb: khoảng trắng → %s, bỏ ký tự đặc biệt nguy hiểm."""
    return text.replace(" ", "%s").replace("\\", "").replace("'", "")


def run_scenario(device, pkg, act, scn, timeout=30, out_dir=None,
                 adb_timeout=20):
    """Chạy kịch bản M3 — trả dict kết quả + evidence từng bước."""
    shots = None
    if out_dir:
        shots = os.path.join(out_dir, "m3_shots")
        os.makedirs(shots, exist_ok=True)
    steps = scn.get("steps", [])
    result = {"steps": [], "passed": False, "status": "M3_SKIP",
              "reasons": []}
    has_assert = False
    failed = False
    _adb(device, ["logcat", "-c"], timeout=adb_timeout)
    for i, st in enumerate(steps):
        t = st["type"]
        entry = {"step": i, "type": t, "ok": True, "detail": ""}
        try:
            if t == "launch":
                if act:
                    rc, out = _adb(device, ["shell", "am", "start", "-n",
                                            "%s/%s" % (pkg, act)],
                                   timeout=adb_timeout)
                else:
                    rc, out = _adb(device, ["shell", "monkey", "-p", pkg,
                                            "-c",
                                            "android.intent.category.LAUNCHER",
                                            "1"], timeout=adb_timeout)
                entry["ok"] = rc == 0
                entry["detail"] = out[:200]
            elif t == "stop":
                rc, out = _adb(device, ["shell", "am", "force-stop", pkg],
                               timeout=adb_timeout)
                entry["ok"] = rc == 0
                entry["detail"] = out[:200]
            elif t == "wait":
                time.sleep(st.get("seconds", 1))
            elif t == "tap":
                rc, out = _adb(device, ["shell", "input", "tap",
                                        str(int(st["x"])), str(int(st["y"]))],
                               timeout=adb_timeout)
                entry["ok"] = rc == 0
                entry["detail"] = out[:200]
            elif t == "swipe":
                dur = st.get("duration_ms", 300)
                rc, out = _adb(device, ["shell", "input", "swipe",
                                        str(int(st["x"])), str(int(st["y"])),
                                        str(int(st["x2"])), str(int(st["y2"])),
                                        str(int(dur))], timeout=adb_timeout)
                entry["ok"] = rc == 0
                entry["detail"] = out[:200]
            elif t == "input":
                rc, out = _adb(device, ["shell", "input", "text",
                                        _esc_input(st["text"])],
                               timeout=adb_timeout)
                entry["ok"] = rc == 0
                entry["detail"] = out[:200]
            elif t == "keyevent":
                rc, out = _adb(device, ["shell", "input", "keyevent",
                                        str(st["code"])], timeout=adb_timeout)
                entry["ok"] = rc == 0
                entry["detail"] = out[:200]
            elif t == "navigate":
                rc, out = _adb(device, ["shell", "input", "keyevent",
                                        _NAV_KEYS[st["key"]]],
                               timeout=adb_timeout)
                entry["ok"] = rc == 0
                entry["detail"] = out[:200]
            elif t == "assert_pid":
                has_assert = True
                rc, out = _adb(device, ["shell", "pidof", pkg],
                               timeout=adb_timeout)
                entry["ok"] = rc == 0 and bool(out.strip())
                entry["detail"] = out.strip() or "không có pid"
            elif t == "assert_logcat":
                has_assert = True
                expect = st.get("expect", [])
                forbid = st.get("forbid", [])
                rc, out = _adb(device, ["logcat", "-d", "-t", "3000"],
                               timeout=adb_timeout)
                lines = out.splitlines()
                miss = [e for e in expect
                        if not any(re.search(e, ln) for ln in lines)]
                bad = [f for f in forbid
                       if any(re.search(f, ln) for ln in lines)]
                entry["ok"] = not miss and not bad
                entry["detail"] = ("expect thiếu: %s; forbid gặp: %s"
                                   % (miss, bad))
            elif t == "assert_no_crash":
                has_assert = True
                rc, out = _adb(device, ["logcat", "-d", "-t", "3000"],
                               timeout=adb_timeout)
                lines = out.splitlines()
                hits = [ln for ln in lines
                        if ("FATAL EXCEPTION" in ln or "AndroidRuntime" in ln)
                        and pkg in ln]
                entry["ok"] = not hits
                entry["detail"] = "%d dòng crash" % len(hits)
            elif t == "assert_no_anr":
                has_assert = True
                rc, out = _adb(device, ["logcat", "-d", "-t", "3000"],
                               timeout=adb_timeout)
                lines = out.splitlines()
                hits = [ln for ln in lines
                        if re.search(r"ANR in %s(?:$| )" % re.escape(pkg),
                                     ln)]
                entry["ok"] = not hits
                entry["detail"] = "%d dòng ANR" % len(hits)
            elif t == "screenshot":
                if not shots:
                    entry["ok"] = False
                    entry["detail"] = "cần --scenario-out để lưu ảnh"
                else:
                    name = st.get("name", "shot_%d" % i)
                    fpath = os.path.join(shots, name + ".png")
                    try:
                        subprocess.run(
                            ["adb", "-s", device, "exec-out", "screencap",
                             "-p"], stdout=open(fpath, "wb"),
                            timeout=adb_timeout, check=True)
                        entry["detail"] = fpath
                    except (OSError, subprocess.TimeoutExpired,
                            subprocess.CalledProcessError) as e:
                        entry["ok"] = False
                        entry["detail"] = "chụp lỗi: %r" % e
        except Exception as e:
            entry["ok"] = False
            entry["detail"] = "lỗi bước: %r" % e
        if not entry["ok"] and t.startswith("assert"):
            failed = True
        if t.startswith("assert") and not entry["ok"]:
            result["reasons"].append("bước %d (%s): %s"
                                     % (i, t, entry["detail"]))
        result["steps"].append(entry)
    if failed:
        result["status"] = "M3_FAIL"
    elif has_assert:
        result["status"] = "M3_PASS"
    else:
        result["reasons"].append("scenario không có bước assert nào — "
                                 "coi như SKIP")
    result["passed"] = result["status"] == "M3_PASS"
    return result
