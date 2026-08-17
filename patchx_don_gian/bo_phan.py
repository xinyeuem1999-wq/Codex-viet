# -*- coding: utf-8 -*-
"""Bản đồ 5 bộ phận của patchx.

Mỗi tên bên dưới chỉ là IMPORT/ALIAS tới code cũ; không có logic mới.
"""

# 1. MẮT: đọc và tạo dữ liệu phân tích
from patchx_core import parser as doc_patch
from patchx_core import indexer as quet_kho
from patchx_core import model as mo_hinh
from patchx_core import semantic_plan as tim_muc_tieu

# 2. BỘ NÃO: lập và biên dịch kế hoạch
from patchx_core import semantic_plan as bo_nao
from patchx_core import plan_compile as lap_ke_hoach

# 3. KIỂM TRA: chặn trước khi thực hiện
from patchx_core import preflight as kiem_tra_truoc
from patchx_core import smali_validate as kiem_tra_smali
from patchx_core import dex_budget as kiem_tra_dex
from patchx_core import baseline as moc_an_toan

# 4. NGƯỜI THỢ: thực hiện patch
from patchx_core import engine as thuc_thi
from patchx_core import audit as kiem_tra_patch

# 5. BỘ NHỚ: kết quả, lỗi và tri thức đã lưu
from patchx_core import knowledge as tri_thuc
from patchx_core import failure_db as bo_nho_loi
from patchx_core import learn as hoc_tu_ket_qua
