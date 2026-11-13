"""Smoke-test Gradio evidence search and session-local uploads."""

import os
import re

from playwright.sync_api import expect, sync_playwright


def main():
    with sync_playwright() as playwright:
        options = {"headless": True}
        if os.getenv("CHROMIUM_PATH"):
            options["executable_path"] = os.environ["CHROMIUM_PATH"]
        browser = playwright.chromium.launch(**options)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.goto("http://127.0.0.1:7860", wait_until="domcontentloaded")
        page.get_by_label("Ask about your documents").fill("How does hybrid search work?")
        page.get_by_role("button", name="Find evidence").click()
        expect(page.get_by_label("Source excerpts", exact=True)).to_have_value(
            re.compile("SOURCE EXCERPTS"), timeout=20000
        )
        page.get_by_role("tab", name="Session library").click()
        page.locator('input[type=file][accept*=".pdf"]').set_input_files(
            {
                "name": "fixture.txt",
                "mimeType": "text/plain",
                "buffer": b"The special reference is cobaltquartz.",
            }
        )
        page.get_by_role("button", name="Index in my session").click()
        expect(page.get_by_label("Library status")).to_have_value(
            re.compile("6 documents"), timeout=20000
        )
        page.get_by_role("button", name="Reset to sample collection").click()
        expect(page.get_by_label("Library status")).to_have_value(
            "Sample collection restored for your session."
        )
        browser.close()
        print("Gradio checks passed: query, excerpts, upload, reset.")


if __name__ == "__main__":
    main()
