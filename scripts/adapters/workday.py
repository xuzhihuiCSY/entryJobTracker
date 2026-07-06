from __future__ import annotations

from typing import Any

from utils import http_post_json

TECH_SEARCH_TERMS = [
    "software",
    "machine learning",
    "data scientist",
    "data engineer",
    "frontend",
    "backend",
    "full stack",
    "site reliability",
    "cloud engineer",
    "devops",
    "ai engineer",
    "intern",
    "new grad",
]


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    source_key = str(company_config.get("source_key") or "").strip()
    if "/" not in source_key:
        return []

    tenant, site = source_key.split("/", 1)
    url = f"https://{tenant}.wd5.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    seen: set[str] = set()
    results: list[dict[str, Any]] = []

    for term in TECH_SEARCH_TERMS:
        offset = 0
        while offset < 120:
            payload = {
                "appliedFacets": {},
                "limit": 20,
                "offset": offset,
                "searchText": term,
            }
            data = http_post_json(
                url,
                payload,
                headers={
                    "Referer": f"https://{tenant}.wd5.myworkdayjobs.com/{site}",
                    "User-Agent": "Mozilla/5.0 EntryJobTracker source verification",
                },
            )
            postings = data.get("jobPostings", []) if isinstance(data, dict) else []
            if not postings:
                break

            for posting in postings:
                external_path = str(posting.get("externalPath") or "").strip()
                req_id = ""
                bullet_fields = posting.get("bulletFields")
                if isinstance(bullet_fields, list) and bullet_fields:
                    req_id = str(bullet_fields[0] or "").strip()
                job_key = req_id or external_path
                if not job_key or job_key in seen:
                    continue
                seen.add(job_key)
                apply_url = f"https://{tenant}.wd5.myworkdayjobs.com/{site}{external_path}"
                results.append(
                    {
                        "external_id": job_key,
                        "title": posting.get("title") or "",
                        "location_raw": posting.get("locationsText") or "",
                        "description": "",
                        "apply_url": apply_url,
                        "source_url": apply_url,
                        "source_platform": "workday",
                    }
                )

            total = int(data.get("total") or 0)
            offset += 20
            if offset >= total:
                break

    return results
