"""Fix a mispronounced word in one narration line without moving any animation.

  audition: cut the clause(s) holding the word out of every candidate take and string them into
            one listening file, each announced by a short edge-tts label ("A", "B", ...).
  apply:    take the chosen candidate and stretch the WHOLE line uniformly (atempo, pitch kept)
            to the original speech length, so frame durations stay valid; match the original line's
            loudness; re-time that line's clauses in audio_meta.json for the captions. (Never cut a
            re-take into clauses by its pauses — it pauses in different places, and the cuts land
            mid-word, duplicating or dropping words.)
            Afterwards: rebuild captions, patch_captions.py, theme.py (it picks up the rebuilt
            captions by itself), transitions inject, render.

  python fix_voice.py --project <dir> audition --line 3 --clauses 0 1
  python fix_voice.py --project <dir> apply --line 3 --take 03_C

Candidates: <project>/assets/voice/fix/cand/NN_X.wav — re-takes of the WHOLE line from the same voice
(same Breeze reference / same edge-tts voice), each with a different seed or a respelling of the
problem word (e.g. "Road-ster", a same-tone homophone). Captions keep the script text.
The user picks by ear from the audition file; never pick by ASR score.
"""
import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_meta as vm  # noqa: E402  (trim, speech_spans, clauses, time_clauses, script_lines)
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console

ROOT = Path(".").resolve()   # set from --project in main()
FIX = ROOT / "assets" / "voice" / "fix"


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def timed(wav, line_text):
    spans, total = vm.speech_spans(wav)
    return vm.time_clauses(vm.clauses(line_text), spans), total


def trimmed(src):
    dst = FIX / "work" / f"{src.stem}.trim.wav"
    dst.parent.mkdir(parents=True, exist_ok=True)
    vm.trim(src, dst)
    return dst


async def say(text, out):
    import edge_tts
    await edge_tts.Communicate(text, "zh-TW-YunJheNeural", rate="+10%").save(str(out))


def label(tag, work):
    """Spoken label (edge-tts) when available, else a short beep."""
    labw = work / f"label_{tag}.wav"
    try:
        lab = work / f"label_{tag}.mp3"
        asyncio.run(say(tag, lab))
        ff("-i", str(lab), "-ar", "24000", "-ac", "1", str(labw))
    except Exception:
        ff("-f", "lavfi", "-i", "sine=f=880:d=0.25", "-ar", "24000", "-ac", "1", str(labw))
    return labw


def audition(line, clause_ids):
    text = vm.script_lines(ROOT)[line]
    takes = sorted((FIX / "cand").glob(f"{line:02d}_*.wav"))
    work = FIX / "work"
    work.mkdir(parents=True, exist_ok=True)
    parts = []
    for t in takes:
        tag = t.stem.split("_")[1]
        labw = label(tag, work)
        tw = trimmed(t)
        cl, _ = timed(tw, text)
        a = max(0.0, cl[min(clause_ids)][1] - 0.05)
        b = cl[max(clause_ids)][2] + 0.1
        seg = work / f"{t.stem}.seg.wav"
        ff("-i", str(tw), "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-ar", "24000", "-ac", "1", str(seg))
        parts += [labw, seg]
        print(f"{t.stem}: clauses {clause_ids} = {a:.2f}-{b:.2f}s  「{''.join(c[0] for c in cl[min(clause_ids):max(clause_ids)+1])}」")
    gap = work / "gap.wav"
    ff("-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "0.6", str(gap))
    listing = work / f"list_{line:02d}.txt"
    seq = []
    for p in parts:
        seq += [p, gap]
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in seq), encoding="utf-8")
    out = FIX / f"audition_line{line:02d}.wav"
    ff("-f", "concat", "-safe", "0", "-i", str(listing), "-ar", "24000", "-ac", "1", str(out))
    print("->", out)


def lufs(wav):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(wav), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    import re
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1])


def apply(line, take, _gain=None):
    """Whole-line swap: stretch the chosen take UNIFORMLY to the original speech length (no
    per-clause cutting — a re-take pauses in different places, so pause-based clause cuts
    land mid-word and duplicate or drop words), match the original line's loudness, then
    re-time that line's clauses for the captions. Frame durations stay the same."""
    meta_path = ROOT / "audio_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    voice = next(v for v in meta["voices"] if v["frame"] == line)
    total = voice["speech_s"]
    dest = ROOT / "assets" / "voice" / f"{line:02d}.wav"
    backup = FIX / f"{line:02d}.before-fix.wav"
    if not backup.exists():
        ff("-i", str(dest), str(backup))
    tw = trimmed(FIX / "cand" / f"{take}.wav")
    _, cand_total = vm.speech_spans(tw)
    tempo = cand_total / total
    if not 0.85 <= tempo <= 1.15:
        print(f"! take is {cand_total:.2f}s vs {total:.2f}s (atempo {tempo:.3f}) — more than 15% off; consider another take")
    stretched = FIX / "work" / f"{take}.stretched.wav"
    ff("-i", str(tw), "-af", f"atempo={tempo:.5f},apad,atrim=0:{total:.3f}", "-ar", "24000", "-ac", "1", str(stretched))
    gain = lufs(backup) - lufs(stretched)
    ff("-i", str(stretched), "-af", f"volume={gain:.2f}dB,alimiter=limit=0.84:level=false",
       "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", str(dest))
    # captions follow the new audio
    text = vm.script_lines(ROOT)[line]
    spans, _ = vm.speech_spans(dest)
    voice["words"] = [{"text": t, "start": round(s, 3), "end": round(e, 3)}
                      for t, s, e in vm.time_clauses(vm.clauses(text), spans)]
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{take}: {cand_total:.2f}s -> {total:.2f}s (atempo {tempo:.3f}), gain {gain:+.1f} dB -> {dest.name}; "
          f"captions re-timed ({len(spans)} pauses / {len(voice['words'])} clauses); backup {backup.name}")


def main():
    global ROOT, FIX
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("audition")
    a1.add_argument("--line", type=int, required=True)
    a1.add_argument("--clauses", type=int, nargs="+", required=True)
    a2 = sub.add_parser("apply")
    a2.add_argument("--line", type=int, required=True)
    a2.add_argument("--take", required=True)
    a = ap.parse_args()
    ROOT = Path(a.project).resolve()
    FIX = ROOT / "assets" / "voice" / "fix"
    if a.cmd == "audition":
        audition(a.line, a.clauses)
    else:
        apply(a.line, a.take)


if __name__ == "__main__":
    main()
