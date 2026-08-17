# Phương án bypass khả thi theo tỷ lệ

- Thời gian: 2026-08-16 07:49:55
- Cây APK: `/storage/emulated/0/Patch/patch1/_patchx/apk_trees/zaz`
- Đầu vào patch: `/storage/emulated/0/Patch/patch1/_patchx/upgraded`

## Patch đơn xếp theo điểm

| Hạng | Patch | Điểm | Bao phủ | Khớp | Năng lực |
|------|-------|-----:|--------:|-----:|----------|
| 1 | Debug_information_and_hack_signature | 1.000 | 100% | 63945 | bypass-license, integrity, trace |
| 2 | patch_bypass_sigcheck_with_reflection | 1.000 | 100% | 481 | bypass-license, integrity, shell |
| 3 | Debug_information | 0.925 | 100% | 63915 | trace |

## Combo bổ trợ xếp theo điểm

| Hạng | Patch 1 | Patch 2 | Điểm | Năng lực |
|------|---------|---------|-----:|----------|
| 1 | AUTH_VK_AND_FB | patch_bypass_sigcheck_with_reflection | 0.865 | bypass-license, integrity, shell |
| 2 | AUTH_VK_AND_FB | Debug_information_and_hack_signature | 0.840 | bypass-license, integrity, trace |
| 3 | AUTH_VK_AND_FB | DexExtractor | 0.795 | bypass-license, shell |