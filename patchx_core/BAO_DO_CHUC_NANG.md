# BẢN ĐỒ PATCHX — BẢN ĐƠN GIẢN

Mục tiêu của nhánh này là **dễ hiểu và dễ vận hành**, không viết lại chức năng.

## 1. Chỉ nhớ 5 nhóm

| Nhóm | Việc chính | Module hiện có |
|---|---|---|
| 1. NHÌN | đọc patch/APK, phân tích | `parser.py`, `indexer.py`, `analyze`/`model` |
| 2. HIỂU | tìm mục tiêu, lập kế hoạch | `advisor.py`, `semantic_plan.py`, `knowledge.py`, `roadmap.py` |
| 3. KIỂM TRA | kiểm tra trước/sau | `preflight.py`, `plan_preflight.py`, `acceptance.py`, `smali_validate.py`, `risk.py` |
| 4. LÀM | áp/gộp/tạo patch | `engine.py`, `plan_compile.py`, `optimizer.py`, `combo.py`, `diffapk.py`, `remote_patch` |
| 5. NHỚ | baseline, lỗi, kết quả | `baseline.py`, `failure_db.py`, `learn.py`, `audit.py` |

Các module chuyên biệt như DEX, fuzz, runtime, JNI/smali vẫn giữ nguyên; **không cần nhớ hết khi vận hành bình thường**.

## 2. Luồng vận hành dễ nhớ

```text
APK / PATCH
    ↓
1. NHÌN       → analyze / model
    ↓
2. HIỂU       → semantic-plan / knowledge
    ↓
3. KIỂM TRA   → preflight
    ↓
4. LÀM        → apply / plan-compile
    ↓
5. KIỂM TRA   → verify / acceptance / test
    ↓
6. NHỚ        → baseline / failure
```

**Không cần chạy tất cả lệnh.** Chỉ chọn đúng bước mình đang làm.

## 3. Các lệnh người dùng nên nhớ

### Kho patch

- `scan` — xem kho có gì
- `dupes` — tìm bản trùng
- `index` — lập chỉ mục
- `report` — xem báo cáo

### APK

- `apk-prepare` — chuẩn bị cây APK
- `validate` — kiểm tra cây APK
- `analyze` — phân tích APK
- `model` — tạo bản đồ dữ liệu/method

### Lập kế hoạch an toàn

- `semantic-plan` — xác định mục tiêu
- `plan-compile` — tạo kế hoạch nháp
- `plan-preflight` — kiểm tra kế hoạch
- `preflight` — kiểm tra trước khi làm

### Thực hiện

- `apply` — áp patch
- `combo` — ghép patch
- `diff-apk` — tạo patch từ khác biệt

### Kiểm tra và ghi nhớ

- `acceptance` — nghiệm thu
- `test` — tự kiểm tra
- `baseline` — chụp/so sánh trạng thái chuẩn
- `failure` — tra lỗi và regression
- `knowledge` — tra kết quả đã biết

## 4. Những thứ chưa cần đụng vào

`advisor`, `optimizer`, `runtime_scenario`, `remote_map`, `remote_patch`, `dex_budget`, `fuzz`, `simulate`, `suggest-*` là các chức năng nâng cao. Chúng **không bị xoá**, nhưng không đưa vào luồng vận hành cơ bản.

## 5. Nguyên tắc của nhánh đơn giản

1. Giữ nguyên chức năng cũ.
2. Không đổi tên module đang được import nếu chưa có lớp tương thích.
3. Không chạy AI để quyết định thay người dùng.
4. Không bỏ qua `preflight` khi áp patch.
5. Không chắc target thì dừng.
6. `master` không phải nơi thử nghiệm cấu trúc.
