from __future__ import annotations

from adapters import workday
from unittest.mock import patch


def test_workday_filters_shared_tenant_by_title() -> None:
    original_post = workday.http_post_json
    original_terms = workday.TECH_SEARCH_TERMS

    def fake_post(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "total": 2,
            "jobPostings": [
                {
                    "title": "Oliver Wyman - Software Engineer",
                    "externalPath": "/job/one",
                    "locationsText": "New York, NY",
                    "bulletFields": ["R_1"],
                },
                {
                    "title": "Marsh - Software Engineer",
                    "externalPath": "/job/two",
                    "locationsText": "Chicago, IL",
                    "bulletFields": ["R_2"],
                },
            ],
        }

    workday.http_post_json = fake_post
    workday.TECH_SEARCH_TERMS = ["software"]
    try:
        jobs = workday.fetch_company_jobs(
            {
                "source_key": "mmc.wd1/MMC",
                "source_title_contains": "Oliver Wyman",
            }
        )
    finally:
        workday.http_post_json = original_post
        workday.TECH_SEARCH_TERMS = original_terms

    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "R_1"
    assert jobs[0]["title"] == "Oliver Wyman - Software Engineer"


def test_workday_merges_experienced_and_campus_boards() -> None:
    def fake_post(url: str, *_args: object, **_kwargs: object) -> dict:
        campus = "/Campus/" in url
        return {"total": 1, "jobPostings": [{"title": "Software Engineer Intern" if campus else "Software Engineer", "externalPath": "/job/one", "locationsText": "New York, NY", "bulletFields": ["CAMPUS" if campus else "REGULAR"]}]}
    with patch.object(workday, "http_post_json", side_effect=fake_post), patch.object(workday, "TECH_SEARCH_TERMS", ["software"]):
        jobs = workday.fetch_company_jobs({"source_key": "example.wd3/Experienced", "additional_source_keys": ["example.wd3/Campus", "example.wd3/Experienced"]})
    assert {job["external_id"] for job in jobs} == {"CAMPUS", "REGULAR"}


if __name__ == "__main__":
    test_workday_filters_shared_tenant_by_title()
    test_workday_merges_experienced_and_campus_boards()
    print("Workday adapter tests passed")
