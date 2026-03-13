#!/bin/bash
# JARVIS ZRAM Status
echo "=== ZRAM STATUS ==="
if command -v zramctl &>/dev/null; then
    zramctl
else
    echo "zramctl non disponible"
fi
echo ""
echo "=== SWAP ==="
swapon -s
echo ""
echo "=== MEMOIRE ==="
free -h
