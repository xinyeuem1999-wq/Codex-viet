/* Patchx Web UI — theo mục tiêu nghiệp vụ: Mod · Bypass · Hook APK.
   Nhãn hiển thị bằng tiếng Việt thuần; lệnh kỹ thuật ẩn trong argv. */
"use strict";

const view = document.getElementById("view");
const envEl = document.getElementById("env");
let STATE = null;
let ACTIVE = "home";
let MODE = "adv";
try { MODE = localStorage.getItem("patchx_mode") || "adv"; } catch (e) {}
const MAN = { apk: "", dir: "", file: "" };

/* ---------- chế độ hiển thị ---------- */
const LEVELS = {
  basic: { label: "Cơ bản", ic: "🟢", desc: "Chỉ thấy tác vụ thường dùng." },
  adv: { label: "Nâng cao", ic: "🟡", desc: "Thêm phân tích, kiểm thử chuyên sâu." },
  exp: { label: "Chuyên gia", ic: "🔴", desc: "Toàn bộ: duyệt cây, sửa patch thủ công." },
};

/* ---------- 6 tầng pipeline (P21) ---------- */
const STAGES = [
  { n: 1, name: "Hiểu cây", ic: "🔎", desc: "Giải mã APK, quét kho, đo độ phủ.",
    tasks: ["pt_prepare", "qt_prepare", "pt_scan", "pt_cover"] },
  { n: 2, name: "Ứng viên", ic: "🧠", desc: "Lọc patch/combos khớp theo năng lực.",
    tasks: ["kh_plan", "pt_callgraph", "pt_dex"] },
  { n: 3, name: "Kế hoạch", ic: "🗺️", desc: "Xếp hạng phương án + tỷ lệ thành công %.",
    tasks: ["kh_plan", "kh_llm", "apkfull"] },
  { n: 4, name: "Áp patch", ic: "🛠️", desc: "Áp patch/combo, sửa tài nguyên, có sao lưu.",
    tasks: ["qt_apply", "qt_fixres", "apkfull"] },
  { n: 5, name: "Build + ký", ic: "🏗️", desc: "Build, zipalign, ký, xác minh chữ ký.",
    tasks: ["kt_build", "apkfull"] },
  { n: 6, name: "Chạy thử", ic: "📱", desc: "Cài lên máy ảo, M2/M3, bắt crash.",
    tasks: ["kt_runtime", "apkfull"] },
];

function pipelineRuns() {
  try { return JSON.parse(localStorage.getItem("patchx_pipeline") || "[]"); }
  catch (e) { return []; }
}
function savePipeline(entry) {
  let p = pipelineRuns();
  p.unshift(entry);
  p = p.slice(0, 80);
  localStorage.setItem("patchx_pipeline", JSON.stringify(p));
}
function stageState(n) {
  const ids = STAGES[n - 1].tasks;
  if (ids.some(id => running.has(id))) return "run";
  const p = pipelineRuns();
  for (const e of p) if (ids.includes(e.task)) return e.ok ? "done" : "fail";
  return "idle";
}

/* ---------- mục tiêu nghiệp vụ (chip cuộn tới thẻ tương ứng) ---------- */
const GOALS = {
  bypass: [
    { id: "bypass_vip", label: "Mở khoá VIP / trả phí" },
    { id: "bypass_sig", label: "Qua kiểm tra chữ ký" },
    { id: "bypass_google", label: "Qua Google Play" },
    { id: "bypass_root", label: "Ẩn root" },
    { id: "bypass_pin", label: "Gỡ SSL pinning" },
    { id: "bypass_installer", label: "Qua kiểm tra nguồn cài" },
    { id: "bypass_spoof", label: "Giả ID thiết bị" },
    { id: "bypass_debug", label: "Chống gỡ lỗi" },
    { id: "bypass_frida", label: "Ẩn Frida" },
    { id: "bypass_emu", label: "Qua kiểm tra máy ảo" },
  ],
  mod: [
    { id: "mod_ads", label: "Chặn quảng cáo" },
    { id: "mod_anon", label: "Xoá theo dõi" },
    { id: "mod_save", label: "Mở khoá tính năng" },
    { id: "mod_perm", label: "Đổi quyền" },
    { id: "mod_shell", label: "Bơm mod lúc khởi động" },
    { id: "mod_ui", label: "Đổi giao diện" },
    { id: "mod_font", label: "Thay font" },
  ],
  hook: [
    { id: "hook_trace", label: "Bắt log dữ liệu" },
    { id: "hook_api", label: "Bắt API" },
    { id: "hook_token", label: "Quét token" },
    { id: "hook_remote", label: "Điều khiển từ xa" },
    { id: "hook_frida", label: "Hook Frida / Xposed" },
  ],
};

/* ---------- tác vụ theo tab ---------- */
/* Mỗi tác vụ: id, title, desc (mục đích + dùng khi nào), fields,
   argv (nút chính), argv2 + btn2 (nút phụ), cap/dir (cho combo). */
const TASKS = {
  home: [
    { id: "apkfull", title: "Dây chuyền vượt chặn — 1 chạm",
      desc: "Từ APK → kế hoạch → chọn patch → áp → sửa tài nguyên → build → ký → xác minh. Khuyên dùng khi bắt đầu.",
      fields: [
        { key: "tree", label: "APK / cây APK", type: "select_tree", hint: "chọn APK trong Apks/ hoặc cây đã giải mã" },
        { key: "top", label: "Số patch hàng đầu tự chọn", type: "number", default: "3" },
        { key: "dry", label: "Chỉ lập kế hoạch, chưa áp (an toàn)", type: "check", default: true },
        { key: "runtime", label: "Chạy thử trên máy ảo sau khi ký", type: "check", default: false },
      ],
      argv: ["patchx_toolkit.py", "apk-full", "{{tree}}", "--top", "{{top}}",
             "{{+dry:--dry-run}}", "{{+runtime:--runtime}}"] },
    { id: "planui", title: "Mở trang kế hoạch vượt chặn",
      desc: "Xem báo cáo trực quan: điểm bypass, cách làm, công cụ, tỷ lệ thành công %.",
      action: "planui" },
    { id: "doctor", title: "Kiểm tra môi trường",
      desc: "Xem đủ công cụ chưa: python, java, apktool, aapt2, zipalign, apksigner, adb.",
      argv: ["patchx_toolkit.py", "doctor"], tone: "ok" },
    { id: "deps", title: "Cài công cụ còn thiếu",
      desc: "Tự cài apktool, zipalign, apksigner… nếu máy chưa có.",
      argv: ["patchx_toolkit.py", "install-deps"] },
    { id: "bench", title: "Đo tốc độ quét (nghiệm thu < 60s)",
      desc: "Quét cây APK lớn, đo thời gian inventory + coverage.",
      fields: [{ key: "tree", label: "Cây APK", type: "select_tree" }],
      argv: ["patchx_toolkit.py", "bench-scan", "{{tree}}"] },
  ],

  bypass: [
    { id: "bypass_vip", title: "Mở khoá VIP / bản quyền",
      desc: "Vô hiệu hoá kiểm tra licence, mở khoá tính năng trả phí (VIP, Pro, Premium). Dùng khi app bắt phải mua / đăng nhập mới xài.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "bypass-license", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "bypass_sig", title: "Qua kiểm tra chữ ký & toàn vẹn",
      desc: "Bỏ kiểm tra chữ ký, dấu vết chỉnh sửa (signature mismatch, app modified). Dùng khi app báo lỗi sau khi mod.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "integrity", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "bypass_google", title: "Qua Google Play / Play Integrity",
      desc: "Bỏ kiểm tra Google Play Services, SafetyNet, Play Integrity. Dùng khi app đòi có Google Play mới chạy.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "google", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "bypass_root", title: "Ẩn root / qua kiểm tra root",
      desc: "Vô hiệu hoá kiểm tra root (RootBeer, isRooted, Magisk). Dùng khi app chặn thiết bị đã root.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "root-hide", dir: "bypass_plus", dirout: "combos_auto_plus",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "bypass_pin", title: "Gỡ SSL pinning / bắt gói tin",
      desc: "Bỏ khoá chứng chỉ (X509TrustManager, CertificatePinner) để bắt gói bằng proxy. Dùng khi cần xem API app gửi gì.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "ssl-pinning", dir: "bypass_plus", dirout: "combos_auto_plus",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "bypass_installer", title: "Qua kiểm tra nguồn cài đặt",
      desc: "Giả nguồn cài là CH Play (getInstallerPackageName). Dùng khi app không chạy vì cài từ file APK.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "installer", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "bypass_spoof", title: "Giả mạo ID thiết bị",
      desc: "Thay Android ID, IMEI, MAC, serial bằng giá trị giả. Dùng khi app khoá theo thiết bị.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "id-spoof", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "bypass_debug", title: "Chống gỡ lỗi (anti-debug)",
      desc: "Bỏ phát hiện debugger (isDebuggerConnected, TracerPid). Dùng khi app tự thoát khi mở ở chế độ gỡ lỗi.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "anti-debug", dir: "bypass_plus", dirout: "combos_auto_plus",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "bypass_frida", title: "Ẩn Frida / qua kiểm tra Frida",
      desc: "Giấu dấu vết Frida (gadget, gum-js). Dùng khi app chặn thiết bị có Frida / môi trường hook.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "frida-hide", dir: "bypass_plus", dirout: "combos_auto_plus",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "bypass_emu", title: "Qua kiểm tra máy ảo",
      desc: "Bỏ phát hiện máy ảo (isEmulator, goldfish, Genymotion). Dùng khi app chặn chạy trên máy ảo.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "emulator", dir: "bypass_plus", dirout: "combos_auto_plus",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
  ],

  mod: [
    { id: "mod_ads", title: "Chặn quảng cáo",
      desc: "Bỏ banner, quảng cáo xen giữa, video quảng cáo. Dùng khi app hiện quá nhiều quảng cáo.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "ads", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "mod_anon", title: "Xoá theo dõi / ẩn danh",
      desc: "Gỡ analytics, thu thập dữ liệu, giả GPS/vị trí. Dùng khi muốn app không gửi dữ liệu riêng tư đi.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "anonymity", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "mod_save", title: "Mở khoá tính năng lưu / nâng cấp",
      desc: "Gỡ khoá tính năng lưu trữ, nâng cấp tài khoản. Dùng khi app chặn lưu / xuất dữ liệu.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "save", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "mod_perm", title: "Đổi quyền ứng dụng",
      desc: "Sửa AndroidManifest.xml: thêm / bớt quyền, cho phép gỡ lỗi. Dùng khi app đòi quyền quá mức hoặc không đòi đủ.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "permission", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "mod_shell", title: "Bơm mod khi app khởi động",
      desc: "Chèn script khởi tạo vào app (INIT / HOOK_SCRIPT). Dùng khi cần bơm biến, gọi hàm nội bộ lúc mở app.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "shell", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "mod_ui", title: "Đổi tên / icon / giao diện",
      desc: "Sửa tên app, icon, giao diện, màu sắc. Dùng khi muốn đổi nhận diện hoặc việt hoá.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "ui", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "mod_font", title: "Thay font chữ",
      desc: "Thay font trong res/font. Dùng khi app dùng font khó đọc.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "font", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
  ],

  hook: [
    { id: "hook_trace", title: "Bắt log dữ liệu (TRACE)",
      desc: "Chèn log quanh lệnh gọi hàm để đọc tham số + kết quả. Dùng để hiểu app trước khi quyết định mod.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "trace", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "hook_api", title: "Bắt API & endpoint (API_LOG)",
      desc: "Ghi lại URL / lời gọi API khi app chạy. Dùng để tìm server thật, sau đó thay endpoint hoặc chặn.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "api", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "hook_token", title: "Quét token / khoá bí mật",
      desc: "Tìm và vô hiệu hoá endpoint lấy token, thay token giả. Dùng khi app xác thực qua token.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "token", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "hook_remote", title: "Điều khiển mod từ xa",
      desc: "Chèn cấu hình từ xa (REMOTE_CONFIG): app tải quyết định bật/tắt tính năng từ URL của bạn.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      cap: "api", dir: "upgraded", dirout: "combos_auto",
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      argv2: ["patchx", "combo", "{{dir}}", "--only", "{{cap}}", "-o", "{{dirout}}"],
      btn2: "Tạo combo sẵn" },
    { id: "hook_frida", title: "Hook bằng Frida / Xposed",
      desc: "Hướng dẫn: hook method khi chạy (không cần build lại APK). Công cụ: Frida, objection, LSPosed. Chạy bên dưới để tìm điểm hook trong APK.",
      fields: [{ key: "tree", label: "Cây APK đã giải mã", type: "select_tree" }],
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"] },
  ],

  quytrinh: [
    { id: "qt_apkfull", title: "Dây chuyền 1 chạm (khuyên dùng)",
      desc: "Lập kế hoạch → chọn patch → áp → sửa tài nguyên → build → ký → xác minh, kèm báo cáo đầy đủ.",
      fields: [
        { key: "tree", label: "APK / cây APK", type: "select_tree" },
        { key: "top", label: "Số patch hàng đầu", type: "number", default: "3" },
        { key: "dry", label: "Chỉ lập kế hoạch (dry-run)", type: "check", default: false },
        { key: "build", label: "Build APK", type: "check", default: true },
        { key: "sign", label: "Ký APK", type: "check", default: true },
        { key: "runtime", label: "Chạy thử trên máy ảo", type: "check", default: false },
      ],
      argv: ["patchx_toolkit.py", "apk-full", "{{tree}}", "--top", "{{top}}",
             "{{+dry:--dry-run}}", "{{-build:--no-build}}", "{{-sign:--no-sign}}",
             "{{+runtime:--runtime}}"] },
    { id: "qt_prepare", title: "Bước 1 · Giải mã APK",
      desc: "Biến tệp APK thành cây thư mục đã giải mã (smali, res, manifest) để quét và áp patch.",
      fields: [
        { key: "apk", label: "Tệp APK", type: "select_apk" },
        { key: "out", label: "Thư mục đầu ra (để trống = apk_trees/<tên APK>)", type: "text", default: "" },
      ],
      argv: ["patchx", "apk-prepare", "{{apk}}", "-o", "{{out}}"] },
    { id: "qt_scan", title: "Bước 2 · Quét & đo độ phủ",
      desc: "Patch khớp bao nhiêu phần của APK. Dùng để biết kho patch nào hợp với app này.",
      fields: [
        { key: "patch", label: "Thư mục patch", type: "text", default: "upgraded" },
        { key: "tree", label: "Cây APK", type: "select_tree" },
      ],
      argv: ["patchx", "coverage", "{{patch}}", "{{tree}}"] },
    { id: "qt_plan", title: "Bước 3 · Lập kế hoạch vượt chặn",
      desc: "Quét cây APK, mô phỏng, xếp hạng phương án kèm tỷ lệ thành công %.",
      fields: [{ key: "tree", label: "Cây APK", type: "select_tree" }],
      argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
      action2: "planui", btn2: "Mở trang kế hoạch" },
    { id: "qt_apply", title: "Bước 4 · Áp patch",
      desc: "Áp combo / patch đã chọn lên cây APK (có sao lưu, chạy lại không hỏng).",
      fields: [
        { key: "patch", label: "Patch (cách nhau dấu phẩy)", type: "text", default: "", hint: "vd: combos_auto/license.patch hoặc tên trong log bước 3" },
        { key: "tree", label: "Cây APK", type: "select_tree" },
        { key: "dry", label: "Xem trước, không ghi", type: "check", default: false },
      ],
      argv: ["patchx", "apply", "{{patch}}", "{{tree}}", "{{+dry:--dry-run}}"] },
    { id: "qt_fixres", title: "Bước 5 · Sửa tài nguyên lỗi",
      desc: "Chuẩn hoá tên resource chứa ký tự $ để build lại được bằng aapt2.",
      fields: [
        { key: "tree", label: "Cây APK", type: "select_tree" },
        { key: "dry", label: "Chỉ xem trước", type: "check", default: false },
      ],
      argv: ["patchx_toolkit.py", "apk-fix-res", "{{tree}}", "{{+dry:--dry-run}}"] },
    { id: "qt_runtime", title: "Bước 6 · Chạy thử trên máy ảo",
      desc: "Cài APK lên máy ảo Redfinger qua adb, mở app, bắt crash / logcat.",
      fields: [
        { key: "connect", label: "Kết nối máy ảo HOST:PORT", type: "text", default: "127.0.0.1:5555" },
        { key: "scan", label: "Tự quét cổng adb phổ biến", type: "check", default: false },
        { key: "wait", label: "Giây chờ sau khi mở app", type: "number", default: "8" },
      ],
      argv: ["patchx_toolkit.py", "apk-runtime", "{{+scan:--scan-local}}",
             "{{+connect:--connect}}", "{{+connect:value}}",
             "--wait", "{{wait}}"] },
    { id: "qt_bench", title: "Đo tốc độ quét (nghiệm thu < 60s)",
      desc: "Đo thời gian quét cây APK lớn — mốc nghiệm thu 477M < 60s.",
      fields: [{ key: "tree", label: "Cây APK", type: "select_tree" }],
      argv: ["patchx_toolkit.py", "bench-scan", "{{tree}}"] },
  ],

  kho: [
    { id: "kho_scan", title: "Quét kho patch",
      desc: "Liệt kê mọi patch trong bộ sưu tập (kể cả thư mục con).",
      fields: [{ key: "dir", label: "Thư mục quét", type: "text", default: ".." }],
      argv: ["patchx", "scan", "{{dir}}", "--recursive"] },
    { id: "kho_index", title: "Lập chỉ mục",
      desc: "Tạo index.json + báo cáo cho toàn kho.",
      argv: ["patchx", "index"] },
    { id: "kho_dupes", title: "Tìm patch trùng",
      desc: "So sánh nội dung theo hash, phát hiện trùng lặp.",
      argv: ["patchx", "dupes"] },
    { id: "kho_audit", title: "Kiểm tra kiến trúc",
      desc: "Phát hiện lỗi cấu trúc từng patch (thẻ, metadata, regex…).",
      argv: ["patchx", "audit"] },
    { id: "kho_upgrade", title: "Nâng cấp chuẩn hoá",
      desc: "Sửa lỗi kiến trúc an toàn, ghi ra thư mục mới (không sửa bộ gốc).",
      fields: [
        { key: "dir", label: "Thư mục gốc", type: "text", default: ".." },
        { key: "out", label: "Đầu ra", type: "text", default: "upgraded" },
      ],
      argv: ["patchx", "upgrade", "{{dir}}", "-o", "{{out}}"] },
    { id: "kho_optimize", title: "Gộp tối ưu",
      desc: "Gộp patch cùng mục tiêu, tách xung đột.",
      fields: [
        { key: "dir", label: "Thư mục patch", type: "text", default: "upgraded" },
        { key: "out", label: "Đầu ra", type: "text", default: "optimized" },
      ],
      argv: ["patchx", "optimize", "{{dir}}", "-o", "{{out}}"] },
    { id: "kho_combo", title: "Gộp combo tự động",
      desc: "Tự phát hiện patch bổ trợ nhau theo họ chức năng + class-link.",
      fields: [
        { key: "dir", label: "Thư mục patch", type: "text", default: "upgraded" },
        { key: "out", label: "Đầu ra", type: "text", default: "combos_auto" },
      ],
      argv: ["patchx", "combo", "{{dir}}", "--auto", "--recursive", "-o", "{{out}}"] },
    { id: "kho_simulate", title: "Mô phỏng toàn diện",
      desc: "Tự sinh mẫu, áp thử từng patch, đánh giá hiệu quả + idempotent.",
      fields: [
        { key: "dir", label: "Thư mục patch", type: "text", default: "upgraded" },
        { key: "quick", label: "Chạy nhanh (15 patch đầu)", type: "check", default: false },
      ],
      argv: ["patchx", "simulate", "{{dir}}", "{{+quick:--quick}}", "-o", "simulation"] },
    { id: "kho_selfcheck", title: "Sức khoẻ toolkit",
      desc: "Kiểm tra module, patch, cấu hình của chính patchx.",
      argv: ["patchx", "selfcheck"] },
    { id: "kho_test", title: "Chạy bộ kiểm thử",
      desc: "Toàn bộ bài kiểm thử hồi quy của patchx.",
      argv: ["patchx", "test"] },
    { id: "kho_doctor", title: "Kiểm tra môi trường",
      desc: "Tổng quan công cụ + kho patch + APK sẵn có.",
      argv: ["patchx_toolkit.py", "doctor"] },
    { id: "kho_deps", title: "Cài công cụ còn thiếu",
      desc: "Tự cài apktool, zipalign, apksigner…",
      argv: ["patchx_toolkit.py", "install-deps"] },
    { id: "kho_hist", title: "Xoá nhật ký lệnh",
      desc: "Xoá lịch sử lệnh đã chạy trên trình duyệt này.",
      action: "clearhist" },
  ],
};

/* ---------- 7 khu vực Workbench (P21) ---------- */
const AREAS = {
  home: { title: "Trang chủ", render: "home" },
  phan_tich: { title: "Phân tích",
    subtitle: "Quét cây APK, đo độ phủ, kiểm tra DEX — hiểu app trước khi vá.",
    render: "tasks", tasks: "phan_tich" },
  ke_hoach: { title: "Kế hoạch", render: "goals" },
  va_loi: { title: "Vá lỗi",
    subtitle: "Áp patch, gộp combo, dây chuyền 1 chạm — có sao lưu và xem trước.",
    render: "tasks", tasks: "va_loi" },
  kiem_thu: { title: "Kiểm thử",
    subtitle: "Kiểm tra trước khi vá, xác thực, build, chạy thử M2/M3 trên máy ảo.",
    render: "tasks", tasks: "kiem_thu" },
  bao_cao: { title: "Báo cáo",
    subtitle: "Kho lỗi, baseline, tốc độ quét, khác biệt APK — bằng chứng đo được.",
    render: "tasks", tasks: "bao_cao" },
  he_thong: { title: "Hệ thống", render: "system" },
};

TASKS.phan_tich = [
  { id: "pt_cover", title: "Đo độ phủ patch",
    desc: "Patch khớp bao nhiêu phần của APK — chọn chế độ quét chi tiết.",
    fields: [
      { key: "patch", label: "Thư mục patch", type: "text", default: "upgraded" },
      { key: "tree", label: "Cây APK", type: "select_tree" },
      { key: "mode", label: "Chế độ quét", type: "select", default: "FAST", opts: [
        { v: "FAST", t: "FAST — nhanh, lấy mẫu ≤300 tệp" },
        { v: "NORMAL", t: "NORMAL — quét đủ mọi tệp" },
        { v: "FULL", t: "FULL — đủ + tìm sâu ngoài target" },
        { v: "RELEASE", t: "RELEASE — đầy đủ nhất" } ] },
    ],
    argv: ["patchx", "coverage", "{{patch}}", "{{tree}}", "--mode", "{{mode}}"] },
  { id: "pt_dex", title: "Đo giới hạn DEX 64K",
    desc: "Đếm method refs, mức an toàn, chiến lược trước khi vá.",
    fields: [
      { key: "tree", label: "Cây APK", type: "select_tree" },
      { key: "workers", label: "Luồng quét (mặc định 1)", type: "number", default: "1" },
    ],
    argv: ["patchx", "dex-budget", "{{tree}}", "--workers", "{{workers}}"] },
  { id: "pt_prepare", title: "Giải mã APK",
    desc: "Biến tệp APK thành cây thư mục smali/res/manifest để quét và vá.",
    fields: [
      { key: "apk", label: "Tệp APK", type: "select_apk" },
      { key: "out", label: "Thư mục đầu ra (để trống = apk_trees/<tên>)", type: "text", default: "" },
    ],
    argv: ["patchx", "apk-prepare", "{{apk}}", "-o", "{{out}}"] },
  { id: "pt_scan", title: "Quét kho patch",
    desc: "Liệt kê mọi patch trong bộ sưu tập (kể cả thư mục con).",
    fields: [{ key: "dir", label: "Thư mục quét", type: "text", default: ".." }],
    argv: ["patchx", "scan", "{{dir}}", "--recursive"] },
  { id: "pt_dupes", title: "Tìm patch trùng",
    desc: "So sánh nội dung theo hash, phát hiện trùng lặp.",
    argv: ["patchx", "dupes"] },
  { id: "pt_audit", title: "Kiểm tra kiến trúc",
    desc: "Phát hiện lỗi cấu trúc từng patch (thẻ, metadata, regex…).",
    argv: ["patchx", "audit"] },
  { id: "pt_callgraph", title: "Sơ đồ gọi (call graph)",
    desc: "Phân tích ngữ nghĩa cây APK: packer, mã hoá chuỗi, top class được gọi nhiều nhất.",
    level: "adv",
    fields: [
      { key: "tree", label: "Cây APK", type: "select_tree" },
      { key: "top", label: "Số class hàng đầu", type: "number", default: "15" },
    ],
    argv: ["patchx", "analyze", "{{tree}}", "-o", "toolkit_out/analyze.json", "--top", "{{top}}"] },
  { id: "pt_diff", title: "So sánh APK gốc ↔ đã mod",
    desc: "Sinh patch từ khác biệt hai APK/cây (trục T2 — đảo pipeline).",
    level: "adv",
    fields: [
      { key: "goc", label: "APK / cây gốc", type: "select_tree" },
      { key: "mod", label: "APK / cây đã mod", type: "select_tree" },
      { key: "name", label: "Tên patch sinh ra", type: "text", default: "diff_patch" },
    ],
    argv: ["patchx", "diff-apk", "{{goc}}", "{{mod}}", "-o", "toolkit_out/diff_patch", "--name", "{{name}}"] },
  { id: "pt_remote", title: "Bản đồ điều khiển từ xa",
    desc: "Lập bản đồ flag boolean + mọi điểm đọc/ghi trong cây APK (remote-map).",
    level: "adv",
    fields: [
      { key: "tree", label: "Cây APK", type: "select_tree" },
      { key: "top", label: "Số flag nổi bật", type: "number", default: "15" },
    ],
    argv: ["patchx", "remote-map", "{{tree}}", "-o", "toolkit_out/remote_map.json", "--top", "{{top}}"] },
  { id: "pt_model_v2", title: "Evidence ngữ nghĩa V2",
    desc: "Chỉ đọc: dựng model identity/caller/callee để review; không áp patch.",
    level: "adv",
    fields: [{ key: "tree", label: "Cây APK", type: "select_tree" }],
    argv: ["patchx", "model", "{{tree}}", "--v2", "-o", "toolkit_out/app_model_v2.json"] },
  { id: "pt_plan_v2", title: "Đánh giá semantic plan V2",
    desc: "Chỉ đọc: chấm evidence và chặn target mơ hồ trước preflight.",
    level: "adv",
    fields: [
      { key: "tree", label: "Cây APK", type: "select_tree" },
      { key: "plan", label: "Tệp plan V2", type: "text", default: "toolkit_out/semantic_plan_v2.json" },
    ],
    argv: ["patchx", "semantic-plan", "{{tree}}", "{{plan}}"] },
  { id: "pt_compile_v2", title: "Tạo transaction nháp V2",
    desc: "Khóa hash evidence và tạo draft cần duyệt; không có lệnh apply hay nội dung Smali thực thi.",
    level: "adv",
    fields: [
      { key: "tree", label: "Cây APK", type: "select_tree" },
      { key: "plan", label: "Tệp plan V2", type: "text", default: "toolkit_out/semantic_plan_v2.json" },
    ],
    argv: ["patchx", "plan-compile", "{{tree}}", "{{plan}}", "-o", "toolkit_out/transaction_draft_v2.json"] },
  { id: "pt_preflight_v2", title: "Kiểm tra evidence của draft V2",
    desc: "Chỉ đọc: chặn draft nếu cây APK đã đổi từ lúc khóa evidence.",
    level: "adv",
    fields: [
      { key: "tree", label: "Cây APK", type: "select_tree" },
      { key: "draft", label: "Tệp transaction nháp", type: "text", default: "toolkit_out/transaction_draft_v2.json" },
    ],
    argv: ["patchx", "plan-preflight", "{{tree}}", "{{draft}}"] },
];

TASKS.ke_hoach = [
  { id: "kh_plan", title: "Lập kế hoạch vượt chặn",
    desc: "Quét cây APK, chấm điểm, đề xuất phương án + tỷ lệ thành công % (kèm evidence và mức tin cậy).",
    fields: [{ key: "tree", label: "Cây APK", type: "select_tree" }],
    argv: ["patchx_toolkit.py", "apk-plan", "{{tree}}", "--output", "toolkit_out/apk_plan"],
    action2: "planui", btn2: "Mở trang kế hoạch" },
  { id: "kh_llm", title: "Gợi ý theo ý định (LLM cục bộ)",
    desc: "Mô tả ý định → chọn patch + khung combo; cần duyệt --approve mới ghi.",
    fields: [
      { key: "dir", label: "Thư mục patch", type: "text", default: "upgraded" },
      { key: "yd", label: "Ý định (vd: mở khoá vip)", type: "text", default: "mở khoá vip" },
    ],
    argv: ["patchx", "suggest-llm", "{{dir}}", "{{yd}}"] },
];

TASKS.va_loi = [
  TASKS.home.find(t => t.id === "apkfull"),
  TASKS.quytrinh.find(t => t.id === "qt_apply"),
  TASKS.quytrinh.find(t => t.id === "qt_fixres"),
  TASKS.kho.find(t => t.id === "kho_combo"),
  TASKS.kho.find(t => t.id === "kho_optimize"),
  TASKS.kho.find(t => t.id === "kho_upgrade"),
  { id: "va_manual", title: "Manual Mode — duyệt cây & xem smali",
    desc: "Duyệt cây APK đã giải mã, xem AndroidManifest.xml / smali, tìm kiếm chuỗi trong toàn cây.",
    level: "exp", action: "manual_tree" },
  { id: "va_patch_edit", title: "Soạn patch thủ công",
    desc: "Dán nội dung patch, chạy thử dry-run hoặc áp thật lên cây APK (có sao lưu).",
    level: "exp", action: "manual_apply" },
];

TASKS.kiem_thu = [
  { id: "kt_preflight", title: "Kiểm tra trước khi vá",
    desc: "Cổng an toàn: package, DEX 64K, xung đột… trước khi áp patch.",
    fields: [
      { key: "patch", label: "Patch (zip/txt)", type: "text", default: "" },
      { key: "tree", label: "Cây APK", type: "select_tree" },
    ],
    argv: ["patchx", "preflight", "{{patch}}", "{{tree}}"] },
  { id: "kt_validate", title: "Xác thực cây APK",
    desc: "Smali/XML/manifest/DEX theo 4 mức: FAST → RELEASE.",
    fields: [
      { key: "tree", label: "Cây APK", type: "select_tree" },
      { key: "level", label: "Mức xác thực", type: "select", default: "NORMAL", opts: [
        { v: "FAST", t: "FAST — smali" },
        { v: "NORMAL", t: "NORMAL — + manifest" },
        { v: "FULL", t: "FULL — + XML + DEX" },
        { v: "RELEASE", t: "RELEASE — chặn cả cảnh báo" } ] },
    ],
    argv: ["patchx", "validate", "{{tree}}", "--level", "{{level}}"] },
  { id: "kt_build", title: "Build + ký APK",
    desc: "apk-build: build, zipalign, ký, xác minh chữ ký.",
    fields: [{ key: "tree", label: "Cây APK", type: "select_tree" }],
    argv: ["patchx_toolkit.py", "apk-build", "{{tree}}"] },
  { id: "kt_runtime", title: "Chạy thử M2/M3",
    desc: "Cài lên máy ảo, mở app, bắt crash/ANR; kịch bản M3 tuỳ chọn.",
    fields: [
      { key: "apk", label: "APK đã ký", type: "select_apk" },
      { key: "device", label: "Máy kiểm thử", type: "select_device" },
      { key: "scenario", label: "Kịch bản M3 (scenario.json — để trống = chỉ M2)", type: "text", default: "" },
      { key: "wait", label: "Giây chờ sau khi mở", type: "number", default: "6" },
    ],
    argv: ["patchx_toolkit.py", "apk-runtime", "{{apk}}", "--device", "{{device}}",
           "{{+scenario:--scenario}}", "{{+scenario:value}}", "--wait", "{{wait}}"] },
  { id: "kt_bench", title: "Đo tốc độ quét (nghiệm thu < 60s)",
    desc: "Đo thời gian quét cây APK lớn.",
    fields: [{ key: "tree", label: "Cây APK", type: "select_tree" }],
    argv: ["patchx_toolkit.py", "bench-scan", "{{tree}}"] },
];

TASKS.bao_cao = [
  { id: "bc_failure", title: "Kho lỗi (Failure Intelligence)",
    desc: "Danh sách lỗi đã biết: nguyên nhân, cách xử lý, test hồi quy.",
    argv: ["patchx", "failure", "report"] },
  { id: "bc_golden", title: "Golden Build gate",
    desc: "Chạy 2 golden test (mini_app + framework-res), ghi golden_gate.json.",
    argv: ["patchx", "golden", "--fw"] },
  { id: "bc_learn", title: "Tự học từ APK thật",
    desc: "Gợi ý chuỗi patch theo APK thật và kho combo thành công (self-learning).",
    fields: [{ key: "tree", label: "Cây APK", type: "select_tree" }],
    argv: ["patchx", "suggest-apk", "{{tree}}"] },
  { id: "bc_bench", title: "Đo tốc độ quét",
    desc: "Quét cây APK lớn, nghiệm thu < 60s.",
    fields: [{ key: "tree", label: "Cây APK", type: "select_tree" }],
    argv: ["patchx_toolkit.py", "bench-scan", "{{tree}}"] },
  { id: "bc_bl_show", title: "Xem baseline",
    desc: "Số liệu chuẩn hiện tại của toolkit.",
    argv: ["patchx", "baseline", "show"] },
  { id: "bc_bl_cap", title: "Chụp baseline mới",
    desc: "Lưu số liệu gốc để chặn hồi quy.",
    argv: ["patchx", "baseline", "capture"] },
];

TASKS.he_thong = [
  TASKS.kho.find(t => t.id === "kho_doctor"),
  TASKS.kho.find(t => t.id === "kho_deps"),
  TASKS.kho.find(t => t.id === "kho_selfcheck"),
  TASKS.kho.find(t => t.id === "kho_test"),
  TASKS.kho.find(t => t.id === "kho_simulate"),
  { id: "hs_fuzz", title: "Fuzz parser + engine",
    desc: "Tấn công ngẫu nhiên theo 5 invariant — tìm lỗi tiềm ẩn.",
    fields: [
      { key: "iter", label: "Số lượt", type: "number", default: "60" },
      { key: "seed", label: "Seed (cố định để tái lập)", type: "number", default: "7" },
    ],
    argv: ["patchx", "fuzz", "--iter", "{{iter}}", "--seed", "{{seed}}"] },
  TASKS.kho.find(t => t.id === "kho_hist"),
];

/* ---------- tiện ích ---------- */
function el(tag, cls, html) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
}
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}
function allTasks() {
  return Object.values(TASKS).flat();
}
const LEVEL = {
  pt_dex: "adv", pt_dupes: "adv", pt_audit: "adv",
  pt_callgraph: "adv", pt_diff: "adv", pt_remote: "adv",
  kh_llm: "adv", kt_preflight: "adv", kt_validate: "adv", kt_bench: "adv",
  bc_bench: "adv", bc_bl_show: "adv", bc_bl_cap: "adv",
  hs_fuzz: "adv", kho_audit: "adv", kho_index: "adv", kho_dupes: "adv",
  kho_simulate: "adv",
  kho_upgrade: "exp", kho_optimize: "exp", kho_combo: "exp",
  kho_selfcheck: "exp", kho_test: "exp", kho_hist: "exp",
  va_manual: "exp", va_patch_edit: "exp",
};
for (const [id, lv] of Object.entries(LEVEL)) {
  const t = allTasks().find(x => x.id === id);
  if (t) t.level = lv;
}
function opts(type) {
  const list = [];
  if (type === "select_tree") {
    for (const a of STATE.apks) list.push({ v: "Apks/" + a.name, t: a.name + " (" + fmtSize(a.size) + ")" });
    for (const t of STATE.trees) list.push({ v: "apk_trees/" + t, t: "cây: " + t });
  }
  if (type === "select_apk") {
    for (const a of STATE.apks) list.push({ v: "Apks/" + a.name, t: a.name + " (" + fmtSize(a.size) + ")" });
  }
  if (type === "select_device") {
    const ws = STATE.WORKERS && STATE.WORKERS.clients;
    if (ws && ws.length) {
      for (const c of ws) list.push({ v: c.addr, t: c.name + " (" + c.addr + ")" });
    } else {
      list.push({ v: "", t: "(chưa có máy — bật adb)" });
    }
  }
  if (!list.length) list.push({ v: "", t: "(chưa có — giải mã APK trước)" });
  return list;
}
function fmtSize(n) {
  if (!n) return "?";
  if (n > 1e6) return (n / 1e6).toFixed(1) + " MB";
  if (n > 1e3) return (n / 1e3).toFixed(0) + " KB";
  return n + " B";
}

/* ---------- xây argv từ task + form ---------- */
function buildArgv(task, which) {
  const argvTpl = task[which || "argv"] || [];
  const root = document.getElementById("form-" + task.id);
  const val = key => {
    if (root) {
      const f = root.querySelector(`[name="${key}"]`);
      if (f) {
        if (f.type === "checkbox") return f.checked ? "1" : "";
        return f.value.trim();
      }
    }
    return task[key] ?? "";
  };
  const argv = [];
  for (const a of argvTpl) {
    let item = a;
    const m = item.match(/^\{\{([+-]?)([a-z]+)(?::([^}]+))?\}\}$/);
    if (m) {
      const neg = m[1] === "-", plus = m[1] === "+";
      const v = val(m[2]);
      if (m[3] === "value") {
        if (v) { argv.push(v); }
      } else if (m[3]) {
        if (plus && v) argv.push(m[3]);
        if (neg && !v) argv.push(m[3]);
      } else if (v) {
        argv.push(v);
      }
      continue;
    }
    if (item.includes("{{")) {
      item = item.replace(/\{\{([a-z]+)\}\}/g, (_, k) => val(k));
      if (item.trim()) argv.push(item);
    } else {
      argv.push(item);
    }
  }
  return argv;
}

/* ---------- chạy lệnh + stream ---------- */
const running = new Set();
function doAction(name) {
  if (name === "planui") return openPlanUi();
  if (name === "map") return openMap();
  if (name === "manual_tree") return openManualTree();
  if (name === "manual_apply") return openManualApply();
  if (name.startsWith("stage")) return openStageDetail(+name.slice(5));
  if (name.startsWith("tab:")) return renderTab(name.slice(4));
  if (name === "clearhist") {
    localStorage.removeItem("patchx_ui_history");
    renderTab(ACTIVE);
  }
}
async function runTask(id, which) {
  const task = allTasks().find(t => t.id === id);
  if (!task) return;
  if (which === "argv2" && task.action2) return doAction(task.action2);
  if (task.action) return doAction(task.action);
  const log = document.getElementById("log-" + id);
  const btn = document.getElementById(which === "argv2" ? "run2-" + id : "run-" + id);
  const argv = buildArgv(task, which);
  if (!argv.length) { logShow(log, "Chưa có tham số đủ — điền vào biểu mẫu rồi chạy lại.", "bad"); return; }
  logShow(log, "");
  running.add(id);
  if (btn) { btn.disabled = true; btn.textContent = "Đang chạy…"; }
  log.classList.add("show");
  try {
    const ok = await streamRun(log, argv);
    savePipeline({ t: new Date().toLocaleString("vi-VN"), task: id,
      title: task.title, cmd: argv.join(" "), ok });
    if (ok) saveHistory(task.title, argv);
  } catch (e) {
    logShow(log, "Lỗi: " + e, "bad");
  } finally {
    running.delete(id);
    if (btn) { btn.disabled = false; btn.textContent = which === "argv2" ? (task.btn2 || "Tạo") : "Chạy"; }
  }
}
function logShow(log, text, cls) {
  log.innerHTML = "";
  if (!text) return;
  const pre = el("pre");
  pre.textContent = text;
  log.classList.add("show");
  if (cls) log.classList.add(cls);
  log.appendChild(pre);
}
function saveHistory(title, argv) {
  let h = [];
  try { h = JSON.parse(localStorage.getItem("patchx_ui_history") || "[]"); } catch (e) {}
  h.unshift({ t: new Date().toLocaleString("vi-VN"), title, cmd: argv.join(" ") });
  h = h.slice(0, 100);
  localStorage.setItem("patchx_ui_history", JSON.stringify(h));
}

/* ---------- mở trang kế hoạch ---------- */
async function openPlanUi() {
  try {
    const r = await fetch("/api/plan_ui");
    const j = await r.json();
    if (j.exists) { window.open("/plan_ui", "_blank"); }
    else { alert("Chưa có kế hoạch — hãy chạy 'Lập kế hoạch vượt chặn' trước."); }
  } catch (e) { alert("Lỗi mở kế hoạch: " + e); }
}

/* ---------- stream lệnh dùng chung ---------- */
async function streamRun(log, argv) {
  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ argv, timeout: 1800 }),
    });
    if (!res.ok || !res.body) {
      logShow(log, "Không kết nối được máy chủ.", "bad");
      return false;
    }
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop();
      const pre = log.querySelector("pre") || log.appendChild(el("pre"));
      pre.textContent += lines.join("\n") + "\n";
      log.scrollTop = log.scrollHeight;
    }
    if (buf.trim()) {
      const pre = log.querySelector("pre") || log.appendChild(el("pre"));
      pre.textContent += buf;
    }
    const m = (log.querySelector("pre") || {}).textContent || "";
    const ex = m.match(/mã thoát (\d+)/);
    return ex ? ex[1] === "0" : true;
  } catch (e) {
    logShow(log, "Lỗi: " + e, "bad");
    return false;
  }
}

/* ---------- overlay chung ---------- */
function overlay(title, bodyCls) {
  const o = el("div", "ovl");
  const head = el("div", "ovhead");
  head.appendChild(el("h3", "", esc(title)));
  const x = el("button", "x", "✕ Đóng");
  x.onclick = () => o.remove();
  head.appendChild(x);
  o.appendChild(head);
  const body = el("div", "ovbody" + (bodyCls ? " " + bodyCls : ""));
  o.appendChild(body);
  document.body.appendChild(o);
  return { body, close: () => o.remove() };
}

/* ---------- thanh trạng thái 6 tầng ---------- */
const TASK_AREA = {};
function buildTaskArea() {
  Object.entries(AREAS).forEach(([k, a]) => {
    if (a.tasks) (TASKS[a.tasks] || []).forEach(t => { TASK_AREA[t.id] = k; });
  });
  (TASKS.home || []).forEach(t => { if (!TASK_AREA[t.id]) TASK_AREA[t.id] = "home"; });
  (TASKS.bypass || []).forEach(t => { if (!TASK_AREA[t.id]) TASK_AREA[t.id] = "ke_hoach"; });
  (TASKS.mod || []).forEach(t => { if (!TASK_AREA[t.id]) TASK_AREA[t.id] = "ke_hoach"; });
  (TASKS.hook || []).forEach(t => { if (!TASK_AREA[t.id]) TASK_AREA[t.id] = "ke_hoach"; });
  (TASKS.quytrinh || []).forEach(t => { if (!TASK_AREA[t.id]) TASK_AREA[t.id] = "va_loi"; });
  (TASKS.kho || []).forEach(t => { if (!TASK_AREA[t.id]) TASK_AREA[t.id] = "he_thong"; });
}
function renderStatusBar() {
  const bar = document.getElementById("statusbar");
  if (!bar) return;
  bar.innerHTML = "";
  for (const st of STAGES) {
    const b = el("button", "st " + stageState(st.n));
    b.title = st.desc;
    b.innerHTML = `<span class="ic">${st.ic}</span>${st.n}. ${esc(st.name)}`;
    b.onclick = () => openStageDetail(st.n);
    bar.appendChild(b);
  }
}
function openStageDetail(n) {
  const st = STAGES[n - 1];
  const o = overlay("Tầng " + st.n + " · " + st.name, "stagepane");
  o.body.appendChild(el("p", "mut", st.desc));
  const runs = pipelineRuns().filter(e => st.tasks.includes(e.task)).slice(0, 12);
  if (!runs.length) {
    o.body.appendChild(el("p", "mut", "Chưa có lần chạy nào cho tầng này — chạy tác vụ trong danh sách để cập nhật."));
    return;
  }
  for (const r of runs) {
    const d = el("div", "run");
    d.appendChild(el("div", "", `<b>${esc(r.title)}</b> · <span class="mut">${esc(r.t)}</span>`));
    d.appendChild(el("div", "cmd", "$ " + esc(r.cmd)));
    d.appendChild(el("div", r.ok ? "ok" : "no", r.ok ? "✓ THÀNH CÔNG" : "✗ THẤT BẠI"));
    const go = el("button", "btn sm", "Mở tác vụ");
    go.onclick = () => {
      const a = TASK_AREA[r.task];
      o.close();
      if (a) renderTab(a);
    };
    d.appendChild(go);
    o.body.appendChild(d);
  }
}

/* ---------- bản đồ toàn bộ toolkit ---------- */
function openMap() {
  const o = overlay("🗺️ Bản đồ toàn bộ toolkit", "map");
  const go = tab => () => { o.close(); renderTab(tab); };
  const col = (label, nodes) => {
    o.body.appendChild(el("div", "grp", label));
    const m = el("div", "mrow");
    for (const nd of nodes) {
      const b = el("button", "node", `<b>${nd.ic} ${esc(nd.name)}</b>${esc(nd.d || "")}`);
      b.onclick = go(nd.tab);
      m.appendChild(b);
    }
    o.body.appendChild(m);
  };
  col("🔬 PHÂN TÍCH", [
    { name: "Manifest & cây", ic: "📄", tab: "phan_tich", d: "giải mã, quét kho" },
    { name: "Độ phủ patch", ic: "🎯", tab: "phan_tich", d: "coverage" },
    { name: "Call graph", ic: "🕸️", tab: "phan_tich", d: "analyze" },
    { name: "DEX 64K", ic: "🧮", tab: "phan_tich", d: "dex-budget" },
    { name: "Diff APK", ic: "🔁", tab: "phan_tich", d: "gốc ↔ mod" },
    { name: "Bản đồ từ xa", ic: "📡", tab: "phan_tich", d: "remote-map" },
  ]);
  col("🧠 LẬP KẾ HOẠCH", [
    { name: "Kế hoạch vượt chặn", ic: "🗺️", tab: "ke_hoach", d: "apk-plan" },
    { name: "Mục tiêu bypass", ic: "🔓", tab: "ke_hoach", d: "VIP, chữ ký, root…" },
    { name: "Mục tiêu mod", ic: "🛠️", tab: "ke_hoach", d: "quảng cáo, theo dõi…" },
    { name: "Hook dữ liệu", ic: "🧪", tab: "ke_hoach", d: "API, token, từ xa" },
    { name: "Gợi ý LLM", ic: "🤖", tab: "ke_hoach", d: "ý định → patch" },
  ]);
  col("🛠️ PATCH & COMBO", [
    { name: "Dây chuyền 1 chạm", ic: "🚀", tab: "va_loi", d: "apk-full" },
    { name: "Áp patch", ic: "📌", tab: "va_loi", d: "apply + sao lưu" },
    { name: "Combo tự động", ic: "🧩", tab: "va_loi", d: "gộp theo năng lực" },
    { name: "Manual Mode", ic: "✍️", tab: "va_loi", d: "duyệt cây + smali" },
  ]);
  col("🏗️ BUILD · 🧪 KIỂM THỬ", [
    { name: "Preflight", ic: "🛡️", tab: "kiem_thu", d: "cổng an toàn" },
    { name: "Xác thực", ic: "✔️", tab: "kiem_thu", d: "validate" },
    { name: "Build + ký", ic: "🏗️", tab: "kiem_thu", d: "apk-build" },
    { name: "Chạy thử M2/M3", ic: "📱", tab: "kiem_thu", d: "máy ảo" },
  ]);
  col("📊 BÁO CÁO · ⚙️ HỆ THỐNG", [
    { name: "Kho lỗi", ic: "🐛", tab: "bao_cao", d: "failure" },
    { name: "Baseline", ic: "📏", tab: "bao_cao", d: "chống hồi quy" },
    { name: "Sức khoẻ", ic: "❤️", tab: "he_thong", d: "selfcheck/doctor" },
    { name: "3 máy", ic: "🖥️", tab: "he_thong", d: "worker manager" },
    { name: "Kiểm thử", ic: "🧪", tab: "he_thong", d: "patchx test" },
  ]);
}

/* ---------- Manual Mode ---------- */
function openManualTree() {
  const o = overlay("✍️ Manual Mode — duyệt cây & xem tệp", null);
  const head = el("div", "treehead");
  const sel = el("select");
  sel.name = "apk";
  if (!MAN.apk && STATE.trees.length) MAN.apk = STATE.trees[0];
  for (const t of STATE.trees) {
    const op = el("option", "", esc(t));
    op.value = t;
    if (t === MAN.apk) op.selected = true;
    sel.appendChild(op);
  }
  sel.onchange = () => { MAN.apk = sel.value; MAN.dir = ""; load(); };
  head.appendChild(sel);
  const srchWrap = el("div", "srch");
  const qin = el("input");
  qin.placeholder = "Tìm chuỗi trong cây (vd: isRooted, license…)";
  const qb = el("button", "btn sm", "Tìm");
  srchWrap.appendChild(qin); srchWrap.appendChild(qb);
  const crumb = el("div", "crumb", "…");
  const listing = el("div", "treegrid");
  const filev = el("div", "fileview");
  filev.style.display = "none";
  o.body.appendChild(head); o.body.appendChild(srchWrap);
  o.body.appendChild(crumb); o.body.appendChild(listing); o.body.appendChild(filev);
  const load = async () => {
    filev.style.display = "none";
    crumb.textContent = "Đang duyệt…";
    const r = await fetch("/api/tree?apk=" + encodeURIComponent(MAN.apk) + "&p=" + encodeURIComponent(MAN.dir));
    if (!r.ok) { crumb.textContent = "Lỗi mở cây APK."; return; }
    const j = await r.json();
    crumb.textContent = "Cây " + MAN.apk + (j.dir ? " / " + j.dir : "");
    listing.innerHTML = "";
    if (j.dir) {
      const up = el("button", "d", "⬆ Lên trên");
      up.onclick = () => { MAN.dir = j.dir.split("/").slice(0, -1).join("/"); load(); };
      listing.appendChild(up);
    }
    for (const d of j.dirs) {
      const b = el("button", "d", "📁 " + esc(d));
      b.onclick = () => { MAN.dir = j.dir ? j.dir + "/" + d : d; load(); };
      listing.appendChild(b);
    }
    for (const f of j.files) {
      const b = el("button", "", "📄 " + esc(f.name) + " · " + fmtSize(f.size));
      b.onclick = () => openFile(filev, j.dir ? j.dir + "/" + f.name : f.name);
      listing.appendChild(b);
    }
    if (!j.dirs.length && !j.files.length) listing.appendChild(el("p", "mut", "Thư mục trống."));
  };
  qb.onclick = async () => {
    const q = qin.value.trim();
    if (!q) return;
    filev.style.display = "none";
    listing.innerHTML = "";
    crumb.textContent = "Đang tìm \"" + q + "\"…";
    const r = await fetch("/api/search?apk=" + encodeURIComponent(MAN.apk) + "&q=" + encodeURIComponent(q));
    const j = await r.json();
    crumb.textContent = "Kết quả tìm \"" + q + "\" — " + (j.hits || []).length + " tệp (tối đa 50)";
    listing.innerHTML = "";
    for (const h of (j.hits || [])) {
      const b = el("button", "", "🔎 " + esc(h));
      b.onclick = () => {
        MAN.dir = h.includes("/") ? h.slice(0, h.lastIndexOf("/")) : "";
        load().then(() => openFile(filev, h));
      };
      listing.appendChild(b);
    }
    if (!(j.hits || []).length) listing.appendChild(el("p", "mut", "Không tìm thấy."));
  };
  load();
}
async function openFile(filev, rel) {
  const r = await fetch("/api/file?apk=" + encodeURIComponent(MAN.apk) + "&p=" + encodeURIComponent(rel));
  const j = await r.json();
  filev.style.display = "block";
  if (j.binary) {
    filev.textContent = "Tệp nhị phân (" + fmtSize(j.size) + ") — không hiển thị.";
    return;
  }
  filev.textContent = "── " + j.path + " (" + fmtSize(j.size) + ")" + (j.truncated ? " · CẮT 512KB" : "") + " ──\n\n" + j.text;
}
function openManualApply() {
  const o = overlay("✍️ Soạn patch thủ công", null);
  const sel = el("select");
  if (!MAN.apk && STATE.trees.length) MAN.apk = STATE.trees[0];
  for (const t of STATE.trees) {
    const op = el("option", "", esc(t));
    op.value = t;
    if (t === MAN.apk) op.selected = true;
    sel.appendChild(op);
  }
  sel.onchange = () => { MAN.apk = sel.value; };
  o.body.appendChild(el("label", "", "Cây APK đích"));
  o.body.appendChild(sel);
  const dry = el("label", "chk");
  dry.innerHTML = `<input type="checkbox" checked> Chỉ xem trước (dry-run, an toàn)`;
  o.body.appendChild(dry);
  o.body.appendChild(el("label", "", "Nội dung patch (khối [MATCH_REPLACE]… hoặc text)"));
  const ta = el("textarea", "texter");
  ta.placeholder = "[MATCH_REPLACE]\nTARGET:\nsmali*/*.smali\nMATCH:\n...\nREGEX:\nfalse\nREPLACE:\n...\n[/MATCH_REPLACE]";
  o.body.appendChild(ta);
  const log = el("div", "log");
  log.id = "manual_log";
  o.body.appendChild(log);
  const row = el("div", "row");
  const b1 = el("button", "btn", "Lưu & chạy thử");
  const b2 = el("button", "btn2", "Lưu & ÁP THẬT");
  row.appendChild(b1); row.appendChild(b2);
  o.body.appendChild(row);
  const run = async apply => {
    const content = ta.value.trim();
    if (!content) { logShow(log, "Chưa có nội dung patch.", "bad"); return; }
    logShow(log, "");
    log.classList.add("show");
    b1.disabled = b2.disabled = true;
    try {
      const r = await fetch("/api/manual_save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content, name: "manual_patch.txt" }) });
      const j = await r.json();
      if (!j.path) { logShow(log, "Lưu thất bại: " + (j.lỗi || ""), "bad"); return; }
      const argv = ["patchx", "apply", j.path, "apk_trees/" + MAN.apk];
      if (!apply) argv.push("--dry-run");
      const ok = await streamRun(log, argv);
      savePipeline({ t: new Date().toLocaleString("vi-VN"), task: "va_patch_edit",
        title: "Soạn patch thủ công", cmd: argv.join(" "), ok });
    } catch (e) { logShow(log, "Lỗi: " + e, "bad"); }
    finally { b1.disabled = b2.disabled = false; }
  };
  b1.onclick = () => run(false);
  b2.onclick = () => run(true);
}

/* ---------- render ---------- */
function renderTab(name) {
  ACTIVE = name;
  renderStatusBar();
  view.innerHTML = "";
  document.querySelectorAll("#nav button").forEach(b =>
    b.classList.toggle("on", b.dataset.tab === name));
  const area = AREAS[name];
  if (!area) return renderHome();
  if (area.render === "home") return renderHome();
  if (area.render === "goals") return renderKeHoach();
  if (area.render === "system") return renderHeThong();
  return renderTasks(area.title, area.subtitle, TASKS[area.tasks]);
}

function renderKeHoach() {
  view.appendChild(el("h2", "", "Kế hoạch"));
  view.appendChild(el("p", "mut", "Chọn mục tiêu để xem phương án, hoặc lập kế hoạch tự động cho cả APK."));
  renderGoalTab("Mục tiêu vượt chặn",
    "Vô hiệu hoá kiểm tra: khoá trả phí, chữ ký, root, SSL pinning…", "bypass", TASKS.bypass);
  renderGoalTab("Mục tiêu chỉnh sửa",
    "Thay đổi hành vi: chặn quảng cáo, xoá theo dõi, mở khoá tính năng…", "mod", TASKS.mod);
  renderGoalTab("Mục tiêu hook",
    "Bắt dữ liệu, tìm API, hook method, điều khiển từ xa.", "hook", TASKS.hook);
  renderTasks("Kế hoạch tự động",
    "Quét APK → xếp hạng patch kèm tỷ lệ thành công % → mô phỏng.", TASKS.ke_hoach);
}

async function renderHeThong() {
  view.appendChild(el("h2", "", "Hệ thống"));
  view.appendChild(el("p", "mut", "Trạng thái 3 máy đang phối hợp + công cụ và sức khoẻ toolkit."));
  await renderWorkers();
  renderTasks("Công cụ & sức khoẻ", "", TASKS.he_thong);
  renderHistory();
}

async function renderWorkers() {
  const wrap = el("div", "wrk");
  let w = null;
  try { w = await (await fetch("/api/workers")).json(); } catch (e) { /* máy chủ tắt */ }
  const main = w && w.main;
  if (main) {
    const c = el("div", "card ok");
    c.appendChild(el("h3", "", "🏠 " + esc(main.name)));
    c.appendChild(el("p", "", esc(main.role)));
    c.appendChild(el("div", "kv",
      `<b>Kiểu máy</b><span>${esc(main.model)}</span>` +
      `<b>Tải CPU</b><span>${esc(main.load)}</span>` +
      `<b>Toolkit</b><span class="mut">${esc(main.toolkit)}</span>`));
    const rm = el("div", "rowm");
    rm.appendChild(el("span", "tagm ok", "HOẠT ĐỘNG"));
    rm.appendChild(el("span", "mut", esc(main.time)));
    c.appendChild(rm);
    wrap.appendChild(c);
  }
  for (const cl of (w && w.clients) || []) {
    const ok = !!cl.ok;
    const c = el("div", "card " + (ok ? "ok" : "bad"));
    c.appendChild(el("h3", "", esc(cl.name)));
    c.appendChild(el("p", "", esc(cl.role)));
    c.appendChild(el("div", "kv",
      `<b>Địa chỉ</b><span>${esc(cl.addr)}</span>` +
      `<b>Kiểu máy</b><span>${esc(cl.model || "—")}</span>` +
      `<b>Android</b><span>${esc(cl.android || "—")}</span>` +
      `<b>Kết nối</b><span>${esc(cl.transport)}</span>`));
    const rm = el("div", "rowm");
    rm.appendChild(el("span", "tagm " + (ok ? "ok" : "bad"),
      ok ? "ADB SẴN SÀNG" : "ADB MẤT"));
    if (cl.ssh_ok !== undefined) {
      rm.appendChild(el("span", "tagm " + (cl.ssh_ok ? "ok" : "bad"),
        cl.ssh_ok ? "SSH SẴN SÀNG" : "SSH MẤT"));
    }
    c.appendChild(rm);
    wrap.appendChild(c);
  }
  if (!w) wrap.appendChild(el("p", "mut", "Không lấy được trạng thái máy chủ."));
  view.appendChild(wrap);
}

function renderGoalTab(title, subtitle, goalKey, tasks) {
  view.appendChild(el("h2", "", title));
  view.appendChild(el("p", "mut", subtitle));
  const bar = el("div", "goalbar");
  bar.appendChild(el("p", "", "Bạn muốn làm gì? Chọn mục tiêu để xem cách thực hiện:"));
  const chips = el("div", "chips");
  for (const g of GOALS[goalKey] || []) {
    const b = el("button", "chip", esc(g.label));
    b.onclick = () => {
      const card = document.getElementById("card-" + g.id);
      if (!card) return;
      card.scrollIntoView({ behavior: "smooth", block: "start" });
      card.classList.add("flash");
      setTimeout(() => card.classList.remove("flash"), 1400);
    };
    chips.appendChild(b);
  }
  bar.appendChild(chips);
  view.appendChild(bar);
  view.appendChild(el("p", "mut", "Mỗi mục tiêu có 2 nút: <b>Lập kế hoạch</b> (quét APK, đề xuất phương án + tỷ lệ %) và <b>Tạo combo sẵn</b> (sinh patch gộp theo đúng mục tiêu)."));
  renderTasks("Mục tiêu", "", tasks);
}

function renderHome() {
  view.appendChild(el("h2", "", "Trang chủ"));
  const cards = [
    ["Môi trường", STATE.tools ? (Object.values(STATE.tools).filter(Boolean).length + "/" + Object.keys(STATE.tools).length) + " công cụ sẵn sàng" : "—", STATE.tools && Object.values(STATE.tools).every(Boolean) ? "ok" : "warn"],
    ["Patch chuẩn hoá", STATE.patches, ""],
    ["Combo chính", STATE.combos, ""],
    ["Combo tự động", STATE.combos_auto, ""],
    ["APK trong Apks/", STATE.apks.length, ""],
    ["Cây APK đã giải mã", STATE.trees.length, ""],
  ];
  const g = el("div", "grid");
  for (const [k, v, tone] of cards) {
    g.appendChild(el("div", "card", `<div class="stat"><b class="${tone}">${esc(v)}</b><span>${esc(k)}</span></div>`));
  }
  view.appendChild(g);
  const qnav = el("div", "chips");
  const mk = (label, act) => {
    const b = el("button", "chip", label);
    b.onclick = () => doAction(act);
    qnav.appendChild(b);
  };
  mk("🗺️ Bản đồ toolkit", "map");
  mk("✍️ Manual Mode", "manual_tree");
  mk("📄 Mở trang kế hoạch", "planui");
  view.appendChild(qnav);
  if (STATE.apks.length) {
    view.appendChild(el("h3", "", "APK sẵn sàng quét"));
    const t = el("table");
    t.appendChild(el("thead", "", "<tr><th>Tệp</th><th>Dung lượng</th></tr>"));
    const tb = el("tbody");
    for (const a of STATE.apks) tb.appendChild(el("tr", "", `<td>${esc(a.name)}</td><td>${fmtSize(a.size)}</td>`));
    t.appendChild(tb);
    view.appendChild(t);
  }
  view.appendChild(el("h3", "", "Dây chuyền 6 tầng"));
  const steps = ["Hiểu cây APK", "Lọc ứng viên", "Lập kế hoạch", "Áp patch", "Build + ký", "Chạy thử, ghi bài học"];
  const flow = el("div", "flow");
  steps.forEach((s, i) => flow.appendChild(el("div", "step", `<span class="n">${i + 1}</span><span>${s}</span>`)));
  view.appendChild(flow);
  view.appendChild(el("p", "mut", "Bắt đầu: vào tab <b>Vượt chặn</b> / <b>Chỉnh sửa</b> / <b>Hook</b> chọn mục tiêu, hoặc chạy dây chuyền 1 chạm bên dưới."));
  renderTasks("Tác vụ nhanh", "", TASKS.home);
}

function visibleTasks(tasks) {
  return tasks.filter(t => {
    const lv = t.level || "basic";
    if (MODE === "exp") return true;
    if (MODE === "adv") return lv !== "exp";
    return lv === "basic";
  });
}
function renderTasks(title, subtitle, tasks) {
  view.appendChild(el("h2", "", title));
  if (subtitle) view.appendChild(el("p", "mut", subtitle));
  const g = el("div", "grid");
  for (const t of visibleTasks(tasks)) g.appendChild(cardTask(t));
  const hidden = tasks.length - visibleTasks(tasks).length;
  if (hidden > 0) view.appendChild(el("p", "mut",
    "(" + hidden + " tác vụ nâng cao/chuyên gia đang ẩn — đổi chế độ ở trên để hiện.)"));
  view.appendChild(g);
  if (title === "Kho & công cụ") renderHistory();
}

function cardTask(t) {
  const c = el("div", "card");
  c.id = "card-" + t.id;
  c.appendChild(el("h3", "", esc(t.title) + (t.cap ? `<span class="tag">${esc(t.cap)}</span>` : "")));
  c.appendChild(el("p", "", esc(t.desc)));
  if (t.fields && t.fields.length) {
    const form = el("div");
    form.id = "form-" + t.id;
    for (const f of t.fields) {
      form.appendChild(fieldHtml(f));
    }
    c.appendChild(form);
  }
  const row = el("div", "row");
  const btn = el("button", "btn", t.action ? "Mở" : "Lập kế hoạch");
  btn.id = "run-" + t.id;
  btn.onclick = () => runTask(t.id);
  row.appendChild(btn);
  if (t.argv2 || t.action2) {
    const btn2 = el("button", "btn2", t.btn2 || (t.action2 ? "Mở" : "Tạo"));
    btn2.id = "run2-" + t.id;
    btn2.onclick = () => runTask(t.id, "argv2");
    row.appendChild(btn2);
  }
  c.appendChild(row);
  const log = el("div", "log");
  log.id = "log-" + t.id;
  c.appendChild(log);
  return c;
}

function fieldHtml(f) {
  const wrap = el("div");
  wrap.appendChild(el("label", "", f.label));
  if (f.type === "check") {
    const l = el("label", "chk");
    l.innerHTML = `<input type="checkbox" name="${f.key}" ${f.default ? "checked" : ""}> ${esc(f.label)}`;
    wrap.replaceChild(l, wrap.firstChild);
    return wrap;
  }
  let inp;
  if (f.type === "select_tree" || f.type === "select_apk"
      || f.type === "select_device") {
    inp = el("select");
    inp.name = f.key;
    const list = opts(f.type);
    for (const o of list) {
      const oe = el("option", "", esc(o.t));
      oe.value = o.v;
      if (f.default && o.v === f.default) oe.selected = true;
      inp.appendChild(oe);
    }
  } else if (f.type === "select") {
    inp = el("select");
    inp.name = f.key;
    for (const o of f.opts || []) {
      const oe = el("option", "", esc(o.t));
      oe.value = o.v;
      if (f.default && o.v === f.default) oe.selected = true;
      inp.appendChild(oe);
    }
  } else if (f.type === "number") {
    inp = el("input");
    inp.type = "number";
    inp.name = f.key;
    inp.value = f.default || "";
  } else {
    inp = el("input");
    inp.type = "text";
    inp.name = f.key;
    inp.value = f.default || "";
  }
  wrap.appendChild(inp);
  if (f.hint) wrap.appendChild(el("div", "mut", f.hint));
  return wrap;
}

function renderHistory() {
  let h = [];
  try { h = JSON.parse(localStorage.getItem("patchx_ui_history") || "[]"); } catch (e) {}
  view.appendChild(el("h3", "", "Lịch sử lệnh (" + h.length + ")"));
  if (!h.length) {
    view.appendChild(el("p", "mut", "Chưa có lệnh nào — chạy một tác vụ ở tab khác."));
    return;
  }
  const t = el("table");
  t.appendChild(el("thead", "", "<tr><th>Lúc</th><th>Tác vụ</th><th>Lệnh</th></tr>"));
  const tb = el("tbody");
  for (const e of h.slice(0, 30)) {
    tb.appendChild(el("tr", "", `<td>${esc(e.t)}</td><td>${esc(e.title)}</td><td class="mut">${esc(e.cmd)}</td>`));
  }
  t.appendChild(tb);
  view.appendChild(t);
}

/* ---------- khởi động ---------- */
async function init() {
  try {
    const r = await fetch("/api/state");
    STATE = await r.json();
  } catch (e) {
    envEl.innerHTML = `<span class="dot bad"></span> không kết nối được máy chủ`;
    return;
  }
  try { STATE.WORKERS = await (await fetch("/api/workers")).json(); }
  catch (e) { STATE.WORKERS = null; }
  const nOk = Object.values(STATE.tools).filter(Boolean).length;
  const nAll = Object.keys(STATE.tools).length;
  const ok = nOk === nAll;
  envEl.innerHTML = `<span class="dot ${ok ? "ok" : "bad"}"></span> công cụ ${nOk}/${nAll} sẵn sàng · ${STATE.patches} patch · ${STATE.apks.length} APK · ${esc(STATE.time)}`;
  document.querySelectorAll("#nav button").forEach(b =>
    b.addEventListener("click", () => renderTab(b.dataset.tab)));
  const syncMode = () => {
    document.querySelectorAll("#modes button").forEach(x =>
      x.classList.toggle("on", x.dataset.mode === MODE));
  };
  document.querySelectorAll("#modes button").forEach(b => {
    b.addEventListener("click", () => {
      MODE = b.dataset.mode;
      try { localStorage.setItem("patchx_mode", MODE); } catch (e) {}
      syncMode();
      renderTab(ACTIVE);
    });
  });
  syncMode();
  buildTaskArea();
  renderStatusBar();
  renderTab("home");
}
init();
