"""Check normal browser rendering, without proxies or stealth modifications."""
import json
from playwright.sync_api import sync_playwright, TimeoutError

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=False)
    page = browser.new_page()
    responses = []
    page.on('response', lambda r: responses.append(r) if '/cua-api/careers/' in r.url else None)
    response = page.goto('https://www.tesla.com/careers/search/', wait_until='networkidle', timeout=60000)
    print('BROWSER_PAGE_STATUS', response.status if response else None, flush=True)
    try:
        page.get_by_role('heading', name='Build your Career at Tesla').wait_for(timeout=30000)
    except TimeoutError:
        print('CAREERS_HEADING_NOT_RENDERED', flush=True)
    print('BROWSER_PAGE_TITLE', page.title(), flush=True)
    print('BROWSER_PAGE_TEXT', page.locator('body').inner_text()[:1200], flush=True)
    for response in responses:
        print('SITE_API_RESPONSE', response.url, response.status, flush=True)
        if response.ok and 'json' in response.headers.get('content-type', ''):
            data = response.json()
            print('SITE_API_KEYS', list(data) if isinstance(data, dict) else type(data).__name__, flush=True)
            if isinstance(data, dict):
                for key, value in data.items():
                    sample = value[:2] if isinstance(value, list) else str(value)[:1000]
                    print('SITE_FIELD', key, 'COUNT', len(value) if hasattr(value, '__len__') else None, 'SAMPLE', str(sample)[:2500], flush=True)
    api = page.goto('https://www.tesla.com/cua-api/careers/state', wait_until='domcontentloaded', timeout=30000)
    print('BROWSER_API_STATUS', api.status, flush=True)
    if api.ok:
        try:
            page.wait_for_function("() => document.body && document.body.innerText.trim().startsWith('{')", timeout=15000)
        except TimeoutError:
            pass
        text = page.locator('pre').inner_text() if page.locator('pre').count() == 1 else page.locator('body').inner_text()
        try:
            data = json.loads(text)
        except ValueError:
            print('BROWSER_API_NON_JSON', text[:300], flush=True)
            browser.close()
            raise SystemExit(0)
        print('BROWSER_API_KEYS', list(data), flush=True)
        for key, value in data.items():
            sample = value[:2] if isinstance(value, list) else str(value)[:1000]
            print('FIELD', key, 'COUNT', len(value) if hasattr(value, '__len__') else None, 'SAMPLE', str(sample)[:2500], flush=True)
    else:
        print('BROWSER_API_BODY', page.locator('body').inner_text()[:300], flush=True)
    browser.close()
