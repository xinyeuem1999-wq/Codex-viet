# Báo cáo quét chi tiết — phương án bypass

- Cây APK: `/storage/emulated/0/Patch/patch1/_patchx/apk_trees/KISS launcher_3.26.0`

## Patch đơn — điểm bypass, công cụ, tỷ lệ thành công

| Hạng | Patch | Điểm | Thành công | Khớp | Năng lực |
|------|-------|-----:|-----------:|-----:|----------|
| 1 | Debug_information_and_hack_signature | 1.000 | 90% | 78141 | bypass-license, integrity, trace |
| 2 | patch_bypass_sigcheck_with_reflection | 1.000 | 90% | 66 | bypass-license, integrity, shell |
| 3 | Debug_information | 0.925 | 88% | 78138 | trace |

### Debug_information_and_hack_signature — dự đoán 90%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Cách: Bật truy vết dữ liệu: chèn TRACE/API_LOG vào method mục tiêu để đọc tham số và phản hồi trước khi quyết định patch.
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`, `logcat`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `smali*/*.smali`: 3 khớp — `smali/androidx/collection/internal/Lock.smali`, `smali/androidx/core/provider/FontProvider.smali`, `smali/androidx/emoji2/text/DefaultEmojiCompatConfig$DefaultEmojiCompatConfigHelper_API28.smali`
- Khối 6 (MATCH_REPLACE) target `smali*/*.smali`: 78138 khớp — `smali/android/support/v4/app/RemoteActionCompatParcelizer.smali`, `smali/android/support/v4/graphics/drawable/IconCompatParcelizer.smali`, `smali/androidx/activity/Api34Impl.smali`, `smali/androidx/activity/Api36Impl.smali`

### patch_bypass_sigcheck_with_reflection — dự đoán 90%

- Cách: Vô hiệu hoá kiểm tra VIP/license: gán cờ đã mua bằng SET_BOOL, nhảy qua khối kiểm tra bằng MATCH_GOTO, hoặc hook hàm kiểm tra bằng Frida/LSPosed.
- Cách: Vô hiệu hoá kiểm tra toàn vẹn/chữ ký: sửa luồng check (MATCH_GOTO) hoặc trả true/false cố định (SET_BOOL/MATCH_ASSIGN).
- Cách: Chèn khởi tạo mod qua INIT/HOOK_SCRIPT: chạy lệnh/script khi app mở để bơm biến hoặc gọi hàm nội bộ.
- Công cụ: `patchx apply`, `apktool`, `apksigner`, `Frida`, `LSPosed`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `smali*/*`: 60 khớp — `smali/androidx/appcompat/app/AppCompatDelegateImpl$3.smali`, `smali/androidx/appcompat/app/AppCompatDelegateImpl.smali`, `smali/androidx/appcompat/app/AppCompatViewInflater$DeclaredOnClickListener.smali`, `smali/androidx/appcompat/view/SupportMenuInflater$InflatedOnMenuItemClickListener.smali`
- Khối 4 (MATCH_REPLACE) target `smali*/*.smali`: 6 khớp — `smali/androidx/collection/internal/Lock.smali`, `smali/androidx/core/provider/FontProvider.smali`, `smali/androidx/emoji2/text/DefaultEmojiCompatConfig$DefaultEmojiCompatConfigHelper_API28.smali`, `smali/androidx/profileinstaller/Encoding.smali`

### Debug_information — dự đoán 88%

- Cách: Bật truy vết dữ liệu: chèn TRACE/API_LOG vào method mục tiêu để đọc tham số và phản hồi trước khi quyết định patch.
- Công cụ: `patchx apply`, `logcat`

Điểm bypass cụ thể:
- Khối 3 (MATCH_REPLACE) target `smali*/*.smali`: 78138 khớp — `smali/android/support/v4/app/RemoteActionCompatParcelizer.smali`, `smali/android/support/v4/graphics/drawable/IconCompatParcelizer.smali`, `smali/androidx/activity/Api34Impl.smali`, `smali/androidx/activity/Api36Impl.smali`

## Phương án triển khai đề xuất

- Phương án: Debug_information_and_hack_signature
- Tỷ lệ thành công dự đoán: 90%

1. Chuẩn bị cây APK (apk-prepare) hoặc dùng cây đã giải mã.
2. Áp patch: python3 patchx apply Debug_information_and_hack_signature <cây-apk>
3. Chuẩn hoá resource chứa `$`: python3 patchx_toolkit.py apk-fix-res
4. Build: apktool b <cây> -o out.apk --aapt <aapt2-thật>
5. Zipalign + ký: zipalign -f 4 && apksigner sign
6. Cài APK, xác minh động bằng logcat/Frida theo mục xác_minh.