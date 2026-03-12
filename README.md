# 🤖 JARVIS Turmont — Advanced Multi-Agent IA Cluster (M1 Linux)

## 📊 État du Système & Audit DevOps (Final - 12 Mars 2026)

Ce dépôt constitue le centre névralgique de l'écosystème **JARVIS Turmont**, migré avec succès de Windows vers un environnement **Ubuntu 22.04 (Kernel 6.17)** ultra-optimisé. L'architecture est conçue pour l'autonomie totale, la résilience et l'exploitation maximale du hardware.

---

## 🏗️ Spécifications Matérielles (M1 Node)
- **CPU** : AMD Ryzen 7 5700X3D (16 Threads) @ **Performance Governor**.
- **RAM** : 46GB DDR4.
- **ZRAM** : 12GB compressé (zstd) activé pour la gestion des charges IA massives.
- **VRAM Extension** : Pilote **emuV** compilé et signé (MOK) pour étendre la mémoire GPU sur la RAM.
- **GPU Cluster** : 6 Cartes NVIDIA (RTX 3080, RTX 2060 12GB, 4x GTX 1660 SUPER).
  - **Kernel Patch** : `NVreg_EnableGpuFirmware=0` injecté pour stabiliser le bus PCI et corriger les erreurs de firmware GSP sur l'architecture Turing.

---

## 🔐 Logique d'Authentification & Identité
Le système utilise une gestion centralisée des secrets pour l'orchestration multi-moteur :

1.  **Anthropic Claude Max** : Authentification via Token `sk-ant-oat01...` injecté dans `~/.openclaw/.env` et les profils d'agents. Utilisé pour le raisonnement complexe et l'interface Telegram.
2.  **MCP Root Security** : Les outils système critiques sont protégés par un **Bearer Token (1202)** configuré dans le serveur MCP Flask (Port 8080).
3.  **Telegram Identity** : Le bot est lié exclusivement à l'ID utilisateur **2010747443** (Approuvé via pairing code).
4.  **GitHub Sync** : Authentification persistante via Git Credentials pour la synchronisation automatique du cluster.
5.  **Local IA Auth** : Accès direct aux modèles LM Studio (Port 1234) et Ollama (Port 11434) sans intermédiaire cloud.

---

## 🛠️ Stack Logicielle & Intégrations DevOps

### 1. Orchestration & Intelligence (The Brain)
- **OpenClaw v2026** : Passerelle centrale (Gateway Port 18790). 
  - **Permissions** : Mode **No-Sandbox**, accès FS complet, outils système élevés.
  - **Engine** : Bascule dynamique entre **Claude 3.5 Sonnet** (Cloud) et **LM Studio** (Local).
- **Auto-Debugger** : Agent autonome surveillant les logs système et appliquant des patchs de code via `qwen2.5-32b` (M2).
- **Resource Manager** : Script de monitoring dynamique pour l'auto-tuning des priorités CPU/RAM selon la charge IA.

### 2. Pipeline Interaction (The Voice & Input)
- **Voice Engine** : **EasySpeak** avec réveil vocal court sur le mot-clé "**Jarvis**".
- **STT (Speech-to-Text)** : Intégration native avec **WhisperFlow** (Port 9000) utilisant le modèle `large-v3-turbo`.
- **TTS (Text-to-Speech)** : Moteur **Piper** haute fidélité avec la voix française **Denise**.
- **Audio Feedback** : Réponse confirmée au réveil ("*Je suis là*") et double bip JARVIS.
- **Computer Control** : Pilotage physique du bureau (fenêtres, souris, clavier) via `xdotool` et `wmctrl`.

### 3. Automation & Data (Domino)
- **Domino Pipelines** : 405 cascades d'actions migrées de Windows (PowerShell) vers **Linux Bash natif**.
- **MCP Bridge** : Serveur Flask (Port 8080) exposant les outils système en mode ROOT.

---

## 🛡️ Sécurité & DevOps
- **Privilèges** : Utilisateur `turbo` en mode `NOPASSWD: ALL` (Sudoers).
- **Access Control** : AppArmor désactivé, `chmod -R 777` sur les répertoires projets.
- **Kernel Tunables** : `dmesg_restrict`, `kptr_restrict` et `perf_event_paranoid` mis à 0.
- **Backup Strategy** : Sauvegarde automatique Git Bundles + SQL Dumps dans `/backups`.

---

## ⌨️ Dashboard & Commandes Utiles
- `ostatus` : Vérification de la Gateway OpenClaw.
- `jarvis-voice` : Redémarrage du pipeline vocal.
- `jdash` : Dashboard tmux temps réel.
- `jdictate "[msg]"` : Simulation de saisie clavier via voix/cli.
- `m1-boost` : Activation forcée du hardware au maximum.

---
*Status : Operational | Architecture : DevOps Multi-Agent | Powered by Gemini CLI*
