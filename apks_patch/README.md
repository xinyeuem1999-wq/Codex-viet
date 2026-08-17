# apks_patch

Thư mục lưu **APK đã chạy patch** (kết quả đầu ra), phân biệt với `Apks/` là
thư mục **APK đầu vào gốc**.

- `Apks/`          → APK gốc chưa sửa (input).
- `apks_patch/`    → APK đã áp patch, build, zipalign và ký (output).

## Cách dùng

```sh
# Áp patch lên APK (mặc định tự chọn APK đầu tiên trong Apks/), build, ký
# và lưu vào apks_patch/:
python3 patchx_toolkit.py apk-patch upgraded/<ten-patch>.zip

# Chỉ định APK/cây cụ thể, nhiều patch:
python3 patchx_toolkit.py apk-patch upgraded/p1.zip upgraded/p2.zip Apks/ten.apk

# Bỏ qua ký (chỉ cần APK đã patch, chưa ký):
python3 patchx_toolkit.py apk-patch --no-sign upgraded/p1.zip
```

Quy trình `apk-patch`: áp patch → chuẩn hoá resource chứa `$` → `apktool b`
→ `zipalign -f 4` → `apksigner sign` → lưu APK + `report_*.json`.

Keystore: dùng `real_apk_test/patchx.keystore` nếu có; nếu không, tự sinh
`patchx-debug.keystore` trong thư mục này.
