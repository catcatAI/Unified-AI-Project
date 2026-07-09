#!/usr/bin/env python3
"""Read and analyze the card pile directory structure."""
import os

CARD_DIR = r"G:\我的雲端硬碟\卡片堆"

if not os.path.exists(CARD_DIR):
    print(f"Directory does not exist: {CARD_DIR}")
    # Try listing G: drive
    try:
        for item in os.listdir("G:\\"):
            print(f"G:\\: {item}")
    except:
        pass
    exit(1)

print(f"Card Pile Directory: {CARD_DIR}")
print()

# List root files
print("=== Root Files ===")
for f in sorted(os.listdir(CARD_DIR)):
    fpath = os.path.join(CARD_DIR, f)
    if os.path.isfile(fpath):
        size = os.path.getsize(fpath)
        try:
            with open(fpath, 'r', encoding='utf-8') as fh:
                content = fh.read(300)
            print(f"  {f} ({size}B) -> {content[:200]}")
        except Exception as e:
            print(f"  {f} ({size}B) -> [read error: {e}]")

# List subdirectories
print()
print("=== Subdirectories ===")
for d in sorted(os.listdir(CARD_DIR)):
    dpath = os.path.join(CARD_DIR, d)
    if os.path.isdir(dpath):
        print(f"\n  [{d}]")
        for f in sorted(os.listdir(dpath)):
            if f == "desktop.ini":
                continue
            fpath = os.path.join(dpath, f)
            size = os.path.getsize(fpath)
            try:
                with open(fpath, 'r', encoding='utf-8') as fh:
                    content = fh.read(300)
                print(f"    {f} ({size}B) -> {content[:150]}")
            except:
                print(f"    {f} ({size}B)")
