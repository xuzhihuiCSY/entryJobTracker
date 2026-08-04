from __future__ import annotations

import html
import json

from adapters import ubs


def test_ubs_parses_preload_and_maps_jobs() -> None:
    smart_search = {
        "KeywordCustomSolrFields": "JobTitle",
        "LocationCustomSolrFields": "Location",
        "EncryptedSessionValue": "session-value",
    }
    preload = html.escape(json.dumps({"SmartSearchJSONValue": json.dumps(smart_search)}), quote=True)
    page = (
        f'<input id="preLoadJSON" value="{preload}">'
        '<input name="__RequestVerificationToken" value="request-token">'
    )
    parsed, token = ubs._parse_preload(page)
    assert parsed == smart_search
    assert token == "request-token"

    jobs = ubs._map_postings(
        [
            {
                "Questions": [
                    {"QuestionName": "reqid", "Value": "348973"},
                    {"QuestionName": "siteid", "Value": "5131"},
                    {"QuestionName": "jobtitle", "Value": "Software Engineer Intern"},
                    {"QuestionName": "formtext23", "Value": "United States - New York"},
                    {"QuestionName": "jobdescription", "Value": "Build services."},
                ]
            }
        ],
        "https://jobs.ubs.com",
        25008,
        5012,
    )
    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "348973"
    assert jobs[0]["location_raw"] == "United States - New York"
    assert "siteid=5131" in jobs[0]["apply_url"]
    assert "jobid=348973" in jobs[0]["apply_url"]


if __name__ == "__main__":
    test_ubs_parses_preload_and_maps_jobs()
    print("UBS adapter tests passed")
