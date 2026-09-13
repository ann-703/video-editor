#!/usr/bin/env python3
"""Concatenate segments into a master, and stage it for Remotion.

  build_master.py --segments <dir> --shots shots.txt --out master.mp4
                  [--stage-remotion] [--music /path/to.mp3]

--stage-remotion also writes a constant-30fps copy to the Remotion project's
public/ folder, which is what the caption composition reads. Constant frame
rate matters: caption timings are computed in frames.
"""
import os, sys, argparse, subprocess, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FFMPEG, FFPROBE, REMOTION, duration

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segments", required=True); ap.add_argument("--shots", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stage-remotion", action="store_true")
    ap.add_argument("--music")
    a = ap.parse_args()

    ids = [l.split()[0] for l in open(a.shots).read().strip().splitlines()
           if l.strip() and not l.startswith("#")]
    listfile = os.path.join(a.segments, "_concat.txt")
    missing = []
    for n in ids:
        if not os.path.exists(os.path.join(a.segments, f"s{n}.mp4")): missing.append(n)
    if missing: sys.exit(f"Missing segment(s): {missing}")


    # The concat demuxer needs identical codec AND timebase. Segments come from
    # different tools (cv2 writes mpeg4 @ 2997/100, ffmpeg writes h264 @ 30000/1001)
    # and a mismatch is SILENTLY destructive: shots get dropped or timing balloons.
    # Normalise everything through ffmpeg first rather than trusting they match.
    norm = os.path.join(a.segments, "_norm")
    os.makedirs(norm, exist_ok=True)
    print(f"normalising {len(ids)} segment(s)...")
    for n in ids:
        src_ = os.path.join(a.segments, f"s{n}.mp4")
        dst_ = os.path.join(norm, f"s{n}.mp4")
        subprocess.run([FFMPEG,"-nostdin","-v","error","-i",src_,
            "-c:v","libx264","-preset","veryfast","-crf","16",
            "-pix_fmt","yuv420p","-r","30000/1001","-an","-y",dst_],
            stdin=subprocess.DEVNULL)
    seg_dir = norm

    with open(listfile, "w") as fh:
        for n in ids:
            fh.write(f"file '{os.path.join(seg_dir, f's{n}.mp4')}'\n")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    subprocess.run([FFMPEG,"-nostdin","-v","error","-f","concat","-safe","0",
        "-i",listfile,"-c:v","libx264","-preset","slow","-crf","20",
        "-pix_fmt","yuv420p","-profile:v","high","-level","4.1",
        "-maxrate","12M","-bufsize","16M","-movflags","+faststart",
        "-r","30000/1001","-an","-y",a.out], stdin=subprocess.DEVNULL)
    print(f"master: {a.out}  ({duration(a.out):.2f}s)")

    if a.stage_remotion:
        pub = os.path.join(REMOTION, "public")
        os.makedirs(pub, exist_ok=True)
        staged = os.path.join(pub, "reel.mp4")
        subprocess.run([FFMPEG,"-nostdin","-v","error","-i",a.out,"-r","30",
            "-c:v","libx264","-preset","medium","-crf","18",
            "-pix_fmt","yuv420p","-an","-y",staged], stdin=subprocess.DEVNULL)
        r = subprocess.run([FFPROBE,"-v","error","-select_streams","v:0",
            "-count_frames","-show_entries","stream=nb_read_frames",
            "-of","default=nw=1:nk=1",staged], capture_output=True, text=True,
            stdin=subprocess.DEVNULL)
        frames = r.stdout.strip().splitlines()
        print(f"staged: public/reel.mp4  ({frames[0] if frames else '?'} frames @30fps)")
        print(f"        set durationInFrames to this number in src/Root.tsx")
        if a.music:
            shutil.copy(a.music, os.path.join(pub, "music.mp3"))
            print(f"staged: public/music.mp3")

if __name__ == "__main__": main()
