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
- **Uttömda källor (lärdom 2026-11-27):** fyra agenter (ca 145 sökningar, ca 120 kandidater) gav 0 leads. Lägg inga sökningar på: MECA/MekoPartner i Norrland, Värmland, Östergötland, Blekinge, Gotland, Södermanland (nästan alla har egen domän, < 10 omdömen eller är redan använda); Reco/Kundernas för hantverk och städ (nästan alla har egen sida); Bokadirekt-profiler för e-post (visas bara som ikon – e-post finns bara i tjänstetexter). Fristående verkstäder i större orter (Umeå, Sundsvall, Östersund) har nästan alltid egen sida. Prova i stället först: kön i `_verktyg/kandidater.md` ("Nästan klara 27 nov"), jobbsafari-listor per yrke/län (hämtas utan sökning, ca var tionde annons har e-post), Skåne/Halland/Västra Götaland/Mälardalen. I schemalagda körningar besvaras inga WebFetch-behörighetsfrågor → profilsidor och upptagna domäner som inte stått ordagrant i en sökträff går inte att öppna; välj kandidater vars domänkoll blir "ledig" i Shopify-kollen.
- **Betyget först** (lärdom 2026-11-26): Google-betyget är flaskhalsen – en verkstad utan kundernas.se-sida går inte att verifiera från molnet. Sök därför `MECA Bilservice <län/ort>` med `allowed_domains: ["kundernas.se"]` (titeln visar ofta snitt + antal), välj ≥4,0/≥10 utan egen webbplats, och hämta sedan MECA-sidan via en sökträff med `allowed_domains: ["meca.se"]` för e-post. Kolla orten mot senaste 14 dagarna FÖRST. Kandidatkön `_verktyg/kandidater.md` har kvar de som redan har betyg (avsnittet "Nästa körning – betyg finns").
- Sökbudgeten (200) delas av alla agenter i HELA körningen – en andra omgång agenter efter ca 190 sökningar får 0. Fördela: ca 6 agenter × 25 sökningar, och spara ca 20 till huvudpasset (domänkoll, stickprov).
- Sökbudget (lärdom 2026-11-24): WebSearch har 200 sökningar per körning, delat av alla agenter. Börja med MECA:s översiktslista https://www.meca.se/hitta-verkstad – den visar e-post för alla MECA-verkstäder (gmail/hotmail/telia-adress = oftast ingen egen sida) – och sålla där innan du söker. Max 2 parallella agenter.
- Google Maps och Pages-adressen går inte att hämta från molnmiljön – kontrollera publicering med GitHub-connectorn (filer + Actions "pages build and deployment").


## Sista kontroll före utskick (sedan 24 nov)
`python3 _verktyg/sista_kontroll.py <slug> … [--mejl 2|3]` kontrollerar mottagare, företagsnamn, exakt en rätt länk, platshållare, Signatur (`class="bento`), enskild firma och `_verktyg/sparrlista.txt`, och skriver ut to/subject/body som JSON för send_message. Gmail-kontrollerna (tidigare mejl, avsändarnamn, taket) och kontroll.py körs fortfarande separat. Nytt nej → lägg adressen i sparrlista.txt.
