"""Narrate SCRIPT.md with edge-tts (Microsoft online neural voices) — no GPU needed.

Writes <project>/assets/voice/raw/NN.wav for every "## Line N" in SCRIPT.md, the same files any
other TTS route produces, so voice_meta.py and the rest of the pipeline do not change.

  pip install edge-tts            # needs an internet connection while generating
  python edge_tts_voice.py --project <dir> [--voice zh-TW-HsiaoChenNeural] [--rate +0%] [--pitch +0Hz]
  python edge_tts_voice.py --list zh-TW       # show voices for a locale
  python edge_tts_voice.py --project <dir> --line 5 --text "Road-ster 的…" --out assets/voice/fix/cand/05_B.wav
                                              # one retake candidate for fix_voice.py

Taiwanese Mandarin voices: zh-TW-HsiaoChenNeural (female, default), zh-TW-HsiaoYuNeural (female),
zh-TW-YunJheNeural (male). Every line uses the same voice, so the narrator stays consistent.
Existing WAVs are skipped; delete one to regenerate it. Requires ffmpeg on PATH.
"""
import argparse
import asyncio
import re
import subprocess
import sys
from pathlib import Path
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console


async def list_voices(locale):
    import edge_tts
    for v in await edge_tts.list_voices():
        if v["Locale"].lower().startswith(locale.lower()):
            print(f'{v["ShortName"]:28} {v["Gender"]:7} {", ".join(v.get("VoiceTag", {}).get("VoicePersonalities", []))}')


async def synth(text, voice, rate, pitch, mp3):
    import edge_tts
    await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(mp3))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    ap.add_argument("--voice", default="zh-TW-HsiaoChenNeural")
    ap.add_argument("--rate", default="+0%", help='speaking rate, e.g. "-5%%" or "+10%%"')
    ap.add_argument("--pitch", default="+0Hz", help='pitch shift, e.g. "-2Hz"')
    ap.add_argument("--list", metavar="LOCALE", help="list voices for a locale (e.g. zh-TW) and exit")
    ap.add_argument("--line", type=int, help="one candidate for fix_voice.py: only this SCRIPT.md line ...")
    ap.add_argument("--text", help="... spoken as this text instead (alternate spelling; captions keep the script)")
    ap.add_argument("--out", help="... written to this WAV, e.g. assets/voice/fix/cand/05_B.wav (overwrites)")
    a = ap.parse_args()
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        sys.exit("edge-tts is not installed: pip install edge-tts")
    if a.list:
        asyncio.run(list_voices(a.list))
        return
    project = Path(a.project).resolve()
    script = (project / "SCRIPT.md").read_text(encoding="utf-8")
    lines = re.findall(r"^## Line (\d+).*?\n(?:.*?\n)*?    (\S.*)$", script, re.M)
    if a.line is not None:
        # edge-tts has no seed: vary candidates by spelling (--text), --rate or --pitch instead.
        found = {int(n): text for n, text in lines}
        if a.line not in found or not a.out:
            sys.exit("--line needs an existing '## Line N' in SCRIPT.md and --out <file.wav>")
        wav = Path(a.out).resolve()
        wav.parent.mkdir(parents=True, exist_ok=True)
        mp3 = wav.with_suffix(".mp3")
        asyncio.run(synth((a.text or found[a.line]).strip(), a.voice, a.rate, a.pitch, mp3))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-ar", "24000", "-ac", "1",
                        "-c:a", "pcm_s16le", str(wav)], check=True)
        mp3.unlink()
        print("[ok]", wav)
        return
    raw = project / "assets" / "voice" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    for n, text in lines:
        wav = raw / f"{int(n):02d}.wav"
        if wav.exists():
            print("[skip]", wav.name)
            continue
        mp3 = wav.with_suffix(".mp3")
        asyncio.run(synth(text.strip(), a.voice, a.rate, a.pitch, mp3))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-ar", "24000", "-ac", "1",
                        "-c:a", "pcm_s16le", str(wav)], check=True)
        mp3.unlink()
        print("[ok]", wav.name)
    print(f"voice {a.voice} -> {raw}")


if __name__ == "__main__":
    main()
