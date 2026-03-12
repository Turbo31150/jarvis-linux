#!/usr/bin/env python3
import asyncio
import websockets
import json
from src.whisper_worker import WhisperWorker

worker = WhisperWorker(model="large-v3-turbo")

async def handler(websocket):
    print("[WHISPER-BRIDGE] Client connecté.")
    async for message in websocket:
        try:
            # message est l audio brut (bytes)
            text = worker.transcribe(message)
            print(f"[WHISPER-BRIDGE] Transcrit: {text}")
            await websocket.send(json.dumps({"text": text}))
        except Exception as e:
            print(f"[WHISPER-BRIDGE] Erreur: {e}")
            await websocket.send(json.dumps({"text": "", "error": str(e)}))

async def main():
    print("[WHISPER-BRIDGE] Serveur pret sur ws://localhost:9000")
    async with websockets.serve(handler, "localhost", 9000):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
