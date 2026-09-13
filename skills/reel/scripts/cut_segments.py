#!/usr/bin/env python3
"""Cut a shot list into downscaled segments ready for blurring and assembly.

  cut_segments.py --shots shots.txt --src <clips-folder> --out <segments-dir>
                  [--width 1080] [--height 1920]

shots.txt is one shot per line:
    <id> <source-filename> <start-seconds> <duration-seconds> [crop-x]
e.g.
    01 V_VID_20260904_173015_004.mp4 15.0 2.5
    12 VID_20260906_164156_085.mp4   1.0  2.0  60

crop-x is optional and only matters for landscape source in a vertical reel:
it is the left edge of the crop window in scaled pixels. Omit it and the crop
is centred. Use it when the subject sits off to one side and a centre crop
would cut them out of frame.

Working on downscaled segments rather than 4K masters is what makes every
later step fast enough to iterate on.
"""
import os, sys, argparse, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FFMPEG, FFPROBE, duration

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", required=True); ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--fps", default="30000/1001")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    rows = [l.split() for l in open(a.shots).read().strip().splitlines()
            if l.strip() and not l.startswith("#")]
    total = 0.0
    for row in rows:
        n, f, ss, d = row[0], row[1], row[2], row[3]
        crop_x = row[4] if len(row) > 4 else None
        src = os.path.join(a.src, f)
        if not os.path.exists(src):
            print(f"  !! missing source: {f}"); continue
        dst = os.path.join(a.out, f"s{n}.mp4")
        # -nostdin is mandatory: without it ffmpeg eats the caller's stdin
        subprocess.run([FFMPEG,"-nostdin","-v","error","-ss",ss,"-i",src,"-t",d,
            "-vf",(f"scale={a.width}:{a.height}:force_original_aspect_ratio=increase,"
                   f"crop={a.width}:{a.height}"
                   + (f":{crop_x}:0" if crop_x else "")
                   + f",fps={a.fps},setsar=1"),
            "-an","-c:v","libx264","-preset","veryfast","-crf","16",
            "-pix_fmt","yuv420p","-y",dst], stdin=subprocess.DEVNULL)
        got = duration(dst); total += got
        tag = f"  crop-x={crop_x}" if crop_x else ""
        print(f"  s{n}  {f[:38]:<40} {ss:>6}s +{d}s  -> {got:.2f}s{tag}")
    print(f"\n{len(rows)} segment(s), total {total:.2f}s")
    if abs(total - round(total)) > 0.5:
        print("   (check this against your target length)")

if __name__ == "__main__": main()
