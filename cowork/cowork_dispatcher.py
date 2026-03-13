#!/usr/bin/env python3
"""COWORK Dispatcher — Route tasks to cowork scripts via pattern matching.
Integrates with etoile.db pattern agents and executes scripts from dev/.
"""

import sqlite3
import subprocess
import sys
import os
import json
import re
import time
from datetime import datetime
from path_resolver import resolve_db_with_table

BASE = os.path.dirname(os.path.abspath(__file__))
PATTERNS_DB_PATH = str(resolve_db_with_table("etoile.db", "agent_patterns"))
MAPPING_DB_PATH = str(resolve_db_with_table("etoile.db", "cowork_script_mapping"))
DEV_PATH = os.path.join(BASE, 'dev')
PYTHON = sys.executable


def get_cowork_patterns(db_path=PATTERNS_DB_PATH):
    """Load all COWORK patterns from etoile.db."""
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    rows = db.execute("""
        SELECT
            p.name AS pattern_id,
            p.target_node AS agent_id,
            p.category AS pattern_type,
            p.keywords AS keywords,
            p.description AS description,
            p.target_node AS model_primary,
            'weighted_route' AS strategy,
            CAST(ROUND((2.0 - COALESCE(p.weight, 1.0)) * 3) AS INTEGER) AS priority
        FROM agent_patterns p
        ORDER BY COALESCE(p.weight, 1.0) DESC, p.name ASC
    """).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_scripts_for_pattern(pattern_id, db_path=MAPPING_DB_PATH):
    """Get scripts mapped to a pattern."""
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    rows = db.execute("""
        SELECT
            script AS script_name,
            script || '.py' AS script_path,
            'active' AS status
        FROM cowork_script_mapping
        WHERE pattern = ?
    """, (pattern_id,)).fetchall()
    db.close()
    return [dict(r) for r in rows]


def match_pattern(query, patterns):
    """Match a query to the best COWORK pattern using keyword scoring."""
    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))
    scores = []

    for pat in patterns:
        keywords = set((pat.get('keywords') or '').split(','))
        # Score: keyword overlap + description match
        keyword_score = len(query_words & keywords)
        desc_words = set(re.findall(r'\w+', (pat.get('description') or '').lower()))
        desc_score = len(query_words & desc_words) * 0.5
        # Priority bonus (lower priority number = higher bonus)
        priority_bonus = (6 - pat['priority']) * 0.3
        total = keyword_score + desc_score + priority_bonus
        if total > 0:
            scores.append((total, pat))

    scores.sort(key=lambda x: -x[0])
    return scores


def execute_script(script_name, args=None, timeout=60):
    """Execute a cowork script and return output."""
    script_path = os.path.join(DEV_PATH, f"{script_name}.py")
    if not os.path.exists(script_path):
        return {"error": f"Script not found: {script_path}"}

    cmd = [PYTHON, script_path]
    if args:
        cmd.extend(args)
    else:
        cmd.append("--once")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=DEV_PATH
        )
        return {
            "script": script_name,
            "returncode": result.returncode,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-500:] if result.stderr else "",
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"script": script_name, "error": "timeout", "success": False}
    except Exception as e:
        return {"script": script_name, "error": str(e), "success": False}


def dispatch(query, execute=False, top_n=3):
    """Dispatch a query: find matching patterns and optionally execute scripts."""
    patterns = get_cowork_patterns()
    matches = match_pattern(query, patterns)

    result = {
        "query": query,
        "matches": [],
        "timestamp": datetime.now().isoformat()
    }

    for score, pat in matches[:top_n]:
        scripts = get_scripts_for_pattern(pat['pattern_id'])
        match_entry = {
            "pattern_id": pat['pattern_id'],
            "agent_id": pat['agent_id'],
            "description": pat['description'],
            "score": round(score, 2),
            "scripts": [s['script_name'] for s in scripts],
            "script_count": len(scripts)
        }

        if execute and scripts:
            # Execute first matching script
            exec_result = execute_script(scripts[0]['script_name'])
            match_entry["execution"] = exec_result

        result["matches"].append(match_entry)

    return result


def list_all():
    """List all patterns and their scripts."""
    patterns = get_cowork_patterns()
    total_scripts = 0
    for pat in patterns:
        scripts = get_scripts_for_pattern(pat['pattern_id'])
        total_scripts += len(scripts)
        print(f"\n{pat['pattern_id']} ({pat['agent_id']})")
        print(f"  {pat['description']}")
        print(f"  Strategy: {pat['strategy']} | Priority: {pat['priority']}")
        print(f"  Scripts ({len(scripts)}): {', '.join(s['script_name'] for s in scripts[:5])}"
              + (f" +{len(scripts)-5} more" if len(scripts) > 5 else ""))

    print(f"\n--- Total: {len(patterns)} patterns, {total_scripts} scripts ---")


def health_check():
    """Check which scripts actually exist and are parseable."""
    db = sqlite3.connect(MAPPING_DB_PATH)
    db.row_factory = sqlite3.Row
    try:
        rows = db.execute("SELECT * FROM cowork_script_mapping").fetchall()
    except sqlite3.OperationalError as e:
        db.close()
        result = {
            "total": 0,
            "ok": 0,
            "missing": 0,
            "syntax_errors": 0,
            "errors": [f"DB schema unavailable in {MAPPING_DB_PATH}: {e}"],
            "status": "db_error",
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
    db.close()

    ok = 0
    missing = 0
    errors = []

    for r in rows:
        script_path = os.path.join(DEV_PATH, f"{r['script_name']}.py")
        if os.path.exists(script_path):
            try:
                with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                    compile(f.read(), script_path, 'exec')
                ok += 1
            except SyntaxError as e:
                errors.append({"script": r['script_name'], "error": str(e)})
        else:
            missing += 1

    result = {
        "total": len(rows),
        "ok": ok,
        "missing": missing,
        "syntax_errors": len(errors),
        "errors": errors[:10]
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def daemon_loop(interval=60):
    """Keep dispatcher alive and emit periodic health snapshots."""
    print(json.dumps({
        "status": "daemon_started",
        "patterns_db": PATTERNS_DB_PATH,
        "mapping_db": MAPPING_DB_PATH,
        "interval": interval,
        "timestamp": datetime.now().isoformat(),
    }, ensure_ascii=False))
    while True:
        try:
            health_check()
        except Exception as e:
            print(json.dumps({
                "status": "daemon_error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }, ensure_ascii=False))
        time.sleep(max(1, interval))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="COWORK Dispatcher")
    parser.add_argument("--dispatch", type=str, help="Query to dispatch")
    parser.add_argument("--execute", action="store_true", help="Execute matched scripts")
    parser.add_argument("--list", action="store_true", help="List all patterns")
    parser.add_argument("--health", action="store_true", help="Health check scripts")
    parser.add_argument("--once", action="store_true", help="Alias for --health")
    parser.add_argument("--daemon", action="store_true", help="Run periodic health checks in a loop")
    parser.add_argument("--interval", type=int, default=60, help="Daemon interval in seconds")
    args = parser.parse_args()

    if args.dispatch:
        result = dispatch(args.dispatch, execute=args.execute)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.list:
        list_all()
    elif args.daemon:
        daemon_loop(interval=args.interval)
    elif args.health or args.once:
        health_check()
    else:
        parser.print_help()
