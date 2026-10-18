"""Shrink the CJK fonts to the characters the film actually uses.

Noto Sans/Serif TC are 12–17 MB each and every frame loads them, which slows the render's
setup and inflates each headless-Chrome worker's memory. A finished film uses a few hundred
distinct characters, so a subset is a few hundred KB.

Scans every composition (frames, captions, index — markup AND script strings, so text set from
JS is included), keeps those characters plus ASCII and common CJK punctuation, writes
<font>.subset.woff2 (or .ttf when the `brotli` package is missing) next to each source font,
and repoints every @font-face url() at the subset. Variable-font axes (weight) are kept.

Run LAST, after captions, theme and every text edit — new characters added later would fall back
to a system font. Re-run after any text change (it always subsets from the full source font).

  python subset_fonts.py --project <dir> [--fonts NotoSansTC-VF.ttf NotoSerifTC-VF.ttf]
  python subset_fonts.py --project <dir> --restore     # point url()s back at the full fonts
Requires: pip install fonttools  (optional: pip install brotli for woff2)
"""
import sys
import argparse
import re
from pathlib import Path
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console

EXTRA = "".join(chr(c) for c in range(0x20, 0x7F)) + "，。、？！：；「」『』（）《》〈〉—…·・～％＋－×÷＝≈≠→←↑↓①②③④⑤⑥⑦⑧⑨⑩²³°μ"


def compositions(project):
    comp = project / "compositions"
    files = sorted(comp.glob("**/*.html")) + [project / "index.html"]
    return [f for f in files if f.exists()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    ap.add_argument("--fonts", nargs="+",
                    default=["GenSekiGothic2TW-B.otf", "NotoSansTC-VF.ttf", "NotoSerifTC-VF.ttf"])
    ap.add_argument("--restore", action="store_true")
    a = ap.parse_args()
    project = Path(a.project).resolve()
    fonts_dir = project / "assets" / "fonts"
    files = compositions(project)

    def full_name(stem):
        for ext in (".otf", ".ttf"):
            if (fonts_dir / f"{stem}{ext}").exists():
                return f"{stem}{ext}"
        return f"{stem}.ttf"

    if a.restore:
        for f in files:
            t = f.read_text(encoding="utf-8")
            t2 = re.sub(r"assets/fonts/([\w.-]+?)\.subset\.(?:woff2|ttf|otf)",
                        lambda m: f"assets/fonts/{full_name(m.group(1))}", t)
            if t2 != t:
                f.write_text(t2, encoding="utf-8")
        print("url()s point at the full fonts again")
        return

    from fontTools import subset
    try:
        import brotli  # noqa: F401
        flavor = "woff2"
    except ImportError:
        flavor = None  # keep the source container: .ttf stays .ttf, CFF .otf stays .otf

    chars = set(EXTRA)
    for f in files:
        chars.update(f.read_text(encoding="utf-8"))
    chars = {c for c in chars if c.isprintable()}
    print(f"{len(chars)} distinct characters across {len(files)} compositions")

    renames = {}
    for name in a.fonts:
        src = fonts_dir / name
        if not src.exists():
            print("skip (not found):", name)
            continue
        out = fonts_dir / f"{src.stem}.subset.{'woff2' if flavor else src.suffix.lstrip('.')}"
        opts = subset.Options()
        opts.flavor = flavor
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        font = subset.load_font(str(src), opts)
        sub = subset.Subsetter(opts)
        sub.populate(text="".join(sorted(chars)))
        sub.subset(font)
        subset.save_font(font, str(out), opts)
        print(f"{name}: {src.stat().st_size / 1e6:.1f} MB -> {out.name} {out.stat().st_size / 1e3:.0f} KB")
        renames[name] = out.name

    for f in files:
        t = f.read_text(encoding="utf-8")
        t2 = t
        for full, small in renames.items():
            stem = Path(full).stem
            t2 = re.sub(rf"assets/fonts/{re.escape(stem)}(?:\.subset\.(?:woff2|ttf|otf)|\.(?:ttf|otf))", f"assets/fonts/{small}", t2)
        if t2 != t:
            f.write_text(t2, encoding="utf-8")
            print("repointed", f.relative_to(project))


if __name__ == "__main__":
    main()
