"""
JARVIS Server - Serveur principal qui connecte Whisper-Flow à JARVIS
Lance le serveur WebSocket pour la transcription + traitement JARVIS
"""

import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path

# Fix Windows cp1252 encoding issues
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ajoute le parent au path pour importer whisperflow
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whisperflow.transcriber import get_model, transcribe_pcm_chunks_async
from whisperflow.streaming import TranscribeSession
from whisperflow.audio.microphone import capture_audio, is_silent
from .jarvis_core import Jarvis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("jarvis.server")

# Bannière JARVIS
BANNER = """
  ========================================
   JARVIS v1.0 - Whisper Flow
   Just A Rather Very Intelligent System
   Controle vocal Windows complet
  ========================================
"""

HELP_TEXT = """
=== COMMANDES VOCALES JARVIS ===

Dites "Jarvis" suivi de votre commande:

APPLICATIONS:
  "Jarvis ouvre Chrome"          "Jarvis ferme Notepad"
  "Jarvis lance le terminal"     "Jarvis ouvre Word"

SYSTÈME:
  "Jarvis monte le volume"       "Jarvis volume à 50"
  "Jarvis muet"                  "Jarvis luminosité à 80"
  "Jarvis quelle heure est-il"   "Jarvis quel jour sommes-nous"
  "Jarvis batterie"              "Jarvis verrouille"

FENÊTRES:
  "Jarvis minimise"              "Jarvis maximise"
  "Jarvis bascule"               "Jarvis bureau"
  "Jarvis capture d'écran"

FICHIERS:
  "Jarvis crée un fichier test"  "Jarvis crée un dossier projets"
  "Jarvis cherche rapport"       "Jarvis supprime brouillon"

WEB:
  "Jarvis google intelligence artificielle"
  "Jarvis youtube tutoriel Python"
  "Jarvis wikipedia machine learning"
  "Jarvis va sur github.com"

MÉDIA:
  "Jarvis play"                  "Jarvis pause"
  "Jarvis suivant"               "Jarvis précédent"

DICTÉE:
  "Jarvis mode dictée"           (tout ce que vous dites est tapé)
  "Arrête la dictée"             (revient en mode commande)

MACROS:
  "Jarvis automatise routine matin"  (enregistre)
  "Fin de macro"                     (sauvegarde)
  "Jarvis lance la macro routine matin"

NAVIGATION:
  "Jarvis paramètres wifi"       "Jarvis ouvre téléchargements"
  "Jarvis paramètres son"        "Jarvis ouvre documents"

CONTRÔLE:
  "Jarvis aide"                  "Jarvis statut"
  "Jarvis annule"                "Jarvis répète"
  "Jarvis au revoir"
"""


async def main():
    """Point d'entrée principal JARVIS"""
    print(BANNER)
    print(HELP_TEXT)

    # Initialise JARVIS
    jarvis = Jarvis()

    # Charge le modèle Whisper
    logger.info("Chargement du modèle Whisper...")
    model = get_model()
    logger.info("Modèle Whisper chargé")

    # Queues et événements
    audio_queue = asyncio.Queue()
    stop_event = asyncio.Event()

    # Callback quand un segment est transcrit
    async def on_segment(result_json: str):
        try:
            result = json.loads(result_json) if isinstance(result_json, str) else result_json
            text = result.get("data", {}).get("text", "").strip()
            is_partial = result.get("is_partial", True)

            if text:
                if not is_partial:
                    logger.info(f"[Final] {text}")
                await jarvis.process_transcription(text, is_partial)

        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Erreur traitement segment: {e}")

    # Crée la session de transcription
    async def transcriber(chunks):
        return await transcribe_pcm_chunks_async(model, chunks)

    async def send_back(result):
        await on_segment(result)

    session = TranscribeSession(transcriber, send_back)

    # Boucle de capture audio
    async def audio_loop():
        try:
            import pyaudio
            RATE = 16000
            CHANNELS = 1
            CHUNK = 1024
            FORMAT = pyaudio.paInt16

            pa = pyaudio.PyAudio()
            stream = pa.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )

            logger.info("Capture audio démarrée - En écoute...")
            await jarvis.start()

            while not stop_event.is_set() and jarvis.is_running:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    if not is_silent(data, silence_threshold=500):
                        session.add_chunk(data)
                    await asyncio.sleep(0.01)
                except OSError:
                    await asyncio.sleep(0.1)

            stream.stop_stream()
            stream.close()
            pa.terminate()

        except ImportError:
            logger.error("PyAudio non installé. pip install PyAudio")
        except Exception as e:
            logger.error(f"Erreur audio: {e}")
        finally:
            stop_event.set()

    # Gestion arrêt propre
    def signal_handler():
        logger.info("Signal d'arrêt reçu")
        stop_event.set()

    try:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, signal_handler)
            except NotImplementedError:
                # Windows ne supporte pas add_signal_handler
                signal.signal(sig, lambda s, f: signal_handler())
    except Exception:
        pass

    # Lance la boucle audio
    try:
        await audio_loop()
    except KeyboardInterrupt:
        pass
    finally:
        await session.stop()
        await jarvis.stop()
        logger.info("JARVIS terminé")


def run():
    """Lance JARVIS"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nJARVIS arrêté.")


if __name__ == "__main__":
    run()
