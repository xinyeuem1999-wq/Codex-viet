#!/data/data/com.termux/files/usr/bin/sh
exec /data/data/com.termux/files/usr/bin/qemu-x86_64 "$(dirname "$0")/aapt2_64" "$@"
