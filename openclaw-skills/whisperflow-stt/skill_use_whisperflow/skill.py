#!/usr/bin/env python3
"""
Skill OpenClaw : use_whisperflow
Remplace openai-whisper par WhisperFlow comme moteur STT.

Usage dans OpenClaw :
  - Configure WHISPERFLOW_URL dans .env
  - Déclare cette skill dans openclaw.json
  - OpenClaw appelle transcribe() pour chaque requête STT
"""
import os
import asyncio
import json
import logging
import tempfile
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("openclaw.skill.whisperflow")

WHISPERFLOW_URL = os.getenv("WHISPERFLOW_URL", "ws://localhost:8000/ws")


class WhisperFlowSkill:
    """Skill OpenClaw pour transcription via WhisperFlow."""

    name = "use_whisperflow"
    description = "Transcription audio temps réel via WhisperFlow (remplace Whisper CLI)"

    def __init__(self, url: str = None):
        self.url = url or WHISPERFLOW_URL
        log.info(f"WhisperFlow skill initialisée → {self.url}")

    async def transcribe_audio(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """Transcrit des données audio brutes (PCM 16-bit mono).

        Args:
            audio_data: bytes PCM
            sample_rate: taux d'échantillonnage

        Returns:
            Texte transcrit
        """
        try:
            import websockets
        except ImportError:
            log.error("pip install websockets")
            return ""

        try:
            async with websockets.connect(self.url) as ws:
                # Config
                await ws.send(json.dumps({
                    "type": "config",
                    "language": os.getenv("WHISPERFLOW_LANG", "fr"),
                    "sample_rate": sample_rate,
                }))

                # Envoyer audio par chunks de 4096 bytes
                for i in range(0, len(audio_data), 4096):
                    await ws.send(audio_data[i:i + 4096])

                # Fin de flux
                await ws.send(json.dumps({"type": "end"}))

                # Récupérer résultat
                transcription = []
                async for msg in ws:
                    result = json.loads(msg)
                    if result.get("type") == "final":
                        transcription.append(result.get("text", ""))
                        break
                    elif result.get("text"):
                        transcription.append(result["text"])

                return " ".join(transcription).strip()

        except ConnectionRefusedError:
            log.error(f"WhisperFlow non joignable : {self.url}")
            return ""
        except Exception as e:
            log.error(f"Erreur transcription : {e}")
            return ""

    async def transcribe_file(self, filepath: str) -> str:
        """Transcrit un fichier audio (WAV, MP3, etc.)."""
        import wave
        try:
            with wave.open(filepath, "rb") as wf:
                audio_data = wf.readframes(wf.getnframes())
                sr = wf.getframerate()
            return await self.transcribe_audio(audio_data, sr)
        except Exception as e:
            log.error(f"Erreur lecture fichier : {e}")
            return ""

    def transcribe_sync(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """Version synchrone pour appels depuis OpenClaw."""
        return asyncio.run(self.transcribe_audio(audio_data, sample_rate))


# Fonction shortcut pour OpenClaw
_skill = None


def transcribe(audio_data: bytes = None, filepath: str = None) -> str:
    """Point d'entrée principal pour OpenClaw.

    Args:
        audio_data: bytes PCM (prioritaire si fourni)
        filepath: chemin fichier audio

    Returns:
        Texte transcrit
    """
    global _skill
    if _skill is None:
        _skill = WhisperFlowSkill()

    if audio_data:
        return _skill.transcribe_sync(audio_data)
    elif filepath:
        return asyncio.run(_skill.transcribe_file(filepath))
    else:
        return ""
