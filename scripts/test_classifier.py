from __future__ import annotations

from classifier import classify_category, classify_level, parse_location


def test_internals_is_not_intern() -> None:
    assert classify_level("Senior Software Engineer - Database Engine Internals") == "Senior"
    assert classify_level("Staff Software Engineer - Database Engine Internals") == "Staff"


def test_actual_intern_titles() -> None:
    assert classify_level("Software Engineer Intern") == "Intern"
    assert classify_level("Software Engineering Internship") == "Intern"
    assert classify_level("Summer Intern, Machine Learning") == "Intern"


def test_senior_beats_entry_description_noise() -> None:
    assert classify_level("Senior Software Engineer", "0-2 years mentioned in unrelated text") == "Senior"


def test_numbered_engineering_levels() -> None:
    assert classify_level("Software Development Engineer II, AWS Security", "2+ years of experience") == "Mid"
    assert classify_level("Software Engineer 2") == "Mid"
    assert classify_level("Software Development Engineer I") == "Entry"
    assert classify_level("SDE 1") == "Entry"


def test_leadership_titles_are_excluded_from_entry() -> None:
    assert classify_level("Software Development Manager, AWS") == "Manager"
    assert classify_level("Lead Software Engineer") == "Manager"
    assert classify_level("Software Engineer (Technical Leadership)") == "Manager"


def test_remote_and_hybrid_location_detection() -> None:
    assert parse_location("Virtual, USA").remote_type == "remote"
    assert parse_location("Remote, US").remote_type == "remote"
    assert parse_location("Remote, US").is_us_based
    assert parse_location("United States of America").is_us_based
    assert parse_location("United States").remote_type == "unknown"
    assert parse_location("Redmond, WA", "This role requires 3 days / week in-office.").remote_type == "hybrid"
    assert not parse_location("DE-Berlin-Trion Building").is_us_based
    assert not parse_location("DE-Munich-MSO").is_us_based


def test_hyphenated_front_end_title_is_frontend() -> None:
    assert (
        classify_category(
            "Front-End Engineer, AWS Holmes, AWS Holmes",
            "Own the front-end architecture and work with backend services.",
        )
        == "Frontend"
    )


if __name__ == "__main__":
    test_internals_is_not_intern()
    test_actual_intern_titles()
    test_senior_beats_entry_description_noise()
    test_numbered_engineering_levels()
    test_leadership_titles_are_excluded_from_entry()
    test_remote_and_hybrid_location_detection()
    test_hyphenated_front_end_title_is_frontend()
    print("classifier tests passed")
