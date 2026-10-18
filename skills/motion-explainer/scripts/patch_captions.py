"""Give the generated caption track a CJK face and weight.

captions.mjs regenerates compositions/captions.html on every build and only knows the preset's
Latin faces, so CJK glyphs would fall back to whatever the render machine has, and the Latin
faces it names have no @font-face (a lint error). Run after every `captions.mjs build`
(and before theme.py):

  python patch_captions.py --project <dir>

theme.json (optional): "caption": {"cjk": "NotoSansTC", "cjk_file": "NotoSansTC-VF.ttf",
                                   "latin": "Hanken Grotesk", "weight": 700}
"""
import sys
import argparse
import json
import re
from pathlib import Path
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console

MARK = "/* caption face (patch_captions.py) */"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    a = ap.parse_args()
    project = Path(a.project).resolve()
    cfg_path = project / "theme.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")).get("caption", {}) if cfg_path.exists() else {}
    cjk = cfg.get("cjk", "NotoSansTC")
    cjk_file = cfg.get("cjk_file", "NotoSansTC-VF.ttf")
    latin = cfg.get("latin", "Hanken Grotesk")
    weight = cfg.get("weight", 700)
    html_path = project / "compositions" / "captions.html"
    html = html_path.read_text(encoding="utf-8")
    if MARK in html:
        print("already patched")
        return
    fonts = project / "assets" / "fonts"
    faces = [f'@font-face {{ font-family: "{cjk}"; src: url("assets/fonts/{cjk_file}"); font-weight: 200 900; }}']
    # declare every local woff2 so all families captions.html names resolve (lint: font_family_without_font_face)
    for f in sorted(fonts.glob("*.woff2")):
        fam, _, style = f.stem.partition("-")
        fam = {"HankenGrotesk": "Hanken Grotesk", "DMMono": "DM Mono"}.get(fam, re.sub(r"(?<=[a-z])(?=[A-Z])", " ", fam))
        w = {"Regular": 400, "Medium": 500, "SemiBold": 600, "Bold": 700}.get(style, 400)
        st = "italic" if "Italic" in style else "normal"
        faces.append(f'@font-face {{ font-family: "{fam}"; src: url("assets/fonts/{f.name}") format("woff2"); font-weight: {w}; font-style: {st}; }}')
    css = (f"\n  {MARK}\n  " + "\n  ".join(faces) +
           f'\n  .caption-line {{ font-family: "{latin}", "{cjk}", sans-serif !important; font-weight: {weight} !important;'
           f" letter-spacing: 0.02em !important; line-height: 1.3 !important; }}\n")
    i = html.index("</style>")
    html_path.write_text(html[:i] + css + html[i:], encoding="utf-8")
    print("patched captions.html")


if __name__ == "__main__":
    main()
