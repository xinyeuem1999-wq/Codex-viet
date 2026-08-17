# Cấu trúc PatchX

Mục tiêu: tên thư mục ngắn, tiếng Việt, không dùng tiền tố số trong tên Python.

```text
patchx_core/
├── co_ban/      # engine, model, parser, session, smali_lib
├── phan_tich/   # indexer, remote_map, smali_sem
├── ke_hoach/    # semantic_plan, plan_compile
├── kiem_tra/    # acceptance, audit, baseline, dex_budget, preflight, risk, smali_validate
├── thuc_thi/    # combo, complement, optimizer, runtime_scenario, simulate
├── tri_thuc/    # advisor, bypass_advisor, failure_db, knowledge, learn
├── cong_cu/     # diffapk, fuzz
└── cli/         # cli
```

## Nguyên tắc chuyển

- `patchx_core/` là package điều phối.
- Mỗi nhóm là một package Python có `__init__.py`.
- Không dùng `01_co_ban`, `02_phan_tich`... vì tên module Python bắt đầu bằng số gây `SyntaxError` khi import.
- Chỉ di chuyển module sau khi sửa toàn bộ import của module đó.
- `patchx_core/cli/` là package; entry point ngoài vẫn có thể giữ nguyên.
- Các file không có trong source hiện tại không tự tạo (`analyze.py`, `coverage.py`, `plan_preflight.py`, `roadmap.py`, `remote_patch.py`).

## Trạng thái nhánh

Nhánh này đang ở **bước dựng khung an toàn**. Source cũ vẫn giữ nguyên để không làm hỏng import hiện tại. Sau khi khung được kiểm tra, mới di chuyển từng nhóm module và cập nhật import.
