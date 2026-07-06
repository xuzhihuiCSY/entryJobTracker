from __future__ import annotations

from adapters.ashby import _location_from_job
from adapters.greenhouse import _job_locations, _primary_location


def test_greenhouse_uses_office_locations_before_generic_location() -> None:
    job = {
        "location": {"name": "Hybrid"},
        "offices": [
            {"name": "Austin, TX", "location": "Austin, TX, United States"},
            {"name": "London, United Kingdom", "location": "London, United Kingdom"},
        ],
    }

    locations = _job_locations(job)

    assert locations == ["Austin, TX, United States", "London, United Kingdom"]
    assert _primary_location(locations) == "Austin, TX, United States"


def test_ashby_north_america_us_address_becomes_remote_us() -> None:
    job = {
        "location": "North America",
        "isRemote": True,
        "address": {"postalAddress": {"addressCountry": "United States"}},
    }

    assert _location_from_job(job) == "Remote, United States"


if __name__ == "__main__":
    test_greenhouse_uses_office_locations_before_generic_location()
    test_ashby_north_america_us_address_becomes_remote_us()
    print("location adapter tests passed")
