from __future__ import annotations

from adapters.uber import _raw_job


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


if __name__ == "__main__":
    test_raw_job_maps_uber_fields()
    print("uber adapter tests passed")
