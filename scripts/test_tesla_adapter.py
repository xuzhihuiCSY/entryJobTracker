from __future__ import annotations

from adapters.tesla import jobs_from_state


def _payload() -> dict:
    return {
        "lookup": {
            "departments": {
                "4": "Tesla AI",
                "7": "Engineering & Information Technology",
                "11": "Manufacturing",
            },
            "locations": {
                "401022": "Palo Alto, California",
                "263687": "Fort Worth, Texas",
                "US000": "Remote, United States",
                "CA999": "Toronto, Ontario",
            },
            "types": {
                "1": "fulltime",
                "3": "intern",
            },
        },
        "geo": [
            {
                "id": "5",
                "name": "North America",
                "sites": [
                    {
                        "id": "US",
                        "name": "United States",
                        "states": [
                            {"id": "CA", "name": "California", "cities": {"Palo Alto": ["401022"]}},
                            {"id": "TX", "name": "Texas", "cities": {"Fort Worth": ["263687"]}},
                            {"id": "00-RM", "name": "Remote", "cities": {"Remote": ["US000"]}},
                        ],
                    },
                    {
                        "id": "CA",
                        "name": "Canada",
                        "cities": {"Toronto": ["CA999"]},
                    },
                ],
            }
        ],
        "listings": [
            {
                "id": "224501",
                "t": "AI Engineer, Manipulation, Optimus",
                "dp": "4",
                "l": "401022",
                "y": 1,
            },
            {
                "id": "263687",
                "t": "Internship, Collision Technician Trainee (Summer 2026)",
                "dp": "7",
                "l": "263687",
                "y": 3,
            },
            {
                "id": "231000",
                "t": "Software Engineer, Vehicle UI",
                "dp": "7",
                "l": "US000",
                "y": 1,
            },
            {
                "id": "999999",
                "t": "Service Technician",
                "dp": "11",
                "l": "CA999",
                "y": 1,
            },
        ],
    }


def test_state_payload_filters_us_jobs_and_normalizes_rows() -> None:
    jobs = jobs_from_state(
        _payload(),
        site="US",
        source_url="https://www.tesla.com/cua-api/apps/careers/state?site=US",
    )

    assert len(jobs) == 3
    by_id = {job["external_id"]: job for job in jobs}
    assert (
        by_id["224501"]["apply_url"]
        == "https://www.tesla.com/careers/search/job/ai-engineer-manipulation-optimus-224501"
    )
    assert by_id["224501"]["location_raw"] == "Palo Alto, California"
    assert by_id["224501"]["description"] == "Tesla AI | Full-Time | Palo Alto, California"
    assert (
        by_id["263687"]["description"]
        == "Engineering & Information Technology | Intern/Apprentice | Fort Worth, Texas"
    )
    assert by_id["231000"]["location_raw"] == "Remote, United States"
    assert "999999" not in by_id


if __name__ == "__main__":
    test_state_payload_filters_us_jobs_and_normalizes_rows()
    print("tesla adapter tests passed")
