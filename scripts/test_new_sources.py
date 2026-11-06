from __future__ import annotations

from unittest.mock import patch

from adapters import greenhouse, lever, talentbrew
from classifier import classify_category, classify_level
from fetch_jobs import build_company_rows, select_companies
from normalizer import normalize_job


def test_duolingo_merges_both_boards_and_deduplicates() -> None:
    def fake_get(url: str, **_kwargs: object) -> dict:
        identifier = 2 if "duolingounirecruitment/" in url else 1
        return {"jobs": [{"id": identifier, "title": "Software Engineer Intern", "location": {"name": "New York, NY"}}]}

    with patch.object(greenhouse, "http_get_json", side_effect=fake_get) as request:
        jobs = greenhouse.fetch_company_jobs({"source_key": "duolingo", "additional_source_keys": ["duolingounirecruitment", "duolingo"]})
    assert {job["external_id"] for job in jobs} == {"1", "2"}
    assert request.call_count == 2


def test_board_failure_does_not_return_partial_company_snapshot() -> None:
    def fake_get(url: str, **_kwargs: object) -> dict:
        if "university/" in url:
            raise RuntimeError("Source unavailable")
        return {"jobs": [{"id": 1, "title": "Software Engineer"}]}
    with patch.object(greenhouse, "http_get_json", side_effect=fake_get):
        try:
            greenhouse.fetch_company_jobs({"source_key": "industry", "additional_source_keys": ["university"]})
        except RuntimeError:
            pass
        else:
            raise AssertionError("An incomplete board sync must preserve previous company data")


def test_duolingo_deduplicates_requisitions_with_different_posting_ids() -> None:
    def fake_get(url: str, **_kwargs: object) -> dict:
        campus = "university/" in url
        return {"jobs": [{"id": 2 if campus else 1, "internal_job_id": 42, "title": "Research Engineer", "location": {"name": "Pittsburgh, PA; New York, NY" if campus else "New York, NY; Pittsburgh, PA"}}]}
    with patch.object(greenhouse, "http_get_json", side_effect=fake_get):
        jobs = greenhouse.fetch_company_jobs({"source_key": "industry", "additional_source_keys": ["university"]})
    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "1"


def test_explicit_intern_metadata_classifies_generic_titles() -> None:
    posting = {"id": 1, "title": "Software Engineer", "location": {"name": "New York, NY"}, "metadata": [{"name": "Employment Type", "value": "Summer Internship"}]}
    with patch.object(greenhouse, "http_get_json", return_value={"jobs": [posting]}):
        raw = greenhouse.fetch_company_jobs({"source_key": "example"})[0]
    job = normalize_job(raw, {"name": "Example", "slug": "example"}, "now", "then")
    assert job["level"] == "Intern"
    raw["title"] = "Senior Software Engineer"
    assert normalize_job(raw, {"name": "Example", "slug": "example"}, "now", "then")["level"] == "Senior"


def test_lever_qualification_lists_reach_education_classifier() -> None:
    posting = {
        "id": "1", "text": "Research Engineer", "categories": {"location": "New York, NY"},
        "descriptionPlain": "Build research tools.",
        "lists": [{"text": "Minimum Qualifications", "content": "<li>A Master's or PhD in CS.</li>"}],
    }
    with patch.object(lever, "http_get_json", return_value=[posting]):
        raw = lever.fetch_company_jobs({"source_key": "example"})[0]
    job = normalize_job(raw, {"name": "Example", "slug": "example"}, "now", "then")
    assert job["phd_requirement"] == "optional"


def test_campus_programs_are_classified() -> None:
    for title in ["Technology Development Program Associate - August 2027", "Software Engineer Program - Full-Time - United States"]:
        assert classify_category(title) == "SDE"
        assert classify_level(title) == "New Grad"
    assert classify_level("Software Engineer Graduate - 2027 Start (BS/MS)") == "New Grad"
    assert classify_level("Software Engineer (C++ or Python) - 2027 Grads") == "New Grad"
    assert classify_category("Algorithm Developer - 2027 Grads") == "Quant"


def test_successful_zero_job_sync_resets_count() -> None:
    with patch("fetch_jobs.read_json", return_value=[{"slug": "example", "active_job_count": 5}]):
        row = build_company_rows([{"name": "Example", "slug": "example", "enabled": False}], [], {"example"}, "now")[0]
    assert row["active_job_count"] == 0
    assert row["enabled"] is False


def test_targeted_sync_validates_slugs_and_skips_disabled_sources() -> None:
    configs = [{"slug": "active", "enabled": True}, {"slug": "disabled", "enabled": False}]
    assert select_companies(configs, None, False, ["active", "disabled"]) == [configs[0]]
    try:
        select_companies(configs, None, False, ["typo"])
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown company slug must be rejected")


def test_talentbrew_accepts_campus_search_terms() -> None:
    with patch.object(talentbrew, "http_post_json", return_value={"results": ""}) as request:
        talentbrew.fetch_company_jobs({"career_url": "https://jobs.example.com", "source_key": "234", "source_search_terms": ["technology development program"]})
    assert request.call_count == 1
    assert request.call_args.args[1]["Keywords"] == "technology development program"


if __name__ == "__main__":
    for name, value in list(globals().items()):
        if name.startswith("test_"):
            value()
    print("new source regression tests passed")
