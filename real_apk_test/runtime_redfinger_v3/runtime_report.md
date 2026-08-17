# Báo cáo Runtime verify (Đợt C — M2/M3)

- Thời gian: 2026-08-16 02:20:27
- APK: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/apk_full_v3/KISS launcher_3.26.0_patched_20260816-021659.apk`
- Package: `fr.neamar.kiss` | Activity: `fr.neamar.kiss.MainActivity`
- Device: 100.64.170.99:5555

| Tiêu chí | Kết quả |
|----------|---------|
| Cài APK | OK |
| Mở app | mã 0 |
| Process sống | Có (pid 33303) |
| Crash (FATAL EXCEPTION) | 0 dòng |
| **M2 (cài + mở + không crash)** | **ĐẠT** |
| **M3 (hành vi đúng)** | **ĐẠT** |


## Logcat (đuôi)

```
itManager: 03:20:37.337 [RxCachedThreadScheduler-15] INFO  [c.r.m.r.RetrofitManager.log:47] - 
08-16 03:20:37.338 26843 33021 I c.r.m.r.RetrofitManager: 03:20:37.338 [RxCachedThreadScheduler-15] INFO  [c.r.m.r.RetrofitManager.log:47] - {"code":0,"msg":"成功","response":{},"times":1786821637317}
08-16 03:20:37.339 26843 33021 I c.r.m.r.RetrofitManager: 03:20:37.338 [RxCachedThreadScheduler-15] INFO  [c.r.m.r.RetrofitManager.log:47] - <-- END HTTP (61-byte body)
08-16 03:20:37.441   845  1307 D BufferPoolAccessor2.0: bufferpool2 0xb400007dfb9b22e8 : 0(0 size) total buffers - 0(0 size) used buffers - 7/10 (recycle/alloc) - 3/9 (fetch/transfer)
08-16 03:20:37.441   845  1307 D BufferPoolAccessor2.0: evictor expired: 1, evicted: 1
08-16 03:20:38.226 23986 25351 D DataSyncHelper: onDataSync result:233
08-16 03:20:38.769   677   677 W HWCDisplay: [msiq-display]{SetVsyncEnabled:487} in...
08-16 03:20:38.769   677   677 W HWCDisplay: Display ID: 0 enabled: Enable
08-16 03:20:38.866   677   677 W HWCDisplay: [msiq-display]{SetVsyncEnabled:487} in...
08-16 03:20:38.866   677   677 W HWCDisplay: Display ID: 0 enabled: Disable
08-16 03:20:39.682 23440 31006 W ProcessStats: Tracking association SourceState{35339d5 system/1000 BTopFgs #4169} whose proc state 2 is better than process ProcessState{5ccb5ea com.tailscale.ipn/10079 pkg=com.tailscale.ipn} proc state 3 (67 skipped)
08-16 03:20:43.277   662 33300 I keystore2: keystore2::watchdog: Watchdog thread idle -> terminating. Have a great day.
```
