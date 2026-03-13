#!/usr/bin/env python3
"""
Serveur MCP WhisperFlow pour Claude Code / Gemini CLI.
Expose la transcription WhisperFlow comme tool MCP.
Port 8082.
"""
import os
import json
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from whisperflow_client import transcribe_sync

load_dotenv()

app = Flask(__name__)
CORS(app)

MCP_API_KEY = os.getenv("WHISPERFLOW_MCP_KEY", "wf-jarvis-2026")

# État streaming
_stream_active = False
_stream_text = ""


@app.route("/mcp", methods=["GET", "POST"])
def mcp_handler():
    if request.method == "GET":
        return jsonify({"status": "ok", "message": "WhisperFlow MCP Server"})

    if request.headers.get("Authorization") != f"Bearer {MCP_API_KEY}":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    method = data.get("method")
    params = data.get("params", {})
    req_id = data.get("id")

    if method == "tools/list":
        tools = [
            {
                "name": "whisperflow_transcribe",
                "description": "Transcrit un fichier audio via WhisperFlow (WAV 16kHz)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "audio_path": {"type": "string", "description": "Chemin vers fichier audio WAV"}
                    },
                    "required": ["audio_path"]
                }
            },
            {
                "name": "whisperflow_status",
                "description": "Vérifie si WhisperFlow est accessible",
                "inputSchema": {"type": "object", "properties": {}}
            }
        ]
        return jsonify({"jsonrpc": "2.0", "id": req_id, "result": tools})

    elif method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})

        if name == "whisperflow_transcribe":
            audio_path = args.get("audio_path", "")
            if not os.path.exists(audio_path):
                return jsonify({"jsonrpc": "2.0", "id": req_id,
                                "result": {"error": f"Fichier non trouvé : {audio_path}"}})
            text = transcribe_sync(audio_path)
            return jsonify({"jsonrpc": "2.0", "id": req_id,
                            "result": {"text": text, "audio_path": audio_path}})

        elif name == "whisperflow_status":
            url = os.getenv("WHISPERFLOW_URL", "ws://localhost:8000/ws")
            try:
                import websockets
                async def check():
                    async with websockets.connect(url) as ws:
                        return True
                ok = asyncio.run(check())
                return jsonify({"jsonrpc": "2.0", "id": req_id,
                                "result": {"status": "connected", "url": url}})
            except Exception as e:
                return jsonify({"jsonrpc": "2.0", "id": req_id,
                                "result": {"status": "disconnected", "url": url, "error": str(e)}})

    return jsonify({"jsonrpc": "2.0", "id": req_id, "result": []})


if __name__ == "__main__":
    port = int(os.getenv("WHISPERFLOW_MCP_PORT", 8082))
    print(f"WhisperFlow MCP sur http://0.0.0.0:{port}/mcp")
    app.run(host="0.0.0.0", port=port, debug=False)
