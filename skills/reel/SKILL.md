---
name: reel
description: Build a finished social video reel from a folder of footage — story planning, shot selection, cutting, face blurring for children, captions, music and render. Use when the user wants to make a reel, an Instagram or TikTok video, a highlights video, a montage, or "turn this footage into something", or names a date folder and asks for a video. Handles vertical or square formats, caption styling, licence-cleared music, and blurring kids' faces.
---

# Make a reel

Footage folder in, finished captioned reel out. Roughly an hour with the user present for five decisions.

## Non-negotiables

1. **Never skip the intake.** Nothing about format, length, story or style is assumed.
2. **Never blur by face size.** Track people, have the tracks labelled, blur only labelled tracks.
3. **Never assemble without looking.** Sample frames from every segment containing a person, every time.
4. **Never delete outright.** Everything goes to a named folder in `~/.Trash`.
5. **`-nostdin` on every ffmpeg call.** The scripts do this; if you write an inline command, do it too.

## Scripts

| Script | Does |
|---|---|
| `~/.claude/skills/reel/scripts/cut_segments.py` | Shot list → downscaled segments |
| `~/.claude/skills/reel/scripts/track_faces.py` | Detect + track faces, build label gallery |
| `~/.claude/skills/reel/scripts/blur_tracks.py` | Blur only the labelled tracks |
| `~/.claude/skills/reel/scripts/build_master.py` | Concat, verify, stage for Remotion |
| `~/.claude/skills/import-footage/scripts/contact_sheet.py` | Contact sheets at any density |
| `~/.claude/skills/import-footage/scripts/probe_orientation.py` | True H/V orientation |

The face scripts need their own Python: `$VIDEO_ENGINE_DIR/facetools/.venv/bin/python`

Remotion project: `$VIDEO_ENGINE_DIR/remotion-app`

(`VIDEO_ENGINE_DIR` defaults to `~/video-engine` — see the main README for setup.)

Face scripts and renders take minutes. **Run them with `run_in_background: true`** and poll, or the call times out.

---

## Stage A intake — before touching anything

Ask all six together with AskUserQuestion. Do not proceed on assumptions.

1. **The story** — what happened that day, and what the reel should say about it.
2. **The title** — also seeds the opening and closing captions.
3. **Format** — vertical 9:16 (Reels/TikTok), square, or landscape.
4. **Length** — 30 / 60 / 90 seconds. Sets shot count: roughly `length ÷ 2.7s`.
5. **Caption vibe** — plain text, or stickers and graphic elements too; and whether sound effects on cuts are wanted.
6. **Music direction** — genre, energy, a reference track, or "surprise me".

## Organise and triage

If the folder isn't already in date folders, run the `import-footage` skill first.

Build contact sheets, **look at them**, and report what's in each clip. Note which clips contain children — you need this for Stage B.

## Stage B intake — after seeing the footage

Show the contact sheets, then ask:

1. **Must-include shots** — anything they specifically want in, picked from what's actually there.
2. **How children should appear** — *only ask if children are present.* Options: only from behind or in profile; faces visible but blurred; or a mix.

**This question comes before the shot list, not at the blurring step.** "Backs only" is a shot-selection rule, not a blur setting — it changes which clips are even candidates. Asking it late means rebuilding the edit.

## Shot list

Filter to the requested format. For vertical, use `probe_orientation.py` — and sanity-check against the contact sheets, because clips shot sideways with no rotation flag will report H.

Build denser filmstrips of candidate clips (`--per-clip 8` or `12`), look at them, and pick specific in/out points on real moments — a smile, a gesture, a turn — not arbitrary offsets.

Structure chronologically in acts. Open on a face if there is one: it holds the scroll better than scenery. Vary shot length for rhythm. End on something quiet.

Present as a table: shot number, source clip, in–out, duration, and *why that shot*. Total must hit the target length exactly. **Get approval before cutting.**

Write the approved list to `shots.txt`:
```
01 V_VID_20260904_173015_004.mp4 15.0 2.5
02 V_VID_20260904_172721_003.mp4 4.0 3.0
```

## Cut

```
cut_segments.py --shots shots.txt --src "<clips>" --out <segments>
```

## Faces

Only if people appear. This is the part that has gone wrong before — follow it exactly.

**1. Track.**
```
<facetools-python> track_faces.py --segments <segments> --out tracks.json --gallery gallery.jpg
```

**2. Label.** Read `gallery.jpg` and identify every track: which are children, which are adults, which are false positives (table tops, menus, hands, murals — there will be several).

Optionally have `face-labeler` propose the mapping. **Its output is a proposal, never a decision** — always verify against the gallery yourself before applying. A subagent quietly mislabelling a track is how a child's face gets published.

Write `labels.json` — only the tracks to blur:
```json
{"01":[0], "09":[0,2], "16":[0], "20":[]}
```

**3. Blur.**
```
<facetools-python> blur_tracks.py --segments <segments> --tracks tracks.json --labels labels.json --out <blurred>
```

**4. Verify — mandatory.** Build a check sheet sampling 5+ frames from every segment with a person, and look at it. Confirm two things separately: every child is covered for the *whole* shot, and no adult is blurred anywhere.

If a child is detected but not tracked, re-run `track_faces.py --threshold 0.2`. A face can be detected at high confidence and still be lost by tracking.

## Assemble

```
build_master.py --segments <blurred> --shots shots.txt --out "<...>/Reels/<name>.mp4" --stage-remotion [--music <mp3>]
```
Note the frame count it reports — that is `durationInFrames` in Remotion.

## Captions

**Agree the words before styling.** Write one card per beat, 3–5 words, roughly one per 3.5s. Draft them as a table with timecodes and let the user edit.

Then styling. See `reference/caption-styles.md` for four ready looks. Render each on the user's *actual frames* and let them choose from pictures, not descriptions.

Edit `remotion-app/src/Reel/captions.ts` (text and timings) and `CaptionCard.tsx` (look). Preview with `npm run dev` at localhost:3000, render with:
```
npx remotion render ReelWithCaptions "<out.mp4>" --codec=h264 --crf=20 --pixel-format=yuv420p
```

Keep captions clear of the top and bottom 15% where Instagram puts its own interface.

## Music

Spawn `music-scout` with the user's direction. It returns licence-verified free tracks with claim-risk ratings.

Once they pick, find the best window rather than defaulting to the start: decode to mono, compute per-second RMS, and print an energy profile. Look for a section whose shape matches the edit — a breakdown where the mood turns, a build that lands on the closing shot.

Add via Remotion `<Audio>` with `trimBefore`, a ~1.2s fade in and a ~3s fade out. Verify audio actually landed:
```
ffmpeg -hide_banner -i <out.mp4> -af volumedetect -f null -
```
Aim for mean around −12 dB, peak near −1 dB. **Do not use `-v error`** — it suppresses the very output you're checking.

Always advise a Close Friends test post before publishing.

## Hard-won gotchas

- **Face size ≠ age.** Costs two rebuilds every time it's tried.
- **Trackers merge people** if tolerance is loose. A toddler's face was absorbed into the adult carrying him and went unblurred at 0.93 confidence.
- **Weak blur leaves faces readable.** Cover the whole head, pixelate hard.
- **Rotation flags, not pixel dimensions.** And some clips lie.
- **Zero-byte files** mean a copy is still running. Check before and after.
- **ffmpeg eats stdin** in loops. `-nostdin`, always.
- **CSS percentage padding resolves against width**, not height. On 9:16 that puts captions in the wrong place — use `top:` positioning.
- **Check the Pixabay Content ID badge.** It rejected nine otherwise-perfect tracks in one search.
- **macOS blocks terminal access to removable volumes.** Copy in Finder.
