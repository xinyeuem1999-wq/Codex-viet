# Bài tập cải thiện từ APK thật

- Thời gian: 2026-08-14 16:31:14
- Cây APK: `/storage/emulated/0/patch/1. PATCH others/_patchx/real_apk_test/app_tree`
- Áp patch: 0 lỗi; build: 1 lỗi

## Patch không thay đổi gì trên APK thật

- Nguyên nhân: MATCH/TARGET không khớp class/method của APK đích.
- Hướng sửa: Chạy `coverage`/`roadmap` trước, lấy class-link thật từ manifest/smali rồi cập nhật TARGET/MATCH.
