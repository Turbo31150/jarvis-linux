# JARVIS Turmont v12.4 — Orchestrateur IA Multi-Agent Distribue

> Cluster autonome multi-GPU, multi-noeud, multi-moteur IA avec voice control, trading, monitoring et self-healing.

**Machine principale** : M1 "La Creatrice" | **OS** : Ubuntu 22.04 (Kernel 6.17) | **SDK** : Claude Agent SDK v0.1.35

---

## Table des matieres

1. [Architecture globale](#architecture-globale)
2. [Hardware & Cluster](#hardware--cluster)
3. [Installation rapide (1 commande)](#installation-rapide)
4. [Installation detaillee](#installation-detaillee)
5. [Cluster IA — Noeuds & Routage](#cluster-ia--noeuds--routage)
6. [Conteneurs Docker (10 services)](#conteneurs-docker)
7. [Services Systemd (24 unites)](#services-systemd)
8. [MCP — Model Context Protocol (609 handlers)](#mcp--model-context-protocol)
9. [Pipeline Vocal](#pipeline-vocal)
10. [COWORK — 559 scripts autonomes](#cowork--559-scripts-autonomes)
11. [Monitoring & Dashboard](#monitoring--dashboard)
12. [Trading Pipeline](#trading-pipeline)
13. [ZRAM & Optimisation memoire](#zram--optimisation-memoire)
14. [Structure du projet](#structure-du-projet)
15. [Ports reseau](#ports-reseau)
16. [Variables d'environnement](#variables-denvironnement)
17. [Commandes & Aliases](#commandes--aliases)
18. [Troubleshooting](#troubleshooting)
19. [Dependances completes](#dependances-completes)

---

## Architecture globale

```
                          JARVIS TURMONT v12.4
                    Orchestrateur IA Distribue Autonome
                                  |
        +-----------+-------------+-------------+-----------+
        |           |             |             |           |
   Claude SDK   LM Studio    Ollama        Gemini API   OpenClaw
   (Anthropic)  (Local GPU)  (Local+Cloud) (Google)     (Gateway)
        |           |             |             |           |
        +-----+-----+------+-----+------+------+-----+-----+
              |            |            |            |
         Dispatch      Consensus    Routing      Voice
         Engine        Voting       Matrix       Pipeline
              |            |            |            |
        +-----+-----+------+-----+------+------+-----+
        |           |             |             |
   FastAPI WS   Docker        Systemd      Monitoring
   port 9742    10 containers  24 services  GPU/RAM/CPU
        |           |             |             |
   Telegram     Canvas UI     Timers       Dashboard
   Electron     port 18800    Health/GPU   CLI temps reel
```

### Flux de donnees principal

```
Utilisateur (voix/texte/telegram)
    |
    v
[Wake Word "Jarvis"] --> [WhisperFlow STT] --> [Texte]
    |                                              |
    v                                              v
[Command Filter]                          [Intent Classifier]
    |                                              |
    v                                              v
[Dispatch Engine 9 etapes]  <---  [Routing Matrix 17 domaines]
    |
    +---> M1 (qwen3-8b, 65 tok/s)      -- CHAMPION LOCAL
    +---> M2 (deepseek-r1, 44 tok/s)   -- Reasoning
    +---> M3 (deepseek-r1, fallback)    -- Fallback
    +---> OL1 (ollama cloud, 51 tok/s)  -- CHAMPION CLOUD
    +---> GEMINI (flash/pro)            -- Vision/Web/Architecture
    +---> CLAUDE (orchestration pure)   -- Coordinateur
    |
    v
[Quality Gates 6 axes] --> [Self-Improvement] --> [Response]
    |
    v
[TTS edge-tts/Piper] --> Utilisateur
```

---

## Hardware & Cluster

### M1 — "La Creatrice" (Noeud Principal)

| Composant | Detail |
|-----------|--------|
| **CPU** | AMD Ryzen 7 5700X3D — 8 cores / 16 threads @ Performance Governor |
| **RAM** | 46 GB DDR4 |
| **ZRAM** | 12 GB compresse (zstd) — swap en RAM |
| **GPU 0** | NVIDIA RTX 2060 12GB — Inference principale |
| **GPU 1-4** | 4x NVIDIA GTX 1660 SUPER 6GB — Compute distribue |
| **GPU 5** | NVIDIA RTX 3080 10GB — Inference lourde |
| **VRAM Total** | 46 GB (12+6+6+6+6+10) |
| **Stockage** | SSD NVMe |
| **OS** | Ubuntu 22.04 LTS, Kernel 6.17 |
| **Driver NVIDIA** | Avec `NVreg_EnableGpuFirmware=0` (stabilite Turing) |

### Topologie du Cluster

```
        M1 (Principal)                    M2 (Reasoning)
  AMD Ryzen 7 5700X3D              Reseau local 192.168.1.26
  6 GPU, 46GB VRAM                 3 GPU, 24GB VRAM
  Ubuntu 22.04                     LM Studio API :1234
  LM Studio :1234                  deepseek-r1-0528-qwen3-8b
  Ollama :11434                         |
  qwen3-8b (champion)                   |
         |                              |
         +------------ LAN ------------+
         |                              |
        M3 (Fallback)              Cloud (OL1/Gemini)
  Reseau local 192.168.1.113       Ollama cloud models
  LM Studio API :1234              gpt-oss:120b-cloud
  deepseek-r1-0528-qwen3-8b       devstral-2:123b-cloud
                                   Gemini 2.5-flash/pro
                                   Gemini 3-flash/pro
```

---

## Installation rapide

```bash
git clone https://github.com/Turbo31150/jarvis-linux.git
cd jarvis-linux
chmod +x install-jarvis-os.sh
./install-jarvis-os.sh
```

L'installateur execute automatiquement :
1. Verification et installation des dependances systeme
2. Configuration ZRAM (12GB zstd)
3. GPU persistence mode (6 GPUs)
4. Copie des 24 services systemd
5. Activation des timers (health, backup, waves)
6. Configuration des aliases shell
7. Health check final

---

## Installation detaillee

### Pre-requis systeme

```bash
# Paquets systeme
sudo apt update && sudo apt install -y \
    python3 python3-pip python3-venv \
    tmux jq curl wget git \
    lm-sensors util-linux \
    nvidia-driver-535 nvidia-utils-535 \
    portaudio19-dev libsndfile1 \
    espeak-ng ffmpeg

# uv (gestionnaire Python moderne)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node.js 20+ (pour Canvas, Telegram, proxies)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Docker & Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Ollama
curl -fsSL https://ollama.com/install.sh | sh

# LM Studio
# Telecharger depuis https://lmstudio.ai/ et installer manuellement
```

### Installation du projet

```bash
# 1. Cloner
git clone https://github.com/Turbo31150/jarvis-linux.git ~/jarvis-linux
cd ~/jarvis-linux

# 2. Environnement Python
uv venv .venv
source .venv/bin/activate
uv pip install -e .

# 3. Dependances Node.js (Canvas + WhisperFlow)
cd canvas && npm install && cd ..
cd whisperflow && npm install && cd ..

# 4. Configuration
cp .env.example .env
# Editer .env avec vos cles API (voir section Variables d'environnement)

# 5. LM Studio — Charger le modele
# Ouvrir LM Studio, telecharger qwen/qwen3-8b
# Activer le serveur API sur 0.0.0.0:1234

# 6. Ollama — Charger les modeles
ollama pull qwen3:1.7b

# 7. Installer JARVIS-OS (services, timers, aliases, ZRAM)
chmod +x install-jarvis-os.sh
./install-jarvis-os.sh

# 8. Lancer Docker Compose
docker compose -f docker-compose.modular.yml up -d

# 9. Demarrer JARVIS
python main.py           # Mode interactif
python main.py -v        # Mode vocal
python main.py -c        # Mode Commandant (orchestration pure)
python main.py -s        # Statut du cluster
```

---

## Cluster IA — Noeuds & Routage

### Noeuds disponibles

| Noeud | URL | Modele | Role | VRAM | Vitesse | Score |
|-------|-----|--------|------|------|---------|-------|
| **M1** | `127.0.0.1:1234` | qwen3-8b | CHAMPION LOCAL | 46GB | 65 tok/s | 98.4/100 |
| **M1B** | `127.0.0.1:1234` | gpt-oss-20b | Deep local | 46GB | ctx 25k | — |
| **M2** | `192.168.1.26:1234` | deepseek-r1-0528-qwen3-8b | Reasoning | 24GB | 44 tok/s | — |
| **M3** | `192.168.1.113:1234` | deepseek-r1-0528-qwen3-8b | Fallback | 8GB | 5.7s lat | — |
| **OL1 cloud** | `127.0.0.1:11434` | gpt-oss:120b-cloud | CHAMPION CLOUD | cloud | 51 tok/s | 100/100 |
| **OL1 local** | `127.0.0.1:11434` | qwen3:1.7b | Ultra-rapide | local | 84 tok/s | — |
| **GEMINI** | API Google | gemini-2.5-flash/pro | Vision/Web/Archi | cloud | 1s-3s | — |
| **CLAUDE** | API Anthropic | claude-opus/sonnet | Orchestrateur | cloud | — | — |

### Matrice de routage (17 domaines)

Le dispatch engine route automatiquement chaque requete vers les noeuds optimaux :

| Domaine | Noeuds (par priorite) |
|---------|-----------------------|
| `code_generation` | M1, GEMINI, M2 |
| `deep_analysis` | M1, GEMINI, M2 |
| `trading_signal` | OL1, M1, GEMINI |
| `short_answer` | OL1, M1, GEMINI |
| `validation` | M2, GEMINI, M1 |
| `critical` | M1, GEMINI, M2, OL1 |
| `web_research` | GEMINI, OL1, M1 |
| `reasoning` | M1, GEMINI, M2, OL1 |
| `voice_correction` | OL1 |
| `auto_learn` | OL1, GEMINI, M1 |
| `embedding` | GEMINI, M1, OL1 |
| `vision` | GEMINI |
| `code_execution` | GEMINI |
| `grounded_search` | GEMINI, OL1 |
| `consensus` | M1, M2, OL1, M3, GEMINI, CLAUDE |
| `architecture` | GEMINI, CLAUDE, M1, M2 |
| `bridge` | M1, M2, OL1, M3, GEMINI, CLAUDE |

### Routage 5 niveaux pondere

Chaque requete est routee selon 5 criteres combines :

1. **N1 — Poids du noeud** : M1=1.8, GEMINI=1.5, M2=1.4, OL1=1.3, CLAUDE=1.2, M3=1.0
2. **N2 — Poids du domaine** : Probabiliste par categorie (code, math, trading, web...)
3. **N3 — Latence adaptative** : Penalite si latence > seuil (auto-tune)
4. **N4 — Temperature GPU** : Exclusion si >= 85C, penalite si >= 75C
5. **N5 — Auto-learn** : Ajustement continu base sur les performances passees

### Regles critiques

- **JAMAIS** `localhost` → toujours `127.0.0.1` (IPv6 cause 10s de lag)
- **Ollama cloud** : `think: false` OBLIGATOIRE (evite le overhead reasoning)
- **M1 Qwen3** : Prefix `/nothink` OBLIGATOIRE (desactive thinking tokens)
- **M2/M3** : `max_output_tokens >= 2048` (deepseek-r1 a besoin d'espace)
- **GPU** : Warning 75C, Critical 85C → re-routage cascade automatique

---

## Conteneurs Docker

### docker-compose.modular.yml — 10 services

```bash
docker compose -f docker-compose.modular.yml up -d
```

| Conteneur | Image/Build | Port | Role | Dependance |
|-----------|-------------|------|------|------------|
| **jarvis-ws** | Build `./` | 19742:9742 | Hub central WebSocket + API REST | — |
| **vocal-whisper** | `wlk:gpu-voxtral` | 18001:8000 | WhisperFlow STT (GPU, large-v3-turbo) | — |
| **vocal-engine** | Build `./` | — | Pipeline vocal (wake word + commandes) | jarvis-ws |
| **jarvis-pipeline** | Build `./` | — | Dispatch engine + workflow automation | jarvis-ws |
| **jarvis-domino** | Build `./` | — | Cascades d'automatisation (444 actions) | jarvis-ws |
| **openclaw-node** | Build `./openclaw` | 28789:18789 | Gateway OpenClaw (40 agents + 56 dynamic) | jarvis-ws |
| **cowork-engine** | Build `./cowork` | — | Moteur autonome (559 scripts) | jarvis-ws |
| **cowork-dispatcher** | Build `./cowork` | — | Routeur de patterns COWORK | jarvis-ws |
| **domino-mcp** | Build `./` | 18901:8901 | Bridge MCP SSE (Server-Sent Events) | jarvis-ws |
| **jarvis-telegram** | Build `./canvas` | — | Bot Telegram (interface remote) | jarvis-ws |

### Variables d'environnement Docker

Tous les conteneurs partagent :
```yaml
TURBO: /app
WS_URL: ws://jarvis-ws:9742
LM_STUDIO_1_URL: http://host.docker.internal:2234
OLLAMA_URL: http://host.docker.internal:21434
JARVIS_LINUX_ROOT: /app
```

### Volumes persistants

- `./data:/app/data` — Bases de donnees, logs
- `./.env:/app/.env:ro` — Configuration (lecture seule)
- `./src:/app/src` — Code source (dev)
- `hf-cache` — Cache HuggingFace (modeles Whisper)

---

## Services Systemd

### 24 unites (services + timers)

Installation :
```bash
cp system/services/*.service system/services/*.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable jarvis-health.timer jarvis-backup.timer
```

| Service | Description | ExecStart |
|---------|-------------|-----------|
| `jarvis-master` | Boot daemon unifie + watchdog | `scripts/jarvis_unified_boot.py --watch` |
| `jarvis-ws` | Serveur WebSocket central | `python_ws.server` |
| `jarvis-mcp` | Serveur MCP (609 handlers) | `src.mcp_server` |
| `jarvis-pipeline` | Pipeline engine daemon | `scripts/pipeline_engine.py --daemon` |
| `jarvis-voice` | Pipeline vocal (wake word + STT) | `src/voice_engine.py` |
| `jarvis-whisper` | Backend WhisperFlow + API REST | `uvicorn python_ws.server:app :9742` |
| `jarvis-proxy` | Proxy HTTP Canvas | `canvas/direct-proxy.js` |
| `jarvis-telegram` | Bot Telegram | `canvas/telegram-bot.js` |
| `jarvis-openclaw` | Gateway OpenClaw | `openclaw gateway --port 18790` |
| `jarvis-auto-heal` | Self-healing automatique | `scripts/auto_heal.py` |
| `jarvis-gpu-monitor` | Monitoring GPU + alertes | `scripts/gpu_monitor.py` |
| `jarvis-gpu-watcher` | Surveillance continue GPU | `scripts/gpu_watcher.py` |
| `jarvis-dashboard` | Dashboard resilient | `scripts/dashboard_resilient.sh` |
| `jarvis-dashboard-resilient` | Dashboard moniteur | `scripts/dashboard_resilient.sh` |
| `jarvis-lms-guard` | Garde LM Studio (health check) | `scripts/lms_guard.py` |
| `jarvis-watchdog` | Watchdog master | `scripts.openclaw_watchdog` |
| `jarvis-gemini-proxy` | Proxy API Gemini | `gemini-proxy.js` |
| `jarvis-gemini-openai` | Proxy Gemini format OpenAI | `gemini-openai-proxy.js` |
| `jarvis-n8n` | n8n workflow engine | `n8n start` |
| `jarvis-trading-sentinel` | Sentinelle trading | `scripts/trading_sentinel.py` |
| `jarvis-backup` | Backup automatique | `scripts/jarvis-backup.sh` |
| `jarvis-wave@` | Service wave template | `jarvis-wave.sh %i` |
| `lmstudio-bridge` | Bridge TCP 2234 → 1234 | `scripts/lmstudio_bridge.py` |

### Timers

| Timer | Intervalle | Service |
|-------|------------|---------|
| `jarvis-health.timer` | 30 minutes | Health check cluster |
| `jarvis-backup.timer` | Quotidien 03:00 | Backup Git bundles + SQL |
| `jarvis-wave@.timer` | Variable | Waves d'automatisation |

---

## MCP — Model Context Protocol

### Serveur MCP principal : `src/mcp_server.py`
- **609 handlers** enregistres
- **87 outils** exposes via stdio
- **6 282 lignes** de code

### Serveurs MCP complementaires

| Serveur | Port | Outils | Auth |
|---------|------|--------|------|
| Flask MCP | 8080 | 7 (gpu_scale, run_wave, crypto_trade...) | Bearer 1202 |
| Domino MCP | 8901 | SSE bridge | — |
| Voice MCP | 8083 | 3 (listen, command, status) | Bearer jarvis-voice-2026 |
| WhisperFlow MCP | 8082 | 2 (transcribe, status) | Bearer wf-jarvis-2026 |
| Cowork MCP | — | 8 (execute, list, proactive, search, stats) | Interne |

### Categories d'outils MCP

- **Systeme** : bash_run, system_info, gpu_info, network_info, list_processes, kill_process...
- **Fichiers** : read_text_file, write_text_file, search_files, list_folder...
- **Browser** : browser_open, browser_navigate, browser_click, browser_screenshot...
- **LM Studio** : lm_query, lm_models, lm_load_model, lm_unload_model, lm_benchmark...
- **Ollama** : ollama_query, ollama_models, ollama_pull, ollama_status...
- **Trading** : trading_status, trading_positions, trading_execute_signal, trading_backtest...
- **Cluster** : cluster_analytics, consensus, bridge_query, drift_check...
- **Monitoring** : health_summary, metrics_snapshot, diagnostics_run, observability_report...
- **Voice** : speak, voice_analytics...
- **Memoire** : memory_remember, memory_recall, memory_list, brain_learn, brain_suggest...
- **Workflow** : workflow_execute, workflow_list, domino_stats, execute_domino...
- **Cowork** : cowork_execute, cowork_search, cowork_stats...
- **Notifications** : notif_send, notif_history, alert_fire, alert_active...

---

## Pipeline Vocal

### Architecture

```
Microphone
    |
    v
[Porcupine Wake Word "Jarvis"]  (pvporcupine, sensibilite 0.6-0.7)
    |
    v
[Enregistrement 5s]  (sounddevice, 16kHz mono)
    |
    v
[WhisperFlow STT]  (faster-whisper, large-v3-turbo, CUDA)
    |
    v
[Command Filter]  (whitelist/greylist/blacklist securite)
    |
    v
[Voice Correction]  (2 628 alias, etoile.db)
    |
    v
[Dispatch Engine]  --> [Noeud IA optimal]
    |
    v
[Execution]  (MCP tools, bash, API)
    |
    v
[TTS Response]  (edge-tts fr-FR-DeniseNeural +10%)
    |
    v
Haut-parleur
```

### Fichiers du pipeline vocal

| Fichier | Role |
|---------|------|
| `src/voice_engine.py` | Moteur principal (wake word + record + dispatch) |
| `src/voice_hub.py` | Serveur Flask (/voice/audio, /voice/text, /voice/status) |
| `src/wakeword_porcupine.py` | Detection mot-cle Porcupine |
| `src/command_filter.py` | Filtre securite (whitelist/greylist/blacklist) |
| `src/voice_correction.py` | Correction vocale (2 415 lignes, 2 628 alias) |
| `src/tts_engine.py` | Text-to-Speech (espeak-ng / edge-tts) |
| `src/voice_commands.json` | Mapping voix → actions MCP (140+ commandes) |
| `whisperflow/` | Client WebSocket + streaming STT |

### WhisperFlow — STT Streaming

| Fichier | Role |
|---------|------|
| `whisperflow/transcriber.py` | Moteur de transcription Whisper |
| `whisperflow/streaming.py` | WebSocket streaming en temps reel |
| `whisperflow/fast_server.py` | Serveur HTTP rapide |
| `whisperflow/whisperflow_client.py` | Client WebSocket (transcribe_file, transcribe_stream) |
| `whisperflow/whisperflow_mcp.py` | MCP server (port 8082) |
| `openclaw-skills/whisperflow-stt/` | Skill OpenClaw pour integration |

---

## COWORK — 559 scripts autonomes

### Architecture

COWORK est une **usine de developpement autonome** — 559 scripts Python s'executent en continu pour developper, tester, monitorer et ameliorer JARVIS.

```
cowork/
├── cowork_engine.py          # Moteur principal (test-all, gaps, anticipate, improve)
├── cowork_dispatcher.py      # Routeur de patterns
├── cowork_mcp_bridge.py      # Interface MCP (8 outils)
├── deploy_cowork_agents.py   # Gestionnaire de deploiement
├── path_resolver.py          # Resolution dynamique des chemins
└── dev/                      # 559 scripts autonomes
    ├── linux_*.py            # Automatisation Linux
    ├── jarvis_*.py           # Intelligence JARVIS
    ├── ia_*.py               # IA autonome & ML
    ├── auto_*.py             # Automatisation transverse
    ├── cluster_*.py          # Gestion cluster
    ├── voice_*.py            # Pipeline vocal
    ├── dispatch_*.py         # Routing engine
    ├── trading_*.py          # Trading automation
    └── ...                   # 559 scripts au total
```

### Outils MCP COWORK

| Outil | Description |
|-------|-------------|
| `cowork_execute` | Execute un script cowork specifique |
| `cowork_list` | Liste les scripts disponibles |
| `cowork_search` | Recherche par pattern/mot-cle |
| `cowork_stats` | Statistiques d'execution |
| `cowork_proactive_discover` | Decouverte proactive de besoins |
| `cowork_proactive_execute` | Execution proactive |
| `cowork_proactive_status` | Statut des taches proactives |

---

## Monitoring & Dashboard

### Scripts monitoring (`monitoring/`)

| Script | Description | Commande |
|--------|-------------|----------|
| `m1-health.py` | Health baseline (CPU, RAM, 6 GPUs, JSON log) | `jhealth` |
| `m1-gpu-health.py` | GPU detaille (temp, fan, power, pstate) | `jgpu` |
| `jarvis-memory-report.py` | RAM + ZRAM + Swap + VRAM | `jmem` |
| `m1-jarvis-dashboard.py` | Dashboard CLI temps reel (5s refresh) | `jdash` |
| `m1-gpu-setup.sh` | Persistence mode toutes GPUs | `jgpusetup` |
| `m1-jarvis-panel.sh` | Layout tmux 4 panes (htop, nvidia-smi, logs, dashboard) | `jpanel` |
| `m1-health.sh` | Wrapper shell pour health check | — |

### Seuils d'alerte

| Metrique | OK | WARNING | CRITICAL |
|----------|----|---------|----------|
| GPU Temperature | < 75C | 75-85C | > 85C |
| RAM Usage | < 80% | 80-95% | > 95% |
| Swap Usage | < 50% | 50-80% | > 80% |

---

## Trading Pipeline

### Module Trading v2

| Fichier | Role |
|---------|------|
| `scripts/scan_sniper.py` | Scanner MEXC (106K lignes) |
| `scripts/trading_v2/gpu_pipeline.py` | Pipeline GPU trading |
| `scripts/trading_v2/strategies.py` | Strategies trading |
| `scripts/trading_v2/ai_consensus.py` | Consensus multi-IA |
| `scripts/trading_v2/data_fetcher.py` | Collecte de donnees |
| `scripts/trading_sentinel.py` | Sentinelle temps reel |

### Configuration trading (`src/config.py`)

- **Exchange** : MEXC Futures
- **Paires** : BTC, ETH, SOL, SUI, PEPE, DOGE, XRP, ADA, AVAX, LINK (USDT)
- **Levier** : 10x
- **TP** : 0.4% | **SL** : 0.25%
- **Mode** : DRY_RUN=true (simulation par defaut)

---

## ZRAM & Optimisation memoire

### Configuration (`system/zram/`)

```bash
# Installer ZRAM
bash system/zram/setup-zram.sh

# Verifier le statut
bash system/zram/zram-status.sh
```

| Fichier | Role |
|---------|------|
| `setup-zram.sh` | Configure ZRAM 12GB zstd, mkswap, swapon priorite 100 |
| `zram-status.sh` | Affiche etat ZRAM + swap + memoire |
| `99-zram-tweaks.conf` | Sysctl : swappiness=180, vfs_cache_pressure=50, page-cluster=0 |

### Parametres sysctl optimises

```
vm.swappiness = 180          # Favorise ZRAM (en RAM compressée) vs flush disque
vm.vfs_cache_pressure = 50   # Garde le cache VFS plus longtemps
vm.dirty_ratio = 40          # Tolerant sur les pages dirty
vm.dirty_background_ratio = 10
vm.page-cluster = 0          # Pas de read-ahead sur swap (ZRAM est deja en RAM)
```

---

## Structure du projet

```
jarvis-linux/
├── main.py                    # Point d'entree (-i, -v, -c, -o, -s, -k)
├── install-jarvis-os.sh       # Installateur complet (1 commande)
├── .env                       # Configuration (cles API, URLs)
├── pyproject.toml             # Dependances Python (26 packages)
├── docker-compose.yml         # Docker simple (4 services)
├── docker-compose.modular.yml # Docker complet (10 services)
│
├── src/                       # 256 modules Python (94K lignes)
│   ├── config.py              # Noeuds cluster, routage, chemins
│   ├── orchestrator.py        # Orchestration Claude SDK (1073 lignes)
│   ├── mcp_server.py          # 609 MCP handlers (6282 lignes)
│   ├── tools.py               # Outils MCP (2856 lignes)
│   ├── agents.py              # 40+ definitions d'agents (22K lignes)
│   ├── brain.py               # Cerveau IA principal (23K lignes)
│   ├── dispatch_engine.py     # Routing 9 etapes (949 lignes)
│   ├── autonomous_loop.py     # Boucle autonome (879 lignes)
│   ├── voice_engine.py        # Pipeline vocal principal
│   ├── voice_hub.py           # Serveur Flask vocal
│   ├── command_filter.py      # Filtre securite commandes
│   ├── wakeword_porcupine.py  # Detection wake word
│   ├── tts_engine.py          # Text-to-Speech
│   ├── domino_pipelines.py    # 444 cascades (6358 lignes)
│   ├── domino_executor.py     # Executeur cascades (1831 lignes)
│   ├── commander.py           # Classification taches
│   ├── commands.py            # Commandes vocales
│   ├── database.py            # Acces SQLite (785 lignes)
│   ├── gemini_provider.py     # Provider Google Gemini
│   ├── cluster_startup.py     # Demarrage cluster (820 lignes)
│   └── ...                    # 230+ autres modules
│
├── scripts/                   # 132 scripts d'automatisation
│   ├── jarvis_unified_boot.py # Boot daemon (60K lignes)
│   ├── pipeline_engine.py     # Pipeline engine (57K lignes)
│   ├── lmstudio_bridge.py     # Bridge TCP 2234→1234
│   ├── lms_guard.py           # Garde LM Studio (health + backoff)
│   ├── auto_heal_daemon.py    # Self-healing (39K lignes)
│   ├── system_audit.py        # Audit systeme (38K lignes)
│   ├── scan_sniper.py         # Scanner trading (106K lignes)
│   └── trading_v2/            # Trading v2 (strategies, GPU pipeline)
│
├── cowork/                    # Pipeline autonome
│   ├── cowork_engine.py       # Moteur (test, gaps, anticipate, improve)
│   ├── cowork_dispatcher.py   # Routeur de patterns
│   ├── cowork_mcp_bridge.py   # Interface MCP
│   └── dev/                   # 559 scripts autonomes
│
├── whisperflow/               # STT streaming
│   ├── transcriber.py         # Moteur Whisper
│   ├── streaming.py           # WebSocket streaming
│   ├── whisperflow_client.py  # Client WS
│   └── whisperflow_mcp.py     # MCP server
│
├── monitoring/                # Supervision M1
│   ├── m1-health.py           # Health check (CPU/RAM/GPU)
│   ├── m1-gpu-health.py       # GPU detaille
│   ├── jarvis-memory-report.py# Memoire (RAM/ZRAM/Swap/VRAM)
│   ├── m1-jarvis-dashboard.py # Dashboard CLI temps reel
│   ├── m1-gpu-setup.sh        # GPU persistence mode
│   └── m1-jarvis-panel.sh     # Layout tmux 4 panes
│
├── canvas/                    # UI Web + Telegram
│   ├── direct-proxy.js        # Proxy HTTP cluster (port 18800)
│   └── telegram-bot.js        # Bot Telegram
│
├── electron/                  # Application desktop (29 pages)
│
├── openclaw-skills/           # Skills OpenClaw
│   └── whisperflow-stt/       # Skill STT WhisperFlow
│
├── system/
│   ├── services/              # 24 fichiers .service + .timer
│   ├── zram/                  # Config ZRAM (setup, status, sysctl)
│   └── zshrc-jarvis.sh        # Aliases shell
│
├── python_ws/                 # Serveur WebSocket FastAPI
├── tests/                     # 308 fichiers de test (2241 fonctions)
├── docs/                      # Documentation (30+ fichiers)
├── knowledge/                 # Base de connaissances
├── plugins/                   # Systeme de plugins
├── ansible/                   # Playbooks Ansible
└── core/                      # Architecture core + memoire
```

---

## Ports reseau

| Port | Service | Protocole | Acces |
|------|---------|-----------|-------|
| **1234** | LM Studio API (M1) | HTTP REST | Local |
| **2234** | LM Studio Bridge (Docker) | TCP | Docker → Host |
| **8080** | Flask MCP Server | HTTP JSON-RPC | Bearer 1202 |
| **8082** | WhisperFlow MCP | HTTP JSON-RPC | Bearer wf-jarvis-2026 |
| **8083** | Voice MCP | HTTP JSON-RPC | Bearer jarvis-voice-2026 |
| **8901/18901** | Domino MCP Bridge (SSE) | HTTP SSE | Interne |
| **9742/19742** | JARVIS WebSocket + REST API | WS + HTTP | Local/Docker |
| **11434** | Ollama API | HTTP REST | Local |
| **18001** | WhisperFlow STT (Docker) | HTTP | Docker |
| **18789/28789** | OpenClaw Gateway | HTTP | Local/Docker |
| **18790** | OpenClaw Gateway (systemd) | HTTP | Local |
| **18800** | Canvas Proxy UI | HTTP | Local |

### Ports cluster reseau

| Port | Machine | Service |
|------|---------|---------|
| `192.168.1.26:1234` | M2 | LM Studio API |
| `192.168.1.113:1234` | M3 | LM Studio API |

---

## Variables d'environnement

### `.env` — Configuration requise

```bash
# === OBLIGATOIRE ===
ANTHROPIC_API_KEY=sk-ant-...        # Cle API Claude (console.anthropic.com)

# === CLUSTER IA ===
LM_STUDIO_1_URL=http://127.0.0.1:1234        # M1 (local)
LM_STUDIO_2_URL=http://192.168.1.26:1234     # M2 (LAN)
LM_STUDIO_3_URL=http://192.168.1.113:1234    # M3 (LAN)
LM_STUDIO_DEFAULT_MODEL=qwen/qwen3-8b       # Modele par defaut
OLLAMA_URL=http://127.0.0.1:11434            # Ollama local

# === TRADING (optionnel) ===
MEXC_API_KEY=                       # MEXC Futures API
MEXC_SECRET_KEY=                    # MEXC Secret
DRY_RUN=true                       # true = simulation, false = ordres reels

# === TELEGRAM (optionnel) ===
TELEGRAM_TOKEN=                     # Bot token (@BotFather)
TELEGRAM_CHAT=                      # Chat ID

# === VOICE (optionnel) ===
PV_ACCESS_KEY=                      # Picovoice Porcupine (wake word)
WAKEWORD_PATH=                      # Chemin vers .ppn
HF_TOKEN=                           # HuggingFace (modeles Whisper)
```

---

## Commandes & Aliases

### Modes de lancement

```bash
python main.py                     # Mode interactif (REPL)
python main.py -i                  # Mode interactif (REPL)
python main.py -c                  # Mode Commandant (Claude = orchestrateur pur)
python main.py -v                  # Mode vocal (Wake Word + STT)
python main.py -k                  # Mode clavier (hybride)
python main.py -o                  # Mode Ollama cloud (gratuit, web + sub-agents)
python main.py -o glm-5:cloud     # Ollama avec modele specifique
python main.py -s                  # Statut du cluster
python main.py "<prompt>"          # Requete unique
```

### Aliases shell (`source system/zshrc-jarvis.sh`)

| Alias | Commande | Description |
|-------|----------|-------------|
| `jhealth` | `python3 monitoring/m1-health.py` | Health check rapide |
| `jgpu` | `python3 monitoring/m1-gpu-health.py` | Statut GPU detaille |
| `jmem` | `python3 monitoring/jarvis-memory-report.py` | Rapport memoire |
| `jdash` | `python3 monitoring/m1-jarvis-dashboard.py` | Dashboard temps reel |
| `jpanel` | `bash monitoring/m1-jarvis-panel.sh` | Panel tmux 4 panes |
| `jzram` | `bash system/zram/zram-status.sh` | Statut ZRAM |
| `jstatus` | `systemctl --user ... \| grep jarvis` | Services actifs |
| `jtimers` | `systemctl --user list-timers \| grep jarvis` | Timers actifs |
| `jlogs` | `journalctl --user -u jarvis-* -f` | Logs temps reel |
| `jlm` | `curl http://127.0.0.1:1234/api/v1/models` | Modeles LM Studio |
| `jws` | `curl http://127.0.0.1:9742/health` | Health WebSocket |
| `jclaw` | `curl http://127.0.0.1:28789/health` | Health OpenClaw |
| `jdocker` | `docker ps --format table` | Conteneurs Docker |
| `jnv` | `nvidia-smi --query-gpu=...` | GPU rapide |
| `jgpusetup` | `sudo bash monitoring/m1-gpu-setup.sh` | Persistence GPU |

---

## Troubleshooting

| Symptome | Cause | Solution |
|----------|-------|----------|
| M2/M3 TIMEOUT | `max_output_tokens` trop bas pour deepseek-r1 | Minimum 2048 |
| OL1 OFFLINE | Ollama arrete | `ollama serve` restart |
| Canvas crash | Node.js crash | `node canvas/direct-proxy.js` restart |
| GPU > 75C | Charge thermique | `/thermal`, decharger modeles |
| LM Studio restart loop | Triple cascade services | Verifier `lms_guard.py` backoff (RestartSec=15, max 5/5min) |
| Port 1234 flap | EventEmitter saturation | `autoStartOnLaunch: false` dans LM Studio config |
| Context exceeded | Prompt trop long | Reduire max_output_tokens |
| OpenClaw cron spam | Trop de crons | Max 11 crons actifs |
| CUDA error | GPU crash modele | Restart LM Studio, verifier temperatures |
| Docker cowork fail | Ancien path `../jarvis-cowork` | Deja corrige vers `./cowork` |

---

## Dependances completes

### Python (`pyproject.toml`)

| Package | Version | Usage |
|---------|---------|-------|
| `claude-agent-sdk` | >= 0.1.35 | SDK orchestration Claude |
| `httpx` | >= 0.27.0 | Client HTTP async |
| `python-dotenv` | >= 1.0.0 | Configuration .env |
| `ccxt` | >= 4.0.0 | Trading crypto (MEXC) |
| `textual` | >= 1.0.0 | TUI framework (dashboard) |
| `pystray` | >= 0.19.0 | System tray |
| `pillow` | >= 10.0.0 | Images |
| `keyboard` | >= 0.13.5 | Controle clavier |
| `numpy` | >= 2.0.0 | Calcul numerique |
| `sounddevice` | >= 0.5.0 | Audio I/O (microphone) |
| `fastapi` | >= 0.129.0 | API REST + WebSocket |
| `uvicorn` | >= 0.40.0 | Serveur ASGI |
| `websockets` | >= 16.0 | Protocole WebSocket |
| `openwakeword` | >= 0.6.0 | Detection wake word |
| `edge-tts` | >= 6.1.0 | Text-to-Speech Microsoft |
| `faster-whisper` | >= 1.1.0 | STT Whisper (CUDA) |
| `onnxruntime` | >= 1.24.2 | Runtime modeles ML |
| `scipy` | >= 1.15.3 | Calcul scientifique |
| `datasets` | >= 4.6.1 | Chargement donnees |
| `pytest-asyncio` | >= 1.3.0 | Tests async |

### Node.js

| Package | Usage |
|---------|-------|
| `grunt` | Task runner |
| `grunt-concurrent` | Taches paralleles |
| `grunt-contrib-watch` | File watcher |

### Systeme (apt)

```
python3 python3-pip python3-venv uv
nodejs npm
docker.io docker-compose-plugin
nvidia-driver-535 nvidia-utils-535
tmux jq curl wget git
lm-sensors util-linux
portaudio19-dev libsndfile1
espeak-ng ffmpeg
```

---

## Bases de donnees

| Base | Emplacement | Tables | Lignes | Usage |
|------|-------------|--------|--------|-------|
| `etoile.db` | `data/etoile.db` | 42 | 13.5K | Patterns agents, commandes vocales, dispatch logs |
| `jarvis.db` | `data/jarvis.db` | — | — | Memoire episodique, signaux trading |
| `trading.db` | `projects/trading_v2/database/` | — | — | Historique trades, predictions |

---

## Repos GitHub associes

| Repo | URL | Relation |
|------|-----|----------|
| **jarvis-linux** (principal) | `github.com/Turbo31150/jarvis-linux` | Source de verite |
| JARVIS-CLUSTER | `github.com/Turbo31150/JARVIS-CLUSTER` | Architecture cluster (identique a jarvis-linux) |
| jarvis-cowork | `github.com/Turbo31150/jarvis-cowork` | Scripts autonomes (integre dans cowork/) |
| jarvis-whisper-flow | `github.com/Turbo31150/jarvis-whisper-flow` | STT streaming (integre dans whisperflow/) |

---

*Status : Operational | Architecture : Multi-Agent Distribue Autonome | v12.4 — Mars 2026*
