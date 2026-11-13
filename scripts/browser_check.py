"""Exercise the local workspace and capture real desktop/mobile screenshots."""

import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = os.getenv("BAYAN_BASE_URL", "http://127.0.0.1:8000")


def capture(page, name):
    page.locator("#toast").evaluate("node => { node.hidden = true; }")
    page.screenshot(path=str(ROOT / f"assets/{name}.png"), full_page=True)


def main():
    with sync_playwright() as playwright:
        options = {"headless": True}
        if os.getenv("CHROMIUM_PATH"):
            options["executable_path"] = os.environ["CHROMIUM_PATH"]
        browser = playwright.chromium.launch(**options)
        page = browser.new_page(viewport={"width": 1440, "height": 950}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(BASE, wait_until="networkidle")
        expect(page.locator("#provider-label")).to_have_text("Offline demo mode")

        page.get_by_role("button", name="Document library").click()
        page.locator("#seed-button").click()
        expect(page.locator("#library-count")).to_have_text("5")
        capture(page, "library")

        # Untrusted filenames/content must be rendered as text, not markup.
        filename = "<img src=x onerror=alert(1)>.txt"
        page.locator("#upload").set_input_files(
            {
                "name": filename,
                "mimeType": "text/plain",
                "buffer": b"Browser fixture: the unique launch code is orchid-72. <script>alert(1)</script>",
            }
        )
        expect(page.locator("#library-count")).to_have_text("6")
        expect(page.locator("#document-list img")).to_have_count(0)
        page.once("dialog", lambda dialog: dialog.accept())
        page.get_by_role("button", name=f"Remove {filename}", exact=True).click()
        expect(page.locator("#library-count")).to_have_text("5")

        page.get_by_role("button", name="Knowledge assistant").click()
        expect(page.locator("#stat-docs")).to_have_text("5")
        capture(page, "workspace")
        page.get_by_role("button", name="What makes hybrid search effective?").click()
        expect(page.locator(".answer-badge")).to_have_text("SOURCE EXCERPTS · NO LANGUAGE MODEL")
        expect(page.locator(".source-card").first).to_be_visible()
        page.locator(".citation").first.click()
        expect(page.locator("#source-1 details")).to_have_attribute("open", "")
        capture(page, "evidence")

        page.locator("#question").fill("What is the price of gold today?")
        page.locator("#ask-button").click()
        expect(page.locator(".message.assistant").last).to_contain_text("not enough evidence")

        page.get_by_role("button", name="Evaluation lab").click()
        page.locator("#evaluate-button").click()
        expect(page.locator(".eval-row")).to_have_count(12)
        reference = json.loads((ROOT / "docs/evaluation-results.json").read_text())
        expect(page.locator("#eval-recall")).to_have_text(
            f"{reference['hybrid']['recall_at_k']:.3f}"
        )
        expect(page.locator("#baseline-comparison")).to_contain_text("BM25 baseline")
        capture(page, "evaluation")

        page.set_viewport_size({"width": 390, "height": 844})
        for label in ["Knowledge assistant", "Document library", "Evaluation lab"]:
            page.get_by_role("button", name=label).click()
            assert not page.evaluate("document.documentElement.scrollWidth > innerWidth"), (
                f"Horizontal overflow in {label}"
            )
        page.get_by_role("button", name="Knowledge assistant").click()
        page.locator("#clear-chat").click()
        page.locator("#question").blur()
        capture(page, "mobile")
        assert not errors, errors
        browser.close()
        print(
            "Browser checks passed: navigation, upload, duplicate-safe seed, safe text rendering, deletion, querying, citations, abstention, evaluation, and mobile layout."
        )


if __name__ == "__main__":
    main()
