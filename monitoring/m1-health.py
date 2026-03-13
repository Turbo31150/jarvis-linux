#!/usr/bin/env python3
"""M1 Health Baseline — CPU, RAM, 6 GPUs, log JSON."""
import json
import subprocess
import time
import os
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent
LOG_FILE = LOG_DIR / "health.log"


def get_cpu_info():
    """Charge CPU + température via sensors."""
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
    return {"load_1m": load1, "load_5m": load5, "load_15m": load15, "temp_c": temp}


def get_ram_info():
    """RAM depuis /proc/meminfo."""
    info = {}
    with open("/proc/meminfo") as f:
        for line in f:
            parts = line.split()
            if parts[0] in ("MemTotal:", "MemAvailable:", "MemFree:", "SwapTotal:", "SwapFree:"):
                info[parts[0].rstrip(":")] = int(parts[1]) // 1024  # MB
    return {
        "total_mb": info.get("MemTotal", 0),
        "available_mb": info.get("MemAvailable", 0),
        "used_mb": info.get("MemTotal", 0) - info.get("MemAvailable", 0),
        "swap_total_mb": info.get("SwapTotal", 0),
        "swap_used_mb": info.get("SwapTotal", 0) - info.get("SwapFree", 0),
    }


def get_gpu_info():
    """6 GPUs via nvidia-smi."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
             "--format=csv,noheader,nounits"],
            text=True, timeout=10
        )
        gpus = []
        for line in out.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            temp = float(parts[5])
            status = "OK" if temp < 80 else ("WARNING" if temp < 90 else "CRITICAL")
            gpus.append({
                "id": int(parts[0]), "name": parts[1],
                "util_pct": int(parts[2]), "mem_used_mb": int(parts[3]),
                "mem_total_mb": int(parts[4]), "temp_c": temp,
                "power_w": float(parts[6]) if parts[6] != "[N/A]" else None,
                "status": status,
            })
        return gpus
    except Exception as e:
        return [{"error": str(e)}]


def main():
    report = {
        "timestamp": datetime.now().isoformat(),
        "hostname": os.uname().nodename,
        "cpu": get_cpu_info(),
        "ram": get_ram_info(),
        "gpus": get_gpu_info(),
    }

    # Résumé global
    gpu_statuses = [g.get("status", "UNKNOWN") for g in report["gpus"]]
    if "CRITICAL" in gpu_statuses:
        report["overall"] = "CRITICAL"
    elif "WARNING" in gpu_statuses:
        report["overall"] = "WARNING"
    else:
        report["overall"] = "OK"

    # Stdout
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # Append log
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(report, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
