from __future__ import annotations

import argparse
import logging
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from adapters import get_adapter
from normalizer import dedupe_jobs, is_relevant_technical_job, make_job_id, normalize_job
from utils import read_json, setup_logging, write_json

ROOT = Path(__file__).resolve().parents[1]
COMPANIES_YAML = ROOT / "scripts" / "data" / "companies.yaml"
PUBLIC_DATA = ROOT / "public" / "data"

LOGGER = logging.getLogger(__name__)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_companies() -> list[dict[str, Any]]:
    if not COMPANIES_YAML.exists():
        raise FileNotFoundError(f"Missing company config: {COMPANIES_YAML}")
    payload = yaml.safe_load(COMPANIES_YAML.read_text(encoding="utf-8")) or []
    if not isinstance(payload, list):
        raise ValueError("companies.yaml must be a list of company objects")
    return payload


def select_companies(companies: list[dict[str, Any]], priority: int | None, include_all: bool) -> list[dict[str, Any]]:
    selected = [company for company in companies if company.get("enabled", True)]
    if include_all:
        return selected
    if priority is None:
        return selected
    return [company for company in selected if int(company.get("sync_priority", 3)) == priority]


def fetch_raw_jobs(company: dict[str, Any]) -> list[dict[str, Any]] | None:
    adapter = get_adapter(company.get("source_type", "placeholder"))
    try:
        return adapter(company)
    except Exception:
        LOGGER.exception("Failed to fetch jobs for %s", company.get("name", company.get("slug")))
        return None


def merge_first_seen(
    raw_job: dict[str, Any],
    company: dict[str, Any],
    seen_jobs: dict[str, Any],
    checked_at: str,
    previous_first_seen_by_apply_url: dict[str, str],
) -> str:
    job_id = make_job_id(company["slug"], raw_job)
    existing = seen_jobs.get(job_id) or {}
    apply_url = str(raw_job.get("apply_url") or raw_job.get("source_url") or "").strip()
    first_seen = existing.get("first_seen") or previous_first_seen_by_apply_url.get(apply_url) or checked_at
    seen_jobs[job_id] = {"first_seen": first_seen}
    return first_seen


def build_company_rows(
    companies: list[dict[str, Any]],
    active_jobs: list[dict[str, Any]],
    synced_slugs: set[str],
    checked_at: str,
) -> list[dict[str, Any]]:
    counts = Counter(job["company_slug"] for job in active_jobs)
    rows: list[dict[str, Any]] = []
    existing_rows = {
        row.get("slug"): row
        for row in read_json(PUBLIC_DATA / "companies.json", [])
        if isinstance(row, dict)
    }
    for company in companies:
        slug = company["slug"]
        previous = existing_rows.get(slug, {})
        rows.append(
            {
                "name": company["name"],
                "slug": slug,
                "company_group": company.get("company_group", "other"),
                "career_url": company.get("career_url", ""),
                "source_type": company.get("source_type", "placeholder"),
                "active_job_count": counts.get(slug, previous.get("active_job_count", 0)),
                "last_synced": checked_at if slug in synced_slugs else previous.get("last_synced", ""),
            }
        )
    return sorted(rows, key=lambda item: (item["company_group"] != "big_tech", item["name"].lower()))


def run(priority: int | None, include_all: bool) -> None:
    checked_at = utc_now()
    companies = load_companies()
    selected = select_companies(companies, priority, include_all)
    seen_jobs = read_json(PUBLIC_DATA / "seen_jobs.json", {})
    previous_jobs = read_json(PUBLIC_DATA / "jobs.json", [])
    previous_first_seen_by_apply_url: dict[str, str] = {}
    for job in previous_jobs:
        if not isinstance(job, dict):
            continue
        apply_url = str(job.get("apply_url") or "").strip()
        first_seen = str(job.get("first_seen") or "").strip()
        if not apply_url or not first_seen:
            continue
        previous = previous_first_seen_by_apply_url.get(apply_url)
        if not previous or first_seen < previous:
            previous_first_seen_by_apply_url[apply_url] = first_seen
    previous_by_unsynced_company = {
        job["id"]: job
        for job in previous_jobs
        if job.get("company_slug") not in {company["slug"] for company in selected}
    }
    previous_by_company_slug: dict[str, list[dict[str, Any]]] = {}
    for job in previous_jobs:
        if not isinstance(job, dict):
            continue
        company_slug = str(job.get("company_slug") or "")
        if company_slug:
            previous_by_company_slug.setdefault(company_slug, []).append(job)

    normalized_jobs: list[dict[str, Any]] = list(previous_by_unsynced_company.values())
    synced_slugs: set[str] = set()

    for company in selected:
        LOGGER.info("Fetching %s via %s", company.get("name"), company.get("source_type"))
        raw_jobs = fetch_raw_jobs(company)
        if raw_jobs is None:
            normalized_jobs.extend(previous_by_company_slug.get(company["slug"], []))
            continue
        synced_slugs.add(company["slug"])
        for raw_job in raw_jobs:
            first_seen = merge_first_seen(raw_job, company, seen_jobs, checked_at, previous_first_seen_by_apply_url)
            job = normalize_job(raw_job, company, checked_at, first_seen)
            if is_relevant_technical_job(job):
                normalized_jobs.append(job)

    if selected and not synced_slugs:
        LOGGER.warning("No selected sources synced successfully; leaving public data unchanged")
        return

    active_jobs = dedupe_jobs(normalized_jobs)
    active_jobs.sort(key=lambda item: item.get("first_seen", ""), reverse=True)

    companies_json = build_company_rows(companies, active_jobs, synced_slugs, checked_at)
    fresh_24h = 0
    checked_at_dt = datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
    for job in active_jobs:
        first_seen_dt = datetime.fromisoformat(job["first_seen"].replace("Z", "+00:00"))
        if (checked_at_dt - first_seen_dt).total_seconds() <= 24 * 60 * 60:
            fresh_24h += 1

    write_json(PUBLIC_DATA / "jobs.json", active_jobs)
    write_json(PUBLIC_DATA / "companies.json", companies_json)
    write_json(PUBLIC_DATA / "seen_jobs.json", seen_jobs)
    write_json(
        PUBLIC_DATA / "last_updated.json",
        {
            "last_updated": checked_at,
            "total_jobs": len(active_jobs),
            "big_tech_jobs": sum(1 for job in active_jobs if job.get("company_group") == "big_tech"),
            "fresh_24h_jobs": fresh_24h,
            "sources_synced": len(synced_slugs),
        },
    )
    LOGGER.info("Wrote %s active jobs from %s synced sources", len(active_jobs), len(synced_slugs))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch and normalize public tech jobs")
    parser.add_argument("--priority", type=int, choices=[1, 2, 3], help="Sync only this priority")
    parser.add_argument("--all", action="store_true", help="Sync every enabled company")
    return parser.parse_args()


if __name__ == "__main__":
    setup_logging()
    args = parse_args()
    run(priority=args.priority, include_all=args.all)
