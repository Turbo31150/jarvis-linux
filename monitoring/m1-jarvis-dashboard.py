#!/usr/bin/env python3
"""JARVIS M1 Dashboard — Affichage CLI temps reel CPU/RAM/GPU/Docker/Services."""
import json
import os
import subprocess
import time
from datetime import datetime


def clear():
    os.system("clear")


def section(title):
    print(f"\n\033[1;36m{'─' * 60}\033[0m")
    print(f"\033[1;33m  {title}\033[0m")
    print(f"\033[1;36m{'─' * 60}\033[0m")


def get_cpu():
    load1, load5, load15 = os.getloadavg()
    temp = None
    try:
        out = subprocess.check_output(["sensors"], text=True, timeout=5)
        for line in out.splitlines():
            if "Tctl" in line or "Tdie" in line:
                temp = float(line.split("+")[1].split("°")[0])
                break
    except Exception:
        pass
    return load1, load5, load15, temp


def get_ram():
    info = {}
    with open("/proc/meminfo") as f:
        for line in f:
            parts = line.split()
            key = parts[0].rstrip(":")
            if key in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
                info[key] = int(parts[1]) // 1024
    total = info.get("MemTotal", 0)
    avail = info.get("MemAvailable", 0)
    used = total - avail
    pct = (used / total * 100) if total else 0
    swap_total = info.get("SwapTotal", 0)
    swap_used = swap_total - info.get("SwapFree", 0)
    return used, total, pct, swap_used, swap_total


def get_gpus():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
             "--format=csv,noheader,nounits"],
            text=True, timeout=10
        )
        gpus = []
        for line in out.strip().splitlines():
            p = [x.strip() for x in line.split(",")]
            gpus.append({
                "id": p[0], "name": p[1], "util": p[2],
                "mem_used": p[3], "mem_total": p[4],
                "temp": p[5], "power": p[6]
            })
        return gpus
    except Exception:
        return []


def get_docker():
    try:
        out = subprocess.check_output(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            text=True, timeout=10
        )
        return [line.split("\t") for line in out.strip().splitlines() if line]
    except Exception:
        return []


def get_services():
    try:
        out = subprocess.check_output(
            ["systemctl", "--user", "list-units", "--type=service", "--state=running", "--no-pager", "--plain"],
            text=True, timeout=10
        )
        services = []
        for line in out.strip().splitlines():
            if "jarvis" in line.lower() or "lmstudio" in line.lower():
                parts = line.split()
                if parts:
                    services.append(parts[0])
        return services
    except Exception:
        return []


def color_temp(t):
    try:
        t = float(t)
    except (ValueError, TypeError):
        return f"{t}°C"
    if t >= 85:
        return f"\033[1;31m{t:.0f}°C\033[0m"
    elif t >= 75:
        return f"\033[1;33m{t:.0f}°C\033[0m"
    return f"\033[1;32m{t:.0f}°C\033[0m"


def color_pct(v, warn=75, crit=90):
    try:
        v = float(v)
    except (ValueError, TypeError):
        return str(v)
    if v >= crit:
        return f"\033[1;31m{v:.1f}%\033[0m"
    elif v >= warn:
        return f"\033[1;33m{v:.1f}%\033[0m"
    return f"\033[1;32m{v:.1f}%\033[0m"


def display():
    clear()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\033[1;35m{'=' * 60}\033[0m")
    print(f"\033[1;35m  JARVIS M1 DASHBOARD — {now}\033[0m")
    print(f"\033[1;35m{'=' * 60}\033[0m")

    # CPU
    section("CPU — Ryzen 7 5700X3D")
    l1, l5, l15, temp = get_cpu()
    temp_str = color_temp(temp) if temp else "N/A"
    print(f"  Load: {l1:.2f} / {l5:.2f} / {l15:.2f}  |  Temp: {temp_str}")

    # RAM
    section("MEMOIRE")
    used, total, pct, sw_used, sw_total = get_ram()
    print(f"  RAM: {used}/{total} MB ({color_pct(pct, 80, 95)})")
    print(f"  Swap: {sw_used}/{sw_total} MB")

    # GPUs
    section("GPUs (6x NVIDIA)")
    gpus = get_gpus()
    if gpus:
        print(f"  {'ID':>2}  {'Nom':<22} {'Util':>5}  {'VRAM':>12}  {'Temp':>6}  {'Power':>6}")
        for g in gpus:
            mem_pct = float(g["mem_used"]) / float(g["mem_total"]) * 100 if float(g["mem_total"]) > 0 else 0
            print(f"  {g['id']:>2}  {g['name']:<22} {g['util']:>4}%  {g['mem_used']:>5}/{g['mem_total']:>5}MB  {color_temp(g['temp'])}  {g['power']:>5}W")
    else:
        print("  nvidia-smi indisponible")

    # Docker
    section("DOCKER")
    containers = get_docker()
    if containers:
        for c in containers:
            name = c[0] if len(c) > 0 else "?"
            status = c[1] if len(c) > 1 else "?"
            icon = "\033[1;32m●\033[0m" if "Up" in status else "\033[1;31m●\033[0m"
            print(f"  {icon} {name:<30} {status}")
    else:
        print("  Aucun conteneur actif")

    # Services systemd
    section("SERVICES SYSTEMD")
    services = get_services()
    if services:
        for s in services:
            print(f"  \033[1;32m●\033[0m {s}")
    else:
        print("  Aucun service jarvis actif")

    print(f"\n\033[0;37m  Rafraichissement: 5s | Ctrl+C pour quitter\033[0m")


def main():
    try:
        while True:
            display()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\033[0mDashboard arrete.\033[0m")


if __name__ == "__main__":
    main()
