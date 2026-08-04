from __future__ import annotations

from adapters import talentbrew


def _results_page(page: int, total_pages: int = 2) -> str:
    return f"""
    <section id="search-results" data-total-pages="{total_pages}">
      <ul>
        <li class="sr-job-item">
          <a class="sr-job-item__link" data-job-id="job-{page}"
             href="/job/austin/software-engineer/287/job-{page}">Software Engineer {page}</a>
          <span class="sr-job-location">Austin, Texas, United States</span>
        </li>
      </ul>
    </section>
    """


def test_talentbrew_paginates_and_maps_jobs() -> None:
    calls: list[tuple[str, dict]] = []

    def fake_post_json(url: str, payload: dict) -> dict:
        calls.append((url, payload))
        return {"hasJobs": True, "results": _results_page(payload["CurrentPage"])}

    original_post_json = talentbrew.http_post_json
    original_terms = talentbrew.TECH_SEARCH_TERMS
    talentbrew.http_post_json = fake_post_json
    talentbrew.TECH_SEARCH_TERMS = ["software engineer"]
    try:
        jobs = talentbrew.fetch_company_jobs(
            {"career_url": "https://jobs.example.com/", "source_key": "287"}
        )
    finally:
        talentbrew.http_post_json = original_post_json
        talentbrew.TECH_SEARCH_TERMS = original_terms

    assert [payload["CurrentPage"] for _, payload in calls] == [1, 2]
    assert all(url == "https://jobs.example.com/search-jobs/resultspost" for url, _ in calls)
    assert [job["external_id"] for job in jobs] == ["job-1", "job-2"]
    assert jobs[0]["apply_url"] == "https://jobs.example.com/job/austin/software-engineer/287/job-1"
    assert jobs[0]["location_raw"] == "Austin, Texas, United States"
    assert jobs[0]["source_platform"] == "talentbrew"


def test_talentbrew_parses_alternate_theme_markup() -> None:
    html = """
    <section id="search-results" data-total-pages="1">
      <section id="search-results-list">
        <ul><li>
          <a data-job-id="job-3" href="/job/new-york/ai-engineer/932/job-3">
            <h2>AI Engineer</h2>
            <span class="job-location">Multiple Locations</span>
          </a>
        </li></ul>
      </section>
    </section>
    """

    jobs, total_pages = talentbrew._parse_results(
        html,
        "https://jobs.example.com/",
        "United States",
    )

    assert total_pages == 1
    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "job-3"
    assert jobs[0]["title"] == "AI Engineer"
    assert jobs[0]["location_raw"] == "New York, United States"


if __name__ == "__main__":
    test_talentbrew_paginates_and_maps_jobs()
    test_talentbrew_parses_alternate_theme_markup()
    print("TalentBrew adapter tests passed")
