# CÁCH ĐỌC KÝ HIỆU PHÁT ĐỒ PATCHX (BẢNG TRA)

- Ngày: 2026-08-16. Mục đích: giải thích vì sao có các ký hiệu trùng chữ
  (M2/M3, P1/P2, T1/T7…) và cách đọc/sắp xếp vị trí cho đúng.
- Quy tắc vàng: **cùng một chữ cái, ở tài liệu khác nhau = nghĩa khác nhau**.
  Luôn đọc kèm ngữ cảnh + cụm từ đi sau chữ cái.

---

## 1. BẢNG TRA TỪNG KÝ HIỆU

| Ký hiệu | Tên đầy đủ | Nghĩa | Dùng ở đâu | Ví dụ |
|---|---|---|---|---|
| **M0–M3** | Acceptance (nghiệm thu APK) | Mức kết quả trên 1 APK thật: M0 áp được · M1 rebuild được · M2 cài được · M3 vượt kiểm tra | UPGRADE_PLAN_V3 §6, DE_XUAT_THONG_NHAT §4 | "zaz M2 FAIL" = chưa cài được |
| **M0–M6** | Milestone phát triển | Chặng phát triển của toolkit: M0 FOUNDATION → M6 PRODUCT/SCALE | DE_XUAT_THONG_NHAT §5 | "M4 — RUNTIME VERIFIED" |
| **P0–P21** | Phase triển khai | 22 hạng mục công việc nằm trong 7 milestone M0–M6 | DE_XUAT_THONG_NHAT §5 | "P10 Golden Build", "P21 Workflow UI" |
| **P1–P5** | Phương án mở rộng | 5 hướng phát triển đề xuất (smali-lib, bypass tự động, Frida, diff-apk, dynamic test) — KHÁC phase P0–P21 | UPGRADE_PLAN_V3 §7 | "P1 — KHOÁ KỸ THUẬT SMALI" |
| **T1–T6** | Tầng pipeline | 6 bước dây chuyền: Inventory → Candidate → Plan → Apply → Build → Verify | UPGRADE_PLAN_V4 §2 | "T4 — Apply" |
| **T1–T7** | Trục nâng cấp | 7 hướng công nghệ: ngữ nghĩa mã, diff-apk, dynamic, thông minh, an toàn, nền tảng, CI | UPGRADE_PLAN_V3 §2 | "T1 — Ngữ nghĩa mã" |
| **T0–T3** | Test matrix | 4 cấp kiểm thử: T0 Core · T1 Engine · T2 APK · T3 Runtime | DE_XUAT_THONG_NHAT §7, P11 | "phủ T0–T3, 300+ tests" |
| **R1–R12** | Yêu cầu người dùng | Các yêu cầu gốc từ lịch sử hội thoại | UPGRADE_PLAN_V3 §1 | "R5 suy luận/tìm sâu", "R9 bypass" |
| **GATE 1–6** | Cổng kiểm soát | ANALYSIS · PLAN · PREFLIGHT · VALIDATION · BUILD · RUNTIME | DE_XUAT_THONG_NHAT §3.3 | "GATE 3 PREFLIGHT" |
| **F-XXX-###** | ERROR_ID (mã lỗi) | `F-BUILD-001`, `F-DEX-001`, `F-PATCH-001`, `F-RUNTIME-001`, `F-ENV-001`, `F-SCAN-001` | `patchx_core/failure_db.py` | "F-BUILD-002" |
| **E1/E2** | — | **KHÔNG tồn tại** trong toolkit/tài liệu — không có dãy ký hiệu E. Nếu gặp "E" hãy đối chiếu ERROR_ID dạng F-… | — | — |
| **Đợt A–D** | Đợt nghiệm thu | A tốc độ scan · B apk-full · C runtime · D golden | UPGRADE_PLAN_V4 §7 | "Đợt C — Runtime verify" |

## 2. VÌ SAO TRÙNG CHỮ?

- Các tài liệu được viết ở **các thời điểm khác nhau** (V3 14/08, V4 14/08,
  DE_XUAT_THONG_NHAT 16/08), mỗi tài liệu đặt ký hiệu riêng, không thống nhất
  trước → chữ cái bị dùng lại: M (2 nghĩa), P (2 nghĩa), T (3 nghĩa).
- Hệ quả: "M2" có thể là **milestone RESOURCE SAFE** hoặc **mức nghiệm thu
  "cài được"**; "P1" có thể là **phase Contract** hoặc **phương án smali-lib**;
  "T1" có thể là **tầng Inventory** hoặc **trục ngữ nghĩa mã** hoặc **test T1
  Engine**.

## 3. CÁCH ĐỌC ĐÚNG (3 bước)

1. **Xác định tài liệu gốc** đang nói tới (UPGRADE_PLAN_V3 / V4 /
   DE_XUAT_THONG_NHAT / báo cáo runtime).
2. **Xác định ngữ cảnh**: đang nói về kết quả APK, lộ trình phát triển,
   công nghệ, hay lỗi?
3. **Tra bảng ở mục 1** — cụm từ sau chữ cái sẽ tự khớp nghĩa (vd: "M2 —
   RESOURCE SAFE" = milestone; "M2 (cài + mở + không crash)" = acceptance).

## 4. CÁCH SẮP XẾP VỊ TRÍ ĐÚNG (quan hệ giữa các ký hiệu)

```
LỘ TRÌNH PHÁT TRIỂN (làm cái gì, theo thứ tự nào)
  Milestone M0 ── M1 ── M2 ── M3 ── M4 ── M5 ── M6
     mỗi milestone chứa Phase P0–P21 (dependency cố định)
     mỗi phase chạy trong Sprint 0–9 (kèm người thực hiện)
     điều phối qua 3 máy + Agent A/B/C/D

HƯỚNG CÔNG NGHỆ (nâng cấp theo chiều sâu — song song được)
  Trục T1–T7 (V3) ── triển khai theo Đợt 3.1 (T1,T2) / 3.2 (T3,T5) / 3.3 (T4,T6,T7)
  Phương án P1–P5 (V3 §7) ── thứ tự P1 → P2 → P3/P4/P5

DÂY CHUYỀN VẬN HÀNH (chạy trên APK thật mỗi lần)
  Tầng T1 Inventory → T2 Candidate → T3 Plan → T4 Apply → T5 Build → T6 Verify
  qua 6 GATE, chấm điểm theo DEX gate, kết thúc bằng nghiệm thu M0→M1→M2→M3

KIỂM SOÁT CHẤT LƯỢNG
  Test matrix T0–T3 (300+ test) · ERROR_ID F-…-### · KPI (mục 7 DE_XUAT_THONG_NHAT)
```

## 5. MẸO NHỚ NHANH

- **M0–M3** (3 mức) = đo **APK**; **M0–M6** (7 chặng) = đo **toolkit**.
- **P0–P21** = việc **phải làm**; **P1–P5** = phương án **nên làm** (ưu tiên).
- **T1–T6** (V4) = **bước chạy**; **T1–T7** (V3) = **hướng nâng cấp**;
  **T0–T3** = **cấp test**.
- **E1/E2 không tồn tại** — mã lỗi là `F-<STAGE>-<số>`.
- Gặp ký hiệu lạ → tra bảng mục 1 trước khi kết luận.
