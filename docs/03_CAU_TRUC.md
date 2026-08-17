# Bản đồ thư mục

Không đổi đường dẫn code hiện tại ở bước này để tránh làm hỏng import và lệnh đang chạy.

```text
patchx                 ← lệnh chính, người dùng gọi ở đây
patchx_core/           ← lõi xử lý của toolkit
tests/                 ← kiểm thử

tests/fixtures/        ← dữ liệu mẫu để test
baseline/              ← số liệu chuẩn / cổng hồi quy

patches/ / kho patch   ← patch thực tế (nếu có trong repo)

docs/                  ← tài liệu dễ đọc cho người dùng
```

## patchx_core/ đọc thế nào?

Không cần học 30 file cùng lúc. Nhóm theo nhiệm vụ:

| Nhóm | File chính | Ý nghĩa |
|---|---|---|
| Giao diện | `cli.py` | nhận lệnh từ người dùng |
| Phân tích | `model.py`, `smali_sem.py` | tạo bản đồ APK |
| Tìm mục tiêu | `semantic_plan.py` | chọn mục tiêu theo quy tắc |
| Kiểm tra | `preflight.py`, `smali_validate.py` | chặn lỗi trước khi làm |
| Thực hiện | `engine.py` | áp thay đổi |
| Kế hoạch | `plan_compile.py` | chuẩn bị transaction |
| Nghiệm thu | `acceptance.py` | kiểm tra tiêu chí V2 |
| Bộ nhớ | `baseline.py`, `knowledge.py`, `failure_db.py` | lưu kết quả và lỗi |

Các module khác tạm xem là **tính năng phụ**. Chưa cần hiểu chúng để vận hành đường chính.
