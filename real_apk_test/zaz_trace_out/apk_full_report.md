# Báo cáo apk-full (end-to-end)

- Thời gian: 2026-08-16 14:21:14
- Cây APK: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/zaz_trace_tree`
- Đầu vào patch: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/hook_input`
- Patch chọn: hook_remote_data_control, zaz_force, pro_unlock_vip

| Bước | Kết quả |
|------|---------|
| Plan (inventory+candidate) | 36.9s — 3 patch khớp |
| Apply | mã 0 trong 534.0s |
| Chuẩn hoá resource | 177 tên `$` |
| Build | mã 0 trong 162.0s |
| Zipalign | mã 0 |
| Ký | OK |
| Verify | mã 0 (Verified using v2 scheme (APK Signature Scheme v2): true, Verified using v3 scheme (APK Signature Scheme v3): true) |

## APK đầu ra

- Tệp: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/zaz_trace_out/zaz_trace_tree_patched_20260816-143511.apk`
- Kích thước: 68.27 MB

## Bài tập cải thiện
- Rebuild thành công — cần kiểm tra động tiếp — Ký APK, cài lên emulator/device, chạy logcat/mạng để đạt M2/M3.
