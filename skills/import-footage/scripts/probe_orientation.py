#!/usr/bin/env python3
"""Report true display orientation, and optionally prefix filenames H_ / V_.

  probe_orientation.py <folder> [--rename]

Cameras store portrait footage as a landscape frame plus a rotation flag.
Reading pixel dimensions alone labels every clip horizontal - always read
the flag. Note that some clips lie: content shot sideways with no flag set
will still report H, so a visual check on the contact sheet is worthwhile.
"""
import os, sys, glob, argparse, subprocess
# Point this at your own video-engine checkout, e.g. via:
#   export VIDEO_ENGINE_DIR=/path/to/video-engine
FF = os.path.join(os.environ.get("VIDEO_ENGINE_DIR", os.path.expanduser("~/video-engine")), "bin")

def q(p, entries):
    r = subprocess.run([f"{FF}/ffprobe","-v","error","-show_entries",entries,
                        "-of","default=nw=1:nk=1",p],
                       capture_output=True,text=True,stdin=subprocess.DEVNULL)
    return r.stdout.strip().splitlines()

def orient(p):
    w, h = q(p,"stream=width"), q(p,"stream=height")
    if not w or not h: return None, None, None, "UNKNOWN"
    w, h = int(w[0]), int(h[0])
    rot = q(p,"stream_tags=rotate")
    r = abs(int(rot[0])) if rot and rot[0].lstrip("-").isdigit() else 0
    dw, dh = (h, w) if r in (90,270) else (w, h)
    return w, h, r, ("H" if dw>dh else "V" if dh>dw else "SQUARE")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder"); ap.add_argument("--rename", action="store_true")
    a = ap.parse_args()
    clips = sorted(glob.glob(os.path.join(a.folder,"*.mp4")) +
                   glob.glob(os.path.join(a.folder,"*.MP4")) +
                   glob.glob(os.path.join(a.folder,"*.mov")))
    if not clips: sys.exit("No clips found.")
    print(f"{'FILE':<44}{'W':>6}{'H':>6}{'ROT':>5}  ORIENT")
    counts, renamed = {"H":0,"V":0,"SQUARE":0,"UNKNOWN":0}, 0
    for c in clips:
        b = os.path.basename(c)
        w,h,r,o = orient(c); counts[o] = counts.get(o,0)+1
        print(f"{b[:43]:<44}{w or '?':>6}{h or '?':>6}{r if r is not None else '?':>5}  {o}")
        if a.rename and o in ("H","V") and not b.startswith(("H_","V_")):
            dst = os.path.join(os.path.dirname(c), f"{o}_{b}")
            if not os.path.exists(dst): os.rename(c, dst); renamed += 1
    print(f"\nH={counts['H']}  V={counts['V']}  square={counts['SQUARE']}")
    if a.rename: print(f"Renamed {renamed} file(s).")
    else: print("Add --rename to prefix filenames with H_ / V_.")

if __name__ == "__main__": main()
