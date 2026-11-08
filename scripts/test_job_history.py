import json
from pathlib import Path
from tempfile import TemporaryDirectory

from job_history import history_point, merge_history, record_history


def test_utc_days_and_latest_snapshot_win_without_inventing_missing_dates():
    first = history_point({"last_updated": "2026-11-05T17:00:00-08:00", "total_jobs": 3, "sources_synced": 1}, [{"active_job_count": 3}, {"active_job_count": 0}])
    assert first["date"] == "2026-11-06" and first["recorded_at"] == "2026-11-06T01:00:00Z"
    assert first["companies_with_jobs"] == 1 and "failed_sources" not in first
    later = {**first, "recorded_at": "2026-11-06T10:00:00Z", "total_jobs": 2}
    history = merge_history(merge_history([], first), later)
    assert merge_history(history, first) == [later]
    history = merge_history(history, {**later, "date": "2026-11-08", "recorded_at": "2026-11-08T01:00:00Z"})
    assert [point["date"] for point in history] == ["2026-11-06", "2026-11-08"]


def test_partial_snapshots_record_failure_context_and_total_failure_does_not_overwrite():
    companies = [{"active_job_count": 2, "sync_status": "failed"}, {"active_job_count": 3, "sync_status": "success"}]
    summary = {"last_updated": "2026-11-06T01:00:00Z", "total_jobs": 5, "sources_synced": 1, "sync_status": "partial"}
    with TemporaryDirectory() as directory:
        root = Path(directory)
        record_history(root, summary, companies)
        history = json.loads((root / "history.json").read_text())
        assert history[0]["failed_sources"] == 1 and history[0]["total_jobs"] == 5
        record_history(root, {**summary, "sync_status": "failed", "sources_synced": 0}, companies)
        assert json.loads((root / "history.json").read_text()) == history
    for invalid in ({}, {**summary, "total_jobs": -1}, {**summary, "total_jobs": True}, {**summary, "last_updated": "invalid"}):
        assert history_point(invalid, companies) is None


def test_comparable_counts_keep_synced_zeroes_and_exclude_unavailable_sources():
    tracked = {"source_type": "greenhouse", "active_job_count": 4, "last_synced": "2026-11-06T01:00:00Z"}
    companies = [
        {**tracked, "slug": "established"},
        {**tracked, "slug": "zero", "active_job_count": 0},
        {**tracked, "slug": "new", "last_synced": ""},
        {**tracked, "slug": "failed", "sync_status": "failed"},
        {**tracked, "slug": "disabled", "enabled": False},
    ]
    point = history_point({"last_updated": "2026-11-06T01:00:00Z", "total_jobs": 16}, companies)
    assert point["comparable_jobs"] == {"established:greenhouse": 4, "zero:greenhouse": 0}


if __name__ == "__main__":
    test_utc_days_and_latest_snapshot_win_without_inventing_missing_dates()
    test_partial_snapshots_record_failure_context_and_total_failure_does_not_overwrite()
    test_comparable_counts_keep_synced_zeroes_and_exclude_unavailable_sources()
    print("job history tests passed")
