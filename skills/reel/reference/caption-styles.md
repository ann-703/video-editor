# Caption styles

Four looks that have been rendered and reviewed on real footage. Always render
the candidates on the user's *own frames* and let them choose from pictures —
choosing from descriptions produces the wrong answer.

Position all of them at `top: 62%` on a 1080x1920 frame. That sits in the lower
third but clear of Instagram's own interface. Do **not** use percentage padding
to position vertically: CSS resolves percentage padding against the container's
*width*, so on a 9:16 frame it lands far too high.

---

## Frosted card  *(chosen for the 2026-09-04 reel)*
White text on a blurred glass panel. Modern, always legible regardless of
background, slightly "app-like".

```css
background: rgba(255,255,255,0.16);
backdrop-filter: blur(24px) saturate(1.35);
border: 1.5px solid rgba(255,255,255,0.38);
border-radius: 34px;
padding: 30px 46px;
box-shadow: 0 18px 60px rgba(0,0,0,0.34);
/* text */
font-family: "Avenir Next", "Helvetica Neue", sans-serif;
font-size: 60px;  /* 68px for opening and closing cards */
font-weight: 600; letter-spacing: -0.012em; line-height: 1.24;
color: white; text-shadow: 0 2px 12px rgba(0,0,0,0.42);
```

## Bold uppercase
Reels-native, maximum impact at thumbnail size. Loud, and bulky on long lines.
Note `WebkitTextStroke` renders weakly in Remotion's browser — if a heavy
outline is wanted, layer a duplicate text node behind instead.

```css
font-family: "Helvetica Neue", Impact, sans-serif;
font-size: 80px; font-weight: 900; text-transform: uppercase;
letter-spacing: -0.015em; line-height: 1.06; color: white;
text-shadow: 0 6px 22px rgba(0,0,0,0.5);
```

## Editorial serif
Elegant, considered. Thin, so it fades over bright sky and pale road, and its
slow reflective feel fights an upbeat track. Pair with a hairline rule above.

```css
font-family: Didot, "Playfair Display", Georgia, serif;
font-size: 68px; font-weight: 400; letter-spacing: 0.05em; line-height: 1.32;
color: white; text-shadow: 0 2px 20px rgba(0,0,0,0.6);
```

## Highlight blocks
Dark text on warm cream blocks. Graphic and tasteful at once, holds up over any
background. Use `box-decoration-break: clone` so multi-line text gets one block
per line.

```css
font-family: "Avenir Next", "Helvetica Neue", sans-serif;
font-size: 66px; font-weight: 800; letter-spacing: -0.02em; line-height: 1.5;
color: #1a1109; background: #F7E7C8;
padding: 10px 22px; border-radius: 12px;
box-decoration-break: clone; -webkit-box-decoration-break: clone;
```

---

## Motion
Keep it quiet. Fade in and out over ~0.3s, with a small rise (24px) and a
slight scale (0.965 → 1). Anything more reads as templated.

## Scrim
White text over bright road and sky needs help. A gentle gradient across the
lower third does it without darkening the picture:

```css
background: linear-gradient(to bottom,
  rgba(0,0,0,0) 52%, rgba(0,0,0,0.20) 76%, rgba(0,0,0,0.08) 100%);
```
Lighten this when the caption style carries its own background (frosted, blocks).
