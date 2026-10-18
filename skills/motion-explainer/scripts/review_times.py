"""Print review timestamps: one per narration clause, just before the clause ends (the settled state).

Reads where each voice line actually starts in the assembled film (the <audio src="assets/voice/NN.wav"
data-start=...> tags in index.html, so transitions are already accounted for) and the clause end
times in audio_meta.json. Use it after assemble-index / transitions inject, before reviewing:

  python review_times.py --project <dir>                 # comma list for sheet.py --at
  python review_times.py --project <dir> --table         # clause-by-clause table
  python <review-loop>/scripts/sheet.py --video renders/draft.mp4 --at "$(python review_times.py --project .)" --out review --name draft
"""
import argparse
import json
import re
import sys
from pathlib import Path
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    ap.add_argument("--before", type=float, default=0.15, help="seconds before each clause end (default 0.15)")
    ap.add_argument("--table", action="store_true")
    a = ap.parse_args()
    project = Path(a.project).resolve()
    html = (project / "index.html").read_text(encoding="utf-8")
    starts = {}
    for m in re.finditer(r"<audio\b[^>]*>", html):
        tag = m.group(0)
        src = re.search(r'\bsrc="([^"]+)"', tag)
        st = re.search(r'\bdata-start="([\d.]+)"', tag)
        if src and st:
            starts[src.group(1)] = float(st.group(1))
    meta = json.loads((project / "audio_meta.json").read_text(encoding="utf-8"))
    rows = []
    for v in meta["voices"]:
        if v["path"] not in starts:
            sys.exit(f"{v['path']} is not placed in index.html — run assemble-index first")
        t0 = starts[v["path"]]
        for w in v["words"]:
            rows.append((v["frame"], w["text"], round(max(t0, t0 + w["end"] - a.before), 2)))
    if a.table:
        for frame, text, t in rows:
            print(f"{t:8.2f}  frame {frame}  {text}")
    else:
        print(",".join(f"{t}" for _, _, t in rows))


if __name__ == "__main__":
    main()
