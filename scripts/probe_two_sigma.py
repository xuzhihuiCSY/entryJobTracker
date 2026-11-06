"""Temporary read-only inspection of the official Two Sigma job board."""
import requests
from bs4 import BeautifulSoup

for url in ['https://careers.twosigma.com/', 'https://careers.twosigma.com/careers/SearchJobs']:
    try:
        r = requests.get(url, timeout=25)
        print('STATUS', r.status_code, r.url, r.headers.get('Content-Type'), flush=True)
        if not r.ok:
            print(r.text[:300], flush=True)
            continue
        soup = BeautifulSoup(r.text, 'html.parser')
        print('TEXT', soup.get_text(' ', strip=True)[:6500], flush=True)
        articles = soup.select('article')
        print('ARTICLES', len(articles), str(articles[0])[:5500] if articles else '', flush=True)
        print('LINKS', [(a.get_text(' ',strip=True), a.get('href')) for a in soup.select('a[href]') if 'JobDetail' in a.get('href','') or 'jobOffset' in a.get('href','')][:7], flush=True)
        print('FORMS', [(f.get('action'), [(i.get('name'), i.get('value')) for i in f.select('input')]) for f in soup.select('form')], flush=True)
    except requests.RequestException as e:
        print(type(e).__name__, str(e)[:250], flush=True)
