from __future__ import annotations

from adapters import bank_of_america


def test_bank_of_america_maps_and_deduplicates_jobs() -> None:
    original_get = bank_of_america.http_get_json
    original_terms = bank_of_america.TECH_SEARCH_TERMS
    bank_of_america.http_get_json = lambda *_args, **_kwargs: {
        "totalMatches": 1,
        "jobsList": [
            {
                "jobRequisitionId": "26024269",
                "postingTitle": "Software Engineer",
                "jcrURL": "/en-us/job-detail/26024269/software-engineer",
                "primaryLocation": "Charlotte, North Carolina",
                "additionalLocations": "New York, New York",
            }
        ],
    }
    bank_of_america.TECH_SEARCH_TERMS = ["software", "data engineer"]
    try:
        jobs = bank_of_america.fetch_company_jobs(
            {
                "career_url": "https://careers.bankofamerica.com/en-us/job-search",
                "source_base_url": "https://careers.bankofamerica.com/services/jobssearchservlet",
            }
        )
    finally:
        bank_of_america.http_get_json = original_get
        bank_of_america.TECH_SEARCH_TERMS = original_terms

    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "26024269"
    assert jobs[0]["location_raw"] == "Charlotte, North Carolina; New York, New York"
    assert jobs[0]["apply_url"].endswith("/en-us/job-detail/26024269/software-engineer")


if __name__ == "__main__":
    test_bank_of_america_maps_and_deduplicates_jobs()
    print("Bank of America adapter tests passed")
