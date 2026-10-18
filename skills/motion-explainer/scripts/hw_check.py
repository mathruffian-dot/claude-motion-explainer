"""Check this machine and recommend settings for a motion-explainer run.

Detects CPU cores, RAM, NVIDIA GPU + VRAM (via nvidia-smi) and free disk, then prints
recommendations. Every recommendation is an ESTIMATE from rules of thumb, not a benchmark —
see references/hardware.md for the reasoning and the one measured data point.

  python hw_check.py [--project <dir>]     # --project: check free disk where the film will live
"""
import sys
import argparse
import ctypes
import os
import platform
import shutil
import subprocess
from pathlib import Path
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console


def ram_gb():
    system = platform.system()
    try:
        if system == "Windows":
            class MEMSTAT(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MEMSTAT()
            m.dwLength = ctypes.sizeof(MEMSTAT)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.ullTotalPhys / 2**30, m.ullAvailPhys / 2**30
        if system == "Linux":
            info = {}
            for line in Path("/proc/meminfo").read_text().splitlines():
                k, v = line.split(":", 1)
                info[k] = int(v.split()[0]) * 1024
            return info["MemTotal"] / 2**30, info.get("MemAvailable", 0) / 2**30
        if system == "Darwin":
            total = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout)
            return total / 2**30, None
    except Exception:
        pass
    return None, None


def gpus():
    exe = shutil.which("nvidia-smi")
    if not exe:
        return []
    out = subprocess.run([exe, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True)
    found = []
    for line in out.stdout.strip().splitlines():
        name, _, mem = line.rpartition(",")
        try:
            found.append((name.strip(), int(mem.strip()) / 1024))
        except ValueError:
            pass
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    a = ap.parse_args()

    cores = os.cpu_count() or 1
    total, avail = ram_gb()
    gpu = gpus()
    free = shutil.disk_usage(Path(a.project).resolve().anchor or "/").free / 2**30
    vram = max((v for _, v in gpu), default=0)

    print("== This machine")
    print(f"  OS        {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"  CPU       {cores} logical cores")
    print(f"  RAM       {total:.1f} GB total" + (f", {avail:.1f} GB free" if avail else "") if total else "  RAM       unknown")
    print("  GPU       " + ("; ".join(f"{n} ({v:.0f} GB VRAM)" for n, v in gpu) if gpu else "no NVIDIA GPU found (nvidia-smi missing)"))
    print(f"  Disk      {free:.0f} GB free on the project drive")

    print("\n== Recommendations (estimates — see references/hardware.md)")
    # narration
    if vram >= 12:
        tts = ("edge-tts by default; Breeze TTS 2 is possible on this GPU if the user wants it "
               "(~7.7 GB VRAM eager, ~7 GB of model files, research/non-commercial licence)")
    elif vram >= 8:
        tts = "edge-tts. Breeze TTS 2 might just fit (~7.7 GB VRAM eager) but expect out-of-memory errors"
    else:
        tts = "edge-tts (no GPU needed; needs internet while generating)"
    print(f"  Narration          {tts}")
    # render workers
    if total is None:
        workers = "2 (RAM unknown — start low)"
    elif total < 8:
        workers = "1"
    elif total < 16:
        workers = "2"
    else:
        workers = "auto (HyperFrames default)"
    if cores < 4 and "auto" in workers:
        workers = "2 (few CPU cores)"
    print(f"  Render workers     hyperframes render --workers {workers.split()[0]}   [{workers}]")
    print("  Review renders     always --quality draft; --quality high only for the final render")
    # sub-agent dispatch
    if total is not None and total < 16:
        waves = "waves of 3 (workers may open local preview browsers at the same time)"
    else:
        waves = "all frames at once"
    print(f"  Frame sub-agents   {waves}")
    print("  Fonts              run scripts/subset_fonts.py last (CJK fonts 12-17 MB -> a few hundred KB)")
    if free < 10:
        print(f"  Disk               only {free:.0f} GB free — renders, frame caches and (for Breeze) ~7 GB of model need room")
    print("\n  Measured reference: 24 cores / 95 GB RAM / RTX 5090 -> 105 s film, draft render ~75-80 s,")
    print("  high-quality ~85-90 s, 3 render workers chosen by 'auto'. Slower machines take proportionally longer.")


if __name__ == "__main__":
    main()
