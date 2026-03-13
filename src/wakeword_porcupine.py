#!/usr/bin/env python3
"""
Module wake word Porcupine pour JARVIS.
Écoute en continu le micro et appelle on_wake() quand "Hey Jarvis" est détecté.
"""
import os
import struct
import threading
import logging
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("jarvis.wakeword")

ACCESS_KEY = os.getenv("PV_ACCESS_KEY", "")
KEYWORD_PATH = os.getenv("WAKEWORD_PATH", "./models/hey_jarvis_linux.ppn")


def start_wakeword_listener(on_wake: callable, sensitivity: float = 0.6):
    """Lance l'écoute du wake word dans un thread séparé.

    Args:
        on_wake: callback appelé quand le wake word est détecté
        sensitivity: sensibilité 0.0-1.0 (plus haut = plus sensible)
    """
    def _listen():
        try:
            import pvporcupine
            import pyaudio
        except ImportError:
            log.error("pvporcupine ou pyaudio manquant. pip install pvporcupine pyaudio")
            return

        if not ACCESS_KEY:
            log.error("PV_ACCESS_KEY non défini dans .env")
            return

        if not os.path.exists(KEYWORD_PATH):
            log.error(f"Fichier wake word introuvable : {KEYWORD_PATH}")
            return

        try:
            porcupine = pvporcupine.create(
                access_key=ACCESS_KEY,
                keyword_paths=[KEYWORD_PATH],
                sensitivities=[sensitivity],
            )
        except Exception as e:
            log.error(f"Erreur init Porcupine : {e}")
            return

        pa = pyaudio.PyAudio()
        try:
            audio_stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length,
            )
        except Exception as e:
            log.error(f"Micro introuvable ou inaccessible : {e}")
            pa.terminate()
            porcupine.delete()
            return

        log.info("En écoute pour 'Hey Jarvis'...")
        print("En écoute pour 'Hey Jarvis'...")

        try:
            while True:
                pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                if porcupine.process(pcm) >= 0:
                    log.info("Wake word détecté !")
                    on_wake()
        except KeyboardInterrupt:
            log.info("Arrêt wake word")
        finally:
            audio_stream.stop_stream()
            audio_stream.close()
            pa.terminate()
            porcupine.delete()

    t = threading.Thread(target=_listen, daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    def on_wake():
        print("Wake word détecté : Hey Jarvis !")

    t = start_wakeword_listener(on_wake)
    try:
        t.join()
    except KeyboardInterrupt:
        print("\nArrêt.")
