# Shot list format

## What the user approves

A table, one row per shot, with a reason for each pick. The reason is what makes
the list reviewable — without it they can only judge the timings.

| # | Source | In–Out | Len | Why this shot |
|---|---|---|---|---|
| 1 | `V_004` | 15.0–17.5 | 2.5s | **Hook.** Her biggest smile, kid visible behind |
| 2 | `V_003` | 4.0–7.0 | 3.0s | Storm cloud over the intersection |

Total must hit the target length exactly. State it.

## What the scripts consume

`shots.txt` — id, source filename, start seconds, duration seconds:

```
01 V_VID_20260904_173015_004.mp4 15.0 2.5
02 V_VID_20260904_172721_003.mp4 4.0 3.0
```

Ids are strings and need not be contiguous — dropping a shot later is just
deleting its line. Keep the remaining ids stable so segments don't have to be
re-cut.

## Pacing

- Punchy: ~2.7s average. Good with music carrying the energy.
- Unhurried: ~3.75s average. Better under a voiceover.
- Shot count ≈ length ÷ average.

Vary within the act — a 1.5s beat between two 3s shots creates rhythm. Do not
cut everything to the same length.

## Structure

Chronological acts, following the day. Open on a face if one exists; scenery
opens lose viewers in the first second. Cluster the emotional payload before the
final pull-back. End on something quiet — an empty road, a landscape — and let
the last second run caption-free so the image lands alone.

## Removing a shot later

Delete its line from `shots.txt`, then redistribute its seconds across the
remaining shots *within the same act*. That keeps the total exactly on target
and — crucially — keeps every downstream caption timing valid, so only the
affected act needs rechecking.
