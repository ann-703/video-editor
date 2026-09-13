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
subagents. To use them:

1. Copy `skills/reel` and `skills/import-footage` into `~/.claude/skills/`,
   and the three files in `agents/` into `~/.claude/agents/`.
2. Set up a **video-engine** directory with `ffmpeg`/`ffprobe` binaries, a
   Python virtualenv with a face-detection model (the scripts expect
   [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)
   at `facetools/yunet.onnx`), and a [Remotion](https://www.remotion.dev/)
   project for final rendering and captions.
3. Point the scripts at it:
   ```bash
   export VIDEO_ENGINE_DIR=/path/to/your/video-engine
   ```
4. In Claude Code, say something like *"I just imported footage, let's make
   a reel"* — the `/reel` skill will walk through the rest.

## What this deliberately doesn't do

No auto-posting, no fully-automated face blurring without a verification
step, no assumed creative direction. Every risky or hard-to-reverse step
(deleting source footage, publishing a face-blur decision, picking music
with unclear licensing) has a human checkpoint built into the workflow
itself, not bolted on as an afterthought.

## License

MIT — see [LICENSE](./LICENSE).
