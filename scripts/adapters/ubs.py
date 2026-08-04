from __future__ import annotations

import html
import json
from typing import Any
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from utils import REQUEST_TIMEOUT_SECONDS, USER_AGENT

TECH_SEARCH_TERMS = [
    "software engineer",
    "machine learning",
    "data scientist",
    "data engineer",
    "cloud engineer",
    "cyber security",
    "technology intern",
    "IT intern",
]


def _parse_preload(page_html: str) -> tuple[dict[str, Any], str]:
    soup = BeautifulSoup(page_html, "html.parser")
    preload = soup.select_one("#preLoadJSON")
    token = soup.select_one('input[name="__RequestVerificationToken"]')
    if preload is None or token is None:
        return {}, ""
    payload = json.loads(html.unescape(str(preload.get("value") or "{}")))
    smart_search = json.loads(payload.get("SmartSearchJSONValue") or "{}")
    return smart_search, str(token.get("value") or "")


def _question_values(posting: dict[str, Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    for question in posting.get("Questions") or []:
        if not isinstance(question, dict):
            continue
        name = str(question.get("QuestionName") or "").strip().lower()
        if name:
            values[name] = str(question.get("Value") or "").strip()
    return values


def _map_postings(
    postings: list[Any],
    base_url: str,
    partner_id: int,
    default_site_id: int,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for posting in postings:
        if not isinstance(posting, dict):
            continue
        values = _question_values(posting)
        external_id = values.get("reqid", "")
        if not external_id:
            continue
        site_id = int(values.get("siteid") or default_site_id)
        query = urlencode(
            {
                "PageType": "JobDetails",
                "partnerid": partner_id,
                "siteid": site_id,
                "jobid": external_id,
            }
        )
        apply_url = f"{base_url}/TGnewUI/Search/home/HomeWithPreLoad?{query}"
        results.append(
            {
                "external_id": external_id,
                "title": values.get("jobtitle", ""),
                "location_raw": values.get("formtext23", ""),
                "description": values.get("jobdescription", ""),
                "apply_url": apply_url,
                "source_url": apply_url,
                "source_platform": "ubs",
            }
        )
    return results


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    base_url = str(company_config.get("source_base_url") or "").strip().rstrip("/")
    partner_id = int(company_config.get("source_partner_id") or 0)
    site_ids = company_config.get("source_site_ids") or []
    link_ids = company_config.get("source_link_ids") or []
    if not base_url or not partner_id or not site_ids or len(site_ids) != len(link_ids):
        return []

    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for site_id_value, link_id_value in zip(site_ids, link_ids, strict=True):
        site_id = int(site_id_value)
        link_id = int(link_id_value)
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json,text/plain,*/*"})
        search_page = (
            f"{base_url}/TGnewUI/Search/home/HomeWithPreLoad?"
            + urlencode(
                {
                    "LinkID": link_id,
                    "PageType": "searchResults",
                    "SearchType": "linkquery",
                    "partnerid": partner_id,
                    "siteid": site_id,
                }
            )
        )
        response = session.get(search_page, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        smart_search, request_token = _parse_preload(response.text)
        if not smart_search or not request_token:
            continue
        headers = {"RFT": request_token, "Referer": search_page, "Origin": base_url}
        for term in TECH_SEARCH_TERMS:
            payload = {
                "PartnerId": partner_id,
                "SiteId": site_id,
                "Keyword": term,
                "Location": "",
                "KeywordCustomSolrFields": smart_search.get("KeywordCustomSolrFields"),
                "LocationCustomSolrFields": smart_search.get("LocationCustomSolrFields"),
                "TurnOffHttps": False,
                "Latitude": 0,
                "Longitude": 0,
                "PowerSearchOptions": {"PowerSearchOption": []},
                "FacetFilterFields": {"Facet": []},
                "EncryptedSessionValue": smart_search.get("EncryptedSessionValue"),
            }
            response = session.post(
                f"{base_url}/TgNewUI/Search/Ajax/MatchedJobs",
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
            container = (data.get("Jobs") or {}) if isinstance(data, dict) else {}
            postings = (container.get("Job") or []) if isinstance(container, dict) else []
            for job in _map_postings(postings, base_url, partner_id, site_id):
                external_id = job["external_id"]
                if external_id in seen:
                    continue
                seen.add(external_id)
                results.append(job)
    return results
