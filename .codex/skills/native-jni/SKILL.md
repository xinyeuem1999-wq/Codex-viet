---
name: native-jni
description: Phân tích lib.so, ELF, JNI và liên kết native với Java/Kotlin.
---

# Native / JNI Analysis

## Kiểm tra

- architecture
- ABI
- ELF
- sections
- symbols
- imports
- exports
- strings
- dependencies

## JNI

Tìm:

- JNIEXPORT
- Java_* symbols
- JNI_OnLoad
- RegisterNatives
- JNIEnv
- native method declarations

Liên kết:

Java/Kotlin
→ JNI
→ native function

## Native data flow

Theo dõi:

- String
- byte[]
- jstring
- jbyteArray
- jobject
- ByteBuffer

## Crypto

Nếu gặp cryptography:

- xác định algorithm;
- input;
- key source;
- IV/nonce;
- output;
- storage.

Chỉ kết luận khi có bằng chứng.

Không tự suy đoán algorithm hoặc key.

## Output

Báo cáo:

- binary
- architecture
- symbols
- JNI mapping
- call flow
- Java/native data flow
- FACT
- INFERENCE
- UNKNOWN
