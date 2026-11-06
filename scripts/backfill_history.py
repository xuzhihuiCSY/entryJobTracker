"""Recover actual daily counts from main's committed public snapshots."""
from __future__ import annotations

import json
import subprocess

from fetch_jobs import PUBLIC_DATA, ROOT
from job_history import history_point, merge_history, record_history
from utils import read_json, write_json


def snapshot(commit: str, filename: str):
    result = subprocess.run(["git", "show", f"{commit}:public/data/{filename}"], cwd=ROOT, capture_output=True, check=False)
    if result.returncode:
        return None
    try:
        return json.loads(result.stdout)
    except (ValueError, UnicodeDecodeError):
        return None


def main() -> None:
    shallow = subprocess.check_output(["git", "rev-parse", "--is-shallow-repository"], cwd=ROOT, text=True).strip()
    if shallow == "true":
        raise SystemExit("Backfill needs full Git history; fetch it before running this one-time command.")
    commits = subprocess.check_output(["git", "log", "--reverse", "--format=%H", "HEAD", "--", "public/data/last_updated.json"], cwd=ROOT, text=True).splitlines()
    history = []
    for commit in commits:
        summary = snapshot(commit, "last_updated.json")
        companies = snapshot(commit, "companies.json")
        if isinstance(summary, dict) and isinstance(companies, list):
            point = history_point(summary, companies)
            if point is not None:
                history = merge_history(history, point)
    # Keep observations already recorded by future syncs even if their commits
    # don't appear in this checkout's history yet.
    for point in read_json(PUBLIC_DATA / "history.json", []):
        history = merge_history(history, point)
    write_json(PUBLIC_DATA / "history.json", history)
    record_history(PUBLIC_DATA, read_json(PUBLIC_DATA / "last_updated.json", {}), read_json(PUBLIC_DATA / "companies.json", []))
    history = read_json(PUBLIC_DATA / "history.json", [])
    print(f"Recovered {len(history)} daily observations from {len(commits)} committed snapshots")
    if history:
        print(f"Coverage: {history[0]['date']} through {history[-1]['date']}; missing dates are left missing")


if __name__ == "__main__":
    main()
