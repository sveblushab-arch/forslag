# Förslag – SveBlush hemsidebyrå

Förhandsvisningar av hemsidor till företag. Varje mapp `<slug>/` är en publicerad sida (GitHub Pages, noindex).

## Produktionslinje (för automationen)
1. `_foretag/<slug>/data.json` – all fakta om företaget (följ schemat i `_foretag/wahras-salong/data.json`).
2. `python3 _verktyg/bygg.py <slug>` – bygger `<slug>/index.html` från `_mall/template.html` och tre mejl i `_foretag/<slug>/`.
3. `python3 _verktyg/kontroll.py <slug>` – måste säga GODKÄND innan något publiceras eller mejlas.
4. Teman per bransch: `salong`, `verkstad`, `hantverk`, `stad`, `mat`, `butik` (`_verktyg/teman.py`).
5. Säljarens uppgifter och pris: `_verktyg/saljare.json`.

Mappar som börjar med `_` publiceras inte av GitHub Pages.

## Snabbaste vägen till nya leads (lärdom 2026-11-23)
- Börja alltid med `git fetch && git checkout -B main origin/main` och jämför `git log -1` med senaste commit i status.md – en inaktuell origin-ref gav 23 nov gammal kod (utan variant B och "exkl. moms").
- Verkstäder: MekoPartner (mekopartner.se/hitta-verkstad/<ort>/<firma>/) och MECA (meca.se/hitta-verkstad/<ort>/<firma>) visar e-post, telefon, öppettider och tjänster per verkstad. Google-betyg och antal: kundernas.se/<namn> eller kundernas.se/bilverkstad/<ort>, dackplatsen.se/<ort>/.
- Salonger m.fl.: offentlig e-post finns sällan på hitta.se – sök arbetsgivarens aktuella platsannonser via JobTech: `https://jobsearch.api.jobtechdev.se/search?q=<bolagsnamn>&limit=20` (arbetsgivare, arbetsplatsadress och ansöknings-e-post). Priser, tider och betyg: Bokadirekt-profilen.
- Domän upptagen (Shopify-koll) → webbsök domänen; ingen sida → föreslå variant med ort (t.ex. kamochsaxvallentuna.se).
- Sökbudget (lärdom 2026-11-24): WebSearch har 200 sökningar per körning, delat av alla agenter. Börja med MECA:s översiktslista https://www.meca.se/hitta-verkstad – den visar e-post för alla MECA-verkstäder (gmail/hotmail/telia-adress = oftast ingen egen sida) – och sålla där innan du söker. Max 2 parallella agenter.
- Google Maps och Pages-adressen går inte att hämta från molnmiljön – kontrollera publicering med GitHub-connectorn (filer + Actions "pages build and deployment").
