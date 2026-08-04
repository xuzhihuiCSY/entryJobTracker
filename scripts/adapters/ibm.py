from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

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


def _attributes(posting: dict[str, Any]) -> dict[str, Any]:
    attributes: dict[str, Any] = {}
    for item in posting.get("docattributes") or []:
        if isinstance(item, dict):
            attributes.update(item)
    return attributes


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    career_url = str(company_config.get("career_url") or "").strip()
    source_url = str(company_config.get("source_base_url") or "").strip()
    if not career_url or not source_url:
        return []

    headers = {"Origin": "https://www.ibm.com", "Referer": career_url}
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for term in TECH_SEARCH_TERMS:
        offset = 0
        while offset < 500:
            data = http_get_json(
                source_url,
                params={
                    "scope": "careers2",
                    "rmdt": "ALL",
                    "appid": "careers",
                    "sortby": "-dcdate",
                    "query": term,
                    "fr": offset,
                    "nr": 100,
                    "sm": "false",
                    "dict": "spelling",
                    "ql": "en",
                    "rc": "us",
                    "filter": "(language:en OR language:zz)",
                    "refinement": "ibmcom",
                    "variant": "pvboost:1",
                },
                headers=headers,
            )
            resultset = data.get("resultset", {}) if isinstance(data, dict) else {}
            search = resultset.get("searchresults", {}) if isinstance(resultset, dict) else {}
            postings = search.get("searchresultlist", []) if isinstance(search, dict) else []
            if not postings:
                break
            for posting in postings:
                if not isinstance(posting, dict):
                    continue
                attrs = _attributes(posting)
                apply_url = str(posting.get("url") or attrs.get("url") or "").strip()
                external_id = str(attrs.get("field_text_01") or "").strip()
                if not external_id and apply_url:
                    external_id = parse_qs(urlparse(apply_url).query).get("jobId", [""])[0]
                if not external_id or external_id in seen:
                    continue
                seen.add(external_id)
                location = str(attrs.get("field_keyword_19") or "").strip()
                country = str(attrs.get("field_keyword_05") or "").strip()
                if country and country.lower() not in location.lower() and not location.lower().endswith(", us"):
                    location = ", ".join(value for value in (location, country) if value)
                results.append(
                    {
                        "external_id": external_id,
                        "title": posting.get("title") or attrs.get("title") or "",
                        "location_raw": location,
                        "description": attrs.get("raw_body") or posting.get("description") or "",
                        "apply_url": apply_url,
                        "source_url": apply_url,
                        "source_platform": "ibm",
                    }
                )
            returned = len(postings)
            offset += returned
            total = int(search.get("totalresults") or 0)
            if offset >= total or returned < 100:
                break
    return results
