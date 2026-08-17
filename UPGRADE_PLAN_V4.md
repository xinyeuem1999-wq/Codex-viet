# Quy trình phát triển và nâng cấp ToolPatch — Hợp nhất logic

Phiên bản: V4. Mục tiêu: biến các công cụ rời rạc thành một dây chuyền thống
nhất, mỗi bước đều có đầu vào/đầu ra rõ ràng, đo được và tự cải thiện.

## 1. Tầm nhìn

ToolPatch trở thành một toolkit tự hành:

```text
APK hoặc cây APK
      ↓
1. Inventory  → hiểu cây APK có gì
      ↓
2. Candidate  → lọc patch có khả năng khớp
      ↓
3. Plan       → xếp hạng patch/combo theo bằng chứng
      ↓
4. Apply      → áp patch an toàn, idempotent
      ↓
5. Build      → chuẩn hoá tài nguyên, rebuild bằng aapt đúng
      ↓
6. Verify     → ký, cài, logcat, ghi bài tập cải thiện
      ↓
APK bypass + báo cáo + bài học
```

## 2. Sáu tầng thống nhất

### T1 — Inventory
- Quét nhanh cây APK: manifest, smali, resource, apktool.yml.
- Lưu cache theo hash cây APK.
- Đầu ra: `inventory.json`.

### T2 — Candidate
- Dùng `rg`/index/hash để lọc file ứng viên trước khi regex.
- Không quét regex toàn bộ 477M text.
- Đầu ra: danh sách patch ứng viên + lý do.

### T3 — Plan
- Điểm = bao phủ + số khớp + trọng số năng lực.
- Xếp patch đơn và combo bổ trợ từ cao đến thấp.
- Đầu ra: `bypass_plan.json/md`.

### T4 — Apply
- `session` chọn patch người dùng muốn.
- `Engine.apply_many` idempotent + backup.
- Đầu ra: thay đổi thật trên cây APK.

### T5 — Build
- `apk-fix-res` chuẩn hoá resource `$`.
- `apktool b --aapt <aapt2>`.
- Đầu ra: APK chưa ký.

### T6 — Verify
- zipalign + apksigner.
- `apksigner verify`.
- Cài/emulator + logcat + mạng nếu có.
- `apk-test` sinh `improvements_report`.

## 3. Ánh xạ lệnh hiện có → tầng

| Tầng | Lệnh hiện có | Trạng thái |
|---|---|---|
| Inventory | `scan`, `manifest`, `selfcheck` | đã có |
| Candidate | `coverage`, `roadmap` | cần tối ưu tốc độ |
| Plan | `apk-plan`, `list` | đã có |
| Apply | `apply`, `session` | đã có |
| Build | `apk-fix-res`, `apktool b` | đã có |
| Verify | `apk-test`, apksigner | đã có |

## 4. Dây chuyền tự động `apk-full` cần xây tiếp

Lệnh mục tiêu:

```sh
python3 patchx_toolkit.py apk-full \
  --tree real_apk_test/app_tree \
  --input upgraded \
  --top 3 \
  --build \
  --sign \
  --aapt /data/data/com.termux/files/usr/bin/aapt2 \
  --output real_apk_test/apk_full_out
```

`apk-full` sẽ chạy tuần tự:

1. Inventory nhanh + chọn top patch theo năng lực/khớp.
2. Apply các patch đã chọn.
3. `apk-fix-res`.
4. `apktool b`.
5. zipalign + sign + verify.
6. Ghi `apk_full_report.json/md`.

## 5. Quy tắc đồng bộ dữ liệu

- Mọi tầng đều ghi JSON vào cùng thư mục output.
- Tên tệp ổn định: `inventory.json`, `candidates.json`,
  `bypass_plan.json`, `apply_report.json`, `build_report.json`,
  `verify_report.json`.
- Mỗi bước đọc kết quả bước trước, không tự đoán lại.

## 6. Vòng tự cải thiện

Mỗi lỗi phát sinh được chuyển thành bài tập:

```text
lỗi apply/build/verify
      ↓
phân loại bằng _apk_error_exercises
      ↓
improvements.json/md
      ↓
sửa toolkit hoặc patch
      ↓
test 64/64 + rebuild
```

## 7. Lộ trình phát triển

### Đợt A — Tốc độ Inventory/Candidate
- Tích hợp `rg`/hash vào `coverage_patch_cached`.
- Cache inventory theo hash APK.
- Nghiệm thu: quét APK 477M < 60s cho candidate; không treo regex.

### Đợt B — `apk-full` end-to-end
- Xây lệnh `apk-full`.
- Tự chọn top patch, apply, build, sign.
- Nghiệm thu: chạy `apk-full` trên APK thật tạo APK ký hợp lệ.

### Đợt C — Runtime verify
- Kết nối adb/emulator.
- Smoke test + logcat + bắt mạng.
- Nghiệm thu: M2/M3 đạt trên 1 APK thật.

### Đợt D — Golden tests
- APK mẫu nhỏ trong `tests/fixtures/`.
- Mọi thay đổi engine phải rebuild không tụt.
- Nghiệm thu: CI tự chạy `test + rebuild golden`.

## 8. Nghiệm thu tổng

- Test: ≥ 64 bài, không tụt.
- Full pipeline `run`: 12/12.
- Simulate: không dưới 51 ĐẠT.
- `apk-full`: tạo APK ký v2/v3 hợp lệ từ APK thật.
- Báo cáo lỗi: có `improvements_report`.
