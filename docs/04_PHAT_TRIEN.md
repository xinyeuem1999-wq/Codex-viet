# Quy trình phát triển PatchX

Mỗi thay đổi đi theo một vòng nhỏ:

```text
Ý tưởng
  ↓
Fixture / test
  ↓
Sửa code
  ↓
Chạy test liên quan
  ↓
Chạy toàn bộ test
  ↓
So baseline
  ↓
Cập nhật tài liệu
```

## Quy tắc khi sửa

1. Không sửa nhiều hệ thống cùng lúc.
2. Một thay đổi phải có một mục tiêu rõ ràng.
3. Test cũ phải tiếp tục PASS.
4. Không xóa tính năng chỉ vì chưa hiểu nó; trước tiên ghi nhận nó thuộc nhóm nào.
5. Không đổi tên hoặc di chuyển module lõi khi chưa kiểm tra toàn bộ import/path.
6. Khi chưa hiểu một module, để nó ngoài đường chạy chính thay vì tiếp tục mở rộng nó.
