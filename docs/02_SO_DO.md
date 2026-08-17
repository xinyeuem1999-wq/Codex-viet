# Sơ đồ PatchX

## 5 bộ phận dễ nhớ

```text
1. MẮT       → model / phân tích APK
2. BỘ NÃO    → semantic-plan / tìm mục tiêu
3. BẢO VỆ    → preflight / kiểm tra trước khi làm
4. NGƯỜI THỢ → apply / thực hiện patch
5. BỘ NHỚ    → baseline / knowledge / failure
```

## Đường đi chính

```text
APK / cây APK
      ↓
   MODEL
      ↓
 TÌM MỤC TIÊU
      ↓
  CÓ CHẮC KHÔNG?
   ↙        ↘
 CÓ         KHÔNG
 ↓            ↓
PREFLIGHT    DỪNG
 ↓
APPLY
 ↓
VERIFY / TEST
 ↓
GHI KẾT QUẢ
```

## Nguyên tắc

- Không chắc mục tiêu → dừng.
- Chưa preflight → không apply.
- Apply lỗi → không coi là thành công.
- Thay đổi code phải giữ test/baseline.
- AI không nằm trên đường chạy bắt buộc.
