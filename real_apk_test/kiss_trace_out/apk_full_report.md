# Báo cáo apk-full (end-to-end)

- Thời gian: 2026-08-16 13:33:16
- Cây APK: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/kiss_trace_tree`
- Đầu vào patch: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/hook_input`
- Patch chọn: hook_remote_data_control

| Bước | Kết quả |
|------|---------|
| Plan (inventory+candidate) | 1.2s — 1 patch khớp |
| Apply | mã 0 trong 18.7s |
| Chuẩn hoá resource | 0 tên `$` |
| Build | mã 1 trong 17.7s |

## Bài tập cải thiện
- Smali do patch sinh ra không hợp lệ — Dùng smali_lib.alloc_temps và find_method_block trước khi chèn; bổ sung kiểm tra type và test rebuild tự động.
- Nghi vấn sai số thanh ghi smali — Chuẩn hoá bump register qua smali_lib.smali_alloc_temps; thêm golden test cho method instance/static.
