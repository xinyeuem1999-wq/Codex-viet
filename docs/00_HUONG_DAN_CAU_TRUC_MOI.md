# Cấu trúc Toolkit đơn giản

> Nhánh này chỉ là bản sắp xếp thử nghiệm. `master` không bị sửa.

## Mục tiêu

Giữ nguyên code đang chạy, chỉ làm cho người vận hành dễ hiểu:

```text
patchx
  ↓
Cửa vào (cli.py)
  ↓
┌───────────────┬────────────────┬────────────────┐
│ PHÂN TÍCH     │ LẬP KẾ HOẠCH   │ THỰC THI       │
│ model         │ semantic_plan  │ parser         │
│ smali_lib     │ plan_compile   │ engine         │
│ smali_sem     │ preflight      │ apply          │
└───────────────┴────────────────┴────────────────┘
                 ↓
              kiểm tra
                 ↓
                test
```

## 5 nhóm dễ nhớ

1. **Cửa vào** — `cli.py`
2. **Phân tích** — `model.py`, `smali_lib.py`, `smali_sem.py`, `smali_validate.py`
3. **Kế hoạch & an toàn** — `semantic_plan.py`, `plan_compile.py`, `plan_preflight.py`, `preflight.py`, `risk.py`
4. **Thực thi patch** — `parser.py`, `engine.py`
5. **Kho / kiểm thử / hỗ trợ** — các module còn lại như `indexer`, `optimizer`, `acceptance`, `baseline`, `failure_db`, `knowledge`, `simulate`...

## Nguyên tắc chuyển đổi

- Không sửa trực tiếp `master`.
- Không viết lại engine.
- Không xoá chức năng cũ.
- Khi cần đổi tên hoặc di chuyển module, tạo lớp tương thích/import lại để đường chạy cũ vẫn hoạt động.
- Mỗi bước phải kiểm tra CLI và test trước khi bước tiếp.

## Cách vận hành tối giản

```text
1. model APK
2. semantic-plan tìm mục tiêu
3. plan-compile tạo kế hoạch
4. plan-preflight/preflight kiểm tra
5. apply thực hiện
6. test kiểm tra kết quả
```

Các lệnh phụ chỉ dùng khi có nhu cầu cụ thể.
