# PATCHX V2 — ĐỀ XUẤT NÂNG CẤP THỐNG NHẤT (bản hợp nhất)

- Ngày: 2026-08-16
- Nguồn hợp nhất: `dexuat1.txt`, `dexuat1_v2.txt`, `dexuat2.txt`,
  `dexuat2_v2.txt`, `dexuat_v3.txt`, `MA_TRAN_PHASE.md`,
  `UPGRADE_PROPOSAL.md`, `UPGRADE_PLAN_V3.md`, `UPGRADE_PLAN_V4.md`.
- Mục đích: 1 tài liệu duy nhất thay cho các bản đề xuất rời — lộ trình rõ
  thứ tự, lược bỏ phần trùng, gắn với trạng thái hiện tại (2026-08-16).
- Quy ước: tài liệu tiếng Việt; tên module/tệp/lệnh giữ nguyên gốc.

---

## 1. Tầm nhìn

Biến PATCHX từ "bộ nhiều công cụ" thành **một dây chuyền kiểm chứng đầu-cuối**:
người dùng chỉ cần nói mục tiêu → PATCHX tự SCAN → EVIDENCE → PLAN →
PREFLIGHT → APPLY → VALIDATE → BUILD → SIGN → INSTALL → M2 → M3 → REPORT,
mỗi bước có đầu vào/đầu ra đo được, tự học từ lỗi và cải thiện dần.

Điểm mấu chốt: **không đánh giá bằng số lượng tính năng** — một patch chỉ
được coi là SUCCESS khi đi qua đủ chuỗi: FOUND → CORRECT PLAN → PREFLIGHT
PASS → DEX BUDGET PASS → APPLY → POSTCONDITION PASS → VALIDATE PASS →
BUILD PASS → SIGN PASS → INSTALL PASS → M2 PASS → M3 PASS (nếu có kịch bản)
→ REGRESSION PASS.

## 2. Nguyên tắc bất biến

1. Không Apply nếu chưa Preflight.
2. Không Build nếu Validation fail.
3. Không gọi Success nếu chưa Verify.
4. AI chỉ SUGGEST / EXPLAIN / DIAGNOSE — không được bypass Core, Preflight,
   Validation, Commit.
5. Không tối ưu trước baseline + regression (đo trước, sửa sau).
6. Mọi thay đổi quan trọng phải có test + artifact.
7. Patch sau không được sửa tệp do patch khác tạo (provenance), trừ khi
   khai báo `allow_generated_target = true`.
8. Không có trạng thái "chắc là OK" — mọi gate trả PASS / WARNING / BLOCK.

## 3. Kiến trúc đích

### 3.1 Năm tầng

```
USER / UI LAYER      Dashboard · Analyze · Plan · Patch · Verify · Reports
ORCHESTRATION LAYER  Workflow · Job Queue · Pipeline · Report · Artifacts
PATCHX CORE LAYER    Scanner · Planner · Preflight · Executor · Transaction
                     Validator · Builder · Runtime Verifier
PATCH MODEL LAYER    Contract · Provenance · Result · Risk · Evidence
DATA / LEARNING      Baseline · Failure DB · Success DB · Cache · Workers
```

### 3.2 Pipeline chuẩn (16 bước)

```
APK → SCAN → EVIDENCE → PLAN → PREFLIGHT → TRANSACTION → APPLY →
PROVENANCE → POSTCHECK → VALIDATE → BUILD → SIGN → INSTALL → M2 → M3 → REPORT
```

### 3.3 Sáu gate kiểm soát

| Gate | Nội dung | Kết quả |
|---|---|---|
| GATE 1 | ANALYSIS | PASS / WARNING / BLOCK |
| GATE 2 | PLAN | PASS / WARNING / BLOCK |
| GATE 3 | PREFLIGHT | PASS / WARNING / BLOCK |
| GATE 4 | VALIDATION | PASS / WARNING / BLOCK |
| GATE 5 | BUILD | PASS / WARNING / BLOCK |
| GATE 6 | RUNTIME | PASS / WARNING / BLOCK |

### 3.4 DEX gate (5 mức)

```
<70% SAFE · 70–85% WATCH · 85–95% HIGH · 95–99% CRITICAL · ≥100% BLOCK
```
Không Apply nếu `free_refs < estimated_delta`.

## 4. Thang đo nghiệm thu APK (M0–M3)

Phân biệt rõ với milestone phát triển M0–M6 (mục 5): đây là thang đo kết
quả trên APK thật.

- **M0 — Áp được (static)**: patch áp lên cây apktool không lỗi, idempotent,
  coverage > 0.
- **M1 — Rebuild được**: cây sau patch chạy qua `apktool b` thành công.
- **M2 — Cài được**: APK build + ký (apksigner) cài được, mở app không crash,
  logcat sạch lỗi mới.
- **M3 — Vượt kiểm tra**: hành vi bypass được xác minh đúng mong muốn
  (license/VIP active, không gửi analytics, signature hợp lệ...) bằng test
  động / logcat + mạng.

Nghiệm thu "thành công": M0→M3 trên ≥ 1 APK thật, có biên bản số liệu.

## 5. Lộ trình thống nhất P0–P21 (7 milestone M0–M6)

Trạng thái ghi theo `MA_TRAN_PHASE.md` + `TRANG_THAI_HIEN_TAI.md`
(2026-08-16). ĐÃ CÓ = đủ cho phase, có thể chỉ cần kiểm chứng.

### M0 — FOUNDATION (Lớp A)

| Phase | Nội dung | Module | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| P0 | Baseline + CI: benchmark (mini/medium/large/64K/framework/runtime), metrics.json, chặn regression | `patchx_core/baseline.py`, CLI `baseline`, `baseline/` | ĐÃ CÓ | Chụp baseline số thật + CI chạy định kỳ |

### M1 — CORE SAFE (Lớp A)

| Phase | Nội dung | Module | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| P1 | Unified contract: lifecycle LOAD→…→COMMIT; Result MATCHED/CHANGED/NO_MATCH/SKIPPED/FAILED/ROLLED_BACK | `parser.py`, `model.py`, `engine.py` | ĐÃ CÓ | test_result_contract |
| P2 | Transaction engine: DRY_RUN/SAFE/STRICT; BEGIN→SNAPSHOT→…→COMMIT; rollback 100% | `engine.py` (backup/state/idempotent) | ĐÃ CÓ | test_strict_rollback |
| P3 | Provenance: ledger JSON; chặn sửa tệp do patch khác tạo | `engine.py` | ĐÃ CÓ | test kèm engine |
| P4 | Fixpoint: MAX_PASSES=5, passes_used/cycle_detected | `engine.py` | ĐÃ CÓ | test fixpoint |

### M2 — RESOURCE SAFE (Lớp A)

| Phase | Nội dung | Module | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| P5 | DEX Resource Manager: used/max/free/delta/remaining; 5 mức SAFE→BLOCK | `patchx_core/dex_budget.py` | ĐÃ CÓ | Benchmark 64K trên S26 ĐẠT |
| P6 | DEX Strategy: 5 chiến lược ưu tiên + risk/confidence/reason | `patchx_core/dex_budget.py` | ĐÃ CÓ | test_dex_budget |
| P7 | Preflight Engine: READY/READY_WITH_WARNING/INCOMPATIBLE/UNSAFE | `patchx_core/preflight.py` | ĐÃ CÓ | gate trong apk-patch/apk-full |
| P8 | Pipeline Gate: preflight bắt buộc trước apply | `patchx_toolkit.py` | ĐÃ CÓ | test_pipeline_gate |

### M3 — BUILD VERIFIED (Lớp B)

| Phase | Nội dung | Module | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| P9 | Validation V2: 4 level FAST/NORMAL/FULL/RELEASE + Smali/XML/Manifest/DEX | `smali_validate.py` | ĐÃ CÓ | test_validation_v2 |
| P10 | Golden Build: critical 100% / extended ≥99% | `test_golden_rebuild`, `test_golden_framework_res` | **MỘT PHẦN** | Bộ golden chuẩn (64K, framework, core) + gate CI tự chạy |
| P11 | Test Matrix T0–T3: 300+ tests | `tests/run_tests.py` | ĐÃ CÓ (307) | Duy trì, mở rộng theo phase mới |
| P12 | Fuzz/Chaos: 5 invariant, chặn xóa manifest | `patchx_core/fuzz.py`, CLI `fuzz` | ĐÃ CÓ | Chạy định kỳ, mở rộng seed |

### M4 — RUNTIME VERIFIED (Lớp B)

| Phase | Nội dung | Module | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| P13 | Runtime M2: install/launch/wait/pid/logcat/crash/ANR; M2_PASS/FAIL/SKIP | `apk-runtime` | ĐÃ CÓ | Nghiệm thu thật Pixel 7 M2_PASS; mở rộng benchmark ≥95% |
| P14 | Runtime M3: scenario.json (launch/tap/swipe/input/navigate/assert_*/screenshot) | `runtime_scenario.py`, `--scenario` | ĐÃ CÓ | Nghiệm thu 12 bước M3_PASS; mở rộng M3 ≥80%→95% |
| P15 | Failure Intelligence: ERROR_ID/STAGE/pattern/cause/fix/regression; sinh test tự động | `failure_db.py`, CLI `failure` | ĐÃ CÓ | Gắn ERROR_ID vào runtime + CI |

### M5 — INTELLIGENCE (Lớp C)

| Phase | Nội dung | Module | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| P16 | Scanner V2: 4 mode FAST/NORMAL/FULL/RELEASE + evidence graph | `advisor.py`, `apk-plan` | ĐÃ CÓ | FULL hết xấp xỉ; mode lạ bị chặn |
| P17 | Simulation V2: 5 chiều PASS/EXPECTED_SKIP/UNSUPPORTED/BAD_PATCH/ENGINE_LIMIT + cache hash | `simulate.py` | ĐÃ CÓ | Cache 7415ms→81ms |
| P18 | Evidence-based Plan: score + confidence + evidence files/top_files | `apk-plan` (bypass_plan.json) | ĐÃ CÓ | confidence % + evidence graph |
| P19 | Self-learning + LLM: LLM chỉ SUGGEST (--approve mới ghi combo) | `learn.py`, `suggest-llm` | ĐÃ CÓ | test_learn_smart |

### M6 — PERFORMANCE + PRODUCT (Lớp D)

| Phase | Nội dung | Module | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| P20 | Performance: cache scan/simulate/regex/candidate; workers tùy chọn | ScanCache, sim cache, `dex-budget --workers` | ĐÃ CÓ | Quét 70K method 1,78s (KPI <30s); mặc định 1 worker |
| P21 | Product UI: Workbench theo workflow, 7 khu vực, 3 chế độ người dùng | `webui/` | ĐÃ CÓ | Hoàn thiện 7 khu vực + nối failure/self-learning |

## 6. Dependency và thứ tự triển khai

### 6.1 Dependency (bất biến — không nhảy cóc)

```
P0
 ↓
P1 → P2 → P3 → P4
                  ↓
         P5 → P6 ─┤
         P7 → P8 → P9 ──── P10 ── P11 ── P12
                                        ↓
                            P13 → P14 → P15
                                        ↓
                            P16 → P17 → P18 → P19
                                        ↓
                                    P20 → P21
```

Chạy song song được: P5+P6 · P7+P9 · P10+P11+P12 · chuẩn bị runtime/golden ·
P16+P17 khi dependency đủ.

### 6.2 Sprint (kèm người thực hiện)

| Sprint | Phase | Mục tiêu | Thực hiện |
|---|---|---|---|
| 0 | P0 | Baseline + CI + observability | Main |
| 1 | P1, P2 | Contract + Transaction | Main |
| 2 | P3, P4 | Provenance + Fixpoint | Main |
| 3 | P5, P6, P7 | DEX budget + Preflight | Agent A + B |
| 4 | P8, P9, P10 | Pipeline gate + Validation + Golden | Agent B + C + VM |
| 5 | P11, P12 | Test matrix + Fuzz | Agent C |
| 6 | P13, P14, P15 | Runtime M2/M3 + Failure intelligence | Agent B + Device |
| 7 | P16, P17, P18 | Scanner V2 + Simulation V2 + Plan Engine | Agent A + Main |
| 8 | P19 | Self-learning + LLM | Main + Agent A |
| 9 | P20, P21 | Performance + UI hoàn chỉnh | Main + UI team |

## 7. KPI tổng thể (một bảng duy nhất)

| Nhóm | Chỉ số | Mục tiêu |
|---|---|---|
| Độ tin cậy | Rollback / Idempotency | 100% |
| | Silent partial success / Unhandled crash / Known regression / DEX overflow | 0 |
| Build | Critical Golden | 100% |
| | Extended Golden | ≥99% |
| Test | Meaningful tests, phủ T0–T3 | 300+ (hiện 307) |
| Runtime | M2 benchmark | ≥95% |
| | M3 benchmark | ≥80% → 95% |
| Thông minh | Unexpected SKIP | <5% |
| Hiệu năng | Scan APK lớn 477M | <30s (target <20s) — hiện 23,6s |
| | Simulation 60 patch | <30s (target <25s) |
| | Full pipeline | <50s |

## 8. UI/UX đích

- **7 khu vực**: 🏠 Dashboard · 🔍 Analyze · 🧠 Plan · 🛠 Patch · 🧪 Verify ·
  📊 Reports · ⚙ System.
- **3 chế độ người dùng**: 🟢 Cơ bản (Goal → Recommended → One Click) ·
  🟡 Nâng cao (Goal → Plan → Select → Configure) · 🔴 Chuyên gia
  (Inventory → Candidate → Plan → Raw Patch → Diff → Engine → Build).
- **Workbench là trung tâm**: hiển thị APK hiện tại, trạng thái, đề xuất,
  tiến trình 6 bước ANALYZE → PLAN → PREFLIGHT → PATCH → BUILD → VERIFY,
  kèm APK health (thanh DEX, Risk, Targets, Candidates).
- **Nguyên tắc UX**: người mới không cần biết PATCHX hoạt động thế nào;
  người chuyên gia phải nhìn được mọi thứ. Toàn bộ 20+ module, 60 patch,
  76 combo vẫn nằm phía dưới — UI không bắt học lệnh.

## 9. Tổ chức thực thi

- **Main**: P0–P4, tích hợp, regression, review, merge.
- **Agent A**: P5–P6 (DEX resource + strategy + test + benchmark).
- **Agent B**: P7–P9 (preflight, pipeline gate, validation).
- **Agent C**: P10–P12 (golden, test matrix, fuzz).
- **Agent D**: P16–P18 (scanner, evidence, simulation, scoring, plan engine).
- **VM worker**: decode/build/sign, 64K benchmark, golden build, M2/M3.
- **Device/emulator**: install, launch, runtime M2/M3, logcat, screenshot.
- **Quy trình**: MAIN → TASK CONTRACT (objective/input/output/files được phép
  sửa/acceptance/test command/regression) → AGENT → UNIT TEST → INTEGRATION
  TEST → MAIN REVIEW → GOLDEN/CI → PASS=merge, FAIL=failure artifact → agent fix.
- Mọi agent chỉ chạy phase ĐÃ ĐƯỢC phép; cuối đợt gộp về Main → regression →
  so baseline → mới coi là xong.

## 10. Definition of Done (một patch "thành công" thật sự)

Phải sinh đủ artifact: `scan.json`, `plan.json`, `preflight.json`,
`transaction.json`, `validation.json`, `build.json`, `runtime.json`,
`logs/`, `report/` — và kết thúc ở `PATCHX SUCCESS` (M2/M3 + regression).

## 11. Việc tiếp theo ưu tiên (2026-08-16)

1. **P10 Golden Build** — phase duy nhất còn MỘT PHẦN: chốt bộ golden chuẩn
   (64K, framework-res, core APK) + gate CI tự chạy mỗi đợt.
2. **M4 mở rộng benchmark**: M2 ≥95% / M3 ≥80%→95% trên bộ benchmark thay vì
   1 APK; gắn ERROR_ID từ failure_db vào mọi bước runtime.
3. **M6 UI**: hoàn thiện 7 khu vực (đặc biệt Plan/Verify/Reports), nối failure
   intelligence + self-learning vào UI, tùy chọn đóng gói APK UI.
4. **Baseline số thật**: chụp metrics.json chính thức, CI chạy định kỳ để giữ
   KPI không tụt.
5. Duy trì test 307/307, simulate 51 ĐẠT, scan 477M < 30s sau mỗi đợt.
