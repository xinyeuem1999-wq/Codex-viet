# Báo cáo apk-full (end-to-end)

- Thời gian: 2026-08-16 02:11:15
- Cây APK: `/storage/emulated/0/Patch/patch1/_patchx/apk_trees/KISS launcher_3.26.0`
- Đầu vào patch: `/storage/emulated/0/Patch/patch1/_patchx/upgraded`
- Patch chọn: Debug_information_and_hack_signature, patch_bypass_sigcheck_with_reflection, Debug_information

| Bước | Kết quả |
|------|---------|
| Plan (inventory+candidate) | 290.7s — 3 patch khớp |
| Apply | mã 0 trong 35.2s |
| Chuẩn hoá resource | 0 tên `$` |
| Build | mã 0 trong 16.4s |
| Zipalign | mã 0 |
| Ký | OK |
| Verify | mã 0 (Verified using v1 scheme (JAR signing): true, Verified using v2 scheme (APK Signature Scheme v2): true, Verified using v3 scheme (APK Signature Scheme v3): true) |

## APK đầu ra

- Tệp: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/apk_full_v3/KISS launcher_3.26.0_patched_20260816-021659.apk`
- Kích thước: 2.22 MB

## Bài tập cải thiện
- Rebuild thành công — cần kiểm tra động tiếp — Ký APK, cài lên emulator/device, chạy logcat/mạng để đạt M2/M3.
