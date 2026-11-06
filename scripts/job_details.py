"""Fetch official job descriptions with bounded, reusable per-posting caching."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from normalizer import clean_html
from utils import http_get_json, http_get_text

LOGGER = logging.getLogger(__name__)
CACHE_HOURS = 24 * 7
PARSER_VERSION = 1
SUMMARY_SOURCES = {
    "workday", "custom_nvidia", "oracle_hcm", "talentbrew", "successfactors",
    "avature", "eightfold", "kpmg", "bank_of_america", "smartrecruiters", "phenom",
    "rippling_algolia", "zoom", "custom_microsoft", "custom_google", "custom_apple", "qualcomm", "goldman_sachs",
}


def _job_postings(value: Any):
    if isinstance(value, dict):
        types = value.get("@type") or []
        if types == "JobPosting" or (isinstance(types, list) and "JobPosting" in types):
            yield value
        for child in value.values():
            yield from _job_postings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _job_postings(child)


def description_from_page(page: str, url: str) -> str:
    soup = BeautifulSoup(page, "html.parser")
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            payload = json.loads(script.string or script.get_text())
        except (ValueError, TypeError):
            continue
        for posting in _job_postings(payload):
            description = posting.get("description")
            if isinstance(description, str) and len(clean_html(description)) >= 100:
                return description
    # Rippling renders its public posting as Next.js page data.
    script = soup.select_one("script#__NEXT_DATA__")
    if script:
        try:
            data = json.loads(script.string or script.get_text())
            description = data["props"]["pageProps"]["apiData"]["jobPost"]["description"]
            if isinstance(description, dict):
                description = "\n".join(str(description.get(key) or "") for key in ("company", "role"))
            if isinstance(description, str) and len(clean_html(description)) >= 100:
                return description
        except (ValueError, KeyError, TypeError):
            pass
    for selector in [".jobdescription", "[itemprop='description']", ".ats-description", ".job-description__content", ".job-description__wrap", ".job-description", ".job-detail-description"]:
        element = soup.select_one(selector)
        if element and len(element.get_text(" ", strip=True)) >= 100:
            return str(element)
    if (urlparse(url).hostname or "").endswith("google.com"):
        main = soup.select_one("main")
        if main and main.find(string=lambda s: s and "Minimum qualifications" in s):
            return str(main)
    # Do not treat login pages, cookie notices, or the entire site as a JD.
    return ""


def fetch_description(raw_job: dict[str, Any], company: dict[str, Any]) -> str:
    url = str(raw_job.get("apply_url") or raw_job.get("source_url") or "")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("No official HTTPS posting URL")
    source = raw_job.get("source_platform") or company.get("source_type")
    if source == "custom_apple":
        data = http_get_json(f"https://jobs.apple.com/api/v1/jobDetails/{raw_job['external_id']}", params={"locale": "en-us"})
        posting = data.get("res") or {}
        parts = [str(posting.get(key) or "") for key in ("jobSummary", "description", "responsibilities")]
        parts.extend(["<h3>Minimum Qualifications</h3>", str(posting.get("minimumQualifications") or ""), "<h3>Preferred Qualifications</h3>", str(posting.get("preferredQualifications") or "")])
        for footer in posting.get("postingFooters") or []:
            for block in (footer.get("localizations") or {}).get("en_US", []):
                parts.append(str(block.get("content") or ""))
        return "\n".join(parts)
    if parsed.hostname.endswith(".myworkdayjobs.com") and "/job/" in parsed.path:
        prefix, suffix = parsed.path.split("/job/", 1)
        site = prefix.strip("/").split("/")[-1]
        tenant = parsed.hostname.split(".")[0]
        endpoint = f"https://{parsed.netloc}/wday/cxs/{tenant}/{site}/job/{suffix}"
        return str(http_get_json(endpoint).get("jobPostingInfo", {}).get("jobDescription") or "")
    if source == "oracle_hcm":
        base = str(company.get("source_base_url") or "https://eeho.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions")
        endpoint = base.replace("recruitingCEJobRequisitions", "recruitingCEJobRequisitionDetails")
        data = http_get_json(endpoint, params={"finder": f"ById;Id={raw_job['external_id']},siteNumber={company['source_key']}", "onlyData": "true"})
        items = data.get("items") or []
        posting = next((item for item in items if str(item.get("Id")) == str(raw_job["external_id"])), {})
        return "\n".join(str(posting.get(key) or "") for key in ("ExternalDescriptionStr", "ExternalResponsibilitiesStr", "ExternalQualificationsStr"))
    if source == "smartrecruiters":
        data = http_get_json(f"https://api.smartrecruiters.com/v1/companies/{company['source_key']}/postings/{raw_job['external_id']}")
        sections = (data.get("jobAd") or {}).get("sections") or {}
        return "\n".join(str((sections.get(key) or {}).get("text") or "") for key in ("companyDescription", "jobDescription", "qualifications", "additionalInformation"))
    return description_from_page(http_get_text(url), url)


def enrich_description(raw_job: dict[str, Any], company: dict[str, Any], cached: dict[str, Any], checked_at: str, allow_fetch: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = dict(raw_job)
    source = raw.get("source_platform") or company.get("source_type")
    original = str(raw.get("description") or "")
    url = str(raw.get("apply_url") or raw.get("source_url") or "")
    cached = cached if cached.get("source_url") == url else {}
    status = raw.get("description_status") or ("full" if original and source not in SUMMARY_SOURCES else "summary" if original else "missing")
    if not clean_html(original):
        status = "missing"
    description = original
    fetched_at = checked_at if status == "full" else ""
    if status != "full":
        try:
            age = (datetime.fromisoformat(checked_at.replace("Z", "+00:00")) - datetime.fromisoformat(str(cached.get("fetched_at", "")).replace("Z", "+00:00"))).total_seconds() / 3600
        except ValueError:
            age = CACHE_HOURS + 1
        if cached.get("status") == "full" and 0 <= age < CACHE_HOURS:
            description, status, fetched_at = cached["text"], "full", cached["fetched_at"]
        else:
            # Retry failed detail fetches at most once per day, rather than on
            # every six-hour listing sync. The listing itself stays active.
            retry_at = str(cached.get("last_attempted") or "")
            try:
                retry_age = (datetime.fromisoformat(checked_at.replace("Z", "+00:00")) - datetime.fromisoformat(retry_at.replace("Z", "+00:00"))).total_seconds() / 3600
            except ValueError:
                retry_age = 24
            if cached.get("parser_version") != PARSER_VERSION:
                retry_age = 24
            try:
                full = fetch_description(raw, company) if allow_fetch and (retry_age >= 24 or not cached.get("fetch_error")) else ""
                if len(clean_html(full)) >= 100:
                    description, status, fetched_at = full, "full", checked_at
                    cached = {}
                elif not cached.get("fetch_error"):
                    raise ValueError("No complete description in public response" if allow_fetch else "Source details temporarily unavailable")
            except Exception as error:
                if allow_fetch:
                    LOGGER.warning("Job detail unavailable for %s/%s: %s", company["slug"], raw.get("external_id"), type(error).__name__)
                cached = {**cached, "last_attempted": checked_at, "fetch_error": type(error).__name__, "fetch_error_code": getattr(getattr(error, "response", None), "status_code", None)}
            if status != "full" and cached.get("status") == "full":
                description, status, fetched_at = cached["text"], "full", cached["fetched_at"]
    raw.update(description=description, description_status=status, description_fetched_at=fetched_at)
    detail = {"text": clean_html(description, preserve_paragraphs=True), "status": status, "fetched_at": fetched_at, "source_url": url, "parser_version": PARSER_VERSION}
    if raw.get("level_hint"):
        detail["level_hint"] = raw["level_hint"]
    if cached.get("fetch_error"):
        detail.update(last_attempted=cached.get("last_attempted", ""), fetch_error=cached["fetch_error"], fetch_error_code=cached.get("fetch_error_code"))
    return raw, detail
