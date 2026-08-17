# Báo cáo apk-full (end-to-end)

- Thời gian: 2026-08-15 23:47:04
- Cây APK: `/storage/emulated/0/Patch/patch1/_patchx/apk_trees/KISS launcher_3.26.0`
- Đầu vào patch: `/storage/emulated/0/Patch/patch1/_patchx/upgraded`
- Patch chọn: Debug_information_and_hack_signature, patch_bypass_sigcheck_with_reflection, Debug_information

| Bước | Kết quả |
|------|---------|
| Plan (inventory+candidate) | 230.5s — 3 patch khớp |
| Apply | mã 0 trong 48.8s |
| Chuẩn hoá resource | 0 tên `$` |
| Build | mã 1 trong 11.9s |

## Bài tập cải thiện
- Smali do patch sinh ra không hợp lệ — Dùng smali_lib.alloc_temps và find_method_block trước khi chèn; bổ sung kiểm tra type và test rebuild tự động.
