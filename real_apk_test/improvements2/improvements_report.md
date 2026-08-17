# Bài tập cải thiện từ APK thật

- Thời gian: 2026-08-14 16:31:46
- Cây APK: `/storage/emulated/0/patch/1. PATCH others/_patchx/real_apk_test/app_tree`
- Áp patch: 0 lỗi; build: 1 lỗi

## apktool 3.x không còn cờ --use-aapt1

- Nguyên nhân: Phiên bản apktool hiện tại chỉ hỗ trợ `--aapt <file>`, không có cờ chuyển aapt1 như các bản cũ.
- Hướng sửa: Dùng `apktool b --aapt /path/to/aapt2` hoặc cài apktool 2.x nếu thật sự cần aapt1; đồng thời bỏ tuỳ chọn `--use-aapt1` khỏi toolkit khi chạy apktool 3.x.
