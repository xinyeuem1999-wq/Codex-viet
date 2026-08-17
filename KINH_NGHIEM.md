# Đúc kết từ chạy APK thật — hướng phát triển ToolPatch

Ngày: 2026-08-14. Nguồn: chạy thực tế trên `_patchx/real_apk_test/app_tree`
(477M, nhiều smali, resource cũ) và toàn bộ pipeline patchx.

## 1. Những gì đã chứng minh hoạt động tốt

- `INIT`, `TRACE`, `HOOK_SCRIPT`, `REMOTE_CONFIG`, `SET_BOOL`, `API_LOG` đều
  ghi thật vào smali APK, có marker/idempotent.
- `session` chọn patch và áp chung phiên hoạt động.
- `apk-fix-res` đổi được tên resource `$` và cập nhật `public.xml`.
- `apktool b --aapt aapt2_thật` build thành công APK 75M.
- zipalign + apksigner cho APK ký v2/v3 hợp lệ.
- Full pipeline `run` 12/12; test 88/88; simulate 51/60 ĐẠT.

## 2. Lỗi / hạn chế thật đã gặp

1. apktool 3.0.3 wrapper `aapt2` trên Termux lỗi shell.
2. apktool 3.x không còn `--use-aapt1`.
3. Cây APK cũ có resource bắt đầu bằng `$` làm aapt2 từ chối.
4. `apk-plan` quét toàn bộ cây APK 477M + regex trên toàn bộ patch bị chậm
   → đã tối ưu Đợt A: `bench-scan` đạt **23.6s < 60s** (literal hint + `rg -P`
   + memo đếm + cache theo hash cây).
5. Patch dùng `TARGET: smali*/*.smali` trên APK lớn khi áp cũng chậm vì duyệt
   mọi file.

## 3. Nên phát triển

- **Bộ tiền kiểm môi trường APK**: kiểm tra phiên bản apktool, aapt2, resource
  `$`, `public.xml`, rồi tự chọn chiến lược build đúng.
- **Fast scanner**: ✅ đã làm (Đợt A) — `bench-scan` dùng `rg`/hash/index lọc
  ứng viên trước regex Python; cây 553M quét 23.6s.
- **APK profile/cache**: ✅ đã làm — cache theo hash cây tại
  `toolkit_out/cache/scan_*.json`, nạp lại ~0s.
- **Pipeline tự động**: `apk-full` = plan → chọn top patch → apply → fix-res →
  build → zipalign → sign → verify.
- **Runtime verify**: cài APK, chạy logcat, bắt mạng để đo M2/M3.
- **Golden rebuild tests**: dùng APK mẫu nhỏ để hồi quy mỗi khi sửa engine.

## 4. Nên thay đổi / loại bỏ

- Bỏ tuỳ chọn `--use-aapt1` trong toolkit vì apktool 3.x không hỗ trợ; thay
  bằng `--aapt <aapt2>`.
- Thay việc duyệt toàn bộ `smali*/*.smali` bằng index + candidate filter.
  → ✅ đã làm: literal hint lọc tệp trước khi regex, memo đếm theo tệp.
- Trong `apk-plan`, đừng tính coverage đầy đủ trên APK lớn; hãy có `--fast`
  dùng literal hint/rg trước, chỉ regex khi cần. → ✅ đã làm (mặc định trong
  `bench-scan`/`apk-plan`).
- Sửa `apk-fix-res` để cập nhật tham chiếu đúng bằng một lượt duyệt và mapping
  đúng key (tránh lỗi key `$` + `$`).
- Bỏ cảnh báo gây hiểu nhầm “patch không thay đổi” khi build đang lỗi.

## 5. Hướng tốt nhất cho ToolPatch hiện tại

Kiến trúc nên tách rõ 6 tầng:

1. **Inventory**: scan nhanh APK, liệt kê class/method/resource.
2. **Candidate**: dùng index/rg để tìm patch có khả năng khớp.
3. **Plan**: xếp hạng patch/combo theo bằng chứng, không đoán.
4. **Apply**: áp patch với engine an toàn/idempotent.
5. **Build**: chuẩn hoá resource, chọn đúng aapt, rebuild.
6. **Verify**: ký, cài, logcat/mạng, sinh bài tập cải thiện.

Điểm ưu tiên cao nhất tiếp theo:

- Tối ưu `advisor.coverage_patch` / `count_matches` để APK lớn chạy nhanh.
  → ✅ đã xong (Đợt A, 2026-08-15): 23.6s < 60s.
- Thêm `apk-full` end-to-end.
- Tự chuẩn hoá resource trước build.
- Tự ghi lỗi build vào `improvements_report`.


## 4. Đợt C — Runtime verify thật trên máy ảo Redfinger (2026-08-16)

1. **M2 bắt được bug thật mà simulate không thấy**: helper `com.anymy.reflection`
   bị engine multi-pass tự sửa (MATCH_REPLACE chạy lên chính file ADD_FILES
   của patch) → `getPackageInfo` tự gọi chính nó → StackOverflowError lúc chạy.
   Bài học: simulate kiểm tra cấu trúc, không phát hiện được lỗi hành vi —
   runtime verify trên thiết bị thật là tầng bắt buộc.
2. **ADB qua gateway cloud phone (Redfinger)**: pairing Wi-Fi luôn lỗi
   `protocol fault` — gateway chặn TLS pairing. Cổng ADB chỉ mở lúc hộp thoại
   hiển thị, tự đổi port. Giải pháp: Tailscale hai đầu (máy ảo + máy chủ cùng
   tailnet) → `adb connect <tailscale-ip>:5555` trực tiếp, không pairing.
3. **Máy ảo cloud spam log kinh khủng** (hàng trăm dòng/giây từ phần mềm
   giám sát của hãng): cửa sổ logcat `-t 200` trôi mất sự kiện launch →
   phải `logcat -c` trước launch + đọc ≥ 2000 dòng + decode `errors="replace"`
   (logcat chứa byte nhị phân làm subprocess vỡ Unicode).
4. **Cây apk_trees tái sử dụng bị ô nhiễm**: bản áp trước để lại
   `smali/smali/apkeditor/...` → apktool "class has already been interned".
   Khi build lỗi kiểu này, xóa cây và giải mã lại từ APK gốc thay vì sửa tay.
5. **Kịch bản M3 nên dùng sự kiện hệ thống ổn định**: `Displayed
   <pkg>/.<Activity>` (ActivityTaskManager) là bằng chứng UI hiển thị thật,
   đáng tin hơn log riêng của app (app có thể không log gì hữu ích).

## 5. Đợt D — Golden tests và bài học framework-res (2026-08-16)

1. **apk-fix-res còn thiếu nửa việc**: hàm `_normalize_resource_names` chỉ
   đổi tên tệp chứa `$`, nhưng `public.xml` và tham chiếu dùng **tên resource
   không đuôi** — mapping theo tên tệp có đuôi nên hai bên không khớp, build
   vẫn lỗi `invalid entry name`. Sửa: đối chiếu theo thân tên, thay tên dài
   trước (`$$x` trước `$x` để không nuốt nhầm), bỏ qua `original/`/`.patchx/`,
   thay toàn cây. Bài học: khi "chuẩn hoá" một định danh, phải cập nhật mọi
   nơi tham chiếu định danh đó, không chỉ nơi định nghĩa.
2. **aapt2 2.20 (kho Termux) không build được framework-res**: crash
   `PrivateAttributeMover` — bug aapt2 với package ID 0x01; apktool 2.6+ đã
   vá bằng aapt2 patched (MrIkso). Bản patched prebuilt chỉ có x86_64 →
   chạy qua `qemu-user-x86-64` (binary static, không cần sysroot). aapt2
   arm64 cũ (2.19) không crash nhưng thiếu flag `--no-compile-sdk-metadata`
   → không thay thế được.
3. **Storage emulated không cho exec binary** (`chmod +x` vô hiệu, SELinux):
   công cụ build phải đặt ngoài storage (vd `~/.local/share/patchx/tools/`),
   trong workspace chỉ lưu cấu hình/tài liệu.
4. **Golden test nên tách 2 mức**: mức nhẹ chạy mãi (decode + fix-res + assert
   sạch `$`), mức đầy đủ (build + sign + verify) kích hoạt bằng biến môi
   trường `PATCHX_GOLDEN_FW=1` vì build framework-res qua qemu mất ~7 phút.
5. **framework-res là mẫu vàng resource-only tuyệt vời** (3.180 tệp, không
   dex): kiểm tra được decode/build tài nguyên thuần hệ thống, lộ lỗi
   `$` + attr-private mà APK thường không gặp.

## 6. Đợt T1–T7 + Termux máy ảo (2026-08-16)

1. **Termux bootstrap offline là chìa khóa cho máy ảo**: bản APK có
   `libtermux-bootstrap.so` (114 MB trong `Download/`) tự khởi tạo
   `/data/data/com.termux/files` ngay lần mở đầu — không cần mạng tải
   bootstrap. Bản Termux thường (33 MB) không làm được trên VM Redfinger.
2. **Điều khiển Termux trên VM**: `adb shell input text` chậm và dễ lỗi
   (không đọc được output); giải pháp bền vững là cài `openssh`, sinh key
   trên VM, pull private key về máy thật (`~/.ssh/vm_key`), rồi SSH thẳng
   `u0_a85@100.64.170.99 -p 8022`. Script hóa qua `ssh ... 'sh /sdcard/x.sh'`.
3. **Máy ảo là máy biên dịch thật**: apktool 3.0.3 + openjdk-21 + aapt2
   (kèm gói apktool) + apksigner chạy native arm64 trên VM — build + ký APK
   nhanh hơn máy thật (đang phải qua qemu cho framework-res). Công cụ điều
   khiển `vm_worker.py` chỉ là TẠM THỜI — dùng cho đợt máy ảo, không nên
   nhập vào toolkit chính.
4. **Test mới bắt bug thật**: thêm test cho `risk.py` và `smali_lib`
   phát hiện 2 lỗi — `_section_text` nối dict (crash cờ rủi ro) và thứ tự
   nhận diện `FooKt$Metadata` bị nhầm "inner". Luôn viết test cho từng trục
   mới ngay khi thêm code.
5. **Dashboard/CI dùng cho nghiệm thu dài hạn**: `patchx ci` chạy cả dây
   chuyền (audit → upgrade → optimize → combo → simulate) và xuất
   trước/sau — dùng làm mốc khi đổi engine thay vì chạy tay từng lệnh.
6. **Lưu ý escape HTML**: template HTML dùng `%`-formatting của Python phải
   viết `%%` cho ký tự `%` trong CSS/JS (lỗi `unsupported format character`
   đã gặp khi thêm `width:100%`).

## 7. Đợt E + F — CI chính thức và thực chiến APK 122M (2026-08-16)

1. **MATCH_REPLACE quét nhầm chính helper do patch khác thêm**: khối hook
   `TARGET: smali*/*.smali` đổi nhánh fallback `iget-object ... signatures`
   bên trong `Fix.smali` (ADD_FILES của patch trước) thành lời gọi đệ quy.
   Loại trừ `_added_this_patch` chỉ đủ trong cùng patch; phải loại trừ xuyên
   patch (`_added_files_all` theo lượt chạy). Bài học: khi hook một pattern,
   luôn nghĩ "pattern này có nằm trong chính class bổ trợ không".
2. **Placeholder của patch thật phải được thay, không được bỏ sót**: lỗi
   `%PACKAGE_NAME%` (StackOverflow) và `%RSA_DATA%` (spoof chết lặng vì
   try/catch nuốt lỗi) đều do giữ placeholder gốc. Khi áp patch kiểu Apk
   Editor, rà toàn bộ `%XXX%` còn sót trong cây đã áp (`rg "%[A-Z_]+%"`).
3. **Cert DER hex phải là SEQUENCE đầy đủ**: trích PKCS#7 bằng parser tự
   viết dễ cắt thiếu phần chữ ký (chỉ lấy TBSCertificate). Nghiệm thu bằng
   `keytool -printcert -file` hoặc so với `CertificateFactory` Java; nếu
   parse lỗi "Failed to parse input" nghĩa là hex sai.
4. **Lỗi bị try/catch nuốt khó thấy hơn lỗi crash**: `Fix.smali` bắt
   `Throwable` và chỉ log `D fix: error`; chạy thành công nhưng chức năng
   (spoof chữ ký) chết lặng. Khi M2 đạt nhưng nghi ngờ nhánh chức năng,
   bật log riêng (tag `fix`) và so sánh "old:"/"new:" trong logcat.
5. **Cài sạch trước khi nghiệm thu runtime**: `adb install -r` giữ dữ liệu
   cũ; uninstall trước rồi install bản mới, `logcat -c` trước launch để kết
   luận M2/M3 không nhiễu log lần chạy trước.
6. **Build lâu phải chạy đồng bộ trong session dài**: chạy nền `&` trong
   lệnh rồi thoát sẽ bị giết theo phiên; dùng session dài (yield lớn) cho
   `apktool b` APK 123M (~2–4 phút).
7. **`apk-full` tự nạp `PATCHX_RSA_DATA`**: khi apply thủ công patch hack
   signature, đặt biến môi trường bằng cert hex trích từ APK gốc, nếu không
   spoof sẽ không hoạt động (nhưng không crash).
