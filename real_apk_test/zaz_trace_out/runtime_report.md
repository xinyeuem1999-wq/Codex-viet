# Báo cáo Runtime verify (Đợt C — M2/M3)

- Thời gian: 2026-08-16 14:35:15
- APK: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/zaz_trace_out/zaz_trace_tree_patched_20260816-143511.apk`
- Package: `com.zaz.translate` | Activity: `com.zaz.translate.WelcomeActivity`
- Device: 100.64.170.99:5555

| Tiêu chí | Kết quả |
|----------|---------|
| Cài APK | LỖI |
| Mở app | mã 0 |
| Process sống | KHÔNG |
| Crash (FATAL EXCEPTION) | 1 dòng |
| **M2 (cài + mở + không crash)** | **CHƯA ĐẠT** |
| **M3 (hành vi đúng)** | **CHƯA ĐẠT** |

## Lý do M3

- logcat không chứa mẫu --expect

## Xác thực hiện đại (T3)

- Chữ ký: HỢP LỆ (v1, v2, v3, v3.1, v4)
- Nếu thiếu v2/v3: patch cần bổ sung để qua kiểm tra signature (khoá v1/v2/v3).
- Play Integrity / hardware attestation cần thiết bị thật — máy ảo cloud không xác minh được (giới hạn T3).

## Hành vi mạng (T3)

- Phát hiện 3 kết nối mạng mới sau khi mở app — kiểm tra nếu là hành vi 'âm thầm' gửi dữ liệu của patch.
- Kết nối mới:
  - 0:0:0:0:65535:0:51924:1057:36256 -> 0:0:0:0:65535:0:49946:55724:443 (ESTABLISHED)
  - 0:0:0:0:65535:0:51924:1057:36258 -> 0:0:0:0:65535:0:49946:55724:443 (ESTABLISHED)
  - 0:0:0:0:65535:0:51924:1057:36286 -> 0:0:0:0:65535:0:49946:55724:443 (ESTABLISHED)

## Crash log (trích)

```
08-16 15:36:10.058 30754 30754 E AndroidRuntime: Process: com.zaz.translate, PID: 30754
```

## Logcat (đuôi)

```
 data save over FILE 0 false
08-16 15:36:38.893 50728 50728 I Finsky  : [2] nqz.a(197): App states replicator found 12 unowned apps
08-16 15:36:38.902 50728 50728 I Finsky  : [2] nre.b(23): Completed 0 account content syncs with 0 successful.
08-16 15:36:38.902 50728 50728 I Finsky  : [2] ContentSyncJob.a(14): [ContentSync] Installation state replication succeeded.
08-16 15:36:38.903 50728 50728 I Finsky  : [2] ahvv.q(61): SCH: jobFinished: 12-1. TimeElapsed: 3128ms.
08-16 15:36:38.929 50728 50909 I Finsky  : [51] sgc.accept(59): SCH: Scheduling phonesky job Id: 1-1337, CT: 1786831221822, Constraints: [{ L: 43146665, D: 86346665, C: CHARGING_NONE, I: IDLE_NONE, N: NET_ANY, B: BATTERY_ANY }]
08-16 15:36:38.929 50728 50909 I Finsky  : [51] sgc.accept(59): SCH: Scheduling phonesky job Id: 34-2, CT: 1786818595312, Constraints: [{ L: 79199923, D: 1375199923, C: CHARGING_NONE, I: IDLE_NONE, N: NET_ANY, B: BATTERY_ANY }]
08-16 15:36:38.930 50728 50909 I Finsky  : [51] sgc.accept(59): SCH: Scheduling phonesky job Id: 34-4, CT: 1786818605640, Constraints: [{ L: 604800000, D: 2591998552, C: CHARGING_NONE, I: IDLE_NONE, N: NET_ANY, B: BATTERY_ANY }]
08-16 15:36:38.941 50728 50914 I Finsky  : [56] nit.apply(254): SCH: Scheduling 1 system job(s)
08-16 15:36:38.941 50728 50914 I Finsky  : [56] ahvr.b(86): SCH: Scheduling system job Id: 9063, L: 8569546, D: 51769546, C: false, I: false, N: 1
08-16 15:36:38.948 50728 30991 I Finsky  : [841] ahxm.a(26): SCH: job service finished with id 9058.
```
