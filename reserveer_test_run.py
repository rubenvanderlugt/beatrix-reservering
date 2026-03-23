from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import os

# Login via GitHub Secrets
USERNAME = os.getenv("BEATRIX_USER")
PASSWORD = os.getenv("BEATRIX_PASS")

BOOT_NAAM = "St. Antonisloop"
PLOEG_ID = "#cbxg_ploeg_p120"   # Donderslag

def aankomende_zondag():
    """Dummy testdatum: eerstvolgende zondag (veilig, geen echte reservering)."""
    nl_now = datetime.utcnow() + timedelta(hours=0)
    dagen = (6 - nl_now.weekday()) % 7
    return nl_now + timedelta(days=dagen)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # LOGIN
    page.goto("https://www.ervbeatrix.nl/component/users/login?Itemid=101")
    page.fill("input[name='username']", USERNAME)
    page.fill("input[name='password']", PASSWORD)
    page.click("button[type='submit']")
    page.wait_for_load_state()

    # NAAR RESERVERINGSPAGINA
    page.goto("https://www.ervbeatrix.nl/snel-naar/boten-afschrijven?view=reservering")
    page.wait_for_load_state()

    # TESTDATUM: A.S. zondag
    doel = aankomende_zondag()
    dag = doel.day
    page.click(f"text='{dag}'")

    # BOOT
    boot = page.locator(f"td:has-text('{BOOT_NAAM}')").first

    # TIJDSLOT
    tijdcel = boot.locator("xpath=following-sibling::td[15]")
    tijdcel.click()

    # POPUP iframe
    page.wait_for_selector("#if_bootsrc")
    frame = page.frame_locator("#if_bootsrc")

    # Klik op 'Reserveren'
    frame.locator("#btn_reserve_txt").click()

    # PLOEG: Donderslag
    page.locator(PLOEG_ID).check()

    # Tijd invullen (dummy, maakt niet uit)
    page.fill("input[name='afstijdvan']", "09:30")
    page.fill("input[name='afstijdtot']", "11:00")
