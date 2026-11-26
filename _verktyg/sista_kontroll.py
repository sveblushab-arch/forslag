#!/usr/bin/env python3
"""Sista kontroll före utskick (automation.md DEL B steg 2).

Användning: python3 _verktyg/sista_kontroll.py <slug> [<slug> ...] [--mejl 1|2|3|lank]
(variant B = förstamejl utan länk; --mejl lank = svaret med länken som inkorgen skickar)

Kontrollerar per slug: mejlfilen finns, rätt mottagare (Till: = data.json mejl/epost
om den finns), företagsnamnet i ämne och text, exakt en länk och att den är
/forslag/<slug>/#forslag (förstamejl), inga hakparenteser/platshållare, sidan
<slug>/index.html finns och är byggd med Signatur (class="bento"), mottagaren inte
på spärrlistan i spärrlista.txt (om den finns) och att bolagsformen inte är enskild firma.
Skriver OK/STOPP per slug och ett JSON-block (to, subject, body) för OK-mejl.
Gmail-kontrollerna (tidigare mejl, avsändarnamn, taket) görs fortfarande i Gmail.
kontroll.py måste köras separat (kräver webbläsare).
"""
import json, re, sys, pathlib

ROT = pathlib.Path(__file__).resolve().parent.parent


def kontrollera(slug, nr):
    fel = []
    mapp = ROT / "_foretag" / slug
    fil = mapp / f"mejl{nr}.txt"  # nr = 1, 2, 3 eller "_lank"
    if not fil.exists():
        return [f"{fil.name} saknas"], None
    rader = fil.read_text(encoding="utf-8").split("\n")
    if not (rader[0].startswith("Till: ") and rader[1].startswith("Ämne: ")):
        return ["huvudet Till:/Ämne: saknas"], None
    till = rader[0][6:].strip()
    amne = rader[1][6:].strip()
    body = "\n".join(rader[3:]).strip() + "\n"
    data = {}
    if (mapp / "data.json").exists():
        data = json.loads((mapp / "data.json").read_text(encoding="utf-8"))
    namn = data.get("namn")
    if str(data.get("kanal", "")).lower() == "besok" or str(data.get("bolagsform", "")).upper() in ("EF", "ENSKILD FIRMA"):
        fel.append("enskild firma/besöksläge – får inte mejlas")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", till):
        fel.append(f"ogiltig mottagare: {till}")
    if namn and nr == 1 and namn not in body:
        fel.append(f"företagsnamnet '{namn}' saknas i texten")
    lankar = re.findall(r"https?://\S+", body)
    ratt = f"https://forslag.sveblush.shop/{slug}/#forslag"
    utan_lank = nr == 1 and (data.get("mejl") or {}).get("variant") == "B" and (data.get("mejl") or {}).get("test") == "lank-2"  # test 2: förstamejl utan länk
    if utan_lank and lankar:
        fel.append(f"variant B ska inte ha någon länk i förstamejlet: {lankar}")
    elif (nr == 1 and not utan_lank) or nr == "_lank":
        gammal = f"https://sveblushab-arch.github.io/forslag/{slug}/#forslag"  # byggt före 25 nov 08:20 – skickas vidare automatiskt
        if lankar not in ([ratt], [gammal]):
            fel.append(f"länkar {lankar} – ska vara exakt [{ratt}]")
    if nr == 1:
        text_utan = re.sub(r"https?://\S+", "", body.split("Varma hälsningar")[0])
        dom = re.search(r"\b[\w-]+\.(?:se|com|nu|net|org|io)\b", text_utan, re.I)
        if dom:
            fel.append(f"webbadress i mejltexten ({dom.group(0)}) blir en extra länk – skriv om (t.ex. 'på Kundernas sida')")
    if nr == 1:
        # Domänkoll (26 nov 13:23): bygg.py kräver den bara för nya byggen – leads byggda före regeln
        # stod i kön utan. Förstamejlet går bara om <namn>.se är ledig eller visad parkerad.
        dk = data.get("domankoll") or {}
        if not dk.get("namnDoman") or dk.get("status") not in ("ledig", "parkerad") or not dk.get("bevis"):
            fel.append("domankoll saknas/ej godkänd i data.json – kolla <namn>.se (Shopify-koll ledig, eller öppnad och parkerad) innan förstamejlet")
    if re.search(r"[\[\]{}]|XXX|TODO|<[a-z]", body + amne):
        fel.append("hakparenteser eller platshållare kvar")
    sida = ROT / slug / "index.html"
    if not sida.exists():
        fel.append("sidan saknas i repot")
    elif 'class="bento' not in sida.read_text(encoding="utf-8"):
        fel.append("sidan är inte byggd med Signatur (class=\"bento\" saknas)")
    sparr = ROT / "_verktyg" / "sparrlista.txt"
    if sparr.exists() and till.lower() in sparr.read_text(encoding="utf-8").lower():
        fel.append("mottagaren står på spärrlistan")
    return fel, {"slug": slug, "to": till, "subject": amne, "body": body}


def main():
    args = sys.argv[1:]
    nr = 1
    if "--mejl" in args:
        i = args.index("--mejl"); nr = args[i + 1]; nr = "_lank" if nr in ("lank", "_lank") else int(nr); del args[i:i + 2]
    if not args:
        print(__doc__); sys.exit(2)
    ok, alla_ok = [], True
    for slug in args:
        fel, mejl = kontrollera(slug, nr)
        if fel:
            alla_ok = False
            print(f"STOPP {slug}: " + "; ".join(fel))
        else:
            print(f"OK    {slug} → {mejl['to']}")
            ok.append(mejl)
    print(json.dumps(ok, ensure_ascii=False, indent=1))
    sys.exit(0 if alla_ok else 1)


if __name__ == "__main__":
    main()
