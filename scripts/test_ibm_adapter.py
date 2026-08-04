from __future__ import annotations

from adapters import ibm


def test_ibm_maps_and_deduplicates_jobs() -> None:
    original_get = ibm.http_get_json
    original_terms = ibm.TECH_SEARCH_TERMS
    ibm.http_get_json = lambda *_args, **_kwargs: {
        "resultset": {
            "searchresults": {
                "totalresults": 1,
                "searchresultlist": [
                    {
                        "title": "Software Engineer",
                        "description": "Fallback description",
                        "url": "https://careers.ibm.com/careers/JobDetail?jobId=127189",
                        "docattributes": [
                            {"field_text_01": "127189"},
                            {"field_keyword_05": "United States"},
                            {"field_keyword_19": "Yorktown Heights, US"},
                            {"raw_body": "<p>Build software.</p>"},
                        ],
                    }
                ],
            }
        }
    }
    ibm.TECH_SEARCH_TERMS = ["software", "data"]
    try:
        jobs = ibm.fetch_company_jobs(
            {
                "career_url": "https://www.ibm.com/careers/search",
                "source_base_url": "https://www-api.ibm.com/search/api/v1/ibmcom/appid/careers/responseFormat/json",
            }
        )
    finally:
        ibm.http_get_json = original_get
        ibm.TECH_SEARCH_TERMS = original_terms

    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "127189"
    assert jobs[0]["location_raw"] == "Yorktown Heights, US"
    assert jobs[0]["description"] == "<p>Build software.</p>"


if __name__ == "__main__":
    test_ibm_maps_and_deduplicates_jobs()
    print("IBM adapter tests passed")
