#!/usr/bin/env python3
"""
JARVIS Voice Hub — Serveur central de contrôle vocal.
Pipeline : Wake Word → STT → LLM/MCP → Executor → TTS

Endpoints :
  POST /voice/audio  — envoie audio → STT → commande
  POST /voice/text   — envoie texte → commande
  GET  /voice/status — état du hub
"""
import os
import json
import subprocess
import tempfile
import logging
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from command_filter import filter_command
from audio_utils import record_audio, save_audio, SAMPLE_RATE
from tts import speak, speak_async

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("jarvis.voice_hub")

app = Flask(__name__)
CORS(app)

# Configuration
MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:8080/mcp")
MCP_API_KEY = os.getenv("MCP_API_KEY", "1202")
WAKEWORD_ENABLED = os.getenv("WAKEWORD_ENABLED", "true").lower() == "true"
VOICE_BUTTON = os.getenv("VOICE_BUTTON", "false").lower() == "true"
STT_ENGINE = os.getenv("STT_ENGINE", "whisper")  # whisper, whisperflow, api
WHISPERFLOW_URL = os.getenv("WHISPERFLOW_URL", "ws://localhost:8000/ws")

# Mapping commandes vocales → actions
COMMANDS_FILE = os.path.join(os.path.dirname(__file__), "commands.json")

# État global
hub_state = {"status": "idle", "last_command": None, "last_result": None}


def load_commands() -> dict:
    """Charge le mapping commandes vocales → actions."""
    try:
        with open(COMMANDS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def stt_transcribe(audio_path: str) -> str:
    """Transcrit un fichier audio en texte via Whisper local."""
    try:
        # Whisper CLI local
        result = subprocess.run(
            ["whisper", audio_path, "--language", "fr", "--model", "base",
             "--output_format", "txt", "--output_dir", "/tmp"],
            capture_output=True, text=True, timeout=60
        )
        txt_path = audio_path.replace(".wav", ".txt")
        if os.path.exists(f"/tmp/{os.path.basename(txt_path)}"):
            with open(f"/tmp/{os.path.basename(txt_path)}") as f:
                return f.read().strip()
        return result.stdout.strip()
    except FileNotFoundError:
        log.warning("Whisper CLI non trouvé, fallback sur texte brut")
        return ""
    except Exception as e:
        log.error(f"Erreur STT : {e}")
        return ""


def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Appelle un tool MCP JARVIS."""
    try:
        resp = requests.post(
            MCP_URL,
            headers={
                "Authorization": f"Bearer {MCP_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments}
            },
            timeout=30
        )
        return resp.json().get("result", {})
    except Exception as e:
        log.error(f"Erreur MCP : {e}")
        return {"error": str(e)}


def match_voice_command(text: str) -> dict | None:
    """Cherche une correspondance dans commands.json."""
    commands = load_commands()
    text_lower = text.lower().strip()
    for pattern, action in commands.items():
        if pattern.lower() in text_lower:
            return action
    return None


def execute_text_command(text: str) -> dict:
    """Traite une commande textuelle : match → filtre → exécute."""
    hub_state["status"] = "processing"
    hub_state["last_command"] = text

    # 1. Chercher dans les commandes vocales mappées
    matched = match_voice_command(text)
    if matched:
        if matched.get("type") == "mcp":
            result = call_mcp_tool(matched["tool"], matched.get("args", {}))
            response = {"source": "mcp", "tool": matched["tool"], "result": result}
        elif matched.get("type") == "bash":
            cmd = matched["command"]
            check = filter_command(cmd)
            if not check["allowed"]:
                response = {"error": check["reason"], "blocked": True}
            elif check["needs_confirm"]:
                response = {"needs_confirm": True, "command": cmd, "reason": check["reason"]}
            else:
                out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                response = {"source": "bash", "stdout": out.stdout, "stderr": out.stderr}
        else:
            response = {"source": "matched", "action": matched}
    else:
        # 2. Pas de match direct → traiter comme commande bash si ça ressemble
        check = filter_command(text)
        if not check["allowed"]:
            response = {"error": check["reason"], "blocked": True}
        elif check["needs_confirm"]:
            response = {"needs_confirm": True, "command": text, "reason": check["reason"]}
        else:
            try:
                out = subprocess.run(text, shell=True, capture_output=True, text=True, timeout=30)
                response = {"source": "bash", "stdout": out.stdout, "stderr": out.stderr}
            except Exception as e:
                response = {"error": str(e)}

    hub_state["last_result"] = response
    hub_state["status"] = "idle"

    # TTS réponse
    if "stdout" in response and response["stdout"]:
        # Résumer la sortie pour la voix
        lines = response["stdout"].strip().split("\n")
        summary = lines[0] if len(lines) == 1 else f"{len(lines)} lignes de résultat"
        speak_async(f"Commande exécutée. {summary}")

    return response


@app.route("/voice/audio", methods=["POST"])
def handle_audio():
    """Reçoit un fichier audio, transcrit, exécute."""
    if "audio" not in request.files:
        return jsonify({"error": "Fichier audio manquant"}), 400

    audio_file = request.files["audio"]
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_file.save(tmp.name)
        text = stt_transcribe(tmp.name)
        os.unlink(tmp.name)

    if not text:
        return jsonify({"error": "Transcription vide"}), 400

    result = execute_text_command(text)
    return jsonify({"transcription": text, "result": result})


@app.route("/voice/text", methods=["POST"])
def handle_text():
    """Reçoit du texte, exécute."""
    data = request.json or {}
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "Texte manquant"}), 400

    result = execute_text_command(text)
    return jsonify({"result": result})


@app.route("/voice/status", methods=["GET"])
def handle_status():
    """Retourne l'état du voice hub."""
    return jsonify({
        "status": hub_state["status"],
        "wakeword_enabled": WAKEWORD_ENABLED,
        "voice_button": VOICE_BUTTON,
        "stt_engine": STT_ENGINE,
        "last_command": hub_state["last_command"],
    })


@app.route("/voice/listen", methods=["POST"])
def handle_listen():
    """Enregistre depuis le micro et traite."""
    duration = request.json.get("duration", 5) if request.json else 5
    pcm = record_audio(duration)
    if not pcm:
        return jsonify({"error": "Enregistrement échoué"}), 500

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        save_audio(pcm, tmp.name)
        text = stt_transcribe(tmp.name)
        os.unlink(tmp.name)

    if not text:
        return jsonify({"error": "Transcription vide"}), 400

    result = execute_text_command(text)
    return jsonify({"transcription": text, "result": result})


def start_with_wakeword():
    """Démarre le hub avec écoute wake word."""
    if not WAKEWORD_ENABLED:
        log.info("Wake word désactivé, mode API uniquement")
        return

    from wakeword import start_wakeword_listener

    def on_wake():
        log.info("Wake word détecté ! Enregistrement commande...")
        speak("Oui ?")
        pcm = record_audio(5.0)
        if pcm:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                save_audio(pcm, tmp.name)
                text = stt_transcribe(tmp.name)
                os.unlink(tmp.name)
            if text:
                log.info(f"Commande vocale : {text}")
                result = execute_text_command(text)
                log.info(f"Résultat : {result}")

    start_wakeword_listener(on_wake)
    log.info("Wake word listener démarré")


if __name__ == "__main__":
    start_with_wakeword()
    port = int(os.getenv("VOICE_HUB_PORT", 8081))
    log.info(f"Voice Hub sur http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
