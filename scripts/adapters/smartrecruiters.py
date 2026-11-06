from __future__ import annotations

from typing import Any
import re

from utils import http_get_json

API_BASE_URL = "https://api.smartrecruiters.com/v1/companies"
PAGE_SIZE = 100


def _location(posting: dict[str, Any]) -> str:
    location = posting.get("location")
    if not isinstance(location, dict):
        return ""
    return str(location.get("fullLocation") or "").strip()


def _level_hint(posting: dict[str, Any]) -> str:
    employment = posting.get("typeOfEmployment") or {}
    experience = posting.get("experienceLevel") or {}
    text = " ".join(str(field.get(key) or "") for field in (employment, experience) for key in ("id", "label", "name"))
    text += " " + " ".join(
        f"{field.get('valueId', '')} {field.get('valueLabel', '')}"
        for field in posting.get("customField") or []
        if field.get("fieldLabel") in {"Recruiting Team", "Job Posting Type", "Career Level", "Employee Type"}
    )
    if re.search(r"\bintern(?:ship)?\b|\bco-?op\b", text, re.I):
        return "Intern"
    if re.search(r"\b(?:new[ _-]grad(?:uate)?|graduate)\b", text, re.I):
        return "New Grad"
    if re.search(r"\bentry[ _-]level\b", text, re.I):
        return "Entry"
    if re.search(r"\b(?:early[ _-](?:in[ _-])?career|global emerging talent)\b", text, re.I):
        return "Early Career"
    return ""


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    company_identifier = str(company_config.get("source_key") or "").strip()
    if not company_identifier:
        return []

    url = f"{API_BASE_URL}/{company_identifier}/postings"
    results: list[dict[str, Any]] = []
    offset = 0
    while True:
        data = http_get_json(url, params={"limit": PAGE_SIZE, "offset": offset})
        if not isinstance(data, dict) or not isinstance(data.get("content"), list) or "totalFound" not in data:
            raise ValueError("SmartRecruiters returned an invalid posting list")
        postings = data["content"]
        total = int(data["totalFound"])
        if not postings:
            if offset < total:
                raise ValueError("SmartRecruiters returned an incomplete posting list")
            break

        for posting in postings:
            if not isinstance(posting, dict):
                continue
            external_id = str(posting.get("id") or "").strip()
            if not external_id:
                continue
            apply_url = f"https://jobs.smartrecruiters.com/{company_identifier}/{external_id}"
            results.append(
                {
                    "external_id": external_id,
                    "title": posting.get("name") or "",
                    "level_hint": _level_hint(posting),
                    "location_raw": _location(posting),
                    "description": "",
                    "apply_url": apply_url,
                    "source_url": apply_url,
                    "source_platform": "smartrecruiters",
                }
            )

        offset += len(postings)
        if offset >= total:
            break

    return results
