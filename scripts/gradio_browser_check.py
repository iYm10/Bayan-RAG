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
        page.goto(
            os.getenv("BAYAN_GRADIO_URL", "http://127.0.0.1:7860"), wait_until="domcontentloaded"
        )
        page.get_by_label("Ask about your documents").fill("How does hybrid search work?")
        page.get_by_role("button", name="Find evidence").click()
        page.get_by_role("button", name="Copy source excerpts").click()
        expect(page.locator("#source-excerpts textarea")).to_have_value(
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
        page.get_by_role("button", name="Manage your collection").click()
        page.get_by_role("combobox", name="Document to remove").click()
        page.get_by_role("option", name="fixture.txt", exact=True).click()
        page.get_by_role("button", name="Remove selected document").click()
        expect(page.locator(".library-row")).to_have_count(5)
        page.get_by_role("button", name="Reset to sample collection").click()
        expect(page.get_by_label("Library status")).to_have_value(
            "Sample collection restored for your session."
        )
        page.get_by_role("button", name="Knowledge assistant").click()
        expect(page.get_by_role("tab", name="Knowledge assistant", exact=True)).to_have_attribute(
            "aria-selected", "true"
        )
        page.get_by_role("button", name="What makes hybrid search effective?", exact=False).click()
        expect(page.locator("#source-excerpts textarea")).to_have_value(
            re.compile("SOURCE EXCERPTS"), timeout=20000
        )
        page.locator(".evidence-card summary").first.click()
        expect(page.locator(".evidence-card").first).to_have_attribute("open", "")
        page.set_viewport_size({"width": 390, "height": 844})
        for tab in ["Knowledge assistant", "Document library", "Evaluation lab"]:
            page.get_by_role("button", name=tab, exact=False).click()
            assert not page.evaluate("document.documentElement.scrollWidth > innerWidth"), (
                f"Overflow: {tab}"
            )
        browser.close()
        print(
            "Gradio checks passed: query, excerpts, upload, removal, reset, navigation, suggestions, source expansion, and mobile layout."
        )


if __name__ == "__main__":
    main()
