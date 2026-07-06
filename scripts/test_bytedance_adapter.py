from __future__ import annotations

from adapters.bytedance import _description, _location_from_city_info


def test_location_from_city_info_includes_city_state_country() -> None:
    city_info = {
        "en_name": "San Jose",
        "parent": {
            "en_name": "California",
            "parent": {
                "en_name": "United States of America",
            },
        },
    }

    assert _location_from_city_info(city_info) == "San Jose, California, United States of America"


def test_description_combines_core_fields() -> None:
    job = {
        "description": "Build distributed systems.",
        "requirement": "BS in Computer Science.",
        "recruit_type": {"en_name": "Intern"},
        "job_subject": {"en_name": "Seed Foundation Model Campus Recruitment - Intern"},
        "job_category": {"en_name": "R&D"},
    }

    description = _description(job)
    assert "Build distributed systems." in description
    assert "BS in Computer Science." in description
    assert "Intern" in description
    assert "R&D" in description


if __name__ == "__main__":
    test_location_from_city_info_includes_city_state_country()
    test_description_combines_core_fields()
    print("bytedance adapter tests passed")
