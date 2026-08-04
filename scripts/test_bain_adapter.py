from __future__ import annotations

from adapters import bain


def test_bain_maps_filters_and_deduplicates_jobs() -> None:
    original_get = bain.http_get_json
    bain.http_get_json = lambda *_args, **_kwargs: {
        "results": [
            {
                "JobId": "101",
                "JobTitle": "Software Engineer",
                "JobDescription": "Build products.",
                "Link": "/careers/find-a-role/position/?jobid=101",
                "Location": ["Boston ", "New York"],
                "Categories": ["Technology & Engineering"],
            },
            {
                "JobId": "101",
                "JobTitle": "Software Engineer",
                "Categories": ["Technology & Engineering"],
            },
            {
                "JobId": "102",
                "JobTitle": "Associate, Primary Research",
                "Categories": ["Analytics, Data, & Research"],
            },
        ]
    }
    try:
        jobs = bain.fetch_company_jobs(
            {
                "career_url": "https://www.bain.com/careers/find-a-role/",
                "source_base_url": "https://www.bain.com/en/api/jobsearch/keyword/get",
            }
        )
    finally:
        bain.http_get_json = original_get

    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "101"
    assert jobs[0]["location_raw"] == "Boston; New York"
    assert jobs[0]["apply_url"].endswith("/careers/find-a-role/position/?jobid=101")


if __name__ == "__main__":
    test_bain_maps_filters_and_deduplicates_jobs()
    print("Bain adapter tests passed")
