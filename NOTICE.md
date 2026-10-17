# Third-party notices

## Adapted work (included)

- `skills/motion-design/` and `skills/review-loop/` are adapted from the `motion-design` and
  `review-loop` skills in [whaleyxbt/claude-motion](https://github.com/whaleyxbt/claude-motion)
  (MIT License, Copyright (c) 2026 whaleyxbt). The original license is kept in each folder's
  `LICENSE`. Changes: rewritten for HyperFrames instead of Remotion, Traditional Chinese
  typography, the three-color theme rule, and a new `sheet.py`; sections added in this version are
  marked 「本版新增」.

## Dependencies (not included — installed by the user)

- [HyperFrames](https://github.com/heygen-com/hyperframes) and its official skills — Apache-2.0, by HeyGen.
- [GSAP](https://gsap.com) — loaded from a CDN by each composition; see GSAP's license.
- Fonts, fetched by `scripts/fetch_fonts.sh` from the [@fontsource](https://fontsource.org) npm
  packages or the system: Newsreader, DM Mono, Hanken Grotesk, Noto Sans TC, Noto Serif TC — all
  SIL Open Font License 1.1.
- [edge-tts](https://github.com/rany2/edge-tts) — GPL-3.0 Python package that calls Microsoft's
  online text-to-speech service; check the service's terms before commercial use.
- [Breeze TTS 2](https://github.com/breezeblue-ai/breeze-tts) — inference code Apache-2.0; model
  weights and generated audio under the BreezeBlue Research and Non-Commercial License.

No product logos, photos or trademarks are included; example artwork is an invented illustration.
