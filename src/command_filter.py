#!/usr/bin/env python3
"""
Filtre de sécurité pour commandes JARVIS.
Whitelist / Greylist (confirmation) / Blacklist (refusé).
"""

# Commandes toujours autorisées
WHITELIST = [
    "ls", "cat", "head", "tail", "grep", "find", "pwd", "whoami", "date",
    "docker ps", "docker stats", "docker logs",
    "journalctl", "systemctl status", "systemctl list-timers",
    "nvidia-smi", "sensors", "free", "df", "du",
    "python3", "git status", "git log", "git diff",
    "zramctl", "swapon", "htop", "top", "uptime",
    "curl", "wget",
]

# Commandes nécessitant confirmation vocale/textuelle
GREYLIST = [
    "apt", "pip install", "pip uninstall",
    "rm", "rmdir", "mv",
    "systemctl stop", "systemctl restart", "systemctl start",
    "systemctl enable", "systemctl disable",
    "reboot", "shutdown", "poweroff",
    "docker stop", "docker rm", "docker rmi",
    "git push", "git reset", "git checkout",
    "kill", "pkill", "killall",
    "chmod", "chown",
    "sudo",
]

# Commandes toujours refusées
BLACKLIST = [
    "rm -rf /", "rm -rf /*", "rm -rf ~",
    "dd if=", "mkfs", "fdisk", "parted",
    ":(){ :|:& };:",  # fork bomb
    "wget | sh", "curl | sh", "curl | bash",
    "> /dev/sda", "shred",
]


def filter_command(cmd: str) -> dict:
    """Analyse une commande et retourne son statut de sécurité.

    Returns:
        dict avec keys: allowed (bool), needs_confirm (bool), reason (str)
    """
    cmd_stripped = cmd.strip()

    # Vérifier blacklist en premier
    for pattern in BLACKLIST:
        if pattern in cmd_stripped:
            return {
                "allowed": False,
                "needs_confirm": False,
                "reason": f"BLOQUÉ : commande dangereuse détectée ({pattern})"
            }

    # Vérifier greylist (confirmation requise)
    for pattern in GREYLIST:
        if cmd_stripped.startswith(pattern) or f" {pattern}" in cmd_stripped:
            return {
                "allowed": True,
                "needs_confirm": True,
                "reason": f"Confirmation requise : {pattern} détecté"
            }

    # Vérifier whitelist
    for pattern in WHITELIST:
        if cmd_stripped.startswith(pattern):
            return {
                "allowed": True,
                "needs_confirm": False,
                "reason": "Commande autorisée"
            }

    # Par défaut : autoriser avec confirmation
    return {
        "allowed": True,
        "needs_confirm": True,
        "reason": "Commande inconnue, confirmation requise"
    }


if __name__ == "__main__":
    # Tests
    tests = [
        "ls -la",
        "nvidia-smi",
        "rm -rf /",
        "sudo systemctl restart docker",
        "apt install htop",
        "python3 health.py",
    ]
    for cmd in tests:
        r = filter_command(cmd)
        status = "BLOQUÉ" if not r["allowed"] else ("CONFIRM" if r["needs_confirm"] else "OK")
        print(f"[{status}] {cmd} → {r['reason']}")
