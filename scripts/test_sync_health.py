import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import fetch_jobs


def test_partial_sync_removes_closed_jobs_and_preserves_failed_and_unscheduled_sources() -> None:
    companies = [{"name": slug, "slug": slug, "source_type": "greenhouse", "enabled": True, "sync_priority": priority} for slug, priority in [("closed", 1), ("failed", 1), ("unscheduled", 2)]]
    previous = [{"id": slug + "-1", "company_slug": slug, "first_seen": "2026-01-01T00:00:00Z", "company_group": "public"} for slug in ["closed", "failed", "unscheduled"]]
    with TemporaryDirectory() as directory:
        root = Path(directory) / "public"
        root.mkdir()
        seen_path = root.parent / "seen_jobs.json"
        seen = {"closed-1": {"first_seen": "2026-01-01T00:00:00Z"}}
        seen_path.write_text(json.dumps(seen))
        (root / "jobs.json").write_text(json.dumps(previous))
        (root / "companies.json").write_text(json.dumps([{"slug": c["slug"], "active_job_count": 1, "last_synced": "2026-01-01T00:00:00Z"} for c in companies]))
        with patch.object(fetch_jobs, "PUBLIC_DATA", root), patch.object(fetch_jobs, "SEEN_JOBS", seen_path), patch.object(fetch_jobs, "load_companies", return_value=companies), patch.object(fetch_jobs, "fetch_raw_jobs", side_effect=lambda c: None if c["slug"] == "failed" else []):
            assert fetch_jobs.run(1, False)
        assert json.loads(seen_path.read_text()) == seen
        assert not (root / "seen_jobs.json").exists()
        jobs = json.loads((root / "jobs.json").read_text())
        rows = {c["slug"]: c for c in json.loads((root / "companies.json").read_text())}
        summary = json.loads((root / "last_updated.json").read_text())
        assert {j["company_slug"] for j in jobs} == {"failed", "unscheduled"}
        assert rows["closed"]["active_job_count"] == 0
        assert rows["failed"]["active_job_count"] == 1 and rows["failed"]["sync_status"] == "failed"
        assert rows["failed"]["last_synced"] == "2026-01-01T00:00:00Z"
        assert not rows["unscheduled"]["last_attempted"]
        assert summary["sync_status"] == "partial" and summary["sources_failed"] == 1
        assert sum(c["active_job_count"] for c in rows.values()) == len(jobs)
        history = json.loads((root / "history.json").read_text())
        assert len(history) == 1 and history[0]["total_jobs"] == len(jobs)
        assert history[0]["failed_sources"] == 1


def test_total_failure_does_not_claim_new_success() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "last_updated.json").write_text(json.dumps({"last_updated": "2026-01-01T00:00:00Z"}))
        company = {"name": "Failed", "slug": "failed", "source_type": "greenhouse"}
        with patch.object(fetch_jobs, "PUBLIC_DATA", root), patch.object(fetch_jobs, "SEEN_JOBS", root / "seen_jobs.json"), patch.object(fetch_jobs, "load_companies", return_value=[company]), patch.object(fetch_jobs, "fetch_raw_jobs", return_value=None):
            assert fetch_jobs.run(None, True) is False
        summary = json.loads((root / "last_updated.json").read_text())
        assert summary["last_updated"] == "2026-01-01T00:00:00Z"
        assert summary["sync_status"] == "failed" and summary["sources_synced"] == 0
        assert not (root / "history.json").exists()


def test_malformed_source_is_isolated_without_discarding_its_cache() -> None:
    company = {"name": "Malformed", "slug": "malformed", "source_type": "greenhouse"}
    cache = {"malformed-1": {"text": "Previous complete description"}}
    with patch.object(fetch_jobs, "fetch_raw_jobs", return_value=[{"title": "Software Engineer"}]), patch.object(fetch_jobs, "normalize_job", side_effect=ValueError("Malformed source record")):
        jobs, retained = fetch_jobs._fetch_with_details((company, cache, "2026-11-05T00:00:00Z"))
    assert jobs is None and retained == cache
    assert company["_fetch_error"] == "ValueError"


if __name__ == "__main__":
    test_partial_sync_removes_closed_jobs_and_preserves_failed_and_unscheduled_sources()
    test_total_failure_does_not_claim_new_success()
    test_malformed_source_is_isolated_without_discarding_its_cache()
    print("sync health tests passed")
