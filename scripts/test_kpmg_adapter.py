from __future__ import annotations

from adapters import kpmg


FRAGMENT = """
<div class="search--item">
  <a href="/jobdetail/?jobId=135815">
    <div class="list-view">
      <div class="h5">Associate Director, Software Engineer</div>
      <div class="text-xs">Tax | Atlanta, GA; Denver, CO</div>
    </div>
  </a>
</div>
"""


def test_kpmg_parses_jobs() -> None:
    jobs = kpmg._parse_jobs(FRAGMENT, "https://www.kpmguscareers.com/job-search/")

    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "135815"
    assert jobs[0]["title"] == "Associate Director, Software Engineer"
    assert jobs[0]["location_raw"] == "Atlanta, GA; Denver, CO"


def test_kpmg_deduplicates_terms_and_pages() -> None:
    original_get = kpmg.http_get_json
    original_terms = kpmg.TECH_SEARCH_TERMS
    kpmg.http_get_json = lambda *_args, **_kwargs: {"postings": {"jobs": FRAGMENT}}
    kpmg.TECH_SEARCH_TERMS = ["software", "data engineer"]
    try:
        jobs = kpmg.fetch_company_jobs(
            {
                "career_url": "https://www.kpmguscareers.com/job-search/",
                "source_base_url": "https://example.com/get-jobs.php",
            }
        )
    finally:
        kpmg.http_get_json = original_get
        kpmg.TECH_SEARCH_TERMS = original_terms

    assert len(jobs) == 1


if __name__ == "__main__":
    test_kpmg_parses_jobs()
    test_kpmg_deduplicates_terms_and_pages()
    print("KPMG adapter tests passed")
