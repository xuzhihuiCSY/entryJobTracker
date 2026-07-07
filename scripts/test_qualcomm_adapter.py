from __future__ import annotations

from adapters.qualcomm import _raw_job


def test_raw_job_keeps_only_us_locations() -> None:
    raw = _raw_job(
        {
            "id": 446718450778,
            "displayJobId": "3091137",
            "atsJobId": "3091137",
            "name": "Senior Software Engineer",
            "department": "Software Engineering",
            "locations": [
                "San Diego, California, United States of America",
                "Cork, Ireland",
            ],
            "standardizedLocations": ["San Diego, CA, US", "Cork, CO, IE"],
            "positionUrl": "/careers/job/446718450778",
        }
    )

    assert raw is not None
    assert raw["external_id"] == "3091137"
    assert raw["title"] == "Senior Software Engineer"
    assert raw["location_raw"] == "San Diego, CA, US"
    assert raw["locations"] == ["San Diego, CA, US"]
    assert raw["apply_url"] == "https://careers.qualcomm.com/careers/job/446718450778"
    assert "Software Engineering" in raw["description"]
    assert raw["source_platform"] == "qualcomm"


def test_raw_job_drops_non_us_locations() -> None:
    raw = _raw_job(
        {
            "id": 1,
            "displayJobId": "1",
            "name": "Software Engineer",
            "locations": ["Cork, Ireland"],
            "standardizedLocations": ["Cork, CO, IE"],
        }
    )

    assert raw is None


if __name__ == "__main__":
    test_raw_job_keeps_only_us_locations()
    test_raw_job_drops_non_us_locations()
    print("qualcomm adapter tests passed")
