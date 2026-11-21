# Förslag – SveBlush hemsidebyrå

Förhandsvisningar av hemsidor till företag. Varje mapp `<slug>/` är en publicerad sida (GitHub Pages, noindex).

## Produktionslinje (för automationen)
1. `_foretag/<slug>/data.json` – all fakta om företaget (följ schemat i `_foretag/wahras-salong/data.json`).
2. `python3 _verktyg/bygg.py <slug>` – bygger `<slug>/index.html` från `_mall/template.html` och tre mejl i `_foretag/<slug>/`.
3. `python3 _verktyg/kontroll.py <slug>` – måste säga GODKÄND innan något publiceras eller mejlas.
4. Teman per bransch: `salong`, `verkstad`, `hantverk`, `stad`, `mat`, `butik` (`_verktyg/teman.py`).
5. Säljarens uppgifter och pris: `_verktyg/saljare.json`.

Mappar som börjar med `_` publiceras inte av GitHub Pages.
