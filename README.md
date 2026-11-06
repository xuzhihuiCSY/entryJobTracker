# US Tech Entry Jobs Tracker

A lightweight static tracker for curated U.S. tech job application links, focused on SDE, DS, ML, Data Engineering, AI, Backend, Full Stack, Cloud, DevOps, Security, and related roles.

The MVP is intentionally simple:

- Next.js App Router + TypeScript + Tailwind CSS
- Static JSON files in `public/data/`
- Python 3 crawler scripts
- YAML company source config
- GitHub Actions scheduled updates
- Vercel deployment
- No backend API, database, authentication, or admin panel

## Why there is no database

The site only needs to display current active jobs. `public/data/jobs.json` is the current snapshot, while `public/data/seen_jobs.json` preserves `first_seen` timestamps. This keeps hosting and deployment simple, avoids operational database work, and makes the data diffable in Git.

Closed jobs are not retained in `jobs.json`. If a job disappears from the next source response, it is removed from the active listing.

## Run the frontend locally

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

For production checks:

```bash
npm run typecheck
npm run build
```

## Run the crawler locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/fetch_jobs.py --all
```

Other supported commands:

```bash
python scripts/fetch_jobs.py --priority=1
python scripts/fetch_jobs.py --priority=2
python scripts/fetch_jobs.py --priority=3
python scripts/fetch_jobs.py --companies palantir duolingo capital-one
```

The crawler writes:

- `public/data/jobs.json`
- `public/data/companies.json`
- `public/data/seen_jobs.json`
- `public/data/last_updated.json`
- `public/data/descriptions/<company-slug>.json` (posting text, loaded on demand)

## Configure companies.yaml

Company sources live in `scripts/data/companies.yaml`.

```yaml
- name: Example Company
  slug: example
  company_group: startup
  source_type: greenhouse
  source_key: example
  career_url: https://boards.greenhouse.io/example
  sync_priority: 2
  enabled: true
```

Supported `source_type` values:

- `avature`
- `bank_of_america`
- `bain`
- `goldman_sachs`
- `ibm`
- `kpmg`
- `mckinsey`
- `successfactors`
- `greenhouse`
- `lever`
- `ashby`
- `eightfold`
- `bytedance`
- `rippling`
- `smartrecruiters`
- `talentbrew`
- `ubs`
- `workday`
- `oracle_hcm`
- `phenom`
- `radancy`
- `zoom`
- `custom_google`
- `custom_amazon`
- `custom_microsoft`
- `custom_meta`
- `custom_apple`
- `custom_nvidia`
- `custom_generic`
- `placeholder`

Use `sync_priority: 1` for high-frequency sources, `2` for daily sources, and `3` for weekly long-tail sources.

Greenhouse companies can use `additional_source_keys` to merge multiple verified
boards under one company. Duolingo includes both `duolingo` and
`duolingounirecruitment`; a failure from either board preserves the previous
company snapshot. TalentBrew sources can set `source_search_terms` to include
campus programs that do not have "engineer" in the title.
Workday supports the same multi-board setting. PwC includes its experienced and
entry-level boards. Zoom and PwC use verified Workday sources after their old
career URLs stopped working.

The catalog also includes Citadel's official career link, with `enabled: false`:
its website returned HTTP 403 during source verification. Airtable's verified
board may have zero relevant technical jobs; this is a valid successful sync.

## PhD requirement filter

All job list filters default to hiding only postings classified as
`phd_requirement: required`. Users can show all postings or only PhD-required
postings. Master's/Bachelor's or PhD alternatives, equivalent experience,
preferred qualifications, and unknown requirements remain visible.

The crawler classifies the full source description and title before truncating
the card snippet. `phd_evidence` records the matching text for review on the job
card. Sources that do not supply a description can only be classified from the
title; unknown means unconfirmed, not that no PhD is required. Existing snapshot
rows without education metadata are kept visible until refreshed.

Regression checks:

```bash
python scripts/test_education.py
python scripts/test_new_sources.py
npm run test:filters
```

## Add a Greenhouse company

Find the board token from a public URL such as:

```text
https://boards.greenhouse.io/companyslug
```

Then add:

```yaml
- name: Company Name
  slug: company-name
  company_group: startup
  source_type: greenhouse
  source_key: companyslug
  career_url: https://boards.greenhouse.io/companyslug
  sync_priority: 2
  enabled: true
```

## Add a Lever company

Find the Lever slug from:

```text
https://jobs.lever.co/companyslug
```

Then add:

```yaml
- name: Company Name
  slug: company-name
  company_group: startup
  source_type: lever
  source_key: companyslug
  career_url: https://jobs.lever.co/companyslug
  sync_priority: 2
  enabled: true
```

## Add an Ashby company

Find the organization slug from:

```text
https://jobs.ashbyhq.com/companyslug
```

Then add:

```yaml
- name: Company Name
  slug: company-name
  company_group: startup
  source_type: ashby
  source_key: companyslug
  career_url: https://jobs.ashbyhq.com/companyslug
  sync_priority: 2
  enabled: true
```

## Add a Big Tech custom parser

Create or update a file in `scripts/adapters/`, then expose:

```python
def fetch_company_jobs(company_config: dict) -> list[dict]:
    return [
        {
            "external_id": "...",
            "title": "...",
            "location_raw": "...",
            "description": "...",
            "apply_url": "...",
            "source_url": "...",
            "source_platform": "custom_company",
        }
    ]
```

Register the adapter in `scripts/adapters/__init__.py`. Placeholder parsers intentionally return an empty list and log a warning, so incomplete custom parsers do not break the sync.

Do not invent `source_key` values. If a company source is uncertain, leave `source_key` blank and `enabled: false` until the public endpoint is verified.

## GitHub Actions automatic updates

The homepage chart uses `public/data/history.json`, with the latest successful
or partially successful snapshot per UTC day. Each sync records the active-job
total, companies with active postings, and known failed sources; a total source
failure does not create a new observation. Both crawling and cached-JD
reclassification update the day's final count before validation and commit.
Missing days remain gaps. Net change compares recorded snapshots, and percentage
change uses the first count in the selected window (undefined for a zero baseline).
Counts cover all tracked job levels and can change when source coverage or
classification rules change, as well as when postings open or close.

The initial history was recovered from committed snapshots, without deriving
counts from `first_seen` or fabricating missing dates. To repeat this one-time
recovery from a full Git checkout, run `python scripts/backfill_history.py`.
Scheduled Actions and Vercel builds use the committed history directly and do
not need full Git history. `npm run test:trends` checks chart calculations.

The crawler runs on GitHub's `macos-15` hosted runner. Cloud tests found that
Uber's public careers domain challenges the Azure-hosted Ubuntu runner, while
standard HTTP requests from the macOS runner succeed. The Uber adapter uses the
official client's `/api/jobs/search/` route and the shared HTTP helper; it does
not attempt to solve challenge pages. Application CI remains on Ubuntu.

The manual **Update jobs** workflow accepts an optional `companies` input, such
as `uber` or `uber zoom`, to refresh specific sources instead of an entire
priority group. Leave it blank to use the selected priority. Scheduled runs
continue to use their configured priorities.

Each company records `last_attempted`, `last_synced`, `sync_status`, active job
count and full-JD count. The Companies page distinguishes a failed fetch with
retained postings from a successful sync with zero jobs. It marks data stale
after 12 hours (priority 1), 48 hours (priority 2), or 14 days (priority 3).
The global summary describes the latest run; it does not claim all companies
were refreshed. An all-source failure preserves the last successful timestamp
and exits nonzero. Partial failures retain only the failed sources' old data.

Full descriptions use the public source payload, official detail API, JobPosting
JSON-LD, or a specific job-description section. Workday, Oracle HCM,
SmartRecruiters and common career-page formats have detail fetchers. Full text
is kept in per-company JSON files, fetched only when a user expands a job card.
Detail responses are reused for seven days, failed detail requests are retried
after one day, and repeated access failures stop detail requests for that source
in the current run. A missing/blocked JD never removes an otherwise valid job.

Visa filters distinguish explicit sponsorship, explicit no sponsorship,
conditional sponsorship, and unknown. Hiding explicit no-sponsorship jobs keeps
unknown postings visible. Work authorization questions and silence are not
treated as sponsorship commitments. Citizenship and clearance requirements have
separate optional filters. Evidence text is shown on each tagged job card.

Validate the generated snapshot with `python scripts/validate_data.py`.
Run all crawler regressions with `python scripts/run_tests.py`.
Use `python scripts/reclassify_jobs.py` to apply new education, campus, and visa
rules to cached complete descriptions while preserving IDs and source timestamps.
Incomplete or missing JDs keep their sponsorship status unknown.

`.github/workflows/update-jobs.yml` supports:

- Priority 1 every 6 hours
- Priority 2 daily
- Priority 3 weekly
- Manual runs for `all`, `1`, `2`, or `3`

After the crawler runs, the workflow validates and commits changes under
`public/data/`, including the per-company description files. Runs are serialized
to prevent overlapping scheduled jobs from overwriting each other's snapshots.
If the branch advances while a crawler is running, that run does not publish its
older generated snapshot; the next scheduled run picks up the new branch head.
Queued runs check out the current branch when they start, so a preceding data
commit does not make an otherwise valid queued sync stale.

`.github/workflows/ci.yml` runs Python regressions, snapshot validation, filter
tests, TypeScript checks, and the production build on application pushes and pull
requests. Data-only commits skip this duplicate application check. The connected
Vercel Git integration deploys the committed frontend and JSON snapshot together;
the crawler runs in GitHub Actions, not during a Vercel build. No Vercel API token
or Deploy Hook is required for the existing Git integration.

If a source request fails, the crawler logs the error and preserves that company's previous data instead of treating the failed run as a successful zero-job sync.

## Deploy to Vercel

Import the repository in Vercel and use the default Next.js settings:

- Build command: `npm run build`
- Install command: `npm install`
- Output: managed by Next.js on Vercel

No backend service or database is required.

## Compliance

This project only targets public career pages and public job APIs. It does not bypass login, CAPTCHA, paywalls, or access controls. It does not scrape LinkedIn or Indeed as MVP data sources.

Crawler rules:

- Use low request frequency.
- Set a clear `User-Agent`.
- Set request timeouts.
- Respect `robots.txt` where applicable.
- Link users to official application pages.
- Do not claim complete coverage.
- Do not describe the site as an official partner of any company.

Site disclaimer:

> We link to official career pages and public job postings. We are not affiliated with these companies. Job availability can change quickly.
