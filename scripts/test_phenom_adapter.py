from __future__ import annotations

import json

from adapters import phenom


def _page_with_jobs() -> str:
    payload = {
        "status": 200,
        "totalHits": 1,
        "data": {
            "jobs": [
                {
                    "reqId": "REQ-1",
                    "title": "AI Engineer",
                    "multi_location": [
                        "Boston, Massachusetts, United States",
                        "New York, New York, United States",
                    ],
                    "descriptionTeaser": "Build machine learning systems.",
                    "applyUrl": "https://example.com/job/1?show_apply=1&amp;source=careers",
                }
            ]
        },
    }
    return f'<script>window.state={{"eagerLoadRefineSearch":{json.dumps(payload)}}};</script>'


def test_phenom_extracts_embedded_jobs() -> None:
    jobs = phenom._extract_jobs(_page_with_jobs())

    assert len(jobs) == 1
    assert jobs[0]["reqId"] == "REQ-1"


def test_phenom_fetches_and_deduplicates_search_terms() -> None:
    original_get_text = phenom.http_get_text
    original_terms = phenom.TECH_SEARCH_TERMS
    phenom.http_get_text = lambda *_args, **_kwargs: _page_with_jobs()
    phenom.TECH_SEARCH_TERMS = ["software engineer", "machine learning"]
    try:
        jobs = phenom.fetch_company_jobs({"career_url": "https://example.com/search-results"})
    finally:
        phenom.http_get_text = original_get_text
        phenom.TECH_SEARCH_TERMS = original_terms

    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "REQ-1"
    assert jobs[0]["location_count"] == 2
    assert jobs[0]["apply_url"] == "https://example.com/job/1?show_apply=1&source=careers"
    assert jobs[0]["source_platform"] == "phenom"


if __name__ == "__main__":
    test_phenom_extracts_embedded_jobs()
    test_phenom_fetches_and_deduplicates_search_terms()
    print("Phenom adapter tests passed")
