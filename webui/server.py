#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Web UI cho toàn bộ bộ patchx — chạy trên điện thoại qua Termux.

Dùng: python3 webui/server.py [--host 127.0.0.1] [--port 8787]
Mở trình duyệt: http://127.0.0.1:8787

API:
  GET  /               → trang dashboard (index.html)
  GET  /static/*       → tệp tĩnh
  GET  /api/state      → trạng thái môi trường + kho + APK
  POST /api/run        → chạy lệnh patchx, trả log stream (chunked)
  GET  /api/plan_ui    → đường dẫn trang kế hoạch vượt chặn gần nhất
  GET  /plan_ui        → chính trang đó (nếu có)
  GET  /api/tree       → duyệt thư mục cây APK (Manual Mode)
  GET  /api/file       → nội dung tệp trong cây APK (giới hạn 512KB)
  GET  /api/search     → tìm chuỗi trong cây APK bằng rg (50 kết quả)
  POST /api/manual_save→ lưu patch tạm để chạy thử / áp thủ công
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.abspath(__file__))   # webui/
TOOLKIT = os.path.dirname(ROOT)                     # _patchx/
STATIC = os.path.join(ROOT, "static")
LOGS = os.path.join(ROOT, "logs")
PY = sys.executable or "python3"

COMMON = {"text": True, "bufsize": 1}

# Các máy điều phối (P21 — Worker Manager)
ADB_CLIENTS = [
    {"name": "Pixel 7", "addr": "100.64.170.99:5555", "transport": "adb",
     "role": "Thiết bị kiểm thử M2/M3"},
    {"name": "Samsung S26", "addr": "100.76.244.117:5555",
     "transport": "adb + ssh", "role": "Máy build + benchmark 64K DEX",
     "ssh": {"port": 8022, "user": "u0_a81",
             "key": "/data/data/com.termux/files/usr/tmp/vm2_key"}},
]


def _which(name):
    import shutil
    return shutil.which(name) or ""


def _run_quick(argv, timeout=60):
    """Chạy lệnh ngắn, trả (mã, stdout)."""
    try:
        p = subprocess.run(argv, cwd=TOOLKIT, capture_output=True, text=True,
                           timeout=timeout)
        return p.returncode, p.stdout
    except Exception as e:
        return -1, str(e)


def _count_zip(d):
    try:
        return len([f for f in os.listdir(d)
                    if not f.startswith(".") and not f.lower().endswith(".md")])
    except OSError:
        return 0


def _apks():
    d = os.path.join(TOOLKIT, "Apks")
    out = []
    try:
        for f in sorted(os.listdir(d)):
            if f.lower().endswith(".apk"):
                p = os.path.join(d, f)
                out.append({"name": f, "size": os.path.getsize(p)})
    except OSError:
        pass
    return out


def _trees():
    d = os.path.join(TOOLKIT, "apk_trees")
    out = []
    try:
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            if os.path.isdir(p) and os.path.isfile(os.path.join(p, "apktool.yml")):
                out.append(f)
    except OSError:
        pass
    return out


def _latest_plan_ui():
    best, best_t = None, -1
    for root, dirs, files in os.walk(TOOLKIT):
        dirs[:] = [d for d in dirs if not d.startswith((".", "apk_trees", "real_apk_test"))]
        if "bypass_plan_ui.html" in files:
            p = os.path.join(root, "bypass_plan_ui.html")
            t = os.path.getmtime(p)
            if t > best_t:
                best, best_t = p, t
    return best


def _ancestors():
    """Tập PID của chính mình + toàn bộ chuỗi tiến trình cha (để không giết)."""
    out = set()
    pid = os.getpid()
    seen = set()
    while pid > 1 and pid not in seen:
        seen.add(pid)
        out.add(str(pid))
        try:
            with open("/proc/%d/stat" % pid) as fh:
                parts = fh.read().rsplit(")", 1)[-1].split()
            pid = int(parts[1])  # ppid nằm sau dấu ")" trong stat
        except (OSError, IndexError, ValueError):
            break
    return out


def _kill_old_servers():
    """Tắt mọi server web/http cũ của dự án đang chạy (webui/server.py,
    patchx_toolkit.py webui, python3 -m http.server) — /proc/net/tcp bị
    sandbox Android chặn nên không tìm được PID theo cổng, phải dò cmdline."""
    import signal as _sig
    # Không bao giờ tự giết mình hay bất kỳ tổ tiên nào (shell, timeout,
    # patchx_toolkit.py webui...) — chỉ giết server cũ là "anh em" tiến trình.
    me = _ancestors()
    killed = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or pid in me:
            continue
        cmd = _cmdline(pid)
        if not cmd:
            continue
        if "webui/server.py" in cmd or "http.server" in cmd:
            try:
                os.kill(int(pid), _sig.SIGTERM)
            except OSError:
                continue
            killed.append(pid)
    for pid in killed:
        for _ in range(20):
            try:
                os.kill(int(pid), 0)
            except OSError:
                break
            time.sleep(0.1)
        else:
            try:
                os.kill(int(pid), _sig.SIGKILL)
            except OSError:
                pass
    return killed


def _cmdline(pid):
    try:
        with open("/proc/%s/cmdline" % pid, "rb") as fh:
            return fh.read().decode("utf-8", "replace").replace("\x00", " ")
    except OSError:
        return ""


def _local_ips():
    """Lấy IP nội bộ của máy để mở từ thiết bị khác (không cần mạng ngoài)."""
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    return sorted(ips)


def _adb_devices():
    rc, out = _run_quick(["adb", "devices"], timeout=15)
    devs = set()
    for line in (out or "").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devs.add(parts[0])
    return devs


def _adb_prop(addr, prop):
    rc, out = _run_quick(["adb", "-s", addr, "shell", "getprop", prop],
                         timeout=8)
    return (out or "").strip() if rc == 0 else ""


def _ssh_ok(cfg):
    key = cfg.get("key") or ""
    if not os.path.isfile(key):
        return False, "thiếu khóa SSH"
    try:
        p = subprocess.run(
            ["ssh", "-i", key, "-p", str(cfg.get("port", 8022)),
             "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
             "%s@%s" % (cfg["user"], cfg["addr"]), "echo ok"],
            capture_output=True, text=True, timeout=12)
        ok = p.returncode == 0 and "ok" in (p.stdout or "")
        return ok, (p.stdout or (p.stderr or "")).strip()[:100]
    except Exception as e:
        return False, str(e)[:100]


def _loadavg():
    try:
        with open("/proc/loadavg") as fh:
            return fh.read().split()[0]
    except OSError:
        return "—"


def build_workers():
    """Trạng thái 3 máy: máy chính + 2 client (adb/ssh)."""
    devs = _adb_devices()
    main = {
        "name": "Máy chính",
        "model": "Termux (aarch64)",
        "role": "Toolkit + điều phối + webui",
        "ok": True,
        "load": _loadavg(),
        "toolkit": TOOLKIT,
        "time": time.strftime("%H:%M:%S"),
    }
    clients = []
    for c in ADB_CLIENTS:
        item = dict(c)
        item["ok"] = c["addr"] in devs
        item["model"] = _adb_prop(c["addr"], "ro.product.model") \
            if item["ok"] else ""
        item["android"] = _adb_prop(c["addr"], "ro.build.version.release") \
            if item["ok"] else ""
        if c.get("ssh"):
            s_ok, s_d = _ssh_ok(dict(c["ssh"],
                                    addr=c["addr"].split(":")[0]))
            item["ssh_ok"] = s_ok
            item["ssh_detail"] = s_d
        clients.append(item)
    return {"generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "main": main, "clients": clients}


def build_state():
    tools = {}
    for name in ("python3", "java", "apktool", "aapt2", "zipalign", "apksigner",
                 "adb", "termux-notification", "rg"):
        tools[name] = bool(_which(name))
    state = {
        "tools": tools,
        "patches": _count_zip(os.path.join(TOOLKIT, "upgraded")),
        "combos": _count_zip(os.path.join(TOOLKIT, "combos")),
        "combos_auto": _count_zip(os.path.join(TOOLKIT, "combos_auto")),
        "apks": _apks(),
        "trees": _trees(),
        "plan_ui": _latest_plan_ui(),
        "toolkit": TOOLKIT,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return state




def _tree_base(apk):
    """Trả đường dẫn gốc cây APK từ tên cây (apk_trees/<tên>) hoặc đường dẫn."""
    if os.path.isabs(apk):
        return apk
    return os.path.join(TOOLKIT, "apk_trees", apk)


def _tree_resolve(apk, rel):
    """Chuẩn hoá rel trong cây APK; None nếu trốn ra ngoài."""
    base = os.path.realpath(_tree_base(apk))
    if not os.path.isdir(base):
        return None, None
    cur = os.path.realpath(os.path.join(base, rel or ""))
    if cur != base and not cur.startswith(base + os.sep):
        return None, None
    return base, cur


def tree_list(apk, rel):
    base, cur = _tree_resolve(apk, rel)
    if not cur or not os.path.isdir(cur):
        return None
    dirs, files = [], []
    try:
        for name in sorted(os.listdir(cur)):
            p = os.path.join(cur, name)
            if os.path.isdir(p):
                dirs.append(name)
            else:
                try:
                    sz = os.path.getsize(p)
                except OSError:
                    sz = 0
                files.append({"name": name, "size": sz})
    except OSError:
        return None
    rel_cur = os.path.relpath(cur, base)
    if rel_cur == ".":
        rel_cur = ""
    return {"apk": apk, "dir": rel_cur.replace(os.sep, "/"),
            "dirs": dirs, "files": files}


def tree_file(apk, rel, limit=512 * 1024):
    base, cur = _tree_resolve(apk, rel)
    if not cur or not os.path.isfile(cur):
        return None
    size = os.path.getsize(cur)
    try:
        with open(cur, "rb") as fh:
            data = fh.read(limit)
    except OSError:
        return None
    truncated = size > len(data)
    binary = b"\x00" in data[:8192]
    text = ""
    if not binary:
        text = data.decode("utf-8", "replace")
    return {"name": os.path.basename(cur), "size": size,
            "path": os.path.relpath(cur, base).replace(os.sep, "/"),
            "text": text, "truncated": truncated, "binary": binary}


def tree_search(apk, q, limit=50, timeout=25):
    base, cur = _tree_resolve(apk, "")
    if not cur or not q:
        return None
    try:
        p = subprocess.run(
            ["rg", "-l", "-i", "-m", "1", "--", q, base],
            cwd=TOOLKIT, capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None
    hits = []
    for line in (p.stdout or "").splitlines():
        if not line.startswith(base):
            continue
        rel = os.path.relpath(line, base).replace(os.sep, "/")
        hits.append(rel)
        if len(hits) >= limit:
            break
    return {"apk": apk, "q": q, "hits": hits}


def save_manual(content, name):
    d = os.path.join(TOOLKIT, "toolkit_out")
    os.makedirs(d, exist_ok=True)
    fn = (name or "manual_patch.txt").strip()
    if not fn.endswith(".txt"):
        fn += ".txt"
    fn = os.path.basename(fn)
    p = os.path.join(d, fn)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(content or "")
    return os.path.relpath(p, TOOLKIT).replace(os.sep, "/")


class PatchxServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    server_version = "PatchxWebUI/1.0"

    def log_message(self, fmt, *args):
        pass

    # ---- tiện ích ----
    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _chunk(self, text):
        b = text.encode("utf-8", "replace")
        self.wfile.write(("%x\r\n" % len(b)).encode("ascii") + b + b"\r\n")
        self.wfile.flush()

    def _file(self, path, ctype):
        try:
            with open(path, "rb") as fh:
                body = fh.read()
        except OSError:
            self._json({"lỗi": "không tìm thấy tệp"}, 404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---- GET ----
    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            return self._file(os.path.join(STATIC, "index.html"),
                              "text/html; charset=utf-8")
        if u.path.startswith("/static/"):
            rel = u.path[len("/static/"):]
            p = os.path.normpath(os.path.join(STATIC, rel))
            if not p.startswith(STATIC):
                return self._json({"lỗi": "đường dẫn không hợp lệ"}, 400)
            ctype = "text/plain; charset=utf-8"
            if rel.endswith(".html"):
                ctype = "text/html; charset=utf-8"
            elif rel.endswith(".css"):
                ctype = "text/css; charset=utf-8"
            elif rel.endswith(".js"):
                ctype = "application/javascript; charset=utf-8"
            return self._file(p, ctype)
        if u.path == "/api/state":
            return self._json(build_state())
        if u.path == "/api/workers":
            return self._json(build_workers())
        if u.path == "/api/plan_ui":
            p = _latest_plan_ui()
            return self._json({"path": p or "", "exists": bool(p)})
        if u.path == "/api/tree":
            q = parse_qs(u.query)
            apk = (q.get("apk") or [""])[0]
            rel = (q.get("p") or [""])[0]
            r = tree_list(apk, rel)
            if r is None:
                return self._json({"lỗi": "không tìm thấy cây APK / thư mục"}, 404)
            return self._json(r)
        if u.path == "/api/file":
            q = parse_qs(u.query)
            apk = (q.get("apk") or [""])[0]
            rel = (q.get("p") or [""])[0]
            r = tree_file(apk, rel)
            if r is None:
                return self._json({"lỗi": "không tìm thấy tệp"}, 404)
            return self._json(r)
        if u.path == "/api/search":
            q = parse_qs(u.query)
            apk = (q.get("apk") or [""])[0]
            qq = (q.get("q") or [""])[0].strip()
            if not apk or not qq:
                return self._json({"lỗi": "thiếu apk / q"}, 400)
            return self._json(tree_search(apk, qq) or {"apk": apk, "q": qq, "hits": []})
        if u.path == "/plan_ui":
            p = _latest_plan_ui()
            if p:
                return self._file(p, "text/html; charset=utf-8")
            return self._json({"lỗi": "chưa có kế hoạch — chạy apk-plan trước"}, 404)
        return self._json({"lỗi": "không biết đường dẫn"}, 404)

    # ---- POST ----
    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/api/manual_save":
            try:
                n = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
            except Exception as e:
                return self._json({"lỗi": "dữ liệu sai: %s" % e}, 400)
            try:
                path = save_manual(data.get("content", ""), data.get("name", ""))
            except Exception as e:
                return self._json({"lỗi": "không lưu được: %s" % e}, 500)
            return self._json({"path": path})
        if u.path != "/api/run":
            return self._json({"lỗi": "không biết đường dẫn"}, 404)
        try:
            n = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
        except Exception as e:
            return self._json({"lỗi": "dữ liệu sai: %s" % e}, 400)
        argv = data.get("argv") or []
        if not argv:
            return self._json({"lỗi": "thiếu argv"}, 400)
        timeout = int(data.get("timeout", 1800))

        # Chuẩn hoá: "patchx ..." / "patchx_toolkit.py ..." → python3 <script>
        if argv[0] in ("patchx",):
            cmd = [PY, "patchx"] + argv[1:]
        elif argv[0] in ("patchx_toolkit.py", "patchx_toolkit"):
            cmd = [PY, "patchx_toolkit.py"] + argv[1:]
        else:
            cmd = argv

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        def _log_line(s):
            try:
                self._chunk(s + "\n")
            except (BrokenPipeError, ConnectionResetError):
                return False
            return True

        _log_line("$ " + " ".join(cmd))
        t0 = time.time()
        try:
            p = subprocess.Popen(cmd, cwd=TOOLKIT, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, **COMMON)
        except Exception as e:
            _log_line("LỖI khởi động: %s" % e)
            self._chunk("")
            return

        try:
            for line in p.stdout:
                if not _log_line(line.rstrip("\n")):
                    p.kill()
                    break
            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            _log_line("\n⚠ QUÁ THỜI GIAN (%ss) — đã dừng lệnh." % timeout)
        except Exception as e:
            p.kill()
            _log_line("\nLỖI: %s" % e)
        dt = time.time() - t0
        _log_line("\nHoàn tất sau %.1fs (mã thoát %s)." % (dt, p.returncode))
        self._chunk("")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="webui/server.py",
                                 description="Web UI toàn bộ patchx")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    args = ap.parse_args(argv)
    os.makedirs(LOGS, exist_ok=True)

    # Ưu tiên: cổng bận → TẮT server cũ rồi dùng ĐÚNG cổng yêu cầu.
    # Chỉ nhảy cổng khi không tắt được (server lạ, không phải web/http của ta).
    port = args.port
    if port == 0:
        port = 8787
    srv = None
    first = port
    for cand in list(range(first, first + 20)):
        for attempt in range(2):
            try:
                srv = PatchxServer((args.host, cand), Handler)
                port = cand
                break
            except OSError:
                if attempt == 0:
                    killed = _kill_old_servers()
                    if killed:
                        print("Đã tắt server cũ (PID %s) đang chiếm cổng %s."
                              % (", ".join(killed), cand), flush=True)
                        time.sleep(0.3)
                        continue
                break
        if srv is not None:
            break
        if cand == first:
            print("Cảnh báo: cổng %s bị chiếm và không tắt được — tự dùng "
                  "cổng %s." % (first, cand + 1), flush=True)
    if srv is None:
        print("LỖI: không mở được cổng nào từ %s trở đi (đều bận)." % first, flush=True)
        return 1
    print("Patchx Web UI: http://%s:%s  (Ctrl+C để dừng)" % (args.host, port), flush=True)
    print("Thư mục làm việc: %s" % TOOLKIT, flush=True)
    if args.host == "0.0.0.0":
        for ip in _local_ips():
            print("Mở từ điện thoại/máy khác: http://%s:%s" % (ip, port), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
