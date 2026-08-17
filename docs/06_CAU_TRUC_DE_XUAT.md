# CẤU TRÚC ĐỀ XUẤT — bản đơn giản

> Chỉ áp dụng trên nhánh `don-gian-hoa-toolkit`.
> Nhánh `master` giữ nguyên.

## Mục tiêu

Không viết lại toolkit. Chỉ gom các module hiện có theo 5 nhóm để người vận hành nhìn vào là hiểu.

```text
patchx/
├── Phân tích/
├── Tìm mục tiêu/
├── Kế hoạch/
├── Kiểm tra/
└── Thực hiện/
```

## Ánh xạ module hiện tại

### 1. Phân tích

- `model.py`
- `smali_lib.py`
- `smali_sem.py`
- `parser.py` (phần đọc cấu trúc patch vẫn giữ ở vị trí cũ cho đến khi kiểm tra import)

### 2. Tìm mục tiêu

- `semantic_plan.py`
- `remote_map.py`

### 3. Kế hoạch

- `plan_compile.py`
- `session.py`

### 4. Kiểm tra

- `preflight.py`
- `plan_preflight` (logic trong CLI)
- `smali_validate.py`
- `risk.py`
- `baseline.py`
- `dex_budget.py`
- `acceptance.py`
- `fuzz.py`

### 5. Thực hiện

- `parser.py`
- `engine.py`

## Nhóm phụ — chưa đưa vào đường chính

- Kho patch: `indexer.py`, `optimizer.py`, `combo.py`, `complement.py`
- Bộ nhớ: `knowledge.py`, `learn.py`, `failure_db.py`
- Trợ lý: `advisor.py`, `bypass_advisor.py`
- Công cụ: `audit.py`, `diffapk.py`, `simulate.py`, `runtime_scenario.py`
- Giao diện: `cli.py`

## Cách di chuyển an toàn

```text
1. Giữ nguyên master
2. Làm trên don-gian-hoa-toolkit
3. Sao chép module sang nhóm mới
4. Sửa import
5. Chạy test
6. Chạy `python3 patchx --help`
7. Chạy đường chính model → semantic-plan → plan-compile → plan-preflight → apply
8. Chỉ khi PASS mới xoá file cũ
```

## Trạng thái

**Đợt này chưa di chuyển file runtime.** Đây là chủ ý để không làm hỏng toolkit đang chạy. Các thư mục nhóm chỉ được tạo sau khi mapping import hoàn tất.
