"""Narrate SCRIPT.md with Breeze TTS 2 through its official CLI (infer.py) — local NVIDIA GPU.

Two steps, so the whole film keeps ONE narrator:
  1. Voice Design: one reference clip from a natural-language voice description (--voice)
  2. Voice Clone: every "## Line N" spoken by that reference -> assets/voice/raw/NN.wav

  python breeze_voice.py --project <dir> \
      --breeze-repo <path to breeze-tts clone> --model <path to Breeze-TTS-2 checkpoint> \
      --voice "A lively, clear Taiwanese woman science teacher in her early thirties, warm and curious, natural Taiwanese Mandarin accent, moderate pace." \
      [--python <python in the Breeze venv>] [--ref-text "..."] [--only-ref]

Use --only-ref first and let the user listen to assets/voice/raw/ref_narrator.wav before
generating every line. Existing WAVs are skipped. infer.py reloads the model on each call, so this
is slower than a batch runner; tts_jobs.py writes a job list for one if you have it.
Licence: Breeze TTS 2 weights and their outputs are research / non-commercial only.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console

DEFAULT_REF = "同學們好，今天我們用三個簡單的物理原理，來拆解一個看起來很神奇的現象。"


def infer(a, out, text, extra):
    cmd = [a.python, str(Path(a.breeze_repo) / "infer.py"), str(a.model), "--text", text, "--output", str(out), *extra]
    r = subprocess.run(cmd, cwd=a.breeze_repo)
    if r.returncode != 0 or not out.exists():
        sys.exit(f"infer.py failed for {out.name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    ap.add_argument("--breeze-repo", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--voice", required=True, help="voice-design description for the narrator")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--ref-text", default=DEFAULT_REF)
    ap.add_argument("--only-ref", action="store_true", help="make the reference clip only (for a listening check)")
    a = ap.parse_args()
    project = Path(a.project).resolve()
    raw = project / "assets" / "voice" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    ref = raw / "ref_narrator.wav"
    if not ref.exists():
        infer(a, ref, a.ref_text, ["--instruction", a.voice, "--cfg-scale", "4"])
        print("[ok] ref_narrator.wav")
    if a.only_ref:
        return
    script = (project / "SCRIPT.md").read_text(encoding="utf-8")
    for n, text in re.findall(r"^## Line (\d+).*?\n(?:.*?\n)*?    (\S.*)$", script, re.M):
        out = raw / f"{int(n):02d}.wav"
        if out.exists():
            print("[skip]", out.name)
            continue
        infer(a, out, text.strip(), ["--ref-audio", str(ref), "--ref-text", a.ref_text])
        print("[ok]", out.name)


if __name__ == "__main__":
    main()
