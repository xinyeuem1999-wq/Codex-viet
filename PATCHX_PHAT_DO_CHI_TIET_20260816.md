# PHÁT ĐỒ CHI TIẾT TOÀN BỘ — PATCHX TOOLKIT

- Ngày: **2026-08-16 21:55**. Bản chi tiết từng mục / từng tầng / từng phần.
- Nguồn hợp nhất: `DE_XUAT_THONG_NHAT.md`, `UPGRADE_PLAN_V3.md`,
  `UPGRADE_PLAN_V4.md`, `dexuat_v3.txt`, `MA_TRAN_PHASE.md`,
  `TRANG_THAI_HIEN_TAI.md`.
- Quy ước: tiếng Việt; tên module/tệp/lệnh giữ nguyên gốc; ĐÃ CÓ = đủ cho
  phase, có thể chỉ cần kiểm chứng.

---

# PHẦN A — KIẾN TRÚC ĐÍCH (từng phần)

## A.1 Năm tầng kiến trúc
| Tầng | Thành phần | Trách nhiệm |
|---|---|---|
| 1. USER / UI LAYER | Dashboard · Analyze · Plan · Patch · Verify · Reports | Giao diện người dùng, 7 khu vực, 3 chế độ (🟢/🟡/🔴) |
| 2. ORCHESTRATION LAYER | Workflow · Job Queue · Pipeline · Report · Artifacts | Điều phối chuỗi công việc, lưu artifact |
| 3. PATCHX CORE LAYER | Scanner · Planner · Preflight · Executor · Transaction · Validator · Builder · Runtime Verifier | Lõi xử lý patch (từng module trong `patchx_core/`) |
| 4. PATCH MODEL LAYER | Contract · Provenance · Result · Risk · Evidence | Mô hình dữ liệu patch: hợp đồng, nguồn gốc, kết quả, rủi ro, bằng chứng |
| 5. DATA / LEARNING | Baseline · Failure DB · Success DB · Cache · Workers | Dữ liệu đo, học từ lỗi, cache hiệu năng |

## A.2 Pipeline chuẩn 16 bước (từng bước)
```
APK → SCAN → EVIDENCE → PLAN → PREFLIGHT → TRANSACTION → APPLY →
PROVENANCE → POSTCHECK → VALIDATE → BUILD → SIGN → INSTALL → M2 → M3 → REPORT
```
| Bước | Đầu vào → Đầu ra | Ghi chú |
|---|---|---|
| SCAN | APK/cây → inventory.json | Quét nhanh rg/hash + cache |
| EVIDENCE | inventory → evidence_graph.json | Bằng chứng khớp từng patch |
| PLAN | evidence → bypass_plan.json | Score + confidence % + top N |
| PREFLIGHT | plan → verdict (READY/…/UNSAFE) | Kiểm tra khả thi trước khi áp |
| TRANSACTION | preflight → snapshot | DRY_RUN/SAFE/STRICT |
| APPLY | patch + cây → thay đổi thật | Idempotent + backup |
| PROVENANCE | thay đổi → ledger | Chặn patch sau sửa tệp của patch trước |
| POSTCHECK | cây → điều kiện sau áp | Kiểm tra hậu điều kiện |
| VALIDATE | cây → validation.json | 4 mức FAST/NORMAL/FULL/RELEASE |
| BUILD | cây → APK chưa ký | apk-fix-res + apktool b --aapt |
| SIGN | APK → APK đã ký | zipalign + apksigner |
| INSTALL | APK → adb install | Cài lên device/emulator |
| M2 | app → pid + logcat | Cài + mở + sống + không crash/ANR |
| M3 | app → kịch bản hành vi | launch/tap/swipe/assert/screenshot |
| REPORT | toàn bộ → report/ | Báo cáo + bài học cải thiện |

## A.3 Sáu gate kiểm soát
| Gate | Tên | Kiểm tra | Kết quả |
|---|---|---|---|
| GATE 1 | ANALYSIS | Chất lượng đầu vào, khớp mẫu | PASS / WARNING / BLOCK |
| GATE 2 | PLAN | Plan đầy đủ bằng chứng, top N hợp lý | PASS / WARNING / BLOCK |
| GATE 3 | PREFLIGHT | Khả thi áp, DEX budget, xung đột | PASS / WARNING / BLOCK |
| GATE 4 | VALIDATION | Cây hợp lệ sau apply | PASS / WARNING / BLOCK |
| GATE 5 | BUILD | Rebuild + tài nguyên sạch | PASS / WARNING / BLOCK |
| GATE 6 | RUNTIME | M2/M3 đạt theo kịch bản | PASS / WARNING / BLOCK |

## A.4 DEX gate (5 mức)
```
<70% SAFE · 70–85% WATCH · 85–95% HIGH · 95–99% CRITICAL · ≥100% BLOCK
```
- Công thức: `used_refs / max_refs`; preflight phải tính `used_refs`,
  `max_refs`, `free_refs`, `estimated_delta`, `remaining_refs`.
- Quy tắc chặn: **không Apply nếu `free_refs < estimated_delta`**.

## A.5 Thang đo nghiệm thu APK (M0–M3)
- **M0 — Áp được (static)**: patch áp lên cây apktool không lỗi, idempotent,
  coverage > 0.
- **M1 — Rebuild được**: cây sau patch chạy `apktool b` thành công.
- **M2 — Cài được**: APK build + ký cài được, mở app không crash, logcat
  sạch lỗi mới.
- **M3 — Vượt kiểm tra**: hành vi bypass xác minh đúng (license/VIP active,
  không gửi analytics, signature hợp lệ...) bằng test động/logcat + mạng.
- Nghiệm thu "thành công": M0→M3 trên ≥1 APK thật, có biên bản số liệu.

---

# PHẦN B — LỘ TRÌNH P0–P21 (7 MILESTONE M0–M6) — TỪNG PHASE

## M0 — FOUNDATION (Lớp A)
| Phase | Nội dung | Module | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| **P0** | Baseline + CI: benchmark mini/medium/large/64K/framework/runtime, metrics.json, chặn regression | `baseline.py`, CLI `baseline`, `baseline/` | ĐÃ CÓ | Chụp baseline số thật + CI chạy định kỳ |

## M1 — CORE SAFE (Lớp A)
| Phase | Nội dung | Module | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| **P1** | Unified contract: lifecycle LOAD→…→COMMIT; Result MATCHED/CHANGED/NO_MATCH/SKIPPED/FAILED/ROLLED_BACK | `parser.py`, `model.py`, `engine.py` | ĐÃ CÓ | test_result_contract |
| **P2** | Transaction engine: DRY_RUN/SAFE/STRICT; BEGIN→SNAPSHOT→…→COMMIT; rollback 100% | `engine.py` (backup/state/idempotent) | ĐÃ CÓ | test_strict_rollback |
| **P3** | Provenance: ledger JSON; chặn sửa tệp do patch khác tạo | `engine.py` | ĐÃ CÓ | test kèm engine |
| **P4** | Fixpoint: MAX_PASSES=5, passes_used/cycle_detected | `engine.py` | ĐÃ CÓ | test fixpoint kèm engine |

## M2 — RESOURCE SAFE (Lớp A)
| Phase | Nội dung | Module | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| **P5** | DEX Resource Manager: used/max/free/delta/remaining; 5 mức SAFE→BLOCK | `dex_budget.py` | ĐÃ CÓ | Benchmark 64K trên S26 ĐẠT (70K→BLOCK) |
| **P6** | DEX Strategy: 5 chiến lược ưu tiên + risk/confidence/reason | `dex_budget.py` | ĐÃ CÓ | test_dex_budget |
| **P7** | Preflight Engine: READY/READY_WITH_WARNING/INCOMPATIBLE/UNSAFE | `preflight.py` | ĐÃ CÓ | Gate trong apk-patch/apk-full |
| **P8** | Pipeline Gate: preflight bắt buộc trước apply | `patchx_toolkit.py` (_preflight_gate) | ĐÃ CÓ | test_pipeline_gate |

## M3 — BUILD VERIFIED (Lớp B)
| Phase | Nội dung | Module | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| **P9** | Validation V2: 4 level FAST/NORMAL/FULL/RELEASE + Smali/XML/Manifest/DEX | `smali_validate.py` (validate_tree_v2) | ĐÃ CÓ | test_validation_v2 |
| **P10** | Golden Build: critical 100% / extended ≥99% | `test_golden_rebuild`, `test_golden_framework_res` | **MỘT PHẦN** | Bộ golden chuẩn (64K, framework-res, core APK) + gate CI tự chạy |
| **P11** | Test Matrix T0–T3: 300+ tests | `tests/run_tests.py` (307) | ĐÃ CÓ | Duy trì, mở rộng theo phase mới |
| **P12** | Fuzz/Chaos: 5 invariant PARSER_SAFE/ENGINE_SAFE/STATE_VALID/TREE_CONTAINED/VALIDATE_SAFE | `fuzz.py`, CLI `fuzz` | ĐÃ CÓ | 60 lượt seed 7 sạch; chặn REMOVE_FILES xóa manifest; chạy định kỳ |

## M4 — RUNTIME VERIFIED (Lớp B)
| Phase | Nội dung | Module | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| **P13** | Runtime M2: install/launch/wait/pid/logcat/crash/ANR; M2_PASS/FAIL/SKIP + verdict | `apk-runtime` | ĐÃ CÓ | Nghiệm thu thật Pixel 7 M2_PASS; mở rộng benchmark ≥95% |
| **P14** | Runtime M3: scenario.json (launch/stop/wait/tap/swipe/input/keyevent/navigate/assert_*/screenshot) | `runtime_scenario.py`, `--scenario` | ĐÃ CÓ | Nghiệm thu 12 bước M3_PASS kèm ảnh; mở rộng M3 ≥80%→95% |
| **P15** | Failure Intelligence: ERROR_ID/STAGE/pattern/cause/fix/regression; sinh test tự động | `failure_db.py`, CLI `failure` | ĐÃ CÓ | 8 entry mặc định + gắn ERROR_ID vào runtime verify + CI |

## M5 — INTELLIGENT (Lớp C)
| Phase | Nội dung | Module | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| **P16** | Scanner V2: 4 mode FAST/NORMAL/FULL/RELEASE + evidence graph | `advisor.py` (coverage --mode), `apk-plan` | ĐÃ CÓ | FULL hết xấp xỉ (KISS 77.581→311.473 khớp); mode lạ bị chặn |
| **P17** | Simulation V2: 5 chiều PASS/EXPECTED_SKIP/UNSUPPORTED/BAD_PATCH/ENGINE_LIMIT + cache hash | `simulate.py` | ĐÃ CÓ | Cache 7415ms→81ms; sửa bug engine _tx ADD_FILES |
| **P18** | Evidence-based Plan: score + confidence + evidence (files/top_files) | `apk-plan` (bypass_plan.json) | ĐÃ CÓ | confidence % mỗi patch/combo + evidence graph |
| **P19** | Self-learning + LLM: LLM chỉ SUGGEST (--approve mới ghi combo; không tự apply) | `learn.py`, `suggest-llm` | ĐÃ CÓ | test_learn_smart |

## M6 — PERFORMANCE + PRODUCT (Lớp D)
| Phase | Nội dung | Module | Trạng thái | Việc cần làm |
|---|---|---|---|---|
| **P20** | Performance: cache scan/simulate/regex/candidate; workers tùy chọn | ScanCache, sim cache, `dex-budget --workers` | ĐÃ CÓ | Quét 70K method 1,78s (KPI<30s); workers>1 chậm trên máy 1 ổ → mặc định 1 |
| **P21** | Product UI: Workbench theo workflow, 7 khu vực, 3 chế độ người dùng | `webui/` | ĐÃ CÓ | Hoàn thiện 7 khu vực (Plan/Verify/Reports) + nối failure/self-learning |

## B.1 Dependency (bất biến — không nhảy cóc)
```
P0 → P1 → P2 → P3 → P4
                       ├── P5 → P6
                       └── P7 → P8 → P9 ── P10 ── P11 ── P12
                                                     ↓
                                        P13 → P14 → P15
                                                     ↓
                                        P16 → P17 → P18 → P19
                                                     ↓
                                                P20 → P21
```
- Chạy song song được: P5+P6 · P7+một phần P9 · P10+P11+P12 · chuẩn bị
  runtime/golden · P16+P17 khi dependency đủ.

## B.2 Lộ trình Sprint (10 sprint)
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

---

# PHẦN C — SÁU TẦNG THỐNG NHẤT (UPGRADE_PLAN_V4) — TỪNG TẦNG

| Tầng | Mô tả | Lệnh hiện có | Đầu ra | Trạng thái |
|---|---|---|---|---|
| **T1 — Inventory** | Quét nhanh: manifest, smali, resource, apktool.yml; cache theo hash cây APK | `scan`, `manifest`, `selfcheck` | `inventory.json` | đã có |
| **T2 — Candidate** | rg/index/hash lọc file ứng viên trước regex; không quét toàn bộ 477M | `coverage`, `roadmap` | danh sách ứng viên + lý do | đã có (tối ưu tốc độ Đợt A) |
| **T3 — Plan** | Điểm = bao phủ + số khớp + trọng số năng lực; xếp patch đơn + combo | `apk-plan`, `list` | `bypass_plan.json/md` | đã có |
| **T4 — Apply** | session chọn patch; engine idempotent + backup | `apply`, `session` | thay đổi thật trên cây | đã có |
| **T5 — Build** | apk-fix-res chuẩn hoá `$`; apktool b --aapt aapt2 | `apk-fix-res`, `apktool b` | APK chưa ký | đã có |
| **T6 — Verify** | zipalign + apksigner + verify; cài/emulator + logcat + mạng | `apk-test`, apksigner | APK ký + báo cáo | đã có |

- Vòng tự cải thiện: lỗi apply/build/verify → `_apk_error_exercises` →
  `improvements.json/md` → sửa toolkit/patch → test + rebuild.

---

# PHẦN D — TRỤC NÂNG CẤP T1–T7 (UPGRADE_PLAN_V3) — TỪNG TRỤC

| Trục | Nội dung chính | Việc cụ thể | Nghiệm thu |
|---|---|---|---|
| **T1 — Ngữ nghĩa mã** | Từ khớp chuỗi → hiểu code | Parser smali thành cây cú pháp, coverage theo method; nhận diện R8/ProGuard (mapping.txt); phát hiện packer (libjiagu/libDexHelper/TencentLegu); call-graph từ entry | Coverage theo method không tụt; giảm dương tính giả |
| **T2 — Sinh patch từ diff** | Đảo pipeline | `diff-apk ORIGINAL MODDED` sinh MATCH/REPLACE + ADD_FILES; vòng khép kín so hash | Tái sinh ≥90% patch mẫu |
| **T3 — Kiểm thử động** | Emulator/device | Cài APK, smoke test, logcat, bắt mạng; signature v2/v3/v4 + Play Integrity; split APK/bundle | M2/M3 trên APK thật; thiếu môi trường = trạng thái hợp lệ |
| **T4 — Thông minh** | Học + đề xuất | `combo --apk` roadmap động; kho combo thành công theo danh mục; LLM gợi ý có duyệt | 100% combo idempotent; LLM chỉ SUGGEST |
| **T5 — An toàn chuỗi cung ứng** | SLSA-lite | MANIFEST.json + hash toàn kho; cô lập EXECUTE_DEX (timeout, chặn shell, thư mục tạm, bộ lọc lệnh); cờ rủi ro | EXECUTE_DEX cô lập 100% |
| **T6 — Hiện đại hoá nền tảng** | apktool 2.x + aapt2 | decode/encode arsc, res modern (values-v31+); D8/R8 (R$, lambda, kotlin metadata); Unicode UTF-8 | Rebuild APK hiện đại OK |
| **T7 — Trải nghiệm & CI** | Dashboard + CI | Bảng điều khiển HTML (tìm/lọc/xem diff); CI scan/audit/optimize/simulate xuất diff số liệu; golden tests | Báo cáo trước/sau sau mỗi cập nhật |

## D.1 Ma trận nhu cầu ↔ trục
| Nhu cầu | T1 | T2 | T3 | T4 | T5 | T6 | T7 |
|---|---|---|---|---|---|---|---|
| R5 suy luận/tìm sâu | ● | ● | | ● | | | |
| R7 mô phỏng/code hiểu code | ● | ● | ● | | | | |
| R8 combo bổ trợ | | | | ● | | | ● |
| R9 AI đổi logic → bypass | ● | ● | ● | ● | | | |
| R11 cập nhật/CI | | | | | ● | ● | ● |
| R12 logic hiện đại | ● | ● | ● | ● | ● | ● | ● |

## D.2 Đợt triển khai T1–T7
- **Đợt 3.1 — Ngữ nghĩa + sinh patch (T1, T2)**: method-level coverage;
  diff-apk sinh patch; auto-adapt mapping.txt. Nghiệm thu: test ≥45; diff-apk
  ≥90%; coverage method không tụt.
- **Đợt 3.2 — Động + an toàn (T3, T5)**: sandbox EXECUTE_DEX; signature/
  Play Integrity; split APK. Nghiệm thu: EXECUTE_DEX cô lập 100%; báo cáo
  rủi ro; 3 patch BỎ-QUA kiểu NoUpdates chuyển sang kiểm tra được.
- **Đợt 3.3 — Thông minh + CI (T4, T6, T7)**: roadmap/combo động; học combo
  thành công; LLM gợi ý; dashboard + CI. Nghiệm thu: combo idempotent trên
  APK thật; CI xuất diff; dashboard duyệt/tải combo.

---

# PHẦN E — PHƯƠNG ÁN MỞ RỘNG P1–P5 (UPGRADE_PLAN_V3) — TỪNG PHƯƠNG ÁN

| PA | Tên | Khả thi | Nội dung | Nghiệm thu |
|---|---|---|---|---|
| **P1** | Khoá kỹ thuật smali | Cao, làm ngay, nền tảng | smali-lib: bump register an toàn, tìm call-site, chèn invoke có kiểm tra type, chuyển .locals↔.registers | Test ≥49 (đã 52/52); rebuild demo-apk sau khi chèn log/init |
| **P2** | Lộ trình bypass tự động theo APK thật | Cao, hiệu quả nhất | Nâng roadmap/combo --apk: phân tích manifest/smali → chuỗi patch (VIP+shell+token+integrity+trace) → áp → rebuild → M0/M1; vòng sửa lỗi rebuild | Tự chạy 3 APK mẫu → M1 ≥ 2/3 |
| **P3** | Hook tầng thấp / Frida | Trung bình, cần ngữ cảnh khác | Frida gadget inject (libfrida-gadget + config) bypass runtime; chuẩn bị khối HOOK_SCRIPT | 1 APK mẫu hook qua Frida, logcat xác minh |
| **P4** | Diff-APK + học mẫu | Trung bình, cần dữ liệu sạch | diff-apk ORIGINAL MODDED sinh patch; kho combo thành công gợi ý theo danh mục | Tái sinh ≥90% patch mẫu trên 1 cặp APK thật |
| **P5** | Kiểm thử động tự động | Thấp hơn, cần device | Emulator + adb: cài APK, smoke test, logcat, chụp mạng → M2/M3 | Pipeline chạy khi có device; thiếu môi trường = trạng thái hợp lệ |

- Thứ tự triển khai đề xuất: P1 (smali-lib + rebuild demo → M1) → P2
  (roadmap --apk có vòng sửa lỗi → M2/M3 trên APK thật) → P3/P4/P5 bổ sung.

---

# PHẦN F — PHÂN CÔNG THỰC THI (3 MÁY + AGENT SONG SONG)

## F.1 Bảng phân công 3 máy (2026-08-16)
| Máy | Vai trò | Việc chính | Ưu tiên |
|---|---|---|---|
| Máy THẬT (máy chính) | Main + Agent A/B | Chạy toolkit, adb server, tích hợp + regression gate, điều phối | P0→P9 |
| Client Samsung S26 (100.76.244.117) | Build/Runtime worker | Benchmark 64K DEX (ĐẠT), golden rebuild P10, runtime M2/M3 P13–P14 | P13–P14 |
| Client Pixel 7 (100.64.170.99) | Thiết bị test | Cài/kiểm thử APK, runtime M2/M3, logcat | P13–P14 |

## F.2 Agent song song
- **Main AI**: P0–P4 + tích hợp + regression + review + merge.
- **Agent A**: P5–P6 (DEX Resource + Strategy + test + benchmark).
- **Agent B**: P7–P9 (Preflight + Pipeline Gate + Validation).
- **Agent C**: P10–P12 (Golden + Test Matrix + Fuzz).
- **Agent D**: P16–P18 (Scanner + Evidence + Simulation + Scoring + Plan).
- **VM Worker**: decode/build/sign, 64K benchmark, golden build, M2/M3.
- **Device/Emulator**: install, launch, runtime M2/M3, logcat, screenshot,
  UI dump.

## F.3 Quy trình giao việc agent
```
MAIN AI → TASK CONTRACT → AGENT → IMPLEMENT → UNIT TEST → INTEGRATION TEST
→ MAIN REVIEW → GOLDEN/CI → PASS=merge / FAIL=failure artifact → agent fix
```
- Task Contract bắt buộc có: Objective · Input · Output · Files được phép sửa
  · API/contract · Acceptance criteria · Test command · Regression yêu cầu.
- Máy nào chỉ chạy phase ĐÃ ĐƯỢC PHÉP; cuối đợt gộp về máy chính → regression
  → so baseline → mới coi là xong.

---

# PHẦN G — KPI TỔNG THỂ (một bảng duy nhất)

| Nhóm | Chỉ số | Mục tiêu | Hiện tại (16/08) |
|---|---|---|---|
| Độ tin cậy | Rollback / Idempotency | 100% | 100% (test) |
| | Silent partial success / Unhandled crash / Known regression / DEX overflow | 0 | 0 |
| Build | Critical Golden | 100% | MỘT PHẦN (P10) |
| | Extended Golden | ≥99% | MỘT PHẦN |
| Test | Meaningful tests T0–T3 | 300+ | **307/307** (main + Pixel 7) |
| Runtime | M2 benchmark | ≥95% | KISS M2_PASS; zaz M2 FAIL (đang sửa) |
| | M3 benchmark | ≥80% → 95% | KISS 12 bước M3_PASS |
| Thông minh | Unexpected SKIP | <5% | theo dõi |
| Hiệu năng | Scan APK 477M | <30s (target <20s) | **23,6s** |
| | Simulation 60 patch | <30s (target <25s) | 81ms (cache) |
| | Full pipeline | <50s | theo dõi |

---

# PHẦN H — VIỆC TIẾP THEO ƯU TIÊN (hiện trạng 16/08 21:55)

1. **Đưa APK mục tiêu zaz (com.zaz.translate) qua M2/M3 — ưu tiên #1**.
   Root-cause đã rõ (patch debug-info làm hỏng DEX). Đang dở: cây sạch
   `apk_trees/zaz` + `patch_bypass_sigcheck_with_reflection` (292 thay đổi).
   Bước kế: kiểm tra `smali/com/anymy/reflection.smali` → đặt `%RSA_DATA%`
   nếu spoof chữ ký → `apk-fix-res` → `apktool b --aapt .../aapt2` → kiểm tra
   7 DEX hợp lệ → zipalign + ký → M2/M3 trên 3 máy.
2. **P10 Golden Build** — phase duy nhất còn MỘT PHẦN: chốt bộ golden chuẩn
   (64K, framework-res, core APK) + gate CI tự chạy mỗi đợt.
3. **M4 mở rộng benchmark**: M2 ≥95% / M3 ≥80%→95% trên bộ benchmark thay vì
   1 APK; gắn ERROR_ID từ failure_db vào mọi bước runtime.
4. **M6 UI**: hoàn thiện 7 khu vực (Plan/Verify/Reports), nối failure
   intelligence + self-learning, tùy chọn đóng gói APK UI.
5. **Baseline số thật**: chụp metrics.json chính thức + CI định kỳ giữ KPI.
6. **Đồng bộ 3 máy**: sau mỗi thay đổi chạy `sync_machines.sh` + md5; S26 cài
   `framework-res.apk` để lên 307/307; danh sách công việc `mau.csv` cập nhật
   theo chỉ đạo người dùng.
7. **Duy trì chuẩn**: test 307/307 · simulate 51 ĐẠT · scan 477M <30s · md5
   8/8 ✓ sau mỗi đợt.

---

# PHẦN I — DEFINITION OF DONE (một patch "thành công" thật sự)

Một patch chỉ được coi là thành công khi đi qua đủ chuỗi và sinh đủ artifact:
`scan.json` · `plan.json` · `preflight.json` · `transaction.json` ·
`validation.json` · `build.json` · `runtime.json` · `logs/` · `report/` —
kết thúc ở **PATCHX SUCCESS** (M2/M3 + regression).
