from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import os
import time

# LOGIN GEGEVENS UIT GITHUB SECRETS
USERNAME = os.getenv("BEATRIX_USER")
PASSWORD = os.getenv("BEATRIX_PASS")

# BOOT + TIJDEN
BOOT_NAAM = "St. Antonisloop"
STARTTIJD = "09:30"
EINDTIJD = "11:00"

# PLOEG Donderslag
PLOEG_ID = "#cbxg_ploeg_p120"

def zaterdag_over_een_week():
    """Return the Saturday of next week in NL time."""
    utc_now = datetime.utcnow()
    nl_now = utc_now + timedelta(hours=1)  # CET. In zomer +2? Script wacht zelf tot middernacht, dus ok.
    dagen_tot_zat = (5 - nl_now.weekday()) % 7
    if dagen_tot_zat == 0:
        dagen_tot_zat = 7
    return nl_now + timedelta(days=dagen_tot_zat)

def wacht_tot_middernacht():
    """Wacht tot 00:00:01 Nederlandse tijd."""
    print("⏳ Wachten tot 00:00:01 NL tijd...")
    while True:
        nl_now = datetime.utcnow() + timedelta(hours=1)
        if nl_now.strftime("%H:%M:%S") == "00:00:01":
            print("🎉 Het is 00:00:01 — starten!")
            break
        time.sleep(0.2)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # WACHT TOT EXACT MIDDERNACHT NL
    wacht_tot_middernacht()

    # LOGIN
    page.goto("https://www.ervbeatrix.nl/component/users/login?Itemid=101")
    page.fill("input[name='username']", USERNAME)
    page.fill("input[name='password']", PASSWORD)
    page.click("button[type='submit']")
    page.wait_for_load_state()

    # NAAR RESERVERINGSPAGINA
    page.goto("https://www.ervbeatrix.nl/snel-naar/boten-afschrijven?view=reservering")
    page.wait_for_load_state()

    doel_datum = zaterdag_over_een_week()
    dag = doel_datum.day

    page.click(f"text='{dag}'")

    # BOOT
    boot = page.locator(f"td:has-text('{BOOT_NAAM}')").first

    # TIJDSLOT (kolom 15)
    tijdcel = boot.locator("xpath=following-sibling::td[15]")
    tijdcel.click()

    # POPUP
    page.wait_for_selector("#if_bootsrc")
    frame = page.frame_locator("#if_bootsrc")
    frame.locator("#btn_reserve_txt").click()

    # PLOEG SELECTEREN (DONDERSLAG)
    page.locator(PLOEG_ID).check()

    # TIJDEN INVULLEN
    page.fill("input[name='afstijdvan']", STARTTIJD)
    page.fill("input[name='afstijdtot']", EINDTIJD)

    # OPSLAAN
    page.click("#btn_saveafs_txt")

    print(f"✔ Reservering voltooid voor {BOOT_NAAM} op {doel_datum.strftime('%Y-%m-%d')}")
    browser.close()