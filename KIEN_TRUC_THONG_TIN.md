# Bản đồ kiến trúc thông tin dự án `_patchx/`

Ngày quét: 2026-08-16. Số liệu đo trực tiếp từ đĩa.

## Tài liệu định hướng (gốc)
- Tài liệu chính: `AGENTS.md`, `README.md`, `QUY_TRINH.md`, `NGU_CANH.md`, `KINH_NGHIEM.md`, `TRANG_THAI_HIEN_TAI.md`, `EVALUATION.md`, `UPGRADE_PLAN_V3.md`, `UPGRADE_PLAN_V4.md`, `UPGRADE_PROPOSAL.md`, `UI_TOOLKIT_ANDROID.md`.
- Dữ liệu quét/tổng hợp: `MANIFEST.json`, `audit.json`, `audit_report.md`, `dupes.json`, `dupes_report.md`, `patchx_index.json`, `patchx_report.md`, `roadmap.json`, `roadmap.md`, `simulation.json`, `simulation_report.md`, `danhsach.txt`.

## Mã nguồn
- `patchx` — điểm vào CLI.
- `patchx_core/` — 24 module: `parser.py` + `model.py` (phân tích), `engine.py` (áp patch, 6 khối hiện đại SET_BOOL/INIT/HOOK_SCRIPT/TRACE/API_LOG/REMOTE_CONFIG), `audit.py` (15 lớp kiểm tra), `optimizer.py` + `combo.py` (gộp/năng lực), `advisor.py` (coverage/suggest/roadmap), `simulate.py`, `indexer.py`, `cli.py` (26 lệnh con), cùng các module trục mới `smali_sem.py`, `diffapk.py`, `learn.py`, `risk.py`, `smali_validate.py`, `smali_lib.py`, `baseline.py`, `failure_db.py`, `fuzz.py`, `preflight.py`, `dex_budget.py`, `remote_map.py`, `runtime_scenario.py`, `bypass_advisor.py`, `session.py`.
- `patchx_toolkit.py` — CLI lớn (149K): `doctor`, `run`, `package`, `list`, `session`, `bench-scan`, `apk-prepare`, `apk-plan`, `apk-test`, `apk-fix-res`, `apk-patch`, `apk-build`, `apk-debug`, `apk-full`, `apk-runtime`, `plan-ui`, `webui`, `install-deps`.
- `webui/` — `server.py` (API REST + log stream) + `static/` (`app.js`, `index.html`, `style.css`), 6 tab nghiệp vụ.
- `tools/` — phụ trợ: `vm_worker.py` (máy ảo tạm), `bell.sh`, `bench_dex64k.py`.

## Bộ dữ liệu patch
- `upgraded/` — 60 zip chuẩn hóa (nguồn chính).
- `optimized/` — 12 `.patch` gộp tối ưu + 2 tệp JSON/MD.
- `combos/` — 74 `.patch` combo chính + 2 tệp JSON/MD.
- `combos_auto/` — 13 `.patch` tự phát hiện + `_auto_combos.json` + báo cáo.
- `combos_auto_plus/` — 4 `.patch` combo nâng cao + `_combos.json` + báo cáo.
- `bypass_plus/` — 13 zip (ssl pinning, root, emulator, anti-debug, frida, IAP, Play Integrity, pro_unlock, ...).
- Phụ trợ: `hook_remote_data_control/` (DataGuard.smali + patch), `termux_patches/` (fix windowed jitter), `demo-apk/`, `backup/` (bản gốc đã xóa + zip hỏng).

## Dữ liệu APK thực chiến
- `Apks/` — APK gốc chưa sửa: `MT Manager_2.14.5-clone.apk`, `Screen Translation_3.1.2.apk`, `app.apk`.
- `apk_trees/` — 5 cây giải mã (KISS, Screen Translation, app, app_clean, zaz).
- `real_apk_test/` — cây 477M `app_tree`, cây bench `bench_477M_v2/v3/v4`, kết quả `apk_full_v1/v2/v3`, `kiss_tree_clean` + `kiss_trace_tree`, `zaz_trace_tree` + `zaz_trace_out`, `resource_fix`, `runtime_redfinger(_v3)`, keystore `patchx.keystore`, APK đã ký `app_bypass_signed.apk`, `kiss.apk`, patch thử `p1_test.patch.txt`.
- `apks_patch/` — APK patched + `report_*.json`; `apk_full_out/` + `toolkit_out/apk_full_screen/`, `toolkit_out/apk_full_zaz/` — kết quả `apk-full` (báo cáo JSON/MD + APK ký v1/v2/v3).

## Đầu ra pipeline và kiểm thử
- `toolkit_out/` — `toolkit_report.md/json`, `report.html`, `scan.json`, cache `cache/scan_*.json`, `ci_baseline/`, `bench_e_baseline/`, `screens/`, các bản `audit/`, `dupes/`, `combos/`, `optimized/`, `upgraded/`.
- `tests/` — `run_tests.py` + `fixtures/` (`mini_app.apk`, `golden/`, `test.keystore`).
- `benchmarks/` (dex 64K), `scenarios/` (`kiss_m3.json`), `baseline/` (`environment.json`, `metrics.json`).
- Tạm thời: `.tmp_build/`, `.tmp_repro/`, `.tools/aapt2_patched/`, `__pycache__` — không phải phần chính.

## Luồng thông tin tổng thể
`Apks/` → `apk_trees/` (giải mã) → `upgraded/` (chuẩn hóa) → `optimized/` → `combos/` + `combos_auto/` → đo bằng `coverage`/`roadmap`/`apk-plan` → `apply` lên cây → `apk-fix-res` → build/sign/verify → kết quả ở `apks_patch/` + `toolkit_out/`, nghiệm thu runtime qua `apk-runtime`.
