# Báo cáo quét chi tiết — phương án bypass

- Cây APK: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/zaz_trace_tree`

## Lớp bảo vệ phát hiện

| Loại | Số lần | Tệp ví dụ |
|------|-------:|-----------|
| tamper | 94 | `smali/a4b.smali`, `smali/androidx/credentials/playservices/controllers/BeginSignIn/ua.smali`, `smali/androidx/profileinstaller/ProfileInstallReceiver.smali`, `smali/as3.smali`, `smali/ce7.smali` |
| pinning | 27 | `smali/mq6.smali`, `smali/ya0.smali`, `smali_classes3/com/google/api/client/json/webtoken/JsonWebSignature.smali`, `smali_classes3/com/google/api/client/testing/json/webtoken/TestCertificates$CertData.smali`, `smali_classes3/com/google/api/client/util/SecurityUtils.smali` |
| emulator | 22 | `AndroidManifest.xml`, `smali/ai/onnxruntime/OnnxRuntime.smali`, `smali/com/firebase/ui/auth/ui/idp/AuthMethodPickerActivity.smali`, `smali/com/firebase/ui/auth/ui/idp/SingleSignInActivity.smali`, `smali/com/firebase/ui/auth/ui/idp/WelcomeBackIdpPrompt.smali` |
| safetynet | 4 | `smali/com/google/android/gms/fido/fido2/api/common/AuthenticatorAttestationResponse.smali`, `smali/com/google/android/gms/fido/fido2/api/common/PublicKeyCredentialCreationOptions.smali`, `smali_classes3/com/google/android/gms/internal/ads/zzbie.smali`, `smali_classes3/com/google/android/gms/internal/ads/zzbkd.smali` |
| root | 1 | `smali_classes3/e60.smali` |
| frida | 1 | `unknown/mozilla/public-suffix-list.txt` |
| anti-debug | 1 | `smali_classes3/ab1.smali` |

## Patch đơn — điểm bypass, công cụ, tỷ lệ thành công

| Hạng | Patch | Điểm | Thành công | Khớp | Năng lực |
|------|-------|-----:|-----------:|-----:|----------|
| 1 | pro_unlock_vip | 0.830 | 0% | 3 | bypass-license |
| 2 | hook_remote_data_control | 0.425 | 0% | 3 | api, google, shell, trace |
| 3 | zaz_force | 0.240 | 0% | 0 | api |

### pro_unlock_vip — dự đoán 0%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `smali_classes4/com/zaz/account/uc.smali`: 1 khớp — `smali_classes4/com/zaz/account/uc.smali`
- Khối 4 (MATCH_REPLACE) target `smali_classes4/com/zaz/subscription/manager/ua.smali`: 1 khớp — `smali_classes4/com/zaz/subscription/manager/ua.smali`
- Khối 5 (MATCH_REPLACE) target `smali_classes4/com/zaz/subscription/manager/ua.smali`: 1 khớp — `smali_classes4/com/zaz/subscription/manager/ua.smali`

### hook_remote_data_control — dự đoán 0%

- Cách: Tìm API thật bằng log API_LOG/TRACE, sau đó thay domain/endpoint trong MATCH_REPLACE hoặc chặn tại class xử lý mạng.
- Cách: Bỏ kiểm tra Google Play Services/SafetyNet: gỡ hoặc bỏ qua khối attestation, thay bằng kết quả giả.
- Cách: Chèn khởi tạo mod qua INIT/HOOK_SCRIPT: chạy lệnh/script khi app mở để bơm biến hoặc gọi hàm nội bộ.
- Cách: Bật truy vết dữ liệu: chèn TRACE/API_LOG vào method mục tiêu để đọc tham số và phản hồi trước khi quyết định patch.
- Công cụ: `patchx apply`, `Frida`, `logcat`, `apktool`, `LSPosed`

Điểm bypass cụ thể:
- Khối 4 (MATCH_REPLACE) target `smali*/com/zaz/translate/ui/tool/ConfigKt.smali`: 1 khớp — `smali_classes5/com/zaz/translate/ui/tool/ConfigKt.smali`
- Khối 9 (MATCH_REPLACE) target `smali*/*.smali`: 2 khớp — `smali_classes4/com/zaz/translate/analysis/DataAnalysisHelperKt$logFirebaseEvent$1.smali`, `smali_classes4/com/zaz/translate/analysis/DataAnalysisHelperKt$logFirebaseEvent$2.smali`

Đề xuất tăng khả năng thành công:
- Khối 8 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 10 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 11 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 12 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 13 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 14 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK

### zaz_force — dự đoán 0%

- Cách: Tìm API thật bằng log API_LOG/TRACE, sau đó thay domain/endpoint trong MATCH_REPLACE hoặc chặn tại class xử lý mạng.
- Công cụ: `patchx apply`, `Frida`, `logcat`

## Combo bổ trợ

| Patch 1 | Patch 2 | Thành công | Bổ trợ |
|---------|---------|-----------:|--------|
| hook_remote_data_control | pro_unlock_vip | 2% | google→bypass-license, shell→bypass-license |
| hook_remote_data_control | zaz_force | 2% | shell→api, trace→api |

## Phương án triển khai đề xuất

- Phương án: pro_unlock_vip
- Tỷ lệ thành công dự đoán: 0%

1. Chuẩn bị cây APK (apk-prepare) hoặc dùng cây đã giải mã.
2. Áp patch: python3 patchx apply pro_unlock_vip <cây-apk>
3. Chuẩn hoá resource chứa `$`: python3 patchx_toolkit.py apk-fix-res
4. Build: apktool b <cây> -o out.apk --aapt <aapt2-thật>
5. Zipalign + ký: zipalign -f 4 && apksigner sign
6. Cài APK, xác minh động bằng logcat/Frida theo mục xác_minh.

Rủi ro:
- APK có dấu hiệu tamper (94 lần) — trừ ~8% điểm dự đoán; ưu tiên patch integrity/token xử lý lớp này.
- APK có dấu hiệu pinning (27 lần) — trừ ~15% điểm dự đoán; ưu tiên patch integrity/token xử lý lớp này.
- APK có dấu hiệu emulator (22 lần) — trừ ~8% điểm dự đoán; ưu tiên patch integrity/token xử lý lớp này.
- APK có dấu hiệu safetynet (4 lần) — trừ ~18% điểm dự đoán; ưu tiên patch integrity/token xử lý lớp này.