"""Re-color a built film with a three-color theme: background / main / accent.

Frames are authored in a source palette (e.g. the cobalt-grid preset: cobalt ink on cream paper).
theme.json maps every source color onto the three theme colors, like a slide template:

  paper    -> bg
  ink      -> fg   (text, line art, rules; grids keep their original alpha)
  ink-soft -> fg mixed 70% over bg
  per-frame accents ("accents" in theme.json, keyed by frame file stem):
     block -> accent background + bg text   (chapter cards, result blocks)
     fill  -> accent background             (the one bar that carries the claim)
     text  -> accent text                   (hero numbers)
     stroke -> accent line colour            (an SVG line / outline that carries the point)
  captions: the active word becomes an accent block
  font (optional, theme.json "font"): ONE face for every piece of text in every frame and the
     captions, e.g. {"family": "GenSekiGothic", "file": "GenSekiGothic2TW-B.otf", "weight": 700}
     (the file lives in assets/fonts/). Overrides whatever stacks the frame workers wrote.

The first run keeps pristine copies in .hyperframes/pre-theme/; every later run starts from those,
so the theme can be changed and re-applied any number of times. Also recolors index.html's ground.
Themed files carry a "(theme.py)" marker. A file without it was regenerated since the last run
(assemble-index, captions build, a re-made frame) and replaces its pristine copy automatically.
Hand edits to an already-themed file must also go into its .hyperframes/pre-theme/ copy.

  python theme.py --project <dir>            # apply theme.json
  python theme.py --project <dir> --restore  # back to the source palette
"""
import sys
import argparse
import json
import re
import shutil
from pathlib import Path
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console

MARK = "/* theme accents (theme.py) */"
THEMED = "(theme.py)"  # every themed file carries this; its absence marks a freshly generated source


def rgb(hex_):
    h = hex_.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    ca, cb = rgb(a), rgb(b)
    return "#" + "".join(f"{round(x * t + y * (1 - t)):02X}" for x, y in zip(ca, cb))


def recolor(text, th):
    src, fg, bg = th["source"], th["fg"], th["bg"]
    soft = mix(fg, bg, 0.7)
    fr, fgc, fb = rgb(fg)
    for h in src["ink"]:
        text = re.sub(re.escape(h), fg, text, flags=re.I)
    for h in src["paper"]:
        text = re.sub(re.escape(h), bg, text, flags=re.I)
    for h in src.get("ink_soft", []):
        text = re.sub(re.escape(h), soft, text, flags=re.I)
    r, g, b = src["ink_rgb"].split(",")
    text = re.sub(rf"rgba\(\s*{r}\s*,\s*{g}\s*,\s*{b}\s*,", f"rgba({fr}, {fgc}, {fb},", text)
    return re.sub(r"(?<![\w-])#fff(?![\w])", bg, text, flags=re.I)


def accent_css(spec, th):
    a, bg = th["accent"], th["bg"]
    rules = [MARK]
    rules += [f"{s} {{ background: {a} !important; background-color: {a} !important; color: {bg} !important; }}" for s in spec.get("block", [])]
    rules += [f"{s} {{ background: {a} !important; background-color: {a} !important; border-color: {a} !important; }}" for s in spec.get("fill", [])]
    rules += [f"{s} {{ color: {a} !important; fill: {a} !important; }}" for s in spec.get("text", [])]
    rules += [f"{s} {{ stroke: {a} !important; }}" for s in spec.get("stroke", [])]
    return "\n    " + "\n    ".join(rules) + "\n"


def caption_css(th):
    a, bg, fg = th["accent"], th["bg"], th["fg"]
    return (f"\n  {MARK}\n"
            f"  .caption-word.is-active {{ background: {a} !important; color: {bg} !important; box-shadow: 0 0 0 0.06em {a} !important; }}\n"
            f"  .caption-word.is-spoken {{ color: {fg} !important; }}\n")


def font_css(th, scope):
    """One face for all text. scope: '#root' for frames, '.caption-line' for captions."""
    fo = th.get("font")
    if not fo:
        return ""
    fam, w = fo["family"], fo.get("weight", 700)
    return (f'\n  /* theme font (theme.py) */\n'
            f'  @font-face {{ font-family: "{fam}"; src: url("assets/fonts/{fo["file"]}"); font-weight: 100 900; }}\n'
            f'  {scope}, {scope} * {{ font-family: "{fam}", sans-serif !important; font-weight: {w} !important; }}\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    ap.add_argument("--restore", action="store_true")
    a = ap.parse_args()
    project = Path(a.project).resolve()
    comp, keep = project / "compositions", project / ".hyperframes" / "pre-theme"
    files = sorted((comp / "frames").glob("*.html")) + [comp / "captions.html", project / "index.html"]
    files = [f for f in files if f.exists()]
    if a.restore:
        for f in files:
            k = keep / f.relative_to(project)
            if k.exists():
                shutil.copy2(k, f)
        print("restored the source palette")
        return
    th = json.loads((project / "theme.json").read_text(encoding="utf-8"))
    for f in files:
        k = keep / f.relative_to(project)
        # A file without a theme.py marker was (re)generated since the last run — assemble-index,
        # captions build, a re-dispatched frame — so it becomes the new pristine copy.
        if not k.exists() or THEMED not in f.read_text(encoding="utf-8"):
            k.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, k)
        text = recolor(k.read_text(encoding="utf-8"), th)
        if f.name == "index.html":
            text = text.rstrip() + f"\n<!-- {THEMED} -->\n"
        if f.name == "captions.html":
            i = text.rindex("</style>")
            text = text[:i] + caption_css(th) + font_css(th, ".caption-line") + text[i:]
        elif f.parent.name == "frames":
            i = text.index("</style>")
            accents = th.get("accents", {}).get(f.stem)
            text = text[:i] + f"\n  /* themed {THEMED} */" + (accent_css(accents, th) if accents else "") + font_css(th, "#root") + text[i:]
        f.write_text(text, encoding="utf-8")
        print("themed", f.relative_to(project))
    print(f"theme: bg {th['bg']} / fg {th['fg']} / accent {th['accent']}")


if __name__ == "__main__":
    main()
