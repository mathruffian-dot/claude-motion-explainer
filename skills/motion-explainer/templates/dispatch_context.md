# Dispatch context (shared by every frame worker)

> Template — copy to `<project>/.hyperframes/frame-packets/_dispatch_context.md` and fill every `<…>`.
> Each worker reads, in order: `_role.md` → this file → its own packet → `frame.md` → shared assets.

- `PROJECT_DIR`: `<absolute project path>`
- Canvas: **<1920×1080>** (<16:9>). Display sizes in `cqw` per `frame.md`.
- Confirmed sketch on disk: **<no / yes>**.
- Captions: **enabled** — a root caption track owns the bottom 17%. Keep every element at **y ≤ <896> px** (0.83 × height). Never render the narration sentence as on-screen text.
- Read `frame.md` (palette, type, and its **Traditional Chinese override** section — follow it exactly).
- Write ONLY your own `compositions/frames/NN-*.html` (the `src` in your packet). Do not edit STORYBOARD.md, frame.md, index.html, or other frames. Do not render.

## Video direction (paste STORYBOARD.md's `## Video direction` block here verbatim)

<…>

## Shared assets (mandatory where they appear)

`<assets/shared/<name>.svg>` is the ONE `<car / character / instrument>`. Copy its paths **verbatim** into an inline `<svg>` (inline so you can animate parts); scale the whole group uniformly — never redraw or reshape it. Part ids and fixed coordinates: `<list ids, anchor points, which parts appear in which frames>`. (Example: `templates/shared-asset.example.svg`.)

## Continuity between adjacent frames

`<e.g. "frame 08 starts on frame 07's final g-scale: 0 g at x=160, 400 px per g, axis top y=575, cells 34×56 on a 40 px pitch">` — the orchestrator relays exact geometry from whichever worker finishes first.

## Timing and motion rules (from `motion-design` — these numbers are the defaults)

- Register one paused GSAP timeline on `window.__timelines["<your composition id>"]`; every tween has an explicit position taken from your shot list's Scene start times (frame-relative seconds). Prefer `fromTo()`.
- Style the composition root with **`#root` only** — never `#root[data-composition-id="…"]` (the attribute no longer matches after mounting; every variable on it silently disappears).
- Eases: CustomEase (`gsap@3.14.2/dist/CustomEase.min.js`) `enter` = `0.16,1,0.3,1`, `exit` = `0.6,0,0.9,0.35`, `move` = `0.65,0,0.35,1`; built-in fallbacks `expo.out` / `power3.in` / `power2.inOut` / `back.out(1.4)`; continuous rotation/flow `none`.
- Staggers: Chinese per-character ~0.045 s, per phrase ~0.09 s, list items ~0.2 s, dots/arrows ~0.06 s.
- Mask reveal ≈ 0.8 s: `overflow:hidden` wrapper with `data-layout-allow-overflow`, inner starts at **`yPercent: 135, rotation: 3`** (100 leaks a glyph corner when rotated). CJK line boxes `line-height` 1.15–1.25.
- A bar that grows alongside a counter: place each cell at the **inverse of the counter's ease** (power2.out → `1 - Math.sqrt(1 - y)`), never a stagger with its own ease.
- Exits ≈ half the entrance. Reading holds: a short phrase holds ≥ 1 s after it settles.
- Deterministic only: no `Math.random()` (seeded function instead), no `Date`, no timers, no CSS transitions/keyframes. Continuous motion = a linear tween across the frame on the same timeline.
- Fonts: only files in `assets/fonts/` (`@font-face` for each family you name; no Google Fonts `@import`). Latin face first, CJK face second in every stack.
- Colors: author in the `frame.md` palette; the orchestrator re-colors to the user's three-color theme afterwards. Give the elements that carry the answer / key number / chapter card one of the classes `accent-block` (accent background + bg text), `accent-fill` (accent background), `accent-text` (accent text) or `accent-stroke` (accent SVG line) — still drawn in the source palette; `theme.py` turns them into the accent.
- Bottom hairline at **y = <880> px**, top at **<3cqw>** — same in every frame. Name them `<frame-id>-hair-top` / `<frame-id>-hair-bottom` (id or class) and position them with `top:` in a rule selected by that name, so `unify_frames.py` can align them.
