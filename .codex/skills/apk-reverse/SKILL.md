---
name: apk-reverse
description: Phân tích APK, Manifest, DEX, resources và kiến trúc Android.
---

# APK Reverse Engineering

Phân tích APK được cung cấp trong project mà người dùng có quyền kiểm thử.

## Quy trình

1. Kiểm tra AndroidManifest.xml.
2. Xác định package/application ID.
3. Liệt kê Activities, Services, Receivers và Providers.
4. Kiểm tra permissions và exported components.
5. Kiểm tra assets và resources.
6. Kiểm tra classes.dex và multidex.
7. Phân tích Java/Kotlin và đối chiếu Smali.
8. Kiểm tra lib/*.so và chuyển sang native-jni khi cần.
9. Theo dõi data flow và call graph.

## Nguyên tắc

- Smali/DEX được ưu tiên khi decompiler không chắc chắn.
- Không bịa class, method, API hoặc behavior.
- Giữ nguyên package/class/method/field names.
- Phân biệt FACT, INFERENCE và UNKNOWN.
- Nếu thiếu dữ liệu, nói rõ cần file/class/method nào.
