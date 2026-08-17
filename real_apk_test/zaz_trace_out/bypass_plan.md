# Phương án bypass khả thi theo tỷ lệ

- Thời gian: 2026-08-16 14:21:51
- Cây APK: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/zaz_trace_tree`
- Đầu vào patch: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/hook_input`

## Patch đơn xếp theo điểm

| Hạng | Patch | Điểm | Bao phủ | Khớp | Năng lực |
|------|-------|-----:|--------:|-----:|----------|
| 1 | pro_unlock_vip | 0.830 | 100% | 3 | bypass-license |
| 2 | hook_remote_data_control | 0.425 | 25% | 3 | api, google, shell, trace |
| 3 | zaz_force | 0.240 | 0% | 0 | api |

## Combo bổ trợ xếp theo điểm

| Hạng | Patch 1 | Patch 2 | Điểm | Năng lực |
|------|---------|---------|-----:|----------|
| 1 | hook_remote_data_control | pro_unlock_vip | 0.677 | api, bypass-license, google, shell, trace |
| 2 | hook_remote_data_control | zaz_force | 0.383 | api, google, shell, trace |