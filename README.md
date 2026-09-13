# reel-pipeline

I built this to edit one specific video: a 60-second reel of a day out with
friends, ending on my kids waving at me through the window when I got home.
It's Claude Code skills and subagents, not a demo — I use it on real footage
of my own kids, which is exactly why it's built the way it is.

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

Every "AI video editor" example I found blurs faces by how big they are in
frame. That's backwards for family footage: a toddler close to the camera is
bigger than an adult standing further back. Get that wrong once and either a
kid's face goes public or every adult ends up pixelated by mistake.

So this pipeline tracks people, not sizes, and it asks about the story
before it cuts a single frame instead of guessing. Getting either of those
wrong isn't a bug you patch afterward - an unblurred child's face or a
published wrong cut is already out.

## What to expect

This isn't a "drop in footage, walk away" tool. It's a workflow you run
inside a Claude Code session, and it stops to check in with you on purpose:

- Roughly an hour end to end for a 60-90 second reel, most of it spent
  waiting on face tracking and rendering rather than doing active work.
- It asks before touching anything: what happened, what the reel should say,
  format, length, caption style, music direction. Then it asks again once
  you've seen the footage, about must-include shots and how any kids in
  frame should appear.
- It shows you things instead of just telling you: contact sheets before
  cutting, a face-label gallery before blurring, caption style samples
  rendered on your actual frames, a finished render to review.
- You end up with an MP4 in your chosen folder, plus the shot list and
  face-track files left on disk so you can check or redo any step.
- It won't post anywhere on its own, won't invent your story for you, and
  won't decide a face is safe to leave unblurred without you confirming it
  from a gallery image first.

## What's in here

`skills/import-footage/` sorts raw camera dumps into dated folders, reads
true portrait/landscape orientation from rotation flags instead of pixel
dimensions (which lie), and builds contact sheets so you can actually see
what's on the card before anything gets cut.

`skills/reel/` is the main workflow. A two-stage intake - story, format, and
length up front, then must-include shots and how kids should appear once
you've seen the footage - followed by shot listing, cutting, face tracking
and blurring, caption styling, music selection, and a final render through a
Remotion project.

`agents/face-labeler.md` looks at a gallery of tracked faces and proposes
which are children, which are adults, and which are false positives (table
tops and printed menus get picked up more often than you'd think). It's a
proposal for you to check, not a decision it makes on its own.

`agents/footage-scout.md` reads contact sheets from a day's shoot and writes
a plain-language inventory of what's in each clip, so triage doesn't mean
scrubbing through dozens of raw files by hand.

`agents/music-scout.md` searches for royalty-free music and actually reads
the licensing page and claim-risk signals for each track, rather than
trusting a "free" badge at face value.

## The non-negotiables (from `skills/reel/SKILL.md`)

1. Never skip the intake. Nothing about format, length, story, or style is
   assumed.
2. Never blur by face size. Track people, label the tracks, blur only
   labelled tracks.
3. Never assemble without looking. Sample frames from every segment with a
   person, every time.
4. Never delete outright. Everything goes to a named folder in `~/.Trash`.
5. `-nostdin` on every ffmpeg call. A loop feeding ffmpeg over stdin can
   silently eat lines meant for the shell - it cost 11 of 23 segments once,
   and that's not a mistake worth repeating.

## Setup

These are [Claude Code](https://claude.com/claude-code) skills and
subagents.

**1. Install the skills and agents.**
```bash
cp -r skills/reel skills/import-footage ~/.claude/skills/
cp agents/*.md ~/.claude/agents/
```

**2. Set up a `video-engine` directory.** This is your own local working
area for binaries and the render pipeline - this repo doesn't ship it for
you. It needs:
- `bin/ffmpeg` and `bin/ffprobe` (static builds are fine)
- `facetools/.venv/`, a Python virtualenv with a face-detection model. The
  scripts expect [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)
  at `facetools/yunet.onnx`
- `remotion-app/`, a [Remotion](https://www.remotion.dev/) project for final
  rendering and caption overlays

**3. Point the scripts at it:**
```bash
export VIDEO_ENGINE_DIR=/path/to/your/video-engine
```

**4. Use it.** Inside a Claude Code session, in the folder your footage
lives in, try:
```
"I just imported footage from today, let's organize it"
```
That runs `/import-footage` - sorts into dated folders, checks true
orientation, builds contact sheets for you to review. Then:
```
"Let's make a reel from this"
```
starts `/reel`. It asks its intake questions first - don't skip past these
even if you're in a hurry, they're the whole point - then shows you the
footage and a shot list to approve, hands tracked faces to `face-labeler`,
offers caption style samples rendered on your real frames, and finishes with
`music-scout` proposing licence-checked tracks before the final render.

## What this deliberately doesn't do

No auto-posting. No fully-automated face blurring without you confirming it
first. No assumed creative direction. Every step that's hard to take back -
deleting source footage, deciding whose face is blurred, picking music with
murky licensing - has a human checkpoint built into the workflow itself, not
bolted on afterward.

## License

MIT - see [LICENSE](./LICENSE).
