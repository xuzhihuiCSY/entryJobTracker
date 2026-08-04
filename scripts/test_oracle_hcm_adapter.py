from __future__ import annotations

from adapters import oracle_hcm


def test_default_oracle_source_settings_are_preserved() -> None:
    base_url, site, location_id, apply_url = oracle_hcm._source_settings({"source_key": "CX_45001"})

    assert base_url == oracle_hcm.BASE_URL
    assert site == "CX_45001"
    assert location_id == oracle_hcm.US_LOCATION_ID
    assert apply_url == oracle_hcm.DEFAULT_APPLY_URL


def test_custom_oracle_hcm_source_uses_configured_tenant() -> None:
    calls: list[tuple[str, dict]] = []

    def fake_get_json(url: str, params: dict) -> dict:
        calls.append((url, params))
        return {
            "items": [
                {
                    "TotalJobsCount": 1,
                    "requisitionList": [
                        {
                            "Id": "123",
                            "Title": "Software Engineer",
                            "PrimaryLocation": "Dearborn, MI, United States",
                            "ShortDescriptionStr": "Build vehicle software.",
                        }
                    ],
                }
            ]
        }

    original_get_json = oracle_hcm.http_get_json
    oracle_hcm.http_get_json = fake_get_json
    try:
        jobs = oracle_hcm.fetch_company_jobs(
            {
                "source_key": "CX_1",
                "source_base_url": "https://example.oraclecloud.com/hcmRestApi/jobs",
                "source_location_id": None,
                "source_apply_url": "https://example.oraclecloud.com/sites/CX_1/job/{job_id}",
            }
        )
    finally:
        oracle_hcm.http_get_json = original_get_json

    assert jobs == [
        {
            "external_id": "123",
            "title": "Software Engineer",
            "location_raw": "Dearborn, MI, United States",
            "description": "Build vehicle software.",
            "apply_url": "https://example.oraclecloud.com/sites/CX_1/job/123",
            "source_url": "https://example.oraclecloud.com/sites/CX_1/job/123",
            "source_platform": "oracle_hcm",
        }
    ]
    assert calls
    assert all(url == "https://example.oraclecloud.com/hcmRestApi/jobs" for url, _ in calls)
    assert all("locationId=" not in params["finder"] for _, params in calls)


if __name__ == "__main__":
    test_default_oracle_source_settings_are_preserved()
    test_custom_oracle_hcm_source_uses_configured_tenant()
    print("oracle HCM adapter tests passed")
