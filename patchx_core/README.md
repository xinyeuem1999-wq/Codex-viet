# patchx_core — Bản đồ dễ hiểu

Đây là **bản đồ của toolkit**, không phải một pipeline mới.

## Đường chính

```text
APK đã giải mã
    ↓
model
    ↓
semantic-plan
    ↓
plan-compile
    ↓
plan-preflight
    ↓
apply
    ↓
kiểm tra / test
```

## 5 nhóm chức năng

| Nhóm | Nhiệm vụ | Module chính |
|---|---|---|
| 1. Phân tích | Đọc cây APK và tạo bản đồ | `model.py`, `smali_lib.py`, `smali_sem.py`, `analyze` |
| 2. Tìm mục tiêu | Tìm method/class phù hợp | `semantic_plan.py`, `remote_map.py` |
| 3. Kế hoạch | Chuẩn bị việc sẽ làm | `plan_compile.py` |
| 4. Kiểm tra | Kiểm tra trước/sau khi làm | `preflight.py`, `smali_validate.py`, `risk.py`, `baseline.py` |
| 5. Thực hiện | Đọc patch và sửa cây APK | `parser.py`, `engine.py` |

## Các nhóm phụ

- **Kho patch:** `indexer.py`, `optimizer.py`, `combo.py`, `complement.py`
- **Bộ nhớ:** `knowledge.py`, `learn.py`, `failure_db.py`
- **Kiểm thử:** `acceptance.py`, `simulate.py`, `fuzz.py`, `runtime_scenario.py`
- **Tiện ích:** `audit.py`, `diffapk.py`, `dex_budget.py`, `session.py`, `advisor.py`, `bypass_advisor.py`
- **Giao diện:** `cli.py`

## Quy tắc khi dọn cấu trúc

1. Không đổi tên lệnh CLI đang dùng.
2. Không đổi format patch.
3. Không đổi đường chạy chính nếu chưa có test chứng minh.
4. Không xóa module chỉ vì tên khó hiểu; phải xác định nơi gọi trước.
5. Mỗi lần di chuyển code phải chạy lại test.

> Giai đoạn này chỉ tạo bản đồ. Code hiện tại vẫn giữ nguyên vị trí để toolkit không bị vỡ.