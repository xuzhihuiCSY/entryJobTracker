from __future__ import annotations

from education import classify_phd_requirement
from normalizer import normalize_job
from adapters import amazon
from unittest.mock import patch


def test_required_phd() -> None:
    for title, description in [
        ("Software Engineer Intern (PhD)", ""),
        ("AI Research Engineer, New PhD Graduate", ""),
        ("Research Scientist", "A Ph.D. in computer science is required."),
        ("Research Scientist", "<h3>Minimum Qualifications</h3><ul><li>PhD in Computer Science</li></ul>"),
        ("Research Intern", "Currently pursuing a doctoral degree in Computer Science."),
        ("Research Intern", "Must be enrolled in a Ph.D. program."),
        ("Research Scientist", "You have a PhD in statistics."),
    ]:
        signal = classify_phd_requirement(title, description)
        assert signal.phd_requirement == "required", (title, description, signal)
        assert signal.phd_evidence


def test_alternative_degrees_remain_visible() -> None:
    for description in [
        "Master's or PhD in Computer Science required.",
        "A Master's degree or a Ph.D. in statistics.",
        "A PhD or Master's degree in machine learning is required.",
        "BS/MS/PhD in Computer Science.",
        "Bachelor’s, Master’s, or PhD in a relevant field.",
        "PhD in Computer Science or equivalent practical experience.",
        "You hold a PhD in Computer Science, or have equivalent experience.",
        "Hold a PhD or have research experience in machine learning.",
        "Hold a PhD or other degree in computer science.",
        "Candidates without a PhD may be considered with equivalent research experience.",
        "A Master's degree and 3 years of experience; or a PhD and 0 years.",
        "<li>A <strong>Master's</strong> or <strong>Ph.D.</strong> in Computer Science.</li>",
        "Required: M.S. or Ph.D. in a quantitative field.",
        "<li>Master's degree and 3 years of experience, OR</li><li>PhD in computer science.</li>",
        "<h3>Qualifications</h3><li>Master's or PhD in CS.</li><li>For MS holders: 5+ years of experience.</li><li>For PhD holders: 3+ years of experience.</li>",
        "<h3>Qualifications</h3><li>MS: 7+ years of experience.</li><li>PhD: 5+ years of experience.</li>",
        "<h3>You have</h3><li>BS and 5+ years of experience OR</li><li>MS and 3+ years of experience</li><li>PhD and 1+ years of experience</li>",
    ]:
        signal = classify_phd_requirement("Research Engineer", description)
        assert signal.phd_requirement == "optional", (description, signal)
    assert classify_phd_requirement("Software Engineer Graduate (BS/MS/PhD)").phd_requirement == "optional"
    assert classify_phd_requirement("Graduate (Master's or PhD)", "PhD in computer science.").phd_requirement == "optional"
    assert classify_phd_requirement("Technical Recruiter, PhD Software Engineering").phd_requirement == "unknown"


def test_preferred_and_negated_phd_remain_visible() -> None:
    for description, expected in [
        ("A PhD is preferred, but not required.", "preferred"),
        ("PhD in statistics is a plus.", "preferred"),
        ("<h2>Preferred Qualifications</h2><li>Ph.D. in computer science.</li>", "preferred"),
        ("<p>We prefer that you have:</p><li>PhD in a quantitative field</li>", "preferred"),
        ("No PhD required.", "optional"),
        ("A PhD is not required.", "optional"),
        ("You do not need a PhD to apply.", "optional"),
    ]:
        signal = classify_phd_requirement("Software Engineer", description)
        assert signal.phd_requirement == expected, (description, signal)


def test_mentions_and_missing_descriptions_are_not_requirements() -> None:
    for description in [
        "", "We collaborate with PhD researchers.",
        "Our team members have PhDs from leading universities.",
        "<h2>Minimum Qualifications</h2><li>BS in Computer Science.</li><h2>About the team</h2><p>Our team has PhD researchers.</p>",
    ]:
        assert classify_phd_requirement("Software Engineer", description).phd_requirement == "unknown"


def test_a_separate_preference_does_not_erase_required_phd() -> None:
    signal = classify_phd_requirement("Research Scientist", "PhD in computer science required. Preferred: industry research experience.")
    assert signal.phd_requirement == "required"


def test_phd_title_is_not_downgraded_by_an_unrelated_preference() -> None:
    signal = classify_phd_requirement("Research Intern (PhD)", "Preferred Qualifications\nCurrently enrolled in a PhD program.")
    assert signal.phd_requirement == "required"


def test_amazon_keeps_basic_and_preferred_qualifications_separate() -> None:
    with patch.object(amazon, "http_get_json", return_value={"jobs": [{
        "id": "1", "title": "Applied Scientist", "country_code": "US", "location": "Seattle, WA",
        "basic_qualifications": "<li>Master's in computer science.</li>",
        "preferred_qualifications": "<li>PhD in computer science.</li>",
    }]}):
        raw = amazon.fetch_company_jobs({})[0]
    job = normalize_job(raw, {"name": "Amazon", "slug": "amazon"}, "now", "then")
    assert job["phd_requirement"] == "preferred"
    signal = classify_phd_requirement("Research Scientist", "A PhD and a bachelor's degree in mathematics or a related field are required.")
    assert signal.phd_requirement == "required"


def test_normalizer_uses_complete_description_not_snippet() -> None:
    for suffix, expected in [
        ("<h3>Minimum Qualifications</h3><li>PhD in CS.</li>", "required"),
        ("<h3>Minimum Qualifications</h3><li>Master's or PhD in CS.</li>", "optional"),
    ]:
        job = normalize_job(
            {"external_id": "1", "title": "Research Engineer", "location_raw": "New York, NY", "description": "<p>" + "Introductory company copy. " * 30 + "</p>" + suffix},
            {"name": "Example", "slug": "example"}, "2026-11-06T00:00:00Z", "2026-11-06T00:00:00Z",
        )
        assert job["phd_requirement"] == expected
        assert "PhD" not in job["description_snippet"]


if __name__ == "__main__":
    for name, value in list(globals().items()):
        if name.startswith("test_"):
            value()
    print("education tests passed")
