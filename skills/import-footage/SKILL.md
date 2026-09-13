---
name: import-footage
description: Import, organise and triage camera footage from a memory card or folder. Sorts media into date folders by capture time, removes proxy files, tags true H/V orientation, and builds contact sheets so you can see what you shot. Use when the user says they've plugged in a camera, copied footage off a card, wants to organise video/photos, asks "what's on this card", or before making any reel or edit from a day's footage. Also triggers on Insta360, GoPro, action cam, memory card, DCIM, or "sort my videos".
---

# Import & organise footage

Turns a pile of camera files into dated, triaged folders you can actually work with.

## Scripts

All paths absolute; run them directly.

| Script | Does |
|---|---|
| `~/.claude/skills/import-footage/scripts/organize_media.py` | Sort into `YYYY-MM-DD` folders, quarantine proxies |
| `~/.claude/skills/import-footage/scripts/contact_sheet.py` | Sample frames, build contact sheets |
| `~/.claude/skills/import-footage/scripts/probe_orientation.py` | True H/V from rotation flags |

ffmpeg/ffprobe live at `$VIDEO_ENGINE_DIR/bin/` (defaults to `~/video-engine` — see the main README).

## Getting footage off the camera

**macOS blocks terminal access to removable volumes.** You will get `Operation not permitted` reading a mounted card, and the Privacy setting that fixes it only takes effect after the terminal restarts. Do not fight this.

Instead: check the card is mounted (`ls /Volumes/`, `diskutil list external`), then **ask the user to drag the files in Finder** to a folder they choose. Confirm when the copy is done.

For an Insta360 GO: the camera must be docked in its Action Pod, and USB Mode set to File Transfer / U-Disk on the Pod screen. Unplugging and replugging while powered on usually surfaces the prompt directly.

**Always ask which folder to copy into.** Never assume.

## Steps

**1. Wait for the copy to finish.** Check for zero-byte files first — `organize_media.py` does this and refuses to run if it finds any. Sorting mid-copy once moved three empty placeholders into date folders while Finder was still writing the real files.

**2. Dry run, then apply.**
```
organize_media.py "<folder>"            # shows the plan
organize_media.py "<folder>" --apply    # moves files
```
Report the per-date breakdown. Confirm the total file count matches what was there before.

**3. Proxy files.** Cameras write a low-resolution `.lrv` twin of every clip for phone preview. They are useless on a computer and are typically half the file count. The script moves them to `~/.Trash/camera-proxies` so they stay recoverable. Tell the user how much space that freed, and that emptying the Trash is what actually reclaims it.

**4. Orientation.**
```
probe_orientation.py "<folder>/<date>" [--rename]
```
Only rename if the user asks. **Never trust pixel dimensions** — cameras store portrait footage as a landscape frame plus a rotation flag, so raw width/height calls everything horizontal. Also warn that some clips lie: footage shot sideways with no flag set still reports H, so the contact sheet is the real check.

**5. Contact sheets.**
```
contact_sheet.py "<folder>/<date>" --out <sheets-dir> --per-clip 4
```
Then **actually look at them** with the Read tool. Report what's in each clip: who's in it, what's happening, whether it's usable. Flag clips with nothing identifiable — pocket recordings, fingers over the lens, black frames — and offer to remove them.

For a large day, spawn the `footage-scout` agent to review the sheets and return a written inventory, rather than loading dozens of images into the main context.

## Deleting

Never delete outright. Move to a named folder inside `~/.Trash` so it stays recoverable, tell the user where it went, and say that emptying the Trash is what frees the space.

**Never delete from the camera card.** Originals stay there until the user has watched the copies and confirmed. Cards are usually NTFS, which macOS can read but not write — format in-camera, never from the Mac.

## Reporting

Give a table: date, file count, video/photo split, total size. State plainly whether every file is accounted for. If anything is missing or unreadable, say so — do not round it away.
