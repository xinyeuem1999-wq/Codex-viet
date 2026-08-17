# AGENTS.md — patchx toolkit (Reverse APK / Smali / Java)

Tài liệu tổng hợp tối ưu để mọi phiên Codex sau này nắm ngay bối cảnh, quy
trình, lệnh, mốc đo được và việc tiếp theo — không cần đọc lại lịch sử.

## Quy ước bắt buộc

- Tài liệu, bình luận, thông báo viết bằng **tiếng Việt**.
- Danh từ/chuỗi trong mã nguồn (khóa patch, mẫu regex, nội dung smali/XML,
  tên biến, tên tệp) **giữ nguyên gốc** — không dịch, không đổi, tránh lỗi
  cấu trúc khi áp patch.
- Bộ sưu tập gốc không bị sửa; mọi chuẩn hóa ghi ra thư mục mới (`upgraded/`,
  `optimized/`, `toolkit_out/`, ...).
- Regex lỗi/không khớp chỉ cảnh báo, không tự sửa nội dung patch.
- `EXECUTE_DEX` mặc định bỏ qua; chỉ chạy với `--dex-runner` an toàn.
- Mọi kết luận phải có số liệu đo được (test, simulate, coverage).

## Vị trí dữ liệu quan trọng

- Bộ làm việc chính: `upgraded/` — 60 zip chuẩn hóa, 0 lỗi.
- Bộ mẫu bypass nâng cao: `bypass_plus/` — 13 zip (ssl pinning, root,
  emulator, anti-debug, frida, IAP fake, Play Integrity) — audit 0 lỗi,
  combo sinh tại `combos_auto_plus/`.
- Patch gốc đã xóa; manifest lưu: `backup/deleted_originals_20260814-155340.json`.
- Toolkit: `patchx_toolkit.py`; bản phân phối: `dist/patchx-toolkit-*.zip`.
- APK đầu vào: `Apks/` (gốc, chưa sửa — hiện 1 APK: `ApkToolPatcher v5.0.apk`);
  APK đã patch: `apks_patch/` (đầu ra của lệnh `apk-patch`, kèm `report_*.json`).
- Kết quả full pipeline: `toolkit_out/toolkit_report.md`.
- APK thật để test: `real_apk_test/app_tree` (477M); APK đã ký:
  `real_apk_test/app_bypass_signed.apk`; keystore: `real_apk_test/patchx.keystore`
  (pass: `patchx123`).
- Combo: `combos/` (76 combo chính), `combos_auto/` (13 combo tự phát hiện
  theo họ chức năng).
- Cache quét APK: `toolkit_out/cache/scan_*.json` — theo hash cây, nạp lại
  ~0s (xem lệnh `bench-scan`).
- Hook điều khiển thu thập dữ liệu từ xa: `hook_remote_data_control/`.
- Đề xuất kiến trúc V2: `de xuat phuong an/đề xuất.txt` +
  `de xuat phuong an/mau_ke_hoach_ngu_nghia.json` (2 tệp).
- Nguồn "patch update" (chỉ đọc, không sửa):
  `/storage/emulated/0/Modder Hub/Apk Editor Patches/` — bản lành của
  `SignatureHack_arm64.zip` lấy từ đây.

## Lệnh cốt lõi

Chạy từ `_patchx`:

| Nhóm | Lệnh |
|------|------|
| Quét | `python3 patchx scan KHO [--recursive]` (vd `upgraded`), `index KHO`, `dupes KHO`, `manifest KHO`, `report [--apk CÂY]` |
| Kiểm tra | `python3 patchx audit`, `selfcheck`, `test`, `golden [--fw]` |
| Nâng cấp | `python3 patchx upgrade .. -o upgraded`, `optimize .. -o optimized` |
| Gộp | `python3 patchx combo .. --only <năng-lực,...> [--auto] [--recursive] -o <đầu-ra>` |
| Đo | `python3 patchx coverage PATCH CÂY_APK [--method]`, `suggest`, `roadmap .. CÂY_APK -o .` |
| Phân tích | `python3 patchx analyze CÂY_APK`, `diff-apk GỐC MOD [-o out.zip]`, `suggest-apk`, `suggest-llm "ý định" --approve`, `verify-manifest ..` |
| Ngữ nghĩa V2 | `python3 patchx model CÂY [--v2] [--bench]`, `semantic-plan CÂY PLAN [--model MODEL] [--verbose]`, `plan-compile CÂY PLAN_V2 -o DRAFT.json`, `plan-preflight CÂY DRAFT.json [-o DRAFT_MỚI.json]`, `acceptance FIXTURE [-o REPORT.json]`, `knowledge record/query/suggest-plan`, `remote-map CÂY --flow|--dataflow`, `diff-apk GỐC MOD --version-map MAP.json [--semantic-plan-v2 PLAN.json]` |
| CI | `python3 patchx ci KHO [-o ĐẦU_RA] [--quick] [--golden]` — audit → upgrade → optimize → combo-auto → simulate (+ golden gate nếu `--golden`) |
| Baseline | `python3 patchx baseline capture [--full] / show / compare` — chặn hồi quy; `--full` tự chạy test + simulate |
| Áp | `python3 patchx apply PATCH... CÂY_APK` (backup + idempotent, có `--dry-run`) |
| Mô phỏng | `python3 patchx simulate .. -o <đầu-ra> [--dex-runner LỆNH] [--apk CÂY_APK]` |
| APK | `python3 patchx apk-prepare APK -o CÂY` |
| Toolkit | `python3 patchx_toolkit.py doctor / run / package / list / session / apk-plan / apk-test / apk-fix-res / apk-patch / apk-full / apk-runtime / bench-scan / plan-ui / webui / install-deps` |

## Luồng chuẩn

1. `scan` → xem bộ sưu tập có gì.
2. `audit` → phát hiện lỗi kiến trúc từng patch.
3. `upgrade` → chuẩn hóa (metadata đủ, thẻ đóng đủ, bỏ trùng).
4. `optimize` → gộp patch cùng mục tiêu, tách xung đột.
5. `combo --auto` → gộp patch bổ trợ theo HỌ chức năng + class-link.
6. `coverage` / `roadmap` / `apk-plan` → đo trên APK thật, xếp hạng.
7. `apply` → áp lên cây APK đã giải mã.
8. Build → sign → verify (xem bên dưới).

## Build APK thật (đã kiểm chứng thành công)

```sh
# 1. Giải mã
python3 patchx apk-prepare app.apk -o cay-apk
# hoặc dùng cây có sẵn: real_apk_test/app_tree

# 2. Áp patch
python3 patchx apply real_apk_test/p1_test.patch.txt real_apk_test/app_tree

# 3. Chuẩn hóa resource tên chứa `$`
python3 patchx_toolkit.py apk-fix-res real_apk_test/app_tree \
  --output real_apk_test/resource_fix

# 4. Build (bắt buộc trỏ aapt2 thật — wrapper Termux bị lỗi shell)
apktool b real_apk_test/app_tree -o real_apk_test/app_bypass.apk \
  --aapt /data/data/com.termux/files/usr/bin/aapt2

# 5. Zipalign + ký
zipalign -f 4 real_apk_test/app_bypass.apk real_apk_test/app_bypass_aligned.apk
apksigner sign --ks real_apk_test/patchx.keystore \
  --ks-pass pass:patchx123 --key-pass pass:patchx123 \
  --out real_apk_test/app_bypass_signed.apk real_apk_test/app_bypass_aligned.apk

# 6. Xác minh
apksigner verify --verbose real_apk_test/app_bypass_signed.apk
```

## Lỗi đã gặp và cách xử lý

- **aapt2 wrapper Termux** (`aapt2_*.tmp: Syntax error: "(" unexpected`):
  dùng `apktool b --aapt /data/data/com.termux/files/usr/bin/aapt2`.
- **apktool 3.x** không còn `--use-aapt1` → luôn dùng `--aapt <aapt2>`.
- **Resource tên `$`** làm aapt2 báo `has invalid entry name` → chạy
  `apk-fix-res`. Đã sửa tận gốc (Đợt D): `_normalize_resource_names()` đổi
  tên tệp VÀ cập nhật `public.xml` + mọi tham chiếu (đối chiếu theo thân
  tên, thay tên dài trước, bỏ qua `original/`/`.patchx/`).
- **aapt2 2.20 crash build framework-res** (`PrivateAttributeMover.cpp:85
  Check failed: priv_attr_type->entries.empty()` — bug aapt2 với package
  ID 0x01): dùng aapt2 patched x86_64 (từ apktool 2.9.x) chạy qua
  `qemu-user-x86-64`, wrapper tại
  `~/.local/share/patchx/tools/aapt2_patched/aapt2.sh`; toolkit tự retry
  qua `_build_apktool()`/`_find_patched_aapt2()` (apk-test/apk-patch/apk-full).
- **APK lớn (477M/553M)**: đã tối ưu Đợt A — `bench-scan` dùng inventory
  `rg`/hash + cache theo hash cây + literal hint lọc regex (không chạy regex
  Python toàn cây); quét cây 553M đạt **23.557s < 60s**. Trước khi tối ưu,
  dùng `roadmap` hoặc chọn patch mục tiêu.
- **`SignatureHack_arm64.zip` hỏng entry `libfrida-gadget.so`** (lỗi nén):
  thay bằng bản lành từ Modder Hub, sao lưu bản hỏng.
- **Không có gói `zipalign` trong kho Termux main** (`apt-cache search`
  trống): `install-deps` tải prebuilt arm64 từ `rendiix/termux-zipalign`,
  kiểm tra sha256 trước khi cài vào `$PREFIX/bin`; doctor báo đủ khi đã cài.
- **Test phụ thuộc bố cục dữ liệu** → `COLLECTION` trỏ `upgraded/`, test tự
  chứa fixture, không phụ thuộc thư mục ngoài.
- **ADB máy ảo Redfinger**: pairing Wi-Fi qua gateway luôn lỗi
  `protocol fault` (gateway chặn TLS pairing; cổng tự đổi, mở vài chục giây).
  Cách chạy được: cài **Tailscale** cả máy ảo lẫn máy chủ (APK universal ở
  `pkgs.tailscale.com/stable/tailscale-android-universal-<ver>.apk`, cài vào
  máy ảo qua tính năng cài APK của Redfinger) → cùng tailnet →
  `adb connect 100.64.170.99:5555` đạt `state=device`, không cần pairing.
- **Engine tự sửa helper ADD_FILES** (multi-pass MATCH_REPLACE chạy lên chính
  file do patch thêm → `com/anymy/reflection.getPackageInfo` tự gọi chính nó
  → StackOverflowError lúc chạy, M2=False): đã sửa tại `patchx_core/engine.py`
  (`_added_this_patch` loại trừ file ADD_FILES khỏi MATCH của cùng patch),
  test hồi quy `test_add_files_khong_tu_sua`.
- **MATCH_REPLACE hook nhầm helper của patch TRƯỚC (Đợt F)**: patch
  `patch_bypass_sigcheck_with_reflection` quét `smali*/*.smali` và đổi cả
  nhánh fallback `iget-object ... signatures` bên trong `Fix.smali` (do patch
  trước ADD_FILES) thành lời gọi đệ quy `Fix.getSignatures` → mọi gói khác
  bị StackOverflow, tiến trình phụ AppMetrica chết lặp. Đã sửa: thêm
  `_added_files_all` (theo lượt chạy, không reset theo patch) + `_is_injected()`
  loại trừ ở `_match_replace`/`_match_assign`/`_match_present`; test
  `test_match_replace_khong_quet_file_them_truoc`.
- **Placeholder `%RSA_DATA%` chưa thay (Đợt F)**: `Fix.smali` dựng cert giả
  từ hex DER; giữ nguyên `%RSA_DATA%` → `BigInteger` ném lỗi bị try/catch
  nuốt (spoof chữ ký chết lặng). Cách xử lý: engine đọc biến môi trường
  `PATCHX_RSA_DATA` (cert DER hex APK gốc) thay vào khi ghi ADD_FILES/
  REPLACE_FILES (`_expand_rsa_placeholders`); `apk-full` TỰ trích cert v1 qua
  `_extract_apk_cert_hex()`/`_pkcs7_first_cert_hex()` (DER parser thuần
  Python, kiểm chứng bằng `CertificateFactory` Java) rồi đặt biến trước apply.
  Chú ý: cert phải là SEQUENCE đầy đủ (có phần chữ ký), không chỉ phần thân —
  dùng `keytool -printcert` để nghiệm thu. Test: `test_add_files_placeholder_rsa`,
  `test_extract_apk_cert_hex`.
- **Apktool tái dùng DEX dở dang + method_ids 64K (ZAZ 2026-08-17)**:
  cây ZAZ gốc có `classes.dex`/`classes3.dex` đúng 65536 method_ids; patch
  reflection thêm method ref → smali writer báo `Unsigned short value out of
  range`, build chết giữa chừng để `classes.dex` header zero. Nếu retry mà
  không xoá `tree/build`, apktool báo `smali has not changed` và đóng gói
  DEX hỏng. Đã sửa: `_build_apktool()` xoá `tree/build` trước mỗi build/retry;
  tách 60% file nặng của `smali`→`smali_classes6` và
  `smali_classes3`→`smali_classes7` để có 7 DEX hợp lệ; thêm hồi quy
  `F-DEX-002` + `test_failure_dex_cache_p15`.
- **`reflection.smali` NPE lúc `Application.attachBaseContext`**:
  `getPackageInfo()` gọi `getContext().getPackageName()` khi
  `ActivityThread.currentApplication()` còn null → crash lúc khởi động.
  Đã sửa bản patch trong `upgraded/`: thay bằng
  `const-string v2, "%PACKAGE_NAME%"` (engine tự thay package thật qua
  `_expand_package_placeholders`). APK ZAZ reflection-only M2/M3 PASS.
- **Cây apk_trees cũ ô nhiễm** (`smali/smali/...` → apktool "class has
  already been interned"): xóa cây, để `apk-full` giải mã lại từ APK gốc.
- **`apk-runtime` trên máy ảo spam log**: đọc logcat bằng `errors="replace"`;
  `logcat -c` trước launch; mặc định `--logcat-lines 2000` (200 bị trôi dòng
  `Displayed`, làm M3=false dù app hiển thị bình thường).

## Trạng thái hiện tại (mốc đo được)

- Test: **146/146 đạt** (mức nhẹ; golden đầy đủ kèm build framework-res
  110/110, chạy bằng `PATCHX_GOLDEN_FW=1 python3 tests/run_tests.py`);
  selfcheck: 8/8 module, 60 patch, 0 lỗi; full pipeline `run`: 12/12.
- Test (Đợt E+F, 2026-08-16): **155/155 đạt** (thêm: lọc mẫu suy biến,
  placeholder `%PACKAGE_NAME%`, MATCH_REPLACE xuyên patch, placeholder
  `%RSA_DATA%`, trích cert APK).
- Test + nghiệm thu đề xuất thống nhất (2026-08-17): **345/345 đạt**;
  `baseline capture --full`: `test_pass=345/345`, `simulate_pass=51/60`,
  `golden_build_pass=14/14`, `errors=0`; `patchx golden --fw` **14/14 PASS**
  (mini_app + framework-res); `patchx ci upgraded` **85% đạt / 35,4s** (< 50s);
  `ci --quick` **93% đạt / 12,9s**.
  Lệnh mới: `patchx golden`, `baseline capture --full`, `ci --golden`; Web UI
  thêm tác vụ `bc_golden`/`bc_learn`.
- Tầng ngữ nghĩa V2 (2026-08-17, theo `de xuat phuong an/đề xuất.txt`): đã
  hiện thực lát cắt đầu tiên — `patchx model --v2` (`patchx.app-model/v2`),
  `semantic-plan` V2 với verdict `READY_FOR_PREFLIGHT` / `AMBIGUOUS_TARGET` /
  `INSUFFICIENT_EVIDENCE` / `NO_CONFIDENT_TARGET`, `plan-compile` +
  `plan-preflight` (draft `DRAFT_REQUIRES_APPROVAL`, không gọi `apply`),
  `knowledge` V2, `diff-apk --version-map/--semantic-plan-v2`. V1 và
  `upgraded/` giữ nguyên làm tầng tương thích. Chi tiết:
  `TRANG_THAI_HIEN_TAI.md` mục 10.
- Evidence report V2 (2026-08-17): `semantic-plan --verbose` in cả ứng viên
  bị loại kèm điều kiện còn thiếu; failure DB thêm `F-SEM-001..004` cho
  `AMBIGUOUS_TARGET`, `INSUFFICIENT_EVIDENCE`, draft stale và
  `NO_CONFIDENT_TARGET`.
- Selector V2 quan hệ (2026-08-17): hỗ trợ thêm `requires_caller` và
  `requires_field_write`; `model --v2 --bench` đo cache lạnh không ghi JSON.
  Benchmark `apk_trees/zaz` 540M: **169,161s**, 201.495 method, 912.805 cạnh
  gọi, 64.598 điểm quyết định, 4.519 method từ entry.
- Decision-flow + data-flow V2 (2026-08-17): `remote-map CÂY --flow` dựng
  `patchx.decision-flow/v1` (source/transform/decision/sink + đường tới sink);
  `remote-map CÂY --dataflow` dựng `patchx.data-flow/v1` với `primary_role`,
  `roles`, `data_type`, `confidence` và đường decision → sink;
  `knowledge suggest-plan CÂY -o PLAN.json` sinh semantic-plan/V2 tham chiếu
  từ kho tri thức, `recommendation_only=true`, không tự chọn target.
- Nghiệm thu + học từ selector thất bại (2026-08-17): `acceptance FIXTURE`
  đo tái lập model 100%, tái nhận diện 100%, READY đúng, dương tính giả 0%,
  mơ hồ/không tự tin bị chặn 100%; `semantic-plan --verbose` in gợi ý siết/nới
  selector cho `AMBIGUOUS_TARGET`/`NO_CONFIDENT_TARGET`.
- Plan-preflight (2026-08-17): khi hash cây thay đổi sẽ tự đánh giá lại plan
  V2; nếu vẫn `READY_FOR_PREFLIGHT` thì sinh draft mới (`-o` để ghi), nếu mơ
  hồ/không đủ bằng chứng thì `BLOCKED` và yêu cầu người dùng sửa selector.
- An toàn thực thi V2 (2026-08-17): test chuyên biệt monkeypatch
  `Engine.apply`/`apply_many` rồi chạy model/plan/compile/preflight/map/
  acceptance — khẳng định **0 lần** gọi apply.
- Runtime M2/M3 (2026-08-17): `apk-runtime` đã hỗ trợ `.apks`/split APK
  (tự giải nén + `adb install-multiple`) và fallback `dumpsys activity
  activities` khi logcat bị spam làm trôi dòng `Displayed`. Đã PASS trên
  Pixel 7: KISS, Hi Translate split bundle, HiDich (xem
  `toolkit_out/M2M3_TOAN_CANH_20260817.md`).
- Simulate `upgraded/`: **51 ĐẠT / 0 THẤT-BẠI / 9 BỎ-QUA / 0 LỖI**, 100%
  idempotent.
- Optimize: 60 → 12 tệp, gộp trùng 19 khối, tách 20 xung đột.
- Combo: 76 combo chính + 13 combo tự phát hiện (25/25 combo auto áp thành
  công, idempotent, engine multi-pass 3 lượt).
- Quét APK lớn (Đợt A): **đạt mốc < 60s** — `bench-scan` cây 553M
  (43.629 tệp text) = **23.557s** (60 patch / 13.604 rule; khớp 6.870,
  lọc hint 5.980, ước lượng mẫu 41); cache nạp ~0s.
- Rebuild APK thật: **thành công** — APK 75M ký v2/v3 hợp lệ; `apk-patch`
  KISS launcher 2.3M ký OK (`apks_patch/`).
- `apk-full` end-to-end: **hoàn tất + nghiệm thu ĐẠT** — cây KISS sạch, top 3
  tự chọn, apply 0 lỗi, build OK, ký v1/v2/v3 hợp lệ, APK 2.3M + báo cáo
  `apk_full_report.json/md` (kèm inventory/candidates/bypass_plan/apply/build/
  verify). Đã sửa lỗi engine `ADD_FILES` EXTRACT lặp tiền tố `smali/smali`
  (có test hồi quy).
- Runtime verify (Đợt C): **HOÀN TẤT + NGHIỆM THU ĐẠT** (2026-08-16) —
  `apk-runtime` trên máy ảo Redfinger qua Tailscale
  (`adb connect 100.64.170.99:5555`): APK KISS rebuild từ gốc, apply 3013
  thay đổi, **M2=True M3=True** (expect `Displayed fr.neamar.kiss/.MainActivity`,
  forbid `FATAL EXCEPTION`/`ANR`), 0 crash — xem
  `real_apk_test/runtime_redfinger_v3/runtime_report.md`. Đã sửa bug engine
  tự-sửa helper ADD_FILES + 3 cải tiến `apk-runtime` (errors replace,
  `logcat -c`, `--logcat-lines 2000`).
- Đợt E — CI chính thức (2026-08-16): `patchx ci upgraded` → 60 file, audit
  0 lỗi, optimize 60→12, 13 combo auto, simulate 51 ĐẠT/0 THẤT-BẠI/9 BỎ-QUA/
  0 LỖI (85%); dọn 5 cache cũ `scan_*.json`; lọc mẫu suy biến (`.`, `.+`,
  `.*`, `(.+)`) khỏi đo coverage → `bench-scan` 477M: 13.604→7.102 rule,
  khớp 6.870→368, **22.9s < 60s**.
- Đợt F — Thực chiến APK Screen Translation_3.1.2 (122M, cây 993M)
  (2026-08-16): `apk-full` chọn 2 patch (Debug_information_and_hack_signature
  + patch_bypass_sigcheck_with_reflection), apply 53.760 thay đổi; sửa 3 bug
  thật (placeholder `%PACKAGE_NAME%` → StackOverflow; attribute SDK 33+
  `enableOnBackInvokedCallback` → auto-fix manifest; MATCH_REPLACE xuyên
  patch hook nhầm Fix.smali) + placeholder `%RSA_DATA%` (cert gốc APK);
  **runtime trên máy ảo: M2=True** — cài OK, `Displayed` SplashActivity rồi
  sang StartLikeProActivity, pid sống, 0 crash main + 0 subprocess, log
  `fix: new:` trả đúng cert gốc (serial `936EACBE07F201DF`). APK:
  `toolkit_out/apk_full_screen/screen_fixed4_signed.apk` (123M, ký v1/v2/v3).
- Golden tests (Đợt D): **HOÀN TẤT + NGHIỆM THU ĐẠT** (2026-08-16) —
  `test_golden_rebuild` (mini_app.apk, verify v1/v2/v3) +
  `test_golden_framework_res` (framework-res.apk 37.9M: decode → apk-fix-res
  → build bằng aapt2 patched → zipalign → sign → verify v3). Suite
  **110/110**; nghiệm thu đầy đủ: `PATCHX_GOLDEN_FW=1 python3
  tests/run_tests.py`.
- 6 khối thực thi hiện đại hoàn tất: `SET_BOOL`, `INIT`, `HOOK_SCRIPT`,
  `TRACE`, `API_LOG`, `REMOTE_CONFIG`.
- Hệ nhận diện năng lực: 16 cũ + 6 mới (purchase, root-hide, ssl-pinning,
  anti-debug, frida-hide, emulator) — xem `CAP_LABELS` trong
  `patchx_core/optimizer.py`; cách làm/công cụ trong `CAP_TOOLING`
  (`patchx_core/bypass_advisor.py`).
- Web UI: 6 tab theo mục tiêu nghiệp vụ (Vượt chặn / Chỉnh sửa / Hook /
  Quy trình / Kho) — cấu trúc `GOALS` + `TASKS` trong `webui/static/app.js`.
- Trục T1–T7 (`UPGRADE_PLAN_V3.md`): **HOÀN TẤT** (2026-08-16) —
  `smali_sem.py`+`analyze`, `diffapk.py`+`REPLACE_FILES` (tái sinh 100%),
  runtime verify mạng+chữ ký (M2/M3 đạt), `learn.py`+`suggest-apk/llm`,
  `verify-manifest`+`risk.py`+sandbox dex, `smali_lib` modern helpers,
  dashboard `report --apk` + `patchx ci`. Chi tiết
  `TRANG_THAI_HIEN_TAI.md` mục 12.
- ZAZ reflection-only (2026-08-17): **M2_PASS / M3_PASS** — cây
  `apk_trees/zaz` sạch, chỉ áp `patch_bypass_sigcheck_with_reflection`,
  sửa NPE helper, tách 7 DEX, build+ký hợp lệ; APK
  `toolkit_out/zaz_reflect_fix_npe/zaz_patched_20260817-131626.apk`,
  runtime `toolkit_out/zaz_reflect_fix_npe/runtime_m3/runtime_report.json`
  (WelcomeActivity→MainActivity, 0 crash/ANR).
- Máy ảo Termux (worker tạm thời): đã cài Termux từ
  `/storage/emulated/0/Download/termux_0._signed_sign.apk` (bootstrap
  offline) + `openssh` (sshd 8022, key `~/.ssh/vm_key`) + `apktool 3.0.3` +
  `openjdk-21` + `python` + `apksigner` + `git`; **build + ký APK trên VM
  thành công**. Công cụ điều khiển `tools/vm_worker.py` chỉ dùng TẠM THỜI
  cho đợt máy ảo — không phải phần chính của toolkit, khi xong việc sẽ bỏ.

## Việc tiếp theo (ưu tiên)

0. Mở rộng fixture obfuscation + test âm cho selector: đổi tên class/method,
   đổi thanh ghi, chèn `.line`, thay đổi vô nghĩa; đo `model --v2` cache lạnh
   trên cây APK 477–553M và ghi số thật (chưa tối ưu riêng).
1. ~~Bổ sung test an toàn thực thi: khẳng định plan V2 tự gọi `apply` = 0 lần
   trên toàn bộ lệnh V2.~~ **Đã xong**: `test_v2_never_calls_apply`, suite
   **345/345**.
2. Chỉ đưa V2 vào đường mặc định/Web UI khi các tiêu chí `acceptance` đạt
   ngưỡng; giữ nguyên `patch.txt`/parser/`upgraded/` làm baseline tương thích.
3. Nối `diff-apk` + `knowledge` vào luồng đề xuất ở giai đoạn kế tiếp; không
   để plan V2 tự gọi `apply`.
4. Tiếp tục mở rộng `bypass_plus/` theo nguồn công khai (Frida/objection/
   MASTG, Lucky Patcher, MT Manager) và nghiệm thu trên APK thật qua
   `apk-full`.
5. Khi áp patch hack signature cho APK mới: `apk-full` tự nạp `PATCHX_RSA_DATA`;
   nếu áp thủ công `patchx apply`, đặt biến `PATCHX_RSA_DATA=$(python3 -c
   '...trích hex...')`.

## Tài liệu tham chiếu (đọc khi cần chi tiết)

- `QUY_TRINH.md` — vận hành đầy đủ + lỗi đã gặp.
- `NGU_CANH.md` — ngữ cảnh, lịch sử yêu cầu, trạng thái dự án.
- `KINH_NGHIEM.md` — bài học từ chạy APK thật, hướng phát triển/bỏ.
- `UPGRADE_PLAN_V4.md` — kiến trúc 6 tầng + lộ trình `apk-full`.
- `UPGRADE_PLAN_V3.md` — trục nâng cấp T1–T7 + ma trận yêu cầu.
- `EVALUATION.md` — mức đạt theo nhu cầu + bằng chứng đo được.
- `UPGRADE_PROPOSAL.md` — đề xuất đợt 2, lỗi phát sinh, tiêu chí nghiệm thu.
- `README.md` — toàn bộ lệnh + ví dụ + kiến trúc module.
- `UI_TOOLKIT_ANDROID.md` — nghiên cứu nguồn UI toolkit + thiết kế giao diện toàn bộ patchx trên Android.
