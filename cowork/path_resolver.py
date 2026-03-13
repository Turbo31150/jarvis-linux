from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEV_DIR = BASE_DIR / "dev"


def _candidate_roots() -> list[Path]:
    env_root = os.environ.get("JARVIS_LINUX_ROOT")
    roots: list[Path] = []
    if env_root:
        roots.append(Path(env_root))
    roots.extend(
        [
            Path("/home/turbo/jarvis-linux"),
            BASE_DIR.parent / "jarvis-linux",
            Path("/home/turbo/jarvis"),
            Path("/home/turbo"),
        ]
    )
    return roots


def resolve_project_root() -> Path:
    for root in _candidate_roots():
        if (root / "data").exists():
            return root
    return BASE_DIR.parent


def resolve_data_dir() -> Path:
    data_dir = resolve_project_root() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def resolve_db(name: str) -> Path:
    for candidate in candidate_dbs(name):
        if candidate.exists():
            return candidate
    return resolve_data_dir() / name


def candidate_dbs(name: str) -> list[Path]:
    candidates: list[Path] = []
    for root in _candidate_roots():
        candidates.extend([root / "data" / name, root / name])

    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            deduped.append(candidate)
            seen.add(key)
    return deduped


def resolve_db_with_table(name: str, table: str) -> Path:
    import sqlite3

    for candidate in candidate_dbs(name):
        if not candidate.exists():
            continue
        try:
            conn = sqlite3.connect(candidate)
            try:
                row = conn.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                ).fetchone()
            finally:
                conn.close()
            if row and row[0]:
                return candidate
        except Exception:
            continue
    return resolve_db(name)


def resolve_openclaw_dev_dir() -> Path:
    env_path = os.environ.get("OPENCLAW_DEV_DIR")
    if env_path:
        return Path(env_path)

    candidates = [
        Path.home() / ".openclaw" / "workspace" / "dev",
        resolve_project_root() / "openclaw" / "workspace" / "dev",
        DEV_DIR,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]
