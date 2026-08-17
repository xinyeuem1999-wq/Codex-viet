# Báo cáo quét chi tiết — phương án bypass

- Cây APK: `/storage/emulated/0/Patch/patch1/_patchx/apk_trees/zaz`

## Lớp bảo vệ phát hiện

| Loại | Số lần | Tệp ví dụ |
|------|-------:|-----------|
| pinning | 27 | `smali/mq6.smali`, `smali/ya0.smali`, `smali_classes3/com/google/api/client/json/webtoken/JsonWebSignature.smali`, `smali_classes3/com/google/api/client/testing/json/webtoken/TestCertificates$CertData.smali`, `smali_classes3/com/google/api/client/util/SecurityUtils.smali` |
| emulator | 22 | `AndroidManifest.xml`, `smali/ai/onnxruntime/OnnxRuntime.smali`, `smali/com/firebase/ui/auth/ui/idp/AuthMethodPickerActivity.smali`, `smali/com/firebase/ui/auth/ui/idp/SingleSignInActivity.smali`, `smali/com/firebase/ui/auth/ui/idp/WelcomeBackIdpPrompt.smali` |
| safetynet | 4 | `smali/com/google/android/gms/fido/fido2/api/common/AuthenticatorAttestationResponse.smali`, `smali/com/google/android/gms/fido/fido2/api/common/PublicKeyCredentialCreationOptions.smali`, `smali_classes3/com/google/android/gms/internal/ads/zzbie.smali`, `smali_classes3/com/google/android/gms/internal/ads/zzbkd.smali` |
| root | 1 | `smali_classes3/e60.smali` |
| anti-debug | 1 | `smali_classes3/ab1.smali` |

## Patch đơn — điểm bypass, công cụ, tỷ lệ thành công

| Hạng | Patch | Điểm | Thành công | Khớp | Năng lực |
|------|-------|-----:|-----------:|-----:|----------|
| 1 | Debug_information_and_hack_signature | 1.000 | 27% | 63945 | bypass-license, integrity, trace |
| 2 | patch_bypass_sigcheck_with_reflection | 1.000 | 27% | 481 | bypass-license, integrity, shell |
| 3 | Debug_information | 0.925 | 24% | 63915 | trace |

### Debug_information_and_hack_signature — dự đoán 27%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Cách: Bật truy vết dữ liệu: chèn TRACE/API_LOG vào method mục tiêu để đọc tham số và phản hồi trước khi quyết định patch.
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`, `logcat`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `smali*/*.smali`: 30 khớp — `smali/ch3.smali`, `smali/com/adjust/sdk/DeviceInfo.smali`, `smali/com/google/android/gms/common/GooglePlayServicesUtilLight.smali`, `smali/com/google/android/gms/common/GoogleSignatureVerifier.smali`
- Khối 6 (MATCH_REPLACE) target `smali*/*.smali`: 63915 khớp — `smali/WordDetailsPopupWindow$show$3$1.smali`, `smali/a00.smali`, `smali/a02.smali`, `smali/a03.smali`

### patch_bypass_sigcheck_with_reflection — dự đoán 27%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Cách: Chèn khởi tạo mod qua INIT/HOOK_SCRIPT: chạy lệnh/script khi app mở để bơm biến hoặc gọi hàm nội bộ.
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `smali*/*`: 382 khớp — `smali/aj2.smali`, `smali/androidx/appcompat/app/AppCompatDelegateImpl.smali`, `smali/androidx/appcompat/app/AppCompatViewInflater$DeclaredOnClickListener.smali`, `smali/androidx/appcompat/view/SupportMenuInflater$InflatedOnMenuItemClickListener.smali`
- Khối 4 (MATCH_REPLACE) target `smali*/*.smali`: 99 khớp — `smali/a4b.smali`, `smali/androidx/credentials/playservices/controllers/BeginSignIn/ua.smali`, `smali/androidx/profileinstaller/ProfileInstallReceiver.smali`, `smali/as3.smali`

### Debug_information — dự đoán 24%

- Cách: Bật truy vết dữ liệu: chèn TRACE/API_LOG vào method mục tiêu để đọc tham số và phản hồi trước khi quyết định patch.
- Công cụ: `patchx apply`, `logcat`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `smali*/*.smali`: 63915 khớp — `smali/WordDetailsPopupWindow$show$3$1.smali`, `smali/a00.smali`, `smali/a02.smali`, `smali/a03.smali`

## Phương án triển khai đề xuất

- Phương án: Debug_information_and_hack_signature
- Tỷ lệ thành công dự đoán: 27%

1. Chuẩn bị cây APK (apk-prepare) hoặc dùng cây đã giải mã.
2. Áp patch: python3 patchx apply Debug_information_and_hack_signature <cây-apk>
3. Chuẩn hoá resource chứa `$`: python3 patchx_toolkit.py apk-fix-res
4. Build: apktool b <cây> -o out.apk --aapt <aapt2-thật>
5. Zipalign + ký: zipalign -f 4 && apksigner sign
6. Cài APK, xác minh động bằng logcat/Frida theo mục xác_minh.

Rủi ro:
- APK có dấu hiệu pinning (27 lần) — trừ ~15% điểm dự đoán; ưu tiên patch integrity/token xử lý lớp này.
- APK có dấu hiệu emulator (22 lần) — trừ ~8% điểm dự đoán; ưu tiên patch integrity/token xử lý lớp này.
- APK có dấu hiệu safetynet (4 lần) — trừ ~18% điểm dự đoán; ưu tiên patch integrity/token xử lý lớp này.
- APK có dấu hiệu root (1 lần) — trừ ~12% điểm dự đoán; ưu tiên patch integrity/token xử lý lớp này.