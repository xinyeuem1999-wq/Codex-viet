#!/data/data/com.termux/files/usr/bin/bash
set -e

pkg update
pkg install -y git python

chmod +x git.py
cp git.py "$PREFIX/bin/gitui"
chmod +x "$PREFIX/bin/gitui"

echo
echo "✅ Đã cài Git Manager."
echo "Vào một Git repository rồi chạy: gitui"
