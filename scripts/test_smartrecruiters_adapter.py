from __future__ import annotations

from adapters import smartrecruiters


def test_smartrecruiters_paginates_and_maps_jobs() -> None:
    offsets: list[int] = []

    def fake_get_json(_url: str, params: dict) -> dict:
        offset = params["offset"]
        offsets.append(offset)
        if offset == 0:
            return {
                "totalFound": 2,
                "content": [
                    {
                        "id": "job-1",
                        "name": "Data Engineer",
                        "location": {"fullLocation": "Chicago, IL, United States"},
                    }
                ],
            }
        return {
            "totalFound": 2,
            "content": [
                {
                    "id": "job-2",
                    "name": "AI Specialist",
                    "location": {"fullLocation": "Boston, MA, United States"},
                }
            ],
        }

    original_get_json = smartrecruiters.http_get_json
    smartrecruiters.http_get_json = fake_get_json
    try:
        jobs = smartrecruiters.fetch_company_jobs({"source_key": "ExampleCompany"})
    finally:
        smartrecruiters.http_get_json = original_get_json

    assert offsets == [0, 1]
    assert [job["external_id"] for job in jobs] == ["job-1", "job-2"]
    assert jobs[0]["apply_url"] == "https://jobs.smartrecruiters.com/ExampleCompany/job-1"
    assert jobs[0]["location_raw"] == "Chicago, IL, United States"
    assert all(job["source_platform"] == "smartrecruiters" for job in jobs)


if __name__ == "__main__":
    test_smartrecruiters_paginates_and_maps_jobs()
    print("SmartRecruiters adapter tests passed")
