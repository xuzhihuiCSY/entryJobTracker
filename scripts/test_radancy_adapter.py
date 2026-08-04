from __future__ import annotations

from adapters import radancy


def test_radancy_paginates_and_maps_jobs() -> None:
    calls: list[tuple[str, dict]] = []

    def fake_get_json(url: str, params: dict) -> dict:
        calls.append((url, params))
        job_number = params["page"]
        return {
            "count": 2,
            "jobs": [
                {
                    "data": {
                        "req_id": f"job-{job_number}",
                        "title": "Software Engineer",
                        "full_location": "Plano, TX, United States",
                        "description": "Build services.",
                        "responsibilities": "Write code.",
                        "qualifications": "Python experience.",
                        "apply_url": f"https://example.com/jobs/job-{job_number}",
                    }
                }
            ],
        }

    original_get_json = radancy.http_get_json
    original_terms = radancy.TECH_SEARCH_TERMS
    original_page_size = radancy.PAGE_SIZE
    radancy.http_get_json = fake_get_json
    radancy.TECH_SEARCH_TERMS = ["software engineer"]
    radancy.PAGE_SIZE = 1
    try:
        jobs = radancy.fetch_company_jobs(
            {"career_url": "https://example.com/careers/", "source_key": "/api/jobs"}
        )
    finally:
        radancy.http_get_json = original_get_json
        radancy.TECH_SEARCH_TERMS = original_terms
        radancy.PAGE_SIZE = original_page_size

    assert [params["page"] for _, params in calls] == [1, 2]
    assert all(url == "https://example.com/api/jobs" for url, _ in calls)
    assert [job["external_id"] for job in jobs] == ["job-1", "job-2"]
    assert jobs[0]["description"] == "Build services. Write code. Python experience."
    assert jobs[0]["source_platform"] == "radancy"


if __name__ == "__main__":
    test_radancy_paginates_and_maps_jobs()
    print("Radancy adapter tests passed")
