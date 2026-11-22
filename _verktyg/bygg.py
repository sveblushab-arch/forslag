#!/usr/bin/env python3
"""Bygger en förhandsvisning och tre säljmejl från _foretag/<slug>/data.json.

Användning:  python3 _verktyg/bygg.py <slug>
Skriver:     <slug>/index.html  (publiceras på GitHub Pages)
             _foretag/<slug>/mejl1.txt, mejl2.txt, mejl3.txt  (publiceras inte – mappar som börjar med _ ignoreras av Pages)
"""
import json, sys, pathlib, re, datetime
from teman import TEMAN, illustration

ROT = pathlib.Path(__file__).resolve().parent.parent
BAS_URL = "https://sveblushab-arch.github.io/forslag"
KRAV = ["slug", "namn", "bolag", "bolagsform", "logo", "tema", "adress", "postnr", "stad", "telefon", "telefonIntl",
        "betyg", "oppettider", "tjanster", "varfor", "faq", "text", "pitch", "seo", "schemaTyp", "mejl"]
TEXTKRAV = ["rubrik", "ingress", "tjanstRubrik", "prisNot", "varforKicker", "varforRubrik", "kontaktRubrik", "kontaktText",
            "pitchRubrik", "pitchIngress", "enhet", "enhetPlural", "pratText"]
# Fält som aldrig får hamna i den publika sidan (mottagare, källor, interna anteckningar, id-nummer)
PRIVAT = {"mejl", "besok", "kallor", "status", "orgnr", "personnr", "kanal", "epost", "notering", "ab"}
IDNUMMER = re.compile(r"\b(?:\d{2})?\d{6}[-+]?\d{4}\b")
MEJLKRAV = ["till", "amne", "hej", "iakttagelse", "problem", "fordelar", "prisJamforelse", "psDatum", "kontaktVal"]


def fel(m):
    sys.exit(f"STOPP: {m}")


def kr(n):
    return f"{n:,}".replace(",", " ") + " kr"


def kontrollera(d):
    besok = d.get("kanal") == "besok"
    for k in KRAV:
        if besok and k == "mejl":
            continue
        if k not in d or d[k] in (None, "", [], {}):
            fel(f"fält saknas: {k}")
    for k in TEXTKRAV:
        if not d["text"].get(k):
            fel(f"text.{k} saknas")
    for k in ([] if besok else MEJLKRAV):
        if not d["mejl"].get(k):
            fel(f"mejl.{k} saknas")
    if besok:
        for k in ("hej", "iakttagelse", "problem", "fordelar", "prisJamforelse", "psDatum"):
            if not d.get("besok", {}).get(k):
                fel(f"besok.{k} saknas")
        if d.get("mejl"):
            fel("kanal besok får inte ha mejl – enskild firma mejlas aldrig")
    elif d["bolagsform"] not in ("AB", "HB", "KB"):
        fel("bolagsform måste vara AB, HB eller KB – enskild firma mejlas inte (använd kanal: besok)")
    if d["tema"] not in TEMAN:
        fel(f"okänt tema {d['tema']} – välj bland {list(TEMAN)}")
    if len(d["oppettider"]) != 7:
        fel("oppettider måste ha 7 rader (måndag–söndag)")
    if len(d["varfor"]) != 3 or len(d["pitch"]["idag"]) != 4 or len(d["pitch"]["medSida"]) != 4:
        fel("varfor ska ha 3 kort, pitch.idag och pitch.medSida 4 punkter var")
    if len((d.get("besok") if besok else d["mejl"])["fordelar"]) != 4:
        fel("mejl.fordelar ska ha 4 punkter")
    if not re.fullmatch(r"\+46\d{7,10}", d["telefonIntl"]):
        fel("telefonIntl ska vara +46…")
    blob = json.dumps(d, ensure_ascii=False)
    if "orgnr" in d or "personnr" in d or IDNUMMER.search(re.sub(r"\+46\d+", "", blob)):
        fel("organisations-/personnummer får aldrig skrivas i data.json – ta bort det")
    if d.get("mejl", {}).get("variant") not in (None, "A", "B"):
        fel("mejl.variant ska vara A eller B")
    if re.search(r"\[[A-ZÅÄÖ ]+\]|XXX|TODO|lorem", blob, re.I):
        fel("platshållare kvar i data.json")


def bygg_sida(d, s):
    t = TEMAN[d["tema"]]
    adr = f'{d["adress"]}, {d["postnr"]} {d["stad"]}'
    schema = {"@context": "https://schema.org", "@type": d["schemaTyp"], "name": d["namn"], "telephone": d["telefonIntl"],
              "address": {"@type": "PostalAddress", "streetAddress": d["adress"], "postalCode": d["postnr"],
                          "addressLocality": d["stad"], "addressCountry": "SE"}}
    if d.get("lat"):
        schema["geo"] = {"@type": "GeoCoordinates", "latitude": d["lat"], "longitude": d["lng"]}
    same = [u for u in (d.get("instagram"), d.get("facebook"), d.get("bokning")) if u]
    if same:
        schema["sameAs"] = same
    html = (ROT / "_mall" / "template.html").read_text()
    rep = {"{{SEO_TITLE}}": d["seo"]["title"], "{{SEO_DESC}}": d["seo"]["description"], "{{ACCENT}}": t["acc"],
           "{{ACCENT_D}}": t["acc_d"], "{{CLAY}}": t["clay"], "{{CLAY_D}}": t["clay_d"], "{{CLAY2}}": t["clay2"],
           "{{FONT_URL}}": t["font"], "{{FONT_CSS}}": t["font_css"], "{{FONT_W}}": t["w"],
           "{{SCHEMA}}": json.dumps(schema, ensure_ascii=False), "{{ILLUSTRATION}}": illustration(d["tema"]),
           "{{DATA}}": json.dumps({k: v for k, v in d.items() if k not in PRIVAT}, ensure_ascii=False).replace("</", "<\\/"),
           "{{SALJARE}}": json.dumps(s, ensure_ascii=False)}
    for k, v in rep.items():
        html = html.replace(k, v.replace('"', "&quot;") if k in ("{{SEO_TITLE}}", "{{SEO_DESC}}") else v)
    nav = d["text"].get("navTjanster")
    if nav:
        html = html.replace("Tjänster &amp; priser", nav.replace("&", "&amp;"))
    if "{{" in html:
        fel("mallfält kvar: " + re.search(r"\{\{\w+\}\}", html).group())
    out = ROT / d["slug"] / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html)
    return out


def bygg_mejl(d, s):
    m, lank = d["mejl"], f'{BAS_URL}/{d["slug"]}/#forslag'
    ford = "\n".join(f"• {a}. {b}" for a, b in m["fordelar"])
    sig = f'Varma hälsningar\n{s["namn"]}\n{s["foretag"]} · {s.get("webb", "")}\n{s["tel"]} · {s["mejl"]}'.replace(" · \n", "\n")
    m1 = f'''Hej {m["hej"]},

Jag heter {s["namn"]} och bygger hemsidor åt lokala företag. {m["iakttagelse"]}

{m["problem"]}

Därför har jag byggt en hemsida åt er. Den är klar, och ni kan titta på den här:
{lank}

Varför den gör skillnad för {m.get("ert", "er")}:
{ford}

Så enkelt får ni den:
1. Svara "ja" på det här mejlet.
2. Säg vad ni vill ändra – bilder, färger, text. Jag fixar det.
3. Inom 7 dagar är sidan live på er egen adress. Ni betalar först när ni är nöjda.

Pris: {kr(s["engang"])} en gång – {m["prisJamforelse"]} – och {kr(s["manad"])} i månaden för domän, drift och små ändringar. Alla priser exkl. moms.

Vill ni hellre prata först? Jag ringer gärna, eller {m["kontaktVal"]} när det passar er. Tio minuter räcker. Svara med en tid, eller ring mig på {s["tel"]}.

{sig}

P.S. Sidan ligger uppe till {m["psDatum"]}. Vill ni inte få fler mejl från mig räcker det att svara "nej tack".
'''
    if m.get("variant") == "B":
        # A/B-test från v.48 (Elliots ja 22 nov): kort förstamejl, ca 100–150 ord. Samma ämne, länk, pris och löften.
        m1 = f'''Hej {m["hej"]},

Jag heter {s["namn"]} och bygger hemsidor åt lokala företag. {m["iakttagelse"]}

{m["problem"]}

Därför har jag byggt en hemsida åt er. Den är klar:
{lank}

Vill ni ha den är den live på er egen adress inom 7 dagar. {kr(s["engang"])} en gång och {kr(s["manad"])} i månaden (exkl. moms) – och ni betalar först när ni är nöjda.

Är det intressant? Svara bara "ja", eller ring mig på {s["tel"]}.

{sig}

P.S. Sidan ligger uppe till {m["psDatum"]}. Vill ni inte få fler mejl från mig räcker det att svara "nej tack".
'''
    m2 = f'''Hej igen {m["hej"]},

Jag vet att det är mycket att göra på dagarna, så jag gör det kort.

Sidan jag byggt åt er ligger kvar här: {lank}

Två sätt att gå vidare, välj det som passar bäst:
1. Svara "ja, testa" – så lägger jag in era egna bilder, utan kostnad, innan ni bestämmer er.
2. Svara med en tid – så ringer jag er eller {m["kontaktVal"]} i tio minuter.

Varma hälsningar
{s["namn"]} · {s["tel"]}
'''
    m3 = f'''Hej {m["hej"]},

Det här är mitt sista mejl om sidan. Förhandsvisningen tas ned den {m["psDatum"]}.

Vill ni ha den räcker ett "ja", så är den live på er egen adress inom en vecka. Vill ni prata först är ni alltid välkomna att ringa mig på {s["tel"]} – även längre fram.

Oavsett vad ni väljer: lycka till.

{sig}
'''
    ut = ROT / "_foretag" / d["slug"]
    amne = m["amne"]
    (ut / "mejl1.txt").write_text(f"Till: {m['till']}\nÄmne: {amne}\n\n{m1}")
    (ut / "mejl2.txt").write_text(f"Till: {m['till']}\nÄmne: Sv: {amne}\n\n{m2}")
    (ut / "mejl3.txt").write_text(f"Till: {m['till']}\nÄmne: Sv: {amne}\n\n{m3}")
    ord_ = len(m1.split())
    lo, hi = (80, 170) if m.get("variant") == "B" else (190, 320)
    if not lo <= ord_ <= hi:
        fel(f"mejl 1 har {ord_} ord – ska vara {lo}–{hi} (variant {m.get('variant', 'A')})")
    if re.search(r"\[|\]|XXX", m1):
        fel("platshållare kvar i mejl 1")
    if d["namn"].split()[0] not in m1:
        fel("företagsnamnet syns inte i mejlet")
    return ord_


def bygg_besok(d, s):
    """Ring-/besöksmanus för enskild firma (marknadsföringslagen: inga mejl utan samtycke)."""
    b, lank = d["besok"], f'{BAS_URL}/{d["slug"]}/#forslag'
    ford = "\n".join(f"  • {a} – {c}" for a, c in b["fordelar"])
    txt = f'''BESÖK/RING – {d["namn"]}, {d["adress"]}, {d["stad"]} · {d["telefon"]}
Kanal: personligt besök eller samtal (enskild firma – inga säljmejl).
Visa sidan på mobilen: {lank}

1. Hälsa: "Hej, jag heter {s["namn"]} och bygger hemsidor åt lokala företag. Är det du som är ansvarig här?" (fråga efter {b["hej"]})
2. Beröm (konkret): {b["iakttagelse"]}
3. Problemet (ärligt): {b["problem"]}
4. Visa sidan: "Jag har redan byggt en åt er – titta." Låt dem scrolla själva.
5. Fyra vinster:
{ford}
6. Pris: {kr(s["engang"])} en gång – {b["prisJamforelse"]} – och {kr(s["manad"])}/mån för domän, drift och små ändringar. Exkl. moms – säg det om de frågar.
7. Tre steg: säg ja → säg vad ni vill ändra → live inom 7 dagar på egen adress{(" (" + d["pitch"]["doman"] + ")") if d["pitch"].get("doman") else ""}.
8. Fråga: "Vill ni att jag kör igång?" Nej → "Helt okej. Sidan ligger uppe till {b["psDatum"]} om ni ändrar er." Lämna nummer: {s["tel"]}.

Får jag mejla dig sidan? Bara om de säger ja – anteckna samtycket (datum, namn) i Kontoret.
'''
    out = ROT / "_foretag" / d["slug"] / "besok.txt"
    out.write_text(txt)
    return len(txt.split())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        fel("ange slug")
    slug = sys.argv[1]
    d = json.loads((ROT / "_foretag" / slug / "data.json").read_text())
    s = json.loads((ROT / "_verktyg" / "saljare.json").read_text())
    if d["slug"] != slug:
        fel("slug i data.json stämmer inte med mappen")
    kontrollera(d)
    sida = bygg_sida(d, s)
    if d.get("kanal") == "besok":
        n = bygg_besok(d, s)
        print(f"OK {slug}: {sida.relative_to(ROT)} + besöksmanus ({n} ord) · {BAS_URL}/{slug}/#forslag")
    else:
        n = bygg_mejl(d, s)
        print(f"OK {slug}: {sida.relative_to(ROT)} + 3 mejl (mejl 1: {n} ord) · {BAS_URL}/{slug}/#forslag")
