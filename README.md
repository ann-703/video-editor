# reel-pipeline

Claude Code skills and subagents for turning a folder of raw phone/camera
footage into a finished, captioned, face-safe social reel — built and used
for real family video edits, not a demo.

Two skills and three subagents, chained together:

```
footage folder
   -> /import-footage   (organize, orientation, contact sheets)
   -> footage-scout      (reviews contact sheets, writes an inventory)
   -> /reel              (intake, shot list, cut, face tracking, captions, music, render)
        -> face-labeler   (proposes which tracked faces are children vs adults)
        -> music-scout    (finds licence-clean, claim-safe background music)
```

## Why this exists

Most "AI video editor" demos skip the two parts that actually matter for a
parent posting real footage of real kids: **never guessing which faces to
blur**, and **never assuming the story, format, or length** before asking.
This pipeline is opinionated about both, because getting either wrong is a
one-way door — an unblurred child's face or a published wrong cut isn't a bug
you patch after the fact.

## What to expect

This is not a "drop in footage, walk away" tool — it's an interactive
workflow you run inside a Claude Code session, with you in the loop at
several points on purpose:

- **Time:** roughly an hour end-to-end for a ~60-90 second reel, most of it
  waiting on face-tracking/rendering rather than active work from you.
- **You'll be asked questions before anything is touched** — what happened,
  what the reel should say, format, length, caption style, music direction —
  and again after you've seen the footage, for must-include shots and how
  any children in frame should appear.
- **You'll be shown things, not just told things** — contact sheets before
  cutting, a face-label gallery before blurring, caption style samples
  rendered on your actual frames before they're applied everywhere, a
  render to review before it's called done.
- **Output:** an MP4 in your chosen output folder, captioned and rendered at
  1080x1920 (or your chosen format), plus the intermediate shot list and
  face-track files left on disk so you can see or redo any step.
- **What it won't do on its own:** post anywhere, pick your story for you, or
  decide a face is safe to leave unblurred without you confirming it from a
  gallery image.

## What's in here

- **`skills/import-footage/`** — sorts raw camera dumps into dated folders,
  detects true portrait/landscape orientation from rotation flags (not pixel
  dimensions, which lie), and builds contact sheets so a human can actually
  see what's on the card before anything gets cut.
- **`skills/reel/`** — the main workflow: a structured two-stage intake
  (story/format/length before anything is touched, then must-include shots
  and how children should appear once the footage has been seen), shot
  listing, cutting, face tracking + blurring, caption styling, music
  selection, and final render via a Remotion project.
- **`agents/face-labeler.md`** — reviews a gallery of tracked faces and
  proposes child/adult/false-positive labels. Its output is always a
  proposal for human verification, never an auto-applied decision.
- **`agents/footage-scout.md`** — reads contact sheets from a day's shoot and
  writes a plain-language inventory of what's in every clip, so triage
  doesn't mean scrubbing through dozens of raw files by hand.
- **`agents/music-scout.md`** — searches for royalty-free music, checks
  licence terms and Content-ID claim risk on the actual source page (not just
  "says free" badges), and rates claim risk before anything gets downloaded.

## The non-negotiables (from `skills/reel/SKILL.md`)

1. Never skip the intake — nothing about format, length, story or style is
   assumed.
2. Never blur by face size — track people, label the tracks, blur only
   labelled tracks. Face size does not indicate age.
3. Never assemble without looking — sample frames from every segment with a
   person, every time.
4. Never delete outright — everything goes to a named folder in `~/.Trash`.
5. `-nostdin` on every ffmpeg call — a loop feeding ffmpeg over stdin can
   silently eat lines meant for the shell, which once cost 11 of 23 segments
   in a real edit.

## Setup

These are [Claude Code](https://claude.com/claude-code) skills and
subagents.

**1. Install the skills and agents.**
```bash
cp -r skills/reel skills/import-footage ~/.claude/skills/
cp agents/*.md ~/.claude/agents/
```

**2. Set up a `video-engine` directory** — this project's local working area
for binaries and the render pipeline, not something this repo ships for you:
- `bin/ffmpeg` and `bin/ffprobe` (static builds are fine)
- `facetools/.venv/` — a Python virtualenv with a face-detection model. The
  scripts expect [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)
  at `facetools/yunet.onnx`
- `remotion-app/` — a [Remotion](https://www.remotion.dev/) project for
  final rendering and caption overlays

**3. Point the scripts at it:**
```bash
export VIDEO_ENGINE_DIR=/path/to/your/video-engine
```

**4. Use it.** Inside a Claude Code session, in the folder your footage
lives in:
```
"I just imported footage from today, let's organize it"
```
walks through `/import-footage` — sorts into dated folders, checks true
orientation, builds contact sheets for you to review. Then:
```
"Let's make a reel from this"
```
starts `/reel` — it will ask its intake questions first (do not skip past
these, even if you're in a hurry), show you the footage and a shot list to
approve, hand off to `face-labeler` for any tracked faces, offer caption
style samples rendered on your real frames, and end with `music-scout`
proposing licence-checked tracks before the final render.

## What this deliberately doesn't do

No auto-posting, no fully-automated face blurring without a verification
step, no assumed creative direction. Every risky or hard-to-reverse step
(deleting source footage, publishing a face-blur decision, picking music
with unclear licensing) has a human checkpoint built into the workflow
itself, not bolted on as an afterthought.

## License

MIT — see [LICENSE](./LICENSE).
