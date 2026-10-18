"""Unify cross-frame details that parallel frame workers choose differently.

- Fonts: drop Google Fonts @imports (offline / cloud renders fail on them); declare every local
  face found in <project>/assets/fonts/ (files named Family-Style.woff2, e.g. Newsreader-Regular,
  HankenGrotesk-SemiBold) in every frame; put the Latin face in front of CJK-only stacks so
  numbers, units and formulas look the same in every frame.
- Hairlines (optional): force the top/bottom frame rules to one position in every frame.

theme.json (optional keys):
  "font_stacks": {"NotoSerifTC": "Newsreader", "NotoSansTC": "Hanken Grotesk"}
  "hairlines":   {"top": "3cqw", "bottom": "880px"}

Idempotent — run after any frame is (re)built:  python unify_frames.py --project <dir>
"""
import sys
import argparse
import json
import re
from pathlib import Path
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console

MARK = "/* local Latin faces (unify_frames.py) */"
WEIGHTS = {"Thin": 100, "ExtraLight": 200, "Light": 300, "Regular": 400, "Italic": 400, "Medium": 500,
           "SemiBold": 600, "Bold": 700, "ExtraBold": 800, "Black": 900}
FAMILY_NAMES = {"HankenGrotesk": "Hanken Grotesk", "DMMono": "DM Mono", "JetBrainsMono": "JetBrains Mono",
                "InstrumentSerif": "Instrument Serif", "SpaceGrotesk": "Space Grotesk"}


def faces(fonts_dir):
    out = []
    for f in sorted(fonts_dir.glob("*.woff2")):
        fam, _, style = f.stem.partition("-")
        fam = FAMILY_NAMES.get(fam, re.sub(r"(?<=[a-z])(?=[A-Z])", " ", fam))
        w = WEIGHTS.get(style.replace("Italic", "") or "Regular", 400) if style != "Italic" else 400
        st = "italic" if "Italic" in style else "normal"
        out.append(f'@font-face {{ font-family: "{fam}"; src: url("assets/fonts/{f.name}") format("woff2"); '
                   f"font-weight: {w}; font-style: {st}; }}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    a = ap.parse_args()
    project = Path(a.project).resolve()
    cfg_path = project / "theme.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    stacks = cfg.get("font_stacks", {"NotoSerifTC": "Newsreader", "NotoSansTC": "Hanken Grotesk"})
    hair = cfg.get("hairlines")
    block = MARK + "".join("\n    " + x for x in faces(project / "assets" / "fonts")) + "\n"
    latin = "|".join(re.escape(v) for v in stacks.values())

    def fix_stack(m):
        stack = m.group(1)
        if re.search(latin, stack):
            return m.group(0)
        for cjk, lat in stacks.items():
            if stack.lstrip().startswith(f'"{cjk}"'):
                return m.group(0).replace(stack, f'"{lat}", ' + stack.lstrip(), 1)
        return m.group(0)

    for f in sorted((project / "compositions" / "frames").glob("*.html")):
        t0 = f.read_text(encoding="utf-8")
        t = re.sub(r"[ \t]*@import url\(\"https://fonts\.googleapis\.com[^\n]*\n", "", t0)
        if MARK in t:
            t = re.sub(re.escape(MARK) + r"(?:\n\s*@font-face[^\n]*)*\n", block, t)
        else:
            i = re.search(r"<style[^>]*>", t).end()
            t = t[:i] + "\n    " + block + t[i:]
        t = re.sub(r"font-family:\s*([^;{}]*,[^;{}]*);", fix_stack, t)
        if hair:
            t = re.sub(r'(hair(?:line)?-top"\]\s*\{\s*top:\s*)[\d.]+(px|cqw)', rf"\g<1>{hair['top']}", t)
            t = re.sub(r'(hair(?:line)?-bottom"\]\s*\{\s*top:\s*)[\d.]+(px|cqw)', rf"\g<1>{hair['bottom']}", t)
        if t != t0:
            f.write_text(t, encoding="utf-8")
        print("patched" if t != t0 else "ok     ", f.name)


if __name__ == "__main__":
    main()
