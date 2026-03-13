#!/usr/bin/env python3
"""M1 GPU Health — Score OK/WARNING/CRITICAL par GPU, log JSON."""
import json
import subprocess
import os
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent / "gpu.log"
WARN_TEMP = 80
CRIT_TEMP = 90


def check_gpus():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,fan.speed,power.draw,pstate",
             "--format=csv,noheader,nounits"],
            text=True, timeout=10
        )
    except Exception as e:
        return [{"error": str(e)}]

    gpus = []
    for line in out.strip().splitlines():
        p = [x.strip() for x in line.split(",")]
        temp = float(p[5])
        status = "OK" if temp < WARN_TEMP else ("WARNING" if temp < CRIT_TEMP else "CRITICAL")
        gpus.append({
            "id": int(p[0]), "name": p[1],
            "util_pct": int(p[2]),
            "mem_used_mb": int(p[3]), "mem_total_mb": int(p[4]),
            "temp_c": temp,
            "fan_pct": p[6] if p[6] != "[N/A]" else None,
            "power_w": float(p[7]) if p[7] != "[N/A]" else None,
            "pstate": p[8],
            "status": status,
        })
    return gpus


def main():
    gpus = check_gpus()
    report = {"timestamp": datetime.now().isoformat(), "gpus": gpus}

    criticals = [g for g in gpus if g.get("status") == "CRITICAL"]
    warnings = [g for g in gpus if g.get("status") == "WARNING"]

    if criticals:
        report["overall"] = "CRITICAL"
        print(f"CRITICAL: {len(criticals)} GPU(s) > {CRIT_TEMP}°C !")
    elif warnings:
        report["overall"] = "WARNING"
        print(f"WARNING: {len(warnings)} GPU(s) > {WARN_TEMP}°C")
    else:
        report["overall"] = "OK"
        print("Toutes les GPUs OK")

    print(json.dumps(report, indent=2, ensure_ascii=False))

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(report, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
