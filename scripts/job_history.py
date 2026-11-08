"""Daily published snapshot counts, never inferred from job first_seen dates."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from utils import read_json, write_json


def history_point(summary: dict[str, Any], companies: list[dict[str, Any]]) -> dict[str, Any] | None:
    # Failed runs retain last_updated and old data; they are not new observations.
    if summary.get("sync_status") == "failed" or summary.get("sources_synced") == 0:
        return None
    total = summary.get("total_jobs")
    if type(total) is not int or total < 0:
        return None
    try:
        timestamp = datetime.fromisoformat(str(summary["last_updated"]).replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            return None
    except (KeyError, ValueError):
        return None
    timestamp = timestamp.astimezone(UTC)
    point = {
        "date": timestamp.date().isoformat(),
        "recorded_at": timestamp.isoformat().replace("+00:00", "Z"),
        "total_jobs": total,
        "companies_with_jobs": sum(company.get("active_job_count", 0) > 0 for company in companies),
        "comparable_jobs": comparable_job_counts(companies),
    }
    if any("sync_status" in company for company in companies):
        point["failed_sources"] = sum(company.get("sync_status") == "failed" for company in companies)
    return point


def comparable_job_counts(companies: list[dict[str, Any]]) -> dict[str, int]:
    counts = {}
    for company in companies:
        if not company.get("enabled", True) or not company.get("last_synced"):
            continue
        if company.get("sync_status") in {"failed", "disabled"}:
            continue
        slug, source = company.get("slug"), company.get("source_type")
        count = company.get("active_job_count")
        if slug and source and source != "placeholder" and type(count) is int and count >= 0:
            counts[f"{slug}:{source}"] = count
    return dict(sorted(counts.items()))


def merge_history(history: list[dict[str, Any]], point: dict[str, Any]) -> list[dict[str, Any]]:
    by_day = {row["date"]: row for row in history}
    previous = by_day.get(point["date"])
    if previous is None or point["recorded_at"] >= previous["recorded_at"]:
        by_day[point["date"]] = point
    return [by_day[day] for day in sorted(by_day)]


def record_history(data_dir: Path, summary: dict[str, Any], companies: list[dict[str, Any]]) -> None:
    point = history_point(summary, companies)
    if point is not None:
        history = read_json(data_dir / "history.json", [])
        write_json(data_dir / "history.json", merge_history(history, point))
