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
                 plan_preflight / preflight

Nhánh thực thi:
patch → parser.py → engine.py → cây APK
```

`cli.py` là cửa vào CLI. File này hiện khai báo các lệnh từ quét kho patch, phân tích APK, model, Semantic V2, plan, preflight, apply, test và các công cụ phụ trợ. Đây là **điểm điều phối**, không phải nơi chứa toàn bộ logic xử lý.

---

## 2. Bảng lõi `patchx_core/`

| File | Làm gì | Ai gọi | Đường chạy chính? | Nhóm |
|---|---|---|---|---|
| `cli.py` | Cửa vào CLI, khai báo toàn bộ lệnh | `patchx` | **CÓ — trung tâm** | Điều phối |
| `parser.py` | Đọc/parse patch | CLI/engine và các luồng patch | **CÓ** khi apply | Thực thi |
| `engine.py` | Bộ máy áp patch lên cây APK | CLI `apply`, mô phỏng/test | **CÓ** khi apply | Thực thi |
| `model.py` | Dựng model từ cây APK | CLI `model`, Semantic | **CÓ** trong phân tích | Phân tích |
| `smali_lib.py` | Tiện ích đọc/chuẩn hoá Smali | model/semantic/validate | **CÓ** gián tiếp | Phân tích |
| `smali_sem.py` | Identity, semantic matching, caller/callee | model, semantic-plan, acceptance/test | **CÓ** trong Semantic V2 | Phân tích |
| `semantic_plan.py` | Tìm/đánh giá target theo kế hoạch | CLI, plan, acceptance/test | **CÓ** trong Semantic | Quyết định |
| `plan_compile.py` | Biến plan thành transaction nháp | CLI `plan-compile` | **CÓ** trong V2 | Kế hoạch |
| `preflight.py` | Cổng kiểm tra trước thao tác | CLI `preflight` và luồng kiểm tra | **CÓ** trước apply khi dùng cổng này | An toàn |
| `smali_validate.py` | Kiểm tra Smali | validate/verify/test | **CÓ** khi validate | Kiểm tra |
| `audit.py` | Kiểm tra kiến trúc patch | CLI `audit`, `upgrade`, CI | Không thuộc apply tối thiểu | Kiểm tra |
| `indexer.py` | Quét patch, index, report | CLI `scan`, `index`, `dupes`, report | Không | Kho patch |
| `optimizer.py` | Gộp/tách/tối ưu patch | CLI `optimize` | Không | Kho patch |
| `combo.py` | Tạo combo patch | CLI `combo` | Không | Kho patch |
| `complement.py` | Thành phần bổ sung/đề xuất | luồng suggest/optimizer | Không bắt buộc | Hỗ trợ |
| `acceptance.py` | Nghiệm thu Semantic V2 fixture | CLI `acceptance`, test | **Test/acceptance**, không phải apply | Kiểm thử |
| `baseline.py` | Chụp/đọc/so sánh baseline | CLI `baseline`, test | Không thuộc apply | Kiểm thử |
| `failure_db.py` | DB lỗi/regression | CLI `failure`, test | Không | Bộ nhớ |
| `knowledge.py` | Kho outcome/fingerprint | CLI `knowledge`, test | Không bắt buộc | Bộ nhớ |
| `learn.py` | Hỗ trợ học từ kết quả | knowledge/luồng phụ | Không bắt buộc | Bộ nhớ |
| `advisor.py` | Gợi ý/phân tích hỗ trợ | suggest/luồng phụ | Không | Trợ lý |
| `bypass_advisor.py` | Gợi ý bypass | suggest/bypass | Không | Trợ lý |
| `risk.py` | Đánh giá rủi ro | plan/verify/luồng phụ | Không phải cửa vào | An toàn |
| `dex_budget.py` | Ước lượng DEX refs | CLI `dex-budget`, validate | Không | Kiểm tra |
| `diffapk.py` | So sánh hai APK/cây, sinh patch | CLI `diff-apk` | Không | Công cụ |
| `remote_map.py` | Lập bản đồ flag remote | CLI `remote-map` | Không | Công cụ |
| `runtime_scenario.py` | Kịch bản runtime | simulate/test | Không | Kiểm thử |
| `simulate.py` | Mô phỏng áp patch | CLI `simulate`, CI | Không | Kiểm thử |
| `session.py` | Quản lý phiên | luồng session | Không bắt buộc | Hỗ trợ |
| `fuzz.py` | Fuzz/chaos parser + engine | CLI `fuzz`, test | Không | Kiểm thử |
| `__init__.py` | Version/package metadata | CLI | **Gián tiếp** | Hệ thống |

### Điểm quan trọng

Không nên gọi tất cả các file trên là “core chạy cùng nhau”. Có ba lớp khác nhau:

```text
A. ĐƯỜNG CHÍNH
cli → parser/engine
cli → model → semantic → plan → preflight

B. CÁC CỬA CÔNG CỤ RIÊNG
scan/index/audit/optimize/combo/diff/remote/simulate...

C. HỖ TRỢ / DỮ LIỆU / KIỂM THỬ
acceptance/baseline/failure/knowledge/fuzz/tests/reports...
```

Điều này giải thích vì sao repo hiện tại có nhiều module nhưng không có nghĩa mỗi module đều chạy khi `python3 patchx` hoặc khi `apply`.

---

## 3. `cli.py` — bản đồ lệnh hiện tại

Đây là bảng vận hành cần giữ để sau này người dùng chỉ cần nhìn một chỗ:

| Lệnh | Vai trò dễ hiểu | Có sửa APK không? |
|---|---|---:|
| `scan` | Xem kho patch | Không |
| `index` | Tạo danh mục kho patch | Không |
| `dupes` | Tìm patch trùng | Không |
| `manifest` | Ghi danh sách/hash kho | Không |
| `verify-manifest` | Kiểm tra kho có bị đổi | Không |
| `report` | Tạo báo cáo | Không |
| `ci` | Chạy chuỗi kiểm tra tự động | Tuỳ bước bên trong |
| `golden` | Chạy kiểm thử chuẩn | Không |
| `validate` | Kiểm tra cây APK | Không |
| `apk-prepare` | Giải mã APK | Tạo cây đầu ra |
| `audit` | Kiểm tra cấu trúc patch | Không |
| `upgrade` | Nâng cấp patch an toàn | Tạo đầu ra mới |
| `optimize` | Tối ưu/gộp patch | Tạo đầu ra mới |
| `apply` | **Áp patch vào cây APK** | **CÓ** |
| `coverage` | Đo patch có chạm mục tiêu không | Không |
| `suggest` | Gợi ý cải tiến | Không |
| `analyze` | Phân tích APK | Không |
| `model` | **Tạo bản đồ `app_model.json`** | Không |
| `semantic-plan` | **Tìm mục tiêu theo plan** | Không |
| `acceptance` | Chạy nghiệm thu V2 | Không |
| `plan-compile` | Tạo transaction nháp | Không |
| `plan-preflight` | Kiểm tra transaction nháp | Không |
| `knowledge` | Ghi/tra kho tri thức | Không |
| `diff-apk` | Tìm khác biệt hai APK | Không |
| `suggest-apk` | Gợi ý patch cho APK | Không |
| `suggest-llm` | Tạo khung đề xuất từ ý định | Không |
| `roadmap` | Lập lộ trình mod | Không |
| `combo` | Gộp patch hỗ trợ nhau | Tạo đầu ra |
| `simulate` | Mô phỏng | Không sửa APK thật |
| `selfcheck` | Kiểm tra chính toolkit | Không |
| `remote-map` | Tìm flag remote | Không |
| `remote-patch` | Sinh patch từ flag | Tạo patch |
| `baseline` | Quản lý mốc chất lượng | Không |
| `dex-budget` | Kiểm tra ngân sách DEX | Không |
| `preflight` | Cổng kiểm tra trước apply | Không |
| `fuzz` | Kiểm thử lỗi parser/engine | Không |
| `failure` | Quản lý DB lỗi/regression | Không |
| `test` | Chạy bộ test | Không |

**Đây là bản đồ vận hành.** Người dùng không cần biết 30 module để sử dụng toolkit; trước mắt chỉ cần nhớ các lệnh chính.

---

## 4. File gốc liên quan trực tiếp

| File/thư mục | Vai trò | Chính hay phụ |
|---|---|---|
| `patchx` | Launcher vào CLI | **Chính** |
| `patchx_core/` | Mã nguồn toolkit | **Chính** |
| `tests/run_tests.py` | Regression hiện tại | **Chính cho phát triển** |
| `tests/fixtures/` | Fixture kiểm thử | **Chính cho test** |
| `baseline/metrics.json` | Mốc chất lượng | **Chính cho regression** |
| `docs/` | Tài liệu | Phụ trợ quan trọng |
| `.codex/skills/` | Hướng dẫn AI/Codex | Không phải core runtime |
| `.tools/` | Công cụ/binary phụ trợ | Phụ trợ runtime/build |

Repo hiện có thêm nhiều cây dữ liệu, kết quả và tài liệu; **chưa được phép coi chúng là module chạy chính chỉ vì chúng nằm ở root**.

---

## 5. Dữ liệu — không nhầm với mã nguồn

| Nhóm | Ví dụ | Cách hiểu |
|---|---|---|
| Model | `.patchx/app_model.json` | Bản đồ APK |
| Plan | `plan_v2.json`, `bypass_plan.json` | Ý định/kế hoạch |
| Evidence | candidate/evidence JSON | Bằng chứng phân tích |
| Baseline | `baseline/metrics.json` | Mốc chất lượng |
| Report | `*_report.md/json` | Báo cáo |
| Cache | `.patchx/*` | Dữ liệu trung gian |
| APK output | `real_apk_test/*`, `apk_*_out/*` | Kết quả test/phân tích |

**`app_model.json` không phải engine.** Lệnh `model` tạo nó; `semantic-plan` có thể đọc lại model đã có thay vì quét APK lại.

---

## 6. Test và fixture

`tests/` hiện có:

```text
tests/
├── run_tests.py
├── fixtures/
└── __pycache__/
```

`tests/run_tests.py` là file test lớn và đang chứa regression cho nhiều thế hệ tính năng. Vì vậy **không nên chia lại test hoặc đổi tên test trước khi kiểm kê mapping test → module**.

`tests/fixtures/` là dữ liệu kiểm thử; đặc biệt fixture Semantic V2 đang dùng để kiểm tra nhận diện mục tiêu và obfuscation. Đây là dữ liệu, không phải code runtime.

---

## 7. Những thứ không được tự động xoá trong đợt này

- `__pycache__/`
- các file backup
- các cây APK/output
- report JSON/MD
- dữ liệu benchmark/simulation
- patch cũ/nâng cấp
- `.tools/`
- `.codex/skills/`

Chúng có thể được đề xuất phân loại sau, nhưng **chỉ di chuyển/xoá khi người dùng đồng ý**.

---

## 8. Trạng thái kiểm kê

- [x] Kiểm tra đúng branch `don-gian-hoa-toolkit`.
- [x] Xác định `patchx` → `cli.py` là cửa vào.
- [x] Xác định nhóm Model/Semantic/Plan/Preflight/Apply.
- [x] Xác định `tests/run_tests.py` và `tests/fixtures/` là vùng phát triển/test.
- [x] Tách khái niệm **code runtime** khỏi **model/report/cache/output**.
- [x] Lập bảng vận hành các lệnh CLI.
- [ ] Hoàn thiện call graph `module → module` cho toàn bộ `patchx_core`.
- [ ] Đối chiếu từng module với test gọi nó.
- [ ] Đánh dấu module chỉ được gọi bởi lệnh phụ.
- [ ] Sau khi hoàn tất kiểm kê mới đề xuất cấu trúc thư mục mới.
- [ ] **Chưa xoá file.**
- [ ] **Chưa đổi tên file.**
- [ ] **Chưa di chuyển file.**

## 9. Quy tắc làm việc với người dùng

**Bất kỳ thay đổi cấu trúc nào** như:

```text
đổi tên
↓
di chuyển
↓
gộp file
↓
tách file
↓
xoá file
↓
thay đổi import/path
```

đều phải **hỏi người dùng trước**.

Trong lúc chưa được đồng ý, chỉ được:

```text
đọc → kiểm kê → giải thích → ghi tài liệu → test
```

Mục tiêu của đợt này là làm cho toolkit **dễ hiểu và dễ vận hành hơn**, không phải viết lại toolkit.
