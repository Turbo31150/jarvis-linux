#!/bin/bash
# 🚀 LM Studio Auto-Boot Script for JARVIS M1

# 1. Attendre que la session graphique soit prête
sleep 10

# 2. Lancer l'interface graphique en mode discret
export DISPLAY=:1
/usr/bin/lm-studio --no-sandbox --disable-gpu &

# 3. Démarrer le serveur API local (Port 1234)
# On attend un peu que le coeur soit initialisé
sleep 15
/home/turbo/.lmstudio/bin/lms server start

# 4. Charger les modèles prioritaires (Champion)
# On charge le modele Qwen3 8B sur le cluster local
/home/turbo/.lmstudio/bin/lms load qwen3-8b --gpu=max

echo "[LM-STUDIO] Boot Séquence Terminée."
