#!/usr/bin/env python3
"""Bygger en förhandsvisning och tre säljmejl från _foretag/<slug>/data.json.

Användning:  python3 _verktyg/bygg.py <slug>
Skriver:     <slug>/index.html  (publiceras på GitHub Pages)
             _foretag/<slug>/mejl1.txt, mejl2.txt, mejl3.txt  (publiceras inte – mappar som börjar med _ ignoreras av Pages)
"""
import json, sys, pathlib, re, datetime
from teman import TEMAN, illustration

ROT = pathlib.Path(__file__).resolve().parent.parent
BAS_URL = "https://forslag.sveblush.shop"
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
    if d.get("mejl", {}).get("test") not in (None, "lank-2"):
        fel("mejl.test ska vara \"lank-2\" (A/B-test 2 från 25 nov) eller saknas")
    if d.get("mejl", {}).get("variant") not in (None, "A", "B"):
        fel("mejl.variant ska vara A eller B")
    if re.search(r"\[[A-ZÅÄÖ ]+\]|XXX|TODO|lorem", blob, re.I):
        fel("platshållare kvar i data.json")
    # Leadjakt 26 nov: inga webbadresser i mejltexten (Gmail gör dem till länkar → fler länkar, sämre leverans)
    mj = d.get("mejl", {})
    doman = re.compile(r"\b[\w-]+\.(?:se|com|nu|net|org|io)\b", re.I)
    for k in ("hej", "iakttagelse", "problem"):
        if doman.search(str(mj.get(k, ""))):
            msg = f"mejl.{k} innehåller en webbadress ({doman.search(str(mj[k])).group(0)}) – skriv t.ex. 'på Kundernas sida' i stället"
            if (ROT / "_foretag" / d["slug"] / "mejl1.txt").exists():
                print("VARNING (redan byggt/skickat):", msg)
            else:
                fel(msg)


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
    # Förstamejl v2 (24 nov, efter forskning: Gong/Woodpecker/Instantly – under ca 125 ord, ett enda
    # intresse-CTA, max två länkar, källa till adressen enligt GDPR art. 14). Samma text för A och B;
    # från 25 nov testar variant A/B ämnesraden (sätts i data.json av Del A).
    kalla = f' Er adress hittade jag på {m["adressKalla"]}.' if m.get("adressKalla") else ""
    m1 = f'''Hej {m["hej"]},

Jag heter {s["namn"]} och bygger hemsidor åt lokala företag. {m["iakttagelse"]}

{m["problem"]}

Så jag har byggt en hemsida åt er. Den är redan klar:
{lank}

Vill ni ha den är den live på er egen adress inom 7 dagar. {kr(s["engang"])} en gång och {kr(s["manad"])} i månaden, exkl. moms – och ni betalar först när ni är nöjda.

Ska jag göra klart den åt er? Ett "ja" räcker.

{sig}

P.S. Sidan ligger uppe till {m["psDatum"]}.{kalla} Vill ni inte få fler mejl från mig räcker det att svara "nej tack".
'''
    if m.get("variant") == "B" and m.get("test") == "lank-2":
        # A/B-test 2 (från 25 nov, Elliots ja 24 nov): förstamejl UTAN länk – intresse-CTA, länken
        # skickas automatiskt (mejl_lank.txt) av inkorgsuppgiften när de svarar.
        m1 = f'''Hej {m["hej"]},

Jag heter {s["namn"]} och bygger hemsidor åt lokala företag. {m["iakttagelse"]}

{m["problem"]}

Så jag har byggt en hemsida åt er, med era tjänster, öppettider och omdömen. Den är redan klar.

Vill ni ha den är den live på er egen adress inom 7 dagar. {kr(s["engang"])} en gång och {kr(s["manad"])} i månaden, exkl. moms – och ni betalar först när ni är nöjda.

Vill ni se den? Svara bara "ja", så skickar jag länken.

{sig}

P.S. Sidan ligger uppe till {m["psDatum"]}.{kalla} Vill ni inte få fler mejl från mig räcker det att svara "nej tack".
'''
    mlank = f'''Hej {m["hej"]},

Tack! Här är sidan jag har byggt åt {d["namn"]}:
{lank}

Titta gärna på mobilen – det är där de flesta av era kunder kommer att se den. Säg till om något ska ändras, eller svara "ja" om ni vill att jag gör klart den. {kr(s["engang"])} en gång och {kr(s["manad"])} i månaden, exkl. moms – ni betalar först när ni är nöjda.

{sig}
'''
    m2 = f'''Hej igen {m["hej"]},

Jag vet att det är mycket att göra på dagarna, så jag gör det kort.

Sidan jag byggt åt er ligger kvar här: {lank}

Två sätt att gå vidare, välj det som passar bäst:
1. Svara "ja, testa" – så lägger jag in era egna bilder, utan kostnad, innan ni bestämmer er.
2. Svara med en tid – så ringer jag er eller {m["kontaktVal"]} i tio minuter.

Ni behöver inte göra något själva – texter, bilder, domän och Google-uppgifter sköter jag.

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
    (ut / "mejl_lank.txt").write_text(f"Till: {m['till']}\nÄmne: Sv: {amne}\n\n{mlank}")
    ord_ = len(m1.split())
    lo, hi = 70, 175
    if not lo <= ord_ <= hi:
        fel(f"mejl 1 har {ord_} ord – ska vara {lo}–{hi} (sikta på ca 110–130; korta iakttagelse/problem)")
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
