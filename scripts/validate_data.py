"""Validate the published snapshot and its lazily loaded description files."""
from __future__ import annotations

from collections import Counter
from datetime import datetime

from fetch_jobs import PUBLIC_DATA, load_companies
from utils import read_json


def validate() -> None:
    jobs = read_json(PUBLIC_DATA / "jobs.json", None)
    companies = read_json(PUBLIC_DATA / "companies.json", None)
    summary = read_json(PUBLIC_DATA / "last_updated.json", None)
    assert isinstance(jobs, list) and isinstance(companies, list) and isinstance(summary, dict), "Missing snapshot files"
    assert len({job["id"] for job in jobs}) == len(jobs), "Duplicate job IDs"
    assert {c["slug"] for c in companies} == {c["slug"] for c in load_companies()}, "Catalog mismatch"
    counts = Counter(job["company_slug"] for job in jobs)
    assert set(counts) <= {company["slug"] for company in companies}, "Unknown company in jobs"
    assert sum(company["active_job_count"] for company in companies) == len(jobs), "Company counts do not sum to total"
    full = Counter(job["company_slug"] for job in jobs if job.get("description_status") == "full")
    for company in companies:
        assert company["active_job_count"] == counts[company["slug"]], company["slug"]
        assert company.get("full_description_count", 0) == full[company["slug"]], company["slug"]
        details = read_json(PUBLIC_DATA / "descriptions" / f"{company['slug']}.json", {})
        for job in jobs:
            if job["company_slug"] != company["slug"]:
                continue
            datetime.fromisoformat(job["first_seen"].replace("Z", "+00:00"))
            assert job["is_us_based"] and job["category"] != "Other", job["id"]
            if job.get("description_path"):
                assert job["id"] in details and details[job["id"]].get("text"), job["id"]
            if job.get("description_status") == "full":
                assert details[job["id"]]["status"] == "full", job["id"]
            assert "description_text" not in job, "Full bodies must be loaded separately"
    assert summary["total_jobs"] == len(jobs)
    assert summary.get("full_description_jobs", 0) == sum(full.values())
    history = read_json(PUBLIC_DATA / "history.json", None)
    assert isinstance(history, list), "Missing daily job history"
    assert [point["date"] for point in history] == sorted({point["date"] for point in history}), "History dates must be unique and sorted"
    for point in history:
        recorded = datetime.fromisoformat(point["recorded_at"].replace("Z", "+00:00"))
        assert recorded.utcoffset().total_seconds() == 0 and recorded.date().isoformat() == point["date"], "History must use UTC days"
        assert type(point["total_jobs"]) is int and point["total_jobs"] >= 0
        assert type(point["companies_with_jobs"]) is int and point["companies_with_jobs"] >= 0
        assert point.get("failed_sources", 0) >= 0
    if summary.get("sync_status") != "failed" and summary.get("sources_synced", 0) > 0:
        assert history and history[-1]["recorded_at"] == summary["last_updated"], "History is missing the latest snapshot"
        assert history[-1]["total_jobs"] == len(jobs), "History count does not match jobs"
    print(f"Snapshot valid: {len(jobs)} jobs, {len(companies)} companies, {sum(full.values())} full JDs")


if __name__ == "__main__":
    validate()
