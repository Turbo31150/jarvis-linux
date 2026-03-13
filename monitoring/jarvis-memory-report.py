#!/usr/bin/env python3
"""JARVIS Memory Report — RAM + ZRAM + Swap status."""
import subprocess
import json
import os
from datetime import datetime


def get_mem():
    info = {}
    with open("/proc/meminfo") as f:
        for line in f:
            parts = line.split()
            key = parts[0].rstrip(":")
            if key in ("MemTotal", "MemAvailable", "MemFree", "SwapTotal", "SwapFree", "Cached", "Buffers"):
                info[key] = int(parts[1]) // 1024
    return info


def get_zram():
    try:
        out = subprocess.check_output(["zramctl", "--output", "NAME,ALGORITHM,DISKSIZE,DATA,COMPR,TOTAL,MOUNTPOINT", "--bytes"],
                                       text=True, timeout=5)
        return out.strip()
    except Exception:
        return "ZRAM non disponible"


def get_swap():
    try:
        return subprocess.check_output(["swapon", "-s"], text=True, timeout=5).strip()
    except Exception:
        return "Swap non disponible"


def get_gpu_vram():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=index,memory.used,memory.total", "--format=csv,noheader,nounits"],
            text=True, timeout=5
        )
        total_used = 0
        total_avail = 0
        for line in out.strip().splitlines():
            parts = [int(x.strip()) for x in line.split(",")]
            total_used += parts[1]
            total_avail += parts[2]
        return {"vram_used_mb": total_used, "vram_total_mb": total_avail}
    except Exception:
        return {}


def main():
    mem = get_mem()
    vram = get_gpu_vram()

    total = mem.get("MemTotal", 0)
    avail = mem.get("MemAvailable", 0)
    used_pct = ((total - avail) / total * 100) if total else 0
    swap_total = mem.get("SwapTotal", 0)
    swap_used = swap_total - mem.get("SwapFree", 0)

    # Score
    if used_pct > 95 or (swap_total > 0 and swap_used / max(swap_total, 1) > 0.8):
        status = "CRITICAL"
    elif used_pct > 85:
        status = "WARNING"
    else:
        status = "OK"

    print(f"=== JARVIS MEMORY STATUS : {status} ===")
    print(f"RAM : {total - avail} / {total} MB ({used_pct:.1f}% utilisé)")
    print(f"Swap : {swap_used} / {swap_total} MB")
    if vram:
        print(f"VRAM GPU : {vram['vram_used_mb']} / {vram['vram_total_mb']} MB")
    print()
    print("--- ZRAM ---")
    print(get_zram())
    print()
    print("--- Swap ---")
    print(get_swap())


if __name__ == "__main__":
    main()
