# PatchX — Bản đồ nhanh

Nếu bạn quên toolkit hoạt động thế nào, bắt đầu từ file này.

## Tôi muốn làm gì?

| Việc | Lệnh |
|---|---|
| Xem toàn bộ lệnh | `python3 patchx --help` |
| Xem cách dùng một lệnh | `python3 patchx <lenh> --help` |
| Tạo model APK | `python3 patchx model <cay_apk> --v2` |
| Đánh giá kế hoạch | `python3 patchx semantic-plan ...` |
| Biên dịch kế hoạch | `python3 patchx plan-compile ...` |
| Kiểm tra trước khi áp | `python3 patchx plan-preflight ...` / `preflight ...` |
| Áp patch | `python3 patchx apply ...` |
| Chạy test | `python3 patchx test` |

## Đọc tiếp

1. `01_BAT_DAU.md` — cách vận hành.
2. `02_SO_DO.md` — toolkit gồm 5 bộ phận.
3. `03_CAU_TRUC.md` — đọc thư mục và file lõi.
4. `04_PHAT_TRIEN.md` — cách sửa code mà không làm rối hệ thống.

## Một câu cần nhớ

**Model để nhìn → Semantic để tìm → Preflight để chặn → Apply để làm → Test để xác nhận.**
