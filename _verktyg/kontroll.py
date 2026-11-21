#!/usr/bin/env python3
"""Kvalitetskontroll av en förhandsvisning innan den publiceras och mejlas.

Användning:  python3 _verktyg/kontroll.py <slug> [<slug> ...]
Kräver:      pip install playwright --break-system-packages && python3 -m playwright install chromium
Sparar:      _foretag/<slug>/dator.png och mobil.png
Avslutar med kod 1 om något fall faller.
"""
import sys, json, pathlib, re
from playwright.sync_api import sync_playwright

ROT = pathlib.Path(__file__).resolve().parent.parent


def kolla(pw, slug):
    fel = []
    d = json.loads((ROT / "_foretag" / slug / "data.json").read_text())
    html = (ROT / slug / "index.html").read_text()
    m1 = (ROT / "_foretag" / slug / "mejl1.txt").read_text()
    if 'name="robots" content="noindex' not in html: fel.append("noindex saknas")
    if "Förhandsvisning" not in html: fel.append("bannern saknas")
    if "{{" in html: fel.append("mallfält kvar")
    if f"/forslag/{slug}/#forslag" not in m1: fel.append("fel länk i mejlet")
    if re.search(r"\[[^\]]*\]", m1): fel.append("hakparentes i mejlet")
    if d["telefon"].replace(" ", "")[:6] not in html.replace(" ", ""): fel.append("telefonnumret syns inte")
    b = pw.chromium.launch()
    for w, h, namn in [(1366, 900, "dator"), (390, 844, "mobil")]:
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1 if w > 500 else 2)
        js = []
        pg.on("pageerror", lambda e: js.append(str(e)))
        pg.goto((ROT / slug / "index.html").as_uri()); pg.wait_for_timeout(900)
        if js: fel.append(f"skriptfel ({namn}): {js[0][:80]}")
        if pg.evaluate("document.documentElement.scrollWidth") > w + 1: fel.append(f"sidledsscroll på {namn}")
        if not pg.evaluate("document.querySelector('h1').textContent.trim().length>5"): fel.append("rubrik saknas")
        tomma = pg.evaluate("[...document.querySelectorAll('a.btn')].filter(a=>!a.getAttribute('href')||a.getAttribute('href')==='#').map(a=>a.textContent.trim()).filter(t=>t&&!['Jag vill ha sidan','Hellre prata först'].includes(t))")
        if tomma: fel.append(f"knappar utan länk: {tomma}")
        pg.evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('in'))")
        pg.screenshot(path=str(ROT / "_foretag" / slug / f"{namn}.png"), full_page=(namn == "dator"))
        pg.goto("about:blank"); pg.goto((ROT / slug / "index.html").as_uri() + "#forslag"); pg.wait_for_timeout(500)
        if not pg.evaluate("document.getElementById('sheet').classList.contains('open')"): fel.append(f"säljpanelen öppnas inte ({namn})")
        pg.close()
    b.close()
    return fel


if __name__ == "__main__":
    allt_ok = True
    with sync_playwright() as pw:
        for slug in sys.argv[1:]:
            f = kolla(pw, slug)
            print(("GODKÄND " if not f else "UNDERKÄND ") + slug + ("" if not f else ": " + "; ".join(f)))
            allt_ok &= not f
    sys.exit(0 if allt_ok else 1)
