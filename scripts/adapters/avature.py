from __future__ import annotations

from typing import Any
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from utils import http_get_text

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


def _parse_jobs(page: str, career_url: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(page, "html.parser")
    jobs: list[dict[str, Any]] = []
    for article in soup.select("article.article--result"):
        title_link = article.select_one("h3 a[href]")
        if title_link is None:
            continue
        apply_url = urljoin(career_url, str(title_link.get("href") or ""))
        external_id = apply_url.rstrip("/").rsplit("/", 1)[-1]
        if not external_id.isdigit():
            continue
        subtitle = article.select_one(".article__header__text__subtitle")
        subtitle_values = (
            [value.get_text(" ", strip=True) for value in subtitle.select("span")]
            if subtitle is not None
            else []
        )
        description = article.select_one(".article__content")
        jobs.append(
            {
                "external_id": external_id,
                "title": title_link.get_text(" ", strip=True),
                "location_raw": subtitle_values[0] if subtitle_values else "",
                "description": description.get_text(" ", strip=True) if description else "",
                "apply_url": apply_url,
                "source_url": apply_url,
                "source_platform": "avature",
            }
        )
    return jobs


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    career_url = str(company_config.get("career_url") or "").strip()
    base_url = str(company_config.get("source_base_url") or "").strip()
    if not career_url or not base_url:
        return []

    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for term in TECH_SEARCH_TERMS:
        offset = 0
        while offset < 120:
            page = http_get_text(
                f"{base_url.rstrip('/')}/{quote(term, safe='')}",
                params={"jobOffset": offset},
                headers={
                    "Referer": career_url,
                    "User-Agent": "Mozilla/5.0",
                },
            )
            jobs = _parse_jobs(page, career_url)
            if not jobs:
                break
            for job in jobs:
                external_id = job["external_id"]
                if external_id in seen:
                    continue
                seen.add(external_id)
                results.append(job)
            offset += len(jobs)
            if len(jobs) < 20:
                break
    return results
