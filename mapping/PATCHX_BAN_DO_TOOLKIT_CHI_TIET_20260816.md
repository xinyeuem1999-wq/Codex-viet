# BẢN ĐỒ CHI TIẾT TOÀN BỘ TOOLKIT PATCHX (từng thư mục — từng tệp)

- Ngày: **2026-08-16 22:00**. Thư mục gốc: `/storage/emulated/0/Patch/patch1/_patchx`.
- Tổng quan: 26 thư mục con; tổng ~465.000 tệp (phần lớn là cây giải mã APK lớn).
- Quy ước: tên tệp/lệnh giữ nguyên gốc; mô tả tiếng Việt.

---

## 1. TỆP GỐC (root — 25 tệp)

| Tệp | Dung lượng | Vai trò |
|---|---|---|
| `patchx` | 291 B | CLI chính (scan/audit/upgrade/optimize/combo/apply/simulate/coverage/roadmap/apk-prepare…) |
| `patchx_toolkit.py` | 149 KB | Orchestrator: doctor/run/package/list/session/apk-plan/apk-test/apk-patch/apk-full/apk-runtime/install-deps/bench-scan |
| `AGENTS.md` | 17 KB | Hướng dẫn tối ưu cho mọi phiên Codex (quy ước, lệnh, lỗi đã gặp, trạng thái) |
| `README.md` | 16 KB | Toàn bộ lệnh + ví dụ + kiến trúc module |
| `NGU_CANH.md` | 16 KB | Ngữ cảnh, lịch sử yêu cầu, trạng thái dự án |
| `TRANG_THAI_HIEN_TAI.md` | 12 KB | **Bản master trạng thái hiện tại** (3 máy, cấu trúc, bản đồ tài nguyên, phát đồ, việc dở) |
| `UPGRADE_PLAN_V3.md` | 12 KB | Trục nâng cấp T1–T7 + phương án P1–P5 + thang M0–M3 |
| `UPGRADE_PLAN_V4.md` | 4 KB | Sáu tầng thống nhất T1–T6 + đợt A–D |
| `UPGRADE_PROPOSAL.md` | 8 KB | Đề xuất đợt 2, lỗi phát sinh, tiêu chí nghiệm thu |
| `UI_TOOLKIT_ANDROID.md` | 13 KB | Thiết kế UI toolkit cho Android |
| `EVALUATION.md` | 6 KB | Mức đạt theo nhu cầu + bằng chứng đo được |
| `QUY_TRINH.md` | 6 KB | Vận hành đầy đủ + lỗi đã gặp |
| `KINH_NGHIEM.md` | 11 KB | Bài học từ chạy APK thật, hướng phát triển/bỏ |
| `MANIFEST.json` | 1 KB | Chuẩn hash toàn kho (SLSA-lite) |
| `patchx_index.json` | 85 KB | Index bộ sưu tập patch |
| `patchx_report.md` | 4 KB | Báo cáo quét bộ sưu tập |
| `roadmap.json` + `roadmap.md` | 59+15 KB | Lộ trình mod theo bộ sưu tập |
| `simulation.json` + `simulation_report.md` | 17+4 KB | Mô phỏng toàn bộ (51 ĐẠT/0 LỖI) |
| `audit.json` + `audit_report.md` | 1.7+0.9 KB | Kiểm tra kiến trúc patch |
| `dupes.json` + `dupes_report.md` | 1+1 KB | Tệp trùng theo hash |
| `combos_success.json` | 13 KB | Kho combo thành công (P19 học mẫu) |
| `danhsach.txt` | 4 KB | Danh sách công việc tham chiếu |
| `a.zip` | 68 KB | ZIP thử nghiệm |

## 2. `patchx_core/` — 27 module lõi (+ __pycache__)

| Module | Vai trò |
|---|---|
| `cli.py` | Giao diện dòng lệnh patchx, toàn bộ thông báo tiếng Việt |
| `model.py` | Mô hình dữ liệu: Section (khối lệnh) + Patch (tệp patch) |
| `parser.py` | Phân tích cú pháp patch.txt, xử lý biến thể thực tế |
| `engine.py` | Động cơ áp patch: glob target, transaction, idempotent, fixpoint, provenance |
| `audit.py` | Kiểm tra kiến trúc patch + nâng cấp tự động an toàn |
| `optimizer.py` | Gộp/dedupe/phát hiện xung đột + kết xuất patch chuẩn |
| `combo.py` | Gộp combo — patch hỗ trợ nhau thành combo tối ưu |
| `complement.py` | Tự phát hiện patch bổ trợ (phiên bản 2 — theo họ thực tế) |
| `indexer.py` | Quét bộ sưu tập → index.json + báo cáo Markdown |
| `advisor.py` | Cố vấn: tìm nhanh/sâu, đề xuất cải tiến, xây lộ trình mod (coverage nhanh rg/hash/cache) |
| `bypass_advisor.py` | Bypass Advisor: dữ liệu quét → báo cáo triển khai + tỷ lệ thành công % |
| `simulate.py` | Mô phỏng "code hiểu code" — tự sinh văn bản mẫu kiểm tra regex |
| `session.py` | Quản lý phiên chạy patch người dùng chọn |
| `learn.py` | P19 — học + đề xuất: kho combo thành công, gợi ý theo danh mục, khung LLM |
| `risk.py` | P5 — cờ rủi ro chuỗi cung ứng (hành vi nguy hiểm trong patch) |
| `preflight.py` | P7 — Preflight Engine: cổng kiểm tra TRƯỚC khi áp patch |
| `dex_budget.py` | P5/P6 — DEX Resource Manager + Strategy (5 mức SAFE→BLOCK) |
| `smali_lib.py` | Thư viện tiện ích smali dùng chung (bump register, chèn invoke…) |
| `smali_sem.py` | T1 — phân tích ngữ nghĩa smali (parser method-level) |
| `smali_validate.py` | P9 — xác thực cấu trúc smali (validate_tree_v2, 4 mức) |
| `baseline.py` | P0 — Baseline & đo lường (metrics.json, so sánh hồi quy) |
| `failure_db.py` | P15 — Failure Intelligence: DB lỗi ERROR_ID + sinh regression test |
| `fuzz.py` | P12 — Fuzz/Chaos: 5 invariant, tấn công parser + engine |
| `runtime_scenario.py` | P14 — Runtime M3 scenario engine (launch/tap/swipe/assert/screenshot) |
| `diffapk.py` | T2 — diff-apk: sinh patch từ khác biệt 2 APK |
| `remote_map.py` | Bản đồ flag điều khiển hành vi từ xa (remote_map) |
| `__init__.py` | Khởi tạo gói patchx |

## 3. `webui/` — Web UI (5 tệp + logs)

| Tệp | Vai trò |
|---|---|
| `server.py` | HTTP server cổng 8787: `/api/state`, `/api/plan`, `/api/tree`, `/api/file`, `/api/search`, `/api/manual_save`… |
| `static/index.html` | Giao diện chính (6 tab nghiệp vụ, việt hoá thuần) |
| `static/app.js` | Logic UI: chip mục tiêu, plan, combo, bypass report, manual mode |
| `static/style.css` | Giao diện tối, tối ưu hiển thị điện thoại |
| `logs/` | smoke_test.log, smoke3.log, worklist_test.log |

## 4. `tests/` — Kiểm thử (15 tệp)

| Tệp | Vai trò |
|---|---|
| `run_tests.py` | 307 bài kiểm thử T0–T3 (main + Pixel 7: 307/307) |
| `fixtures/mini_app.apk` + `.idsig` | APK mẫu nhỏ cho golden rebuild |
| `fixtures/golden/` | Mẫu golden so khớp (reflection_getPackageInfo.golden…) |
| `fixtures/test.keystore` | Keystore test (pass patchx123) |

## 5. `tools/` — Công cụ phụ trợ (4 tệp)

| Tệp | Vai trò |
|---|---|
| `bell.sh` | Phát chuông thông báo hoàn thành |
| `bench_dex64k.py` | Benchmark DEX 64K method refs |
| `vm_worker.py` | Worker máy ảo (decode/build/sign) |

## 6. `Apks/` — APK đầu vào (3 tệp)

| Tệp | Dung lượng | Vai trò |
|---|---|---|
| `app.apk` | 71 MB | **APK mục tiêu** com.zaz.translate 6.0.9.005.gp |
| `Screen Translation_3.1.2.apk` | 121 MB | APK dịch màn hình |
| `MT Manager_2.14.5-clone.apk` | 23 MB | APK quản lý MT |

## 7. `upgraded/` — 61 patch chuẩn hoá (bộ nguồn chính)

Nhóm theo chức năng (đủ 61 tệp):
- **Quảng cáo/phân tích**: New. Metrics…Inok_ZP, disable_google_analytics, Anti_analytics2 (+ _22-41-11), New. Removing the analytic…, Yandex_Metrica (1 + bản thường + by Vergil777), GooglePlayServices (Edik1d + HTC600), NoPlayGames
- **Chữ ký/license**: BinSignatureHack_with_htc, Bin_sig&installer_fix[Amazon], Bin_sig&installer_fix[Google], SignatureHack_arm64, SignatureHack_armv7, License_hack (+ Amazon + v2), patch_bypass_sigcheck, patch_bypass_sigcheck_with_reflection, IsPremium, accounts_hack
- **Vị trí/giả mạo**: FakeGPS, FakeGpsAutoGenerate, FakeIP, MockLocation, NoLocation
- **Quyền**: Permission_calendar, Permission_camera, Permission_location, Permission_phone, Permission_readContact, Permission_readSMS, permission_memory
- **Ngôn ngữ/dịch**: Commenting on untranslated lines, Dictionary+ru+uk+2, Language substitution, Only Ru, Unicode text, UnicodeToUTF, Wrap non-translated strings, delete_languages, patch_delete_translation_raw-values_xxx, patch_remove_translation, res_raw_TRANSLATIONxx, translate_debugger, translate_obfuscation
- **Debug/info**: Debug_information, Debug_information_and_hack_signature, AddSave Debug_Information Toast, Decoder_ID_Resource
- **Hook/vận hành**: Inject_Hook_Remote_Data_Control, Activator, Anonymous[Auto_Generate], DexExtractor, DisableBillingService, Password_login_english, AUTH_VK_AND_FB, RES-ID, RES-ID (t1046)

## 8. `combos/` — 76 combo chính (tệp .patch)

- Bypass-Google+Check-Toàn-Vẹn (_1→_6) · Bypass-VIP-License+Bypass-Google (_1→_5)
- Bypass-VIP-License+Check-Toàn-Vẹn (_1→_6) · Bypass-VIP-License+Mod-Shell+Check-Toàn-Vẹn (_1→_7)
- Bypass-VIP-License+Mod-Shell (_1→_5) · Bypass-VIP-License+Quét-Token (_1→_4)
- Check-Toàn-Vẹn+Mod-Shell (_1→_7) · Chặn-Quảng-Cáo+Mạng · Chặn-Quảng-Cáo+Ẩn-Danh (_1→_2)
- Cài-Đặt+Mod-Shell (_1→_6) · Mod-Shell+Quét-Token (_1→_4) · Mod-Shell+Truy-Vết-Dữ-Liệu (_1→_4)
- Quét-Token+Truy-Vết-Dữ-Liệu · Truy-Vết-Dữ-Liệu+Tìm-API+Quét-Token+Check-Toàn-Vẹn (_1→_6)
- Tìm-API+Mod-Shell (_1→_4) · Tìm-API+Quét-Token · Tìm-API+Truy-Vết-Dữ-Liệu
- Ẩn-Danh+Mạng (_1→_2) · Ẩn-Danh+Spoof-ID (_1→_2) + `_combos.json`, `combos_report.md`

## 9. `combos_auto/` — 15 combo tự phát hiện

`api.patch`, `google_1.patch`, `license.patch`, `quyền_1.patch`, `shell.patch`,
`signature_1→_5.patch`, `trace.patch`, `ẩn danh_1→_2.patch`,
`_auto_combos.json`, `auto_combos_report.md`

## 10. `combos_auto_plus/` — 6 combo năng lực mới

`Gỡ-SSL-Pinning.patch`, `Ẩn-Root-Giả-Lập.patch`,
`Ẩn-Root-Giả-Lập+Gỡ-SSL-Pinning+Chống-Debug+Ẩn-Frida+Bỏ-Kiểm-Tra-Máy-Ảo+Giả-Lập-Mua-Hàng.patch`
(+ bản thêm Check-Toàn-Vẹn), `_combos.json`, `combos_report.md`

## 11. `bypass_plus/` — 13 mẫu bypass nâng cao

`anti_debug_off`, `anti_tamper_signature_off`, `emulator_check_off`,
`emulator_fingerprint_off`, `frida_detect_off`, `iap_fake`,
`iap_purchase_state`, `integrity_verdict_off`, `pro_unlock_vip`
(+ legacy-backup), `root_check_off`, `root_su_binary_off`, `ssl_pinning_off`

## 12. `optimized/` — 14 tệp patch tối ưu

`Khác.patch` (_2→_6), `Lưu-trữ.patch`, `Mạng.patch`, `Tiện-ích.patch` (_2→_4),
`_conflicts.json`, `_stats.json`

## 13. `hook_remote_data_control/` — Hook điều khiển thu thập từ xa

| Tệp | Vai trò |
|---|---|
| `patch.txt` | Patch chèn hook (Inject_Hook_Remote_Data_Control) |
| `DataGuard.smali` | Class giám sát dữ liệu (guard dữ liệu trước khi gửi) |

## 14. `apk_trees/` — 6 cây giải mã (286.170 tệp, 3.2G)

| Cây | Ngày | Trạng thái |
|---|---|---|
| `app` | 14:42 | Cây zaz **đã patch** (477M) — build cũ hỏng DEX |
| `app_clean` | 12:10 | Cây zaz đã patch (bản sạch hơn) |
| `zaz` | 20:39 | Cây zaz **sạch + đã áp reflection patch** (đang xử lý M2/M3) |
| `KISS launcher_3.26.0` | 02:16 | Cây KISS (M2/M3 ĐẠT) |
| `Screen Translation_3.1.2` | 04:55 | Cây dịch màn hình |
| (thư mục tên trống) | 06:26 | Cây phụ |

Mỗi cây gồm: `AndroidManifest.xml`, `apktool.yml`, `assets/`, `lib/`,
`res/`, `smali/…smali_classes7/`, `original/`, `unknown/`, `build/` (khi đã build).

## 15. `real_apk_test/` — APK thật + nghiệm thu (93.510 tệp, 1.6G)

| Tệp/Thư mục | Vai trò |
|---|---|
| `app_tree` (477M) | Cây APK thật để đo tốc độ quét |
| `app_bypass.apk` → `_aligned` → `_signed` | APK zaz đã patch/ký (78 MB, v2/v3 OK) |
| `patchx.keystore` | Keystore ký (pass patchx123) |
| `kiss.apk` | APK KISS launcher 2.2 MB (đã ký) |
| `apk_full_dry/v1/v2/v3` | Kết quả pipeline apk-full từng đợt |
| `bench_477M_v2/v3/v4` | Benchmark quét 477M |
| `kiss_tree_clean`, `kiss_trace_tree/out`, `zaz_trace_tree/out` | Cây + trace hook |
| `resource_fix` | Cây sau apk-fix-res |
| `bypass_session`, `hook_input` | Phiên bypass + dữ liệu hook |
| `improvements/1/2/3` | Bài tập cải thiện từ lỗi |
| `runtime_check`, `runtime_redfinger`, `runtime_redfinger_v3`, `runtime_scan` | Kết quả runtime verify |
| `p1_test.patch.txt`, `zaz_force.zip` | Patch thử nghiệm |

## 16. `toolkit_out/` — Kết quả pipeline (84.906 tệp, 2.7G)

| Mục | Vai trò |
|---|---|
| `apk_full_zaz/` | **Pipeline zaz**: bypass_plan.json, apply_report, build_report (fail), apk_full_signed.apk (66MB, DEX hỏng), runtime_report (M2 FAIL) |
| `apk_full_screen/` | Pipeline Screen Translation |
| `apk_plan_zaz_pro/`, `zaz_pro_tree/` | Plan nâng cao + cây zaz pro |
| `cache/` | Cache scan theo hash APK (`scan_*.json`) |
| `scan.json`, `report.html`, `simulation.json/md`, `toolkit_report.json/md` | Báo cáo tổng |
| `audit/`, `combos/`, `dupes/`, `optimized/`, `upgraded/` | Kết quả từng bước |
| `bench_e_baseline/`, `ci_baseline/` | Baseline đo tốc độ + CI |
| `screens/` | Ảnh chụp màn hình nghiệm thu |

## 17. Dữ liệu đo & môi trường

| Thư mục | Vai trò |
|---|---|
| `baseline/` | `metrics.json` + `environment.json` (P0 baseline) |
| `benchmarks/` | `bench_dex64k_s26.json` (64K DEX ĐẠT) |
| `bench_out/` | `bench_report.json/md` |
| `scenarios/` | `kiss_m3.json` — kịch bản M3 (12 bước) |
| `simulation_plus/` | Mô phỏng mở rộng (json + report) |

## 18. Đóng gói & phụ trợ

| Thư mục | Vai trò |
|---|---|
| `dist/` | 3 bản phân phối: patchx-toolkit-9/10/11-*.zip (~11 MB mỗi bản) |
| `demo-apk/` | APK demo (AndroidManifest + smali) cho test nhanh |
| `backup/` | `deleted_originals_*.json`, `upgraded_old/pre_*`, `SignatureHack_arm64.zip.bak` (bản hỏng) |
| `apks_patch/` | APK đã patch: `KISS launcher_3.26.0_patched_*.apk` + report |
| `apk_full_out/` | Kết quả apk-full test (inventory/candidates/bypass_plan/report) |
| `termux_patches/` | `fix_termux_windowed_jitter.patch.txt` |
| `de xuat phuong an/` | 9 tài liệu đề xuất (dexuat1/v2, dexuat2/v2, dexuat_v3, DE_XUAT_THONG_NHAT, MA_TRAN_PHASE, PHAT_DO_CHI_TIET_TOAN_BO, CACH_DOC_KY_HIEU_PHAT_DO) |

## 19. KHỐI NGOÀI TOOLKIT (`/storage/emulated/0/Patch/patch1/`)

| Tệp/Thư mục | Vai trò |
|---|---|
| `mau.csv` | **Danh sách công việc 3 nhân viên AI** (10 mục, báo cáo xong ngay trong danh sách) |
| `worklist_ui/` | UI giám sát danh sách (server.py cổng 8799 + index.html) — KHÔNG đụng toolkit |
| `NHAT_KY.md` | Nhật ký phiên (tiếng Việt, ghi khi người dùng vắng mặt) |
| `THIET_KE_DANH_SACH.md` | Mục tiêu thiết kế danh sách công việc |
| `RUT_KINH_NGHIEM_DIEU_PHOI.md` | Bài học điều phối 3 máy |
| `DE_XUAT_DONG_BO_3_MAY.md` | Đề xuất tối ưu đồng bộ (PA-1/2/3) |
| `dich.apk` / `dich_sign.apk` | APK dịch + bản ký |
