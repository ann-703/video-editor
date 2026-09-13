#!/usr/bin/env python3
"""Blur only the named tracks. Everyone else stays sharp.

  blur_tracks.py --segments <dir> --tracks tracks.json --labels labels.json
                 --out <blurred-dir>

labels.json maps segment id -> list of track indices to blur:
    {"01":[0], "09":[0,2], "16":[0], "20":[]}

Blur strength is deliberately heavy. A first attempt used a weak blur on a
tight box and left a child recognisable - the box covered her eyes and nothing
else. Cover the whole head (GROW) and pixelate hard.

Gaps inside a track are interpolated and the ends are held, so a face cannot
flash unblurred for the frames where detection dropped.
"""
import os, sys, json, argparse
import cv2, numpy as np

GROW = 0.62   # expand box to cover the whole head, not just the face
HOLD = 8      # frames to keep blurring past a track's first/last detection

def build(track, nframes):
    kf = sorted(int(k) for k in track["boxes"])
    if not kf: return {}
    out = {}
    for a, b in zip(kf, kf[1:]):
        ba, bb = track["boxes"][str(a)], track["boxes"][str(b)]
        for f in range(a, b):
            u = (f - a) / max(1, b - a)
            out[f] = [ba[i] + (bb[i] - ba[i]) * u for i in range(4)]
    out[kf[-1]] = track["boxes"][str(kf[-1])][:4]
    for f in range(max(0, kf[0]-HOLD), kf[0]):  out[f] = track["boxes"][str(kf[0])][:4]
    for f in range(kf[-1]+1, min(nframes, kf[-1]+HOLD+1)):
        out[f] = track["boxes"][str(kf[-1])][:4]
    return out

def blur_region(img, x, y, w, h):
    H, W = img.shape[:2]
    x, y, w, h = int(x), int(y), int(w), int(h)
    gx, gy = int(w*GROW), int(h*GROW)
    x0, y0 = max(0, x-gx), max(0, y-gy)
    x1, y1 = min(W, x+w+gx), min(H, y+h+gy)
    if x1-x0 < 8 or y1-y0 < 8: return
    roi = img[y0:y1, x0:x1]
    k = max(41, (int(max(x1-x0, y1-y0)/1.5) | 1))
    blurred = cv2.GaussianBlur(roi, (k, k), 0)
    small = cv2.resize(roi, (max(1,(x1-x0)//28), max(1,(y1-y0)//28)),
                       interpolation=cv2.INTER_LINEAR)
    pix = cv2.resize(small, (x1-x0, y1-y0), interpolation=cv2.INTER_NEAREST)
    mixed = cv2.addWeighted(blurred, 0.35, pix, 0.65, 0)
    mask = np.zeros(roi.shape[:2], np.uint8)
    cv2.ellipse(mask, ((x1-x0)//2, (y1-y0)//2), ((x1-x0)//2, (y1-y0)//2),
                0, 0, 360, 255, -1)
    mask = cv2.GaussianBlur(mask, (31,31), 0).astype(np.float32)/255.0
    m3 = cv2.merge([mask]*3)
    img[y0:y1, x0:x1] = (mixed*m3 + roi*(1-m3)).astype(np.uint8)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segments", required=True); ap.add_argument("--tracks", required=True)
    ap.add_argument("--labels", required=True);   ap.add_argument("--out", required=True)
    a = ap.parse_args()

    tracks = json.load(open(a.tracks))
    labels = json.load(open(a.labels))
    os.makedirs(a.out, exist_ok=True)

    for name in sorted(tracks):
        src = os.path.join(a.segments, f"s{name}.mp4")
        if not os.path.exists(src): continue
        want = labels.get(name, [])
        cap = cv2.VideoCapture(src)
        fps = cap.get(cv2.CAP_PROP_FPS)
        W, H = int(cap.get(3)), int(cap.get(4))
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        per = [build(tracks[name][i], n) for i in want if i < len(tracks[name])]
        vw = cv2.VideoWriter(os.path.join(a.out, f"s{name}.mp4"),
                             cv2.VideoWriter_fourcc(*'mp4v'), fps, (W, H))
        fi, ops = 0, 0
        while True:
            ok, img = cap.read()
            if not ok: break
            for p in per:
                if fi in p:
                    blur_region(img, *p[fi]); ops += 1
            vw.write(img); fi += 1
        cap.release(); vw.release()
        print(f"s{name}: {fi} frames, blur tracks={want}, {ops} op(s)")

    print("\nNow LOOK at the result before assembling. Sample frames from every")
    print("segment that contains a person. Detection is good, not perfect.")

if __name__ == "__main__": main()
