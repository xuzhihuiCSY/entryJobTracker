from __future__ import annotations

from adapters import mckinsey


def test_mckinsey_maps_us_locations_and_deduplicates_jobs() -> None:
    calls: list[dict[str, object]] = []
    original_get = mckinsey.http_get_json

    def fake_get(*_args: object, **kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {
            "numFound": 2,
            "docs": [
                {
                    "jobID": "109242",
                    "title": "Data Engineer II",
                    "cities": ["Atlanta", "Toronto", "Boston"],
                    "countries": ["United States", "Canada", "United States"],
                    "friendlyURL": "dataengineerii-109242",
                    "jobApplyURL": "https://mckinsey.avature.net/careers/ApplicationMethods?folderId=109242",
                    "whatYouWillDo": "<div>Build data pipelines.</div>",
                    "yourBackground": "Python experience.",
                },
                {
                    "jobID": "109242",
                    "title": "Data Engineer II",
                    "cities": ["Atlanta"],
                    "countries": ["United States"],
                },
            ],
        }

    mckinsey.http_get_json = fake_get
    try:
        jobs = mckinsey.fetch_company_jobs(
            {
                "career_url": "https://www.mckinsey.com/careers/search-jobs",
                "source_base_url": "https://gateway.mckinsey.com/example/v1/api/jobs/search",
                "source_interests": ["Tech & AI", "Technology & Digital"],
            }
        )
    finally:
        mckinsey.http_get_json = original_get

    assert len(calls) == 1
    assert calls[0]["params"]["start"] == 1  # type: ignore[index]
    assert calls[0]["params"]["interest"] == "Tech & AI,Technology & Digital"  # type: ignore[index]
    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "109242"
    assert jobs[0]["location_raw"] == "Atlanta, United States; Boston, United States"
    assert jobs[0]["locations"] == ["Atlanta, United States", "Boston, United States"]
    assert jobs[0]["source_url"].endswith("/jobs/dataengineerii-109242")
    assert jobs[0]["apply_url"].startswith("https://mckinsey.avature.net/")


if __name__ == "__main__":
    test_mckinsey_maps_us_locations_and_deduplicates_jobs()
    print("McKinsey adapter tests passed")
