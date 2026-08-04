from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from utils import http_get_json

TECH_SEARCH_TERMS = [
    "software engineer",
    "machine learning",
    "data scientist",
    "data engineer",
    "cloud engineer",
    "security engineer",
    "technology intern",
    "IT intern",
]


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    career_url = str(company_config.get("career_url") or "").strip()
    source_url = str(company_config.get("source_base_url") or "").strip()
    if not career_url or not source_url:
        return []

    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for term in TECH_SEARCH_TERMS:
        offset = 0
        while offset < 500:
            data = http_get_json(
                source_url,
                params={
                    "term": term,
                    "search": "jobsByKeyword",
                    "start": offset,
                    "rows": 100,
                },
            )
            postings = data.get("jobsList", []) if isinstance(data, dict) else []
            if not postings:
                break
            for posting in postings:
                external_id = str(posting.get("jobRequisitionId") or "").strip()
                if not external_id or external_id in seen:
                    continue
                seen.add(external_id)
                job_path = str(posting.get("jcrURL") or "").strip()
                apply_url = urljoin(career_url, job_path)
                primary = str(posting.get("primaryLocation") or "").strip()
                additional = str(posting.get("additionalLocations") or "").strip()
                locations = [value for value in (primary, additional) if value]
                results.append(
                    {
                        "external_id": external_id,
                        "title": posting.get("postingTitle") or "",
                        "location_raw": "; ".join(locations),
                        "description": "",
                        "apply_url": apply_url,
                        "source_url": apply_url,
                        "source_platform": "bank_of_america",
                    }
                )
            offset += len(postings)
            total = int(data.get("totalMatches") or 0)
            if offset >= total:
                break
    return results
