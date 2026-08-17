# TRẠNG THÁI HIỆN TẠI — PATCHX TOOLKIT (BẢN MASTER)

Ngày cập nhật: **2026-08-17 (Asia/Ho_Chi_Minh)** — mốc đồng bộ hiện trạng: suite 345/345.

### Mốc cập nhật phiên hiện tại

- Đã bổ sung `diff-apk --semantic-plan-v2`: sinh semantic plan chỉ tham
  chiếu từ ghép method duy nhất, có `on_ambiguous=STOP`.
- Đã bổ sung `plan-compile`: tạo `patchx.transaction-draft/v1` với hash
  evidence, `DRAFT_REQUIRES_APPROVAL`, `executable=false`.
- Đã bổ sung `plan-preflight`: kiểm tra hash cây APK; nếu hash khác sẽ tự
  đánh giá lại plan V2 — vẫn `READY` thì sinh draft mới (`-o` để ghi), mơ hồ/
  không đủ bằng chứng thì `BLOCKED`.
- Web UI đã có các tác vụ model V2, semantic-plan V2, plan-compile và
  plan-preflight; không tác vụ nào tự gọi `apply`.
- Đã hủy và xóa `tools/sync_machines.sh`; toolkit không còn lệnh đồng bộ
  sang máy khác.
- Benchmark model V2 cache lạnh trên `apk_trees/zaz` (540M, 45.018 tệp):
  **201.495 method**, **912.805 cạnh gọi**, **64.598 điểm quyết định**,
  **4.519 method reachable từ entry**, thời gian **169,161s** (`patchx model
  apk_trees/zaz --v2 --bench`, không ghi JSON). Số đo này là KPI thực tế,
  chưa có tối ưu riêng cho model.
- Suite đơn vị hiện tại: **345/345 đạt** (`python3 tests/run_tests.py`, 0 lỗi).
  Đã chụp lại `baseline capture --full`: `test_pass=345/345`,
  `simulate_pass=51/60`, `golden_build_pass=14/14`, `errors=0`.
- CI hiện tại trên `upgraded/`: `ci` đầy đủ **85% đạt / 35,4s**; `ci --quick`
  **93% đạt / 12,9s** — 60 file, 0 lỗi audit, 13 combo.
- Evidence report V2: `semantic-plan --verbose` in ứng viên bị loại kèm điều
  kiện còn thiếu; failure DB thêm `F-SEM-001..004` cho `AMBIGUOUS_TARGET`,
  `INSUFFICIENT_EVIDENCE`, draft stale và `NO_CONFIDENT_TARGET`.
- Decision-flow + data-flow V2: `remote-map CÂY --flow` dựng
  `patchx.decision-flow/v1` (source/transform/decision/sink + đường tới sink);
  `remote-map CÂY --dataflow` dựng `patchx.data-flow/v1` với `primary_role`,
  `roles`, `data_type`, `confidence` và đường decision → sink.
- Nghiệm thu V2: `acceptance FIXTURE` đo tái lập model 100%, tái nhận diện
  100%, READY đúng 1/1, dương tính giả 0%, mơ hồ/không tự tin bị chặn 100%.
- Học từ selector thất bại: `semantic-plan --verbose` in gợi ý siết/nới
  selector khi `AMBIGUOUS_TARGET` hoặc `NO_CONFIDENT_TARGET`.
- An toàn thực thi V2: test monkeypatch `Engine.apply`/`apply_many` rồi chạy
  model/plan/compile/preflight/map/acceptance — kết quả **0 lần** gọi apply.
- Knowledge bridge: `knowledge suggest-plan CÂY -o PLAN.json` sinh
  semantic-plan/V2 tham chiếu từ kho tri thức, `recommendation_only=true`.
Tài liệu tổng duy nhất: trạng thái 3 máy + cấu trúc toolkit + bản đồ tài
nguyên + phát đồ phát triển + dự án dang dở/chuẩn bị. Đọc tệp này trước, chi
tiết lịch sử xem `QUY_TRINH.md`, `KINH_NGHIEM.md`, `NGU_CANH.md`,
`UPGRADE_PLAN_V3.md`, `UPGRADE_PLAN_V4.md`, `de xuat phuong an/`.

---

## 1. TRẠNG THÁI 3 MÁY (mốc bàn giao)

| Máy | IP adb | Kiểm thử | Trạng thái | Ghi chú |
|-----|--------|----------|------------|---------|
| **Máy chính** (Termux) | — | **345/345 đạt** (0 lỗi) | 🟢 Điều phối + giám sát | Suite đã chạy lại trong lần đồng bộ này |
| **Pixel 7** (Redfinger) | 100.64.170.99:5555 | Chưa xác minh lại | 🟡 Cần chạy lại | Đồng bộ máy đã hủy; số 320/320 cũ chưa được kiểm chứng lại |
| **S26** (Redfinger) | 100.76.244.117:5555 | Chưa xác minh lại | 🟡 Cần chạy lại | Đồng bộ máy đã hủy; số 320/320 cũ chưa được kiểm chứng lại |

- Đồng bộ từ toolkit: **đã hủy và gỡ bỏ**; không còn script đẩy dữ liệu sang
  Pixel 7 hoặc S26.
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
- `patchx_core/` — 31 module: `advisor` (coverage nhanh rg/hash/cache),
  `bypass_advisor` (báo cáo bypass + tỷ lệ %), `engine` (áp patch), `audit`,
  `optimizer`, `combo`, `preflight`, `smali_lib/smali_sem/smali_validate`
  (ngữ nghĩa smali), `dex_budget`, `diffapk`, `runtime_scenario` (M3),
  `failure_db` (chẩn đoán), `remote_map` (bản đồ điều khiển từ xa), `learn`,
  `session`, `simulate`, `fuzz`, `risk`, `baseline`, `model`, `parser`,
  `cli`, `indexer`, `complement`, `semantic_plan` (plan V1/V2),
  `plan_compile` (transaction nháp), `knowledge` (kho tri thức V2),
  `acceptance` (tiêu chí nghiệm thu V2).
- `webui/` — server.py (cổng 8787) + static (index.html/app.js/style.css):
  6 tab nghiệp vụ **Trang chủ / Vượt chặn / Chỉnh sửa / Hook / Quy trình /
  Kho**, chế độ 🟢/🟡/🔴, bản đồ toolkit, thanh trạng thái 6 tầng, Manual
  Mode, API `/api/state /api/plan /api/tree /api/file /api/search ...`.
- `tests/` — `run_tests.py` (345 bài) + `fixtures/` (golden, keystore test,
  semantic_v2).
- `tools/` — `bell.sh`, `bench_dex64k.py`, `vm_worker.py`.
- `de xuat phuong an/` — 2 tệp đề xuất kiến trúc V2: `đề xuất.txt` +
  `mau_ke_hoach_ngu_nghia.json` (xem mục 10).

## 3. BẢN ĐỒ KHỐI TÀI NGUYÊN (mapping)

| Thư mục | Nội dung | Số lượng | Vai trò |
|---------|----------|---------|---------|
| `Apks/` | APK đầu vào gốc | 1 | `ApkToolPatcher v5.0.apk` |
| `upgraded/` | Patch chuẩn hóa | 60 zip | Nguồn patch chính, 0 lỗi cấu trúc |
| `combos/` | Combo gộp chính | 76 | Gộp patch theo mục tiêu |
| `combos_auto/` | Combo tự phát hiện | 15 | Theo họ chức năng + class-link |
| `combos_auto_plus/` | Combo năng lực mới | 6 | bypass_plus nâng cao |
| `bypass_plus/` | Mẫu bypass nâng cao | 13 | purchase/root-hide/ssl-pinning/anti-debug/frida-hide/emulator... |
| `optimized/` | Patch tối ưu | 14 | Gộp trùng + tách xung đột |
| `hook_remote_data_control/` | Hook điều khiển thu thập dữ liệu từ xa | 2 tệp | DataGuard.smali + patch.txt |
| `apk_trees/` | Cây giải mã | 3 | `ApkToolPatcher v5.0`, `Screen Translation_3.1.2`, `zaz` |
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
  test **92/92 → 174/174 → 307/307 → 312/312 → 326/326 → 328/328 → 331/331**.
- **Đợt nghiệm thu V2** (17/08): thêm `acceptance`, `remote-map --dataflow`,
  học từ selector thất bại, revalidate draft, an toàn thực thi; test
  **331/331 → 343/343 → 344/344 → 345/345**.
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
- Test: **345/345** (hiện tại); mục tiêu 300+ meaningful tests.
- Scan APK lớn: <30s (hiện 23.5s), target <20s; full pipeline <50s.
- Runtime: M2 ≥95%, M3 ≥80% → target M3 95%.
- Reliability: rollback 100%, idempotent 100%, 0 silent partial success,
  DEX overflow 0, known regression 0.
- Đợt C đã chứng minh: KISS M2+M3 ĐẠT trên thiết bị thật.

## 5. DỰ ÁN CÒN DANG DỞ

1. **APK mục tiêu com.zaz.translate — reflection-only** (xem mục 10): cây
   `apk_trees/zaz` sạch, chỉ áp `patch_bypass_sigcheck_with_reflection`, tách
   7 DEX, build + ký hợp lệ; runtime **M2_PASS / M3_PASS**, 0 crash/ANR.
2. **S26/Pixel 7**: đồng bộ máy đã hủy — chưa chạy lại suite và chưa xác minh
   M2/M3 trong lần đồng bộ này; cần chạy lại khi có thiết bị.
3. **Worklist bên ngoài toolkit**: `mau.csv` và UI worklist nằm ngoài
   `_patchx`, không thuộc phạm vi đồng bộ toolkit.

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
3. Mọi kết luận có số liệu; không dùng toolkit để đồng bộ hoặc đẩy dữ liệu
   sang máy khác.
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
- Test: 72 → 88 → 89 → 92 → 174 → 307/307 → 312/312 → 326/326 → 328/328 →
  **331/331 → 343/343 → 344/344 → 345/345** (main).
- Simulate upgraded: 51 ĐẠT / 0 THẤT-BẠI / 9 BỎ-QUA / 0 LỖI, 100% idempotent.
- Đồng bộ: md5 8/8 ✓ (20:16), worklist 5 tệp khớp 3 máy.

## 10. BÀN GIAO — TẦNG NGỮ NGHĨA V2 (2026-08-17)

Đợt này hiện thực hoá lát cắt đầu tiên của đề xuất tại `de xuat phuong an/đề
xuất.txt`: nhận diện mục tiêu theo cấu trúc/ngữ nghĩa, nhưng **không mở bất kỳ
đường tự động nào sang Engine.apply**. V1 còn nguyên để tương thích mọi plan,
kho tri thức và lệnh cũ.

### 10.1 Thành phần đã hoàn tất

| Thành phần | Tệp | Hợp đồng an toàn |
|---|---|---|
| App model V2 | `patchx_core/smali_sem.py` | `build_app_model_v2()` chỉ đọc cây APK; tạo `patchx.app-model/v2`, identity `exact/structural/semantic`, caller/callee, `entry_distance`, provenance. |
| CLI model | `patchx_core/cli.py` | `python3 patchx model CÂY --v2`; không có thao tác ghi vào cây APK, chỉ ghi JSON model nếu yêu cầu. |
| Semantic plan V2 | `patchx_core/semantic_plan.py` | `patchx.semantic-plan/v2`: `selector.all`, `near_entry`, `policy.min_score/max_accepted`, bắt buộc `on_ambiguous: STOP`; chỉ nhận app-model/V2. |
| Verdict V2 | `semantic_plan.py` | `READY_FOR_PREFLIGHT`, `AMBIGUOUS_TARGET`, `INSUFFICIENT_EVIDENCE`, `NO_CONFIDENT_TARGET`; verdict không gọi apply. |
| Knowledge V2 | `patchx_core/knowledge.py` | `patchx.knowledge-record/v2` bắt buộc identity, `extractor_version`, đủ gate preflight/validate/build/runtime và `verified=true`; query V2 luôn trả `recommendation_only=true`. |
| Ghép phiên bản | `patchx_core/diffapk.py` | `match_app_models_v2()` phân loại `exact/structural/semantic/unknown`; nhiều ứng viên hoặc thiếu evidence luôn là `unknown`. |
| CLI version map | `patchx_core/cli.py` | `patchx diff-apk GỐC MOD --version-map map.json`; chỉ ghi JSON evidence, độc lập với patch ZIP diff. |
| Data-flow V2 | `patchx_core/remote_map.py` | `remote-map --dataflow` mỗi nút có `primary_role`, `roles`, `data_type`, `confidence`; đường decision → sink chỉ là bằng chứng. |
| Nghiệm thu V2 | `patchx_core/acceptance.py` | `acceptance FIXTURE` đo tái lập model, tái nhận diện, dương tính giả, mơ hồ/không tự tin bị chặn. |
| Revalidate draft | `patchx_core/plan_compile.py` | `revalidate_draft()` đánh giá lại plan V2 khi hash cây đổi; chỉ ghi draft mới nếu vẫn READY. |
| An toàn thực thi V2 | `tests/run_tests.py` | `test_v2_never_calls_apply` khóa ràng buộc: các bước V2 chỉ-đọc không được gọi `Engine.apply`. |

### 10.2 Ý nghĩa identity và quy tắc dùng

- `exact`: hash thân Smali chuẩn hoá (bỏ metadata/debug); phát hiện thay đổi
  chính xác, không dùng để chịu obfuscation.
- `structural`: kiểu, histogram opcode, nhánh, hình dạng lời gọi; chịu đổi tên
  class/method và thanh ghi. Chỉ là bằng chứng xếp hạng/kế hoạch.
- `semantic`: kiểu, API nền tảng, string, kiểu field-read; không bao giờ đủ
  một mình để tự thay đổi APK.
- Với plan V2, phải đồng thời đạt score, `max_accepted` và evidence yêu cầu.
  Nhiều ứng viên = dừng (`AMBIGUOUS_TARGET`), không chọn ứng viên đứng đầu.
- Với knowledge/version map, điểm 100/90/70/55% chỉ là thứ hạng tham chiếu.
  Muốn tác động APK mới vẫn phải chạy semantic-plan V2, người dùng duyệt và
  qua preflight → validate → build/sign → M2 → M3.

### 10.3 Fixture và số liệu nghiệm thu

- Fixture: `tests/fixtures/semantic_v2/source/` và `obfuscated/` cùng
  `plan_v2.json`. Bản obfuscate đổi tên class/method và thanh ghi.
- Model V2 fixture: 3 method, 2 cạnh gọi, 3 method reachable từ entry.
- Semantic plan V2 fixture: chọn đúng duy nhất
  `Lcom/example/semantic/License;->isEnabled()Z`, score 100%,
  `READY_FOR_PREFLIGHT`.
- Knowledge V2: nguồn → obfuscate khớp `structural + semantic`, confidence
  90%, có `recommendation_only=true`; không tự chọn target.
- Version map: **exact=0, structural=3, semantic=0, unknown=0**.
- `acceptance tests/fixtures/semantic_v2`: tái lập model **100% (3/3)**,
  tái nhận diện **100%**, READY đúng **1/1**, dương tính giả **0%**, mơ hồ bị
  chặn **1/1**, không tự tin bị chặn **1/1**.
- Full suite gồm cả nhánh CLI `diff-apk --version-map` + `acceptance` +
  data-flow + revalidate draft + an toàn thực thi: **345/345 đạt**.
  Smoke fixture của CLI cũng thành công.
- Cầu nối V2 từ version map: `diff-apk --semantic-plan-v2 PLAN.json` chỉ
  sinh plan tham chiếu từ ghép method duy nhất. Smoke source → obfuscated tạo
  3 target, mỗi target có đúng 1 ứng viên (`READY_FOR_PREFLIGHT`), 0 đường
  gọi `apply`; provenance luôn là `recommendation_only=true`.

### 10.4 Lệnh tái nghiệm thu

```sh
python3 patchx model tests/fixtures/semantic_v2/source --v2 -o /data/data/com.termux/files/usr/tmp/model_v2.json
python3 patchx semantic-plan tests/fixtures/semantic_v2/source tests/fixtures/semantic_v2/plan_v2.json
python3 patchx diff-apk tests/fixtures/semantic_v2/source tests/fixtures/semantic_v2/obfuscated --no-verify -o /data/data/com.termux/files/usr/tmp/version_fixture.zip --version-map /data/data/com.termux/files/usr/tmp/version_map.json
python3 patchx remote-map tests/fixtures/semantic_v2/source --dataflow
python3 patchx acceptance tests/fixtures/semantic_v2
python3 tests/run_tests.py
```

### 10.5 Điểm tiếp tục ưu tiên

1. ~~Đo thời gian `model --v2` cache lạnh trên cây APK 477–553M.~~
   **Đã xong**: `apk_trees/zaz` 540M = **169,161s** cho 201.495 method,
   912.805 cạnh gọi; ghi nhận là số đo thực tế, chưa tối ưu riêng cho model.
2. ~~Sinh **semantic-plan/V2 tham chiếu** từ version map nhưng chỉ cho ghép duy
   nhất, đồng thời ghi source/target identity + evidence. Không tạo patch.~~
   **Đã xong**: `diff-apk --semantic-plan-v2`; selector luôn có
   `max_accepted=1`, `on_ambiguous=STOP`, provenance chỉ tham chiếu.
3. ~~Thiết kế `plan-compile` sau bước 2: chỉ nhận plan đã duyệt và evidence khoá
   theo hash cây; tạo transaction/patch nháp có provenance, rồi qua gate cũ.~~
   **Đã xong**: `plan-compile CÂY PLAN_V2 -o DRAFT.json` chỉ xuất
   `patchx.transaction-draft/v1` với `DRAFT_REQUIRES_APPROVAL`, hash evidence,
   target đã chọn và các gate bắt buộc; `executable=false`, không gọi apply.
4. ~~**Evidence gate**: `plan-preflight CÂY DRAFT.json` phải chặn khi hash cây
   thay đổi.~~ **Đã xong**: khi hash khác, CLI tự `revalidate_draft()` — vẫn
   READY thì ghi draft mới qua `-o`, mơ hồ/không đủ bằng chứng thì `BLOCKED`.
5. Sau khi có số liệu và test âm đủ mạnh mới đưa evidence V2 vào Web UI.
