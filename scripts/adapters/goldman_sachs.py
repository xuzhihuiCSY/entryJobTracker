from __future__ import annotations

from typing import Any

from utils import http_post_json

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

ROLE_SEARCH_QUERY = """
query GetRoles($searchQueryInput: RoleSearchQueryInput!) {
  roleSearch(searchQueryInput: $searchQueryInput) {
    items {
      roleId
      corporateTitle
      jobTitle
      jobFunction
      locations { primary state country city }
      status
      division
      skills
      externalSource { sourceId }
    }
  }
}
"""


def _format_locations(locations: Any) -> str:
    if not isinstance(locations, list):
        return ""
    formatted: list[str] = []
    for location in locations:
        if not isinstance(location, dict):
            continue
        value = ", ".join(
            str(location.get(key) or "").strip()
            for key in ("city", "state", "country")
            if str(location.get(key) or "").strip()
        )
        if value and value not in formatted:
            formatted.append(value)
    return "; ".join(formatted)


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    career_url = str(company_config.get("career_url") or "").strip().rstrip("/")
    source_url = str(company_config.get("source_base_url") or "").strip()
    if not career_url or not source_url:
        return []

    headers = {"Origin": career_url, "Referer": f"{career_url}/results"}
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for term in TECH_SEARCH_TERMS:
        payload = {
            "query": ROLE_SEARCH_QUERY,
            "variables": {
                "searchQueryInput": {
                    "page": {"pageSize": 100, "pageNumber": 0},
                    "sort": {"sortStrategy": "RELEVANCE", "sortOrder": "DESC"},
                    "filters": [],
                    "experiences": ["EARLY_CAREER", "PROFESSIONAL"],
                    "searchTerm": term,
                }
            },
        }
        data = http_post_json(source_url, payload, headers=headers)
        search = data.get("data", {}).get("roleSearch", {}) if isinstance(data, dict) else {}
        postings = search.get("items", []) if isinstance(search, dict) else []
        for posting in postings:
            if not isinstance(posting, dict) or posting.get("status") != "POSTED":
                continue
            external_source = posting.get("externalSource") or {}
            external_id = str(external_source.get("sourceId") or posting.get("roleId") or "").strip()
            if not external_id or external_id in seen:
                continue
            seen.add(external_id)
            apply_url = f"{career_url}/roles/{external_id}"
            description_parts = [
                posting.get("corporateTitle"),
                posting.get("jobFunction"),
                posting.get("division"),
                " ".join(posting.get("skills") or []),
            ]
            results.append(
                {
                    "external_id": external_id,
                    "title": posting.get("jobTitle") or "",
                    "location_raw": _format_locations(posting.get("locations")),
                    "description": " | ".join(str(value) for value in description_parts if value),
                    "apply_url": apply_url,
                    "source_url": apply_url,
                    "source_platform": "goldman_sachs",
                }
            )
    return results
