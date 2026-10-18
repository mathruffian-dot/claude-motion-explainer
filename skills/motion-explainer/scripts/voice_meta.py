"""Narration WAVs -> trimmed WAVs + audio_meta.json for the HyperFrames faceless-explainer pipeline.

For each <project>/assets/voice/raw/NN.wav (NN = storyboard frame number, from any TTS engine):
  1. trim leading/trailing silence (keep 80 ms head, 150 ms tail) -> assets/voice/NN.wav
  2. find pauses with ffmpeg silencedetect and time each clause of that frame's SCRIPT.md line
     (clauses split at Chinese/Latin punctuation) onto the speech spans between pauses
  3. write audio_meta.json: voices[{frame, path, source:"host", speech_s, duration_s,
     words:[{text,start,end}]}]

Clause-level "words" keep captions in the script's own text — no ASR, so no simplified-character
or digit/number mismatches. captions.mjs then groups clauses into caption lines.

  python voice_meta.py --project <dir> [--pad 0.7] [--last-pad 1.8]
Requires ffmpeg + ffprobe on PATH.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console

HEAD_KEEP, TAIL_KEEP = 0.08, 0.15
NOISE, MIN_GAP = "-38dB", 0.10
SPLIT = r"[，。？！；、：,.?!;:]"


def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", str(path)])
    return float(out.stdout.strip())


def speech_spans(path):
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
               "-af", f"silencedetect=noise={NOISE}:d={MIN_GAP}", "-f", "null", "-"]).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    total = duration(path)
    if len(ends) < len(starts):
        ends.append(total)
    spans, cur = [], 0.0
    for s, e in zip(starts, ends):
        if s > cur + 0.02:
            spans.append((cur, s))
        cur = e
    if cur < total - 0.02:
        spans.append((cur, total))
    return spans, total


def trim(src, dst):
    spans, total = speech_spans(src)
    if not spans:
        sys.exit(f"no speech found in {src}")
    a = max(0.0, spans[0][0] - HEAD_KEEP)
    b = min(total, spans[-1][1] + TAIL_KEEP)
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-ss", f"{a:.3f}", "-to", f"{b:.3f}",
         "-c:a", "pcm_s16le", str(dst)])


def clauses(text):
    parts, buf = [], ""
    for ch in text:
        if re.match(SPLIT, ch):
            if buf.strip():
                parts.append(buf.strip() + (ch if ch in "？?" else ""))
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf.strip())
    return parts


def time_clauses(parts, spans):
    """Equal counts -> one span per clause. Otherwise lay clauses over speech time by
    character share, then snap each boundary into the nearest pause."""
    if len(parts) == len(spans):
        return [(p, s, e) for p, (s, e) in zip(parts, spans)]
    total_speech = sum(e - s for s, e in spans)
    weights = [len(re.sub(r"\s", "", p)) for p in parts]
    wsum = sum(weights)

    def at(frac):
        target = frac * total_speech
        for s, e in spans:
            if target <= e - s:
                return s + target
            target -= e - s
        return spans[-1][1]

    gaps = [(spans[i][1], spans[i + 1][0]) for i in range(len(spans) - 1)]
    out, acc, start = [], 0, spans[0][0]
    for k, (p, w) in enumerate(zip(parts, weights)):
        acc += w
        end = at(acc / wsum)
        near = min(gaps, key=lambda g: abs((g[0] + g[1]) / 2 - end), default=None)
        if near and abs((near[0] + near[1]) / 2 - end) < 0.35 and k < len(parts) - 1:
            end, nxt = near[0], near[1]
        else:
            nxt = end
        out.append((p, start, end))
        start = nxt
    return out


def script_lines(project):
    text = (project / "SCRIPT.md").read_text(encoding="utf-8")
    return {int(n): t.strip() for n, t in
            re.findall(r"^## Line (\d+).*?\n(?:.*?\n)*?    (\S.*)$", text, re.M)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    ap.add_argument("--pad", type=float, default=0.7, help="seconds of hold after each line")
    ap.add_argument("--last-pad", type=float, default=1.8, help="hold after the closing line")
    a = ap.parse_args()
    project = Path(a.project).resolve()
    raw, out = project / "assets/voice/raw", project / "assets/voice"
    lines = script_lines(project)
    frames = sorted(lines)
    voices = []
    for n in frames:
        src = raw / f"{n:02d}.wav"
        if not src.exists():
            sys.exit(f"missing {src}")
        dst = out / f"{n:02d}.wav"
        trim(src, dst)
        spans, total = speech_spans(dst)
        timed = time_clauses(clauses(lines[n]), spans)
        pad = a.last_pad if n == frames[-1] else a.pad
        voices.append({
            "frame": n, "path": f"assets/voice/{n:02d}.wav", "source": "host",
            "speech_s": round(total, 3), "duration_s": round(total + pad, 2),
            "words": [{"text": t, "start": round(s, 3), "end": round(e, 3)} for t, s, e in timed],
        })
        print(f"frame {n}: {total:.2f}s speech, {len(spans)} spans, {len(timed)} clauses")
    meta = {"bgm": None, "voices": voices, "sfx": []}
    (project / "audio_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("total", round(sum(v["duration_s"] for v in voices), 2), "s -> audio_meta.json")


if __name__ == "__main__":
    main()
