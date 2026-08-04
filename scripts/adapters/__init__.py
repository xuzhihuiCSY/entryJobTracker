from __future__ import annotations

from typing import Any, Callable

from . import amd, amazon, apple, ashby, avature, bank_of_america, bytedance, eightfold, google, greenhouse, kpmg, lever, meta, microsoft, nvidia, oracle_hcm, phenom, placeholder, qualcomm, radancy, rippling, smartrecruiters, successfactors, talentbrew, uber, valve, workday, zoom

Adapter = Callable[[dict[str, Any]], list[dict[str, Any]]]

ADAPTERS: dict[str, Adapter] = {
    "greenhouse": greenhouse.fetch_company_jobs,
    "lever": lever.fetch_company_jobs,
    "ashby": ashby.fetch_company_jobs,
    "avature": avature.fetch_company_jobs,
    "bank_of_america": bank_of_america.fetch_company_jobs,
    "kpmg": kpmg.fetch_company_jobs,
    "successfactors": successfactors.fetch_company_jobs,
    "eightfold": eightfold.fetch_company_jobs,
    "bytedance": bytedance.fetch_company_jobs,
    "rippling": rippling.fetch_company_jobs,
    "smartrecruiters": smartrecruiters.fetch_company_jobs,
    "talentbrew": talentbrew.fetch_company_jobs,
    "custom_google": google.fetch_company_jobs,
    "custom_amazon": amazon.fetch_company_jobs,
    "custom_microsoft": microsoft.fetch_company_jobs,
    "custom_meta": meta.fetch_company_jobs,
    "custom_apple": apple.fetch_company_jobs,
    "custom_nvidia": nvidia.fetch_company_jobs,
    "custom_amd": amd.fetch_company_jobs,
    "custom_valve": valve.fetch_company_jobs,
    "custom_uber": uber.fetch_company_jobs,
    "custom_qualcomm": qualcomm.fetch_company_jobs,
    "oracle_hcm": oracle_hcm.fetch_company_jobs,
    "phenom": phenom.fetch_company_jobs,
    "radancy": radancy.fetch_company_jobs,
    "workday": workday.fetch_company_jobs,
    "zoom": zoom.fetch_company_jobs,
    "custom_generic": placeholder.fetch_company_jobs,
    "placeholder": placeholder.fetch_company_jobs,
}


def get_adapter(source_type: str) -> Adapter:
    return ADAPTERS.get(source_type, placeholder.fetch_company_jobs)
