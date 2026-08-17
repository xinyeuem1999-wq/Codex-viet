# Git Manager CLI

CLI Python nhỏ để dùng Git trên Termux/Android.

## Tính năng

- Git pull
- Git push
- Git status
- Add + commit + push
- Git log
- Giao diện menu chạy trong terminal
- Không cần thư viện Python bên ngoài

## Cài trên Termux

```bash
pkg update
pkg install git python
```

## Cài đặt

Giải nén ZIP:

```bash
unzip git-manager.zip
cd git-manager
```

Cho phép chạy:

```bash
chmod +x git.py
```

Chạy:

```bash
python git.py
```

## Dùng như một lệnh

Bạn có thể đặt script vào `$PREFIX/bin`:

```bash
cp git.py $PREFIX/bin/gitui
chmod +x $PREFIX/bin/gitui
```

Sau đó đi vào một Git repository và chạy:

```bash
gitui
```

## Nếu chưa có repository

Clone repository trước:

```bash
git clone <URL_REPOSITORY>
cd <TEN_REPOSITORY>
gitui
```

## Push lần đầu

Nếu Git yêu cầu xác thực, hãy cấu hình SSH hoặc credential/token của Git hosting trước. Không đặt token/mật khẩu trực tiếp vào script.

## Lưu ý

Mục `Git Push` trong script sẽ:

1. `git add .`
2. `git commit -m "..."`
3. `git push`

Hãy kiểm tra `git status` trước khi commit nếu repository có nhiều thay đổi.

## Yêu cầu

- Python 3
- Git
- Termux hoặc Linux/macOS/Windows có Git + Python
