from __future__ import annotations

import hashlib
import re
from html import unescape
from typing import Any

from bs4 import BeautifulSoup

from education import classify_phd_requirement
from authorization import classify_authorization

from classifier import (
    classify_category,
    classify_level,
    parse_location,
)


def clean_html(value: str | None, preserve_paragraphs: bool = False) -> str:
    if not value:
        return ""
    value = unescape(value)
    if "<" not in value and ">" not in value:
        if preserve_paragraphs:
            return "\n".join(clean_markdown_text(line) for line in value.splitlines() if line.strip())
        return clean_markdown_text(value)
    soup = BeautifulSoup(value, "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    if preserve_paragraphs:
        for element in soup.find_all(["p", "li", "div", "h1", "h2", "h3", "h4", "br"]):
            element.insert_before("\n")
            element.insert_after("\n")
        return "\n".join(clean_markdown_text(line) for line in soup.get_text(" ").splitlines() if line.strip())
    text = soup.get_text(" ", strip=True)
    return clean_markdown_text(unescape(text))


def clean_markdown_text(value: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", value)
    text = re.sub(r"__(.+?)__", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def _slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def normalize_title(title: str | None) -> str:
    return re.sub(r"\s+", " ", title or "").strip()


def normalize_location(location_raw: str | None) -> str:
    return re.sub(r"\s+", " ", location_raw or "").strip()


def make_job_id(company_slug: str, raw_job: dict[str, Any]) -> str:
    external_id = str(raw_job.get("external_id") or "").strip()
    if external_id:
        return _slugify(f"{company_slug}-{external_id}")

    title = normalize_title(raw_job.get("title"))
    location = normalize_location(raw_job.get("location_raw"))
    apply_url = str(raw_job.get("apply_url") or "")
    digest = hashlib.sha1(f"{company_slug}|{title}|{location}|{apply_url}".encode("utf-8")).hexdigest()[:12]
    return _slugify(f"{company_slug}-{title}-{location}-{digest}")


def build_description_snippet(description: str, max_length: int = 260) -> str:
    cleaned = clean_html(description)
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 3].rstrip() + "..."


def normalize_job(raw_job: dict[str, Any], company: dict[str, Any], checked_at: str, first_seen: str) -> dict[str, Any]:
    title = normalize_title(raw_job.get("title"))
    description = clean_html(raw_job.get("description"), preserve_paragraphs=True)
    authorization = classify_authorization(description)
    education = classify_phd_requirement(title, str(raw_job.get("description") or ""))
    location_raw = normalize_location(raw_job.get("location_raw"))
    parsed_location = parse_location(location_raw, description)
    level = classify_level(title, description)
    if raw_job.get("level_hint") in {"Intern", "New Grad", "Early Career", "Entry"} and classify_level(title) == "Unknown":
        level = raw_job["level_hint"]
    job = {
        "id": make_job_id(company["slug"], raw_job),
        "company": company["name"],
        "company_slug": company["slug"],
        "company_group": company.get("company_group", "other"),
        "title": title,
        "category": classify_category(title, description),
        "level": level,
        "source_level_hint": raw_job.get("level_hint") or "",
        "phd_requirement": education.phd_requirement,
        "phd_evidence": education.phd_evidence,
        "location_raw": location_raw,
        "city": parsed_location.city,
        "state": parsed_location.state,
        "country": parsed_location.country,
        "is_us_based": parsed_location.is_us_based,
        "remote_type": parsed_location.remote_type,
        "apply_url": raw_job.get("apply_url") or raw_job.get("source_url") or company.get("career_url", ""),
        "source_url": raw_job.get("source_url") or company.get("career_url", ""),
        "source_platform": raw_job.get("source_platform") or company.get("source_type", "unknown"),
        "first_seen": first_seen,
        "last_checked": checked_at,
        "requires_citizenship": authorization.requires_citizenship,
        "citizenship_evidence": authorization.citizenship_evidence,
        "requires_clearance": authorization.requires_clearance,
        "clearance_evidence": authorization.clearance_evidence,
        "visa_signal": authorization.visa_signal,
        "visa_evidence": authorization.visa_evidence,
        "description_text": description,
        "description_status": raw_job.get("description_status") or ("full" if description else "missing"),
        "description_fetched_at": raw_job.get("description_fetched_at") or (checked_at if description else ""),
        "description_path": f"/data/descriptions/{company['slug']}.json" if description else "",
        "description_snippet": build_description_snippet(description),
    }
    locations = raw_job.get("locations")
    if isinstance(locations, list):
        cleaned_locations = [normalize_location(str(location)) for location in locations if normalize_location(str(location))]
        if cleaned_locations:
            job["locations"] = cleaned_locations
            job["location_count"] = int(raw_job.get("location_count") or len(cleaned_locations))
            if len(cleaned_locations) > 1 and job["remote_type"] == "onsite":
                job["remote_type"] = "unknown"
    return job


def is_relevant_technical_job(job: dict[str, Any]) -> bool:
    return job["is_us_based"] and job["category"] != "Other"


def dedupe_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for job in jobs:
        job_id = job["id"]
        if job_id in seen:
            continue
        seen.add(job_id)
        deduped.append(job)
    return deduped
