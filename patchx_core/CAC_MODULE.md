# CÁC MODULE — ĐỂ LÀM GÌ?

Đây là bảng tra nhanh. Không phải module nào cũng cần hiểu để dùng patchx.

## Luồng chính

- `parser.py` — đọc cấu trúc patch.
- `indexer.py` — quét/index kho patch.
- `engine.py` — bộ máy áp patch.
- `semantic_plan.py` — kế hoạch tìm mục tiêu theo ngữ nghĩa.
- `plan_compile.py` — chuyển kế hoạch thành transaction nháp.
- `preflight.py` — cửa kiểm tra trước khi thực hiện.
- `acceptance.py` — kiểm tra nghiệm thu.

## Phân tích / nhận diện

- `model.py` — mô hình trung gian của APK.
- `advisor.py` — phân tích/đề xuất.
- `knowledge.py` — kho kết quả đã biết.
- `learn.py` — xử lý học/kết quả.
- `remote_map.py` — lập bản đồ flag từ xa.
- `diffapk.py` — tìm khác biệt giữa APK/cây.

## Kho patch

- `audit.py` — kiểm tra kiến trúc patch.
- `optimizer.py` — gộp/tối ưu/tách xung đột.
- `combo.py` — ghép nhóm patch.
- `complement.py` — tìm phần bổ sung.
- `baseline.py` — trạng thái chuẩn.
- `failure_db.py` — cơ sở dữ liệu lỗi.

## Kiểm tra chuyên sâu

- `smali_lib.py`, `smali_sem.py`, `smali_validate.py` — xử lý/kiểm tra Smali.
- `dex_budget.py` — kiểm tra ngân sách tham chiếu DEX.
- `risk.py` — đánh giá rủi ro.
- `fuzz.py` — kiểm thử phá vỡ parser/engine.
- `runtime_scenario.py` — kịch bản runtime.
- `simulate.py` — mô phỏng.

## Chức năng phụ / nâng cao

- `bypass_advisor.py` — tư vấn nhóm bypass.
- `suggest` / `suggest_apk` / `suggest_llm` — gợi ý.
- `remote_patch` — tạo patch từ flag từ xa.
- `roadmap` — lập lộ trình.
- `optimizer` / `dex_budget` / `fuzz` — dùng khi cần kiểm tra sâu.

## Quy tắc đọc code

Nếu chỉ muốn vận hành patchx: đọc `cli.py` → `engine.py` → `parser.py` → `preflight.py` trước.

Nếu muốn hiểu nhận diện mục tiêu: đọc thêm `model.py` → `semantic_plan.py` → `advisor.py`.

Không cần mở 30 module cùng lúc.
