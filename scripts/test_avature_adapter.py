from __future__ import annotations

from adapters import avature


PAGE = """
<article class="article--result" data-total="1">
  <h3><a href="https://example.com/jobs/JobDetail/Software-Engineer/251115">Software Engineer</a></h3>
  <div class="article__header__text__subtitle"><span>New York</span><span>Posted today</span></div>
  <div class="article__content">Build beauty technology.</div>
</article>
"""


def test_avature_parses_search_results() -> None:
    jobs = avature._parse_jobs(PAGE, "https://example.com/jobs/SearchJobs")

    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "251115"
    assert jobs[0]["title"] == "Software Engineer"
    assert jobs[0]["location_raw"] == "New York"
    assert jobs[0]["description"] == "Build beauty technology."


def test_avature_deduplicates_search_terms() -> None:
    original_get = avature.http_get_text
    original_terms = avature.TECH_SEARCH_TERMS
    avature.http_get_text = lambda *_args, **_kwargs: PAGE
    avature.TECH_SEARCH_TERMS = ["software engineer", "data engineer"]
    try:
        jobs = avature.fetch_company_jobs(
            {
                "career_url": "https://example.com/jobs/SearchJobs",
                "source_base_url": "https://example.com/jobs/SearchJobsAJAX",
            }
        )
    finally:
        avature.http_get_text = original_get
        avature.TECH_SEARCH_TERMS = original_terms

    assert len(jobs) == 1


if __name__ == "__main__":
    test_avature_parses_search_results()
    test_avature_deduplicates_search_terms()
    print("Avature adapter tests passed")
