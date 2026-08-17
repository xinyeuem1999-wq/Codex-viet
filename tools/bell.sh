#!/data/data/com.termux/files/usr/bin/sh
# Chuông báo hoàn thành đợt — cần app Termux:API (com.termux.api) trên thiết bị.
# Dùng: tools/bell.sh "Tiêu đề" "Nội dung"
title="$1"; content="$2"
command -v termux-notification >/dev/null 2>&1 || { echo "thiếu termux-api"; exit 1; }
timeout 8 termux-notification --id patchx_bell --title "$title" --content "$content" --sound --vibrate "1000,500,1000,500,1000" --led-color ff8800 --alert-once || \
  echo "Chuông chưa đổ được: cài app Termux:API từ F-Droid (com.termux.api)."
timeout 8 termux-vibrate -d 1200 2>/dev/null || true
exit 0
