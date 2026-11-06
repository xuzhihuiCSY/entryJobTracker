"""Apply current classification rules to cached complete JDs without recrawling."""
from __future__ import annotations

from authorization import classify_authorization
from classifier import classify_level
from education import classify_phd_requirement
from fetch_jobs import PUBLIC_DATA, build_company_rows, load_companies, utc_now
from utils import read_json, write_json


def reclassify_job(job: dict, detail: dict) -> dict:
    updated = dict(job)
    full_text = str(detail.get("text") or "") if detail.get("status") == "full" else ""
    level = classify_level(job["title"], full_text)
    hint = job.get("source_level_hint") or detail.get("level_hint")
    if classify_level(job["title"]) == "Unknown" and hint in {"Intern", "New Grad", "Entry", "Early Career"}:
        level = hint
    elif job.get("level") in {"Intern", "New Grad", "Early Career"} and classify_level(job["title"]) == "Unknown":
        # Legacy snapshots did not retain explicit source employment metadata.
        # Preserve established campus tags for otherwise generic titles.
        level = job["level"]
    if level != "Unknown" or full_text:
        updated["level"] = level
    if full_text:
        signal = classify_authorization(full_text)
        updated.update(visa_signal=signal.visa_signal, visa_evidence=signal.visa_evidence,
                       requires_citizenship=signal.requires_citizenship, citizenship_evidence=signal.citizenship_evidence,
                       requires_clearance=signal.requires_clearance, clearance_evidence=signal.clearance_evidence)
        education = classify_phd_requirement(job["title"], full_text)
        updated.update(phd_requirement=education.phd_requirement, phd_evidence=education.phd_evidence)
    else:
        updated.update(visa_signal="unknown", visa_evidence="", requires_citizenship=False,
                       citizenship_evidence="", requires_clearance=False, clearance_evidence="")
    return updated


def run() -> None:
    jobs = read_json(PUBLIC_DATA / "jobs.json", [])
    details = {company["slug"]: read_json(PUBLIC_DATA / "descriptions" / f"{company['slug']}.json", {}) for company in load_companies()}
    updated = [reclassify_job(job, details.get(job["company_slug"], {}).get(job["id"], {})) for job in jobs]
    write_json(PUBLIC_DATA / "jobs.json", updated)
    write_json(PUBLIC_DATA / "companies.json", build_company_rows(load_companies(), updated, set(), utc_now()))
    summary = read_json(PUBLIC_DATA / "last_updated.json", {})
    summary.update(total_jobs=len(updated), full_description_jobs=sum(job.get("description_status") == "full" for job in updated))
    write_json(PUBLIC_DATA / "last_updated.json", summary)
    print(f"Reclassified {len(updated)} jobs from cached complete descriptions; source timestamps preserved")


if __name__ == "__main__":
    run()
