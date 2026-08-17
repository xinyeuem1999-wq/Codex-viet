# Báo cáo quét chi tiết — phương án bypass

- Cây APK: `/storage/emulated/0/Patch/patch1/_patchx/apk_trees/ApkToolPatcher v5.0`

## Lớp bảo vệ phát hiện

| Loại | Số lần | Tệp ví dụ |
|------|-------:|-----------|
| tamper | 7 | `assets/signatureHack/cc/binmt/signature/PmsHookApplication.smali`, `smali/androidx/fragment/app/FragmentManagеrImpl.smali`, `smali/jp/sblo/pandora/aGrep/OptionActivity.smali`, `smali/org/セト.smali`, `smali/ru/svolf/rxmanager/AppsDetailsFragment.smali` |
| emulator | 6 | `smali/apk/tool/patcher/filesystem/private.smali`, `smali/org/アザレ.smali`, `smali/org/アヮオ.smali`, `smali/org/ヶト.smali`, `smali_classes2/org/アズワ.smali` |
| signature | 1 | `res/values/strings.xml` |
| anti-debug | 1 | `smali_classes2/org/アホゾ$private.smali` |

## Patch đơn — điểm bypass, công cụ, tỷ lệ thành công

| Hạng | Patch | Điểm | Thành công | Khớp | Năng lực |
|------|-------|-----:|-----------:|-----:|----------|
| 1 | DexExtractor | 0.910 | 41% | 71 | shell |
| 2 | patch_bypass_sigcheck_with_reflection | 0.750 | 14% | 71 | bypass-license, integrity, shell |
| 3 | Unicode text | 0.715 | 34% | 934 |  |
| 4 | License_hack | 0.640 | 1% | 9 | bypass-license, installer, integrity |
| 5 | New. Removing the analytic tag, etc.. Inok_ZP 12.04.18 | 0.637 | 3% | 2723982 | api, google |
| 6 | License_hack(Amazon) | 0.630 | 0% | 8 | bypass-license, integrity |
| 7 | translate_obfuscation | 0.615 | 22% | 1242 |  |
| 8 | 3. GooglePlayServices by Edik1d | 0.615 | 0% | 8 | google, integrity |
| 9 | Debug_information_and_hack_signature | 0.560 | 0% | 1 | anti-debug, bypass-license, integrity, trace |
| 10 | patch_bypass_sigcheck | 0.560 | 0% | 1 | bypass-license, google, integrity |
| 11 | Password_login_english | 0.535 | 0% | 2613309 | shell |
| 12 | GooglePlayServices | 0.532 | 0% | 8 | google, integrity |
| 13 | Permission_location | 0.510 | 0% | 3 | anonymity, permission |
| 14 | Language substitution | 0.501 | 9% | 763 |  |
| 15 | Only Ru | 0.501 | 9% | 763 |  |
| 16 | License_hack&htc v2 | 0.494 | 0% | 10 | bypass-license, installer, integrity |
| 17 | BinSignatureHack_with_htc | 0.487 | 0% | 2 | bypass-license, integrity |
| 18 | Permission_readSMS | 0.480 | 0% | 3 | ads, permission |
| 19 | Bin_sig&installer_fix[Amazon] | 0.448 | 0% | 2 | installer, integrity |
| 20 | Bin_sig&installer_fix[Google] | 0.448 | 0% | 2 | google, installer, integrity |
| 21 | Permission_calendar | 0.435 | 0% | 3 | permission |
| 22 | Permission_camera | 0.435 | 0% | 3 | permission |
| 23 | Permission_phone | 0.435 | 0% | 3 | permission |
| 24 | Permission_readContact | 0.435 | 0% | 3 | permission |
| 25 | SignatureHack_arm64 | 0.431 | 0% | 2 | bypass-license, frida-hide, integrity, shell |
| 26 | SignatureHack_armv7 | 0.431 | 0% | 2 | bypass-license, frida-hide, integrity, shell |
| 27 | Dictionary+ru+uk+2 | 0.309 | 0% | 313 |  |
| 28 | 4. DisableBillingService by VERGIL777 | 0.300 | 0% | 0 | bypass-license, purchase |
| 29 | AUTH_VK_AND_FB | 0.300 | 0% | 0 | bypass-license |
| 30 | Activator | 0.300 | 0% | 0 | bypass-license |

### DexExtractor — dự đoán 41%

- Cách: Chèn khởi tạo mod qua INIT/HOOK_SCRIPT: chạy lệnh/script khi app mở để bơm biến hoặc gọi hàm nội bộ.
- Công cụ: `patchx apply`, `apktool`, `Frida`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `smali*/*`: 71 khớp — `smali/androidx/appcompat/widget/SearchView$if.smali`, `smali/androidx/appcompat/widget/const.smali`, `smali/androidx/appcompat/widget/デボ.smali`, `smali/androidx/appcompat/widget/ヹゲ.smali`

Đề xuất tăng khả năng thành công:
- Chuỗi khối 3 còn xuất hiện ngoài target (assets/signatureHack/cc/binmt/signature/PmsHookApplication.smali, 3 lần) — cân nhắc bổ sung class-link

### patch_bypass_sigcheck_with_reflection — dự đoán 14%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Cách: Chèn khởi tạo mod qua INIT/HOOK_SCRIPT: chạy lệnh/script khi app mở để bơm biến hoặc gọi hàm nội bộ.
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `smali*/*`: 71 khớp — `smali/androidx/appcompat/widget/SearchView$if.smali`, `smali/androidx/appcompat/widget/const.smali`, `smali/androidx/appcompat/widget/デボ.smali`, `smali/androidx/appcompat/widget/ヹゲ.smali`

Đề xuất tăng khả năng thành công:
- Chuỗi khối 3 còn xuất hiện ngoài target (assets/signatureHack/cc/binmt/signature/PmsHookApplication.smali, 3 lần) — cân nhắc bổ sung class-link
- Khối 4 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK

### Unicode text — dự đoán 34%

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `smali/*.smali`: 15 khớp — `smali/org/アザレ.smali`, `smali/org/ゲワ.smali`, `smali/org/サプ.smali`, `smali/org/ゼメ.smali`
- Khối 4 (MATCH_REPLACE) target `smali/*.smali`: 12 khớp — `smali/org/アザレ.smali`, `smali/org/ゲワ.smali`, `smali/org/サプ.smali`, `smali/org/ゼメ.smali`
- Khối 5 (MATCH_REPLACE) target `smali/*.smali`: 14 khớp — `smali/org/アザレ.smali`, `smali/org/ゲワ.smali`, `smali/org/サプ.smali`, `smali/org/ゼメ.smali`
- Khối 6 (MATCH_REPLACE) target `smali/*.smali`: 13 khớp — `smali/org/アザレ.smali`, `smali/org/ゲワ.smali`, `smali/org/サプ.smali`, `smali/org/ゼメ.smali`
- Khối 7 (MATCH_REPLACE) target `smali/*.smali`: 15 khớp — `smali/org/アザレ.smali`, `smali/org/ゲワ.smali`, `smali/org/サプ.smali`, `smali/org/ゼメ.smali`
- Khối 8 (MATCH_REPLACE) target `smali/*.smali`: 16 khớp — `smali/org/アザレ.smali`, `smali/org/ゲワ.smali`, `smali/org/サプ.smali`, `smali/org/ゼメ.smali`
- Khối 9 (MATCH_REPLACE) target `smali/*.smali`: 13 khớp — `smali/org/アザレ.smali`, `smali/org/ゲワ.smali`, `smali/org/サプ.smali`, `smali/org/ゼメ.smali`
- Khối 10 (MATCH_REPLACE) target `smali/*.smali`: 10 khớp — `smali/org/アザレ.smali`, `smali/org/ゲワ.smali`, `smali/org/サプ.smali`, `smali/org/ゼメ.smali`

Đề xuất tăng khả năng thành công:
- Chuỗi khối 3 còn xuất hiện ngoài target (smali_classes2/org/ヒオ.smali, 2 lần) — cân nhắc bổ sung class-link
- Chuỗi khối 4 còn xuất hiện ngoài target (smali_classes2/org/ヒオ.smali, 2 lần) — cân nhắc bổ sung class-link
- Chuỗi khối 5 còn xuất hiện ngoài target (smali_classes2/org/ヒオ.smali, 2 lần) — cân nhắc bổ sung class-link
- Chuỗi khối 6 còn xuất hiện ngoài target (smali_classes2/org/ヒオ.smali, 2 lần) — cân nhắc bổ sung class-link
- Chuỗi khối 7 còn xuất hiện ngoài target (smali_classes2/org/ヒオ.smali, 2 lần) — cân nhắc bổ sung class-link
- Chuỗi khối 8 còn xuất hiện ngoài target (smali_classes2/org/シプ.smali, 1 lần) — cân nhắc bổ sung class-link

### License_hack — dự đoán 1%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Cách: Bỏ kiểm tra nguồn cài đặt: sửa luồng kiểm tra installer (getInstallerPackageName) trả về giá trị hợp lệ.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`

Điểm bypass cụ thể:
- Khối 4 (MATCH_REPLACE) target `smali*/*.smali`: 8 khớp — `smali/org/アズピ.smali`, `smali/org/ィゾケ.smali`, `smali/org/ウィ.smali`, `smali_classes2/org/アオロ.smali`
- Khối 6 (MATCH_REPLACE) target `smali*/*.smali`: 1 khớp — `smali_classes2/org/ヲモ.smali`

Đề xuất tăng khả năng thành công:
- Khối 3 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 5 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK

### New. Removing the analytic tag, etc.. Inok_ZP 12.04.18 — dự đoán 3%

- Cách: Tìm API thật bằng log API_LOG/TRACE, sau đó thay domain/endpoint trong MATCH_REPLACE hoặc chặn tại class xử lý mạng.
- Cách: Bỏ kiểm tra Google Play Services/SafetyNet: gỡ hoặc bỏ qua khối attestation, thay bằng kết quả giả.
- Công cụ: `patchx apply`, `Frida`, `logcat`, `apktool`, `LSPosed`

Điểm bypass cụ thể:
- Khối 1 (MATCH_REPLACE) target `smali*/*.smali`: 2723982 khớp — `smali/android/support/design/widget/TabLayout$break.smali`, `smali/android/support/design/widget/TabLayout$catch.smali`, `smali/android/support/design/widget/TabLayout$class.smali`, `smali/android/support/design/widget/TabLayout$instanceof.smali`

Đề xuất tăng khả năng thành công:
- Khối 2 trượt target AndroidManifest.xml — cập nhật TARGET theo class-link thật của APK
- Khối 3 trượt target AndroidManifest.xml — cập nhật TARGET theo class-link thật của APK

### License_hack(Amazon) — dự đoán 0%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `smali*/*.smali`: 8 khớp — `smali/org/アズピ.smali`, `smali/org/ィゾケ.smali`, `smali/org/ウィ.smali`, `smali_classes2/org/アオロ.smali`

Đề xuất tăng khả năng thành công:
- Khối 4 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK

### translate_obfuscation — dự đoán 22%

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `res/*`: 190 khớp — `res/drawable-anydpi/design_ic_visibility.xml`, `res/drawable/$avd_hide_password__0.xml`, `res/drawable/$avd_hide_password__1.xml`, `res/drawable/$avd_show_password__0.xml`
- Khối 4 (MATCH_REPLACE) target `res/values*/strings.xml`: 681 khớp — `res/values-ru/strings.xml`, `res/values/strings.xml`
- Khối 5 (MATCH_REPLACE) target `res/values/public.xml`: 370 khớp — `res/values/public.xml`
- Khối 6 (MATCH_GOTO) target `AndroidManifest.xml`: 1 khớp — `AndroidManifest.xml`

Đề xuất tăng khả năng thành công:
- Chuỗi khối 3 còn xuất hiện ngoài target (smali/org/アドヤ.smali, 1 lần) — cân nhắc bổ sung class-link
- Khối 8 trượt target AndroidManifest.xml — cập nhật TARGET theo class-link thật của APK

### 3. GooglePlayServices by Edik1d — dự đoán 0%

- Cách: Bỏ kiểm tra Google Play Services/SafetyNet: gỡ hoặc bỏ qua khối attestation, thay bằng kết quả giả.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Công cụ: `patchx apply`, `apktool`, `LSPosed`, `apksigner`

Điểm bypass cụ thể:
- Khối 1 (MATCH_REPLACE) target `smali*/*.smali`: 8 khớp — `smali/org/アズピ.smali`, `smali/org/ィゾケ.smali`, `smali/org/ウィ.smali`, `smali_classes2/org/アオロ.smali`

Đề xuất tăng khả năng thành công:
- Khối 0 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK

### Debug_information_and_hack_signature — dự đoán 0%

- Cách: Chống phát hiện gỡ lỗi: gán kết quả isDebuggerConnected về false, xoá kiểm tra TracerPid bằng MATCH_REPLACE/SET_BOOL.
- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Cách: Bật truy vết dữ liệu: chèn TRACE/API_LOG vào method mục tiêu để đọc tham số và phản hồi trước khi quyết định patch.
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`, `logcat`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `smali*/*.smali`: 1 khớp — `smali_classes2/org/アヅハ.smali`

Đề xuất tăng khả năng thành công:
- Chuỗi khối 3 còn xuất hiện ngoài target (assets/signatureHack/cc/binmt/signature/PmsHookApplication.smali, 2 lần) — cân nhắc bổ sung class-link
- Khối 6 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK

### patch_bypass_sigcheck — dự đoán 0%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Cách: Bỏ kiểm tra Google Play Services/SafetyNet: gỡ hoặc bỏ qua khối attestation, thay bằng kết quả giả.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `smali*/*.smali`: 1 khớp — `smali_classes2/org/アヅハ.smali`

Đề xuất tăng khả năng thành công:
- Chuỗi khối 3 còn xuất hiện ngoài target (assets/signatureHack/cc/binmt/signature/PmsHookApplication.smali, 2 lần) — cân nhắc bổ sung class-link
- Khối 6 trượt target smali*/*smali — cập nhật TARGET theo class-link thật của APK

### Password_login_english — dự đoán 0%

- Cách: Chèn khởi tạo mod qua INIT/HOOK_SCRIPT: chạy lệnh/script khi app mở để bơm biến hoặc gọi hàm nội bộ.
- Công cụ: `patchx apply`, `apktool`, `Frida`

Điểm bypass cụ thể:
- Khối 3 (MATCH_GOTO) target `smali*/*.smali`: 2613301 khớp — `smali/android/support/design/widget/TabLayout$break.smali`, `smali/android/support/design/widget/TabLayout$catch.smali`, `smali/android/support/design/widget/TabLayout$class.smali`, `smali/android/support/design/widget/TabLayout$instanceof.smali`
- Khối 16 (MATCH_REPLACE) target `AndroidManifest.xml`: 4 khớp — `AndroidManifest.xml`
- Khối 18 (MATCH_REPLACE) target `AndroidManifest.xml`: 4 khớp — `AndroidManifest.xml`

Đề xuất tăng khả năng thành công:
- Khối 5 trượt target AndroidManifest.xml — cập nhật TARGET theo class-link thật của APK
- Khối 6 trượt target AndroidManifest.xml — cập nhật TARGET theo class-link thật của APK
- Khối 8 trượt target AndroidManifest.xml — cập nhật TARGET theo class-link thật của APK
- Khối 10 trượt target AndroidManifest.xml — cập nhật TARGET theo class-link thật của APK
- Khối 11 trượt target AndroidManifest.xml — cập nhật TARGET theo class-link thật của APK
- Khối 13 trượt target AndroidManifest.xml — cập nhật TARGET theo class-link thật của APK

### GooglePlayServices — dự đoán 0%

- Cách: Bỏ kiểm tra Google Play Services/SafetyNet: gỡ hoặc bỏ qua khối attestation, thay bằng kết quả giả.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Công cụ: `patchx apply`, `apktool`, `LSPosed`, `apksigner`

Điểm bypass cụ thể:
- Khối 5 (MATCH_REPLACE) target `smali*/*.smali`: 8 khớp — `smali/org/アズピ.smali`, `smali/org/ィゾケ.smali`, `smali/org/ウィ.smali`, `smali_classes2/org/アオロ.smali`

Đề xuất tăng khả năng thành công:
- Khối 3 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 4 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK

### Permission_location — dự đoán 0%

- Cách: Ẩn danh: vô hiệu hoá thu thập định danh (analytics), thay chuỗi identifiers bằng giá trị giả.
- Cách: Điều chỉnh quyền: sửa AndroidManifest.xml (thêm/bớt quyền, debuggable, backup).
- Công cụ: `patchx apply`, `apktool`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `AndroidManifest.xml`: 1 khớp — `AndroidManifest.xml`
- Khối 5 (MATCH_REPLACE) target `[LAUNCHER_ACTIVITIES]`: 1 khớp — `smali/apk/tool/patcher/ui/modules/main/MainActivity.smali`
- Khối 6 (MATCH_ASSIGN) target `[LAUNCHER_ACTIVITIES]`: 1 khớp — `smali/apk/tool/patcher/ui/modules/main/MainActivity.smali`

Đề xuất tăng khả năng thành công:
- Chuỗi khối 3 còn xuất hiện ngoài target (smali/org/アェレ.smali, 4 lần) — cân nhắc bổ sung class-link
- Khối 4 trượt target [LAUNCHER_ACTIVITIES] — cập nhật TARGET theo class-link thật của APK
- Khối 7 trượt target [LAUNCHER_ACTIVITIES] — cập nhật TARGET theo class-link thật của APK

### Language substitution — dự đoán 9%

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `res/values-ru/strings.xml`: 328 khớp — `res/values-ru/strings.xml`
- Khối 4 (MATCH_ASSIGN) target `res/values-ru/strings.xml`: 1 khớp — `res/values-ru/strings.xml`
- Khối 5 (MATCH_REPLACE) target `res/values/strings.xml`: 433 khớp — `res/values/strings.xml`
- Khối 6 (MATCH_REPLACE) target `res/values/strings.xml`: 1 khớp — `res/values/strings.xml`

Đề xuất tăng khả năng thành công:
- Chuỗi khối 4 còn xuất hiện ngoài target (res/values-h360dp-land/dimens.xml, 1 lần) — cân nhắc bổ sung class-link
- Chuỗi khối 6 còn xuất hiện ngoài target (res/values-h360dp-land/dimens.xml, 1 lần) — cân nhắc bổ sung class-link
- Khối 7 trượt target res/values/strings.xml — cập nhật TARGET theo class-link thật của APK
- Khối 8 trượt target res/values-ru/strings.xml — cập nhật TARGET theo class-link thật của APK
- Khối 9 trượt target res/values/strings.xml — cập nhật TARGET theo class-link thật của APK

### Only Ru — dự đoán 9%

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `res/values-ru/strings.xml`: 328 khớp — `res/values-ru/strings.xml`
- Khối 4 (MATCH_ASSIGN) target `res/values-ru/strings.xml`: 1 khớp — `res/values-ru/strings.xml`
- Khối 5 (MATCH_REPLACE) target `res/values/strings.xml`: 433 khớp — `res/values/strings.xml`
- Khối 6 (MATCH_REPLACE) target `res/values/strings.xml`: 1 khớp — `res/values/strings.xml`

Đề xuất tăng khả năng thành công:
- Chuỗi khối 4 còn xuất hiện ngoài target (res/values-h360dp-land/dimens.xml, 1 lần) — cân nhắc bổ sung class-link
- Chuỗi khối 6 còn xuất hiện ngoài target (res/values-h360dp-land/dimens.xml, 1 lần) — cân nhắc bổ sung class-link
- Khối 7 trượt target res/values/strings.xml — cập nhật TARGET theo class-link thật của APK
- Khối 8 trượt target res/values-ru/strings.xml — cập nhật TARGET theo class-link thật của APK
- Khối 9 trượt target res/values/strings.xml — cập nhật TARGET theo class-link thật của APK

### License_hack&htc v2 — dự đoán 0%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Cách: Bỏ kiểm tra nguồn cài đặt: sửa luồng kiểm tra installer (getInstallerPackageName) trả về giá trị hợp lệ.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `smali*/*.smali`: 8 khớp — `smali/org/アズピ.smali`, `smali/org/ィゾケ.smali`, `smali/org/ウィ.smali`, `smali_classes2/org/アオロ.smali`
- Khối 5 (MATCH_REPLACE) target `smali*/*.smali`: 1 khớp — `smali_classes2/org/ヲモ.smali`
- Khối 10 (MATCH_ASSIGN) target `AndroidManifest.xml`: 1 khớp — `AndroidManifest.xml`

Đề xuất tăng khả năng thành công:
- Khối 4 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 6 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 7 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 8 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 11 trượt target smali/com/android/vending/licensing/htc600.smali — cập nhật TARGET theo class-link thật của APK
- Khối 12 trượt target AndroidManifest.xml — cập nhật TARGET theo class-link thật của APK

### BinSignatureHack_with_htc — dự đoán 0%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`

Điểm bypass cụ thể:
- Khối 5 (MATCH_REPLACE) target `AndroidManifest.xml`: 1 khớp — `AndroidManifest.xml`
- Khối 7 (MATCH_REPLACE) target `AndroidManifest.xml`: 1 khớp — `AndroidManifest.xml`

Đề xuất tăng khả năng thành công:
- Khối 4 trượt target AndroidManifest.xml — cập nhật TARGET theo class-link thật của APK
- Chuỗi khối 5 còn xuất hiện ngoài target (smali/org/アェレ.smali, 1 lần) — cân nhắc bổ sung class-link
- Khối 8 trượt target [APPLICATION] — cập nhật TARGET theo class-link thật của APK
- Khối 9 trượt target [APPLICATION] — cập nhật TARGET theo class-link thật của APK
- Khối 10 trượt target smali/cc/binmt/signature/PmsHookApplication.smali — cập nhật TARGET theo class-link thật của APK

### Permission_readSMS — dự đoán 0%

- Cách: Chặn quảng cáo: thay URL ad network bằng chuỗi rỗng hoặc bỏ qua khối hiển thị quảng cáo.
- Cách: Điều chỉnh quyền: sửa AndroidManifest.xml (thêm/bớt quyền, debuggable, backup).
- Công cụ: `patchx apply`, `apktool`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `AndroidManifest.xml`: 1 khớp — `AndroidManifest.xml`
- Khối 5 (MATCH_REPLACE) target `[LAUNCHER_ACTIVITIES]`: 1 khớp — `smali/apk/tool/patcher/ui/modules/main/MainActivity.smali`
- Khối 6 (MATCH_ASSIGN) target `[LAUNCHER_ACTIVITIES]`: 1 khớp — `smali/apk/tool/patcher/ui/modules/main/MainActivity.smali`

Đề xuất tăng khả năng thành công:
- Chuỗi khối 3 còn xuất hiện ngoài target (smali/org/アェレ.smali, 4 lần) — cân nhắc bổ sung class-link
- Khối 4 trượt target [LAUNCHER_ACTIVITIES] — cập nhật TARGET theo class-link thật của APK
- Khối 7 trượt target [LAUNCHER_ACTIVITIES] — cập nhật TARGET theo class-link thật của APK

### Bin_sig&installer_fix[Amazon] — dự đoán 0%

- Cách: Bỏ kiểm tra nguồn cài đặt: sửa luồng kiểm tra installer (getInstallerPackageName) trả về giá trị hợp lệ.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Công cụ: `patchx apply`, `apktool`, `apksigner`

Điểm bypass cụ thể:
- Khối 6 (MATCH_REPLACE) target `AndroidManifest.xml`: 1 khớp — `AndroidManifest.xml`
- Khối 8 (MATCH_REPLACE) target `AndroidManifest.xml`: 1 khớp — `AndroidManifest.xml`

Đề xuất tăng khả năng thành công:
- Khối 4 trượt target smali/cc/binmt/signature/PmsHookApplication.smali — cập nhật TARGET theo class-link thật của APK
- Khối 5 trượt target AndroidManifest.xml — cập nhật TARGET theo class-link thật của APK
- Chuỗi khối 6 còn xuất hiện ngoài target (smali/org/アェレ.smali, 1 lần) — cân nhắc bổ sung class-link
- Khối 9 trượt target [APPLICATION] — cập nhật TARGET theo class-link thật của APK
- Khối 10 trượt target [APPLICATION] — cập nhật TARGET theo class-link thật của APK
- Khối 11 trượt target smali/cc/binmt/signature/PmsHookApplication.smali — cập nhật TARGET theo class-link thật của APK

### Bin_sig&installer_fix[Google] — dự đoán 0%

- Cách: Bỏ kiểm tra Google Play Services/SafetyNet: gỡ hoặc bỏ qua khối attestation, thay bằng kết quả giả.
- Cách: Bỏ kiểm tra nguồn cài đặt: sửa luồng kiểm tra installer (getInstallerPackageName) trả về giá trị hợp lệ.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Công cụ: `patchx apply`, `apktool`, `LSPosed`, `apksigner`

Điểm bypass cụ thể:
- Khối 6 (MATCH_REPLACE) target `AndroidManifest.xml`: 1 khớp — `AndroidManifest.xml`
- Khối 8 (MATCH_REPLACE) target `AndroidManifest.xml`: 1 khớp — `AndroidManifest.xml`

Đề xuất tăng khả năng thành công:
- Khối 4 trượt target smali/cc/binmt/signature/PmsHookApplication.smali — cập nhật TARGET theo class-link thật của APK
- Khối 5 trượt target AndroidManifest.xml — cập nhật TARGET theo class-link thật của APK
- Chuỗi khối 6 còn xuất hiện ngoài target (smali/org/アェレ.smali, 1 lần) — cân nhắc bổ sung class-link
- Khối 9 trượt target [APPLICATION] — cập nhật TARGET theo class-link thật của APK
- Khối 10 trượt target [APPLICATION] — cập nhật TARGET theo class-link thật của APK
- Khối 11 trượt target smali/cc/binmt/signature/PmsHookApplication.smali — cập nhật TARGET theo class-link thật của APK

### Permission_calendar — dự đoán 0%

- Cách: Điều chỉnh quyền: sửa AndroidManifest.xml (thêm/bớt quyền, debuggable, backup).
- Công cụ: `patchx apply`, `apktool`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `AndroidManifest.xml`: 1 khớp — `AndroidManifest.xml`
- Khối 5 (MATCH_REPLACE) target `[LAUNCHER_ACTIVITIES]`: 1 khớp — `smali/apk/tool/patcher/ui/modules/main/MainActivity.smali`
- Khối 6 (MATCH_ASSIGN) target `[LAUNCHER_ACTIVITIES]`: 1 khớp — `smali/apk/tool/patcher/ui/modules/main/MainActivity.smali`

Đề xuất tăng khả năng thành công:
- Chuỗi khối 3 còn xuất hiện ngoài target (smali/org/アェレ.smali, 4 lần) — cân nhắc bổ sung class-link
- Khối 4 trượt target [LAUNCHER_ACTIVITIES] — cập nhật TARGET theo class-link thật của APK
- Khối 7 trượt target [LAUNCHER_ACTIVITIES] — cập nhật TARGET theo class-link thật của APK

### Permission_camera — dự đoán 0%

- Cách: Điều chỉnh quyền: sửa AndroidManifest.xml (thêm/bớt quyền, debuggable, backup).
- Công cụ: `patchx apply`, `apktool`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `AndroidManifest.xml`: 1 khớp — `AndroidManifest.xml`
- Khối 5 (MATCH_REPLACE) target `[LAUNCHER_ACTIVITIES]`: 1 khớp — `smali/apk/tool/patcher/ui/modules/main/MainActivity.smali`
- Khối 6 (MATCH_ASSIGN) target `[LAUNCHER_ACTIVITIES]`: 1 khớp — `smali/apk/tool/patcher/ui/modules/main/MainActivity.smali`

Đề xuất tăng khả năng thành công:
- Chuỗi khối 3 còn xuất hiện ngoài target (smali/org/アェレ.smali, 4 lần) — cân nhắc bổ sung class-link
- Khối 4 trượt target [LAUNCHER_ACTIVITIES] — cập nhật TARGET theo class-link thật của APK
- Khối 7 trượt target [LAUNCHER_ACTIVITIES] — cập nhật TARGET theo class-link thật của APK

### Permission_phone — dự đoán 0%

- Cách: Điều chỉnh quyền: sửa AndroidManifest.xml (thêm/bớt quyền, debuggable, backup).
- Công cụ: `patchx apply`, `apktool`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `AndroidManifest.xml`: 1 khớp — `AndroidManifest.xml`
- Khối 5 (MATCH_REPLACE) target `[LAUNCHER_ACTIVITIES]`: 1 khớp — `smali/apk/tool/patcher/ui/modules/main/MainActivity.smali`
- Khối 6 (MATCH_ASSIGN) target `[LAUNCHER_ACTIVITIES]`: 1 khớp — `smali/apk/tool/patcher/ui/modules/main/MainActivity.smali`

Đề xuất tăng khả năng thành công:
- Chuỗi khối 3 còn xuất hiện ngoài target (smali/org/アェレ.smali, 4 lần) — cân nhắc bổ sung class-link
- Khối 4 trượt target [LAUNCHER_ACTIVITIES] — cập nhật TARGET theo class-link thật của APK
- Khối 7 trượt target [LAUNCHER_ACTIVITIES] — cập nhật TARGET theo class-link thật của APK

### Permission_readContact — dự đoán 0%

- Cách: Điều chỉnh quyền: sửa AndroidManifest.xml (thêm/bớt quyền, debuggable, backup).
- Công cụ: `patchx apply`, `apktool`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `AndroidManifest.xml`: 1 khớp — `AndroidManifest.xml`
- Khối 5 (MATCH_REPLACE) target `[LAUNCHER_ACTIVITIES]`: 1 khớp — `smali/apk/tool/patcher/ui/modules/main/MainActivity.smali`
- Khối 6 (MATCH_ASSIGN) target `[LAUNCHER_ACTIVITIES]`: 1 khớp — `smali/apk/tool/patcher/ui/modules/main/MainActivity.smali`

Đề xuất tăng khả năng thành công:
- Chuỗi khối 3 còn xuất hiện ngoài target (smali/org/アェレ.smali, 4 lần) — cân nhắc bổ sung class-link
- Khối 4 trượt target [LAUNCHER_ACTIVITIES] — cập nhật TARGET theo class-link thật của APK
- Khối 7 trượt target [LAUNCHER_ACTIVITIES] — cập nhật TARGET theo class-link thật của APK

### SignatureHack_arm64 — dự đoán 0%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Cách: Ẩn dấu vết Frida: thay chuỗi 'frida' bằng giá trị giả, comment lời gọi checkFrida/findFrida, tránh phát hiện gadget.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Cách: Chèn khởi tạo mod qua INIT/HOOK_SCRIPT: chạy lệnh/script khi app mở để bơm biến hoặc gọi hàm nội bộ.
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`

Điểm bypass cụ thể:
- Khối 8 (MATCH_GOTO) target `smali*/*.smali`: 1 khớp — `smali_classes2/ru/leymoy/StubApp.smali`
- Khối 14 (MATCH_REPLACE) target `smali*/*.smali`: 1 khớp — `smali_classes2/ru/leymoy/StubApp.smali`

Đề xuất tăng khả năng thành công:
- Khối 4 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 7 trượt target [APPLICATION] — cập nhật TARGET theo class-link thật của APK
- Khối 9 trượt target smali/com/unity3d/player/UnityPlayerActivity.smali — cập nhật TARGET theo class-link thật của APK
- Khối 10 trượt target [LAUNCHER_ACTIVITIES] — cập nhật TARGET theo class-link thật của APK
- Khối 12 trượt target smali/com/unity3d/player/UnityPlayerActivity.smali — cập nhật TARGET theo class-link thật của APK
- Khối 13 trượt target [APPLICATION] — cập nhật TARGET theo class-link thật của APK

### SignatureHack_armv7 — dự đoán 0%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Cách: Ẩn dấu vết Frida: thay chuỗi 'frida' bằng giá trị giả, comment lời gọi checkFrida/findFrida, tránh phát hiện gadget.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Cách: Chèn khởi tạo mod qua INIT/HOOK_SCRIPT: chạy lệnh/script khi app mở để bơm biến hoặc gọi hàm nội bộ.
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`

Điểm bypass cụ thể:
- Khối 8 (MATCH_GOTO) target `smali*/*.smali`: 1 khớp — `smali_classes2/ru/leymoy/StubApp.smali`
- Khối 14 (MATCH_REPLACE) target `smali*/*.smali`: 1 khớp — `smali_classes2/ru/leymoy/StubApp.smali`

Đề xuất tăng khả năng thành công:
- Khối 4 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 7 trượt target [APPLICATION] — cập nhật TARGET theo class-link thật của APK
- Khối 9 trượt target smali/com/unity3d/player/UnityPlayerActivity.smali — cập nhật TARGET theo class-link thật của APK
- Khối 10 trượt target [LAUNCHER_ACTIVITIES] — cập nhật TARGET theo class-link thật của APK
- Khối 12 trượt target smali/com/unity3d/player/UnityPlayerActivity.smali — cập nhật TARGET theo class-link thật của APK
- Khối 13 trượt target [APPLICATION] — cập nhật TARGET theo class-link thật của APK

### Dictionary+ru+uk+2 — dự đoán 0%

Điểm bypass cụ thể:
- Khối 4 (MATCH_REPLACE) target `res/values-ru/strings.xml`: 1 khớp — `res/values-ru/strings.xml`
- Khối 5 (MATCH_REPLACE) target `res/values-ru/strings.xml`: 311 khớp — `res/values-ru/strings.xml`
- Khối 10 (MATCH_REPLACE) target `res/values-ru/strings.xml`: 1 khớp — `res/values-ru/strings.xml`

Đề xuất tăng khả năng thành công:
- Khối 3 trượt target res/values-ru/strings.xml — cập nhật TARGET theo class-link thật của APK
- Chuỗi khối 4 còn xuất hiện ngoài target (res/values-h360dp-land/dimens.xml, 1 lần) — cân nhắc bổ sung class-link
- Chuỗi khối 5 còn xuất hiện ngoài target (res/values/strings.xml, 370 lần) — cân nhắc bổ sung class-link
- Khối 6 trượt target res/values-ru/strings.xml — cập nhật TARGET theo class-link thật của APK
- Khối 7 trượt target res/values-ru/strings.xml — cập nhật TARGET theo class-link thật của APK
- Khối 8 trượt target res/values-ru/strings.xml — cập nhật TARGET theo class-link thật của APK

### 4. DisableBillingService by VERGIL777 — dự đoán 0%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Cách: Giả lập mua hàng trong app: vô hiệu hoá lời gọi queryPurchases/getBuyIntent (MATCH_REPLACE), hoặc trả trạng thái đã mua qua SET_BOOL/MATCH_ASSIGN như Lucky Patcher.
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`, `Lucky Patcher`

Đề xuất tăng khả năng thành công:
- Khối 1 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 2 trượt target AndroidManifest.xml — cập nhật TARGET theo class-link thật của APK

### AUTH_VK_AND_FB — dự đoán 0%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`

Đề xuất tăng khả năng thành công:
- Khối 3 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK
- Khối 4 trượt target smali*/*.smali — cập nhật TARGET theo class-link thật của APK

### Activator — dự đoán 0%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`

## Combo bổ trợ

| Patch 1 | Patch 2 | Thành công | Bổ trợ |
|---------|---------|-----------:|--------|
| 3. GooglePlayServices by Edik1d | DexExtractor | 21% | integrity→shell |
| 3. GooglePlayServices by Edik1d | patch_bypass_sigcheck_with_reflection | 10% | google→bypass-license, google→integrity, integrity→bypass-license |
| 3. GooglePlayServices by Edik1d | License_hack | 3% | google→bypass-license, google→integrity, integrity→bypass-license |
| 3. GooglePlayServices by Edik1d | License_hack(Amazon) | 3% | google→bypass-license, google→integrity, integrity→bypass-license |
| 3. GooglePlayServices by Edik1d | Debug_information_and_hack_signature | 3% | google→bypass-license, google→integrity, integrity→anti-debug |
| 3. GooglePlayServices by Edik1d | patch_bypass_sigcheck | 3% | google→bypass-license, google→integrity, integrity→bypass-license |
| 3. GooglePlayServices by Edik1d | New. Removing the analytic tag, etc.. Inok_ZP 12.04.18 | 2% | integrity→google |
| 4. DisableBillingService by VERGIL777 | DexExtractor | 21% | bypass-license→shell |
| AUTH_VK_AND_FB | DexExtractor | 21% | bypass-license→shell |
| Activator | DexExtractor | 21% | bypass-license→shell |
| 3. GooglePlayServices by Edik1d | License_hack&htc v2 | 2% | google→bypass-license, google→integrity, integrity→bypass-license |
| 3. GooglePlayServices by Edik1d | BinSignatureHack_with_htc | 2% | google→bypass-license, google→integrity, integrity→bypass-license |
| 4. DisableBillingService by VERGIL777 | patch_bypass_sigcheck_with_reflection | 10% | bypass-license→integrity, bypass-license→shell, purchase→bypass-license |
| 3. GooglePlayServices by Edik1d | GooglePlayServices | 2% | google→integrity, integrity→google |
| 3. GooglePlayServices by Edik1d | SignatureHack_arm64 | 3% | google→bypass-license, google→integrity, integrity→bypass-license |
| 3. GooglePlayServices by Edik1d | SignatureHack_armv7 | 3% | google→bypass-license, google→integrity, integrity→bypass-license |
| 3. GooglePlayServices by Edik1d | Password_login_english | 1% | integrity→shell |
| 3. GooglePlayServices by Edik1d | Bin_sig&installer_fix[Google] | 2% | google→integrity, integrity→google |
| AUTH_VK_AND_FB | patch_bypass_sigcheck_with_reflection | 9% | bypass-license→integrity, bypass-license→shell |
| Activator | patch_bypass_sigcheck_with_reflection | 9% | bypass-license→integrity, bypass-license→shell |
| 3. GooglePlayServices by Edik1d | Bin_sig&installer_fix[Amazon] | 1% | google→integrity |
| 4. DisableBillingService by VERGIL777 | License_hack | 3% | bypass-license→integrity, purchase→bypass-license, purchase→integrity |
| 4. DisableBillingService by VERGIL777 | License_hack(Amazon) | 3% | bypass-license→integrity, purchase→bypass-license, purchase→integrity |
| 3. GooglePlayServices by Edik1d | 4. DisableBillingService by VERGIL777 | 2% | google→bypass-license, integrity→bypass-license, integrity→purchase |
| 4. DisableBillingService by VERGIL777 | patch_bypass_sigcheck | 3% | bypass-license→google, bypass-license→integrity, purchase→bypass-license |

## Phương án triển khai đề xuất

- Phương án: DexExtractor
- Tỷ lệ thành công dự đoán: 41%

1. Chuẩn bị cây APK (apk-prepare) hoặc dùng cây đã giải mã.
2. Áp patch: python3 patchx apply DexExtractor <cây-apk>
3. Chuẩn hoá resource chứa `$`: python3 patchx_toolkit.py apk-fix-res
4. Build: apktool b <cây> -o out.apk --aapt <aapt2-thật>
5. Zipalign + ký: zipalign -f 4 && apksigner sign
6. Cài APK, xác minh động bằng logcat/Frida theo mục xác_minh.

Rủi ro:
- APK có dấu hiệu tamper (7 lần) — trừ ~8% điểm dự đoán; ưu tiên patch integrity/token xử lý lớp này.
- APK có dấu hiệu emulator (6 lần) — trừ ~8% điểm dự đoán; ưu tiên patch integrity/token xử lý lớp này.
- APK có dấu hiệu signature (1 lần) — trừ ~20% điểm dự đoán; ưu tiên patch integrity/token xử lý lớp này.
- APK có dấu hiệu anti-debug (1 lần) — trừ ~10% điểm dự đoán; ưu tiên patch integrity/token xử lý lớp này.

Đề xuất nâng tỷ lệ:
- Chuỗi khối 3 còn xuất hiện ngoài target (assets/signatureHack/cc/binmt/signature/PmsHookApplication.smali, 3 lần) — cân nhắc bổ sung class-link