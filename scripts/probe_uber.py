"""Temporary public-endpoint diagnostics; no credentials or dataset writes."""
import json
import requests
from curl_cffi import requests as curl_requests

URL = "https://jobs.uber.com/api/jobs/search"
PARAMS = {"locale": "en", "search": "software", "countries": "United States", "page": 1}


def report(label, response):
    print(label, json.dumps({"status": response.status_code, "url": response.url,
          "headers": {k: v for k, v in response.headers.items() if k.lower() in {
              "content-type", "server", "cf-mitigated", "x-vercel-mitigated", "location"}},
          "body_start": response.text[:600]}, ensure_ascii=True), flush=True)


report("plain_requests", requests.get(URL, params=PARAMS, timeout=30))
with curl_requests.Session(impersonate="chrome120") as session:
    session.headers.update({"Accept": "application/json,text/plain,*/*", "Referer": "https://jobs.uber.com/en/jobs/"})
    report("existing_adapter", session.get(URL, params=PARAMS, timeout=30))
report("public_careers_page", requests.get("https://jobs.uber.com/en/jobs/", timeout=30))
report("official_client_route", requests.get(URL + "/", params=PARAMS, timeout=30))
