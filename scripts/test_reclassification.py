from reclassify_jobs import reclassify_job


def test_reclassification_uses_complete_jd_without_changing_identity_or_freshness() -> None:
    previous = {"id": "example-1", "company_slug": "example", "title": "Software Engineering Analyst - Campus", "level": "Unknown", "first_seen": "2026-01-01T00:00:00Z", "last_checked": "2026-11-05T00:00:00Z"}
    updated = reclassify_job(previous, {"status": "full", "text": "Requirements\nMaster's or PhD in CS.\nWe cannot sponsor this position."})
    assert updated["level"] == "New Grad" and updated["phd_requirement"] == "optional"
    assert updated["visa_signal"] == "not_likely"
    for key in ("id", "first_seen", "last_checked"):
        assert updated[key] == previous[key]


def test_missing_jd_is_unknown_and_explicit_intern_hint_is_preserved() -> None:
    previous = {"title": "Software Engineer", "level": "Unknown", "visa_signal": "strong"}
    updated = reclassify_job(previous, {"status": "summary", "text": "We sponsor..."})
    assert updated["visa_signal"] == "unknown"
    updated = reclassify_job(previous, {"status": "full", "text": "Build software.", "level_hint": "Intern"})
    assert updated["level"] == "Intern"
    previous.update(level="New Grad")
    assert reclassify_job(previous, {"status": "full", "text": "Build software."})["level"] == "New Grad"


if __name__ == "__main__":
    test_reclassification_uses_complete_jd_without_changing_identity_or_freshness()
    test_missing_jd_is_unknown_and_explicit_intern_hint_is_preserved()
    print("reclassification tests passed")
