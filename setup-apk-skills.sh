#!/data/data/com.termux/files/usr/bin/bash
set -e

BASE=".codex/skills"

echo "[+] Creating skills..."

mkdir -p "$BASE"/{apk-reverse,smali-analysis,native-jni,android-security}

cat > "$BASE/apk-reverse/SKILL.md" <<'SKILL'
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
SKILL

cat > "$BASE/smali-analysis/SKILL.md" <<'SKILL'
---
name: smali-analysis
description: Phân tích DEX và Smali, control flow, data flow và reconstruct Java/Kotlin.
---

# Smali / DEX Analysis

## Register

Theo dõi:

- p0, p1...
- v0, v1...
- parameters
- locals
- return values
- object types
- primitive types

## Instructions

Đặc biệt phân tích:

- move
- move-result
- const
- new-instance
- invoke-*
- iget/iput
- sget/sput
- if-*
- goto
- switch
- throw
- catch
- return

## Control flow

Xây dựng:

entry → branches → loops → exceptions → return

## Data flow

Theo dõi dữ liệu từ:

- parameters
- constants
- fields
- Intent
- Bundle
- SharedPreferences
- database
- network
- native methods

đến output hoặc side effects.

## Reconstruction

Khi chuyển Smali thành Java/Kotlin:

- giữ nguyên semantics;
- giữ nguyên null checks;
- giữ nguyên branches;
- giữ nguyên casts;
- giữ nguyên exception behavior.

Nếu không chắc chắn, đánh dấu INFERENCE.

Không bịa code.
SKILL

cat > "$BASE/native-jni/SKILL.md" <<'SKILL'
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
SKILL

cat > "$BASE/android-security/SKILL.md" <<'SKILL'
---
name: android-security
description: Phân tích bảo mật APK: Manifest, network, storage, WebView, crypto và IPC.
---

# Android Security Analysis

## Manifest

Kiểm tra:

- permissions
- exported components
- intent filters
- deep links
- providers
- services
- receivers
- backup configuration
- cleartext traffic
- network security config

## Network

Tìm:

- HTTP/HTTPS
- domains
- endpoints
- headers
- authentication
- tokens
- certificate validation
- TLS configuration

Không coi một endpoint hoặc string là vulnerability nếu chưa có bằng chứng.

## Storage

Kiểm tra:

- SharedPreferences
- SQLite
- files
- cache
- external storage
- logs

## WebView

Kiểm tra:

- JavaScript
- JavaScript interfaces
- file access
- URL loading
- custom schemes
- WebViewClient

## IPC

Kiểm tra:

- Intent
- Binder
- AIDL
- ContentProvider
- BroadcastReceiver
- exported components

## Crypto

Kiểm tra:

- algorithm
- key generation
- key storage
- IV/nonce
- randomness
- Android Keystore

## Findings

Mỗi finding gồm:

- location
- evidence
- impact
- preconditions
- severity
- confidence
- remediation

Phân biệt rõ:

FACT
INFERENCE
UNKNOWN

Chỉ phân tích APK mà người dùng có quyền kiểm thử.
SKILL

echo
echo "[+] Created:"
find "$BASE" -name SKILL.md -print

echo
echo "[+] Syntax check:"
bash -n setup-apk-skills.sh

echo
echo "[+] Done."
