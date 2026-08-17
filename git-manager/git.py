#!/usr/bin/env python3
import os
import subprocess
import sys

def run(cmd):
    print(f"\n$ {' '.join(cmd)}\n")
    return subprocess.run(cmd).returncode == 0

def git(*args):
    return run(["git", *args])

def pause():
    input("\nNhấn Enter để tiếp tục...")

def status():
    git("status")
    pause()

def pull():
    print("\n=== GIT PULL ===")
    git("pull")
    pause()

def push():
    print("\n=== GIT PUSH ===")
    subprocess.run(["git", "status"])
    message = input("\nCommit message: ").strip()
    if not message:
        print("❌ Commit message không được để trống.")
        pause()
        return
    if not git("add", "."):
        pause()
        return
    if not git("commit", "-m", message):
        pause()
        return
    git("push")
    pause()

def log():
    git("log", "--oneline", "--graph", "--decorate", "-20")
    pause()

def full_sync():
    print("\n=== ADD → COMMIT → PUSH ===")
    if not git("status"):
        pause()
        return
    message = input("\nCommit message: ").strip()
    if not message:
        print("❌ Commit message không được để trống.")
        pause()
        return
    if not git("add", "."):
        pause()
        return
    if not git("commit", "-m", message):
        pause()
        return
    if not git("push"):
        pause()
        return
    print("\n✅ Đã push thành công.")
    pause()

def check_git_repo():
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        print("❌ Thư mục hiện tại không phải Git repository.")
        print("Dùng: git clone <URL>")
        sys.exit(1)

def menu():
    while True:
        os.system("clear" if os.name != "nt" else "cls")
        print("""
╔══════════════════════════════════╗
║          GIT MANAGER             ║
╠══════════════════════════════════╣
║  1. Git Pull                     ║
║  2. Git Push                     ║
║  3. Git Status                   ║
║  4. Add + Commit + Push          ║
║  5. Git Log                      ║
║  0. Thoát                        ║
╚══════════════════════════════════╝
""")
        choice = input("Chọn: ").strip()
        if choice == "1":
            pull()
        elif choice == "2":
            push()
        elif choice == "3":
            status()
        elif choice == "4":
            full_sync()
        elif choice == "5":
            log()
        elif choice == "0":
            print("Bye!")
            break
        else:
            print("❌ Lựa chọn không hợp lệ.")
            pause()

if __name__ == "__main__":
    check_git_repo()
    menu()
