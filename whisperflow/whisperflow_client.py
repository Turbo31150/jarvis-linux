#!/usr/bin/env python3
"""
Client WhisperFlow pour JARVIS.
Se connecte à WhisperFlow via WebSocket, envoie des chunks audio PCM,
reçoit la transcription en temps réel.
"""
import os
import json
import asyncio
import wave
import logging
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("jarvis.whisperflow")

WHISPERFLOW_URL = os.getenv("WHISPERFLOW_URL", "ws://localhost:8000/ws")
CHUNK_SIZE = 4096  # taille des chunks audio envoyés


async def transcribe_file(audio_path: str, url: str = None) -> str:
    """Transcrit un fichier audio via WhisperFlow WebSocket.

    Args:
        audio_path: chemin vers fichier WAV 16kHz mono
        url: URL WebSocket WhisperFlow (défaut: env WHISPERFLOW_URL)

    Returns:
        Texte transcrit
    """
    try:
        import websockets
    except ImportError:
        log.error("websockets manquant. pip install websockets")
        return ""

    url = url or WHISPERFLOW_URL

    try:
        async with websockets.connect(url) as ws:
            # Envoyer config initiale
            config = {
                "type": "config",
                "language": "fr",
                "sample_rate": 16000,
                "channels": 1,
            }
            await ws.send(json.dumps(config))

            # Lire et envoyer le fichier audio par chunks
            with wave.open(audio_path, "rb") as wf:
                while True:
                    data = wf.readframes(CHUNK_SIZE)
                    if not data:
                        break
                    await ws.send(data)

            # Signaler fin du flux
            await ws.send(json.dumps({"type": "end"}))

            # Collecter les résultats
            transcription = []
            try:
                async for msg in ws:
                    result = json.loads(msg)
                    if result.get("type") == "final":
                        transcription.append(result.get("text", ""))
                        break
                    elif result.get("type") == "partial":
                        log.debug(f"Partiel : {result.get('text', '')}")
                    elif result.get("text"):
                        transcription.append(result["text"])
            except Exception:
                pass

            return " ".join(transcription).strip()

    except ConnectionRefusedError:
        log.error(f"WhisperFlow non accessible sur {url}")
        return ""
    except Exception as e:
        log.error(f"Erreur WhisperFlow : {e}")
        return ""


async def transcribe_stream(audio_generator, url: str = None) -> str:
    """Transcrit un flux audio en temps réel.

    Args:
        audio_generator: générateur qui yield des bytes PCM
        url: URL WebSocket WhisperFlow
    """
    try:
        import websockets
    except ImportError:
        return ""

    url = url or WHISPERFLOW_URL
    transcription = []

    try:
        async with websockets.connect(url) as ws:
            config = {"type": "config", "language": "fr", "sample_rate": 16000}
            await ws.send(json.dumps(config))

            # Envoyer audio en parallèle avec réception
            async def send_audio():
                for chunk in audio_generator:
                    await ws.send(chunk)
                await ws.send(json.dumps({"type": "end"}))

            async def receive_text():
                async for msg in ws:
                    result = json.loads(msg)
                    if result.get("type") == "final":
                        transcription.append(result.get("text", ""))
                        break
                    elif result.get("text"):
                        transcription.append(result["text"])

            await asyncio.gather(send_audio(), receive_text())

    except Exception as e:
        log.error(f"Erreur streaming : {e}")

    return " ".join(transcription).strip()


def transcribe_sync(audio_path: str, url: str = None) -> str:
    """Version synchrone de transcribe_file."""
    return asyncio.run(transcribe_file(audio_path, url))


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage : python3 whisperflow_client.py <fichier.wav>")
        sys.exit(1)

    result = transcribe_sync(sys.argv[1])
    print(f"Transcription : {result}")
