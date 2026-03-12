# 🤖 JARVIS Turmont — DevOps Multi-Agent Cluster (M1 Linux)

## 📊 Audit Système Global (12 Mars 2026)
Le système a été entièrement migré vers une architecture **Root-Centric** ultra-performante sur Ubuntu 22.04. Toutes les barrières de permissions ont été levées pour permettre une orchestration IA sans friction.

### 🏗️ Infrastructure & Hardware
- **CPU Governance** : AMD Ryzen 7 5700X3D @ Performance Mode (PBO Curve -20).
- **Memory Stack** : 
  - 46GB RAM Physique.
  - **ZRAM** : 12GB compressé (zstd) @ Priorité 100.
  - **Extension VRAM (emuV)** : Prêt pour le déploiement (MOK Signature générée).
- **GPU Cluster (6 Nodes)** : 
  - 1x RTX 3080 | 1x RTX 2060 (12GB) | 4x GTX 1660 SUPER.
  - **Fix Appliqué** : Désactivation GSP Firmware (`NVreg_EnableGpuFirmware=0`) pour stabiliser le bus PCI 07:00.0.
  - **Persistence** : Activée sur tous les nœuds.

---

## 🛠️ Stack Logicielle & Intégrations

### 1. Intelligence & Agents (The Brain)
- **OpenClaw v2026** : Interface Gateway (Port 18790). 
  - **Auth** : Anthropic Claude 3.5 Sonnet (Claude Max).
  - **Permissions** : No-Sandbox, Full FS Access, Elevated Tools.
- **LM Studio (M1/M2)** : Backend local (Port 1234). Modèle actuel : `gpt-oss-20b`.
- **Auto-Debugger** : Agent autonome surveillant les logs système et appliquant des patchs de code via `qwen2.5-32b` (M2).
- **Resource Manager** : Monitoring dynamique CPU/RAM/VRAM avec auto-tuning.

### 2. Pipeline Vocal (The Voice)
- **Voice Engine** : EasySpeak (Wake word : "**Jarvis**").
- **STT (Speech-to-Text)** : Whisper (Forcé en mode CPU pour résilience totale).
- **TTS (Text-to-Speech)** : Piper avec la voix française **Denise**.
- **Interaction** : Réponse personnalisée au réveil ("*Je suis là*").
- **Computer Control** : Pilotage complet du bureau (fenêtres, souris, clavier) via `xdotool` et `wmctrl`.

### 3. Automation & Data (Domino)
- **Domino Pipelines** : 405 cascades d'actions migrées de Windows (PowerShell) vers **Linux Bash natif**.
- **MCP Bridge** : Serveur Flask (Port 8080) exposant les outils système en mode ROOT.
- **WebSocket Hub** : Bus de communication cluster (Port 9742).

---

## 🛡️ Sécurité & DevOps
- **Privilèges** : Utilisateur `turbo` en mode `NOPASSWD: ALL` (Sudoers).
- **Firewall** : Désactivé (UFW off) pour le cluster local.
- **Access Control** : AppArmor désactivé, `chmod -R 777` sur les répertoires projets.
- **Observabilité** : 
  - `jarvis_ci.sh` : Pipeline de validation qualité.
  - `jarvis_preflight_check.sh` : Rapport de santé cluster (100% Vert).
- **Backup Strategy** : Sauvegarde automatique Git Bundles + SQL Dumps dans `/backups`.

---

## ⌨️ Commandes Rapides (Quick Start)
- `jarvis-voice` : Redémarrer le système vocal.
- `ostatus` : Statut détaillé de l'assistant OpenClaw.
- `jdictate "[texte]"` : Dictée vocale assistée par clavier.
- `m1-boost` : Pousser le matériel à son maximum.
- `jdash` : Dashboard de monitoring tmux.

---
*Status : Operational | Engine : Gemini-CLI / Claude Code | Revision : 10.6.2*
