"""
JARVIS Cluster Bridge — Connecte jarvis-whisper-flow au cluster IA (M1/OL1/M2/M3)
et au dispatcher cowork (395 scripts autonomes).

Pipeline: Voix → Whisper → Commander → Skills/Cluster → TTS
Fallback: M1+OL1 race → M2 reasoning → M3 fallback
"""

import asyncio
import json
import re
import logging
from typing import Optional

logger = logging.getLogger("jarvis.cluster")

# Cluster nodes — ordered by priority
NODES = {
    "M1": {
        "url": "http://127.0.0.1:1234/v1/chat/completions",
        "model": "qwen3-8b",
        "timeout": 12,
        "api": "openai",
        "system": "/nothink\nTu es JARVIS, assistant de Turbo. Francais, concis 2-3 phrases.",
        "max_tokens": 200,
    },
    "OL1": {
        "url": "http://127.0.0.1:11434/api/chat",
        "model": "qwen3:1.7b",
        "timeout": 12,
        "api": "ollama",
        "system": "Tu es JARVIS. Francais, concis.",
        "max_tokens": 200,
    },
    "M2": {
        "url": "http://192.168.1.26:1234/v1/chat/completions",
        "model": "deepseek-r1-0528-qwen3-8b",
        "timeout": 30,
        "api": "openai",
        "system": "Tu es JARVIS, assistant de Turbo. Francais, concis 2-3 phrases.",
        "max_tokens": 300,
    },
    "M3": {
        "url": "http://192.168.1.113:1234/v1/chat/completions",
        "model": "deepseek-r1-0528-qwen3-8b",
        "timeout": 25,
        "api": "openai",
        "system": "Tu es JARVIS, assistant de Turbo. Francais, concis 2-3 phrases.",
        "max_tokens": 300,
    },
}

THINK_RE = re.compile(r'<think>[\s\S]*?</think>')

# Anti-regurgitation patterns
_REJECT_PATTERNS = [
    "Tu es JARVIS",
    "/nothink",
    "mode sandbox",
    "activez le mode",
    "Veuillez activer",
]


async def _http_post(url: str, payload: dict, timeout: float) -> Optional[dict]:
    """HTTP POST via httpx (preferred) or curl fallback."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                return resp.json()
    except ImportError:
        # Fallback: curl subprocess
        import tempfile, os
        body = json.dumps(payload)
        # Write body to temp file to avoid shell escaping issues on Windows
        fd, tmp = tempfile.mkstemp(suffix=".json")
        try:
            os.write(fd, body.encode("utf-8"))
            os.close(fd)
            proc = await asyncio.create_subprocess_exec(
                "curl", "-s", "--max-time", str(int(timeout)),
                url,
                "-H", "Content-Type: application/json",
                "-d", f"@{tmp}",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout + 3)
            return json.loads(stdout.decode("utf-8"))
        finally:
            os.unlink(tmp)
    except Exception as e:
        logger.debug(f"HTTP POST {url} failed: {e}")
    return None


def _validate_response(text: str, prompt: str) -> bool:
    """Quality gate — reject bad responses."""
    if not text or len(text) < 2:
        return False
    # Anti-regurgitation
    for pattern in _REJECT_PATTERNS:
        if pattern.lower() in text.lower() and pattern.lower() not in prompt.lower():
            logger.warning(f"Rejected (regurgitation): {text[:60]}")
            return False
    return True


async def query_node(name: str, prompt: str, system: str = None) -> Optional[str]:
    """Query any cluster node by name."""
    node = NODES.get(name)
    if not node:
        return None

    sys_prompt = system or node["system"]

    if node["api"] == "ollama":
        payload = {
            "model": node["model"],
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "think": False,
            "options": {"num_predict": node["max_tokens"]},
        }
    else:  # openai
        payload = {
            "model": node["model"],
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": node["max_tokens"],
            "stream": False,
        }

    try:
        data = await _http_post(node["url"], payload, node["timeout"])
        if not data:
            return None

        # Extract text based on API type
        if node["api"] == "ollama":
            text = data["message"]["content"]
        else:
            text = data["choices"][0]["message"]["content"]

        text = THINK_RE.sub('', text).strip()

        if _validate_response(text, prompt):
            return text
        return None
    except Exception as e:
        logger.warning(f"{name} query failed: {e}")
        return None


# Convenience wrappers
async def query_m1(prompt: str, system: str = None) -> Optional[str]:
    return await query_node("M1", prompt, system)


async def query_ol1(prompt: str, system: str = None) -> Optional[str]:
    return await query_node("OL1", prompt, system)


async def cluster_race(prompt: str, system: str = None) -> tuple[Optional[str], str]:
    """Race M1 vs OL1 — first good response wins.
    Fallback to M2/M3 if both fail.
    Returns (response_text, agent_name).
    """
    # Phase 1: Race M1 vs OL1
    async def _query(name):
        r = await query_node(name, prompt, system)
        return (r, name) if r else None

    tasks = [asyncio.create_task(_query("M1")), asyncio.create_task(_query("OL1"))]

    for coro in asyncio.as_completed(tasks):
        result = await coro
        if result:
            for t in tasks:
                t.cancel()
            return result

    # Phase 2: Fallback M2 then M3
    for fallback in ("M2", "M3"):
        logger.info(f"Primary race failed, trying {fallback}")
        r = await query_node(fallback, prompt, system)
        if r:
            return (r, fallback)

    return (None, "NONE")


async def dispatch_cowork(query: str, cowork_path: str = "F:/BUREAU/jarvis-cowork") -> Optional[str]:
    """Dispatch a query to cowork scripts via the cowork dispatcher.
    Returns the best match description or execution result.
    """
    import sys
    dispatcher = f"{cowork_path}/cowork_dispatcher.py"
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, dispatcher, "--dispatch", query,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            cwd=cowork_path,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode("utf-8", errors="replace").strip()
        if output:
            try:
                data = json.loads(output)
                matches = data.get("matches", [])
                if matches:
                    best = matches[0]
                    desc = best.get("description", "")
                    scripts = best.get("scripts", [])[:3]
                    return f"{desc} (scripts: {', '.join(scripts)})"
            except json.JSONDecodeError:
                pass
    except Exception as e:
        logger.warning(f"Cowork dispatch failed: {e}")
    return None
