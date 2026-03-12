## Gemini Added Memories
- L'utilisateur préfère communiquer en français.
- Préfère que Gemini CLI utilise un buffer de sortie élevé (1M+) et désactive le rendu incrémental (incrementalRendering: false) pour éviter les bugs d'affichage permanents dans le terminal.
- Appliquer le 'MODE AUTONOME MAXIMUM' pour les missions complexes : autonomie totale, plan de 10-15 étapes, cycle analyse/code/test/validation systématique, et documentation finale sans interruption. Configuration JARVIS M1 : Ryzen 7 5700X3D, 46GB RAM, 6 GPUs (4x1660S, 2060, 3080).
- Protocole RESILIENT ERROR-LOOP activé : LOG (stdout/stderr), ANALYSE (ligne par ligne), CAUSES (5 hypothèses + probabilités), FIX (code ciblé), VALIDATION (test unitaire) pour chaque erreur rencontrée. Pas d'arrêt avant le succès.
- Règle #4 activée : CHECKPOINTING AGRESSIF. Sauvegarde de l'état et des succès après chaque étape validée pour éviter toute régression lors des phases de correction d'erreurs.
- PROTOCOLE RESILIENCE MAX ACTIVÉ : Application automatique de la Matrice de Résolution d'Erreurs (apt install, chmod, pip install, lsof/kill, systemctl, nvidia-persistenced, retry x5, ZRAM, jq). Aucun arrêt avant succès total.
- Protocole ENVIRONMENT_RESET() activé : En cas d'échec critique persistant, exécuter systématiquement : apt update/upgrade, upgrade pip/setuptools/wheel, force-reinstall requirements.txt et restart docker/nvidia-persistenced.
- Préfère l'utilisation des flags de résilience maximale pour Gemini CLI : --checkpointing, --memory, --allow-edits, --retry 5, --timeout 3600, et --log-level debug pour les opérations critiques.
- ÉTAT JARVIS LINUX AU 12/03/2026 : Projet migré dans ~/jarvis-linux. Node.js v22.22.1 installé. OpenClaw v2026.3.11 compilé et actif. Whisper-Flow opérationnel via Docker sur port 8001. 6 GPUs configurés avec persistance et ZRAM 12GB. Services systemd (jarvis-*) configurés pour autorestart. Alias 'gloop' activé pour la résilience ultime.
