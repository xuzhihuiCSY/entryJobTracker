"""Temporary read-only diagnostics for Tesla's public careers feed."""
import json
import requests
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup

for url in ['https://www.tesla.com/cua-api/careers/state', 'https://www.tesla.com/careers/search/']:
    response = requests.get(url, timeout=30)
    print('URL', url, 'STATUS', response.status_code, flush=True)
    if 'json' in response.headers.get('Content-Type', ''):
        data = response.json()
        print('TYPE', type(data).__name__, flush=True)
        if isinstance(data, dict):
            for key, value in data.items():
                print('FIELD', key, 'TYPE', type(value).__name__, 'COUNT', len(value) if hasattr(value, '__len__') else None,
                      'SAMPLE', json.dumps(value[:2] if isinstance(value, list) else dict(list(value.items())[:3]) if isinstance(value, dict) else value)[:6000], flush=True)
    else:
        soup = BeautifulSoup(response.text, 'html.parser')
        print('BODY', response.text[:300], flush=True)
        print('SCRIPTS', [tag['src'] for tag in soup.find_all('script', src=True)], flush=True)

response = curl_requests.get('https://www.tesla.com/cua-api/careers/state',
                             impersonate='chrome', headers={'Accept': 'application/json',
                             'Referer': 'https://www.tesla.com/careers/search/'}, timeout=30)
print('CURL_STATUS', response.status_code, flush=True)
if response.ok:
    payload = response.json()
    for key, value in payload.items():
        sample = value[:2] if isinstance(value, list) else dict(list(value.items())[:3]) if isinstance(value, dict) else value
        print('CURL_FIELD', key, 'TYPE', type(value).__name__, 'COUNT', len(value) if hasattr(value, '__len__') else None,
              'SAMPLE', json.dumps(sample)[:6000], flush=True)
else:
    print('CURL_BODY', response.text[:300], flush=True)
