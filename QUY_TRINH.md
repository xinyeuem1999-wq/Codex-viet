# Quy trình vận hành patchx — bản lưu đầy đủ

Mục tiêu: lần sau chỉ cần đọc tệp này + `NGU_CANH.md` là nắm rõ toàn bộ quy
trình, không cần lục lại lịch sử hội thoại.

## 1. Thư mục và dữ liệu quan trọng

- Bộ patch chuẩn hoá đang dùng: `_patchx/upgraded/` (60 zip, 0 lỗi).
- Bộ patch gốc: **đã xoá**; manifest tại
  `_patchx/backup/deleted_originals_20260814-155340.json`.
- Toolkit: `_patchx/patchx_toolkit.py`.
- Bản phân phối: `_patchx/dist/patchx-toolkit-*.zip`.
- Kết quả full pipeline: `_patchx/toolkit_out/`.
- APK thật để test: `_patchx/real_apk_test/app_tree` (477M), kết quả build:
  `_patchx/real_apk_test/app_bypass_signed.apk`.
- Nguồn hook điều khiển thu thập dữ liệu:
  `_patchx/hook_remote_data_control/`.

## 2. Các lệnh toolkit

```sh
cd "_patchx"

python3 patchx_toolkit.py doctor
python3 patchx_toolkit.py run
python3 patchx_toolkit.py run --quick
python3 patchx_toolkit.py package

python3 patchx_toolkit.py list --limit 80
python3 patchx_toolkit.py list --json danh_sach.json

python3 patchx_toolkit.py session \
  --select 'IsPremium,SignatureHack_arm64' \
  --tree real_apk_test/app_tree \
  --dry-run \
  --output real_apk_test/bypass_session

python3 patchx_toolkit.py apk-plan real_apk_test/app_tree \
  --output real_apk_test/bypass_plan --limit 10

python3 patchx_toolkit.py bench-scan real_apk_test/app_tree \
  --input upgraded --output real_apk_test/bench_477M_vN

python3 patchx_toolkit.py apk-full real_apk_test/app_tree \
  --input upgraded --top 3 --output real_apk_test/apk_full_out

python3 patchx_toolkit.py apk-runtime real_apk_test/app_bypass_signed.apk \
  --expect 'patchx' --forbid 'FATAL EXCEPTION' \
  --output real_apk_test/runtime_check

# Với máy ảo cloud (Redfinger/VMOS): lấy host:port từ client rồi:
python3 patchx_toolkit.py apk-runtime <APK> --connect 127.0.0.1:PORT \
  --output real_apk_test/runtime_cloud

python3 patchx_toolkit.py apk-test real_apk_test/p1_test.patch.txt \
  real_apk_test/app_tree --build \
  --aapt /data/data/com.termux/files/usr/bin/aapt2 \
  --output real_apk_test/improvements3

python3 patchx_toolkit.py apk-fix-res real_apk_test/app_tree \
  --output real_apk_test/resource_fix
```

## 3. Full pipeline `run`

Thứ tự: `selfcheck` → `test` → `scan` → `dupes` → `manifest` → `audit` →
`upgrade` → `optimize` → `combo --auto` → `simulate` → `report`.

Kết quả gần nhất: **12/12 bước thành công**; test **89/89**; simulate
**51 ĐẠT / 0 THẤT-BẠI / 9 BỎ-QUA / 0 LỖI** (60 patch, 85%).

## 4. Quy trình APK → APK bypass bằng code thật

1. Chuẩn bị cây APK:
   ```sh
   python3 patchx apk-prepare app.apk -o cây-apk
   ```
   Hoặc dùng cây đã giải mã sẵn `real_apk_test/app_tree`.
2. Áp patch thử:
   ```sh
   python3 patchx apply real_apk_test/p1_test.patch.txt real_apk_test/app_tree
   ```
3. Chuẩn hoá resource tên chứa `$`:
   ```sh
   python3 patchx_toolkit.py apk-fix-res real_apk_test/app_tree \
     --output real_apk_test/resource_fix
   ```
4. Build:
   ```sh
   apktool b real_apk_test/app_tree -o real_apk_test/app_bypass.apk \
     --aapt /data/data/com.termux/files/usr/bin/aapt2
   ```
5. Zipalign + ký:
   ```sh
   zipalign -f 4 real_apk_test/app_bypass.apk real_apk_test/app_bypass_aligned.apk
   apksigner sign --ks real_apk_test/patchx.keystore \
     --ks-pass pass:patchx123 --key-pass pass:patchx123 \
     --out real_apk_test/app_bypass_signed.apk real_apk_test/app_bypass_aligned.apk
   ```
6. Xác minh:
   ```sh
   apksigner verify --verbose real_apk_test/app_bypass_signed.apk
   ```

Kết quả: build thành công, chữ ký v2/v3 hợp lệ.

## 5. Lỗi đã gặp và cách xử lý

- **`zipalign` không có gói trong kho Termux main**: chạy
  `python3 patchx_toolkit.py install-deps` — toolkit tải prebuilt arm64 từ
  `rendiix/termux-zipalign`, kiểm tra sha256 rồi cài vào `$PREFIX/bin`.
- **aapt2 wrapper Termux**: `aapt2_*.tmp: Syntax error: "(" unexpected`.
  → Dùng `apktool b --aapt /data/data/com.termux/files/usr/bin/aapt2`.
- **apktool 3.x không có `--use-aapt1`**:
  → Dùng `--aapt <aapt2>`.
- **Resource tên `$`**: aapt2 báo `has invalid entry name`.
  → Chạy `apk-fix-res`, sau đó cập nhật tham chiếu `public.xml`/drawable.
- **`apk-plan` quét cây APK lớn bị chậm** (đã giải quyết Đợt A):
  → Dùng `bench-scan` (inventory `rg`/hash + cache theo hash cây + literal
    hint lọc regex): cây 553M quét **23.557s < 60s**. Với cây lớn vẫn nên
    dùng `roadmap` hoặc chọn patch mục tiêu thay vì coverage toàn bộ.

## 6. Trạng thái phát triển

- 6 khối hiện đại: hoàn tất.
- smali_lib: hoàn tất, engine đã dùng chung.
- session selector: hoàn tất.
- apk-plan / apk-test / apk-fix-res: hoàn tất.
- Rebuild APK thật: **đã thành công**.
- **Tối ưu quét APK lớn (Đợt A): đã đạt < 60s** — `bench-scan` cây 553M =
  **23.557s** (60 patch / 13.604 rule; khớp 6.870, lọc hint 5.980, mẫu 41);
  cơ chế literal hint + `rg -P` chống ReDoS + memo đếm + cache theo hash;
  hồi quy test **89/89**. Chi tiết: `TRANG_THAI_HIEN_TAI.md`.
- **`apk-full` end-to-end (Đợt B): hoàn tất** — plan → chọn top patch →
  apply → `apk-fix-res` → build → zipalign → sign → verify → báo cáo
  `apk_full_report.json/md`; nghiệm thu cây KISS sạch: APK ký v1/v2/v3 hợp lệ.
  Kèm sửa lỗi engine `ADD_FILES` EXTRACT lặp tiền tố `smali/smali`.
- **Runtime verify (Đợt C): lệnh `apk-runtime` hoàn tất** — tự đọc package/
  activity bằng `aapt2 dump badging`, `adb install -r`, mở app (am start/
  monkey), chờ, kiểm tra process + logcat (FATAL EXCEPTION), đánh giá M2/M3
  qua `--expect`/`--forbid`; tích hợp `apk-full --runtime`. Không có
  device/emulator → báo "thiếu môi trường" (hợp lệ, không lỗi) — nghiệm thu
  M2/M3 chờ kết nối thiết bị.
- **Máy ảo cloud (Redfinger/VMOS)**: `apk-runtime --connect HOST:PORT` kết
  nối trước khi verify; `--scan-local` tự quét cổng adb phổ biến trên
  127.0.0.1 (5555/5557/5559/5561/21503/26944/26945). Máy này không có
  `/dev/kvm` nên emulator Android không chạy trong Termux — dùng máy ảo
  cloud/thiết bị thứ hai/PC.

## 7. Việc tiếp theo nên làm

1. Cài APK đã ký lên emulator/device, chạy logcat xác minh runtime (M2/M3).
2. Bổ sung golden test cho rebuild APK thật (mẫu nhỏ).
