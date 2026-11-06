from __future__ import annotations

from unittest.mock import patch

from adapters.uber import SEARCH_URL, _raw_job, fetch_company_jobs


def test_raw_job_maps_uber_fields() -> None:
    raw = _raw_job(
        {
            "Id": "160010",
            "Reference": "160010",
            "Title": "Software Engineer",
            "Description": "<p>Build systems.</p>",
            "Locations": [
                {
                    "City": "Sunnyvale",
                    "Region": "California",
                    "Country": "United States",
                    "Address": "Sunnyvale, CA, USA",
                }
            ],
            "Urls": [{"Culture": "en-us", "Url": "/en/jobs/160010/", "IsDefault": True}],
        }
    )

    assert raw["external_id"] == "160010"
    assert raw["title"] == "Software Engineer"
    assert raw["location_raw"] == "Sunnyvale, CA, USA"
    assert raw["locations"] == ["Sunnyvale, CA, USA"]
    assert raw["apply_url"] == "https://jobs.uber.com/en/jobs/160010/"
    assert raw["source_platform"] == "uber"


def test_fetches_all_pages_and_deduplicates_search_terms() -> None:
    pages = [
        {"jobs": [{"Id": "1", "Title": "Software Engineer"}], "totalPages": 2},
        {"jobs": [{"Id": "2", "Title": "Software Engineer Intern"}], "totalPages": 2},
        {"jobs": [{"Id": "1", "Title": "Software Engineer"}], "totalPages": 1},
    ]
    with patch("adapters.uber.SEARCH_TERMS", ["software", "intern"]), patch(
        "adapters.uber.http_get_json", side_effect=pages
    ) as get:
        jobs = fetch_company_jobs({})
    assert [job["external_id"] for job in jobs] == ["1", "2"]
    assert [call.kwargs["params"]["page"] for call in get.call_args_list] == [1, 2, 1]
    assert all(call.args[0] == SEARCH_URL for call in get.call_args_list)
    assert SEARCH_URL.endswith("/api/jobs/search/")
    assert all(call.kwargs["params"]["countries"] == "United States" for call in get.call_args_list)
    assert all(call.kwargs["params"]["pagesize"] == 100 for call in get.call_args_list)


def test_failed_or_invalid_responses_never_become_empty_successes() -> None:
    for payload in ({"error": "unavailable"}, [], {"jobs": {}}, {"jobs": [], "totalPages": 201}):
        with patch("adapters.uber.http_get_json", return_value=payload):
            try:
                fetch_company_jobs({})
            except ValueError:
                pass
            else:
                raise AssertionError(f"Accepted an invalid Uber response: {payload!r}")
    with patch("adapters.uber.http_get_json", side_effect=RuntimeError("HTTP 403")):
        try:
            fetch_company_jobs({})
        except RuntimeError:
            pass
        else:
            raise AssertionError("A failed Uber request must preserve the previous snapshot")


if __name__ == "__main__":
    test_raw_job_maps_uber_fields()
    test_fetches_all_pages_and_deduplicates_search_terms()
    test_failed_or_invalid_responses_never_become_empty_successes()
    print("uber adapter tests passed")
