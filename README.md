# 🤖 JARVIS Turmont — Linux M1 Cluster (Ubuntu 22.04)

Bienvenue dans l'écosystème **JARVIS Turmont**, un cluster IA multi-agent ultra-performant orchestré sur Ubuntu 22.04. Ce projet a été migré depuis Windows et optimisé pour exploiter 100% des ressources matérielles.

## 🚀 Spécifications Matérielles (M1)
- **CPU** : AMD Ryzen 7 5700X3D (Boost Performance Governor + PBO Curve -20)
- **RAM** : 46 Go DDR4
- **GPUs (6 Cartes)** : 
  - 4x NVIDIA GTX 1660 SUPER
  - 1x NVIDIA RTX 2060 12GB
  - 1x NVIDIA RTX 3080 10GB
- **Stockage** : SSD NVMe haute performance

## 🛠️ Installation & Architecture (Mise à jour 12/03/2026)

### 1. Cœur du Système (Backends)
- **OpenClaw (v2026)** : Interface principale (Gateway port 18790). Configurée en mode **No-Sandbox / Root Access**.
- **MCP Flask Server** : Serveur de tools JARVIS tournant sur le port 8080 avec accès ROOT complet.
- **WebSocket Server** : Communication cluster temps réel sur le port 9742.
- **LM Studio (M2/LMT2)** : Modèles locaux déportés (qwen2.5-32b) via API compatible OpenAI.

### 2. Contrôle Vocal & Audio
- **Wake Word** : "Hey Jarvis" via **EasySpeak** (intégré nativement).
- **STT** : WhisperFlow WebSocket.
- **TTS** : Piper (vocal fr_FR-denise-medium).
- **Computer Control** : Pilotage du bureau (fenêtres, souris, clavier) via `xdotool` et `wmctrl`.

### 3. Optimisations JARVIS OS (Le "Hacker Mode")
- **VRAM Étendue (emuV)** : Extension de la VRAM GPU via la RAM système (Signature MOK prête).
- **ZRAM Agressif** : 12 Go de RAM compressée (ZSTD) pour éviter les crashs OOM.
- **NVIDIA Fix** : Désactivation du firmware GSP (`NVreg_EnableGpuFirmware=0`) pour stabiliser les 6 GPUs.
- **Permissions Absolues** : Sudoers NOPASSWD, Chmod 777 global, AppArmor désactivé.

## 🧩 Composants Rajoutés & Inclus
- **Auto-Debugger Agent** : Script Python surveillant les logs et corrigeant le code automatiquement via LM Studio.
- **Resource Manager** : Monitoring et auto-tuning dynamique de la charge RAM/VRAM.
- **Domino Pipelines Linux** : 405 pipelines d'actions cascades portés de PowerShell vers Bash natif.
- **CI/CD Local** : Scripts `jarvis_ci.sh` et `jarvis_preflight_check.sh` pour validation 100% verte.

## 📊 Réglages & Paramètres Data
- **Base de données** : SQLite unifiée dans `data/` (etoile.db, agent_memory.db, etc.).
- **Authentification** : Anthropic Claude 3.5 Sonnet (API Key Claude Max injectée).
- **Telegram** : Bot JARVIS couplé (User ID 2010747443 approuvé).
- **Systemd Targets** : `jarvis-cluster.target` pour un démarrage unifié de tous les services.

## ⌨️ Alias Utiles (ZSH)
- `ostatus` : Vérifier la santé d'OpenClaw.
- `jarvis-voice` : Relancer l'écoute vocale.
- `m1-boost` : Forcer le CPU en mode Performance.
- `jdash` : Lancer le dashboard tmux.
- `wave[1-6]` : Lancer les vagues JARVIS.

---
*Status : 100% Opérationnel | Mode : Full Authorizer | Engine : Gemini CLI & Claude Code*
