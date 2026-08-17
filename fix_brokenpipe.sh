#!/data/data/com.termux/files/usr/bin/bash

FILE="./webui/server.py"

if [ ! -f "$FILE" ]; then
    echo "Không tìm thấy $FILE"
    exit 1
fi

cp "$FILE" "$FILE.bak"

python3 - <<PY
from pathlib import Path

f = Path("$FILE")
s = f.read_text()

old = "self.wfile.write(body)"
new = """try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            return"""

count = s.count(old)

if count:
    s = s.replace(old, new)
    f.write_text(s)
    print("Đã fix", count, "vị trí.")
    print("Backup:", FILE + ".bak")
else:
    print("Không tìm thấy dòng cần sửa.")
PY
