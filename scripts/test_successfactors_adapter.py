from __future__ import annotations

from adapters import successfactors


PAGE = """
<table><tr class="data-row">
  <td><span class="jobTitle hidden-phone"><a class="jobTitle-link" href="/ey/job/New-York-Software-Engineer/1408050233/">Software Engineer</a></span></td>
  <td><span class="jobLocation">New York, NY, US</span></td>
</tr></table>
"""


def test_successfactors_parses_jobs() -> None:
    jobs = successfactors._parse_jobs(PAGE, "https://careers.ey.com/careers?locale=en_US")

    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "1408050233"
    assert jobs[0]["title"] == "Software Engineer"
    assert jobs[0]["location_raw"] == "New York, NY, US"


def test_successfactors_deduplicates_terms() -> None:
    original_get = successfactors.http_get_text
    original_terms = successfactors.TECH_SEARCH_TERMS
    successfactors.http_get_text = lambda *_args, **_kwargs: PAGE
    successfactors.TECH_SEARCH_TERMS = ["software", "data engineer"]
    try:
        jobs = successfactors.fetch_company_jobs(
            {
                "career_url": "https://careers.ey.com/careers?locale=en_US",
                "source_base_url": "https://careers.ey.com/ey/search/",
            }
        )
    finally:
        successfactors.http_get_text = original_get
        successfactors.TECH_SEARCH_TERMS = original_terms

    assert len(jobs) == 1


if __name__ == "__main__":
    test_successfactors_parses_jobs()
    test_successfactors_deduplicates_terms()
    print("SuccessFactors adapter tests passed")
