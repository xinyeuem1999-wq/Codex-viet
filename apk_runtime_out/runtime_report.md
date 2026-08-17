# Báo cáo Runtime verify (Đợt C — M2/M3)

- Thời gian: 2026-08-17 21:20:15
- APK: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/app_bypass_signed.apk`
- Package: `com.zaz.translate` | Activity: `com.zaz.translate.WelcomeActivity`
- Device: 100.64.170.99:5555

- Cài đặt: `install`
- Resumed activity: CÓ
| Tiêu chí | Kết quả |
|----------|---------|
| Cài APK | OK |
| Mở app | mã 0 |
| Process sống | Có (pid 31589) |
| Crash (FATAL EXCEPTION) | 0 dòng |
| ANR | 0 dòng |
| **M2 (cài + mở + không crash)** | **ĐẠT** (M2_PASS) |
| Verdict | **SKIP** |
| **M3 (hành vi đúng)** | **CHƯA XÁC MINH** |

## Lý do M3

- Chưa cung cấp kịch bản xác minh hành vi (--scenario hoặc --expect/--forbid).

## Xác thực hiện đại (T3)

- Chữ ký: HỢP LỆ (v1, v2, v3, v3.1, v4)
- Nếu thiếu v2/v3: patch cần bổ sung để qua kiểm tra signature (khoá v1/v2/v3).
- Play Integrity / hardware attestation cần thiết bị thật — máy ảo cloud không xác minh được (giới hạn T3).

## Hành vi mạng (T3)

- Phát hiện 21 kết nối mạng mới sau khi mở app — kiểm tra nếu là hành vi 'âm thầm' gửi dữ liệu của patch.
- Kết nối mới:
  - 0:0:0:0:65535:0:51924:1057:33160 -> 0:0:0:0:65535:0:30621:64398:443 (ESTABLISHED)
  - 0:0:0:0:65535:0:51924:1057:34488 -> 0:0:0:0:65535:0:1138:55724:443 (ESTABLISHED)
  - 0:0:0:0:65535:0:51924:1057:38456 -> 0:0:0:0:65535:0:33561:55724:443 (ESTABLISHED)
  - 0:0:0:0:65535:0:51924:1057:38458 -> 0:0:0:0:65535:0:33561:55724:443 (ESTABLISHED)
  - 0:0:0:0:65535:0:51924:1057:43536 -> 0:0:0:0:65535:0:3532:38841:443 (ESTABLISHED)
  - 0:0:0:0:65535:0:51924:1057:48194 -> 0:0:0:0:65535:0:32870:53512:443 (ESTABLISHED)
  - 0:0:0:0:65535:0:51924:1057:48204 -> 0:0:0:0:65535:0:32870:53512:443 (ESTABLISHED)
  - 0:0:0:0:65535:0:51924:1057:50664 -> 0:0:0:0:65535:0:32829:3705:443 (ESTABLISHED)
  - 0:0:0:0:65535:0:51924:1057:51930 -> 0:0:0:0:65535:0:14727:16658:443 (ESTABLISHED)
  - 0:0:0:0:65535:0:51924:1057:52822 -> 0:0:0:0:65535:0:38771:43456:80 (ESTABLISHED)

## Logcat (đuôi)

```
e.android.gms.providerinstaller.dynamite
08-17 22:21:30.706 26049 31586 I GmsDebugLogger: [20] [MlkitOcrDevanagari.optional:251333100000]
08-17 22:21:30.736 23440 23501 E PackageSettings: Failed to set packages.list SELinux context
08-17 22:21:30.737 23440 23464 I DropBoxManagerService: add tag=system_server_wtf isTagEnabled=true flags=0x2
08-17 22:21:30.747 23440 23464 I DropBoxManagerService: add tag=system_server_wtf isTagEnabled=true flags=0x2
08-17 22:21:30.779 26049 31586 I ChimeraConfigurator: Update complete: success
08-17 22:21:30.798 26049 31586 I GmsModuleFndr: Beginning GMS chimera module scan
08-17 22:21:30.819 26049 31586 I ModuleSetResolution: Computing pending module set with APKs: [[Appsearch.optional:251333100400], [MapsCoreDynamite.integ:250625400100400], [MlkitOcrChinese.optional:251333100000], [MlkitOcrCommon.optional:251333100400], [MlkitOcrDevanagari.optional:251333100000], [MlkitOcrJapanese.optional:251333100000], [MlkitOcrKorean.optional:251333100000], [TfliteDynamiteDynamite.integ:260580502100400], [TfliteDynamiteDynamite.integ:262730502100400], [VisionCustomIca.optional:251333100400], [VisionIca.optional:251333100400], [VisionOcr.optional:251333100000], [Wasmlibs.optional:251333100400], [AdsFdrDynamite.integ:250505301100000], [Cronetdynamite:251333190400], [Dynamiteloader:251333190000], [Dynamitemodulesa:251333190000], [Dynamitemodulesc:251333190000], [Googlecertificates:251333190000], [Mapsdynamite:251333190000], [Measurementdynamite:251333190000]]
```
