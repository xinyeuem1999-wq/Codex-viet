# Bài tập cải thiện từ APK thật

- Thời gian: 2026-08-14 16:34:34
- Cây APK: `/storage/emulated/0/patch/1. PATCH others/_patchx/real_apk_test/app_tree`
- Áp patch: 0 lỗi; build: 1 lỗi

## Tên resource chứa ký tự `$` làm aapt2 từ chối

- Nguyên nhân: Cây APK giải mã cũ có tên resource bắt đầu bằng `$` ($avd_..., $feedback_...); aapt2 không chấp nhận tên này.
- Hướng sửa: Chuẩn hoá tên file trong res/ bằng cách loại bỏ ký tự `$`, cập nhật tham chiếu trong public.xml/values nếu cần; nếu vẫn lỗi thì dùng apktool 2.x/aapt1 cho cây APK cũ.
