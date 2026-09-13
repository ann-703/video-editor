#!/usr/bin/env python3
"""Detect faces, group them into per-person tracks, and build a label gallery.

  track_faces.py --segments <dir> --out tracks.json --gallery gallery.jpg

Why tracks and not per-frame detections: you cannot tell a child from an adult
by face size. People sit at different distances, so a size threshold blurs the
wrong faces AND misses the right ones. Instead we build one track per person,
a human labels each track once from the gallery, and only those tracks blur.

Two association rules exist because breaking them let a child's face through:
  1. Tight distance tolerance. Faces do not teleport between frames.
  2. One detection per track per frame, assigned globally by distance.
     A loose tolerance once let a toddler's face be absorbed into the adult
     track carrying him - he was detected at 0.93 confidence and still went
     unblurred, because his detections were being consumed by another track.
Also gate on size ratio: a toddler's face is not an adult's face.
"""
import os, sys, json, glob, argparse
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import YUNET

MIN_PX      = 20     # ignore specks
MAX_AREA_FR = 0.25   # a "face" filling a quarter of frame is a false positive
GAP         = 10     # frames a track may vanish for and still continue
TOL_SCALE   = 0.8    # distance tolerance = max(w,h)*TOL_SCALE + TOL_BASE
TOL_BASE    = 25
SIZE_LO, SIZE_HI = 0.45, 2.2   # allowed area ratio when matching

def track_one(path, det):
    cap = cv2.VideoCapture(path); tracks=[]; fi=0
    while True:
        ok, img = cap.read()
        if not ok: break
        h, w = img.shape[:2]; det.setInputSize((w, h))
        _, fs = det.detect(img)
        dets=[]
        if fs is not None:
            for f in fs:
                x,y,fw,fh = [int(v) for v in f[:4]]
                if fw < MIN_PX or fh < MIN_PX: continue
                if fw*fh > MAX_AREA_FR*w*h: continue
                dets.append((x,y,fw,fh,float(f[-1])))
        pairs=[]
        for di,d in enumerate(dets):
            cx,cy = d[0]+d[2]/2, d[1]+d[3]/2
            for ti,t in enumerate(tracks):
                if fi - t["last"] > GAP: continue
                dist = ((cx-t["c"][0])**2 + (cy-t["c"][1])**2) ** 0.5
                tol  = max(d[2],d[3])*TOL_SCALE + TOL_BASE
                ratio = (d[2]*d[3]) / max(1, t["area"])
                if dist < tol and SIZE_LO < ratio < SIZE_HI:
                    pairs.append((dist, di, ti))
        pairs.sort()
        ud, ut = set(), set()
        for dist, di, ti in pairs:
            if di in ud or ti in ut: continue
            d = dets[di]; t = tracks[ti]
            t["boxes"][fi]=d; t["last"]=fi
            t["c"]=(d[0]+d[2]/2, d[1]+d[3]/2); t["area"]=d[2]*d[3]
            ud.add(di); ut.add(ti)
        for di,d in enumerate(dets):
            if di in ud: continue
            tracks.append({"boxes":{fi:d}, "last":fi,
                           "c":(d[0]+d[2]/2, d[1]+d[3]/2), "area":d[2]*d[3]})
        fi += 1
    cap.release()
    tracks=[t for t in tracks if len(t["boxes"])>=4]
    tracks.sort(key=lambda t: -len(t["boxes"]))
    return tracks, fi

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segments", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--gallery", required=True)
    ap.add_argument("--threshold", type=float, default=0.35)
    a = ap.parse_args()

    det = cv2.FaceDetectorYN.create(YUNET, "", (320,320), a.threshold, 0.3, 5000)
    segs = sorted(glob.glob(os.path.join(a.segments, "s*.mp4")))
    out, tiles = {}, []

    for p in segs:
        name = os.path.basename(p)[1:-4]
        tr, nf = track_one(p, det)
        out[name] = [{"boxes":{str(k):list(v) for k,v in t["boxes"].items()}} for t in tr]
        print(f"s{name}: {nf}f, {len(tr)} track(s), lengths={[len(t['boxes']) for t in tr]}")
        cap = cv2.VideoCapture(p)
        for ti,t in enumerate(tr):
            fr = sorted(t["boxes"]); pick = fr[len(fr)//2]
            cap.set(cv2.CAP_PROP_POS_FRAMES, pick); ok,img = cap.read()
            if not ok: continue
            x,y,w,h,_ = t["boxes"][pick]
            H,W = img.shape[:2]; pad = int(max(w,h)*0.4)
            x0,y0 = max(0,x-pad), max(0,y-pad)
            x1,y1 = min(W,x+w+pad), min(H,y+h+pad)
            crop = img[y0:y1, x0:x1]
            if crop.size == 0: continue
            ch,cw = crop.shape[:2]; s = 165/max(ch,1)
            crop = cv2.resize(crop, (max(1,int(cw*s)), 165))
            canv = np.full((200,175,3), 35, np.uint8)
            cw2 = min(crop.shape[1], 175); canv[0:165, 0:cw2] = crop[:, :cw2]
            cv2.putText(canv, f"s{name}.t{ti}", (4,185),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
            cv2.putText(canv, f"n={len(fr)}", (118,185),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150,220,150), 1)
            tiles.append(canv)
        cap.release()

    json.dump(out, open(a.out, "w"))
    if tiles:
        cols = 11
        rows = [np.hstack(tiles[i:i+cols] +
                [np.full((200,175,3),35,np.uint8)]*(cols-len(tiles[i:i+cols])))
                for i in range(0, len(tiles), cols)]
        cv2.imwrite(a.gallery, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"\n{len(tiles)} track(s) -> {a.gallery}")
    print("Label each track, then pass the mapping to blur_tracks.py")

if __name__ == "__main__": main()
