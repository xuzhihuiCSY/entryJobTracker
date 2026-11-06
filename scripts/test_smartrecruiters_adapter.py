from __future__ import annotations

from adapters import smartrecruiters
from unittest.mock import patch
from normalizer import normalize_job


def test_smartrecruiters_paginates_and_maps_jobs() -> None:
    offsets: list[int] = []

    def fake_get_json(_url: str, params: dict) -> dict:
        offset = params["offset"]
        offsets.append(offset)
        if offset == 0:
            return {
                "totalFound": 2,
                "content": [
                    {
                        "id": "job-1",
                        "name": "Data Engineer",
                        "location": {"fullLocation": "Chicago, IL, United States"},
                    }
                ],
            }
        return {
            "totalFound": 2,
            "content": [
                {
                    "id": "job-2",
                    "name": "AI Specialist",
                    "location": {"fullLocation": "Boston, MA, United States"},
                }
            ],
        }

    original_get_json = smartrecruiters.http_get_json
    smartrecruiters.http_get_json = fake_get_json
    try:
        jobs = smartrecruiters.fetch_company_jobs({"source_key": "ExampleCompany"})
    finally:
        smartrecruiters.http_get_json = original_get_json

    assert offsets == [0, 1]
    assert [job["external_id"] for job in jobs] == ["job-1", "job-2"]
    assert jobs[0]["apply_url"] == "https://jobs.smartrecruiters.com/ExampleCompany/job-1"
    assert jobs[0]["location_raw"] == "Chicago, IL, United States"
    assert all(job["source_platform"] == "smartrecruiters" for job in jobs)


def test_servicenow_campus_metadata_and_seniority_precedence():
    posting = {"id": "1", "name": "Software Engineer", "location": {"fullLocation": "San Diego, CA, United States"},
               "customField": [{"fieldLabel": "Recruiting Team", "valueId": "early-in-career", "valueLabel": "Global Emerging Talent"},
                               {"fieldLabel": "Employee Type", "valueLabel": "Intern"}]}
    with patch.object(smartrecruiters, "http_get_json", return_value={"totalFound": 1, "content": [posting]}):
        raw = smartrecruiters.fetch_company_jobs({"source_key": "ServiceNow"})[0]
    company = {"slug": "servicenow", "name": "ServiceNow"}
    assert normalize_job(raw, company, "now", "then")["level"] == "Intern"
    raw["title"] = "Senior Software Engineer"
    assert normalize_job(raw, company, "now", "then")["level"] == "Senior"
    assert smartrecruiters._level_hint({"customField": [{"fieldLabel": "Job Posting Type", "valueLabel": "Early Career"}]}) == "Early Career"
    assert smartrecruiters._level_hint({"typeOfEmployment": {"id": "permanent", "label": "Full-time"}}) == ""


def test_malformed_and_truncated_lists_fail_instead_of_clearing_company_jobs():
    for data in ({}, {"totalFound": 2, "content": []}, {"totalFound": 2, "content": {}}):
        with patch.object(smartrecruiters, "http_get_json", return_value=data):
            try:
                smartrecruiters.fetch_company_jobs({"source_key": "ServiceNow"})
            except ValueError:
                pass
            else:
                raise AssertionError("An invalid posting list must fail")


if __name__ == "__main__":
    test_smartrecruiters_paginates_and_maps_jobs()
    test_servicenow_campus_metadata_and_seniority_precedence()
    test_malformed_and_truncated_lists_fail_instead_of_clearing_company_jobs()
    print("SmartRecruiters adapter tests passed")
