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

## 🛠️ Stack Logicielle & Intégrations DevOps

### 1. Orchestration & Intelligence (The Brain)
- **OpenClaw v2026** : Passerelle centrale (Gateway Port 18790/18791).
  - **Permissions** : Mode **No-Sandbox**, accès FS complet, outils système élevés.
  - **Engine** : Hybride entre **Anthropic Claude 3.5 Sonnet** (Cloud) et **LM Studio** (Local).
- **LM Studio (Local Node)** : Backend IA local sur port 1234. Modèle actuel : `gpt-oss-20b`.
- **MCP Flask Server** : Pont de communication Root (Port 8080) exposant les outils système avancés.
- **WebSocket Hub** : Bus de messages temps réel (Port 9742) pour la synchronisation des agents.

### 2. Pipeline Interaction (The Voice & Input)
- **Voice Engine** : **EasySpeak** avec réveil vocal court sur le mot-clé "**Jarvis**".
- **STT (Speech-to-Text)** : Intégration native avec **WhisperFlow** (Port 9000) utilisant le modèle `large-v3-turbo`.
- **TTS (Text-to-Speech)** : Moteur **Piper** haute fidélité avec la voix française **Denise**.
- **Audio Feedback** : Réponse confirmée au réveil ("*Je suis là*") et double bip JARVIS.
- **Computer Control** : Pilotage physique du bureau (fenêtres, souris, clavier) via `xdotool` et `wmctrl`.
  - *Action Spéciale* : "**Jarvis, range mon bureau**" -> Tri intelligent des fichiers et suppression automatique des doublons par hash MD5.

### 3. Agents Autonomes & Monitoring
- **Auto-Debugger** : Agent de maintenance en boucle infinie. Analyse les logs système et auto-corrige le code Python/Systemd via le cluster M2.
- **Resource Manager** : Script de monitoring dynamique pour l'auto-tuning des priorités CPU/RAM selon la charge IA.
- **Domino Pipelines** : 405 pipelines complexes portés intégralement en **Bash Linux natif**.

---

## 🛡️ Politique de Sécurité & Permissions
Le système a été basculé en mode **FULL AUTHORIZER** :
- **Sudoers** : Utilisateur `turbo` configuré en `NOPASSWD: ALL`.
- **FS Access** : Permissions `777` sur les répertoires applicatifs.
- **Security Shields** : AppArmor et UFW désactivés pour une communication fluide entre les nœuds du cluster.
- **Kernel Tunables** : `dmesg_restrict`, `kptr_restrict` et `perf_event_paranoid` mis à 0.

---

## 📂 Gestion des Données & Sauvegardes
- **Bases de Données** : SQLite unifié dans `data/` avec backups automatiques horodatés dans `/backups/sql/`.
- **Git Strategy** : Sauvegardes par **Git Bundles** (Snapshots complets de l'historique local) et synchronisation vers GitHub.
- **Environnement** : Configuration `.env` et `.zshrc` sauvegardée et injectée pour persistance après reboot.

---

## ⌨️ Dashboard & Commandes Utiles
- `ostatus` : Vérification de la Gateway OpenClaw.
- `jarvis-voice` : Redémarrage du pipeline vocal.
- `jdash` : Dashboard tmux temps réel.
- `jdictate "[msg]"` : Simulation de saisie clavier via voix/cli.
- `m1-boost` : Activation forcée du hardware au maximum.

---
*Status : Operational | Architecture : DevOps Multi-Agent | Powered by Gemini CLI*
