#!/bin/bash
# JARVIS ZRAM Setup — 12GB compresse zstd
set -e

ZRAM_SIZE_MB=12288
ALGO="zstd"

echo "=== JARVIS ZRAM SETUP ==="

# Charger module
sudo modprobe zram num_devices=1 2>/dev/null || true

# Verifier si deja configure
if [ -b /dev/zram0 ] && swapon -s | grep -q zram0; then
    echo "ZRAM deja actif:"
    zramctl
    exit 0
fi

# Reset si existant
if [ -b /dev/zram0 ]; then
    sudo swapoff /dev/zram0 2>/dev/null || true
    echo 1 | sudo tee /sys/block/zram0/reset >/dev/null
fi

# Configurer
echo "$ALGO" | sudo tee /sys/block/zram0/comp_algorithm >/dev/null
echo "${ZRAM_SIZE_MB}M" | sudo tee /sys/block/zram0/disksize >/dev/null
sudo mkswap /dev/zram0
sudo swapon -p 100 /dev/zram0

# Appliquer sysctl
if [ -f "$(dirname "$0")/99-zram-tweaks.conf" ]; then
    sudo sysctl -p "$(dirname "$0")/99-zram-tweaks.conf"
fi

echo ""
echo "=== ZRAM ACTIF ==="
zramctl
echo ""
swapon -s
echo ""
echo "ZRAM setup termine: ${ZRAM_SIZE_MB}MB $ALGO"
