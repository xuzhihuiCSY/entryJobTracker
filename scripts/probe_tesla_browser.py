"""Check normal browser rendering, without proxies or stealth modifications."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page()
    response = page.goto('https://www.tesla.com/careers/search/', wait_until='networkidle', timeout=60000)
    print('BROWSER_PAGE_STATUS', response.status if response else None, flush=True)
    print('BROWSER_PAGE_TITLE', page.title(), flush=True)
    print('BROWSER_PAGE_TEXT', page.locator('body').inner_text()[:1200], flush=True)
    api = page.request.get('https://www.tesla.com/cua-api/careers/state', timeout=30000)
    print('BROWSER_API_STATUS', api.status, flush=True)
    if api.ok and 'json' in api.headers.get('content-type', ''):
        data = api.json()
        print('BROWSER_API_KEYS', list(data), flush=True)
        for key, value in data.items():
            sample = value[:2] if isinstance(value, list) else str(value)[:1000]
            print('FIELD', key, 'COUNT', len(value) if hasattr(value, '__len__') else None, 'SAMPLE', str(sample)[:2500], flush=True)
    else:
        print('BROWSER_API_BODY', api.text()[:300], flush=True)
    browser.close()
