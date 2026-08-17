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
