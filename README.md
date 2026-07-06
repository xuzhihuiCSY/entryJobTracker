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
```

The crawler writes:

- `public/data/jobs.json`
- `public/data/companies.json`
- `public/data/seen_jobs.json`
- `public/data/last_updated.json`

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

- `greenhouse`
- `lever`
- `ashby`
- `bytedance`
- `rippling`
- `workday`
- `oracle_hcm`
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

`.github/workflows/update-jobs.yml` supports:

- Priority 1 every 6 hours
- Priority 2 daily
- Priority 3 weekly
- Manual runs for `all`, `1`, `2`, or `3`

After the crawler runs, the workflow commits `public/data/*.json` only when those files changed.

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
