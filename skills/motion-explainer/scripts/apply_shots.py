"""Write each frame's time-coded shot sequence into STORYBOARD.md from shots.json.

Shots are authored per narration clause (an index into audio_meta.json voices[].words), so every
reveal lands on the clause that names it. This turns them into real-second Scene windows and the
metadata bullets the HyperFrames frame-packet builder reads. Re-run after any narration change.

shots.json:
{
  "3": {
    "blueprint": "compose",                      # "<id> (Adapt)" / "<id> (Reproduce)" / "compose"
    "note": "cutaway diagram built layer by layer",
    "rules": "svg-path-draw, svg-icon-enrichment", # hyperframes-animation rule ids
    "focal": "...", "roles": "...", "sfx": "...",
    "scenes": [[0, "what is on screen / what moves"], [2, "..."], ...]   # [clause index, text]
  }, ...
}
  python apply_shots.py --project <dir>
"""
import sys
import argparse
import json
import re
from pathlib import Path
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    a = ap.parse_args()
    project = Path(a.project).resolve()
    shots = {k: v for k, v in json.loads((project / "shots.json").read_text(encoding="utf-8")).items()
             if not k.startswith("_")}
    meta = json.loads((project / "audio_meta.json").read_text(encoding="utf-8"))
    voices = {v["frame"]: v for v in meta["voices"]}
    sb_path = project / "STORYBOARD.md"
    sb = sb_path.read_text(encoding="utf-8")
    for key, spec in shots.items():
        n = int(key)
        v = voices[n]
        words, dur = v["words"], v["duration_s"]
        cues = [i for i, _ in spec["scenes"]]
        assert max(cues) < len(words), f"frame {n}: cue {max(cues)} but only {len(words)} clauses"
        lines = []
        for k, (i, text) in enumerate(spec["scenes"]):
            t0 = 0.0 if k == 0 else words[i]["start"]
            t1 = words[spec["scenes"][k + 1][0]]["start"] if k + 1 < len(spec["scenes"]) else dur
            lines.append(f"Scene {k + 1} ({t0:.1f}–{t1:.1f}s) [VO: 「{words[i]['text']}」]: {text}")
        meta_lines = "\n".join(f"- {k}: {spec[k]}" for k in ("blueprint", "rules", "focal", "roles", "sfx") if spec.get(k))
        sec = re.compile(rf"(## Frame {n} — [^\n]*\n)(.*?)(?=\n## Frame |\Z)", re.S)
        m = sec.search(sb)
        assert m, f"frame {n}: section not found"
        body = re.sub(r"^- (blueprint|rules|focal|roles|sfx): .*\n", "", m.group(2), flags=re.M)
        cut = list(re.finditer(r"^- [a-z_]+: .*\n", body, re.M))[-1].end()
        body = body[:cut] + meta_lines + "\n" + body[cut:]
        body = re.sub(r"\n(Shot note:|Scene \d+ \().*", "", body, flags=re.S).rstrip("\n")
        note = f"Shot note: {spec['note']}\n" if spec.get("note") else ""
        sb = sb[:m.start(2)] + body + "\n\n" + note + "\n".join(lines) + "\n" + sb[m.end(2):]
    sb_path.write_text(sb, encoding="utf-8")
    print("shot sequences written for frames", ", ".join(shots))


if __name__ == "__main__":
    main()
