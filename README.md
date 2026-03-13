# JARVIS Turmont v12.4 — Orchestrateur IA Multi-Agent Distribue

> Cluster autonome multi-GPU, multi-noeud, multi-moteur IA avec voice control, trading, monitoring et self-healing.

**Machine principale** : M1 "La Creatrice" | **OS** : Ubuntu 24.04.4 LTS (Kernel 6.17.0-14-generic PREEMPT_DYNAMIC) | **SDK** : Claude Agent SDK v0.1.35

---

## Table des matieres

1. [Architecture globale](#architecture-globale)
2. [Schemas & Workflows detailles](#schemas--workflows-detailles)
3. [Environnement Linux & Modifications OS](#environnement-linux--modifications-os)
4. [Hardware & Cluster](#hardware--cluster)
5. [Installation rapide (1 commande)](#installation-rapide)
6. [Installation detaillee](#installation-detaillee)
7. [Cluster IA — Noeuds & Routage](#cluster-ia--noeuds--routage)
8. [Conteneurs Docker (10 services)](#conteneurs-docker)
9. [Services Systemd (24 unites)](#services-systemd)
10. [MCP — Model Context Protocol (609 handlers)](#mcp--model-context-protocol)
11. [Pipeline Vocal](#pipeline-vocal)
12. [COWORK — 559 scripts autonomes](#cowork--559-scripts-autonomes)
13. [Monitoring & Dashboard](#monitoring--dashboard)
14. [Trading Pipeline](#trading-pipeline)
15. [ZRAM & Optimisation memoire](#zram--optimisation-memoire)
16. [Structure du projet](#structure-du-projet)
17. [Ports reseau](#ports-reseau)
18. [Variables d'environnement](#variables-denvironnement)
19. [Commandes & Aliases](#commandes--aliases)
20. [Troubleshooting](#troubleshooting)
21. [Dependances completes](#dependances-completes)
22. [Suggestions & Roadmap](#suggestions--roadmap)

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

## Schemas & Workflows detailles

### Schema 1 — Interconnexion Docker (10 conteneurs)

```
                          ┌─────────────────────────────────────────┐
                          │           HOST (M1 La Creatrice)        │
                          │                                         │
                          │  LM Studio :1234    Ollama :11434       │
                          │  Flask MCP :8080     Voice MCP :8083    │
                          │  WhisperFlow :8082                      │
                          └────────────┬──────────────┬─────────────┘
                                       │ host.docker  │
                ┌──────────────────────┼──────────────┼──────────────────────┐
                │                DOCKER NETWORK (jarvis-net)                 │
                │                                                            │
                │  ┌──────────────┐     ┌──────────────┐                     │
                │  │  jarvis-ws   │◄────│ vocal-engine │                     │
                │  │  :9742 (hub) │     │  (pipeline)  │                     │
                │  │  FastAPI+WS  │     │  wake+STT    │                     │
                │  └──────┬───────┘     └──────────────┘                     │
                │         │                                                  │
                │    ┌────┴────┬──────────┬──────────┬──────────┐            │
                │    │         │          │          │          │            │
                │    ▼         ▼          ▼          ▼          ▼            │
                │ ┌────────┐┌────────┐┌────────┐┌─────────┐┌──────────┐     │
                │ │pipeline││domino  ││openclaw││cowork   ││cowork    │     │
                │ │engine  ││(444    ││node    ││engine   ││dispatcher│     │
                │ │dispatch││actions)││:28789  ││(559 py) ││(router)  │     │
                │ └────────┘└────────┘└────┬───┘└─────────┘└──────────┘     │
                │                          │                                 │
                │ ┌──────────┐  ┌──────────┴──┐  ┌──────────────┐           │
                │ │vocal-    │  │ domino-mcp  │  │ jarvis-      │           │
                │ │whisper   │  │ :8901 (SSE) │  │ telegram     │           │
                │ │:18001 GPU│  │ bridge MCP  │  │ (bot remote) │           │
                │ └──────────┘  └─────────────┘  └──────────────┘           │
                │                                                            │
                └────────────────────────────────────────────────────────────┘

    Flux WS:  vocal-engine ──ws──► jarvis-ws ◄──ws── pipeline/domino/openclaw
    Flux HTTP: conteneurs ──http──► host.docker.internal:1234 (LM Studio)
                            ──http──► host.docker.internal:11434 (Ollama)
```

### Schema 2 — Dispatch Engine : Pipeline 9 etapes

```
    Requete utilisateur (pattern + prompt)
                │
                ▼
    ┌───────────────────────┐
    │  CACHE CHECK (MD5)    │──── HIT ──► Retour immediat (< 1ms)
    │  TTL: 5 min, max: 200 │
    └───────────┬───────────┘
                │ MISS
                ▼
    ┌───────────────────────┐
    │  ETAPE 1: HEALTH      │  Circuit breaker (adaptive_router)
    │  CHECK (Guardian)     │  + Ping M1 LM Studio (:1234)
    │                       │──► Nodes DOWN → liste bypass
    └───────────┬───────────┘
                ▼
    ┌───────────────────────┐
    │  ETAPE 1b: AUTO-LOAD  │  Patterns lourds → charger modele
    │  MODEL (si necessaire)│  architecture → gpt-oss-20b
    │                       │  reasoning → qwq-32b
    └───────────┬───────────┘  consensus → deepseek-r1
                ▼
    ┌───────────────────────┐
    │  ETAPE 2: ROUTE       │  1. Blacklist (M3 exclu de 7 patterns)
    │  SELECTION             │  2. Benchmark preferences (16 patterns)
    │  (adaptive_router)    │  3. Adaptive router (latence/score)
    │                       │  4. Fallback: pattern_agents registry
    └───────────┬───────────┘
                ▼
    ┌───────────────────────┐
    │  ETAPE 3: ENRICHMENT  │  Episodic memory recall (etoile.db)
    │  MEMOIRE EPISODIQUE   │  Ajoute contexte similaire au prompt
    └───────────┬───────────┘
                ▼
    ┌───────────────────────┐
    │  ETAPE 3b: PROMPT     │  Optimisation du prompt
    │  OPTIMIZATION         │  (prefix /nothink, think:false, etc.)
    └───────────┬───────────┘
                ▼
    ┌───────────────────────┐
    │  ETAPE 4: DISPATCH    │  Appel LLM via HTTP
    │  (pattern_agents)     │──► M1/M2/M3/OL1/GEMINI/CLAUDE
    │  timeout: 12s/60s     │
    └───────────┬───────────┘
                │
         ┌──────┴──────┐
         │ ECHEC?      │
         ▼             ▼
    ┌─────────┐   ┌──────────────┐
    │ SUCCESS │   │ ETAPE 4b:    │
    │         │   │ FALLBACK     │  Retry sur noeud alternatif
    └────┬────┘   │ auto_fallback│  (max_retries: 1)
         │        └──────┬───────┘
         │               │
         └───────┬───────┘
                 ▼
    ┌───────────────────────┐
    │  ETAPE 5: QUALITY     │  6 GATES:
    │  GATES (6 axes)       │  ├─ Longueur (min tokens)
    │                       │  ├─ Structure (format attendu)
    │  threshold: 0.3       │  ├─ Pertinence (vs prompt)
    │                       │  ├─ Confiance (auto-eval)
    │                       │  ├─ Latence (vs seuil)
    │                       │  └─ Hallucination (detection)
    └───────────┬───────────┘
                │
         ┌──────┴──────┐
         │ GATE FAIL?  │
         ▼             ▼
    ┌─────────┐   ┌──────────────┐
    │ PASSED  │   │ ETAPE 5b:    │
    │         │   │ QUALITY      │  Re-dispatch sur meilleur noeud
    └────┬────┘   │ RETRY        │  Compare scores, garde le meilleur
         │        └──────┬───────┘
         │               │
         └───────┬───────┘
                 ▼
    ┌───────────────────────┐
    │  ETAPE 6: FEEDBACK    │  Enregistrement dans etoile.db
    │  RECORDING            │  (pattern, node, quality, latency)
    └───────────┬───────────┘
                ▼
    ┌───────────────────────┐
    │  ETAPE 7: EPISODIC    │  Stockage pour recall futur
    │  STORAGE              │  (enrichira les futures requetes)
    └───────────┬───────────┘
                ▼
    ┌───────────────────────┐
    │  ETAPE 8: POST-       │
    │  PROCESSING           │
    │  8a. Log pipeline     │  → dispatch_pipeline_log (SQLite)
    │  8b. Drift detection  │  → orchestrator_v2 (auto-tune)
    │  8c. Router affinity  │  → adaptive_router (mise a jour)
    │  8d. Cache store      │  → cache MD5 (si success)
    │  8e. Event SSE emit   │  → Server-Sent Events (temps reel)
    └───────────┬───────────┘
                ▼
         DispatchResult
    (content, quality, latency, node, gates...)
```

### Schema 3 — Sequence de boot systemd

```
    systemctl --user start jarvis-master.service
                │
                ▼
    ┌───────────────────────┐
    │  jarvis-master        │  jarvis_unified_boot.py --watch
    │  (Boot daemon + WD)   │  60K lignes, orchestration complete
    └───────────┬───────────┘
                │ lance en parallele:
         ┌──────┼──────┬──────┬──────┬──────┐
         ▼      ▼      ▼      ▼      ▼      ▼
    ┌────────┐┌─────┐┌─────┐┌─────┐┌─────┐┌──────────┐
    │jarvis  ││jarv-││jarv-││jarv-││lmstu││jarvis    │
    │-ws     ││is-  ││is-  ││is-  ││dio- ││-gpu-     │
    │:9742   ││mcp  ││voice││proxy││bridg││monitor   │
    │        ││:8080││     ││:1880││:2234││          │
    └───┬────┘└──┬──┘└──┬──┘└─────┘└──┬──┘└──────────┘
        │        │      │             │
        ▼        ▼      ▼             ▼
    ┌────────────────────────────────────────┐
    │  HEALTH TIMERS (apres boot)            │
    │                                        │
    │  jarvis-health.timer    → toutes 30min │
    │  jarvis-wave@1.timer    → toutes 4h    │
    │  jarvis-wave@2.timer    → +10min       │
    │  jarvis-wave@3.timer    → +20min       │
    │  jarvis-wave@4.timer    → +30min       │
    │  jarvis-wave@5.timer    → +40min       │
    │  jarvis-wave@6.timer    → +50min       │
    │  jarvis-cowork@1.timer  → toutes 6h    │
    └────────────────────────────────────────┘
                │
                ▼
    ┌────────────────────────────────────────┐
    │  WATCHDOG (jarvis-master --watch)      │
    │                                        │
    │  Boucle infinie:                       │
    │  1. Verifier que tous les services UP  │
    │  2. Si service DOWN → restart          │
    │  3. Si 3 restarts fails → alerte       │
    │  4. Verifier GPU temperatures          │
    │  5. Verifier RAM/VRAM usage            │
    │  6. Log dans pipeline.db               │
    │  7. Sleep 60s → recommencer            │
    └────────────────────────────────────────┘
```

### Schema 4 — Self-Healing Loop

```
    ┌─────────────────────────────────────────────────────┐
    │                SELF-HEALING ENGINE                   │
    │              (auto_heal_daemon.py 39K L)             │
    └────────────────────────┬────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
    ┌──────────┐       ┌──────────┐       ┌──────────┐
    │ DETECTER │       │ DETECTER │       │ DETECTER │
    │ Service  │       │ GPU      │       │ LM Studio│
    │ down     │       │ temp >85C│       │ crash    │
    └────┬─────┘       └────┬─────┘       └────┬─────┘
         │                  │                   │
         ▼                  ▼                   ▼
    ┌──────────┐       ┌──────────┐       ┌──────────┐
    │DIAGNOSTIQ│       │DIAGNOSTIQ│       │DIAGNOSTIQ│
    │ logs/    │       │ nvidia-  │       │ port     │
    │ journal  │       │ smi      │       │ 1234     │
    └────┬─────┘       └────┬─────┘       └────┬─────┘
         │                  │                   │
         ▼                  ▼                   ▼
    ┌──────────┐       ┌──────────┐       ┌──────────┐
    │ REPARER  │       │ REPARER  │       │ REPARER  │
    │ systemctl│       │ unload   │       │ kill PID │
    │ restart  │       │ models   │       │ + restart│
    │          │       │ re-route │       │ lms_guard│
    └────┬─────┘       └────┬─────┘       └────┬─────┘
         │                  │                   │
         └──────────────────┼───────────────────┘
                            ▼
    ┌─────────────────────────────────────────────────────┐
    │ VERIFIER                                            │
    │ 1. Re-tester le composant repare                    │
    │ 2. Si OK → log succes dans auto_heal.db             │
    │ 3. Si ECHEC → escalade (alerte + tentative #2)      │
    │ 4. Si 3 echecs → circuit breaker OPEN               │
    │ 5. Notification (Telegram si configure)              │
    └─────────────────────────────────────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────────────────────┐
    │ BOUCLE CONTINUE                                     │
    │ Sleep 60s → recommencer (24/7 autonome)             │
    │ Backoff exponentiel: 15s → 30s → 60s → 120s        │
    │ Max 5 restarts par fenetre de 5 min (RestartSec=15) │
    └─────────────────────────────────────────────────────┘
```

### Schema 5 — Pipeline Vocal complet

```
    ┌──────────┐
    │MICROPHONE│ sounddevice 16kHz mono
    └────┬─────┘
         │ flux audio continu
         ▼
    ┌────────────────────────┐
    │  PORCUPINE WAKE WORD   │  pvporcupine, sensibilite 0.6-0.7
    │  Mot-cle: "Jarvis"     │  Modele .ppn personnalise
    │  (wakeword_porcupine)  │
    └────────────┬───────────┘
                 │ detection!
                 ▼
    ┌────────────────────────┐
    │  ENREGISTREMENT 5s     │  Buffer audio PCM
    │  sounddevice record    │  16kHz, 16-bit, mono
    └────────────┬───────────┘
                 │ .wav
                 ▼
    ┌────────────────────────┐
    │  WHISPERFLOW STT       │  faster-whisper large-v3-turbo
    │  (GPU CUDA, conteneur  │  ou local via whisperflow/
    │   vocal-whisper :18001)│
    └────────────┬───────────┘
                 │ texte brut
                 ▼
    ┌────────────────────────┐
    │  VOICE CORRECTION      │  2 628 alias dans etoile.db
    │  (voice_correction.py) │  "met la musique" → "play_music"
    │  2 415 lignes          │  "quel temps" → "weather_check"
    └────────────┬───────────┘
                 │ texte corrige
                 ▼
    ┌────────────────────────┐
    │  COMMAND FILTER        │  Securite 3 niveaux:
    │  (command_filter.py)   │  ├─ WHITELIST: exec directe
    │                        │  ├─ GREYLIST: confirmation user
    │                        │  └─ BLACKLIST: refuse (rm -rf, etc)
    └────────┬──────┬────────┘
             │      │
      commande   prompt libre
      directe        │
         │           ▼
         │    ┌────────────────┐
         │    │ INTENT CLASSIFY│  commander.py
         │    │ → pattern IA   │  (code/trading/web/simple...)
         │    └───────┬────────┘
         │            │
         └──────┬─────┘
                ▼
    ┌────────────────────────┐
    │  DISPATCH ENGINE       │  9 etapes (voir Schema 2)
    │  Route vers M1/M2/    │  Selection optimale du noeud
    │  M3/OL1/GEMINI/CLAUDE │
    └────────────┬───────────┘
                 │ reponse texte
                 ▼
    ┌────────────────────────┐
    │  TTS (Text-to-Speech)  │  Priorite:
    │  (tts_engine.py)       │  1. edge-tts fr-FR-DeniseNeural +10%
    │                        │  2. espeak-ng (fallback offline)
    │                        │  3. Piper (si installe)
    └────────────┬───────────┘
                 │ audio .mp3/.wav
                 ▼
    ┌──────────┐
    │HAUT-     │  mpv/aplay/ffplay
    │PARLEUR   │
    └──────────┘
```

### Schema 6 — Trading Pipeline

```
    ┌─────────────────────────────────────────────────────┐
    │          TRADING PIPELINE v2 (MEXC Futures)          │
    └────────────────────────┬────────────────────────────┘
                             │
                             ▼
    ┌────────────────────────────────────────────────────┐
    │  PHASE 1: DATA COLLECTION (data_fetcher.py)        │
    │                                                    │
    │  10 paires: BTC ETH SOL SUI PEPE DOGE XRP ADA     │
    │             AVAX LINK (tous /USDT)                 │
    │                                                    │
    │  Sources:                                          │
    │  ├─ MEXC API (OHLCV 1m/5m/15m/1h/4h)             │
    │  ├─ Orderbook (depth 20 niveaux)                   │
    │  ├─ Funding rates                                  │
    │  └─ Open Interest                                  │
    └────────────────────────┬───────────────────────────┘
                             ▼
    ┌────────────────────────────────────────────────────┐
    │  PHASE 2: ANALYSE TECHNIQUE (strategies.py)        │
    │                                                    │
    │  Indicateurs:                                      │
    │  ├─ RSI (14), MACD (12,26,9), Bollinger (20,2)    │
    │  ├─ Volume Profile, VWAP                           │
    │  ├─ Support/Resistance (auto-detection)            │
    │  ├─ Patterns (breakout, reversal, continuation)    │
    │  └─ Momentum scoring (multi-timeframe)             │
    └────────────────────────┬───────────────────────────┘
                             ▼
    ┌────────────────────────────────────────────────────┐
    │  PHASE 3: GPU PIPELINE (gpu_pipeline.py)           │
    │                                                    │
    │  Scan parallele sur 6 GPU:                         │
    │  ├─ GPU 0 (RTX 2060): BTC + ETH                   │
    │  ├─ GPU 1-4 (1660S): SOL SUI PEPE DOGE            │
    │  └─ GPU 5 (RTX 3080): XRP ADA AVAX LINK           │
    │                                                    │
    │  scan_sniper.py (106K lignes) — scanner principal  │
    └────────────────────────┬───────────────────────────┘
                             ▼
    ┌────────────────────────────────────────────────────┐
    │  PHASE 4: AI CONSENSUS (ai_consensus.py)           │
    │                                                    │
    │  Vote multi-IA sur chaque signal:                  │
    │  ├─ M1 (qwen3-8b)     → BUY/SELL/HOLD + confiance│
    │  ├─ OL1 (gpt-oss:120b)→ BUY/SELL/HOLD + confiance│
    │  ├─ GEMINI (flash)     → BUY/SELL/HOLD + confiance│
    │  ├─ M2 (deepseek-r1)  → BUY/SELL/HOLD + confiance│
    │  └─ CLAUDE (si actif)  → BUY/SELL/HOLD + confiance│
    │                                                    │
    │  Consensus = vote majoritaire pondere              │
    │  Seuil: >= 3 noeuds d'accord + confiance > 0.7    │
    └────────────────────────┬───────────────────────────┘
                             ▼
    ┌────────────────────────────────────────────────────┐
    │  PHASE 5: EXECUTION (DRY_RUN par defaut)           │
    │                                                    │
    │  Si DRY_RUN=true:                                  │
    │  └─ Log signal + skip execution                    │
    │                                                    │
    │  Si DRY_RUN=false:                                 │
    │  ├─ Ouvrir position MEXC Futures (10x leverage)    │
    │  ├─ Take Profit: +0.4%                             │
    │  ├─ Stop Loss: -0.25%                              │
    │  └─ Position tracker (suivi temps reel)             │
    │                                                    │
    │  trading_sentinel.py — surveillance 24/7            │
    └────────────────────────────────────────────────────┘
```

### Schema 7 — Cycle autonome COWORK

```
    ┌─────────────────────────────────────────────────────┐
    │        COWORK AUTONOMOUS CYCLE (toutes les 6h)      │
    │          Timer: jarvis-cowork@1.timer                │
    └────────────────────────┬────────────────────────────┘
                             │
                             ▼
    ┌────────────────────────────────────────────────────┐
    │  PHASE 1: TEST-ALL                                 │
    │  cowork_engine.py --mode test-all                  │
    │                                                    │
    │  Pour chaque script dans cowork/dev/ (559):        │
    │  ├─ Importer le module                             │
    │  ├─ Executer main() ou run()                       │
    │  ├─ Verifier exit code (0 = OK, 1 = fail)         │
    │  ├─ Capturer stdout/stderr                         │
    │  └─ Log resultat dans etoile.db                    │
    └────────────────────────┬───────────────────────────┘
                             ▼
    ┌────────────────────────────────────────────────────┐
    │  PHASE 2: GAPS (detection de manques)              │
    │  cowork_engine.py --mode gaps                      │
    │                                                    │
    │  Analyse le code JARVIS pour trouver:              │
    │  ├─ Fonctions sans tests                           │
    │  ├─ Modules sans monitoring                        │
    │  ├─ Endpoints sans validation                      │
    │  ├─ Patterns de dispatch sans benchmark            │
    │  └─ Genere une liste de scripts a creer            │
    └────────────────────────┬───────────────────────────┘
                             ▼
    ┌────────────────────────────────────────────────────┐
    │  PHASE 3: ANTICIPATE                               │
    │  cowork_engine.py --mode anticipate                │
    │                                                    │
    │  Utilise l'IA (M1/OL1) pour predire:              │
    │  ├─ Quels composants vont avoir besoin de MAJ     │
    │  ├─ Quels bugs sont probables (drift detection)   │
    │  ├─ Quelles optimisations sont possibles          │
    │  └─ Priorise les actions par impact               │
    └────────────────────────┬───────────────────────────┘
                             ▼
    ┌────────────────────────────────────────────────────┐
    │  PHASE 4: IMPROVE                                  │
    │  cowork_engine.py --mode improve                   │
    │                                                    │
    │  Execute les ameliorations identifiees:            │
    │  ├─ Genere de nouveaux scripts cowork              │
    │  ├─ Ameliore les scripts existants                 │
    │  ├─ Met a jour les benchmarks                      │
    │  ├─ Optimise les routes dispatch                   │
    │  └─ Commit les changements (si auto_commit=true)   │
    └────────────────────────┬───────────────────────────┘
                             │
                             ▼
    ┌────────────────────────────────────────────────────┐
    │  BOUCLE: recommence dans 6h                        │
    │                                                    │
    │  Contraintes:                                      │
    │  ├─ Chaque script DOIT etre stdlib-only (no pip)   │
    │  ├─ Chaque script DOIT avoir self-test             │
    │  ├─ Timeout par script: 30s                        │
    │  └─ Max 559 scripts actifs (auto-prune si > 600)   │
    └────────────────────────────────────────────────────┘
```

### Schema 8 — Consensus multi-IA (vote)

```
                    Requete (pattern: "consensus")
                              │
                              ▼
    ┌─────────────────────────────────────────────────────┐
    │  DISPATCH PARALLELE vers tous les noeuds actifs     │
    │  asyncio.gather(*tasks)                             │
    └────────┬──────┬──────┬──────┬──────┬───────────────┘
             │      │      │      │      │
             ▼      ▼      ▼      ▼      ▼
          ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌──────┐
          │ M1 │ │ M2 │ │ OL1│ │ M3 │ │GEMINI│
          │qwen│ │deep│ │gpt-│ │deep│ │flash │
          │3-8b│ │seek│ │oss │ │seek│ │      │
          └──┬─┘ └──┬─┘ └──┬─┘ └──┬─┘ └──┬───┘
             │      │      │      │      │
             ▼      ▼      ▼      ▼      ▼
    ┌─────────────────────────────────────────────────────┐
    │  COLLECTE DES REPONSES                              │
    │                                                    │
    │  M1:     {"answer": "X", "confidence": 0.85}       │
    │  M2:     {"answer": "X", "confidence": 0.72}       │
    │  OL1:    {"answer": "Y", "confidence": 0.91}       │
    │  M3:     {"answer": "X", "confidence": 0.60}  (*)  │
    │  GEMINI: {"answer": "X", "confidence": 0.88}       │
    │                                                    │
    │  (*) Timeout M3 → poids reduit ou exclu            │
    └────────────────────────┬───────────────────────────┘
                             ▼
    ┌─────────────────────────────────────────────────────┐
    │  VOTE PONDERE                                       │
    │                                                    │
    │  Score(X) = (0.85×1.8)+(0.72×1.4)+(0.60×1.0)      │
    │           + (0.88×1.5) = 1.53+1.01+0.60+1.32 = 4.46│
    │  Score(Y) = (0.91×1.3) = 1.18                      │
    │                                                    │
    │  Poids: M1=1.8, GEMINI=1.5, M2=1.4, OL1=1.3, M3=1│
    │  WINNER: X (4.46 vs 1.18)                          │
    │  Consensus: 4/5 noeuds (80%)                       │
    └────────────────────────┬───────────────────────────┘
                             ▼
    ┌─────────────────────────────────────────────────────┐
    │  RESULT                                             │
    │  answer: "X"                                       │
    │  consensus_rate: 0.80                               │
    │  weighted_score: 4.46                               │
    │  dissenting: ["OL1"]                                │
    │  total_latency: max(latencies) ≈ 5.7s              │
    └─────────────────────────────────────────────────────┘
```

### Schema 9 — Carte des ports reseau

```
    M1 — La Creatrice (127.0.0.1)
    ═══════════════════════════════════════════════════

    PORT    SERVICE              PROTO   AUTH
    ────    ───────              ─────   ────
    1234    LM Studio API        HTTP    -
    2234    LM Studio Bridge     TCP     - (Docker→Host)
    8080    Flask MCP Server     HTTP    Bearer 1202
    8082    WhisperFlow MCP      HTTP    Bearer wf-jarvis-2026
    8083    Voice MCP            HTTP    Bearer jarvis-voice-2026
    8901    Domino MCP (SSE)     HTTP    -
    9742    JARVIS WS + REST     WS/HTTP -
    11434   Ollama API           HTTP    -
    18001   Whisper STT (Docker) HTTP    -
    18789   OpenClaw (Docker)    HTTP    -
    18790   OpenClaw (systemd)   HTTP    -
    18800   Canvas Proxy UI      HTTP    -
    18901   Domino MCP (Docker)  HTTP    -
    19742   JARVIS WS (Docker)   WS/HTTP -
    28789   OpenClaw (Docker→H)  HTTP    -

    ═══════════════════════════════════════════════════
    CLUSTER LAN (192.168.1.0/24)
    ═══════════════════════════════════════════════════

    192.168.1.26:1234    M2 — LM Studio API
    192.168.1.113:1234   M3 — LM Studio API

    ═══════════════════════════════════════════════════
    CLOUD (HTTPS sortant)
    ═══════════════════════════════════════════════════

    api.anthropic.com          Claude API (Anthropic)
    generativelanguage.google  Gemini API (Google)
    futures.mexc.com           MEXC Futures (Trading)
    api.telegram.org           Telegram Bot API
```

### Schema 10 — Flux de donnees et bases SQLite

```
    ┌────────────────────────────────────────────────────────────────┐
    │                   FLUX DE DONNEES JARVIS                      │
    └────────────────────────────────────────────────────────────────┘

    ENTREES                    TRAITEMENT                 STOCKAGE
    ───────                    ──────────                 ────────

    Voix (micro)──────►Voice Engine──────────►┐
                                              │
    Texte (CLI)───────►Orchestrator───────────┤
                                              │
    Telegram──────────►telegram-bot.js────────┤
                                              ▼
    API REST──────────►jarvis-ws :9742───► etoile.db (42 tables)
                                          │  ├─ conversations
                                          │  ├─ dispatch_log
                                          │  ├─ voice_aliases (2628)
                                          │  ├─ quality_gates
                                          │  ├─ agent_patterns (40)
                                          │  ├─ cowork_mappings
                                          │  └─ episodic_memory
                                          │
    GPU sensors───────►gpu_monitor────────► jarvis.db
    CPU/RAM sensors───►health.py──────────│  ├─ health_metrics
    Docker stats──────►dashboard──────────│  ├─ gpu_temperatures
                                          │  └─ system_events
                                          │
    MEXC API──────────►scan_sniper────────► trading.db
    Orderbook─────────►data_fetcher───────│  ├─ signals
    Funding rates─────►strategies─────────│  ├─ positions
                                          │  └─ backtest_results
                                          │
    Cowork scripts────►cowork_engine──────► auto_heal.db
    Self-healing──────►auto_heal_daemon───│  ├─ heal_attempts
                                          │  └─ component_status
                                          │
    Decisions─────────►brain.py───────────► decisions.db
    Audit─────────────►system_audit.py────► audit_trail.db
    Browser───────────►browser tools──────► browser_memory.db
    Scheduler─────────►task pipeline──────► scheduler.db
    Sessions──────────►orchestrator───────► sessions.db

    TOTAL: 35+ fichiers SQLite, ~160 MB combines
    SYMLINK: data/ → core/memory/ (acces unifie)
```

---

## Environnement Linux & Modifications OS

### Systeme d'exploitation

| Element | Detail |
|---------|--------|
| **Distribution** | Ubuntu 24.04.4 LTS "Noble Numbat" |
| **Kernel** | 6.17.0-14-generic PREEMPT_DYNAMIC x86_64 |
| **Init** | systemd (PID 1) |
| **Filesystem** | ext4 sur /dev/sdb2 (915 GB, 639 GB utilises) |
| **Boot** | EFI (/dev/sdb1 vfat) |
| **NVMe** | /dev/nvme0n1p1 (stockage additionnel) |
| **Utilisateur** | `turbo` — NOPASSWD sudoers |

### Stack logicielle installee

| Outil | Version | Role |
|-------|---------|------|
| **Python** | 3.12.3 | Runtime principal |
| **uv** | 0.10.9 | Gestionnaire Python (remplacement pip/venv) |
| **Node.js** | 22.22.1 | Canvas, Telegram, Electron, proxies |
| **Docker** | 29.3.0 | Conteneurisation (10 services) |
| **Ollama** | 0.17.7 | Inference IA locale + cloud |
| **Git** | 2.43.0 | Versioning |
| **NVIDIA Driver** | 590.48.01 | GPU compute (CUDA) |
| **LM Studio** | Latest | Inference locale GPU (llama.cpp backend) |
| **tmux** | Installe | Multiplexeur terminal (panel monitoring) |
| **lm-sensors** | Installe | Capteurs temperature CPU |

### Modifications Kernel & Securite

```bash
# /etc/default/grub — Pas de parametres NVIDIA custom (driver 590 natif)
BOOT_IMAGE=/boot/vmlinuz-6.17.0-14-generic root=UUID=... ro quiet splash

# /etc/modprobe.d/ — NVIDIA DRM modesetting
options nvidia_drm modeset=1
# Preserve video memory on suspend/resume (driver 590)
```

**Modules kernel NVIDIA charges** :
```
nvidia              14766080  (913 dependants)
nvidia_uvm           2142208  (8 dependants)
nvidia_drm            139264  (67 dependants)
nvidia_modeset       1683456  (22 dependants)
```

### Modifications securite systeme

| Parametre | Valeur | Effet |
|-----------|--------|-------|
| `kernel.dmesg_restrict` | **0** | Acces dmesg sans root (debug GPU) |
| `kernel.kptr_restrict` | **0** | Pointeurs kernel visibles (debug) |
| `kernel.perf_event_paranoid` | **0** | Profiling performance sans restriction |
| **AppArmor** | **74 profils enforce** | Actif mais permissif pour JARVIS |
| **Sudoers** | `turbo ALL=(ALL) NOPASSWD:ALL` | Sudo sans mot de passe (fichier `/etc/sudoers.d/jarvis-nopasswd`) |

### Optimisations sysctl actives

```bash
vm.swappiness = 10              # Valeur courante (180 quand ZRAM charges via tweaks)
vm.vfs_cache_pressure = 50      # Garde le cache VFS plus longtemps
vm.dirty_ratio = 40             # Tolerant sur les pages dirty (evite flush disque)
```

### CPU Governor

```bash
# Mode performance permanent (pas de throttling)
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
# → performance
```

### ZRAM actif

```
/dev/zram0  zstd  11.7G (disksize)  5.9G (data)  3.6G (compresse)  priorite 100
/swap.img   file  8.0G              0 (inutilise)                   priorite -2
```
Le swap fichier classique (8GB) n'est jamais utilise — ZRAM a priorite 100 absorbe tout.

### Timers systemd actifs (en production)

| Timer | Intervalle | Derniere execution |
|-------|------------|--------------------|
| `jarvis-health.timer` | Toutes les 30 min | En continu |
| `jarvis-wave@1.timer` | Toutes les 4h | Cycle automatique |
| `jarvis-wave@2.timer` | Toutes les 4h (+10min) | Cascade |
| `jarvis-wave@3.timer` | Toutes les 4h (+20min) | Cascade |
| `jarvis-wave@4.timer` | Toutes les 4h (+30min) | Cascade |
| `jarvis-wave@5.timer` | Toutes les 4h (+40min) | Cascade |
| `jarvis-wave@6.timer` | Toutes les 4h (+50min) | Cascade |
| `jarvis-cowork@1.timer` | Toutes les 6h | Scripts autonomes |

### 15 services systemd en production

```
jarvis-brain.service             JARVIS Self-Improvement Engine
jarvis-dashboard-resilient       JARVIS Resilient Dashboard Monitor
jarvis-gpu-fan                   JARVIS GPU Fan Manager
jarvis-gpu-monitor               JARVIS GPU Monitor & Alerting
jarvis-gpu-watcher               JARVIS GPU Watcher Service
jarvis-lms-guard                 JARVIS LM Studio Health Guard
jarvis-mcp                       JARVIS MCP Flask Server
jarvis-pipeline                  JARVIS Pipeline Engine Daemon
jarvis-proxy                     JARVIS Canvas Proxy
jarvis-resource-manager          JARVIS Resource Manager (RAM/VRAM Auto-Tune)
jarvis-turbo-ws                  JARVIS-TURBO WebSocket Bridge
jarvis-voice                     JARVIS Voice Pipeline v3 (Wake Word & Command)
jarvis-whisper                   JARVIS Whisper (Native)
jarvis-ws                        JARVIS WebSocket Server
lmstudio-bridge                  LM Studio Docker Bridge
```

---

## Hardware & Cluster

### M1 — "La Creatrice" (Noeud Principal)

| Composant | Detail |
|-----------|--------|
| **CPU** | AMD Ryzen 7 5700X3D — 8 cores / 16 threads @ **Performance Governor** |
| **RAM** | 46 GB DDR4 |
| **ZRAM** | 12 GB compresse (zstd, ratio 1.6:1) — swap en RAM priorite 100 |
| **Swap fichier** | 8 GB /swap.img (inutilise, priorite -2) |
| **GPU 0** | NVIDIA RTX 2060 12GB — Inference principale |
| **GPU 1-4** | 4x NVIDIA GTX 1660 SUPER 6GB — Compute distribue |
| **GPU 5** | NVIDIA RTX 3080 10GB — Inference lourde |
| **VRAM Total** | 46 GB (12+6+6+6+6+10) |
| **Stockage** | SSD 915 GB ext4 (/dev/sdb2) + NVMe additionnel |
| **OS** | Ubuntu 24.04.4 LTS, Kernel 6.17.0-14-generic PREEMPT_DYNAMIC |
| **Driver NVIDIA** | 590.48.01 avec `nvidia_drm modeset=1` |
| **Init** | systemd — 15 services JARVIS + 8 timers actifs |

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

Toutes les bases sont en SQLite3 (aucun serveur DB externe).

| Base | Emplacement | Tables | Lignes | Usage |
|------|-------------|--------|--------|-------|
| `etoile.db` | `core/memory/etoile.db` | 42 | 13.5K | Patterns agents, commandes vocales, dispatch logs, cowork mappings |
| `jarvis.db` | `core/memory/jarvis.db` | — | — | Memoire episodique, signaux trading, conversations |
| `trading.db` | `projects/trading_v2/database/` | — | — | Historique trades, predictions |
| `sniper_scan.db` | `core/memory/` | — | — | Scanner trading MEXC |
| `agent_memory.db` | `core/memory/` | — | — | Etat des agents (40+ agents) |
| `decisions.db` | `core/memory/` | — | — | Journal de decisions |
| `scheduler.db` | `core/memory/` | — | — | Planificateur de taches |
| `task_queue.db` | `core/memory/` | — | — | File d'attente des taches |
| `conversations.db` | `core/memory/` | — | — | Historique des dialogues |
| `audit_trail.db` | `core/memory/` | — | — | Piste d'audit systeme |
| `sessions.db` | `core/memory/` | — | — | Sessions utilisateur |
| `browser_memory.db` | `core/memory/` | — | — | Etat navigateur |
| `auto_heal.db` | `core/memory/` | — | — | Tentatives auto-reparation |
| `pipeline.db` | `core/memory/` | — | — | Execution pipelines |

**Total** : 35+ fichiers SQLite, ~160 MB combines.
**Symlink** : `data/ → core/memory/` (acces unifie)

---

## Repos GitHub associes

| Repo | URL | Relation |
|------|-----|----------|
| **jarvis-linux** (principal) | `github.com/Turbo31150/jarvis-linux` | Source de verite |
| JARVIS-CLUSTER | `github.com/Turbo31150/JARVIS-CLUSTER` | Architecture cluster (identique a jarvis-linux) |
| jarvis-cowork | `github.com/Turbo31150/jarvis-cowork` | Scripts autonomes (integre dans cowork/) |
| jarvis-whisper-flow | `github.com/Turbo31150/jarvis-whisper-flow` | STT streaming (integre dans whisperflow/) |

---

## Licence & Credits

- **Auteur** : Turbo31150
- **Machine** : M1 "La Creatrice" — Ubuntu 24.04.4 LTS
- **Kernel** : 6.17.0-14-generic PREEMPT_DYNAMIC
- **IA** : Claude Agent SDK (Anthropic) + LM Studio + Ollama + Gemini
- **GPU** : 6x NVIDIA (RTX 3080 + RTX 2060 12GB + 4x GTX 1660 SUPER) — 46GB VRAM
- **Driver** : NVIDIA 590.48.01, CUDA, nvidia_drm modeset=1

---

## Suggestions & Roadmap

### Ce qui reste a faire

| Priorite | Tache | Statut | Description |
|----------|-------|--------|-------------|
| **P0** | Documentation API REST | A faire | Documenter les 517 endpoints REST de jarvis-ws (Swagger/OpenAPI) |
| **P0** | `.env.example` complet | A faire | Creer un fichier `.env.example` avec toutes les variables documentees |
| **P1** | Tests CI/CD | A faire | GitHub Actions : lint + pytest + build Docker sur chaque push |
| **P1** | Docker multi-arch | A faire | Build ARM64 pour portabilite (Raspberry Pi, Mac M-series) |
| **P1** | Requirements freeze | A faire | Generer `requirements.lock` avec versions exactes (reproductibilite) |
| **P1** | Health endpoint unifie | A faire | `/health` sur jarvis-ws qui agrege tous les composants |
| **P2** | Securite tokens | A faire | Remplacer les Bearer hardcodes (1202, wf-jarvis-2026) par variables .env |
| **P2** | HTTPS/TLS | A faire | Certificats Let's Encrypt si expose sur internet |
| **P2** | Rate limiting | A faire | Limiter les appels MCP/API (protection contre abus) |
| **P2** | Logs centralises | A faire | ELK/Loki/Grafana au lieu de journalctl + fichiers epars |
| **P3** | Dashboard Web | A faire | Remplacer le dashboard CLI par une UI web (React/Svelte) |
| **P3** | Metriques Prometheus | A faire | Exporter les metriques GPU/CPU/latence vers Prometheus |
| **P3** | Backup cloud | A faire | Backup automatique des .db vers S3/B2 (pas seulement local) |
| **P3** | Multi-utilisateur | A faire | Authentification + roles (admin/viewer) |

### Suggestions d'amelioration

#### Securite
- [ ] **Rotation des tokens MCP** — Les Bearer tokens sont statiques ; implementer une rotation automatique ou utiliser JWT avec expiration
- [ ] **Chiffrement des .db** — Les bases SQLite contiennent des conversations et decisions ; envisager SQLCipher
- [ ] **Audit des permissions** — `NOPASSWD:ALL` est pratique mais risque ; restreindre aux commandes JARVIS necessaires
- [ ] **Network isolation Docker** — Creer des sous-reseaux Docker separes (monitoring, trading, voice) au lieu d'un seul `jarvis-net`
- [ ] **Secrets management** — Migrer les cles API de `.env` vers un vault (HashiCorp Vault, SOPS, age)

#### Performance
- [ ] **Connection pooling LM Studio** — Reutiliser les connexions HTTP au lieu d'en creer a chaque dispatch
- [ ] **Cache distribue** — Redis/Valkey au lieu du cache Python in-memory (persistance entre restarts)
- [ ] **Batch inference** — Grouper les requetes LM Studio quand plusieurs arrivent simultanement
- [ ] **GPU memory management** — Prevoir l'auto-unload des modeles inactifs pour liberer VRAM
- [ ] **ZRAM auto-resize** — Adapter la taille ZRAM dynamiquement selon la charge

#### Fiabilite
- [ ] **Chaos testing** — Scripts pour simuler des pannes (kill GPU, couper M2, saturer RAM) et valider le self-healing
- [ ] **Canary deployments** — Deployer les nouveaux modeles sur 1 GPU avant de propager au cluster
- [ ] **Circuit breaker tuning** — Les seuils actuels sont fixes ; implementer des seuils adaptatifs bases sur les percentiles
- [ ] **Backup verification** — Tester la restauration des backups periodiquement (pas seulement creer)
- [ ] **Graceful shutdown** — S'assurer que tous les services sauvegardent leur etat avant arret

#### Fonctionnalites
- [ ] **Plugin marketplace** — Permettre a la communaute de contribuer des skills OpenClaw et scripts cowork
- [ ] **Multi-langue voice** — Support anglais/espagnol en plus du francais (wake word + STT + TTS)
- [ ] **Mobile app** — Application Android/iOS pour controler JARVIS a distance (au-dela de Telegram)
- [ ] **Webhook integrations** — Discord, Slack, ntfy.sh en plus de Telegram
- [ ] **Visual workflow editor** — Interface drag-and-drop pour creer des pipelines Domino (au lieu de code)
- [ ] **RAG pipeline** — Retrieval-Augmented Generation avec les documents locaux (PDF, notes, code)

#### Documentation
- [ ] **Tutoriel video** — Screencast de l'installation complete de 0 a operationnel
- [ ] **Architecture Decision Records** — Documenter les choix techniques (pourquoi ZRAM 180 swappiness, pourquoi pas Redis, etc.)
- [ ] **Contribution guide** — CONTRIBUTING.md avec conventions, process de PR, style guide
- [ ] **Changelog** — CHANGELOG.md avec historique des versions et breaking changes
- [ ] **API reference** — Documentation auto-generee des 609 handlers MCP

### Contribuer

```bash
# 1. Fork le repo
git clone https://github.com/VOTRE_USER/jarvis-linux.git
cd jarvis-linux

# 2. Creer une branche
git checkout -b feature/ma-feature

# 3. Installer l'environnement de dev
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# 4. Lancer les tests
uv run pytest tests/ -v

# 5. Soumettre une PR
git push origin feature/ma-feature
# Ouvrir une Pull Request sur GitHub
```

### Architecture de reference

Pour comprendre les choix architecturaux :
- **Pourquoi 6 GPU heterogenes ?** — Cout/performance optimal : la RTX 3080 gere les modeles lourds, les 1660S font du compute distribue a moindre cout
- **Pourquoi SQLite et pas PostgreSQL ?** — Zero config, zero serveur, backup = copier un fichier, suffisant pour un seul utilisateur
- **Pourquoi ZRAM 180 swappiness ?** — Avec ZRAM, le swap est en RAM compressee (pas sur disque), donc swappiness eleve = utiliser la compression plutot que flusher le cache
- **Pourquoi pas Kubernetes ?** — Over-engineering pour 1 machine ; systemd + Docker Compose couvre tous les besoins
- **Pourquoi 4 moteurs IA ?** — Redundance + specialisation : chaque modele excelle dans un domaine different

---

*Status : Operational | Plateforme : Linux x86_64 | Architecture : Multi-Agent Distribue Autonome | v12.4 — Mars 2026*
