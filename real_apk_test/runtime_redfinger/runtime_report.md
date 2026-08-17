# Báo cáo Runtime verify (Đợt C — M2/M3)

- Thời gian: 2026-08-16 02:01:05
- APK: `/storage/emulated/0/Patch/patch1/_patchx/real_apk_test/apk_full_v2/kiss_tree_clean_patched_20260815-235855.apk`
- Package: `fr.neamar.kiss` | Activity: `fr.neamar.kiss.MainActivity`
- Device: 100.64.170.99:5555

| Tiêu chí | Kết quả |
|----------|---------|
| Cài APK | LỖI |
| Mở app | mã 0 |
| Process sống | Có (pid 30210) |
| Crash (FATAL EXCEPTION) | 1 dòng |
| **M2 (cài + mở + không crash)** | **CHƯA ĐẠT** |
| **M3 (hành vi đúng)** | **CHƯA XÁC MINH** |

## Lý do M3

- Chưa cung cấp kịch bản xác minh hành vi (--expect/--forbid).

## Crash log (trích)

```
08-16 03:01:17.826 30118 30196 E AndroidRuntime: Process: fr.neamar.kiss, PID: 30118
```

## Logcat (đuôi)

```
dle: u0a83 -7s398ms fr.neamar.kiss/.dataprovider.AppProvider
08-16 03:01:19.047 23440 26639 W ActivityManager: Stopping service due to app idle: u0a83 -7s395ms fr.neamar.kiss/.dataprovider.ContactsProvider
08-16 03:01:19.047 23440 26639 W ActivityManager: Stopping service due to app idle: u0a83 -7s391ms fr.neamar.kiss/.dataprovider.ShortcutsProvider
08-16 03:01:19.051 30210 30210 I ActivityThread: Relaunch all activities: onCoreSettingsChange
08-16 03:01:19.054 30210 30210 D CompatibilityChangeReporter: Compat change id reported: 171979766; UID 10083; state: ENABLED
08-16 03:01:19.075 30210 30210 V GraphicsEnvironment: ANGLE Developer option for 'fr.neamar.kiss' set to: 'default'
08-16 03:01:19.075 30210 30210 V GraphicsEnvironment: Neither updatable production driver nor prerelease driver is supported.
08-16 03:01:19.082 30210 30210 D NetworkSecurityConfig: No Network Security Config specified, using platform default
08-16 03:01:19.082 30210 30210 D NetworkSecurityConfig: No Network Security Config specified, using platform default
08-16 03:01:19.092   677   677 W HWCDisplay: [msiq-display]{SetVsyncEnabled:487} in...
08-16 03:01:19.092   677   677 W HWCDisplay: Display ID: 0 enabled: Enable
08-16 03:01:19.105 30210 30210 I ActivityThread: handleStopService: token=android.os.BinderProxy@7c951a4 not found.
08-16 03:01:19.111 23440 26639 W ActivityManager: Service done with onDestroy, but executeNesting=2: ServiceRecord{dbe793b u0 fr.neamar.kiss/.dataprovider.ShortcutsProvider}
```
