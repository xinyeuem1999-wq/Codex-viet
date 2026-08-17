# Báo cáo apk-full (end-to-end)

- Thời gian: 2026-08-15 23:54:11
- Cây APK: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/kiss_tree_clean`
- Đầu vào patch: `/storage/emulated/0/Patch/patch1/_patchx/upgraded`
- Patch chọn: Debug_information_and_hack_signature, patch_bypass_sigcheck_with_reflection, Debug_information

| Bước | Kết quả |
|------|---------|
| Plan (inventory+candidate) | 225.7s — 3 patch khớp |
| Apply | mã 0 trong 39.0s |
| Chuẩn hoá resource | 0 tên `$` |
| Build | mã 0 trong 17.9s |
| Zipalign | mã 0 |
| Ký | OK |
| Verify | mã 0 (Verified using v1 scheme (JAR signing): true, Verified using v2 scheme (APK Signature Scheme v2): true, Verified using v3 scheme (APK Signature Scheme v3): true) |

## APK đầu ra

- Tệp: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/apk_full_v2/kiss_tree_clean_patched_20260815-235855.apk`
- Kích thước: 2.22 MB

## Bài tập cải thiện
- Rebuild thành công — cần kiểm tra động tiếp — Ký APK, cài lên emulator/device, chạy logcat/mạng để đạt M2/M3.
