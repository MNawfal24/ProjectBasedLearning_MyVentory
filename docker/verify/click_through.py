"""Click-through verification of the MyVentory dashboard.

Walks every interactive control, records console errors, and captures screenshots
at desktop and mobile widths. Run against the compose stack:

    python3 docker/verify/click_through.py http://localhost:8080
"""

import datetime as dt
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
OUT = pathlib.Path(__file__).resolve().parent / "shots"
OUT.mkdir(exist_ok=True)

results: list[dict] = []
console_errors: list[str] = []


def record(element: str, action: str, outcome: str) -> None:
    results.append({"element": element, "action": action, "outcome": outcome})


def main() -> int:
    try:
        run()
    finally:
        print(json.dumps({"steps": results, "console_errors": console_errors}, indent=2))

    return 0


def run() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})

        page.on(
            "console",
            lambda msg: console_errors.append(f"{msg.type}: {msg.text}")
            if msg.type == "error"
            else None,
        )
        page.on("pageerror", lambda exc: console_errors.append(f"pageerror: {exc}"))

        # Dashboard
        page.goto(f"{BASE}/", wait_until="networkidle")
        page.screenshot(path=OUT / "dashboard-desktop.png", full_page=True)
        record("Dashboard", "load", f"h1={page.locator('h1').first.inner_text()}")

        svg = page.locator("svg[role='img']").first
        record("Revenue chart", "rendered", f"present={svg.count() > 0}")

        for label, days in [("7 hari", 7), ("90 hari", 90), ("1 tahun", 365), ("30 hari", 30)]:
            with page.expect_response(lambda r: f"days={days}" in r.url and r.status == 200):
                page.get_by_role("button", name=label, exact=True).click()
            page.wait_for_timeout(400)
            record(f"Period {label}", "click", page.locator("main p").first.inner_text())

        with page.expect_response(lambda r: "outlet=2" in r.url and r.status == 200):
            page.select_option("#outlet-filter", label="SHOP002")
        page.wait_for_timeout(400)
        record("Outlet filter", "select SHOP002", page.locator("main p").first.inner_text())
        with page.expect_response(lambda r: "outlet=" not in r.url and r.status == 200):
            page.select_option("#outlet-filter", label="Semua outlet")
        page.wait_for_timeout(400)

        # Transactions
        page.get_by_role("link", name="Transactions").first.click()
        page.wait_for_load_state("networkidle")
        page.screenshot(path=OUT / "transactions-desktop.png", full_page=True)
        record("Transactions nav", "click", f"h1={page.locator('h1').first.inner_text()}")

        rows = page.locator("tbody tr").count()
        record("Transactions table", "render", f"rows={rows}")

        page.fill("#search", "SHOP001SEP2502704")
        page.wait_for_timeout(1400)
        record("Receipt search", "type a receipt number", f"rows={page.locator('tbody tr').count()}")
        page.fill("#search", "")
        page.wait_for_timeout(1400)

        page.get_by_role("button", name="Catat penjualan").click()
        page.wait_for_selector("[role='dialog']")
        page.screenshot(path=OUT / "transaction-form.png")
        record("Sale form", "open", "dialog visible")
        page.keyboard.press("Escape")
        page.wait_for_selector("[role='dialog']", state="detached")
        record("Sale form", "Escape", "dialog closed")

        page.get_by_role("button", name="Catat penjualan").click()
        page.wait_for_selector("[role='dialog']")
        page.get_by_role("button", name="Simpan transaksi").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)
        toast = page.locator("[role='status']").first
        record("Sale form", "submit", toast.inner_text() if toast.count() else "no toast")
        page.screenshot(path=OUT / "transaction-created.png", full_page=True)

        # Stock
        page.get_by_role("link", name="Stock").first.click()
        page.wait_for_load_state("networkidle")
        page.screenshot(path=OUT / "stock-desktop.png", full_page=True)
        record("Stock nav", "click", f"h1={page.locator('h1').first.inner_text()}")

        page.select_option("#stock-outlet", label="SHOP002")
        page.wait_for_timeout(600)
        record("Stock filter", "outlet SHOP002", f"rows={page.locator('tbody tr').count()}")
        page.select_option("#stock-outlet", label="Semua")
        page.wait_for_timeout(600)

        page.select_option("#stock-status", label="Menipis")
        page.wait_for_timeout(600)
        record("Stock filter", "status Menipis", f"rows={page.locator('tbody tr').count()}")
        page.select_option("#stock-status", label="Semua")
        page.wait_for_timeout(600)

        page.get_by_role("button", name="Catat pergerakan").click()
        page.wait_for_selector("[role='dialog']")
        page.select_option("#move-type", "in")
        page.fill("#move-qty", "25")
        page.get_by_role("button", name="Simpan").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)
        toast = page.locator("[role='status']").first
        record("Stock movement", "submit in +25", toast.inner_text() if toast.count() else "no toast")

        page.get_by_role("button", name="Atur minimum").first.click()
        page.wait_for_selector("[role='dialog']")
        page.fill("#min-qty", "4")
        page.get_by_role("button", name="Simpan").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)
        record("Stock minimum", "patch", "dialog closed" if page.locator("[role='dialog']").count() == 0 else "still open")

        # Products
        page.get_by_role("link", name="Products").first.click()
        page.wait_for_load_state("networkidle")
        page.screenshot(path=OUT / "products-desktop.png", full_page=True)
        record("Products nav", "click", f"h1={page.locator('h1').first.inner_text()}")

        page.get_by_role("button", name="Tambah produk").click()
        page.wait_for_selector("[role='dialog']")
        page.get_by_role("button", name="Tambah produk").last.click()
        page.wait_for_timeout(500)
        record("Product form", "submit empty", f"errors={page.locator('p.text-danger').count()}")
        # Unique per run: product names are unique, so a fixed name would fail on the
        # second run and leave the dialog open by design.
        page.fill("#product-name", f"Verifikasi {dt.datetime.now():%H%M%S}")
        page.fill("#product-price", "21000")
        page.get_by_role("button", name="Tambah produk").last.click()
        page.wait_for_selector("[role='dialog']", state="detached", timeout=15000)
        page.wait_for_timeout(400)
        record("Product form", "create", f"rows={page.locator('tbody tr').count()}, dialog closed")

        # Dark mode
        page.get_by_role("button", name="Mode gelap").click()
        page.wait_for_timeout(300)
        dark = page.evaluate("document.documentElement.classList.contains('dark')")
        page.screenshot(path=OUT / "dashboard-dark.png", full_page=True)
        record("Theme toggle", "click", f"dark={dark}")
        page.get_by_role("link", name="Overview").first.click()
        page.wait_for_load_state("networkidle")
        page.screenshot(path=OUT / "dashboard-dark.png", full_page=True)

        # Keyboard focus
        page.keyboard.press("Tab")
        focus = page.evaluate("document.activeElement?.textContent?.trim().slice(0, 40)")
        record("Keyboard", "Tab", f"focus={focus}")

        # Mobile
        mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        mobile.on("console", lambda msg: console_errors.append(f"mobile {msg.type}: {msg.text}") if msg.type == "error" else None)
        mobile.goto(f"{BASE}/", wait_until="networkidle")
        mobile.screenshot(path=OUT / "dashboard-mobile.png", full_page=True)
        overflow = mobile.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        record("Mobile dashboard", "load", f"horizontal_overflow={overflow}")

        mobile.get_by_role("link", name="Transactions").first.click()
        mobile.wait_for_load_state("networkidle")
        mobile.screenshot(path=OUT / "transactions-mobile.png", full_page=True)
        record(
            "Mobile transactions",
            "click",
            f"horizontal_overflow={mobile.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth')}",
        )

        browser.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
