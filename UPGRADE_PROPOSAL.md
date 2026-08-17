# Đề xuất nâng cấp patchx — đợt 2 (sau cập nhật bộ sưu tập)

- Ngày: 2026-08-14 (quét lại sau khi bộ sưu tập được cập nhật)
- Phong cách: giữ nguyên quy ước cũ — tài liệu/bình luận bằng tiếng Việt;
  danh từ/chuỗi trong mã nguồn và nội dung patch giữ nguyên gốc.

## 1. Bối cảnh mới (xác nhận từ người dùng + quét lại)

- Bộ patch cũ trong `/Patch` đã được **cập nhật bằng file mới trong
  "patch update"** và người dùng **đã xóa các file cũ** — vì vậy 6 thư mục
  phân loại hiện trống là đúng như thiết kế, không phải mất dữ liệu.
- Nguồn "patch update" định vị được: **`/storage/emulated/0/Modder Hub/Apk
  Editor Patches/`** (700 MB, 22 zip + công cụ). Chứa bản mới của nhiều
  patch đang có trong `/Patch`: `SignatureHack_arm64`, `UnPacker`,
  `Bypass_sigcheck_with_reflection+(Dec_2022)`, `Translate Debuger`,
  `Translate Obfuscation`, `Root`, `SignLauncher`, `Sign_Hack_HTC`, ...
- So sánh mẫu:
  - `SignatureHack_arm64`: `patch.txt` **giống hệt** bản cũ — chỉ khác
    `libfrida-gadget.so` (bản trong `/Patch` hỏng nén, bản Modder Hub lành).
  - `UnPacker` / `Bypass_sigcheck`: có nội dung mới hơn (thêm tác giả,
    cập nhật khối) — đúng nghĩa "bản cập nhật".
- Bộ sưu tập hiện tại: **165 zip / 16 thư mục**; `1. PATCH others/` có
  **59 zip** (lúc đánh giá cũ là 58) — bản `SignatureHack_arm64.zip` mới
  thêm vào đang lỗi nén entry `libfrida-gadget.so` (bản Modder Hub lành:
  sha256 `d7f910309111`).

## 2. Vấn đề phát sinh cần sửa

1. **`SignatureHack_arm64.zip` trong `/Patch` hỏng entry `libfrida-gadget.so`**
   — giải nén lỗi "invalid stored block lengths". Có file lành để thay thế.
2. **Bộ test không chạy được**: `python3 patchx test` văng
   `FileNotFoundError` — `COLLECTION` trỏ về `1. PATCH others/` nhưng
   `AddSave.zip`, `NoInternetWifi.zip`, `Installocation.zip` không còn ở đó
   (đã ở `upgraded/`; `Installocation.zip` tách thành 3 file
   `Installocation_Авто/Внешняя/Внутренняя`). Kết quả "25/25" cũ không
   tái lập từ bố cục hiện tại.
3. **patchx mới chỉ quét `1. PATCH others/`** — chưa bao quát bộ cập nhật
   mới ở Modder Hub và 6 thư mục đã trống.

## 3. Đề xuất ưu tiên

### Đã thực hiện (2026-08-14, sau khi người dùng chỉ định `upgraded/` làm bộ làm việc)

**Đợt 2 — cập nhật phần 2 (bộ 59 patch mới) + nâng cấp script:**

- Tái sinh `upgraded/` từ bộ **59 patch mới** (bản cũ sao lưu tại
  `backup/upgraded_old_20260814-121210`).
- `optimize`: 59 patch → **12 tệp**, gộp trùng **19 khối**, tách **20 xung đột**.
- `combo`: **74 combo** + **13 combo tự phát hiện** (20 patch cô lập liệt kê rõ).
- Lệnh mới: `dupes`, `manifest`, `report` (HTML một file), `apk-prepare`;
  cờ `--recursive` cho scan/index/audit; `simulate --dex-runner/--dex-timeout/--apk`.
- Sửa 3 lỗi engine phát hiện từ patch mới:
  1. **ADD_FILES TARGET `/`/tuyệt đối** (Password_login_english từng ghi vào
     `/smali`): `TARGET: /` giải về gốc cây, chặn đường dẫn tuyệt đối và `..`;
     non-EXTRACT phải là đường dẫn tệp.
  2. **Vòng lặp GOTO** (RES-ID — patch 27.319 khối bị chặn bởi MAX_STEPS=2000):
     thay bằng phát hiện chu trình thực sự (theo dấu chỉ mục khối mỗi lượt).
  3. **`_literal_hint` lọc nhầm** (Debug_information — regex nhiều nhánh `|`
     lấy hint từ nhánh khác mẫu đã chèn): bỏ hint khi có `|` ở mức cao nhất,
     không coi `\d/\w/\s` là literal cố định.
- Test: bộ tự kiểm tra tự chứa (không phụ thuộc bố cục dữ liệu) — **43/43 đạt**.
- Mô phỏng `upgraded/` (59 patch): **50 ĐẠT | 0 THẤT-BẠI | 9 BỎ-QUA | 0 LỖI**
  (9 BỎ-QUA = 2 guard idempotency + 7 patch nhắm tệp không có trong cây giả lập).

- **A1 — Sửa `SignatureHack_arm64.zip`**: thay bằng bản lành từ Modder Hub
  (sha256 `d7f910309111`) ở cả `1. PATCH others/` và `upgraded/`; bản hỏng
  giữ tại `_patchx/backup/SignatureHack_arm64.zip.bak`.
- **A2 — Sửa bộ test**: `COLLECTION` trỏ về `upgraded/`; test zip lồng nhau
  dựng fixture tổng hợp (không phụ thuộc bố cục); test phát hiện A02 dùng
  mẫu tự dựng; thêm test "zip hỏng asset không crash". Kết quả: **30/30**.
- **A3 — Chống lỗi zip nén**: `parser.py` bắt `zlib.error/EOFError/OSError`
  khi đọc asset, ghi vào `patch.issues`; `selfcheck` in cảnh báo entry hỏng,
  không văng exception. `selfcheck` gốc và `upgraded/`: **59 patch, 0 lỗi**.
- **Simulate — guard idempotency**: thêm `_guard_skip` — MATCH_GOTO dạng
  chuỗi literal kèm ADD_FILES (guard đánh dấu đã patch) được phân loại
  `BỎ-QUA` kèm ghi chú thay vì `THẤT-BẠI`. Mô phỏng `upgraded/`
  (59 patch): **55 ĐẠT | 0 THẤT-BẠI | 4 BỎ-QUA | 0 LỖI**.

### Còn lại theo thứ tự

### Đợt 1 — Đồng bộ dữ liệu + sửa nền tảng (làm trước)

- **A0. Nhập bản cập nhật từ Modder Hub vào bộ sưu tập**: copy patch mới
  theo quy ước đặt tên thư mục của `/Patch`; ghi nhật ký "file cũ → file mới"
  (bảng ánh xạ), không sửa file gốc ở Modder Hub.
- **A1. Sửa `SignatureHack_arm64.zip`**: thay bằng bản lành từ Modder Hub
  (sao lưu bản hỏng trước). Sau đó `selfcheck` phải đạt 0 lỗi.
- **A2. Sửa bộ test tái lập được**: `COLLECTION` trỏ về `upgraded/` (bản
  chuẩn hóa), cập nhật test zip lồng nhau sang 3 file `Installocation_*`
  thật; thêm test "zip hỏng không làm crash suite".
- **A3. Chống lỗi zip nén**: parser chỉ cần `patch.txt` — bắt lỗi
  CRC/decompress từng entry, đánh dấu `LỖI-NÉN`, cảnh báo rõ entry, tiếp tục
  xử lý phần còn lại. Áp dụng cho `scan`, `index`, `audit`, `selfcheck`.

### Đợt 2 — Hoàn thiện 2 hướng còn thiếu (theo EVALUATION cũ)

- **B1. Runner an toàn cho `EXECUTE_DEX`**: timeout, chặn lệnh nguy hiểm,
  chạy trong thư mục tạm cô lập, mặc định `--dry-run`; tích hợp vào
  `simulate` để 3 patch đang BỎ-QUA (`NoUpdates`, `ToolReplacement`,
  `patch_script_example`) thành ĐẠT và kiểm tra idempotency.
- **B2. Mô phỏng trên APK thật bằng apktool**: pipeline `apktool d → apply
  → apktool b → (tùy chọn) ký → so sánh cấu trúc`; thiếu apktool thì báo
  "thiếu công cụ", không lỗi. Kết quả tích hợp vào `coverage`/`roadmap`.

### Đợt 3 — Mở rộng thông minh

- **C1. Quét toàn bộ cây `/Patch` (16 thư mục) + nguồn Modder Hub**: báo
  đầy đủ, kể cả thư mục trống và "patch cũ đã bị thay".
- **C2. Phát hiện trùng lặp theo nội dung (hash)**: `Anti_analytics2` vs
  `Anti_analytics2_22-41-11`, `Yandex_Metrica` (3 bản), `License_hack`
  (3 bản), `AddSave` (3 bản) — đề xuất bản chuẩn, tránh combo trùng.
- **C3. `MANIFEST.json` tập trung**: metadata (nhóm, tác giả, engine, hash,
  nguồn cập nhật) sinh tự động, đồng bộ khi `upgrade`/`optimize`/`repair`.
- **C4. Roadmap động theo APK thật**: `combo` tự lọc chỉ giữ patch khớp
  APK đang nhắm, giảm combo rác.
- **C5. Báo cáo HTML một file**: duyệt bộ sưu tập, lỗi audit, combo, độ phủ.

## 4. Tiêu chí nghiệm thu (đo được)

- `patchx test`: tái lập **25/25** và nâng lên **≥ 30 bài**.
- `patchx simulate`: từ **52/55** lên **55/55** (3 BỎ-QUA thành ĐẠT nhờ B1).
- `patchx scan/audit/selfcheck` trên toàn bộ dữ liệu cập nhật: **0 crash**,
  báo đủ lỗi nén.
- `patchx selfcheck` sau A1: **0 lỗi** (bản SignatureHack_arm64 đã lành).
- Hiệu suất giữ ~20 ms/patch, không tụt so với mốc cũ (1.1 s / 55 patch).

## 5. Minh bạch giới hạn

- Không tự "tạo" file binary — mọi thay thế đều lấy từ nguồn lành đã xác
  định (Modder Hub) hoặc do người dùng cấp.
- `B2` phụ thuộc apktool cài sẵn; máy không có công cụ thì báo thiếu.
- Regex lỗi/không khớp vẫn chỉ cảnh báo, không tự sửa nội dung patch.
