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
EXPAND = (
    "requisitionList.workLocation,"
    "requisitionList.otherWorkLocations,"
    "requisitionList.secondaryLocations,"
    "flexFieldsFacet.values,"
    "requisitionList.requisitionFlexFields"
)
US_LOCATION_ID = "300000000149325"


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
    site_number = str(company_config.get("source_key") or "").strip()
    if not site_number:
        return []

    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for term in TECH_SEARCH_TERMS:
        offset = 0
        while offset < 500:
            finder = (
                f"findReqs;siteNumber={site_number},keyword={term},"
                f"locationId={US_LOCATION_ID},facetsList=LOCATIONS,"
                f"sortBy=POSTING_DATES_DESC,limit=100,offset={offset}"
            )
            data = http_get_json(
                BASE_URL,
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
                apply_url = f"https://careers.oracle.com/jobs/#en/sites/jobsearch/job/{external_id}"
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
