
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import os
import time

# LOGIN UIT GITHUB SECRETS
USERNAME = os.getenv("BEATRIX_USER")
PASSWORD = os.getenv("BEATRIX_PASS")

BOOT_NAAM = "St. Antonisloop"
PLOEG_ID = "#cbxg_ploeg_p120"  # Donderslag
STARTTIJD = "09:30"
EINDTIJD = "11:00"

def dinsdag_over_een_week():
    """Return de dinsdag van volgende week (NL tijd)."""
    nl_now = datetime.utcnow() + timedelta(hours=1)  # wintertijd standaard voor 00:00 runs
    dagen = (1 - nl_now.weekday()) % 7  # dinsdag = 1
    if dagen == 0:
        dagen = 7  # vandaag is dinsdag -> volgende week
    return nl_now + timedelta(days=dagen)

def wacht_tot_middernacht():
    """Wacht tot Nederlandse tijd exact 00:00:01."""
    print("⏳ Wachten tot NL 00:00:01...")
    while True:
        nl_now = datetime.utcnow() + timedelta(hours=1)
        if nl_now.strftime("%H:%M:%S") == "00:00:01":
            print("🎉 Het is 00:00:01 NL — starten!")
            return
        time.sleep(0.2)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # 1. WACHT OP EXACT MIDDERNACHT
    wacht_tot_middernacht()

    # 2. LOGIN
    page.goto("https://www.ervbeatrix.nl/component/users/login?Itemid=101")
    page.fill("input[name='username']", USERNAME)
    page.fill("input[name='password']", PASSWORD)
    page.click("button[type='submit']")
    page.wait_for_load_state()

    # 3. NAAR BOOTEN AFSCHRIJVEN
    page.goto("https://www.ervbeatrix.nl/snel-naar/boten-afschrijven?view=reservering")
    page.wait_for_load_state()

    # 4. SELECTEER VOLGENDE-WEEK-DINSDAG
    doel = dinsdag_over_een_week()
    dag = doel.day
    page.click(f"text='{dag}'")

    # 5. VIND BOOT
    boot = page.locator(f"td:has-text('{BOOT_NAAM}')").first

    # 6. ZOEK EERSTE LEGE TIJDSLOT
    alle_cellen = boot.locator("xpath=following-sibling::td")
    count = alle_cellen.count()
    gekozen = False

    for i in range(count):
        cel = alle_cellen.nth(i)
        title = cel.get_attribute("title")
        text = cel.inner_text().strip()

        if not title and text == "":
            cel.click()
            print(f"✔ Lege tijdslotcel gebruikt: index {i}")
            gekozen = True
            break

    if not gekozen:
        raise Exception("❌ Geen lege tijdslotcel gevonden!")

    # 7. POPUP / IFRAME
    page.wait_for_selector("#if_bootsrc")
    frame = page.frame_locator("#if_bootsrc")

    # 8. KLIK 'RESERVEREN'
    frame.locator("#btn_reserve_txt").click()

    # 9. SELECTEER PLOEG DONDERSLAG
    page.locator(PLOEG_ID).check()

    # 10. TIJDEN INVULLEN
    page.fill("input[name='afstijdvan']", STARTTIJD)
    page.fill("input[name='afstijdtot']", EINDTIJD)

    # 11. VASTLEGGEN
    page.click("#btn_saveafs_txt")

    print(f"✔ Reservering voltooid voor {BOOT_NAAM} op {doel.strftime('%Y-%m-%d')}")
    browser.close()
