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
