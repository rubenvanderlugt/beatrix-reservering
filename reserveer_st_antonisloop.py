from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta, timezone
import os
import time

# LOGIN UIT GITHUB SECRETS
USERNAME = os.getenv("BEATRIX_USER")
PASSWORD = os.getenv("BEATRIX_PASS")

BOOT_NAAM = "St. Antonisloop"
PLOEG_ID = "#cbxg_ploeg_p120"  # Donderslag
STARTTIJD = "10:00"
EINDTIJD = "11:30"

def aankomende_geplande_dag():
    nl_now = datetime.now(timezone.utc) + timedelta(hours=1) # NL wintertijd
    dagen_tot_doel = (7 - nl_now.weekday()) % 7 # nummer is hoeveel dagen vooruit (in dit geval 7 dagen vooruit)
    if dagen_tot_doel == 0:
        dagen_tot_doel = 7
    return nl_now + timedelta(days=dagen_tot_doel)

def wacht_tot_middernacht():
    """Wacht tot Nederlandse tijd exact 00:00:00."""
    # print("⏳ Wachten tot NL 00:00:00...")
    while True:
        nl_now = datetime.now(timezone.utc) + timedelta(hours=1)
        if nl_now.strftime("%H:%M:%S") == "17:46:00":
            print("🎉 Het is 00:00:00 NL — starten!")
            return
        time.sleep(0.2)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # 0. Wacht to X tijd
    wacht_tot_middernacht()

    # 1. LOGIN
    page.goto("https://www.ervbeatrix.nl/component/users/login?Itemid=101")
    page.fill("input[name='username']", USERNAME)
    page.fill("input[name='password']", PASSWORD)
    page.click("button[type='submit']")
    page.wait_for_load_state()

    # 2. BOOTEN AFSCHRIJVEN PAGE
    page.goto("https://www.ervbeatrix.nl/snel-naar/boten-afschrijven?view=reservering")
    page.wait_for_load_state()

    # 3. DATUM = geplande doel-datum
    doel = aankomende_geplande_dag()
    formatted_date = doel.strftime("%Y-%m-%d")

    # 4. Klik EXACT juiste kalenderdag via complete datum in onclick
    page.locator(f'td[onclick*="{formatted_date}"]').click()

    # 5. ZOEK BOOT IN TABEL
    boot = page.locator(f"td:has-text('{BOOT_NAAM}')").first

    # 6. ZOEK EERSTE LEGE TIJDSLOT
    # tijdcel = boot.locator("xpath=following-sibling::td[15]")     % alternatief KLIK TIJDSLOT (kolom 15 = ver rechts)
    # tijdcel.click()                                               % alternatief
    alle_cellen = boot.locator("xpath=following-sibling::td")
    count = alle_cellen.count()
    gekozen = False

    for i in range(count):
        cel = alle_cellen.nth(i)
        title = cel.get_attribute("title")
        text = cel.inner_text().strip()

        if not title and text == "":
            cel.click()
          # print(f"✔ Lege tijdslotcel gebruikt: index {i}")
            gekozen = True
            break

    if not gekozen:
        raise Exception("❌ Geen lege tijdslotcel gevonden!")

    # 7. --- POPUP IN IFRAME ---
    page.wait_for_selector("#if_bootsrc")
    frame = page.frame_locator("#if_bootsrc")

    # 8. KLIK OP 'RESERVEREN' BINNEN IFRAME
    frame.locator("#btn_reserve_txt").click()

    # 9. VELDEN START / EINDTIJD INVULLEN (JUISTE SELECTORS!)
    page.locator("#cbxg_ploeg_p120").check()
    page.fill("input[name='afstijdvan']", STARTTIJD)
    page.fill("input[name='afstijdtot']", EINDTIJD)

    # 10. BEWAREN / VASTLEGGEN KNOP
    page.click("#btn_saveafs_txt")

    print(f"Succes! Reservering uitgevoerd voor {BOOT_NAAM} op {formatted_date}")
    browser.close()
