# Báo cáo mô phỏng toàn diện

- Tổng patch: 11
- ĐẠT: 11 | THẤT-BẠI: 0 | BỎ-QUA: 0 | LỖI: 0
- Tỷ lệ đạt: 100.0%
- Tổng thời gian: 1502.6 ms (trung bình 136.6 ms/patch)

| Patch | Quy tắc | Mẫu | Thay đổi | Lặp lại | Idempotent | ms | Trạng thái |
|-------|---------|-----|----------|---------|------------|----|------------|
| anti_debug_off | 2 | 2 | 2 | 0 | True | 74.6 | ĐẠT |
| anti_tamper_signature_off | 2 | 2 | 2 | 0 | True | 91.4 | ĐẠT |
| emulator_check_off | 1 | 1 | 1 | 0 | True | 59.8 | ĐẠT |
| emulator_fingerprint_off | 1 | 1 | 1 | 0 | True | 76.4 | ĐẠT |
| frida_detect_off | 3 | 3 | 3 | 0 | True | 181.4 | ĐẠT |
| iap_fake | 2 | 2 | 2 | 0 | True | 96.3 | ĐẠT |
| iap_purchase_state | 1 | 1 | 1 | 0 | True | 39.0 | ĐẠT |
| integrity_verdict_off | 1 | 1 | 1 | 0 | True | 34.4 | ĐẠT |
| root_check_off | 1 | 1 | 1 | 0 | True | 51.9 | ĐẠT |
| root_su_binary_off | 2 | 2 | 2 | 0 | True | 129.8 | ĐẠT |
| ssl_pinning_off | 2 | 2 | 2 | 0 | True | 110.2 | ĐẠT |
