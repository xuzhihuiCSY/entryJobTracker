from __future__ import annotations

from adapters import goldman_sachs


def test_goldman_sachs_maps_and_deduplicates_posted_roles() -> None:
    original_post = goldman_sachs.http_post_json
    original_terms = goldman_sachs.TECH_SEARCH_TERMS
    goldman_sachs.http_post_json = lambda *_args, **_kwargs: {
        "data": {
            "roleSearch": {
                "items": [
                    {
                        "roleId": "role-1",
                        "jobTitle": "Software Engineer | Associate",
                        "corporateTitle": "Associate",
                        "jobFunction": "Software Engineering",
                        "division": "Engineering Division",
                        "locations": [
                            {"city": "Dallas", "state": "TX", "country": "United States"}
                        ],
                        "status": "POSTED",
                        "skills": ["Python"],
                        "externalSource": {"sourceId": "180562"},
                    },
                    {"roleId": "closed", "status": "CLOSED", "externalSource": {"sourceId": "2"}},
                ]
            }
        }
    }
    goldman_sachs.TECH_SEARCH_TERMS = ["software", "data"]
    try:
        jobs = goldman_sachs.fetch_company_jobs(
            {
                "career_url": "https://higher.gs.com",
                "source_base_url": "https://api-higher.gs.com/gateway/api/v1/graphql",
            }
        )
    finally:
        goldman_sachs.http_post_json = original_post
        goldman_sachs.TECH_SEARCH_TERMS = original_terms

    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "180562"
    assert jobs[0]["location_raw"] == "Dallas, TX, United States"
    assert jobs[0]["apply_url"] == "https://higher.gs.com/roles/180562"


if __name__ == "__main__":
    test_goldman_sachs_maps_and_deduplicates_posted_roles()
    print("Goldman Sachs adapter tests passed")
