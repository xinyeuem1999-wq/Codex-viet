# Bắt đầu với PatchX

PatchX được vận hành theo 1 đường chính:

`APK/cây APK → phân tích → tìm mục tiêu → kiểm tra → lập kế hoạch → preflight → áp patch → kiểm tra kết quả`

## 1. Khi chỉ muốn xem APK

```bash
python3 patchx model <cay_apk> --v2
```

Lệnh này **chỉ đọc**, tạo mô hình phân tích. Không áp patch.

## 2. Khi muốn kiểm tra kế hoạch

```bash
python3 patchx semantic-plan <plan.json> <app_model.json>
python3 patchx plan-compile <plan.json> <app_model.json>
python3 patchx plan-preflight <transaction.json>
```

Ba bước này vẫn thuộc vùng **chỉ đọc / chuẩn bị**.

## 3. Khi thật sự muốn áp patch

Chỉ dùng `apply` sau khi đã biết rõ cây APK, patch và kết quả preflight.

```bash
python3 patchx preflight <cay_apk> <patch>
python3 patchx apply <cay_apk> <patch>
```

## 4. Khi quên cách dùng

```bash
python3 patchx --help
python3 patchx <lenh> --help
```

Không cần nhớ toàn bộ toolkit. Chỉ cần nhớ đường chính và tra `--help` khi cần.
