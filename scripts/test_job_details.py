from unittest.mock import patch

from job_details import description_from_page, enrich_description, fetch_description


def test_extracts_only_jobposting_jsonld_and_preserves_qualifications() -> None:
    text = "<h3>Qualifications</h3><p>Master's or PhD accepted. We do not provide visa sponsorship.</p>" * 3
    import json
    page = '<script type="application/ld+json">' + json.dumps({"@graph": [{"@type": "Organization", "description": "unrelated"}, {"@type": "JobPosting", "description": text}]}) + '</script>'
    assert description_from_page(page, "https://careers.example.com/job/1") == text
    assert description_from_page("<main>Sign in to view your application</main>", "https://careers.example.com") == ""


def test_fetches_workday_and_oracle_detail_apis() -> None:
    with patch("job_details.http_get_json", return_value={"jobPostingInfo": {"jobDescription": "Full description"}}) as request:
        assert fetch_description({"apply_url": "https://example.wd5.myworkdayjobs.com/en-US/External/job/Seattle/Engineer_R1"}, {}) == "Full description"
        assert request.call_args.args[0] == "https://example.wd5.myworkdayjobs.com/wday/cxs/example/External/job/Seattle/Engineer_R1"
    with patch("job_details.http_get_json", return_value={"items": [{"Id": "123", "ExternalDescriptionStr": "Responsibilities", "ExternalQualificationsStr": "Master's or PhD"}]}) as request:
        text = fetch_description({"external_id": "123", "source_platform": "oracle_hcm", "apply_url": "https://careers.oracle.com/jobs/123"}, {"source_key": "CX"})
        assert "Master's or PhD" in text
        assert request.call_args.kwargs["params"]["finder"] == "ById;Id=123,siteNumber=CX"


def test_cache_reuses_full_jd_and_preserves_it_on_failure() -> None:
    raw = {"external_id": "1", "apply_url": "https://jobs.example.com/1", "description": "Listing summary", "source_platform": "workday"}
    cache = {"text": "Full JD " * 40, "status": "full", "fetched_at": "2026-11-01T00:00:00Z", "source_url": raw["apply_url"]}
    company = {"slug": "example"}
    with patch("job_details.fetch_description") as fetch:
        enriched, detail = enrich_description(raw, company, cache, "2026-11-05T00:00:00Z")
        fetch.assert_not_called()
        assert enriched["description"] == cache["text"]
    with patch("job_details.fetch_description", side_effect=RuntimeError("Unavailable")):
        enriched, detail = enrich_description(raw, company, cache, "2026-11-10T00:00:00Z")
        assert enriched["description"] == cache["text"]
        assert detail["fetch_error"] == "RuntimeError"
        assert detail["fetched_at"] == cache["fetched_at"]


def test_missing_detail_is_not_marked_full_and_failure_is_throttled() -> None:
    raw = {"external_id": "1", "apply_url": "https://jobs.example.com/1", "description": "", "source_platform": "workday"}
    with patch("job_details.fetch_description", return_value=""):
        enriched, detail = enrich_description(raw, {"slug": "example"}, {}, "2026-11-05T00:00:00Z")
        assert enriched["description_status"] == "missing"
    with patch("job_details.fetch_description") as fetch:
        enrich_description(raw, {"slug": "example"}, detail, "2026-11-05T06:00:00Z")
        fetch.assert_not_called()


def test_apple_preserves_minimum_and_preferred_sections() -> None:
    with patch("job_details.http_get_json", return_value={"res": {"description": "Build products.", "minimumQualifications": "Bachelor's degree.", "preferredQualifications": "MS/PhD preferred."}}) as request:
        text = fetch_description({"apply_url": "https://jobs.apple.com/en-us/details/123", "external_id": "123", "source_platform": "custom_apple"}, {})
    assert "<h3>Minimum Qualifications</h3>" in text
    assert "<h3>Preferred Qualifications</h3>" in text
    assert request.call_args.args[0] == "https://jobs.apple.com/api/v1/jobDetails/123"


if __name__ == "__main__":
    for name, value in list(globals().items()):
        if name.startswith("test_"): value()
    print("job detail tests passed")
