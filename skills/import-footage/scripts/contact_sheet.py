#!/usr/bin/env python3
"""Sample frames across clips and tile them into contact sheets.

  contact_sheet.py <folder-or-file> --out <dir> [--per-clip 4] [--width 300]
                                    [--sheet 1] [--pattern '*.mp4']

--sheet 1  one sheet per clip (default; best for triage)
--sheet N  N clips per sheet, tiled in a grid (compact overview)

Frames are sampled evenly across each clip, skipping the very start and end
where camera handling artefacts live.
"""
import os, sys, glob, math, argparse, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Point this at your own video-engine checkout, e.g. via:
#   export VIDEO_ENGINE_DIR=/path/to/video-engine
FF = os.path.join(os.environ.get("VIDEO_ENGINE_DIR", os.path.expanduser("~/video-engine")), "bin")

def run(a): subprocess.run(a, stdin=subprocess.DEVNULL,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def dur(p):
    r = subprocess.run([f"{FF}/ffprobe","-v","error","-show_entries",
                        "format=duration","-of","default=nw=1:nk=1",p],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    try: return float(r.stdout.strip().splitlines()[0])
    except Exception: return 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target"); ap.add_argument("--out", required=True)
    ap.add_argument("--per-clip", type=int, default=4)
    ap.add_argument("--width", type=int, default=300)
    ap.add_argument("--sheet", type=int, default=1)
    ap.add_argument("--pattern", default="*.mp4")
    a = ap.parse_args()

    if os.path.isdir(a.target):
        clips = sorted(glob.glob(os.path.join(a.target, a.pattern)))
        clips += sorted(glob.glob(os.path.join(a.target, a.pattern.upper())))
    else:
        clips = [a.target]
    clips = sorted(set(clips))
    if not clips: sys.exit(f"No clips matching {a.pattern} in {a.target}")

    os.makedirs(a.out, exist_ok=True)
    tmp = os.path.join(a.out, "_tmp"); os.makedirs(tmp, exist_ok=True)
    made = []

    for ci, clip in enumerate(clips, 1):
        d = dur(clip)
        if d <= 0: print(f"  skip (unreadable): {os.path.basename(clip)}"); continue
        n = a.per_clip
        for k in range(n):
            t = d * (0.10 + 0.80 * (k / max(1, n - 1)))
            run([f"{FF}/ffmpeg","-nostdin","-v","error","-ss",f"{t:.2f}","-i",clip,
                 "-frames:v","1","-vf",f"scale={a.width}:-2","-q:v","4","-y",
                 os.path.join(tmp, f"{k+1:02d}.jpg")])
        got = sorted(glob.glob(os.path.join(tmp, "*.jpg")))
        if got:
            name = os.path.splitext(os.path.basename(clip))[0]
            out = os.path.join(a.out, f"{ci:03d}__{name}.jpg")
            run([f"{FF}/ffmpeg","-nostdin","-v","error","-i",
                 os.path.join(tmp,"%02d.jpg"),"-filter_complex",
                 f"tile={len(got)}x1","-frames:v","1","-q:v","4","-y",out])
            made.append(out)
            print(f"  {os.path.basename(out)}   ({d:.0f}s)")
        for f in glob.glob(os.path.join(tmp,"*.jpg")): os.remove(f)

    # optional: combine per-clip strips into grouped sheets
    if a.sheet > 1 and made:
        for i in range(0, len(made), a.sheet):
            grp = made[i:i+a.sheet]
            for j, src in enumerate(grp, 1):
                run([f"{FF}/ffmpeg","-nostdin","-v","error","-i",src,"-vf",
                     f"scale={a.width*a.per_clip}:-2","-q:v","4","-y",
                     os.path.join(tmp, f"{j:02d}.jpg")])
            out = os.path.join(a.out, f"sheet_{i//a.sheet+1:02d}.jpg")
            run([f"{FF}/ffmpeg","-nostdin","-v","error","-i",
                 os.path.join(tmp,"%02d.jpg"),"-filter_complex",
                 f"tile=1x{len(grp)}","-frames:v","1","-q:v","4","-y",out])
            for f in glob.glob(os.path.join(tmp,"*.jpg")): os.remove(f)
            print(f"  grouped -> {os.path.basename(out)}")

    os.rmdir(tmp) if not os.listdir(tmp) else None
    print(f"\n{len(made)} sheet(s) in {a.out}")

if __name__ == "__main__": main()
