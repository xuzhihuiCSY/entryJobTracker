from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TARGET_API = "/cua-api/apps/careers/state"
DEFAULT_PAGE_URL = "https://www.tesla.com/careers/search/?site=US&department=vehicle-software"
DEFAULT_OUTPUT = Path(".cache") / "tesla_careers_state.json"


def capture_state(page_url: str, output_path: Path, channel: str, timeout_ms: int) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("Python package 'playwright' is required. Install it with: pip install playwright") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    found: dict[str, Any] = {"saved": False}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=channel, headless=False)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        def handle_response(response: Any) -> None:
            if TARGET_API not in response.url or found["saved"]:
                return
            print(f"Found: {response.url}")
            print(f"Status: {response.status}")
            if response.status != 200:
                return
            try:
                data = response.json()
            except Exception as exc:
                print(f"JSON parse failed: {exc}")
                return
            output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            found["saved"] = True
            print(f"Saved {output_path}")

        page.on("response", handle_response)

        try:
            page.goto(page_url, wait_until="domcontentloaded", timeout=timeout_ms)
        except Exception as exc:
            print(f"Goto error: {exc}")

        page.wait_for_timeout(15_000)
        if not found["saved"]:
            screenshot_path = output_path.with_suffix(".png")
            print("Did not capture Tesla state API. Saving screenshot for debugging.")
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"Saved {screenshot_path}")

        browser.close()

    if not found["saved"]:
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture Tesla careers state JSON from a real browser session.")
    parser.add_argument("--page-url", default=DEFAULT_PAGE_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--channel", default="msedge", help="Playwright Chromium channel, e.g. msedge or chrome")
    parser.add_argument("--timeout-ms", type=int, default=90_000)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    capture_state(args.page_url, args.output, args.channel, args.timeout_ms)
