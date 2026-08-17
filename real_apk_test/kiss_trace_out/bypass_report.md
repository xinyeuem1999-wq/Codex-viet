# Báo cáo quét chi tiết — phương án bypass

- Cây APK: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/kiss_trace_tree`

## Lớp bảo vệ phát hiện

| Loại | Số lần | Tệp ví dụ |
|------|-------:|-----------|
| tamper | 7 | `smali/androidx/collection/internal/Lock.smali`, `smali/androidx/core/provider/FontProvider.smali`, `smali/androidx/emoji2/text/DefaultEmojiCompatConfig$DefaultEmojiCompatConfigHelper_API28.smali`, `smali/androidx/profileinstaller/Encoding.smali`, `smali/androidx/profileinstaller/ProfileInstallReceiver.smali` |

## Patch đơn — điểm bypass, công cụ, tỷ lệ thành công

| Hạng | Patch | Điểm | Thành công | Khớp | Năng lực |
|------|-------|-----:|-----------:|-----:|----------|
| 1 | hook_remote_data_control | 0.270 | 4% | 0 | api, google, shell, trace |

### hook_remote_data_control — dự đoán 4%

- Cách: Tìm API thật bằng log API_LOG/TRACE, sau đó thay domain/endpoint trong MATCH_REPLACE hoặc chặn tại class xử lý mạng.
- Cách: Bỏ kiểm tra Google Play Services/SafetyNet: gỡ hoặc bỏ qua khối attestation, thay bằng kết quả giả.
- Cách: Chèn khởi tạo mod qua INIT/HOOK_SCRIPT: chạy lệnh/script khi app mở để bơm biến hoặc gọi hàm nội bộ.
- Cách: Bật truy vết dữ liệu: chèn TRACE/API_LOG vào method mục tiêu để đọc tham số và phản hồi trước khi quyết định patch.
- Công cụ: `patchx apply`, `Frida`, `logcat`, `apktool`, `LSPosed`

Đề xuất tăng khả năng thành công:
- Khối 4 trượt target smali*/com/zaz/translate/ui/tool/ConfigKt.smali — cập nhật TARGET theo class-link thật của APK
- Khối 8 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 9 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 10 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 11 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 12 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK

## Phương án triển khai đề xuất

- Phương án: hook_remote_data_control
- Tỷ lệ thành công dự đoán: 4%

1. Chuẩn bị cây APK (apk-prepare) hoặc dùng cây đã giải mã.
2. Áp patch: python3 patchx apply hook_remote_data_control <cây-apk>
3. Chuẩn hoá resource chứa `$`: python3 patchx_toolkit.py apk-fix-res
4. Build: apktool b <cây> -o out.apk --aapt <aapt2-thật>
5. Zipalign + ký: zipalign -f 4 && apksigner sign
6. Cài APK, xác minh động bằng logcat/Frida theo mục xác_minh.

Rủi ro:
- APK có dấu hiệu tamper (7 lần) — trừ ~8% điểm dự đoán; ưu tiên patch integrity/token xử lý lớp này.

Đề xuất nâng tỷ lệ:
- Khối 4 trượt target smali*/com/zaz/translate/ui/tool/ConfigKt.smali — cập nhật TARGET theo class-link thật của APK
- Khối 8 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 9 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 10 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 11 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 12 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK