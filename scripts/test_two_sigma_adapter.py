from unittest.mock import patch

from adapters import two_sigma
from job_details import description_from_page
from normalizer import normalize_job


def card(identifier, title, experience):
    return f'''<article class="article article--result"><h3><a href="/careers/JobDetail/Role/{identifier}">{title}</a></h3>
    <div class="article__header__content__text"><span>United States - NY New York</span>
    <div class="article__header__content__sub-text"><span>Engineering</span><span>{experience}</span></div></div></article>'''


def test_pagination_and_explicit_campus_metadata():
    pages = [card(1, "Research Engineer", "Internship") + '<a href="/careers/OpenRoles/?jobOffset=10">Next &gt;&gt;</a>',
             card(2, "Software Engineer - Campus Full-Time", "Early Careers")]
    with patch.object(two_sigma, "http_get_text", side_effect=pages) as get:
        raw = two_sigma.fetch_company_jobs({})
    assert len(raw) == 2 and get.call_count == 2
    assert get.call_args_list[1].args[0].endswith("OpenRoles/?jobOffset=10")
    company = {"slug": "two-sigma", "name": "Two Sigma"}
    assert normalize_job(raw[0], company, "now", "then")["level"] == "Intern"
    assert normalize_job(raw[1], company, "now", "then")["level"] == "New Grad"


def test_access_errors_and_repeated_pages_never_publish_a_partial_snapshot():
    repeated = card(1, "Software Engineer", "Experienced") + '<a href="/careers/OpenRoles/?jobOffset=10">Next &gt;&gt;</a>'
    for pages in (["<main>Sign in</main>"], [repeated, repeated], [card(1, "Software Engineer", "Experienced") + '<a href="https://example.com/">Next</a>']):
        with patch.object(two_sigma, "http_get_text", side_effect=pages):
            try:
                two_sigma.fetch_company_jobs({})
            except ValueError:
                pass
            else:
                raise AssertionError("An incomplete Two Sigma list must fail")


def test_only_the_complete_job_body_is_used_for_education_and_visa():
    body = "<h3>Qualifications</h3><p>A Master's or PhD in computer science is required.</p><p>We do not provide visa sponsorship.</p>" + "<p>Build research infrastructure and production systems.</p>" * 3
    page = '<aside><p>PhD required for other roles. Visa sponsorship is available.</p></aside><div class="grid__item--main"><article class="article--details"><div class="article__content">' + body + '</div></article></div><footer>Unrelated site footer</footer>'
    description = description_from_page(page, "https://careers.twosigma.com/careers/JobDetail/Role/1")
    assert "Unrelated" not in description and "other roles" not in description
    job = normalize_job({"external_id": "1", "title": "Research Engineer", "description": description, "location_raw": "New York, NY"}, {"slug": "two-sigma", "name": "Two Sigma"}, "now", "then")
    assert job["phd_requirement"] == "optional" and job["visa_signal"] == "not_likely"
    assert description_from_page('<main>Sign in</main>', 'https://careers.twosigma.com/careers/JobDetail/Role/1') == ""


if __name__ == "__main__":
    test_pagination_and_explicit_campus_metadata()
    test_access_errors_and_repeated_pages_never_publish_a_partial_snapshot()
    test_only_the_complete_job_body_is_used_for_education_and_visa()
    print("Two Sigma adapter tests passed")
