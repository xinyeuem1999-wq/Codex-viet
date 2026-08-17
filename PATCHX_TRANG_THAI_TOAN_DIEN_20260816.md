# TRẠNG THÁI HIỆN TẠI — PATCHX TOOLKIT (BẢN MASTER)

Ngày cập nhật: **2026-08-16 21:45 (Asia/Ho_Chi_Minh)**.
Tài liệu tổng duy nhất: trạng thái 3 máy + cấu trúc toolkit + bản đồ tài
nguyên + phát đồ phát triển + dự án dang dở/chuẩn bị. Đọc tệp này trước, chi
tiết lịch sử xem `QUY_TRINH.md`, `KINH_NGHIEM.md`, `NGU_CANH.md`,
`UPGRADE_PLAN_V3.md`, `UPGRADE_PLAN_V4.md`, `de xuat phuong an/`.

---

## 1. TRẠNG THÁI 3 MÁY (đồng bộ 100%)

| Máy | IP adb | Kiểm thử | Trạng thái | Ghi chú |
|-----|--------|----------|------------|---------|
| **Máy chính** (Termux) | — | **307/307 đạt** | 🟢 Điều phối + giám sát | Toolkit ổn định; `mau.csv` 5/10 mục ✅ |
| **Pixel 7** (Redfinger) | 100.64.170.99:5555 | **307/307 đạt** (0 FAIL) | 🟢 Sẵn sàng test | Đã cài `framework-res.apk` (37.9MB, md5 khớp main); công cụ 8/8 |
| **S26** (Redfinger) | 100.76.244.117:5555 | chưa chạy lại | 🟡 Sẵn sàng | Chưa có `framework-res.apk`; `apk-full` đã dừng (SIGTERM), sạch tiến trình |

- Đồng bộ: `tools/sync_machines.sh` → **md5 8/8 ✓ ĐỒNG BỘ 100%** (patchx,
  patchx_toolkit.py, webui/server.py, webui/static/app.js trên Pixel 7 + S26).
- Danh sách công việc: `mau.csv` + 4 tài liệu md5 giống hệt trên 3 máy
  (thư mục `worklist/` ngoài toolkit trên client).
- SSH: Pixel 7 port 8022 key `~/.ssh/vm_key` (user u0_a85, dir patchx_test);
  S26 port 8022 key `/data/data/com.termux/files/usr/tmp/vm2_key`
  (user u0_a81, dir patchx_s26).

## 2. CẤU TRÚC TOOLKIT

Thư mục gốc: `/storage/emulated/0/Patch/patch1/_patchx`

- `patchx` — CLI chính (scan/audit/upgrade/optimize/combo/coverage/roadmap/
  apply/simulate/apk-prepare...).
- `patchx_toolkit.py` — orchestrator (doctor/run/package/list/session/apk-plan/
  apk-test/apk-fix-res/apk-patch/**apk-full**/**apk-runtime**/install-deps/
  bench-scan).
- `patchx_core/` — 27 module: `advisor` (coverage nhanh rg/hash/cache),
  `bypass_advisor` (báo cáo bypass + tỷ lệ %), `engine` (áp patch), `audit`,
  `optimizer`, `combo`, `preflight`, `smali_lib/smali_sem/smali_validate`
  (ngữ nghĩa smali), `dex_budget`, `diffapk`, `runtime_scenario` (M3),
  `failure_db` (chẩn đoán), `remote_map` (bản đồ điều khiển từ xa), `learn`,
  `session`, `simulate`, `fuzz`, `risk`, `baseline`, `model`, `parser`,
  `cli`, `indexer`, `complement`.
- `webui/` — server.py (cổng 8787) + static (index.html/app.js/style.css):
  6 tab nghiệp vụ **Trang chủ / Vượt chặn / Chỉnh sửa / Hook / Quy trình /
  Kho**, chế độ 🟢/🟡/🔴, bản đồ toolkit, thanh trạng thái 6 tầng, Manual
  Mode, API `/api/state /api/plan /api/tree /api/file /api/search ...`.
- `tests/` — `run_tests.py` (307 bài) + `fixtures/` (golden, keystore test).
- `tools/` — `sync_machines.sh` (đồng bộ 3 máy + md5), `bell.sh`,
  `bench_dex64k.py`, `vm_worker.py`.
- `de xuat phuong an/` — 6 tài liệu đề xuất (xem mục 6).

## 3. BẢN ĐỒ KHỐI TÀI NGUYÊN (mapping)

| Thư mục | Nội dung | Số lượng | Vai trò |
|---------|----------|---------|---------|
| `Apks/` | APK đầu vào gốc | 3 | `app.apk` (zaz 71MB — APK mục tiêu), `Screen Translation_3.1.2.apk` (121MB), `MT Manager_2.14.5-clone.apk` (23MB) |
| `upgraded/` | Patch chuẩn hóa | 61 zip | Nguồn patch chính (60 zip + bổ sung) |
| `combos/` | Combo gộp chính | 76 | Gộp patch theo mục tiêu |
| `combos_auto/` | Combo tự phát hiện | 15 | Theo họ chức năng + class-link |
| `combos_auto_plus/` | Combo năng lực mới | 6 | bypass_plus nâng cao |
| `bypass_plus/` | Mẫu bypass nâng cao | 13 | purchase/root-hide/ssl-pinning/anti-debug/frida-hide/emulator... |
| `optimized/` | Patch tối ưu | 14 | Gộp trùng + tách xung đột |
| `hook_remote_data_control/` | Hook điều khiển thu thập dữ liệu từ xa | 2 tệp | DataGuard.smali + patch.txt |
| `apk_trees/` | Cây giải mã | 6 | `app` (patched, 477M), `app_clean` (patched), `zaz` (sạch + đã áp reflection), `KISS launcher_3.26.0`, `Screen Translation_3.1.2` |
| `real_apk_test/` | APK thật + nghiệm thu | ~20 mục | `app_tree` (477M), `app_bypass_signed.apk` (78MB, ký OK), `kiss.apk`, `patchx.keystore` (pass patchx123), `bench_477M_v2/v3/v4`, `apk_full_v1/v2/v3`, `improvements1/2/3`, `kiss_tree_clean`, `resource_fix` |
| `toolkit_out/` | Kết quả pipeline | ~25 mục | `apk_full_zaz/` (APK ký 66MB + runtime report), `apk_full_screen/`, `apk_plan_zaz_pro/`, `zaz_pro_tree/`, `cache/` (scan theo hash APK), `scan.json`, `simulation_report.md` |
| `baseline/` + `ci_baseline/` | Số đo gốc | 2 + ~ | metrics.json, environment.json — chuẩn so sánh hồi quy |
| `scenarios/` | Kịch bản M3 | 1 | `kiss_m3.json` |
| `simulation_plus/` | Mô phỏng mở rộng | 2 | simulation.json + report |
| `dist/` | Bản phân phối | 3 | patchx-toolkit-9/10/11-*.zip |
| `demo-apk/` | APK demo | 2 | manifest + smali |
| `backup/` | Bản gốc đã xóa | — | deleted_originals_*.json |
| **Ngoài toolkit** | `patch1/` | — | `mau.csv` (danh sách việc 3 AI), `worklist_ui/` (UI 8799), `NHAT_KY.md`, `THIET_KE_DANH_SACH.md`, `RUT_KINH_NGHIEM_DIEU_PHOI.md`, `DE_XUAT_DONG_BO_3_MAY.md` |

## 4. PHÁT ĐỒ PHÁT TRIỂN

### 4.1 Các đợt đã hoàn tất
- **Đợt A** (15/08): tối ưu tốc độ quét APK lớn — 477M/553M **< 60s** (inventory
  9.94s + coverage 13.62s = 23.55s), rg/hash/index + cache theo hash APK.
- **Đợt B** (15/08 23:59): `apk-full` end-to-end (plan → apply → fix-res →
  build → zipalign → sign → verify → report); nghiệm thu KISS OK.
- **Đợt C** (16/08 02:20): `apk-runtime` M2/M3 — KISS launcher **M2=True M3=True**
  trên Pixel 7 (qua Tailscale adb); phát hiện bug thật + sửa.
- **Đợt D** (16/08 03:15): golden tests + `apk-fix-res` + aapt2 patched;
  test **92/92 → 174/174 → 307/307**.
- **T1–T7** (UPGRADE_PLAN_V3): ngữ nghĩa smali, diff-apk, dynamic test, LLM
  suggestion, chuỗi cung ứng, apktool 2.x, CI — đã có khung + module.

### 4.2 Lộ trình PATCHX V2 thống nhất (DE_XUAT_THONG_NHAT.md)
Pipeline 16 bước: APK → SCAN → EVIDENCE → PLAN → PREFLIGHT → TRANSACTION →
APPLY → PROVENANCE → POSTCHECK → VALIDATE → BUILD → SIGN → INSTALL → M2 →
M3 → REPORT. 6 gate (ANALYSIS/PLAN/PREFLIGHT/VALIDATION/BUILD/RUNTIME),
DEX gate 5 mức (<70 SAFE … ≥100 BLOCK), 7 milestone:

- **M0 FOUNDATION**: P0 Baseline + CI + Observability
- **M1 CORE SAFE**: P1–P4 (Contract, Transaction, Ledger, Fixpoint)
- **M2 RESOURCE SAFE**: P5–P8 (DEX Resource Manager, Strategy, Preflight, Gate)
- **M3 BUILD VERIFIED**: P9–P12 (Validation V2, Golden, Test Matrix, Fuzz)
- **M4 RUNTIME VERIFIED**: P13–P15 (Runtime M2, M3 Scenario, Failure Intelligence)
- **M5 INTELLIGENT**: P16–P19 (Scanner V2, Simulation, Plan Engine, LLM)
- **M6 PRODUCT/SCALE**: P20–P21 (Performance, Workflow UI)

### 4.3 Sáu tầng thống nhất (UPGRADE_PLAN_V4)
T1 Inventory → T2 Candidate → T3 Plan → T4 Apply → T5 Build → T6 Verify.
`apk-full` = tự động hoá toàn dây chuyền (đã xây xong khung, còn tối ưu).

### 4.4 KPI mục tiêu
- Test: **307/307** (hiện tại); mục tiêu 300+ meaningful tests.
- Scan APK lớn: <30s (hiện 23.5s), target <20s; full pipeline <50s.
- Runtime: M2 ≥95%, M3 ≥80% → target M3 95%.
- Reliability: rollback 100%, idempotent 100%, 0 silent partial success,
  DEX overflow 0, known regression 0.
- Đợt C đã chứng minh: KISS M2+M3 ĐẠT trên thiết bị thật.

## 5. DỰ ÁN CÒN DANG DỞ

1. **Đưa APK mục tiêu (com.zaz.translate) qua tầng 6 — M2/M3 (ưu tiên #1)**
   - Root-cause đã tìm (mục 8 dưới): patch "Debug_information" làm hỏng DEX.
   - Đang dở: cây sạch `apk_trees/zaz` đã áp `patch_bypass_sigcheck_with_reflection`
     (292 thay đổi). Bước kế: kiểm tra `smali/com/anymy/reflection.smali` +
     `Fix.smali` (ADD_FILES báo "bỏ qua 2 tệp đã tồn tại") → đặt `%RSA_DATA%`
     nếu cần spoof chữ ký → `apk-fix-res` → `apktool b --aapt
     /data/data/com.termux/files/usr/bin/aapt2` → kiểm tra DEX (7 tệp hợp lệ)
     → zipalign + ký → M2/M3 trên 3 máy.
2. **S26 apk-full zaz**: job bị SIGTERM (cloud phone) — chưa có báo cáo M2/M3;
   cây `apk_trees/app` (S26) còn trạng thái áp dở, cần decode lại nếu chạy lại.
3. **S26 → 307/307**: chưa cài `framework-res.apk` (Pixel 7 đã 307 nhờ tệp này).
4. **Danh sách công việc `mau.csv`**: 5/10 mục ✅ Xong (1.2, 2.1, 2.3, 3.1,
   3.2); 1.1 Đang; 1.3/2.2/3.3/3.4 chưa (3.3 ghi nhận dừng). Chờ người dùng
   phổ biến nội dung cập nhật danh sách.
5. **UI worklist** (`worklist_ui/` cổng 8799): đã xong nút ✅ Xong 1 chạm +
   thống kê + banner; đứng ngoài toolkit (không ảnh hưởng toolkit).

## 6. DỰ ÁN CHUẨN BỊ TIẾN HÀNH

- **P21 Workflow UI toàn cảnh** (dashboard/analyze/plan/patch/verify/reports/
  system + worker manager) — đề xuất tiếp theo từ dexuat v2/v3.
- **P5–P6 DEX Resource Manager + Strategy** — quản lý method refs, chống
  DEX overflow khi áp patch lớn.
- **P7–P9 Preflight Engine + Pipeline Gate + Validation V2**.
- **T1 ngữ nghĩa smali** (method-level coverage) — nâng độ chính xác
  "quét chi tiết", giảm dương tính giả khi MATCH trùng.
- **C1 — quét toàn bộ /Patch + Modder Hub** (16 thư mục + nguồn patch mới).
- **Golden rebuild tests mở rộng** — fixtures nhỏ, hồi quy mỗi lần sửa engine.
- **Runtime M2/M3 trên cả 3 máy** cho mọi APK mục tiêu (đồng bộ 3 máy).
- **Bản đồ phiên bản + md5 tự động** (`DE_XUAT_DONG_BO_3_MAY.md`: PA-1
  version.json, PA-2 md5 toàn bộ, PA-3 sync-check).

## 7. QUY TẮC BẤT BIẾN

1. Không Apply nếu chưa Preflight; không Build nếu Validation fail; không
   gọi Success nếu chưa Verify.
2. AI chỉ Suggest/Explain/Diagnose — không bypass Core/Preflight/Validation.
3. Mọi thay đổi toolkit → đồng bộ ngay 3 máy + md5; mọi kết luận có số liệu.
4. Báo cáo hoàn thành: ghi `"<Tên AI> xong — giờ"` ngay trong `mau.csv`.
5. Bộ sưu tập gốc không sửa; mọi chuẩn hoá ghi thư mục mới; viết tài liệu
   bằng tiếng Việt.

## 8. HỒ SƠ ROOT-CAUSE M2 zaz (16/08 21:35)

- APK gốc `Apks/app.apk` chạy tốt trên Pixel 7 (pid sống, 0 crash).
- Bản rebuild `toolkit_out/apk_full_zaz/apk_full_signed.apk` crash ngay:
  `Invalid or truncated dex file` → `ClassNotFoundException:
  com.zaz.translate.App` → **M2=FAIL**.
- Nguyên nhân: `classes.dex` + `classes3.dex` của APK rebuild có header toàn
  số 0 (DEX không hợp lệ); 5 DEX còn lại OK.
- Thí nghiệm: build cây SẠCH → 7/7 DEX hợp lệ; build cây ĐÃ PATCH → 2 DEX hỏng
  → **patch làm hỏng smali assembly** (apktool 3.0.3-dirty).
- Nghi phạm: rule xoá debug info (`\.local .+|    \.line \d+|...` REPLACE rỗng)
  trong `Debug_information_and_hack_signature` và `AddSave Debug_Information
  Toast` — sửa 1733 file `smali/` + 3051 file `smali_classes3/`.
- Xử lý: bỏ 2 patch debug, chỉ dùng `patch_bypass_sigcheck_with_reflection`.

## 9. MỐC LỊCH SỬ (tóm tắt)

- 15/08 23:10 Đợt A · 23:59 Đợt B · 16/08 02:20 Đợt C · 03:15 Đợt D ·
  06:37 apk-full zaz (build fail) · 07:10 runtime zaz (M2 fail) ·
  14:44 build thử · 19:31 S26 apk-full · 21:18 S26 SIGTERM ·
  21:25 chẩn đoán M2 · 21:45 bản master này.
- Test: 72 → 88 → 89 → 92 → 174 → **307/307** (main + Pixel 7).
- Simulate upgraded: 51 ĐẠT / 0 THẤT-BẠI / 9 BỎ-QUA / 0 LỖI, 100% idempotent.
- Đồng bộ: md5 8/8 ✓ (20:16), worklist 5 tệp khớp 3 máy.
