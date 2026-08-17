# Lộ trình mod (roadmap)

- Thời gian: 2026-08-14 03:08:47

## Hide_Icon [Chống-phát-hiện] — Áp dụng được
- Bao phủ: 1/1 quy tắc, 1 lần khớp
  - khối 3 (MATCH_REPLACE) target=AndroidManifest.xml: 1 khớp

## z [Khác] — Áp dụng được
- Bao phủ: 1/1 quy tắc, 1 lần khớp
  - khối 3 (MATCH_REPLACE) target=[LAUNCHER_ACTIVITIES]: 1 khớp

## AddSave [Lưu-trữ] — Áp dụng được
- Bao phủ: 1/1 quy tắc, 1 lần khớp
  - khối 4 (MATCH_REPLACE) target=[LAUNCHER_ACTIVITIES]: 1 khớp

## Add_Save [Lưu-trữ] — Áp dụng được
- Bao phủ: 1/1 quy tắc, 1 lần khớp
  - khối 4 (MATCH_REPLACE) target=[LAUNCHER_ACTIVITIES]: 1 khớp

## Add_Save_New [Lưu-trữ] — Áp dụng được
- Bao phủ: 1/1 quy tắc, 1 lần khớp
  - khối 4 (MATCH_REPLACE) target=[LAUNCHER_ACTIVITIES]: 1 khớp

## GenerateAndroidID [Spoof-ID] — Áp dụng được
- Bao phủ: 1/1 quy tắc, 1 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*.smali: 1 khớp

## dppp [Tiện-ích] — Áp dụng được
- Bao phủ: 1/1 quy tắc, 1 lần khớp
- Rủi ro: MERGE cần public.xml để tái cấu trúc ID
  - khối 3 (MATCH_REPLACE) target=AndroidManifest.xml: 1 khớp

## patch_mem_editor [Tiện-ích] — Áp dụng được
- Bao phủ: 2/2 quy tắc, 2 lần khớp
- Rủi ro: MERGE cần public.xml để tái cấu trúc ID
  - khối 5 (MATCH_REPLACE) target=AndroidManifest.xml: 1 khớp
  - khối 6 (MATCH_REPLACE) target=AndroidManifest.xml: 1 khớp

## patch_my_font [Tiện-ích] — Áp dụng được
- Bao phủ: 3/4 quy tắc, 3 lần khớp
- Rủi ro: MERGE cần public.xml để tái cấu trúc ID
  - khối 5 (MATCH_GOTO) target=AndroidManifest.xml: 1 khớp
  - khối 6 (MATCH_REPLACE) target=AndroidManifest.xml: 1 khớp
  - khối 8 (MATCH_REPLACE) target=[APPLICATION]: 0 khớp
  - khối 9 (MATCH_REPLACE) target=[ACTIVITIES]: 1 khớp

## Android_ID [Spoof-ID] — Áp dụng được
- Bao phủ: 1/2 quy tắc, 1 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*.smali: 1 khớp
  - khối 4 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp

## IMEI_Locker [Spoof-ID] — Áp dụng được
- Bao phủ: 1/2 quy tắc, 1 lần khớp
  - khối 3 (MATCH_REPLACE) target=[LAUNCHER_ACTIVITIES]: 1 khớp
  - khối 4 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp

## patch_data_editor [Tiện-ích] — Áp dụng được
- Bao phủ: 1/2 quy tắc, 1 lần khớp
- Rủi ro: xóa tệp (có sao lưu), MERGE cần public.xml để tái cấu trúc ID
  - khối 4 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp
  - khối 5 (MATCH_REPLACE) target=AndroidManifest.xml: 1 khớp

## patch_new_entrance [Tiện-ích] — Áp dụng được
- Bao phủ: 1/2 quy tắc, 1 lần khớp
- Rủi ro: MERGE cần public.xml để tái cấu trúc ID
  - khối 3 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp
  - khối 4 (MATCH_REPLACE) target=AndroidManifest.xml: 1 khớp

## LogCat [Tiện-ích] — Một phần
- Bao phủ: 4/11 quy tắc, 4 lần khớp
- Rủi ro: cần --dex-runner
  - khối 4 (MATCH_GOTO) target=AndroidManifest.xml: 0 khớp
  - khối 8 (MATCH_REPLACE) target=AndroidManifest.xml: 1 khớp
  - khối 9 (MATCH_ASSIGN) target=AndroidManifest.xml: 1 khớp
  - khối 10 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp
  - khối 11 (MATCH_GOTO) target=AndroidManifest.xml: 1 khớp
  - khối 12 (MATCH_REPLACE) target=AndroidManifest.xml: 1 khớp
  - khối 13 (MATCH_REPLACE) target=smali/apk/tool/patcher/App.smali: 0 khớp
  - khối 15 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp
  - khối 16 (MATCH_ASSIGN) target=[APPLICATION]: 0 khớp
  - khối 17 (MATCH_REPLACE) target=[APPLICATION]: 0 khớp
  - khối 18 (MATCH_REPLACE) target=smali/apk/tool/patcher/App.smali: 0 khớp

## UnPacker [Tiện-ích] — Một phần
- Bao phủ: 2/7 quy tắc, 2 lần khớp
  - khối 3 (MATCH_REPLACE) target=[LAUNCHER_ACTIVITIES]: 1 khớp
  - khối 4 (MATCH_REPLACE) target=[LAUNCHER_ACTIVITIES]: 0 khớp
  - khối 5 (MATCH_REPLACE) target=[LAUNCHER_ACTIVITIES]: 0 khớp
  - khối 6 (MATCH_REPLACE) target=[LAUNCHER_ACTIVITIES]: 0 khớp
  - khối 8 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp
  - khối 9 (MATCH_ASSIGN) target=[LAUNCHER_ACTIVITIES]: 1 khớp
  - khối 10 (MATCH_REPLACE) target=[LAUNCHER_ACTIVITIES]: 0 khớp

## Anti-Adaptive_Icon_b2 [Chống-phát-hiện] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
- Rủi ro: xóa tệp (có sao lưu)
  - khối 3 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp

## Anti-ModGuard(hide) [Chống-phát-hiện] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 0 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp

## Hide[ModGuard] [Chống-phát-hiện] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
- Rủi ro: cần --dex-runner
  - khối 5 (MATCH_REPLACE) target=smali/RemoveAds1.smali: 0 khớp

## ModGuard [Chống-phát-hiện] — Không khớp
- Bao phủ: 0/2 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp
  - khối 4 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp

## ref_logging [Chống-phát-hiện] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*: 0 khớp

## root [Chống-phát-hiện] — Không khớp
- Bao phủ: 0/3 quy tắc, 0 lần khớp
  - khối 2 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp
  - khối 4 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp

## DelLoc [Khác] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
- Rủi ro: cần --dex-runner
  - khối 4 (MATCH_REPLACE) target=res/values/strings.xml: 0 khớp

## Deletion + Extra + Sound [Khác] — Không khớp
- Bao phủ: 0/4 quy tắc, 0 lần khớp
- Rủi ro: xóa tệp (có sao lưu)
  - khối 4 (MATCH_ASSIGN) target=res/values/public.xml: 0 khớp
  - khối 5 (MATCH_REPLACE) target=res/values/strings.xml: 0 khớp
  - khối 6 (MATCH_REPLACE) target=res/values/strings.xml: 0 khớp
  - khối 7 (MATCH_REPLACE) target=res/values/strings.xml: 0 khớp

## Obleg4it perevod strok [Khác] — Không khớp
- Bao phủ: 0/36 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 4 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 5 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 6 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 7 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 8 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 9 (MATCH_ASSIGN) target=res/values-ru/strings.xml: 0 khớp
  - khối 10 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 11 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 12 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 13 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 14 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 15 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 16 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 17 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 18 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 19 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 20 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 21 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 22 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 23 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 24 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 25 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 26 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 27 (MATCH_ASSIGN) target=res/values-uk/strings.xml: 0 khớp
  - khối 28 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 29 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 30 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 31 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 32 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 33 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 34 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 35 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 36 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 37 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp
  - khối 38 (MATCH_REPLACE) target=res/values-uk/strings.xml: 0 khớp

## Turn off + Checks + On + Emulator + Android [Khác] — Không khớp
- Bao phủ: 0/4 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp
  - khối 4 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp
  - khối 5 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp
  - khối 6 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp

## Только Rus [Khác] — Không khớp
- Bao phủ: 0/7 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 4 (MATCH_ASSIGN) target=res/values-ru/strings.xml: 0 khớp
  - khối 5 (MATCH_REPLACE) target=res/values/strings.xml: 0 khớp
  - khối 6 (MATCH_REPLACE) target=res/values/strings.xml: 0 khớp
  - khối 7 (MATCH_REPLACE) target=res/values/strings.xml: 0 khớp
  - khối 8 (MATCH_REPLACE) target=res/values-ru/strings.xml: 0 khớp
  - khối 9 (MATCH_REPLACE) target=res/values/strings.xml: 0 khớp

## Disconnect_internet [Mạng] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 2 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp

## NoInternet [Mạng] — Không khớp
- Bao phủ: 0/2 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp
  - khối 4 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp

## NoLocation [Mạng] — Không khớp
- Bao phủ: 0/3 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp
  - khối 4 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp
  - khối 5 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp

## NoPlayGames [Mạng] — Không khớp
- Bao phủ: 0/2 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp
  - khối 4 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp

## BSSID [Spoof-ID] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp

## Bluetooth_Mac [Spoof-ID] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp

## GenerateDeviceID [Spoof-ID] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp

## Generate_Device model spoofing [Spoof-ID] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp

## NoInternetWifi [Spoof-ID] — Không khớp
- Bao phủ: 0/7 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp
  - khối 4 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp
  - khối 5 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp
  - khối 6 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp
  - khối 7 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp
  - khối 8 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp
  - khối 9 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp

## SerNum [Spoof-ID] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali/*.smali: 0 khớp

## WiFi_Mac [Spoof-ID] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp

## brand [Spoof-ID] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=*.smali: 0 khớp

## imei [Spoof-ID] — Không khớp
- Bao phủ: 0/2 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp
  - khối 4 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp

## DexExtractor [Tiện-ích] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*: 0 khớp

## DuplicateDel [Tiện-ích] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
- Rủi ro: cần --dex-runner
  - khối 4 (MATCH_REPLACE) target=res/values/public.xml: 0 khớp

## InstallLocation_auto [Tiện-ích] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 0 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp

## InstallerPackageName [Tiện-ích] — Không khớp
- Bao phủ: 0/2 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp
  - khối 4 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp

## NoAutoBoot [Tiện-ích] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp

## NoCamera [Tiện-ích] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp

## NoRecordAudio [Tiện-ích] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp

## NoUpdates [Tiện-ích] — Không khớp
- Bao phủ: 0/0 quy tắc, 0 lần khớp
- Rủi ro: cần --dex-runner

## Receiver_deleter [Tiện-ích] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp

## TimeStop [Tiện-ích] — Không khớp
- Bao phủ: 0/2 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp
  - khối 4 (MATCH_REPLACE) target=smali*/*.smali: 0 khớp

## ToolReplacement [Tiện-ích] — Không khớp
- Bao phủ: 0/0 quy tắc, 0 lần khớp
- Rủi ro: cần --dex-runner, xóa tệp (có sao lưu)

## anti_fullscreen [Tiện-ích] — Không khớp
- Bao phủ: 0/2 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=res/values*/styles.xml: 0 khớp
  - khối 4 (MATCH_REPLACE) target=res/values*/styles.xml: 0 khớp

## fix_for_18_9dpi [Tiện-ích] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp

## fullscreen [Tiện-ích] — Không khớp
- Bao phủ: 0/2 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=res/values*/styles.xml: 0 khớp
  - khối 4 (MATCH_REPLACE) target=res/values*/styles.xml: 0 khớp

## minsdk [Tiện-ích] — Không khớp
- Bao phủ: 0/1 quy tắc, 0 lần khớp
  - khối 3 (MATCH_REPLACE) target=AndroidManifest.xml: 0 khớp

## patch_script_example [Tiện-ích] — Không khớp
- Bao phủ: 0/0 quy tắc, 0 lần khớp
- Rủi ro: cần --dex-runner
