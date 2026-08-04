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
    "bain": ("bain", "https://www.bain.com/careers/find-a-role/"),
    "bank-of-america": ("bank_of_america", "https://careers.bankofamerica.com/en-us/job-search"),
    "citi": ("talentbrew", "https://jobs.citi.com/"),
    "deloitte": ("avature", "https://apply.deloitte.com/en_US/careers/SearchJobs"),
    "bcg": ("phenom", "https://careers.bcg.com/global/en/search-results"),
    "dell": (
        "oracle_hcm",
        "https://enterpriseplatform.dell.com/hcmUI/CandidateExperience/en/sites/careers/jobs",
    ),
    "ford": (
        "oracle_hcm",
        "https://efds.fa.em5.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/jobs",
    ),
    "goldman-sachs": ("goldman_sachs", "https://higher.gs.com"),
    "ibm": ("ibm", "https://www.ibm.com/careers/search"),
    "mckinsey": ("mckinsey", "https://www.mckinsey.com/careers/search-jobs"),
    "jpmorgan-chase": (
        "oracle_hcm",
        "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/jobs",
    ),
    "ey": ("successfactors", "https://careers.ey.com/careers?locale=en_US"),
    "kpmg": ("kpmg", "https://www.kpmguscareers.com/job-search/"),
    "loreal": ("avature", "https://careers.loreal.com/en_US/jobs/SearchJobs"),
    "netflix": ("eightfold", "https://explore.jobs.netflix.net/careers"),
    "oliver-wyman": ("workday", "https://careers.marsh.com/global/en/oliver-wyman"),
    "pepsico": ("radancy", "https://www.pepsicojobs.com/"),
    "pwc": ("talentbrew", "https://jobs.us.pwc.com/"),
    "roland-berger": ("smartrecruiters", "https://jobs.smartrecruiters.com/RolandBerger"),
    "texas-instruments": (
        "oracle_hcm",
        "https://careers.ti.com/en/sites/CX/jobs",
    ),
    "ubs": ("ubs", "https://www.ubs.com/global/en/careers/search-jobs.html"),
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

    oliver_wyman = companies["oliver-wyman"]
    assert oliver_wyman["source_key"] == "mmc.wd1/MMC"
    assert oliver_wyman["source_title_contains"] == "Oliver Wyman"


if __name__ == "__main__":
    test_image_companies_are_in_catalog()
    test_company_slugs_are_unique()
    test_verified_workday_sources_are_enabled()
    test_other_verified_sources_are_enabled()
    print("company catalog tests passed")
