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
    mf = ROT / "_foretag" / slug / "mejl1.txt"
    m1 = mf.read_text() if mf.exists() else (ROT / "_foretag" / slug / "besok.txt").read_text()
    if 'name="robots" content="noindex' not in html: fel.append("noindex saknas")
    if "Förhandsvisning" not in html: fel.append("bannern saknas")
    if "{{" in html: fel.append("mallfält kvar")
    if re.search(r"\b(?:\d{2})?\d{6}[-+]?\d{4}\b", re.sub(r"\+46\d+", "", html)): fel.append("id-nummer (org.nr/personnr) i sidan")
    if d.get("mejl", {}).get("till") and d["mejl"]["till"] in html: fel.append("mottagarens adress läcker in i sidan")
    if '"kallor":' in html or '"status": {' in html: fel.append("interna fält läcker in i sidan")
    lank = f"/forslag/{slug}/#forslag"
    mj = d.get("mejl", {})
    if mj.get("variant") == "B" and mj.get("test") == "lank-2":
        # A/B-test 2: variant B ska SAKNA länk i förstamejlet – länken finns i mejl_lank.txt (och i påminnelse 1)
        if "/forslag/" in m1: fel.append("variant B (lank-2) har länk i förstamejlet")
        ml = ROT / "_foretag" / slug / "mejl_lank.txt"
        if not ml.exists() or lank not in ml.read_text(): fel.append("mejl_lank.txt saknar rätt länk")
        if lank not in (ROT / "_foretag" / slug / "mejl2.txt").read_text(): fel.append("påminnelse 1 saknar länken")
    elif lank not in m1: fel.append("fel länk i mejlet/manuset")
    if re.search(r"\[[^\]]*\]", m1): fel.append("hakparentes i mejlet")
    if d["telefon"].replace(" ", "")[:6] not in html.replace(" ", ""): fel.append("telefonnumret syns inte")
    b = pw.chromium.launch()
    for w, h, namn in [(1366, 900, "dator"), (390, 844, "mobil"), (360, 740, "litenmobil")]:
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1 if w > 500 else 2)
        js = []
        pg.on("pageerror", lambda e: js.append(str(e)))
        pg.goto((ROT / slug / "index.html").as_uri()); pg.wait_for_timeout(900)
        if js: fel.append(f"skriptfel ({namn}): {js[0][:80]}")
        if pg.evaluate("document.documentElement.scrollWidth") > w + 1: fel.append(f"sidledsscroll på {namn}")
        if not pg.evaluate("document.querySelector('h1').textContent.trim().length>5"): fel.append("rubrik saknas")
        # Mobil och dator ska se rena ut: inget sticker ut, inget är för litet att trycka på eller läsa.
        pg.evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('in'))"); pg.wait_for_timeout(1200)
        ut = pg.evaluate("""() => { const vw = document.documentElement.clientWidth, bad = [];
          const clipped = el => { for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) { const o = getComputedStyle(p); if (/(hidden|clip|auto|scroll)/.test(o.overflowX)) return true; } return false; };
          for (const el of document.querySelectorAll('body *')) { if (el.closest('#sheet,[aria-hidden=true],.skip')) continue; const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
            if ((r.right > vw + 1 || r.left < -1) && !clipped(el)) bad.push((el.id || el.className || el.tagName).toString().slice(0, 30)); }
          return [...new Set(bad)].slice(0, 5); }""")
        if ut: fel.append(f"utanför skärmen ({namn}): {ut}")
        sma = pg.evaluate("""() => [...document.querySelectorAll('a.btn, button, .dock a, .tab, summary')].filter(e => { if (e.closest('#sheet')) return false; const r = e.getBoundingClientRect(); return r.width && r.height && r.height < 43.5; }).map(e => e.textContent.trim().slice(0, 25)).slice(0, 5)""")
        if namn != "dator" and sma: fel.append(f"för små tryckytor ({namn}): {sma}")
        lit = pg.evaluate("""() => [...document.querySelectorAll('p, li, summary, .item h3, .lead')].filter(e => { if (e.closest('#sheet,.demo,footer,[aria-hidden=true]')) return false; const r = e.getBoundingClientRect(); return r.width && parseFloat(getComputedStyle(e).fontSize) < 13; }).map(e => e.textContent.trim().slice(0, 25)).slice(0, 5)""")
        if lit: fel.append(f"för liten text ({namn}): {lit}")
        if pg.evaluate("(() => { const h = document.querySelector('h1'); return h.scrollWidth > h.clientWidth + 1; })()"): fel.append(f"rubriken får inte plats ({namn})")
        # Lärdom 25 nov: "07.30–16.30" i varför-kortets stora siffra klipptes på dator utan att något annat larmade.
        pg.wait_for_timeout(1500)
        stor = pg.evaluate("[...document.querySelectorAll('.card .big, .bento .big, .stat .big')].filter(e => e.getBoundingClientRect().width && e.scrollWidth > e.clientWidth + 1).map(e => e.textContent.trim()).slice(0, 3)")
        if stor: fel.append(f"stor siffra får inte plats ({namn}): {stor}")
        tomma = pg.evaluate("[...document.querySelectorAll('a.btn')].filter(a=>!a.getAttribute('href')||a.getAttribute('href')==='#').map(a=>a.textContent.trim()).filter(t=>t&&!['Jag vill ha sidan','Hellre prata först'].includes(t))")
        if tomma: fel.append(f"knappar utan länk: {tomma}")
        pg.evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('in'))"); pg.wait_for_timeout(1200)
        if namn != "litenmobil": pg.screenshot(path=str(ROT / "_foretag" / slug / f"{namn}.png"), full_page=(namn == "dator"))
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
