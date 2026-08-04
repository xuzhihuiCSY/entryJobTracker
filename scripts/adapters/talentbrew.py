from __future__ import annotations

from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from utils import http_post_json

MAX_PAGES_PER_TERM = 10
RECORDS_PER_PAGE = 15
TECH_SEARCH_TERMS = [
    "software engineer",
    "machine learning",
    "data scientist",
    "data engineer",
    "cloud engineer",
    "devops",
    "security engineer",
    "technology intern",
    "IT intern",
]


def _search_payload(company_config: dict[str, Any], term: str, page: int) -> dict[str, Any]:
    return {
        "ActiveFacetID": 0,
        "CurrentPage": page,
        "RecordsPerPage": RECORDS_PER_PAGE,
        "TotalPages": 0,
        "TotalResults": 0,
        "TotalContentResults": 0,
        "Distance": 50,
        "RadiusUnitType": None,
        "Keywords": term,
        "Location": "",
        "Latitude": None,
        "Longitude": None,
        "ShowRadius": False,
        "IsPagination": "True",
        "CustomFacetName": "",
        "FacetTerm": "",
        "FacetType": 0,
        "FacetFilters": [],
        "StaticFacets": None,
        "SearchResultsModuleName": "Search Results",
        "SearchFiltersModuleName": None,
        "SortCriteria": 5,
        "SortDirection": 1,
        "SearchType": 1,
        "CategoryFacetTerm": "",
        "CategoryFacetType": 0,
        "LocationFacetTerm": "",
        "LocationFacetType": 0,
        "KeywordType": "",
        "LocationType": "",
        "LocationPath": "",
        "OrganizationIds": str(company_config.get("source_key") or ""),
        "RefinedKeywords": [],
        "PostalCode": "",
        "ResultsType": 0,
        "fc": None,
        "fl": None,
        "fcf": None,
        "afc": None,
        "afl": None,
        "afcf": None,
    }


def _fallback_location(href: str, source_country: str) -> str:
    path_parts = urlparse(href).path.strip("/").split("/")
    if len(path_parts) < 2 or path_parts[0] != "job":
        return source_country
    location = path_parts[1].replace("-", " ").title()
    return f"{location}, {source_country}" if location else source_country


def _parse_results(
    results_html: str,
    career_url: str,
    source_country: str = "",
) -> tuple[list[dict[str, Any]], int]:
    soup = BeautifulSoup(results_html, "html.parser")
    container = soup.select_one("#search-results")
    total_pages = int(container.get("data-total-pages") or 1) if container else 1
    jobs: list[dict[str, Any]] = []
    items = soup.select(".sr-job-item") or soup.select("#search-results-list li")
    for item in items:
        link = item.select_one(".sr-job-item__link") or item.select_one("a[data-job-id]")
        if link is None:
            continue
        external_id = str(link.get("data-job-id") or "").strip()
        href = str(link.get("href") or "").strip()
        if not external_id or not href:
            continue
        location = item.select_one(".sr-job-location") or item.select_one(".job-location")
        title_element = link.select_one("h2, h3")
        apply_url = urljoin(career_url, href)
        location_text = location.get_text(" ", strip=True) if location else ""
        if source_country and (not location_text or location_text.lower() == "multiple locations"):
            location_text = _fallback_location(href, source_country)
        jobs.append(
            {
                "external_id": external_id,
                "title": title_element.get_text(" ", strip=True) if title_element else link.get_text(" ", strip=True),
                "location_raw": location_text,
                "description": "",
                "apply_url": apply_url,
                "source_url": apply_url,
                "source_platform": "talentbrew",
            }
        )
    return jobs, total_pages


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    career_url = str(company_config.get("career_url") or "").strip()
    organization_id = str(company_config.get("source_key") or "").strip()
    if not career_url or not organization_id:
        return []

    endpoint = urljoin(career_url.rstrip("/") + "/", "/search-jobs/resultspost")
    source_country = str(company_config.get("source_country") or "").strip()
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for term in TECH_SEARCH_TERMS:
        page = 1
        while page <= MAX_PAGES_PER_TERM:
            payload = http_post_json(endpoint, _search_payload(company_config, term, page))
            results_html = str(payload.get("results") or "") if isinstance(payload, dict) else ""
            jobs, total_pages = _parse_results(results_html, career_url, source_country)
            if not jobs:
                break
            for job in jobs:
                external_id = job["external_id"]
                if external_id in seen:
                    continue
                seen.add(external_id)
                results.append(job)
            if page >= total_pages:
                break
            page += 1

    return results
