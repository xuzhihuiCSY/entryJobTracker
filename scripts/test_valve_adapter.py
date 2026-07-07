from __future__ import annotations

from adapters.valve import _parse_detail, _parse_listing


def test_parse_listing_dedupes_by_job_id() -> None:
    html = """
    <div class="job_openings">
      <div class="job_opening"><a href="https://www.valvesoftware.com/en/jobs?job_id=14"><h5>Steam Software Engineer</h5></a></div>
      <div class="job_opening"><a href="https://www.valvesoftware.com/en/jobs?job_id=14"><h5>Steam Software Engineer</h5></a></div>
      <div class="job_opening"><a href="/en/jobs?job_id=16"><h5>Steam Database Administrator</h5></a></div>
    </div>
    """

    jobs = _parse_listing(html)

    assert jobs == [
        {
            "external_id": "14",
            "title": "Steam Software Engineer",
            "apply_url": "https://www.valvesoftware.com/en/jobs?job_id=14",
        },
        {
            "external_id": "16",
            "title": "Steam Database Administrator",
            "apply_url": "https://www.valvesoftware.com/en/jobs?job_id=16",
        },
    ]


def test_parse_detail_reads_title_location_and_description() -> None:
    html = """
    <header class="job_opening_title row">
      <h1>Steam Software Engineer</h1>
      <p class="job_opening_location">We work together in person, in Bellevue, WA, USA</p>
    </header>
    <section class="job_description row">
      <p>Build and maintain Steam services.</p>
    </section>
    """
    listing_job = {
        "external_id": "14",
        "title": "Fallback",
        "apply_url": "https://www.valvesoftware.com/en/jobs?job_id=14",
    }

    job = _parse_detail(html, listing_job)

    assert job["external_id"] == "14"
    assert job["title"] == "Steam Software Engineer"
    assert job["location_raw"] == "We work together in person, in Bellevue, WA, USA"
    assert "Build and maintain Steam services." in job["description"]
    assert job["source_platform"] == "valve"


if __name__ == "__main__":
    test_parse_listing_dedupes_by_job_id()
    test_parse_detail_reads_title_location_and_description()
    print("valve adapter tests passed")
