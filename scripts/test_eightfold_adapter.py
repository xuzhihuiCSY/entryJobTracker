from __future__ import annotations

import json
from html import escape

from adapters import eightfold


def _page_with_positions() -> str:
    state = {
        "companyName": "Example",
        "positions": [
            {
                "id": 123,
                "ats_job_id": "JR123",
                "name": "Software Engineer",
                "posting_name": "Software Engineer, Data Platform",
                "locations": ["Los Gatos, California, United States of America", "USA - Remote"],
                "job_description": "Build data services.",
                "canonicalPositionUrl": "https://example.com/careers/job/123",
            }
        ],
        "count": 1,
    }
    return f'<div data-state="{escape(json.dumps(state))}"></div>'


def test_extract_positions_from_html_encoded_state() -> None:
    positions = eightfold._extract_positions(_page_with_positions())

    assert len(positions) == 1
    assert positions[0]["ats_job_id"] == "JR123"


def test_fetch_company_jobs_deduplicates_search_results() -> None:
    original_get_text = eightfold.http_get_text
    eightfold.http_get_text = lambda *_args, **_kwargs: _page_with_positions()
    try:
        jobs = eightfold.fetch_company_jobs({"career_url": "https://example.com/careers"})
    finally:
        eightfold.http_get_text = original_get_text

    assert jobs == [
        {
            "external_id": "JR123",
            "title": "Software Engineer, Data Platform",
            "location_raw": "Los Gatos, California, United States of America; USA - Remote",
            "locations": ["Los Gatos, California, United States of America", "USA - Remote"],
            "location_count": 2,
            "description": "Build data services.",
            "apply_url": "https://example.com/careers/job/123",
            "source_url": "https://example.com/careers/job/123",
            "source_platform": "eightfold",
        }
    ]


if __name__ == "__main__":
    test_extract_positions_from_html_encoded_state()
    test_fetch_company_jobs_deduplicates_search_results()
    print("eightfold adapter tests passed")
