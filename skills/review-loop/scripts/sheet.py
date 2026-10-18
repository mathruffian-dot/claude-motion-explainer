"""Contact sheets for motion review: one labelled tile per moment, 4x2 per sheet.

Frames come from a rendered video (via ffmpeg) or from existing images
(e.g. hyperframes snapshot output). Tiles default to 360 px wide, the
phone-feed width, so a readable tile means a readable phone.

  python sheet.py --video out/draft.mp4 --timeline timeline.js
  python sheet.py --video out/draft.mp4 --from 3 --to 5 --every 0.2
  python sheet.py --video out/draft.mp4 --at 3.7,3.75,3.8
  python sheet.py --images snaps/a.png snaps/b.png --labels 0.3,1.5
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console

COLS, ROWS = 4, 2
GAP = 8
LABEL_H = 26


def timeline_beats(path, settle):
    """Read window.TL = {...} from timeline.js; return [(label, seconds)]."""
    src = Path(path).read_text(encoding="utf-8")
    body = src[src.index("{"): src.rindex("}") + 1]
    body = re.sub(r"//[^\n]*", "", body)
    body = re.sub(r"([{,]\s*)([A-Za-z_$][\w$]*)\s*:", r'\1"\2":', body)
    body = re.sub(r",(\s*[}\]])", r"\1", body)
    tl = json.loads(body)

    beats = []

    def walk(node, key):
        if isinstance(node, (int, float)) and not isinstance(node, bool):
            beats.append((key, float(node)))
        elif isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{key}.{k}" if key else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{key}[{i}]")

    walk(tl, "")
    beats.sort(key=lambda b: b[1])
    return [(f"{k} {t + settle:.2f}s", t + settle) for k, t in beats]


def duration(video):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(video)],
        check=True, capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def grab(video, t, dest, end):
    # A beat + settle can land past the last frame; show the last frame instead.
    t = max(0.0, min(t, end - 0.05))
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video),
         "-frames:v", "1", str(dest)],
        check=True,
    )
    if not Path(dest).exists():
        sys.exit(f"ffmpeg wrote no frame at {t:.3f}s")
    return dest


def label_font():
    for name in ("msjh.ttc", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, 16)
        except OSError:
            continue
    return ImageFont.load_default()


def build_sheets(tiles, out_dir, width, stem):
    out_dir.mkdir(parents=True, exist_ok=True)
    font = label_font()
    per = COLS * ROWS
    written = []
    for n in range(0, len(tiles), per):
        batch = tiles[n:n + per]
        first = Image.open(batch[0][1])
        h = round(first.height * width / first.width)
        cell_h = h + LABEL_H
        sheet = Image.new("RGB", (COLS * width + (COLS + 1) * GAP,
                                  ROWS * cell_h + (ROWS + 1) * GAP), (24, 24, 24))
        draw = ImageDraw.Draw(sheet)
        for i, (label, img_path) in enumerate(batch):
            x = GAP + (i % COLS) * (width + GAP)
            y = GAP + (i // COLS) * (cell_h + GAP)
            img = Image.open(img_path).convert("RGB").resize((width, h), Image.LANCZOS)
            draw.text((x + 4, y + 4), label, fill=(240, 240, 240), font=font)
            sheet.paste(img, (x, y + LABEL_H))
        dest = out_dir / f"{stem}-{n // per + 1}.png"
        sheet.save(dest)
        written.append(dest)
    return written


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--video", help="rendered video to sample with ffmpeg")
    src.add_argument("--images", nargs="+", help="existing frame images, in order")
    p.add_argument("--timeline", help="timeline.js; one tile per beat")
    p.add_argument("--settle", type=float, default=0.3, help="seconds after each beat (default 0.3)")
    p.add_argument("--at", help="comma-separated times in seconds")
    p.add_argument("--from", dest="t0", type=float)
    p.add_argument("--to", dest="t1", type=float)
    p.add_argument("--every", type=float, default=0.2)
    p.add_argument("--labels", help="comma-separated labels for --images")
    p.add_argument("--width", type=int, default=360, help="tile width in px (default 360 = phone)")
    p.add_argument("--out", default="out/sheets", help="output folder (default out/sheets)")
    p.add_argument("--name", default="beats", help="sheet file stem (default beats)")
    a = p.parse_args()

    if a.images:
        labels = a.labels.split(",") if a.labels else [Path(i).stem for i in a.images]
        if len(labels) != len(a.images):
            sys.exit("--labels must have one entry per image")
        tiles = list(zip(labels, a.images))
    else:
        if a.timeline:
            moments = timeline_beats(a.timeline, a.settle)
        elif a.at:
            moments = [(f"{float(t):.2f}s", float(t)) for t in a.at.split(",")]
        elif a.t0 is not None and a.t1 is not None:
            steps = int(round((a.t1 - a.t0) / a.every)) + 1
            moments = [(f"{a.t0 + i * a.every:.2f}s", a.t0 + i * a.every) for i in range(steps)]
        else:
            sys.exit("with --video, give --timeline, --at, or --from/--to")
        tmp = Path(tempfile.mkdtemp(prefix="sheet-"))
        end = duration(a.video)
        tiles = [(lbl, grab(a.video, t, tmp / f"f{i:03d}.png", end)) for i, (lbl, t) in enumerate(moments)]

    for path in build_sheets(tiles, Path(a.out), a.width, a.name):
        print(path)


if __name__ == "__main__":
    main()
