#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Điều khiển máy ảo Redfinger làm worker (tận dụng tối đa tài nguyên):
  - compile  : aapt2 arm64 native compile resource trên máy ảo
  - zipalign : căn chỉnh APK trên máy ảo
  - runtime  : cài + smoke test APK (M2/M3) trên máy ảo
  - info     : trạng thái kết nối + công cụ
Máy chủ làm link/đóng gói, máy ảo làm các bước nặng — chạy song song.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

ADB = "adb"
DEVICE = os.environ.get("PATCHX_VM", "100.64.170.99:5555")
VM_AAPT2 = "/data/local/tmp/aapt2"
VM_ZIPALIGN = "/data/local/tmp/zipalign"
VM_SSH_PORT = 8022
VM_SSH_KEY = os.path.expanduser("~/.ssh/vm_key")
VM_SSH_USER = "u0_a85"


def _sh(args, timeout=120):
    p = subprocess.run(args, text=True, errors="replace",
                       capture_output=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _adb(args, timeout=120):
    return _sh([ADB, "-s", DEVICE] + args, timeout=timeout)


def _ssh_host():
    """Host SSH = DEVICE bỏ phần cổng adb (vd 100.64.170.99:5555 -> 100.64.170.99)."""
    return DEVICE.split(":")[0]


def _ssh(args, timeout=120):
    cmd = ["ssh", "-i", VM_SSH_KEY, "-p", str(VM_SSH_PORT),
           "-o", "StrictHostKeyChecking=no",
           "-o", "UserKnownHostsFile=/dev/null",
           "-o", "ConnectTimeout=15",
           "%s@%s" % (VM_SSH_USER, _ssh_host())] + list(args)
    return _sh(cmd, timeout=timeout)


def _ensure_connect():
    _adb(["connect", DEVICE], timeout=20)
    rc, out = _adb(["devices"], timeout=20)
    return DEVICE in out and "device" in out


def _ensure_tools():
    for vm_path, local in ((VM_AAPT2, os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "..", ".tmp_build", "vm_setup",
            "aapt2_arm64")), ):
        rc, out = _adb(["shell", "ls", vm_path], timeout=20)
        if rc != 0:
            print("push %s -> %s" % (local, vm_path))
            _adb(["push", local, vm_path])
            _adb(["shell", "chmod", "755", vm_path])


def cmd_info(_args):
    if not _ensure_connect():
        print("KHÔNG kết nối được máy ảo %s" % DEVICE)
        return 1
    rc, out = _adb(["shell", "getprop", "ro.build.version.release"])
    print("Máy ảo: %s (Android %s)" % (DEVICE, out.strip()))
    rc, out = _adb(["shell", "%s version" % VM_AAPT2])
    print("aapt2:", out.strip()[:60] or "chưa push (chạy vm compile trước)")
    rc, out = _adb(["shell", "ls", "-la", VM_ZIPALIGN])
    print("zipalign:", out.strip().splitlines()[0][:60]
          if out.strip() else "chưa có")
    return 0


def cmd_compile(args):
    """Nén cây res → máy ảo aapt2 compile → pull resources.zip."""
    if not _ensure_connect():
        print("KHÔNG kết nối được máy ảo — bấm chuông báo người dùng.")
        return 1
    _ensure_tools()
    tree = os.path.abspath(args.tree)
    res = os.path.join(tree, "res")
    if not os.path.isdir(res):
        print("Thiếu thư mục res/ trong %s" % tree)
        return 1
    tmp = tempfile.mkdtemp(prefix="patchx_vm_")
    try:
        tar = os.path.join(tmp, "res.tar.gz")
        with tarfile.open(tar, "w:gz") as tf:
            tf.add(res, arcname="res")
        print("Push res (%d MB)..." % (os.path.getsize(tar) // 1048576))
        t0 = time.monotonic()
        rc, out = _adb(["push", tar, "/data/local/tmp/res.tar.gz"], timeout=600)
        if rc != 0:
            print("push lỗi:", out[-300:])
            return 1
        rc, out = _adb(["shell",
                        "cd /data/local/tmp && tar xzf res.tar.gz && "
                        "%s compile --dir res -o resources.zip --legacy"
                        % VM_AAPT2], timeout=1200)
        if rc != 0:
            print("compile trên máy ảo lỗi:", out[-500:])
            return 1
        rc, out = _adb(["pull", "/data/local/tmp/resources.zip",
                        args.o], timeout=600)
        if rc != 0:
            print("pull lỗi:", out[-300:])
            return 1
        _adb(["shell", "rm -rf /data/local/tmp/res /data/local/tmp/res.tar.gz "
              "/data/local/tmp/resources.zip"], timeout=60)
        print("resources.zip: %s (%.1fs)" % (
            args.o, time.monotonic() - t0))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_zipalign(args):
    if not _ensure_connect():
        return 1
    rc, out = _adb(["push", args.apk, "/data/local/tmp/in.apk"], timeout=600)
    if rc != 0:
        print("push lỗi:", out[-300:])
        return 1
    rc, out = _adb(["shell", "chmod 755 %s && %s -f 4 /data/local/tmp/in.apk "
                    "/data/local/tmp/out.apk" % (VM_ZIPALIGN, VM_ZIPALIGN)],
                   timeout=600)
    if rc != 0:
        print("zipalign lỗi:", out[-300:])
        return 1
    rc, out = _adb(["pull", "/data/local/tmp/out.apk", args.o], timeout=600)
    _adb(["shell", "rm -f /data/local/tmp/in.apk /data/local/tmp/out.apk"],
         timeout=60)
    print("Đã zipalign qua máy ảo: %s" % args.o)
    return 0 if rc == 0 else 1


def cmd_runtime(args):
    """Chạy apk-runtime trên máy ảo (M2/M3 + mạng + chữ ký)."""
    from patchx_toolkit import cmd_apk_runtime
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    import argparse as _arg
    ns = _arg.Namespace(
        apk=args.apk, package=None, activity=None,
        connect=DEVICE, scan_local=False, wait=args.wait,
        logcat_lines=2000, expect=[], forbid=[],
        output=args.o, no_auto_install=True, no_capture_net=False)
    return cmd_apk_runtime(ns)


def cmd_termux(_args):
    """Trạng thái Termux + SSH trên máy ảo."""
    if not _ensure_connect():
        print("KHÔNG kết nối được máy ảo %s" % DEVICE)
        return 1
    rc, out = _adb(["shell", "ps -A | grep sshd"])
    print("Termux sshd:", "ĐANG CHẠY" if rc == 0 and "sshd" in out else "CHƯA CHẠY")
    rc, out = _ssh(["echo", "TERMUX_SSH_OK"])
    print("SSH từ máy thật:", out.strip() or "LỖI (rc=%s)" % rc)
    rc, out = _ssh(["dpkg -l | grep -E 'apktool|openjdk|python|apksigner'"])
    print("Goi quan trong:\n" + (out.strip() or "chua ro"))
    return 0


def cmd_ssh(args):
    """Chạy lệnh từ xa trong Termux của máy ảo."""
    if not _ensure_connect():
        print("KHÔNG kết nối được máy ảo %s" % DEVICE)
        return 1
    rc, out = _ssh(args.cmd, timeout=args.timeout)
    print(out, end="")
    return rc


def main():
    parser = argparse.ArgumentParser(description="Máy ảo worker (Redfinger)")
    sub = parser.add_subparsers(dest="lệnh")
    sub.add_parser("info", help="Trạng thái máy ảo").set_defaults(func=cmd_info)
    p = sub.add_parser("compile", help="Compile resource trên máy ảo")
    p.add_argument("tree")
    p.add_argument("-o", required=True, help="resources.zip đầu ra")
    p.set_defaults(func=cmd_compile)
    p = sub.add_parser("zipalign", help="Zipalign APK trên máy ảo")
    p.add_argument("apk")
    p.add_argument("-o", required=True)
    p.set_defaults(func=cmd_zipalign)
    p = sub.add_parser("runtime", help="M2/M3 trên máy ảo")
    p.add_argument("apk")
    p.add_argument("-o", default=".tmp_build/vm_runtime")
    p.add_argument("--wait", type=int, default=10)
    p.set_defaults(func=cmd_runtime)
    sub.add_parser("termux", help="Trạng thái Termux/SSH").set_defaults(func=cmd_termux)
    p = sub.add_parser("ssh", help="Chạy lệnh từ xa trong Termux máy ảo")
    p.add_argument("cmd", nargs="+")
    p.add_argument("--timeout", type=int, default=300)
    p.set_defaults(func=cmd_ssh)
    args = parser.parse_args()
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
