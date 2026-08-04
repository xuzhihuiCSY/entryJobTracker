from __future__ import annotations

from adapters.workday import _parse_source_key
from fetch_jobs import load_companies


IMAGE_COMPANY_SLUGS = {
    "airbnb",
    "amazon",
    "bank-of-america",
    "bain",
    "barclays",
    "bcg",
    "blackrock",
    "citi",
    "coca-cola",
    "databricks",
    "dell",
    "deloitte",
    "ey",
    "ford",
    "goldman-sachs",
    "google",
    "hp",
    "ibm",
    "johnson-and-johnson",
    "jpmorgan-chase",
    "kpmg",
    "loreal",
    "mars",
    "mastercard",
    "mckinsey",
    "meta",
    "microsoft",
    "morgan-stanley",
    "netflix",
    "nvidia",
    "oliver-wyman",
    "openai",
    "oracle",
    "paypal",
    "pepsico",
    "procter-and-gamble",
    "pwc",
    "qualcomm",
    "roche",
    "roland-berger",
    "tesla",
    "texas-instruments",
    "ubs",
    "unilever",
    "visa",
    "wells-fargo",
    "adobe",
    "apollo-global-management",
    "cisco",
}

VERIFIED_WORKDAY_SOURCES = {
    "apollo-global-management": "athene.wd5/Apollo_Careers",
    "barclays": "barclays.wd3/External_Career_Site_Barclays",
    "blackrock": "blackrock.wd1/BlackRock_Professional",
    "coca-cola": "coke.wd1/coca-cola-careers",
    "hp": "hp.wd5/ExternalCareerSite",
    "johnson-and-johnson": "jj.wd5/JJ",
    "mastercard": "mastercard.wd1/CorporateCareers",
    "mars": "mars.wd3/External",
    "morgan-stanley": "ms.wd5/External",
    "procter-and-gamble": "pg.wd5/1000",
    "roche": "roche.wd3/roche-ext",
    "unilever": "unilever.wd3/Unilever_Experienced_Professionals",
    "visa": "visa.wd5/Visa",
    "wells-fargo": "wf.wd1/WellsFargoJobs",
}

VERIFIED_OTHER_SOURCES = {
    "citi": ("talentbrew", "https://jobs.citi.com/"),
    "dell": (
        "oracle_hcm",
        "https://enterpriseplatform.dell.com/hcmUI/CandidateExperience/en/sites/careers/jobs",
    ),
    "ford": (
        "oracle_hcm",
        "https://efds.fa.em5.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/jobs",
    ),
    "netflix": ("eightfold", "https://explore.jobs.netflix.net/careers"),
    "pepsico": ("radancy", "https://www.pepsicojobs.com/"),
    "pwc": ("talentbrew", "https://jobs.us.pwc.com/"),
    "roland-berger": ("smartrecruiters", "https://jobs.smartrecruiters.com/RolandBerger"),
}


def test_image_companies_are_in_catalog() -> None:
    companies = load_companies()
    configured_slugs = {company["slug"] for company in companies}

    assert IMAGE_COMPANY_SLUGS <= configured_slugs


def test_company_slugs_are_unique() -> None:
    companies = load_companies()
    slugs = [company["slug"] for company in companies]

    assert len(slugs) == len(set(slugs))


def test_verified_workday_sources_are_enabled() -> None:
    companies = {company["slug"]: company for company in load_companies()}

    for slug, source_key in VERIFIED_WORKDAY_SOURCES.items():
        company = companies[slug]
        assert company["source_type"] == "workday"
        assert company["source_key"] == source_key
        assert company["enabled"] is True
        parsed = _parse_source_key(source_key)
        assert parsed is not None
        _, host, site = parsed
        assert company["career_url"] == f"https://{host}/{site}"


def test_other_verified_sources_are_enabled() -> None:
    companies = {company["slug"]: company for company in load_companies()}

    for slug, (source_type, career_url) in VERIFIED_OTHER_SOURCES.items():
        company = companies[slug]
        assert company["source_type"] == source_type
        assert company["career_url"] == career_url
        assert company["enabled"] is True


if __name__ == "__main__":
    test_image_companies_are_in_catalog()
    test_company_slugs_are_unique()
    test_verified_workday_sources_are_enabled()
    test_other_verified_sources_are_enabled()
    print("company catalog tests passed")
