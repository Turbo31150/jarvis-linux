#!/bin/bash
# M1 GPU Setup — Active persistence mode sur toutes les GPUs
set -e

echo "=== JARVIS M1 GPU SETUP ==="

# Verifier nvidia-smi
if ! command -v nvidia-smi &>/dev/null; then
    echo "ERREUR: nvidia-smi non trouve"
    exit 1
fi

# Nombre de GPUs
GPU_COUNT=$(nvidia-smi --query-gpu=index --format=csv,noheader | wc -l)
echo "GPUs detectees: $GPU_COUNT"

# Activer persistence mode sur toutes les GPUs
for i in $(seq 0 $((GPU_COUNT - 1))); do
    echo -n "  GPU $i: "
    sudo nvidia-smi -i "$i" -pm 1 2>&1 | grep -o "Enabled\|already"
done

# Verifier nvidia-persistenced
if systemctl is-active --quiet nvidia-persistenced 2>/dev/null; then
    echo "nvidia-persistenced: actif"
else
    echo "nvidia-persistenced: inactif — tentative de demarrage..."
    sudo systemctl start nvidia-persistenced 2>/dev/null || echo "  (non installe)"
fi

# Afficher etat final
echo ""
echo "=== ETAT FINAL ==="
nvidia-smi --query-gpu=index,name,persistence_mode,temperature.gpu --format=csv
echo ""
echo "GPU setup termine."
