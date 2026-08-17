# PatchX — cấu trúc đơn giản

Mục tiêu của nhánh này là **dễ hiểu và dễ vận hành**, không viết lại engine.
Code thật vẫn nằm trong `patchx_core/`; thư mục `patchx_don_gian/` chỉ IMPORT lại.

## Nhìn toolkit như 5 bộ phận

```text
APK / cây APK
    ↓
1. MẮT        → đọc, quét, tạo model
    ↓
2. BỘ NÃO     → tìm mục tiêu, lập kế hoạch
    ↓
3. KIỂM TRA   → preflight / validate / baseline
    ↓
4. NGƯỜI THỢ  → apply / engine
    ↓
5. BỘ NHỚ     → knowledge / failure / learn
```

## Module đang dùng lại

| Bộ phận | Module thật trong `patchx_core` |
|---|---|
| Mắt | `parser`, `indexer`, `model`, `semantic_plan` |
| Bộ não | `semantic_plan`, `plan_compile` |
| Kiểm tra | `preflight`, `smali_validate`, `dex_budget`, `baseline` |
| Người thợ | `engine`, `audit` |
| Bộ nhớ | `knowledge`, `failure_db`, `learn` |

## Chạy

Cách cũ vẫn giữ nguyên:

```bash
python3 patchx --help
```

Cách nhìn theo cấu trúc mới:

```bash
python3 -m patchx_don_gian --help
```

Hai cách dùng chung CLI hiện có. Không có engine thứ hai.

## Nguyên tắc của nhánh này

- Không sửa `master`.
- Không xoá code cũ chỉ để làm đẹp.
- Không chép lại logic đã có.
- Không tạo engine song song.
- Chỉ tạo lớp tên dễ hiểu và IMPORT code cũ.
- Khi hiểu rõ từng bộ phận rồi mới tính chuyện di chuyển file thật.
