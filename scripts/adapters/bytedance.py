from __future__ import annotations

from typing import Any

from utils import http_post_json

BASE_URL = "https://jobs.bytedance.com/api/v1/public/supplier"
SEARCH_PATH = "/search/job/posts"
SOURCE_URL = "https://joinbytedance.com/search"
R_AND_D_CATEGORY_ID = "6704215862603155720"
RECRUITMENT_IDS = ["1", "2"]
US_LOCATION_CODES = [
    "CT_94",  # Los Angeles
    "CT_75",  # San Francisco
    "CT_101443",  # Hillsboro
    "CT_1103355",  # San Jose
    "CT_114",  # New York
    "CT_203",  # San Diego
    "CT_157",  # Seattle
    "CT_1000001",  # Ashburn
    "CT_233",  # Washington D.C.
]
HEADERS = {
    "accept-language": "en-US",
    "website-path": "en",
    "origin": "https://joinbytedance.com",
    "referer": SOURCE_URL,
    "x-tt-env": "boe_epam_api",
}


def _location_from_city_info(city_info: dict[str, Any] | None) -> str:
    if not isinstance(city_info, dict):
        return ""
    parts: list[str] = []
    node: dict[str, Any] | None = city_info
    while isinstance(node, dict):
        name = str(node.get("en_name") or node.get("i18n_name") or "").strip()
        if name and name not in parts:
            parts.append(name)
        parent = node.get("parent")
        node = parent if isinstance(parent, dict) else None
    return ", ".join(parts)


def _description(job: dict[str, Any]) -> str:
    parts = [
        job.get("description"),
        job.get("requirement"),
        (job.get("recruit_type") or {}).get("en_name") if isinstance(job.get("recruit_type"), dict) else "",
        (job.get("job_subject") or {}).get("en_name") if isinstance(job.get("job_subject"), dict) else "",
        (job.get("job_category") or {}).get("en_name") if isinstance(job.get("job_category"), dict) else "",
    ]
    return "\n\n".join(str(part).strip() for part in parts if str(part or "").strip())


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    offset = 0
    limit = 100

    while offset < 1000:
        payload = {
            "keyword": "",
            "limit": limit,
            "offset": offset,
            "location_code_list": US_LOCATION_CODES,
            "recruitment_id_list": RECRUITMENT_IDS,
            "job_category_id_list": [R_AND_D_CATEGORY_ID],
        }
        data = http_post_json(f"{BASE_URL}{SEARCH_PATH}", payload, headers=HEADERS)
        if not isinstance(data, dict) or data.get("code") != 0:
            raise RuntimeError(f"ByteDance job search returned unexpected response: {data}")
        search_data = data.get("data") if isinstance(data.get("data"), dict) else {}
        jobs = search_data.get("job_post_list") if isinstance(search_data, dict) else []
        if not isinstance(jobs, list) or not jobs:
            break

        for job in jobs:
            if not isinstance(job, dict):
                continue
            external_id = str(job.get("id") or "").strip()
            if not external_id or external_id in seen:
                continue
            seen.add(external_id)
            apply_url = f"{SOURCE_URL}/{external_id}"
            results.append(
                {
                    "external_id": external_id,
                    "title": job.get("title") or "",
                    "location_raw": _location_from_city_info(job.get("city_info")),
                    "description": _description(job),
                    "apply_url": apply_url,
                    "source_url": apply_url,
                    "source_platform": "bytedance",
                }
            )

        offset += limit
        total = int(search_data.get("count") or 0)
        if offset >= total:
            break

    return results
