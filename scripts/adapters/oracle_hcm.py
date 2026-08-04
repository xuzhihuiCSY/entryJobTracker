from __future__ import annotations

from typing import Any

from utils import http_get_json

TECH_SEARCH_TERMS = [
    "software",
    "machine learning",
    "data scientist",
    "data engineer",
    "cloud",
    "devops",
    "site reliability",
    "ai",
    "backend",
    "frontend",
    "intern",
]

BASE_URL = "https://eeho.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
DEFAULT_APPLY_URL = "https://careers.oracle.com/jobs/#en/sites/jobsearch/job/{job_id}"
EXPAND = (
    "requisitionList.workLocation,"
    "requisitionList.otherWorkLocations,"
    "requisitionList.secondaryLocations,"
    "flexFieldsFacet.values,"
    "requisitionList.requisitionFlexFields"
)
US_LOCATION_ID = "300000000149325"


def _source_settings(company_config: dict[str, Any]) -> tuple[str, str, str, str]:
    base_url = str(company_config.get("source_base_url") or BASE_URL).strip()
    site_number = str(company_config.get("source_key") or "").strip()
    configured_location_id = company_config.get("source_location_id")
    if configured_location_id is None:
        location_id = US_LOCATION_ID if base_url == BASE_URL else ""
    else:
        location_id = str(configured_location_id).strip()
    apply_url_template = str(company_config.get("source_apply_url") or DEFAULT_APPLY_URL).strip()
    return base_url, site_number, location_id, apply_url_template


def _job_locations(job: dict[str, Any]) -> str:
    locations: list[str] = []
    primary = str(job.get("PrimaryLocation") or "").strip()
    if primary:
        locations.append(primary)
    for key in ("secondaryLocations", "otherWorkLocations", "workLocation"):
        values = job.get(key)
        if not isinstance(values, list):
            continue
        for value in values:
            if not isinstance(value, dict):
                continue
            name = str(value.get("Name") or value.get("AddressLine1") or "").strip()
            if name and name not in locations:
                locations.append(name)
    return "; ".join(locations)


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    base_url, site_number, location_id, apply_url_template = _source_settings(company_config)
    if not site_number:
        return []

    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for term in TECH_SEARCH_TERMS:
        offset = 0
        while offset < 500:
            finder_parts = [f"siteNumber={site_number}", f"keyword={term}"]
            if location_id:
                finder_parts.append(f"locationId={location_id}")
            finder_parts.extend(
                ["facetsList=LOCATIONS", "sortBy=POSTING_DATES_DESC", "limit=100", f"offset={offset}"]
            )
            finder = f"findReqs;{','.join(finder_parts)}"
            data = http_get_json(
                base_url,
                params={
                    "onlyData": "true",
                    "expand": EXPAND,
                    "finder": finder,
                },
            )
            items = data.get("items", []) if isinstance(data, dict) else []
            search = items[0] if items else {}
            jobs = search.get("requisitionList", []) if isinstance(search, dict) else []
            if not jobs:
                break

            for job in jobs:
                external_id = str(job.get("Id") or "").strip()
                if not external_id or external_id in seen:
                    continue
                seen.add(external_id)
                apply_url = apply_url_template.format(job_id=external_id)
                results.append(
                    {
                        "external_id": external_id,
                        "title": job.get("Title") or "",
                        "location_raw": _job_locations(job),
                        "description": job.get("ShortDescriptionStr") or "",
                        "apply_url": apply_url,
                        "source_url": apply_url,
                        "source_platform": "oracle_hcm",
                    }
                )

            offset += 100
            total = int(search.get("TotalJobsCount") or 0)
            if offset >= total:
                break

    return results
