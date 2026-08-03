from __future__ import annotations

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


def test_image_companies_are_in_catalog() -> None:
    companies = load_companies()
    configured_slugs = {company["slug"] for company in companies}

    assert IMAGE_COMPANY_SLUGS <= configured_slugs


def test_company_slugs_are_unique() -> None:
    companies = load_companies()
    slugs = [company["slug"] for company in companies]

    assert len(slugs) == len(set(slugs))


if __name__ == "__main__":
    test_image_companies_are_in_catalog()
    test_company_slugs_are_unique()
    print("company catalog tests passed")
