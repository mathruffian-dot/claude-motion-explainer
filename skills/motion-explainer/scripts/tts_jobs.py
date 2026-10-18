"""SCRIPT.md -> a TTS job list: one designed reference voice, then every line cloned from it.

Cloning every line from ONE reference keeps the narrator identical across the film (designing a
voice per line drifts). The output matches the jobs format of Breeze TTS 2 batch runners:

  {"out_dir": "raw", "jobs": [{"name","text","instruction"?,"ref_audio"?,"ref_text"?,"seed"?}]}

  python tts_jobs.py --project <dir> \
      --voice "A lively, clear Taiwanese woman science teacher in her early thirties, ..." \
      [--ref-text "同學們好，今天我們要..."]
writes <project>/assets/voice/tts_jobs.json. Run your TTS batch on it so that
assets/voice/raw/NN.wav exists for every line, then run voice_meta.py.
Any other TTS engine works too — it only has to produce assets/voice/raw/NN.wav per line.
"""
import sys
import argparse
import json
import re
from pathlib import Path
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console

DEFAULT_REF = "同學們好，今天我們用三個簡單的物理原理，來拆解一個看起來很神奇的現象。"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    ap.add_argument("--voice", required=True, help="voice-design instruction for the reference voice")
    ap.add_argument("--ref-text", default=DEFAULT_REF, help="sentence the reference voice reads")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    project = Path(a.project).resolve()
    script = (project / "SCRIPT.md").read_text(encoding="utf-8")
    lines = re.findall(r"^## Line (\d+).*?\n(?:.*?\n)*?    (\S.*)$", script, re.M)
    jobs = [{"name": "ref_narrator", "text": a.ref_text, "instruction": a.voice, "seed": a.seed}]
    for n, text in lines:
        jobs.append({"name": f"{int(n):02d}", "text": text.strip(), "ref_audio": "raw/ref_narrator.wav",
                     "ref_text": a.ref_text, "seed": 42})
    out = project / "assets/voice/tts_jobs.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"out_dir": "raw", "jobs": jobs}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(jobs)} jobs -> {out}")


if __name__ == "__main__":
    main()
