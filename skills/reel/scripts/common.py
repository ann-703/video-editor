"""Shared paths and helpers for the reel pipeline."""
import os, subprocess, sys

# Point this at your own video-engine checkout, e.g. via:
#   export VIDEO_ENGINE_DIR=/path/to/video-engine
VIDEO_ENGINE = os.environ.get(
    "VIDEO_ENGINE_DIR",
    os.path.expanduser("~/video-engine"),
)
FFMPEG  = f"{VIDEO_ENGINE}/bin/ffmpeg"
FFPROBE = f"{VIDEO_ENGINE}/bin/ffprobe"
FACETOOLS = f"{VIDEO_ENGINE}/facetools"
FACE_PY   = f"{FACETOOLS}/.venv/bin/python"
YUNET     = f"{FACETOOLS}/yunet.onnx"
REMOTION  = f"{VIDEO_ENGINE}/remotion-app"

def run(args, **kw):
    """Run a command with stdin closed.

    ffmpeg reads stdin and will silently eat lines from any loop that feeds it,
    which once cost us 11 of 23 segments. Never remove stdin=DEVNULL.
    """
    kw.setdefault("stdin", subprocess.DEVNULL)
    kw.setdefault("check", False)
    return subprocess.run(args, **kw)

def ffmpeg(*args):
    return run([FFMPEG, "-nostdin", "-v", "error", *[str(a) for a in args]])

def probe(path, entries):
    r = run([FFPROBE, "-v", "error", "-show_entries", entries,
             "-of", "default=nw=1:nk=1", str(path)],
            capture_output=True, text=True)
    return r.stdout.strip()

def duration(path):
    try:    return float(probe(path, "format=duration").splitlines()[0])
    except Exception: return 0.0

def orientation(path):
    """True display orientation: H, V or SQUARE.

    Cameras store portrait footage as landscape plus a rotation flag, so raw
    pixel dimensions will call every clip horizontal. Read the flag.
    """
    w = probe(path, "stream=width").splitlines()
    h = probe(path, "stream=height").splitlines()
    if not w or not h: return "UNKNOWN"
    w, h = int(w[0]), int(h[0])
    rot = probe(path, "stream_tags=rotate").splitlines()
    r = abs(int(rot[0])) if rot and rot[0].lstrip("-").isdigit() else 0
    if r in (90, 270): w, h = h, w
    return "H" if w > h else ("V" if h > w else "SQUARE")

def require_tools():
    missing = [p for p in (FFMPEG, FFPROBE) if not os.path.exists(p)]
    if missing:
        sys.exit(f"Missing required tool(s): {missing}")
