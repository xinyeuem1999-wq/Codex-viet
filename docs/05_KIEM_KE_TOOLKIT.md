# KIỂM KÊ TOOLKIT — trước khi tái cấu trúc

> Nhánh: `don-gian-hoa-toolkit`
>
> Mục đích: hiểu toolkit hiện tại trước khi đổi cấu trúc.
>
> **Nguyên tắc:** giai đoạn này **không xoá, không đổi tên, không di chuyển file**. Chỉ phân loại và xác định đường chạy.

## 1. Đường chạy chính cần nhớ

```text
Người dùng
  ↓
patchx
  ↓
patchx_core/cli.py
  ↓
┌──────────────────────────────────────────────────────────┐
│  Đọc/parse → Phân tích → Model → Tìm mục tiêu →          │
│  Plan → Preflight → Apply → Verify/Test                  │
└──────────────────────────────────────────────────────────┘

Nhánh chỉ đọc quan trọng:
APK tree → model.py/smali_sem.py → app_model.json
                         ↓
                 semantic_plan.py
                         ↓
                 plan_compile.py
                         ↓
                 preflight.py

Nhánh thực thi:
patch → parser.py → engine.py → cây APK
```

`cli.py` là cửa vào của các lệnh CLI; nó trực tiếp nạp parser, engine, audit, indexer và optimizer. fileciteturn28file0

---

## 2. Bảng lõi `patchx_core/`

| File | Làm gì | Ai gọi | Đường chạy chính? | Nhóm |
|---|---|---|---|---|
| `cli.py` | Cửa vào CLI, khai báo toàn bộ lệnh | `patchx` | **CÓ — trung tâm** | Điều phối |
| `parser.py` | Đọc/parse patch | `cli.py`, engine và các luồng xử lý patch | **CÓ** khi xử lý patch | Thực thi |
| `engine.py` | Bộ máy áp patch lên cây APK | `cli.py` (`apply`), các luồng mô phỏng/test | **CÓ** khi apply | Thực thi |
| `model.py` | Dựng model từ cây APK | `cli.py` (`model`) | **CÓ** trong phân tích | Phân tích |
| `smali_lib.py` | Tiện ích đọc/chuẩn hoá Smali | các module phân tích/validate | **CÓ** gián tiếp | Phân tích |
| `smali_sem.py` | Nhận dạng semantic/identity/call graph | `model.py`, `semantic_plan.py`, test | **CÓ** trong Semantic V2 | Phân tích |
| `semantic_plan.py` | Tìm/đánh giá mục tiêu theo kế hoạch | `cli.py` (`semantic-plan`), plan/acceptance/test | **CÓ** trong đường Semantic | Quyết định |
| `plan_compile.py` | Biến semantic plan thành transaction nháp | `cli.py` (`plan-compile`) | **CÓ** trong V2 | Kế hoạch |
| `preflight.py` | Kiểm tra an toàn trước khi apply | `cli.py` (`preflight`) và luồng kiểm tra | **CÓ** trước apply | An toàn |
| `smali_validate.py` | Kiểm tra tính hợp lệ Smali | validate/verify/test | **CÓ** khi validate | Kiểm tra |
| `audit.py` | Kiểm tra kiến trúc patch | `cli.py` (`audit`, `upgrade`, CI) | Không phải vòng apply tối thiểu | Kiểm tra |
| `indexer.py` | Quét patch, tạo index/report | `cli.py` (`scan`, `index`, `dupes`, report) | Không | Kho patch |
| `optimizer.py` | Gộp/tách/tối ưu patch | `cli.py` (`optimize`) | Không | Kho patch |
| `combo.py` | Tạo combo patch | `cli.py` (`combo`) | Không | Kho patch |
| `complement.py` | Bổ sung/đề xuất thành phần patch | các luồng suggest/optimizer | Không | Hỗ trợ |
| `acceptance.py` | Chạy nghiệm thu Semantic V2 fixture | `cli.py` (`acceptance`), test | **CÓ trong acceptance/test, không phải apply** | Kiểm thử |
| `baseline.py` | Chụp/đọc/so sánh baseline | `cli.py` (`baseline`), test | Không | Kiểm thử |
| `failure_db.py` | Kho lỗi và regression | `cli.py` (`failure`), test | Không | Bộ nhớ |
| `knowledge.py` | Kho tri thức outcome/fingerprint | `cli.py` (`knowledge`), test | Không bắt buộc | Bộ nhớ |
| `learn.py` | Hỗ trợ học từ kết quả | knowledge/test/luồng phụ | Không bắt buộc | Bộ nhớ |
| `advisor.py` | Gợi ý/đánh giá hỗ trợ | `cli.py` suggest/luồng phụ | Không | Trợ lý |
| `bypass_advisor.py` | Gợi ý nhóm bypass | luồng suggest/bypass | Không | Trợ lý |
| `risk.py` | Đánh giá rủi ro | các luồng lập kế hoạch/kiểm tra | Không bắt buộc | An toàn |
| `dex_budget.py` | Ước lượng giới hạn DEX | `cli.py` (`dex-budget`), validate | Không | Kiểm tra |
| `diffapk.py` | So sánh hai APK/cây và sinh patch | `cli.py` (`diff-apk`) | Không | Công cụ |
| `remote_map.py` | Lập bản đồ flag điều khiển từ xa | `cli.py` (`remote-map`) | Không | Công cụ |
| `runtime_scenario.py` | Mô tả/chạy kịch bản runtime | `cli.py`/simulate/test | Không | Kiểm thử |
| `simulate.py` | Mô phỏng áp patch | `cli.py` (`simulate`), CI | Không | Kiểm thử |
| `session.py` | Quản lý phiên xử lý | các luồng session | Không bắt buộc | Hỗ trợ |
| `fuzz.py` | Fuzz/chaos parser + engine | `cli.py` (`fuzz`), test | Không | Kiểm thử |
| `risk.py` | Mức rủi ro của thao tác | plan/verify | Không phải cửa vào | An toàn |
| `__init__.py` | Version/package metadata | `cli.py` | **Gián tiếp** | Hệ thống |

### 2.1 Ba file cần hiểu trước tiên

**1. `cli.py`** — biết người dùng gọi gì và lệnh nào đi vào module nào.

**2. `engine.py`** — biết lúc `apply` thực sự sửa cây APK như thế nào.

**3. `semantic_plan.py` + `smali_sem.py`** — biết Semantic V2 tìm target như thế nào trước khi cho phép thực thi.

Đây là bốn điểm cần đọc trước khi đổi tên/thư mục; không nên động vào toàn bộ 30 module cùng lúc.

---

## 3. File gốc liên quan trực tiếp đến toolkit

| File/thư mục | Vai trò | Chính hay phụ |
|---|---|---|
| `patchx` | Script launcher gọi package CLI | **Chính** |
| `patchx_core/` | Mã nguồn toolkit | **Chính** |
| `tests/run_tests.py` | Bộ regression hiện tại | **Chính cho phát triển** |
| `tests/fixtures/` | Dữ liệu test, gồm Semantic V2 | **Chính cho test** |
| `baseline/metrics.json` | Mốc chất lượng | **Chính cho regression** |
| `docs/` | Hướng dẫn vận hành/kiến trúc | Phụ trợ nhưng quan trọng |
| `.codex/skills/` | Hướng dẫn cho Codex/AI | **Không thuộc đường chạy core** |
| `tools/` | Công cụ benchmark/worker | Phụ |
| `webui/` | Giao diện web | Phụ, chỉ dùng khi chạy Web UI |
| `.tools/` | Binary/tool phụ trợ như aapt2 | Phụ trợ runtime/build |
| `git/`, `git-manager/` | Công cụ quản lý Git riêng | Không thuộc core patchx |

---

## 4. Dữ liệu tạo ra — không nên nhầm với mã nguồn

| Nhóm | Ví dụ | Ý nghĩa |
|---|---|---|
| Model | `.patchx/app_model.json` | Bản đồ phân tích APK; đầu vào cho Semantic V2 |
| Plan | `plan_v2.json`, `bypass_plan.json` | Mô tả ý định/kế hoạch |
| Evidence | candidates/evidence/report JSON | Bằng chứng và kết quả phân tích |
| Baseline | `baseline/metrics.json` | Mốc để phát hiện hồi quy |
| Report | `*_report.md/json` | Báo cáo, không phải code |
| Cache | `.patchx/*` | Dữ liệu tạm/trung gian |
| APK output | `real_apk_test/*`, `apks_patch/*` | Kết quả thử nghiệm/thực tế |

**`app_model.json` không phải engine.** Nó là dữ liệu do `model.py`/Semantic tooling tạo ra để các bước sau đọc. Lệnh `model` hiện được khai báo là “không áp patch”, và `semantic-plan` có thể dùng lại `app_model.json` thay vì quét lại cây APK. fileciteturn29file0

---

## 5. Các kho dữ liệu lớn trong repo

| Thư mục | Làm gì | Có thuộc đường chạy core không? |
|---|---|---|
| `upgraded/` | Bộ patch đã nâng cấp | **Dữ liệu đầu vào** |
| `backup/` | Bản sao patch cũ | Không |
| `combos/` | Patch combo đã sinh | Không bắt buộc |
| `combos_auto/` | Combo tự sinh | Không bắt buộc |
| `combos_auto_plus/` | Combo mở rộng | Không bắt buộc |
| `optimized/` | Patch đã tối ưu | Không bắt buộc |
| `bypass_plus/` | Nhóm patch bypass | Không bắt buộc |
| `real_apk_test/` | Kết quả thử APK thật | **Test/benchmark** |
| `apk_full_out/` | Kết quả phân tích APK | **Dữ liệu đầu ra** |
| `apk_plan_out/` | Kết quả lập plan | **Dữ liệu đầu ra** |
| `apk_runtime_out/` | Báo cáo runtime | **Dữ liệu đầu ra** |
| `dist/` | Gói phát hành | Không |
| `benchmarks/`, `bench_out/` | Benchmark | Không |
| `simulation_plus/` | Kết quả mô phỏng mở rộng | Không |

---

## 6. Những thứ nhìn giống code nhưng không nên đưa vào đường chạy chính

- `__pycache__/` và `patchx_core/__pycache__/`: bytecode sinh tự động.
- `*.bak`: bản sao cũ.
- `dist/*.zip`: gói phát hành.
- `real_apk_test/`: dữ liệu thử nghiệm thực tế.
- `backup/`: dữ liệu lưu trữ.
- `*_report.json`, `*_report.md`: báo cáo.
- `.codex/skills/`: hướng dẫn AI, không phải dependency bắt buộc của core.

Các nhóm này nên được **phân loại**, không nên vội xoá trong đợt tái cấu trúc đầu tiên.

---

## 7. Kết luận để tái cấu trúc

Ta chưa cần viết lại toolkit. Cấu trúc dễ hiểu nên quy về 5 vùng:

```text
1. VÀO CỬA
   patch → patchx → cli.py

2. HIỂU APK
   model.py → smali_lib.py → smali_sem.py

3. QUYẾT ĐỊNH
   semantic_plan.py → plan_compile.py → preflight.py

4. LÀM VIỆC
   parser.py → engine.py → smali_validate.py

5. HỖ TRỢ / KIỂM THỬ
   acceptance, baseline, failure_db, knowledge,
   simulate, fuzz, audit, optimizer, combo, reports...
```

**Quy tắc tái cấu trúc:**

1. Không xoá chức năng.
2. Không đổi hành vi trước khi có test chứng minh tương đương.
3. Không đổi tên file lõi ngay trong bước đầu.
4. Trước tiên chỉ tạo bản đồ và đường chạy.
5. Sau khi người dùng hiểu được đường chạy, mới gom file theo nhóm.
6. Sau mỗi lần gom phải chạy regression.

### Trạng thái

- [x] Xác định branch `don-gian-hoa-toolkit`.
- [x] Kiểm kê cây repo.
- [x] Xác định `cli.py` là cửa vào.
- [x] Xác định nhóm Model/Semantic/Plan/Preflight/Apply.
- [x] Ghi bảng kiểm kê đầu tiên.
- [ ] Chưa di chuyển file.
- [ ] Chưa xoá file.
- [ ] Chưa đổi tên module lõi.
- [ ] Bước kế tiếp: đối chiếu `cli.py` → từng module → test để tạo **bảng phụ thuộc chính xác** trước khi gom thư mục.
