"""Temporary read-only inspection of the official Two Sigma job board."""
import requests
from pathlib import Path
from bs4 import BeautifulSoup

for url in ['https://careers.twosigma.com/careers/OpenRoles']:
    try:
        r = requests.get(url, timeout=25)
        print('STATUS', r.status_code, r.url, r.headers.get('Content-Type'), flush=True)
        if not r.ok:
            print(r.text[:300], flush=True)
            continue
        soup = BeautifulSoup(r.text, 'html.parser')
        Path('.cache').mkdir(exist_ok=True)
        Path('.cache/two-sigma-list.html').write_text(r.text, encoding='utf-8')
        print('TEXT', soup.get_text(' ', strip=True)[:6500], flush=True)
        articles = soup.select('article')
        print('ARTICLES', len(articles), str(articles[0])[:5500] if articles else '', flush=True)
        print('LINKS', [(a.get_text(' ',strip=True), a.get('href')) for a in soup.select('a[href]') if 'JobDetail' in a.get('href','') or 'jobOffset' in a.get('href','') or 'OpenRoles' in a.get('href','')][:12], flush=True)
        print('FORMS', [(f.get('action'), [(i.get('name'), i.get('value')) for i in f.select('input')]) for f in soup.select('form')], flush=True)
        detail = next((a['href'] for a in soup.select('a[href]') if 'JobDetail' in a['href']), None)
        if detail:
            response = requests.get(detail, timeout=25)
            print('DETAIL_STATUS', response.status_code, detail, flush=True)
            Path('.cache/two-sigma-detail.html').write_text(response.text, encoding='utf-8')
            page = BeautifulSoup(response.text, 'html.parser')
            print('DETAIL_TEXT', page.get_text(' ', strip=True)[:8000], flush=True)
            print('DETAIL_SECTIONS', [(el.name, el.get('class'),el.get('id'),len(el.get_text())) for el in page.select('article, main, [itemprop], [class*=description]')], flush=True)
    except requests.RequestException as e:
        print(type(e).__name__, str(e)[:250], flush=True)
