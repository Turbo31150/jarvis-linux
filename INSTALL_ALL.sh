#!/bin/bash
# 🚀 JARVIS LINUX - MASTER RECOVERY SCRIPT (A to Z)
# Ce script réinstalle tout l'écosystème sur un Ubuntu 22.04 vierge.

set -e

echo "--- 1. MISE À JOUR SYSTÈME & DÉPENDANCES ---"
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y ffmpeg alsa-utils pulseaudio libportaudio2 python3-dev jq curl tmux git sqlite3 build-essential

echo "--- 2. INSTALLATION DOCKER & NVIDIA RUNTIME ---"
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

echo "--- 3. INSTALLATION NODE.JS 22 & PNPM ---"
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo npm install -g pnpm

echo "--- 4. INSTALLATION PYTHON UV & VENV ---"
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv venv .venv
source .venv/bin/activate
# Réinstallation des dépendances extraites
uv pip install -r temp_requirements.txt
uv pip install openwakeword faster-whisper onnxruntime-gpu --no-deps

echo "--- 5. CONFIGURATION ZRAM & TUNING NOYAU ---"
sudo apt-get install -y zram-tools
echo -e "ALGO=zstd\nSIZE=12288\nPRIORITY=100" | sudo tee /etc/default/zramswap
sudo sysctl -w vm.swappiness=150
sudo sysctl -w vm.vfs_cache_pressure=50
sudo sysctl -w vm.overcommit_memory=1

echo "--- 6. CONFIGURATION OPENCLAW & WHISPER ---"
cd openclaw && pnpm install && pnpm run build && cd ..
cd whisper_streaming_web && sudo docker compose up -d && cd ..

echo "--- 7. DÉPLOIEMENT DES SERVICES SYSTEMD ---"
mkdir -p ~/.config/systemd/user/
cp system/services/*.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable jarvis-whisper jarvis-openclaw jarvis-proxy jarvis-mcp jarvis-voice jarvis-gpu-monitor

echo "--- 8. RESTAURATION DES ALIAS ZSH ---"
cat system/config/zsh_aliases >> ~/.zshrc

echo "✅ RÉINSTALLATION TERMINÉE. Redémarrez le terminal."
