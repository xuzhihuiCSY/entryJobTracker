"""Two Sigma's public Avature OpenRoles board, including campus metadata."""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from utils import http_get_text

SEARCH_URL = "https://careers.twosigma.com/careers/OpenRoles"


def _parse_jobs(soup: BeautifulSoup) -> list[dict[str, Any]]:
    jobs = []
    for article in soup.select("article.article--result"):
        link = article.select_one("h3 a[href]")
        location = article.select_one(".article__header__content__text > span")
        if link is None or location is None:
            raise ValueError("Two Sigma listing format changed")
        url = urljoin(SEARCH_URL, str(link["href"]))
        external_id = url.rstrip("/").rsplit("/", 1)[-1]
        if urlparse(url).hostname != "careers.twosigma.com" or "/JobDetail/" not in url or not external_id.isdigit():
            raise ValueError("Two Sigma returned an invalid posting URL")
        title = link.get_text(" ", strip=True)
        metadata = article.select(".article__header__content__sub-text > span")
        experience = metadata[-1].get_text(" ", strip=True).casefold() if metadata else ""
        hint = ""
        if experience == "internship":
            hint = "Intern"
        elif experience == "early careers":
            hint = "New Grad" if re.search(r"\bcampus[ -]+full[ -]?time\b", title, re.I) else "Early Career"
        jobs.append({"external_id": external_id, "title": title,
                     "location_raw": location.get_text(" ", strip=True), "level_hint": hint,
                     "description": "", "apply_url": url, "source_url": url, "source_platform": "two_sigma"})
    return jobs


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    url = SEARCH_URL
    seen_urls: set[str] = set()
    seen_jobs: set[str] = set()
    results = []
    for _ in range(100):
        if url in seen_urls:
            raise ValueError("Two Sigma pagination repeated a page")
        seen_urls.add(url)
        soup = BeautifulSoup(http_get_text(url), "html.parser")
        jobs = _parse_jobs(soup)
        if not jobs:
            if not results and re.search(r"\b(?:no (?:open )?(?:jobs|roles|positions|results) (?:found|available)|0 (?:jobs|roles|results))\b", soup.get_text(" ", strip=True), re.I):
                return []
            raise ValueError("Two Sigma search did not return a valid job list")
        new_jobs = [job for job in jobs if job["external_id"] not in seen_jobs]
        if not new_jobs:
            raise ValueError("Two Sigma pagination repeated its postings")
        for job in new_jobs:
            seen_jobs.add(job["external_id"])
            results.append(job)
        next_link = next((a for a in soup.select("a[href]") if re.match(r"^Next\b", a.get_text(" ", strip=True), re.I)), None)
        if next_link is None:
            return results
        url = urljoin(url, str(next_link["href"]))
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "careers.twosigma.com" or parsed.path.rstrip("/") != "/careers/OpenRoles":
            raise ValueError("Two Sigma returned an invalid next-page URL")
    raise ValueError("Two Sigma search exceeded the page limit; refusing a partial snapshot")
