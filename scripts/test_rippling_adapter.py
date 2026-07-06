from __future__ import annotations

from adapters.rippling import jobs_from_hits


def test_jobs_from_hits_filters_non_us_and_aggregates_locations() -> None:
    hits = [
        {
            "departmentName": "Engineering",
            "jobId": "job-1",
            "name": "Software Engineer",
            "url": "https://ats.rippling.com/rippling/jobs/job-1",
            "locationNames": ["San Francisco, CA"],
            "locations": [{"country": "United States", "countryCode": "US", "name": "San Francisco, CA"}],
        },
        {
            "departmentName": "Engineering",
            "jobId": "job-1",
            "name": "Software Engineer",
            "url": "https://ats.rippling.com/rippling/jobs/job-1",
            "locationNames": ["New York, NY"],
            "locations": [{"country": "United States", "countryCode": "US", "name": "New York, NY"}],
        },
        {
            "departmentName": "Engineering",
            "jobId": "job-2",
            "name": "Senior Software Engineer",
            "url": "https://ats.rippling.com/rippling/jobs/job-2",
            "locationNames": ["Bangalore, India"],
            "locations": [{"country": "India", "countryCode": "IN", "name": "Bangalore, India"}],
        },
        {
            "departmentName": "Marketing",
            "jobId": "job-3",
            "name": "Software Engineer",
            "url": "https://ats.rippling.com/rippling/jobs/job-3",
            "locationNames": ["Seattle, WA"],
            "locations": [{"country": "United States", "countryCode": "US", "name": "Seattle, WA"}],
        },
    ]

    jobs = jobs_from_hits(hits)

    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "job-1"
    assert jobs[0]["location_raw"] == "New York, NY"
    assert jobs[0]["locations"] == ["New York, NY", "San Francisco, CA"]
    assert jobs[0]["location_count"] == 2


if __name__ == "__main__":
    test_jobs_from_hits_filters_non_us_and_aggregates_locations()
    print("rippling adapter tests passed")
