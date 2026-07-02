from __future__ import annotations

from classifier import classify_level


def test_internals_is_not_intern() -> None:
    assert classify_level("Senior Software Engineer - Database Engine Internals") == "Senior"
    assert classify_level("Staff Software Engineer - Database Engine Internals") == "Staff"


def test_actual_intern_titles() -> None:
    assert classify_level("Software Engineer Intern") == "Intern"
    assert classify_level("Software Engineering Internship") == "Intern"
    assert classify_level("Summer Intern, Machine Learning") == "Intern"


def test_senior_beats_entry_description_noise() -> None:
    assert classify_level("Senior Software Engineer", "0-2 years mentioned in unrelated text") == "Senior"


if __name__ == "__main__":
    test_internals_is_not_intern()
    test_actual_intern_titles()
    test_senior_beats_entry_description_noise()
    print("classifier tests passed")
