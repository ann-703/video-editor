#!/usr/bin/env python3
"""Sort camera media into date folders and quarantine proxy files.

  organize_media.py <folder> [--apply] [--keep-proxies]

Default is a dry run. Nothing moves until you pass --apply.

Filenames from Insta360 / GoPro / most action cams carry their own capture
timestamp (IMG_20260904_183926_008.jpg), which is more reliable than file
mtime because copying can rewrite mtime. We group on that.
"""
import os, re, sys, shutil, argparse
from collections import Counter

STAMP = re.compile(r'_(20\d{6})_')
MEDIA = {".mp4", ".mov", ".jpg", ".jpeg", ".png", ".heic", ".dng", ".insv"}
PROXY = {".lrv", ".thm"}   # phone-preview twins; useless on a computer

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--keep-proxies", action="store_true")
    a = ap.parse_args()

    root = os.path.abspath(a.folder)
    if not os.path.isdir(root): sys.exit(f"Not a folder: {root}")

    files = [f for f in os.listdir(root) if os.path.isfile(os.path.join(root, f))
             and not f.startswith(".")]

    # Anything still being written shows up as zero bytes. Sorting mid-copy
    # once moved three empty placeholders into date folders.
    empty = [f for f in files if os.path.getsize(os.path.join(root, f)) == 0]
    if empty:
        print(f"!! {len(empty)} zero-byte file(s) - a copy may still be running:")
        for f in empty[:10]: print(f"     {f}")
        print("   Wait for the copy to finish, then re-run.")
        if a.apply: sys.exit(1)

    moves, proxies, skipped = [], [], []
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in PROXY and not a.keep_proxies:
            proxies.append(f); continue
        if ext not in MEDIA and ext not in PROXY:
            skipped.append(f); continue
        m = STAMP.search(f)
        if not m:
            skipped.append(f); continue
        d = m.group(1)
        moves.append((f, f"{d[:4]}-{d[4:6]}-{d[6:]}"))

    by_date = Counter(d for _, d in moves)
    print(f"\n{len(files)} file(s) in {root}\n")
    for d in sorted(by_date):
        n = by_date[d]
        got = [f for f, dd in moves if dd == d]
        mp4 = sum(1 for f in got if f.lower().endswith((".mp4", ".mov")))
        img = n - mp4
        print(f"  {d}   {n:4d} files   {mp4:3d} video  {img:3d} photo")
    if proxies: print(f"\n  proxies to remove : {len(proxies)}")
    if skipped: print(f"  unrecognised      : {len(skipped)}")

    if not a.apply:
        print("\nDry run. Re-run with --apply to move them.")
        return

    for f, d in moves:
        os.makedirs(os.path.join(root, d), exist_ok=True)
        dst = os.path.join(root, d, f)
        if os.path.exists(dst):
            print(f"  exists, skipped: {f}"); continue
        shutil.move(os.path.join(root, f), dst)

    if proxies:
        trash = os.path.expanduser("~/.Trash/camera-proxies")
        os.makedirs(trash, exist_ok=True)
        for f in proxies:
            dst = os.path.join(trash, f)
            if os.path.exists(dst): os.remove(os.path.join(root, f))
            else: shutil.move(os.path.join(root, f), dst)
        print(f"\n  {len(proxies)} proxy file(s) -> Trash/camera-proxies (recoverable)")

    print(f"\nMoved {len(moves)} file(s) into {len(by_date)} date folder(s).")
    total = sum(len(os.listdir(os.path.join(root, d))) for d in by_date)
    print(f"Verify: {total} file(s) now in date folders.")

if __name__ == "__main__":
    main()
