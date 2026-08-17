# UI Toolkit Patchx trên Android — nghiên cứu & thiết kế toàn diện

Phiên bản: V1 (2026-08-16). Mục tiêu: xây lại giao diện cho **toàn bộ bộ
patchx** (23 lệnh `patchx` + 14 lệnh `patchx_toolkit.py`) chạy ngay trên
điện thoại Android, việt hoá thuần, đẹp, dễ dùng — không phải UI bọc apktool.

## 0. V2 (16/08/2026) — UI theo mục tiêu nghiệp vụ, không theo tên lệnh

Phản hồi người dùng: "chức năng, tên gọi loạn; cần mod/bypass APK mà phần
chính không thấy đâu". Đã tái tổ chức:

- 6 tab: **Trang chủ / Vượt chặn / Chỉnh sửa / Hook / Quy trình / Kho**.
- Tab Vượt chặn / Chỉnh sửa / Hook: hàng chip "Bạn muốn làm gì?" → cuộn tới
  thẻ mục tiêu. Mỗi thẻ: mô tả dùng khi nào + 2 nút **Lập kế hoạch**
  (`apk-plan`) và **Tạo combo sẵn** (`combo --only <năng-lực>`).
- Tab Quy trình: 6 bước rõ ràng (giải mã → quét → kế hoạch → áp → sửa tài
  nguyên → chạy thử máy ảo) + dây chuyền 1 chạm `apk-full`.
- Nhãn thuần Việt, ngắn; chuỗi kỹ thuật (tên patch, năng lực, lệnh) giữ
  nguyên gốc khi hiển thị phụ.

## 1. Phạm vi "toolkit toàn bộ patchx"

UI phải bao phủ toàn bộ dây chuyền 6 tầng (UPGRADE_PLAN_V4) + các lệnh nền:

| Tầng | Lệnh cần có màn hình |
|---|---|
| Nền tảng | `doctor`, `install-deps`, `selfcheck`, `test`, `package` |
| T1 Inventory | `scan`, `index`, `dupes`, `manifest`, `verify-manifest`, `apk-prepare`, `report` |
| T2 Candidate | `coverage`, `bench-scan`, `audit`, `suggest` |
| T3 Plan | `apk-plan`, `roadmap`, `plan-ui`, `analyze`, `suggest-apk`, `suggest-llm`, `list` |
| T4 Apply | `session`, `apply`, `combo`, `apk-patch` |
| T5 Build | `apk-fix-res`, `upgrade`, `optimize` |
| T6 Verify | `apk-test`, `apk-runtime`, `run`, `ci` |
| End-to-end | `apk-full` (plan → apply → fix-res → build → sign → verify) |

Đầu ra có sẵn dạng JSON (`inventory.json`, `candidates.json`,
`bypass_plan.json`, `apply_report.json`, `build_report.json`, ...) — UI chỉ là
lớp hiển thị + nút gọi, không viết lại engine.

## 2. Nghiên cứu nguồn công khai (đã tra cứu 2026-08-16)

### 2.1 Ứng dụng Android native (tham khảo chính)

- **Apktool M** (`ru.maximoff.apktool`, maximoff.su/apktool) — app Android
  decompile/compile APK, editor smali có syntax highlight, antisplit
  (gộp .apks/.xapk/.apkm → .apk), đổi tên app/gói/icon không cần rebuild,
  ký tự động. Dùng các thư viện mở: aapt, aapt2, apktool, dexlib2, smali,
  baksmali, apksig, jadx, textwarrior, guava. **Bài học**: app Android bọc
  engine Java + editor mã + ký ngay trên máy.
- **MT Manager** (`bin.mt.plus`) — file manager 2 khung + APK editor: DEX
  editor (tìm/tìm-thay smali có regex, xoá debug info, tối ưu register),
  ARSC/XML editor, ký, tối ưu, clone, chế độ dịch, plugin API v3.
  **Bài học**: giao diện 2 khung rất hiệu quả trên máy nhỏ; nút tác vụ
  nhanh đặt theo ngữ cảnh file.
- **NP Manager** — Apk/Dex/Jar/Smali editor, mã hoá/xáo trộn, ký, clone,
  thêm Xposed detection, thêm log, v.v. **Bài học**: chia chức năng theo
  danh mục lớn (chức năng / công cụ / tích hợp) giúp người dùng tìm nhanh.
- **Dalvikus** (github.com/loerting/dalvikus, Compose Multiplatform) — mở
  APK/DEX chỉnh thẳng trong APK, smali editor có gợi ý mã + tô màu, light/
  dark, nhiều decompiler, ký bằng apksig + zipalign, ADB runner cài chạy
  thẳng, tìm chuỗi/method/field, duyệt resource/XML qua apktool, 4 ngôn
  ngữ (EN/DE/ZH/HI). **Bài học**: tích hợp "mở → sửa → ký → cài chạy thử"
  trong một màn hình là trải nghiệm tốt nhất.
- **APK Editor** (WSTprojects) — cũ nhưng nhanh sửa XML, áp patch tuỳ biến.
- **Dex-Editor-Android** (developer-krushna) — editor DEX dùng smali + dexlib2.

### 2.2 Ứng dụng desktop (mẫu bố cục & tính năng)

- **ApktoolFX** (oscar0812, JavaFX) — drag&drop, Material design, log màu.
- **APKToolGUI** (AndnixSH / xdnice, C#/Python) — tab Decode/Build, gọi
  apktool + signapk + zipalign + baksmali.
- **APK Editor Studio** (MaxRegner, C++/Qt) — Resource/Icon/Title/Image/
  Code/Manifest/Permission Editor, Signature Viewer, Cloner, Signer,
  Optimizer, Installer. **Bài học**: mỗi thành phần APK một editor riêng,
  bố cục IDE.
- **APK Studio** (vaibhavpandeyvpz, Qt6) — IDE layout, tô màu smali.
- **PulseAPK** (WPF/.NET 8) — drag&drop, output decompile trực tiếp, phân
  tích smali, rebuild + ký.
- **APK Toolkit v1.7** (XDA, Windows native) — Decompile/Compile/Extract,
  assemble/disassemble dex/odex/oat bằng smali/baksmali.

### 2.3 Mô hình Web trên Termux (khả thi nhất cho patchx)

- Flask chạy localhost trong Termux, mở bằng trình duyệt điện thoại
  (webmin-lite, termux-wifi-radar, iperf3-webui, "mini web dashboard on
  Termux"). Không cần build APK, không cần SDK.
- WebView shell APK bọc server local: `dsh-mobile-apk` (WebView UI + runtime
  Termux nhúng), Marinara Engine (Termux bootstrap + WebView). Tạo app thật
  mà vẫn dùng toàn bộ engine Python hiện có.
- Python → APK độc lập: Buildozer/Kivy, Briefcase/BeeWare (Toga). **Lưu ý**:
  không build APK ngay trong Termux được (thiếu SDK/NDK) — phải build trên
  máy tính hoặc VM/CI (GitHub Actions) như mô hình `kmedya-dev/browser`.

### 2.4 Nguyên tắc UI rút ra cho patchx

1. **Một màn hình một việc theo tầng** — người dùng đi theo dây chuyền
   APK → kế hoạch → áp → build → ký → chạy thử, không nhảy lung tung.
2. **Đầu ra có sẵn phải hiển thị ngay** — đọc JSON rồi vẽ bảng/thẻ, thay vì
   bắt người dùng đọc terminal.
3. **Nút tác vụ theo ngữ cảnh** — đang xem cây APK thì hiện nút quét/lập kế
   hoạch/áp patch (giống MT Manager).
4. **Stream log theo thời gian thực** — lệnh dài (bench-scan, apk-full) chạy
   nền, hiện log sống, có nút dừng.
5. **Việt hoá thuần** — mọi nhãn, nút, thông báo bằng tiếng Việt ngắn gọn;
   tên lệnh/khoá kỹ thuật giữ nguyên gốc (đúng quy ước AGENTS.md).
6. **Mobile-first** — điều hướng đáy, thẻ xếp cột, chữ ≥ 13px, touch target
   ≥ 44px, theme tối mặc định.
7. **Offline, một file** — không phụ thuộc CDN/mạng; JS/CSS thuần, không
   framework nặng.

## 3. Kiến trúc đề xuất (3 phương án)

### Phương án A — Web UI localhost trong Termux (làm ngay)
- Server: `webui/server.py` (Python stdlib, `http.server` — không cần cài
  Flask), bind `127.0.0.1:8787`.
- API: `GET /api/state` (môi trường, số patch/combo, APK có sẵn),
  `POST /api/run` (chạy lệnh patchx, **stream log theo thời gian thực** bằng
  chunked HTTP), `GET /api/plan_ui` (trỏ trang `bypass_plan_ui.html`).
- Giao diện: `webui/static/` — HTML/CSS/JS thuần, SPA 5 tab: Trang chủ,
  Kho patch, Kế hoạch, Áp dụng, Nhật ký.
- Ưu: làm trong 1 phiên, tận dụng toàn bộ CLI + JSON có sẵn, mở bằng trình
  duyệt trên máy thật/máy ảo; không cần SDK.
- Nhược: cần bật Termux; chưa phải "app" đúng nghĩa.

### Phương án B — WebView shell APK (trung hạn)
- Bọc server phương án A bằng APK WebView (mô hình `dsh-mobile-apk` /
  Marinara Engine): APK mở `http://127.0.0.1:8787` fullscreen, tự bật
  Termux hoặc nhúng runtime.
- Ưu: trải nghiệm app thật, icon, ký, cài như app bình thường.
- Nhược: cần máy tính/CI build APK (Buildozer/Briefcase hoặc Gradle), phải
  xử lý permission storage, giữ server chạy nền.

### Phương án C — App Android native (dài hạn, theo Apktool M/Dalvikus)
- Kotlin/Compose hoặc Compose Multiplatform; gọi engine patchx qua REST
  local (server Python chạy trong Termux) hoặc port dần sang JVM.
- Ưu: nhanh nhất, đẹp nhất, tích hợp adb/runtime verify.
- Nhược: tốn nhiều đợt, cần SDK + máy build; không tận dụng ngay được
  toàn bộ code Python hiện có.

**Khuyến nghị: làm A ngay (đủ dùng trên máy thật + máy ảo Redfinger), song
song chuẩn bị B; C chỉ khi A/B đã ổn định.**

## 4. Thiết kế giao diện chi tiết (phương án A)

### 4.1 Bố cục chung
- Header: tên toolkit "Patchx — Trung tâm vượt chặn" + trạng thái môi
  trường (chấm xanh/đỏ từ `doctor`).
- Bottom nav 5 tab (mobile): Trang chủ, Kho patch, Kế hoạch, Áp dụng,
  Nhật ký.
- Mỗi tab = danh sách thẻ tác vụ; mỗi thẻ có: tên tiếng Việt, mô tả 1 câu,
  nút "Chạy" (gọi API stream), ô nhập tham số tuỳ chọn, vùng log kết quả.

### 4.2 Tab Trang chủ (Dashboard)
- Thẻ thông tin: môi trường OK/thiếu (python, java, apktool, aapt2,
  zipalign, apksigner), số patch `upgraded/`, số combo, APK trong `Apks/`,
  cây APK trong `apk_trees/`.
- Nút "Dây chuyền 1 chạm" → `apk-full` (form: APK, số patch top, có build/
  ký/verify) — luồng chính của người dùng.
- Nút nhanh: `doctor`, `install-deps`, mở trang `bypass_plan_ui.html`.

### 4.3 Tab Kho patch (T1+T2+audit)
- Thẻ: Quét kho (`scan`), Lập chỉ mục (`index`), Tìm trùng (`dupes`),
  Kiểm tra kiến trúc (`audit`), Nâng cấp (`upgrade -o upgraded`),
  Gộp tối ưu (`optimize`), Gộp combo (`combo --auto`), Mô phỏng
  (`simulate`), Sức khoẻ (`selfcheck`), Chạy thử (`test`).
- Mỗi kết quả JSON hiển thị dạng bảng/tóm tắt + log thô thu gọn.

### 4.4 Tab Kế hoạch (T3)
- Bước 1: chọn APK (`apk-prepare`) hoặc cây có sẵn.
- Bước 2: `coverage` / `roadmap` / `apk-plan` (tạo `bypass_plan_ui.html`).
- Bước 3: mở `plan-ui` — trang chọn patch tương tác đã có (checkbox, điểm,
  % thành công, cách + công cụ), bấm "Sao chép lệnh apk-full".
- Phân tích nâng cao: `analyze`, `diff-apk`, `suggest-apk`, `suggest-llm`.

### 4.5 Tab Áp dụng (T4–T6)
- Form `apk-full`: thư mục APK/cây, `--top N`, bật/tắt build, ký, verify;
  nút "Chạy toàn bộ" + log sống + nút "Dừng".
- Từng bước: `session` (chọn patch), `apply` (chọn cây), `apk-fix-res`,
  build (apktool + aapt2), zipalign + ký, `apk-runtime` (cài lên máy ảo
  Redfinger qua adb, bắt crash/logcat).
- Hiển thị kết quả: `apk_full_report.md/json`, đường dẫn APK đã ký.

### 4.6 Tab Nhật ký
- Lịch sử lệnh đã chạy (tên, tham số, mã thoát, thời gian, tóm tắt) — lưu
  localStorage + ghi `webui/logs/session_*.json`.
- Cài đặt: chủ đề sáng/tối, máy adb (IP:port máy ảo), thư mục làm việc.

### 4.7 Quy ước việt hoá UI
- Nhãn/nút/tiêu đề/thông báo: tiếng Việt thuần, ngắn, súc tích (vd "Chạy",
  "Dừng", "Đang quét…", "Hoàn tất", "Lỗi", "Kho patch", "Lập kế hoạch").
- Tên lệnh, tên patch, khóa JSON, chuỗi smali/XML: giữ nguyên gốc.
- Tham số dài hiển thị mặc định ẩn trong `<details>`.

## 5. Lộ trình triển khai

- **Đợt UI-1 (phiên này)**: tài liệu này + `webui/` hoạt động (server +
  dashboard 5 tab + stream log + state) + lệnh `webui` trong toolkit.
- **Đợt UI-2**: làm mượt từng màn hình theo 6 tầng, bảng render JSON, form
  đầy đủ tham số, lịch sử phiên.
- **Đợt UI-3**: phương án B (WebView APK) build bằng Briefcase hoặc
  Buildozer trên máy/CI; tích hợp adb runtime verify vào nút.
- **Đợt UI-4**: đánh giá phương án C (Compose) khi A/B đã ổn.

Nghiệm thu UI-1: `python3 patchx_toolkit.py webui` → mở
`http://127.0.0.1:8787` trên điện thoại/máy ảo, chạy được `doctor`, `scan`,
`apk-plan`, `apk-full --dry-run`, xem log sống, toàn bộ nhãn tiếng Việt.

## 6. Nguồn tham khảo

- Apktool M: maximoff.su/apktool; github.com/Maximoff/Apktool-M-updates
- MT Manager: apkpure.com/mt-manager/bin.mt.plus
- NP Manager: github.com/githubXiaowangzi/NP-Manager
- Dalvikus: github.com/loerting/dalvikus; XDA thread 4753839
- APK Editor Studio: github.com/MaxRegner/apk-editor-studio
- APK Studio: github.com/vaibhavpandeyvpz/apkstudio
- ApktoolFX: github.com/oscar0812/ApktoolFX
- APKToolGUI: github.com/AndnixSH/APKToolGUI
- PulseAPK: explore.market.dev/ecosystems/android/projects/pulseapk
- Web UI trên Termux: dev.to/terminaltools mini web dashboard; Flask
  localhost (webmin-lite, termux-wifi-radar, iperf3-webui)
- WebView shell: github.com/kelai141/dsh-mobile-apk; Marinara Engine
  (raw.githubusercontent.com/Pasta-Devs/Marinara-Engine)
- Python → APK: buildozer.readthedocs.io; briefcase.beeware.org;
  docs.python.org/3/using/android.html
