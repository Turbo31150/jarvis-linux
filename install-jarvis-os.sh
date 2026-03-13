#!/bin/bash
# JARVIS-OS Installation Script — M1 La Creatrice
set -e

JARVIS_HOME="$(cd "$(dirname "$0")" && pwd)"
echo "=============================================="
echo "  JARVIS-OS INSTALLER — M1 La Creatrice"
echo "  Source: $JARVIS_HOME"
echo "=============================================="

# 1. Dependances systeme
echo ""
echo "[1/7] Verification des dependances..."
DEPS=(python3 pip3 tmux jq curl sensors zramctl)
MISSING=()
for dep in "${DEPS[@]}"; do
    if ! command -v "$dep" &>/dev/null; then
        MISSING+=("$dep")
    fi
done
if [ ${#MISSING[@]} -gt 0 ]; then
    echo "  Installation: ${MISSING[*]}"
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3 python3-pip tmux jq curl lm-sensors util-linux 2>/dev/null || true
else
    echo "  Toutes les dependances OK"
fi

# 2. ZRAM
echo ""
echo "[2/7] Configuration ZRAM..."
if swapon -s | grep -q zram; then
    echo "  ZRAM deja actif"
else
    bash "$JARVIS_HOME/system/zram/setup-zram.sh" || echo "  ZRAM setup echoue (non critique)"
fi

# 3. GPU persistence
echo ""
echo "[3/7] GPU persistence mode..."
if command -v nvidia-smi &>/dev/null; then
    bash "$JARVIS_HOME/monitoring/m1-gpu-setup.sh" || echo "  GPU setup echoue (non critique)"
else
    echo "  nvidia-smi non disponible — GPU setup ignore"
fi

# 4. Services systemd
echo ""
echo "[4/7] Installation services systemd..."
SYSTEMD_USER="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_USER"
for svc in "$JARVIS_HOME"/system/services/*.service "$JARVIS_HOME"/system/services/*.timer; do
    [ -f "$svc" ] || continue
    name=$(basename "$svc")
    cp "$svc" "$SYSTEMD_USER/$name"
    echo "  Installe: $name"
done
systemctl --user daemon-reload
echo "  daemon-reload OK"

# 5. Activer timers
echo ""
echo "[5/7] Activation des timers..."
for timer in "$SYSTEMD_USER"/*.timer; do
    [ -f "$timer" ] || continue
    name=$(basename "$timer")
    systemctl --user enable "$name" 2>/dev/null || true
    systemctl --user start "$name" 2>/dev/null || true
    echo "  Active: $name"
done

# 6. Aliases
echo ""
echo "[6/7] Configuration aliases..."
SHELL_RC="$HOME/.bashrc"
[ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"
if ! grep -q "zshrc-jarvis.sh" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# JARVIS aliases" >> "$SHELL_RC"
    echo "source $JARVIS_HOME/system/zshrc-jarvis.sh" >> "$SHELL_RC"
    echo "  Aliases ajoutes dans $SHELL_RC"
else
    echo "  Aliases deja configures dans $SHELL_RC"
fi

# 7. Verification
echo ""
echo "[7/7] Verification finale..."
echo ""
echo "  Services actifs:"
systemctl --user list-units --type=service --state=running --no-pager | grep -i jarvis | head -10 || echo "    (aucun)"
echo ""
echo "  Timers actifs:"
systemctl --user list-timers --no-pager | grep jarvis | head -10 || echo "    (aucun)"
echo ""

# Health check rapide
if [ -f "$JARVIS_HOME/monitoring/m1-health.py" ]; then
    echo "  Health check:"
    python3 "$JARVIS_HOME/monitoring/m1-health.py" 2>/dev/null || echo "    health check echoue"
fi

echo ""
echo "=============================================="
echo "  JARVIS-OS INSTALLE"
echo "  Ouvrez un nouveau terminal ou: source $SHELL_RC"
echo "  Dashboard: jdash | Panel: jpanel | Health: jhealth"
echo "=============================================="
