# =====================================================================
#  BUILD.PY – BUDOWANIE STRONY
# ---------------------------------------------------------------------
#  Uruchomienie:
#     python build.py                 → pobiera dane ze związków i buduje stronę
#     python build.py --bez-internetu → buduje z ostatnio pobranych danych
#
#  Wynik: folder "strona/" – gotowy do wgrania na serwer FTP
#  (na GitHubie wgrywa się sam).
#
#  Treści zmieniasz w content.py, wygląd elementów w szablony.py,
#  kolory i układ w zasoby/style.css.
# =====================================================================

import hashlib
import json
import re
import os
import shutil
import sys
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote

FOLDER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, FOLDER)

import content as C          # noqa: E402  (wszystkie treści)
import zrodla                # noqa: E402  (pobieranie ze stron związków)
import szablony as S         # noqa: E402  (klocki HTML)
import poradniki as PR       # noqa: E402  (poradnik dla rodziców – Akademia)
from szablony import e       # noqa: E402

WYJSCIE = os.path.join(FOLDER, "strona")
GLOWNA = "seniorki"          # drużyna pokazywana w belce i na plakacie
DZIS = date.today()
INDEXNOW_KLUCZ = "626555853380b51c3aa9050ff937c69a"   # klucz IndexNow (plik 626555853380b51c3aa9050ff937c69a.txt w katalogu głównym)
OG_ZAPOWIEDZ = None          # obraz podglądu linku z najbliższym meczem (ustawia main(), gdy uda się go zrobić)


# =====================================================================
# 1. PRZYGOTOWANIE DANYCH
# =====================================================================
NASZE_NAZWY = {zrodla.norm(C.KLUB["nazwa"]), zrodla.norm(C.KLUB["nazwa_krotka"])}
for _z in C.ZRODLA_ZWIAZKOWE:
    NASZE_NAZWY |= {zrodla.norm(_z["nazwa_w_terminarzu"]), zrodla.norm(_z["nazwa_w_tabeli"])}


def opis_druzyny(nazwa):
    """Pełna nazwa ze związku → nazwa, skrót i herb do wyświetlenia."""
    if nazwa is None:
        return None
    n = zrodla.norm(nazwa)
    if n in NASZE_NAZWY:
        return {"nazwa": C.KLUB["nazwa"], "krotko": C.KLUB["nazwa_krotka"], "nasza": True,
                "volleybox": C.KLUB.get("volleybox")}
    for r in C.RYWALE.values():
        warianty = {zrodla.norm(x) for x in r.get("nazwy_w_zwiazkach", [])} | {zrodla.norm(r["skrot"])}
        if n in warianty:
            return {"nazwa": nazwa, "krotko": r["skrot"], "rywal": r, "nasza": False,
                    "volleybox": r.get("volleybox")}
    return {"nazwa": nazwa, "krotko": nazwa, "rywal": {}, "nasza": False}


def przygotuj_mecz(m, druzyna):
    """Ujednolica mecz (ze związku albo z content.py) do jednego formatu."""
    if m.get("gosc"):
        gosp, gosc = opis_druzyny(m["gospodarz"]), opis_druzyny(m["gosc"])
    else:  # turniej / wydarzenie bez rywala – pokazujemy nasz herb i nazwę wydarzenia
        gosp, gosc = {"nazwa": m["gospodarz"], "krotko": m["gospodarz"], "nasza": True}, None
    u_siebie = gosp["nasza"]
    wygrana = None
    if m.get("wynik"):
        a, b = (int(x) for x in m["wynik"].split(":"))
        wygrana = (a > b) if u_siebie else (b > a)
    d = date.fromisoformat(m["data"])
    hala = m.get("hala")
    if not hala and u_siebie and druzyna == GLOWNA:
        hala = C.HALA_DOMOWA["nazwa"]
    return {
        **m,
        "druzyna": druzyna,
        "data": d,
        "strony": (gosp, gosc),
        "u_siebie": u_siebie,
        "wygrana": wygrana,
        "hala": hala,
        "liga": C.DRUZYNY.get(druzyna, {}).get("liga") or "",
        "plik_ics": f"{druzyna}-{d.isoformat()}.ics",
    }


def zbierz_mecze(dane_zwiazkowe):
    """Mecze ze związków + uzupełnienia i mecze dopisane w content.MECZE."""
    surowe = {}
    for druzyna, d in dane_zwiazkowe.items():
        for m in d["mecze"]:
            surowe[(druzyna, m["data"])] = dict(m)
    for r in C.MECZE:
        klucz = (r["druzyna"], r["data"])
        if klucz in surowe:      # uzupełnienie meczu ze związku
            surowe[klucz].update({k: v for k, v in r.items() if v is not None})
            if r.get("godzina"):
                surowe[klucz]["godzina_pewna"] = True
        elif r.get("gospodarz"):  # mecz spoza związku
            surowe[klucz] = dict(r)
        else:
            print(f"UWAGA: w MECZE jest uzupełnienie dla {klucz}, ale związek nie ma takiego meczu")
    mecze = [przygotuj_mecz(m, druzyna) for (druzyna, _), m in surowe.items()]
    mecze.sort(key=lambda m: (m["data"], m.get("godzina") or "99:99"))
    return mecze


def przygotuj_herby(bez_internetu):
    """Herby: własny plik z img/herby/ albo logo pobrane raz z VolleyStation."""
    def jeden(klucz, wpis, pole_herbu):
        if S.jest_plik(wpis.get(pole_herbu)) or not wpis.get("herb_volleystation"):
            return
        try:
            if bez_internetu:  # bez internetu bierzemy tylko to, co już pobrane
                sciezka = zrodla.herb_z_volleystation(klucz, None)
            else:
                sciezka = zrodla.herb_z_volleystation(klucz, wpis["herb_volleystation"])
            if sciezka:
                wpis[pole_herbu] = sciezka
        except Exception as blad:
            print(f"  UWAGA: nie pobrano herbu „{klucz}”: {blad} – będzie tarcza z inicjałami")

    jeden("easy-wrap-volley", C.KLUB, "herb")
    for klucz, r in C.RYWALE.items():
        jeden(klucz, r, "herb")


# =====================================================================
# 2. ZAPIS PLIKÓW
# =====================================================================
# Ochrona adresów e-mail przed botami zbierającymi adresy:
# w gotowym HTML nie ma żadnego adresu ani „mailto:” – są zakodowane (odwrócone + base64),
# a prawdziwy adres i link składa dopiero main.js w przeglądarce. Bez JavaScriptu widać
# „kontakt (małpa) volleykobylka.pl”, więc człowiek i tak odczyta adres.
_MAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _koduj_mail(adres):
    import base64
    return base64.b64encode(adres[::-1].encode("utf-8")).decode("ascii")


def ukryj_maile(html):
    def link(m):
        adres, zapytanie = m.group(1), m.group(2) or ""
        q = f' data-mail-q="{zapytanie[1:]}"' if zapytanie else ""
        return f'href="#" data-mail="{_koduj_mail(adres)}"{q} rel="nofollow"'
    html = re.sub(r'href="mailto:([^"?]+)(\?[^"]*)?"', link, html)

    def tekst(m):
        a = m.group(0)
        nazwa, domena = a.split("@", 1)
        return (f'<span class="mail" data-mail="{_koduj_mail(a)}">{nazwa} (małpa) {domena}</span>')
    # tylko w tekście między znacznikami (nie w atrybutach, skryptach ani stylach)
    czesci = re.split(r"(<script\b.*?</script>|<style\b.*?</style>|<[^>]+>)", html, flags=re.S)
    return "".join(c if c.startswith("<") else _MAIL.sub(tekst, c) for c in czesci)


_HALA = re.compile(r"(?:[Hh]ala|[Hh]ali|[Hh]alę) przy PSP nr 3 w Kobyłce(?:,? (?:ul\. )?(?:ks\. Marcina )?Załuskiego 57(?:, (?:05-230 )?Kobyłka)?)?")


def linkuj_hale(html):
    """Każda wzmianka „hala przy PSP nr 3 w Kobyłce…” w tekście strony prowadzi do Google Maps
    (poza nagłówkiem, skryptami, atrybutami i istniejącymi linkami/przyciskami)."""
    mapa = C.HALA_DOMOWA.get("mapa")
    if not mapa or "<body" not in html:
        return html
    glowa, cialo = html.split("<body", 1)
    czesci = re.split(r"(<script\b.*?</script>|<style\b.*?</style>|<[^>]+>)", cialo, flags=re.S)
    w_linku = 0
    wynik = []
    for c in czesci:
        if c.startswith("<"):
            if re.match(r"<(a|button|option|textarea|title)\b", c, re.I):
                w_linku += 1
            elif re.match(r"</(a|button|option|textarea|title)>", c, re.I):
                w_linku = max(0, w_linku - 1)
            wynik.append(c)
        elif w_linku:
            wynik.append(c)
        else:
            wynik.append(_HALA.sub(lambda m: f'<a class="link-hala" href="{mapa}" target="_blank" rel="noopener" '
                                             f'title="Pokaż halę w Google Maps">{m.group(0)}</a>', c))
    return glowa + "<body" + "".join(wynik)


# ---- SEO: adres kanoniczny, podgląd przy udostępnianiu, dane strukturalne, mapa strony ----
STRONY_HTML = []          # wszystkie zapisane strony – z nich powstaje sitemap.xml
DODATKI_SEO = {}          # sciezka → {"obraz", "typ", "ld": [...], "data", "obrazy"} ustawiane przez budowę strony
GEO_HALI = {"@type": "GeoCoordinates", "latitude": 52.342153, "longitude": 21.213106}

OKRUSZKI = [("aktualnosci/", "Aktualności", "aktualnosci.html"), ("zawodniczki/", "Kadra", "druzyny.html"),
            ("mecze/", "Terminarz i wyniki", "terminarz.html"), ("akademia-aktualnosci/", "Akademia", "akademia.html"),
            ("akademia-poradnik/", "Akademia", "akademia.html")]


def okruszki_ld(sciezka, html):
    """Ścieżka nawigacji (Start › Sekcja › Strona) – Google pokazuje ją w wynikach zamiast adresu."""
    if sciezka in ("index.html", "404.html", "statystyki.html"):
        return None
    baza = C.KLUB["adres_strony"].rstrip("/") + "/"
    tytul = re.search(r"<title>([^<]*)</title>", html)
    tytul = (tytul.group(1) if tytul else sciezka).split(" – ")[0].split(" | ")[0].strip()
    elementy = [("Volley Kobyłka", baza)]
    for prefiks, nazwa, adres in OKRUSZKI:
        if sciezka.startswith(prefiks):
            elementy.append((nazwa, baza + adres))
    elementy.append((tytul, adres_pelny(sciezka)))
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u}
                                for i, (n, u) in enumerate(elementy)]}


def adres_pelny(sciezka):
    baza = C.KLUB["adres_strony"].rstrip("/") + "/"
    return baza if sciezka == "index.html" else baza + sciezka


def dane_strukturalne(sciezka):
    """JSON-LD dla Google: klub (strona wyboru, drużyna, kontakt, o klubie) albo Akademia."""
    baza = C.KLUB["adres_strony"].rstrip("/") + "/"
    adres = {"@type": "PostalAddress", "streetAddress": "ul. ks. Marcina Załuskiego 57",
             "postalCode": "05-230", "addressLocality": "Kobyłka", "addressRegion": "mazowieckie",
             "addressCountry": "PL"}
    hala = {"@type": "SportsActivityLocation", "@id": baza + "#hala", "name": C.HALA_DOMOWA["nazwa"],
            "address": adres, "geo": GEO_HALI, "hasMap": C.HALA_DOMOWA.get("mapa")}
    klub = {"@context": "https://schema.org", "@type": "SportsOrganization", "@id": baza + "#klub",
            "name": C.KLUB["nazwa_prawna"] + " Kobyłka", "alternateName": [C.KLUB["nazwa"], "KS Volley Kobyłka", "Volley Kobyłka"],
            "url": baza, "logo": baza + "img/favicon-512.png", "sport": "Siatkówka",
            "address": adres, "location": hala, "email": C.KLUB.get("email"), "foundingDate": "2021",
            "areaServed": ["Kobyłka", "Wołomin", "Marki", "Zielonka", "Radzymin", "powiat wołomiński"],
            "sameAs": [x for x in [C.KLUB.get("facebook"), C.KLUB.get("instagram"), C.KLUB.get("youtube"),
                                   C.KLUB.get("volleybox")] if x]}
    if sciezka in ("index.html", S.START_DRUZYNY, "kontakt.html", "o-klubie.html"):
        druzyna = {"@context": "https://schema.org", "@type": "SportsTeam", "name": C.KLUB["nazwa"],
                   "url": baza + S.START_DRUZYNY, "sport": "Siatkówka", "gender": "Female",
                   "memberOf": {"@type": "SportsOrganization", "name": "2. liga kobiet"},
                   "parentOrganization": {"@id": baza + "#klub"}, "location": hala,
                   "coach": [{"@type": "Person", "name": "Mateusz Mosur"}]}
        return [klub, druzyna]
    if sciezka == "akademia.html":
        A = C.AKADEMIA
        return [{"@context": "https://schema.org", "@type": "SportsOrganization",
                 "name": A["nazwa"] + " Kobyłka", "url": baza + "akademia.html",
                 "logo": baza + "img/" + A["logo"] if A.get("logo") else None, "sport": "Siatkówka",
                 "description": A.get("opis"), "address": adres, "location": hala, "email": (A.get("koordynator") or {}).get("email"), "telephone": S.tel_link((A.get("koordynator") or {}).get("telefon")) if (A.get("koordynator") or {}).get("telefon") else None,
                 "areaServed": ["Kobyłka", "Wołomin", "Marki", "Zielonka", "Radzymin"],
                 "parentOrganization": {"@type": "SportsOrganization", "name": C.KLUB["nazwa_prawna"] + " Kobyłka", "url": baza},
                 "sameAs": [x for x in [A.get("facebook")] if x],
                 "member": [{"@type": "Person", "name": f'{t["imie"]} {t["nazwisko"]}', "jobTitle": t.get("rola") or "Trener"}
                            for t in A.get("trenerzy", [])] or None,
                 "makesOffer": [{"@type": "Offer", "name": "Treningi siatkówki dla dziewcząt – " + c["co"],
                                 "price": re.sub(r"[^0-9]", "", c["cena"].split("/")[0]), "priceCurrency": "PLN",
                                 "url": A.get("formularz_google") or baza + "akademia.html#zapisy",
                                 "priceSpecification": {"@type": "UnitPriceSpecification",
                                                        "price": re.sub(r"[^0-9]", "", c["cena"].split("/")[0]),
                                                        "priceCurrency": "PLN", "unitText": "miesiąc"}}
                                for c in A.get("cennik", [])] or None}]
    return []


def seo_glowa(sciezka, html):
    if "</head>" not in html:
        return html
    akademia = sciezka.startswith("akademia")
    baza = C.KLUB["adres_strony"].rstrip("/") + "/"
    obraz = baza + ("img/og-akademia.jpg" if akademia else "img/og-klub.jpg")
    if not akademia and OG_ZAPOWIEDZ and sciezka in ("index.html", S.START_DRUZYNY, "terminarz.html"):
        obraz = baza + OG_ZAPOWIEDZ   # podgląd linku = aktualna zapowiedź meczu
    if sciezka in ("404.html", "statystyki.html"):
        dodatki = '<meta name="robots" content="noindex">'
    else:
        url = adres_pelny(sciezka)
        ext = DODATKI_SEO.get(sciezka, {})
        if ext.get("obraz"):
            obraz = baza + ext["obraz"]
        dodatki = (f'<link rel="canonical" href="{url}">\n<meta property="og:url" content="{url}">\n'
                   f'<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">\n'
                   f'<meta name="google-site-verification" content="QCK9CVR58j00dsLP-OrZPnkaL0-ostHmE8_tMVINryE">\n'
                   f'<meta property="og:locale" content="pl_PL">\n'
                   f'<meta property="og:type" content="{ext.get("typ", "website")}">\n'
                   f'<meta property="og:site_name" content="{"Akademia Siatkówki Volley" if akademia else C.KLUB["nazwa"]}">\n'
                   f'<meta property="og:image" content="{obraz}">\n<meta property="og:image:width" content="1200">\n'
                   f'<meta property="og:image:height" content="630">\n<meta name="twitter:card" content="summary_large_image">')
        okr = okruszki_ld(sciezka, html)
        for d in dane_strukturalne(sciezka) + ext.get("ld", []) + ([okr] if okr else []):
            d = {k: v for k, v in d.items() if v is not None}
            dodatki += ('\n<script type="application/ld+json">' +
                        json.dumps(d, ensure_ascii=False).replace("</", "<\\/") + "</script>")
    return html.replace("</head>", dodatki + "\n</head>", 1)


def zapisz(sciezka, tekst):
    if sciezka.endswith(".html"):
        tekst = ukryj_maile(linkuj_hale(seo_glowa(sciezka, tekst)))
        if sciezka != "404.html":
            STRONY_HTML.append(sciezka)
    pelna = os.path.join(WYJSCIE, sciezka)
    os.makedirs(os.path.dirname(pelna), exist_ok=True)
    with open(pelna, "w", encoding="utf-8", newline="\n") as f:
        f.write(tekst)


def wersja_zasobow():
    """Krótki „odcisk” CSS i JS – przeglądarki pobiorą nowe pliki tylko po zmianie."""
    h = hashlib.md5()
    for plik in ("fonty.css", "style.css", "main.js"):
        with open(os.path.join(FOLDER, "zasoby", plik), "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:8]


# =====================================================================
# 3. PODSTRONY
# =====================================================================
POLITYKA_DATA = "28 października 2026"


def forma_druzyn(wszystkie):
    """Wyniki całej grupy → {nazwa (norm): [mecze od najstarszego]} z punktu widzenia każdej drużyny."""
    forma = {}
    for w in sorted(wszystkie or [], key=lambda x: x["data"]):
        try:
            a, b = (int(x) for x in w["wynik"].split(":"))
        except ValueError:
            continue
        for nazwa, rywal, moje, jego in ((w["gospodarz"], w["gosc"], a, b), (w["gosc"], w["gospodarz"], b, a)):
            forma.setdefault(zrodla.norm(nazwa), []).append(
                {"data": w["data"], "rywal": rywal, "wynik": f"{moje}:{jego}", "w": moje > jego})
    return forma


def zmniejsz_zasoby(folder):
    """Mniejsze style.css i main.js na serwerze (bez komentarzy i wcięć) – szybsze ładowanie na telefonie.
    Pliki źródłowe w zasoby/ zostają czytelne."""
    try:
        sc = os.path.join(folder, "style.css")
        css = open(sc, encoding="utf-8").read()
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        css = re.sub(r"\s+", " ", css)
        css = re.sub(r"\s*([{};,>])\s*", r"\1", css).replace(";}", "}")
        open(sc, "w", encoding="utf-8").write(css.strip())
        sj = os.path.join(folder, "main.js")
        js = open(sj, encoding="utf-8").read()
        js = re.sub(r"(^|\n)\s*/\*.*?\*/", r"\1", js, flags=re.S)
        js = "\n".join(l.strip() for l in js.split("\n") if l.strip() and not l.strip().startswith("//"))
        open(sj, "w", encoding="utf-8").write(js)
    except Exception as blad:
        print(f"  UWAGA: zmniejszanie CSS/JS: {blad} – zostają pełne pliki")


def zglos_indexnow(adresy):
    """Po każdej przebudowie zgłasza Bingowi (i innym wyszukiwarkom IndexNow) strony, których treść się zmieniła.
    Odciski stron trzymane w dane/indexnow.json (repozytorium zapamiętuje je między przebudowami)."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return                                   # zgłaszamy tylko z serwera, nie z komputera
    import urllib.request
    plik = os.path.join(FOLDER, "dane", "indexnow.json")
    try:
        stare = json.load(open(plik, encoding="utf-8"))
    except Exception:
        stare = {}
    nowe, zmienione = {}, []
    baza = C.KLUB["adres_strony"].rstrip("/") + "/"
    for url in adresy:
        sciezka = "index.html" if url == baza else url[len(baza):]
        try:
            tekst = open(os.path.join(WYJSCIE, sciezka), encoding="utf-8").read()
        except OSError:
            continue
        tekst = re.sub(r'\?v=[0-9a-f]+|data-start="[^"]*"|\d+<small>[dhms]</small>', "", tekst)   # zegary, wersje plików
        h = hashlib.md5(tekst.encode("utf-8")).hexdigest()[:12]
        nowe[url] = h
        if stare.get(url) != h:
            zmienione.append(url)
    json.dump(nowe, open(plik, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    if not zmienione:
        return
    klucz = INDEXNOW_KLUCZ
    dane = json.dumps({"host": baza.split("/")[2], "key": klucz, "keyLocation": f"{baza}{klucz}.txt",
                       "urlList": zmienione[:1000]}).encode("utf-8")
    try:
        zad = urllib.request.Request("https://api.indexnow.org/indexnow", data=dane,
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        with urllib.request.urlopen(zad, timeout=20) as odp:
            print(f"  IndexNow: zgłoszono {len(zmienione)} zmienionych stron (HTTP {odp.status})")
    except Exception as blad:
        print(f"  UWAGA: IndexNow: {blad}")


def _sezon():
    r = DZIS.year if DZIS.month >= 8 else DZIS.year - 1
    return f"{r}/{str(r + 1)[2:]}"


# Tytuły i opisy podstron dla Google (frazy: siatkówka kobiet Kobyłka, Volley Kobyłka, II liga)
SEO_PODSTRON = {
    "druzyny.html": ("Kadra Easy Wrap Volley Kobyłka – siatkarki, II liga kobiet",
                     f"Kadra Easy Wrap Volley Kobyłka na sezon {_sezon()}: siatkarki, pozycje, numery, wzrost, "
                     "poprzednie kluby i sezony w Kobyłce. Siatkówka kobiet – II liga."),
    "terminarz.html": ("Terminarz, wyniki i tabela – Easy Wrap Volley Kobyłka",
                       "Terminarz meczów, wyniki i tabela II ligi kobiet – Easy Wrap Volley Kobyłka. "
                       "Godziny, hale, dojazd, forma drużyn i kalendarz sezonu do telefonu."),
    "aktualnosci.html": ("Aktualności – Volley Kobyłka, siatkówka kobiet",
                         "Najnowsze wiadomości Easy Wrap Volley Kobyłka: zapowiedzi i relacje meczów II ligi kobiet, "
                         "MVP, wydarzenia klubu i Akademii Siatkówki Volley."),
    "o-klubie.html": ("O klubie – KS Volley Kobyłka, siatkówka w Kobyłce",
                      "Klub Sportowy Volley z Kobyłki: drużyna siatkówki kobiet Easy Wrap Volley w II lidze "
                      "i Akademia Siatkówki Volley dla dziewcząt. Historia, wartości i dane klubu."),
    "sponsorzy.html": ("Sponsorzy i partnerzy – Easy Wrap Volley Kobyłka",
                       "Firmy, które wspierają siatkówkę kobiet w Kobyłce – sponsorzy i partnerzy Easy Wrap Volley "
                       "Kobyłka. Sprawdź, jak zostać sponsorem klubu."),
    "kontakt.html": ("Kontakt – Volley Kobyłka | Easy Wrap Volley i Akademia",
                     None),
    "galeria.html": ("Galeria – zdjęcia Easy Wrap Volley Kobyłka",
                     "Zdjęcia z meczów i treningów siatkarek Easy Wrap Volley Kobyłka – II liga kobiet, "
                     "hala przy PSP nr 3 w Kobyłce, ul. Załuskiego 57."),
    "sklep.html": ("Sklep – koszulki i gadżety Easy Wrap Volley Kobyłka",
                   "Koszulki i gadżety Easy Wrap Volley Kobyłka – wspieraj siatkówkę kobiet w Kobyłce."),
}


def ladny_tytul(tytul, dlugosc=70):
    """Tytuł newsa z Facebooka: bez WIELKICH LITER (nazwy własne zostają wielką literą) i nie dłuższy niż ~70 znaków."""
    litery = [c for c in tytul if c.isalpha()]
    if litery and sum(c.isupper() for c in litery) / len(litery) > 0.6:
        skroty = {"MVP", "II", "III", "IV", "AZS", "AWF", "MKS", "UKS", "LKS", "ŁKS", "MUKS", "MOS", "PZPS",
                  "WZPS", "KS", "TPS", "SMS", "GKS", "LTS", "PGE", "UMED", "VIP", "EASY", "WRAP"}
        wlasne = set()
        for tekst in ([C.KLUB["nazwa"], "Kobyłka Kobyłce Kobyłki Polska Polski Warszawa Łódź Volley FortisGO Mazowsze"]
                      + [r.get("skrot", "") for r in C.RYWALE.values()]
                      + [n for r in C.RYWALE.values() for n in r.get("nazwy_w_zwiazkach", [])]
                      + [f'{z["imie"]} {z["nazwisko"]}' for z in C.KADRA] + [s["nazwa"] for s in C.SPONSORZY.values()]):
            for w in re.findall(r"\w+", tekst):
                if len(w) > 2:
                    wlasne.add(w.lower()[:5])
        slowa = []
        for i, w in enumerate(re.split(r"(\s+)", tytul.lower())):
            czyste = re.sub(r"\W", "", w)
            if czyste.upper() in skroty and czyste.upper() not in ("EASY", "WRAP"):
                w = w.upper()
            elif czyste and (czyste[:5] in wlasne and len(czyste) > 2):
                w = w[:1].upper() + w[1:] if w[:1].isalpha() else w[:1] + w[1:2].upper() + w[2:]
            slowa.append(w)
        tytul = "".join(slowa)
        tytul = re.sub(r"^(\W*)(\w)", lambda m: m.group(1) + m.group(2).upper(), tytul)
        tytul = re.sub(r"([.!?]\s+)(\w)", lambda m: m.group(1) + m.group(2).upper(), tytul)
    if len(tytul) > dlugosc:
        zdanie = re.split(r"(?<=[.!?])\s", tytul, maxsplit=1)[0]
        if 25 <= len(zdanie) <= dlugosc:
            tytul = zdanie
        else:
            tytul = tytul[:dlugosc - 1].rsplit(" ", 1)[0].rstrip(",;:–-") + "…"
    return tytul


class Budowa:
    def __init__(self, dane_zwiazkowe):
        self.dane = dane_zwiazkowe
        self.zapowiedz = None          # uzupełnia main() po pobraniu postów z FB/IG
        self.mecze = zbierz_mecze(dane_zwiazkowe)
        self.wersja = wersja_zasobow()
        glowne = [m for m in self.mecze if m["druzyna"] == GLOWNA]
        self.rozegrane = [m for m in glowne if m.get("wynik")]
        self.nadchodzace = [m for m in glowne if not m.get("wynik") and m["data"] >= DZIS]
        self.najblizszy = self.nadchodzace[0] if self.nadchodzace else None
        if self.najblizszy:
            self.najblizszy["najblizszy"] = True   # wyróżnienie na kartach meczów
        self.newsy = sorted(C.NEWSY, key=lambda n: n["data"], reverse=True)
        self.newsy_akademii = []       # uzupełnia main() z postów FB Akademii
        self.wyniki_grupy = (dane_zwiazkowe.get(GLOWNA) or {}).get("wszystkie") or []
        self._forma = forma_druzyn(self.wyniki_grupy)

    def forma(self, nazwa, ile=5):
        return self._forma.get(zrodla.norm(nazwa), [])[-ile:]

    def przed_meczem(self, p, m=None):
        """Blok „Przed meczem” pod plakatem: miejsca, forma, wcześniejsze mecze tych drużyn."""
        m = m or self.najblizszy
        if not m or not m["strony"][1] or not self.tabela():
            return ""
        def wiersz(strona):
            for w in self.tabela():
                d = opis_druzyny(w["nazwa"])
                if (strona.get("nasza") and w["nasz"]) or (not strona.get("nasza") and d["krotko"] == strona["krotko"]):
                    return w
            return None
        wg, wh = (wiersz(x) for x in m["strony"])
        if not (wg and wh):
            return ""
        ng, nh = zrodla.norm(wg["nazwa"]), zrodla.norm(wh["nazwa"])
        bezp = [w for w in self.wyniki_grupy if {zrodla.norm(w["gospodarz"]), zrodla.norm(w["gosc"])} == {ng, nh}]
        return S.przed_meczem(p, m, wg, wh, self.forma(wg["nazwa"]), self.forma(wh["nazwa"]),
                              sorted(bezp, key=lambda x: x["data"]), opis_druzyny)

    # --- wspólny układ ---------------------------------------------------
    def strona(self, plik, tytul, opis, tresc, aktywna=None, p=None, pelny=None):
        if p is None:
            p = "../" * plik.count("/")
        seo = SEO_PODSTRON.get(plik)
        if seo:
            pelny, opis = seo[0], seo[1] or opis
        kandydaci = self.rozegrane[-1:] + self.nadchodzace[:4]
        html = S.uklad(tytul, opis, tresc(p), aktywna or plik, p, S.belka(p, kandydaci), self.wersja, pelny)
        zapisz(plik, html)

    def tabela(self, druzyna=GLOWNA):
        return (self.dane.get(druzyna) or {}).get("tabela") or []

    # --- STRONA GŁÓWNA ---------------------------------------------------
    def strona_glowna(self):
        def tresc(p):
            ostatnie = self.rozegrane[-2:]
            kolejne = [m for m in self.mecze if not m.get("wynik") and m["data"] >= DZIS][:4]
            karty = "".join(S.karta_meczu(p, m) for m in ostatnie + kolejne)
            ost = self.rozegrane[-1] if self.rozegrane else None
            ostatni_html = ""
            if ost:
                g, h = ost["strony"]
                a, b = ost["wynik"].split(":")
                ostatni_html = f"""
<div class="ostatni pojaw">
  <span class="wynik-etykieta{'' if ost['wygrana'] else ' wynik-etykieta--p'}">Ostatni mecz · {'wygrana' if ost['wygrana'] else 'porażka'}</span>
  <div class="ostatni__wynik">{e(a)}<span>:</span>{e(b)}</div>
  <p class="ostatni__pary">{e(g['krotko'])} – {e(h['krotko'])}</p>
  {S.sety_html(ost)}
  {f'<p class="ostatni__mvp">MVP: <strong>{e(ost["mvp"])}</strong></p>' if ost.get('mvp') else ''}
  {f'<a class="btn btn--zolty" href="{p}aktualnosci/{e(ost["relacja"])}.html">Relacja z meczu →</a>' if ost.get('relacja') else ''}
</div>"""
            # Na stronie głównej: 3 losowe zawodniczki (losuje main.js przy każdym wejściu;
            # bez JS widać kapitan + kolejne wg numeru)
            kadra = sorted([z for z in C.KADRA if z["druzyna"] == GLOWNA],
                           key=lambda z: (not z.get("kapitan"), z["numer"]))
            newsy = self.newsy[:3]
            sponsorzy = self.sponsorzy_html(p)
            return f"""
{S.okienko_zapowiedzi(p, self.zapowiedz, C.ZAPOWIEDZ, self.najblizszy)}
{S.hero(p, self.najblizszy)}
{self.wydarzenia_ld(tylko_najblizszy=True)}
{self.przed_meczem(p)}
<section class="sekcja sekcja--po-hero" aria-labelledby="news-tytul">
  <div class="kontener">
    {S.naglowek_sekcji('Aktualności', '', p + 'aktualnosci.html', 'Wszystkie', id_='news-tytul')}
    <div class="newsy pojaw">{''.join(S.karta_newsa(p, n, i == 0) for i, n in enumerate(newsy))}</div>
  </div>
</section>
<section class="sekcja" aria-labelledby="mecze-tytul">
  <div class="kontener" data-filtrowanie>
    {S.naglowek_sekcji('Mecze', 'i wyniki', p + 'terminarz.html', 'Pełny terminarz', id_='mecze-tytul')}
    <p class="kal-sub-link"><a href="{p}terminarz.html#w-telefonie">📅 Terminarz w telefonie – aktualizuje się sam →</a></p>
    {self.filtry_druzyn()}
    <div class="mecze pojaw">{karty}</div>
    <p class="przesun" aria-hidden="true">Przesuń</p>
  </div>
</section>

<section class="sekcja" aria-labelledby="tabela-tytul">
  <div class="kontener uklad-tabela">
    {ostatni_html}
    <div class="pojaw">
      {S.naglowek_sekcji('Tabela', '', p + 'terminarz.html#tabela', 'Terminarz i tabela', id_='tabela-tytul')}
      {S.prezentuje('tabela', p)}
      {S.tabela_html(p, self.tabela(), opis_druzyny, C.DRUZYNY[GLOWNA]['liga'], self.forma)}
    </div>
  </div>
</section>

<section class="sekcja sekcja--biala" aria-labelledby="kadra-tytul">
  <div class="kontener">
    {S.naglowek_sekcji('Nasza', 'kadra', p + 'druzyny.html', 'Wszystkie zawodniczki', id_='kadra-tytul')}
    {S.prezentuje('kadra', p)}
    <div class="kadra kadra--losowa pojaw" data-losowa-kadra>{''.join(S.karta_zawodniczki(p, z) for z in kadra)}</div>
    <p class="przesun" aria-hidden="true">Przesuń</p>
    {self.ciekawostka(p, kadra)}
  </div>
</section>

<section class="sekcja" aria-labelledby="bento-tytul">
  <div class="kontener">
    {S.naglowek_sekcji('Więcej', 'niż mecz', id_='bento-tytul')}
    <div class="bento pojaw">{self.kafle(p)}</div>
  </div>
</section>

{sponsorzy}"""
        self.strona(S.START_DRUZYNY, C.KLUB["nazwa"], C.KLUB["opis"], tresc)

    def kafle(self, p):
        """Kafelki „Więcej niż mecz” – Galeria i Sklep tylko wtedy, gdy mają treść."""
        male = []
        if S.galeria_ma_zdjecia():
            male.append(("galeria.html", "Galeria", "Zdjęcia z meczów", "foto-1"))
        if S.sklep_ma_produkty():
            male.append(("sklep.html", "Sklep", "Barwy klubowe", "foto-0"))
        male += [("o-klubie.html", "O klubie", "Od 2021 w Kobyłce", "foto-2"),
                 ("sponsorzy.html", "Sponsorzy", "Zostań partnerem", "foto-1")]
        postac = S.postac_do_plakatu(None)
        # Przy każdym wejściu main.js losuje inną zawodniczkę z listy (bez JS zostaje ta z dnia)
        wszystkie = [S.src_img(p, z['zdjecie']) for z in C.KADRA
                     if z["druzyna"] == GLOWNA and S.jest_plik(z.get("zdjecie"))]
        foto = (f'<img class="kafel__postac" src="{p}img/{e(postac["zdjecie"])}" alt="" '
                f'data-losowe=\'{e(json.dumps(wszystkie))}\'>' if postac else "")
        html = (f'<a class="kafel kafel--akademia" href="{p}druzyny.html"><span class="kafel__foto foto-0">{foto}</span>'
                f'<small>Kadra 2026/27</small><span class="kafel__slowo">Poznaj nas!</span>'
                f'<small>{sum(1 for z in C.KADRA if z["druzyna"] == GLOWNA)} zawodniczek · 2. liga kobiet →</small></a>')
        html += "".join(f'<a class="kafel" href="{p}{plik}"><span class="kafel__foto {tlo}"></span>'
                        f'<span class="kafel__slowo">{nazwa}</span><small>{opis}</small></a>'
                        for plik, nazwa, opis, tlo in male)
        # Kontakt domyka siatkę: przy parzystej liczbie małych kafli zajmuje cały rząd
        szeroki = " kafel--kontakt-pelny" if len(male) % 2 == 0 else ""
        html += (f'<a class="kafel kafel--kontakt{szeroki}" href="{p}kontakt.html"><span class="kafel__foto foto-3"></span>'
                 f'<span class="kafel__slowo">Kontakt</span><small>{e(C.KLUB["email"])}</small></a>')
        return html

    def wydarzenia_ld(self, tylko_najblizszy=False):
        """Mecze jako wydarzenia sportowe (schema.org SportsEvent) – Google może pokazać terminy w wynikach."""
        from zoneinfo import ZoneInfo
        baza = C.KLUB["adres_strony"].rstrip("/") + "/"
        if isinstance(tylko_najblizszy, dict):
            mecze = [tylko_najblizszy]
        else:
            mecze = [self.najblizszy] if tylko_najblizszy and self.najblizszy else \
                [m for m in self.mecze if m["druzyna"] == GLOWNA and (m.get("wynik") or m["data"] >= DZIS - timedelta(days=60))]
        lista = []
        for m in mecze:
            gosp, gosc = m["strony"]
            if not gosc:
                continue
            g = m.get("godzina") or "00:00"
            try:
                hh, mm = (int(x) for x in g.split(":"))
            except ValueError:
                hh, mm = 0, 0
            start = datetime(m["data"].year, m["data"].month, m["data"].day, hh, mm, tzinfo=ZoneInfo("Europe/Warsaw"))
            hala = m.get("hala") or (C.HALA_DOMOWA.get("nazwa") if m["u_siebie"] else "") or "Hala sportowa"
            adres = m.get("adres") or (C.HALA_DOMOWA["adres"] if m["u_siebie"] else "")
            w = {
                "@type": "SportsEvent",
                "name": f"{gosp['nazwa']} – {gosc['nazwa']} ({m['liga']})",
                "sport": "Volleyball",
                "startDate": start.isoformat() if m.get("godzina") else m["data"].isoformat(),
                "eventStatus": "https://schema.org/EventScheduled",
                "endDate": (start + timedelta(hours=2)).isoformat() if m.get("godzina") else m["data"].isoformat(),
                "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
                "location": {"@type": "Place", "name": hala,
                             "address": {"@type": "PostalAddress", "streetAddress": adres or hala, "addressCountry": "PL"}},
                "homeTeam": {"@type": "SportsTeam", "name": gosp["nazwa"]},
                "awayTeam": {"@type": "SportsTeam", "name": gosc["nazwa"]},
                "competitor": [{"@type": "SportsTeam", "name": gosp["nazwa"]}, {"@type": "SportsTeam", "name": gosc["nazwa"]}],
                # „performer” – Google Search Console zgłasza brak tego pola przy wydarzeniach (występują obie drużyny)
                "performer": [{"@type": "SportsTeam", "name": gosp["nazwa"]}, {"@type": "SportsTeam", "name": gosc["nazwa"]}],
                "organizer": {"@type": "SportsOrganization", "name": C.KLUB["nazwa_prawna"], "url": baza},
                "url": baza + (S.adres_meczu(m) or "terminarz.html"),
                "image": baza + (m.get("grafika_wyniku") and S.jest_plik(m["grafika_wyniku"]) and "img/" + m["grafika_wyniku"]
                                 or OG_ZAPOWIEDZ or "img/og-klub.jpg"),
                "description": f"Mecz {m['liga']}: {gosp['nazwa']} – {gosc['nazwa']}"
                               + (f", wynik {m['wynik']}" if m.get("wynik") else "") + ".",
            }
            if m["u_siebie"] and C.KLUB.get("wstep_wolny"):
                w["isAccessibleForFree"] = True
                w["offers"] = {"@type": "Offer", "price": "0", "priceCurrency": "PLN", "availability": "https://schema.org/InStock",
                               "url": baza + "terminarz.html", "validFrom": (m["data"] - timedelta(days=14)).isoformat()}
            lista.append(w)
        if not lista:
            return ""
        dane = {"@context": "https://schema.org", "@graph": lista}
        return '<script type="application/ld+json">' + json.dumps(dane, ensure_ascii=False).replace("</", "<\\/") + "</script>"

    def strony_meczow(self):
        """Osobna strona każdego meczu pierwszej drużyny: zapowiedź → po meczu wynik, sety, MVP, relacja.
        Adres stały (mecze/data-rywal.html) – Google łapie frazy typu „Volley Kobyłka Łask wynik”."""
        mecze = sorted([m for m in self.mecze if S.adres_meczu(m)], key=lambda m: m["data"])
        for i, m in enumerate(mecze):
            adres = S.adres_meczu(m)
            gosp, gosc = m["strony"]
            rywal = gosc if gosp.get("nasza") else gosp
            d = m["data"]
            liga = m.get("liga") or C.DRUZYNY[GLOWNA]["liga"]
            hala = m.get("hala") or (C.HALA_DOMOWA["nazwa"] if m["u_siebie"] else "")
            adr = m.get("adres") or (C.HALA_DOMOWA["adres"] if m["u_siebie"] else "")
            rozegrany = bool(m.get("wynik"))
            if rozegrany:
                tytul = f"{gosp['krotko']} – {gosc['krotko']} {m['wynik']} ({d.strftime('%d.%m.%Y')})"
                opis = (f"Wynik meczu {liga}: {gosp['nazwa']} – {gosc['nazwa']} {m['wynik']}"
                        + (f" (sety {', '.join(m.get('sety') or [])})" if m.get("sety") else "")
                        + (f". MVP: {m['mvp']}" if m.get("mvp") else "") + f". {d.strftime('%d.%m.%Y')}"
                        + (f", {hala}" if hala else "") + ".")
                pelny = f"{gosp['krotko']} – {gosc['krotko']} {m['wynik']} – wynik meczu {d.strftime('%d.%m.%Y')} | Volley Kobyłka"
            else:
                tytul = f"{gosp['krotko']} – {gosc['krotko']}"
                opis = (f"Zapowiedź meczu {liga}: {gosp['nazwa']} – {gosc['nazwa']}, {S.data_pl(d)}"
                        + (f", godz. {m['godzina']}" if m.get("godzina") else "") + (f", {hala}" if hala else "")
                        + (". Wstęp wolny" if m["u_siebie"] and C.KLUB.get("wstep_wolny") else "") + ".")
                pelny = f"{gosp['krotko']} – {gosc['krotko']}, {d.strftime('%d.%m.%Y')} – zapowiedź meczu | Volley Kobyłka"
            obraz = None
            if rozegrany and m.get("grafika_wyniku") and S.jest_plik(m["grafika_wyniku"]):
                obraz = "img/" + m["grafika_wyniku"]
            elif m is self.najblizszy and OG_ZAPOWIEDZ:
                obraz = OG_ZAPOWIEDZ
            ld = self.wydarzenia_ld(m)
            DODATKI_SEO[adres] = {"obraz": obraz, "data": (d if rozegrany else DZIS).isoformat(),
                                  "obrazy": [obraz] if obraz else []}
            poprz = mecze[i - 1] if i > 0 else None
            nast = mecze[i + 1] if i + 1 < len(mecze) else None

            def tresc(p, m=m, gosp=gosp, gosc=gosc, rywal=rywal, d=d, liga=liga, hala=hala, adr=adr,
                      rozegrany=rozegrany, poprz=poprz, nast=nast, ld=ld):
                a = b = ""
                if rozegrany:
                    a, b = m["wynik"].split(":")
                def strona(s_, pkt):
                    return (f'<div class="mstr__druzyna">{S.herb(p, s_, "mstr__herb")}'
                            f'<strong>{S.nazwa_druzyny(s_)}</strong>{f"<b>{e(pkt)}</b>" if pkt != "" else ""}</div>')
                wynik_html = (f'<div class="mstr__wynik">{strona(gosp, a)}<span class="mstr__vs">{"" if rozegrany else "vs"}</span>'
                              f'{strona(gosc, b)}</div>')
                fakty = [("Data", S.data_pl(d)), ("Godzina", m.get("godzina") or "wkrótce"), ("Rozgrywki", liga)]
                if hala:
                    fakty.append(("Hala", hala))
                if adr:
                    fakty.append(("Adres", adr))
                if m["u_siebie"] and C.KLUB.get("wstep_wolny") and not rozegrany:
                    fakty.append(("Wstęp", "wolny"))
                fakty_html = "".join(f"<div><dt>{e(x)}</dt><dd>{e(y)}</dd></div>" for x, y in fakty)
                if rozegrany:
                    o_meczu = (f"{e(gosp['nazwa'])} – {e(gosc['nazwa'])} {e(m['wynik'])}"
                               + (f" (sety: {e(', '.join(m.get('sety') or []))})" if m.get("sety") else "") + ". "
                               + (f"Mecz {e(liga)} rozegrany {e(S.data_pl(d))}" + (f" w hali: {e(hala)}" if hala else "") + ". ")
                               + (f"{'Wygrana' if m.get('wygrana') else 'Porażka'} {e(C.KLUB['nazwa'])}. ")
                               + (f"MVP spotkania: {S.link_zawodniczki(p, m['mvp'])}." if m.get("mvp") else ""))
                else:
                    o_meczu = (f"{'Zapraszamy na mecz' if m['u_siebie'] else 'Mecz wyjazdowy'} {e(liga)}: "
                               f"{e(gosp['nazwa'])} – {e(gosc['nazwa'])}, {e(S.data_pl(d))}"
                               + (f", godz. {e(m['godzina'])}" if m.get("godzina") else "")
                               + (f", {e(hala)}" if hala else "") + ". "
                               + ("Wstęp wolny – przyjdź i dopinguj nasze siatkarki! " if m["u_siebie"] and C.KLUB.get("wstep_wolny") else "")
                               + ("Wynik na żywo zobaczysz na tej stronie w dniu meczu." if C.KLUB.get("wyniki_na_zywo") else ""))
                guziki = []
                if not rozegrany and d >= DZIS:
                    guziki.append(f'<a class="btn btn--zolty" href="{p}kalendarz/{e(m["plik_ics"])}" download>Dodaj do kalendarza</a>')
                    if C.HALA_DOMOWA.get("mapa") and m["u_siebie"]:
                        guziki.append(f'<a class="btn btn--obrys" href="{e(C.HALA_DOMOWA["mapa"])}" target="_blank" rel="noopener">Dojazd ↗</a>')
                    elif adr:
                        guziki.append(f'<a class="btn btn--obrys" href="https://www.google.com/maps/search/?api=1&amp;query={quote(adr)}" '
                                      f'target="_blank" rel="noopener">Dojazd ↗</a>')
                if m.get("relacja"):
                    guziki.append(f'<a class="btn btn--zolty" href="{p}aktualnosci/{e(m["relacja"])}.html">Relacja z meczu →</a>')
                grafika = ""
                if rozegrany and m.get("grafika_wyniku") and S.jest_plik(m["grafika_wyniku"]):
                    grafika = (f'<figure class="mstr__grafika"><img src="{e(S.src_img(p, m["grafika_wyniku"]))}" loading="lazy" '
                               f'alt="Wynik meczu {e(gosp["krotko"])} – {e(gosc["krotko"])} {e(m["wynik"])}"></figure>')
                przed = self.przed_meczem(p, m) if not rozegrany else ""
                rywal_vb = (f'<p>Profil rywala: <a href="{e(rywal["volleybox"])}" target="_blank" rel="noopener">'
                            f'{e(rywal["nazwa"])} na Volleybox ↗</a></p>') if rywal.get("volleybox") else ""
                nawig = '<nav class="pm__nawig" aria-label="Inne mecze">'
                if poprz:
                    nawig += f'<a href="{p}{S.adres_meczu(poprz)}">← {e(poprz["strony"][0]["krotko"])} – {e(poprz["strony"][1]["krotko"])}</a>'
                if nast:
                    nawig += f'<a href="{p}{S.adres_meczu(nast)}">{e(nast["strony"][0]["krotko"])} – {e(nast["strony"][1]["krotko"])} →</a>'
                nawig += "</nav>"
                return f"""
{ld}
<header class="plakat mstr__plakat{' mstr__plakat--wyjazd' if not m['u_siebie'] else ''}"><div class="kontener">
  <p class="plakat__nad">{'Mecz u siebie' if m['u_siebie'] else 'Mecz wyjazdowy'} · {e(liga)}</p>
  <h1 class="plakat__tytul plakat__tytul--artykul">{e(gosp['nazwa'])} <span>– {e(gosc['nazwa'])}</span></h1>
  {wynik_html}
  {S.sety_html(m) if rozegrany else ''}
  {f'<p class="mstr__mvp">MVP: <strong>{S.link_zawodniczki(p, m["mvp"])}</strong></p>' if m.get('mvp') else ''}
</div></header>
<section class="sekcja"><div class="kontener uklad-2">
  <div class="artykul__tresc"><h2 class="pm__h2">{'Po meczu' if rozegrany else 'Zapowiedź'}</h2><p>{o_meczu}</p>{rywal_vb}
    <div class="przyciski-cta">{''.join(guziki)}</div>{grafika}</div>
  <dl class="pm__fakty mstr__fakty">{fakty_html}</dl>
</div></section>
{przed}
<section class="sekcja sekcja--biala"><div class="kontener">{nawig}
  <p><a class="sekcja__link" href="{p}terminarz.html">← Cały terminarz i tabela</a></p></div></section>"""

            self.strona(adres, tytul, opis, tresc, aktywna="terminarz.html", pelny=pelny)

    def filtry_miejsca(self):
        przyciski = "".join(
            f'<button class="filtr" aria-pressed="{"true" if w == "wszystkie" else "false"}" data-klucz="miejsce" data-wartosc="{w}">{n}</button>'
            for w, n in (("wszystkie", "Wszystkie"), ("dom", "U siebie"), ("wyjazd", "Wyjazdowe")))
        return f'<div class="filtry filtry--miejsce" role="group" aria-label="Pokaż mecze">{przyciski}</div>'

    def filtry_druzyn(self):
        druzyny = sorted({m["druzyna"] for m in self.mecze}, key=lambda d: list(C.DRUZYNY).index(d) if d in C.DRUZYNY else 99)
        if len(druzyny) < 2:
            return ""
        przyciski = '<button class="filtr" aria-pressed="true" data-klucz="druzyna" data-wartosc="wszystkie">Wszystkie</button>'
        for d in druzyny:
            przyciski += (f'<button class="filtr" aria-pressed="false" data-klucz="druzyna" data-wartosc="{e(d)}">'
                          f'{e(C.DRUZYNY.get(d, {}).get("krotko", d))}</button>')
        return f'<div class="filtry" role="group" aria-label="Pokaż mecze drużyny">{przyciski}</div>'

    def sponsorzy_html(self, p, pelna=False):
        poziomy = [("tytularny", "Sponsor tytularny"), ("strategiczny", "Sponsorzy strategiczni"),
                   ("techniczny", "Partner techniczny"), ("partner", "Partnerzy")]
        bloki = ""
        for klucz, nazwa in poziomy:
            lista = [s for s in C.SPONSORZY.values() if s["poziom"] == klucz]
            if not lista:
                continue
            loga = ""
            for s in lista:
                wnetrze = S.img(p, s.get("logo"), s["nazwa"], "logo-sp__img") or f"<span>{e(s['nazwa'])}</span>"
                tag = (f'a href="{e(s["www"])}" target="_blank" rel="noopener" title="{e(s["nazwa"])}"'
                       if s.get("www") else f'div title="{e(s["nazwa"])}"')
                loga += f'<{tag} class="logo-sp">{wnetrze}</{tag.split()[0]}>'
            bloki += (f'<div class="poziom"><div class="poziom__nazwa">{nazwa}</div>'
                      f'<div class="loga loga--{klucz}">{loga}</div></div>')
        naglowek = "" if pelna else S.naglowek_sekcji("Sponsorzy", "", p + "sponsorzy.html", "Zostań sponsorem", id_="sp-tytul")
        return f'<section class="sponsorzy" aria-label="Sponsorzy"><div class="kontener">{naglowek}{bloki}</div></section>'

    # --- TERMINARZ I WYNIKI ---------------------------------------------
    def terminarz(self):
        def tresc(p):
            # Najpierw to, co przed nami (od najbliższego), potem wyniki (od najnowszego)
            przed = [m for m in self.mecze if not m.get("wynik") and m["data"] >= DZIS]
            po = sorted([m for m in self.mecze if m not in przed],
                        key=lambda m: (m["data"], m.get("godzina") or ""), reverse=True)
            karty_przed = "".join(S.karta_meczu(p, m) for m in przed) or '<p class="lista-pusta">Brak zaplanowanych meczów.</p>'
            karty_po = "".join(S.karta_meczu(p, m) for m in po) or '<p class="lista-pusta">Sezon jeszcze się nie zaczął.</p>'
            pobrano = (self.dane.get(GLOWNA) or {}).get("pobrano")
            info = ""
            if pobrano:
                t = datetime.fromisoformat(pobrano)
                info = (f'<p class="zrodlo">Terminarz i wyniki pobierane automatycznie z systemów WSMWZPS i PZPS. '
                        f'Ostatnia aktualizacja: {t.strftime("%d.%m.%Y, %H:%M")}.</p>')
            return f"""
{self.wydarzenia_ld()}
{S.plakat_podstrony(p, 'Terminarz i wyniki', C.DRUZYNY[GLOWNA]['liga'], 'terminarz')}
<nav class="skroty" aria-label="Na tej stronie"><div class="kontener">
  <a href="#nadchodzace">Nadchodzące</a><a href="#wyniki">Wyniki</a><a href="#tabela">Tabela</a><a href="#kalendarium">Kalendarium</a>
</div></nav>
<section class="sekcja" aria-labelledby="nadchodzace">
  <div class="kontener" data-filtrowanie>
    {S.naglowek_sekcji('Nadchodzące', 'mecze', id_='nadchodzace')}
    {S.prezentuje('terminarz', p)}
    {self.filtry_druzyn()}
    <div class="terminarz-pasek">{self.filtry_miejsca()}<a class="btn-kal" href="#w-telefonie"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3v3M17 3v3M4 9h16M5 6h14a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1Z"/></svg>Cały sezon w kalendarzu</a></div>
    <div class="mecze mecze--siatka">{karty_przed}</div>
    {S.subskrypcja_kalendarza(p, GLOWNA)}
    <h2 class="sekcja__tytul sekcja__tytul--drugi" id="wyniki">Wyniki</h2>
    <div class="mecze mecze--siatka">{karty_po}</div>
    {info}
  </div>
</section>
<section class="sekcja sekcja--biala" id="tabela" aria-labelledby="tabela-tytul">
  <div class="kontener">
    {S.naglowek_sekcji('Tabela', C.DRUZYNY[GLOWNA]['liga'], id_='tabela-tytul')}
    {S.prezentuje('tabela', p)}
    {S.tabela_html(p, self.tabela(), opis_druzyny, C.DRUZYNY[GLOWNA]['liga'], self.forma)}
  </div>
</section>
<section class="sekcja" id="kalendarium" aria-labelledby="kal-tytul">
  <div class="kontener">
    {S.naglowek_sekcji('Kalendarium', 'dzień po dniu', id_='kal-tytul')}
    <div class="kal" data-kalendarium>
      <div class="kal__gora">
        <button class="kal__nav" data-kal="poprzedni" aria-label="Poprzedni miesiąc">←</button>
        <h3 class="kal__miesiac" aria-live="polite"></h3>
        <button class="kal__nav" data-kal="nastepny" aria-label="Następny miesiąc">→</button>
      </div>
      <div class="filtry" role="group" aria-label="Pokaż w kalendarium">
        <button class="filtr filtr--mecz" aria-pressed="true" data-typ="mecz">Mecze</button>
        <button class="filtr filtr--trening" aria-pressed="true" data-typ="trening">Treningi Akademii</button>
        <button class="filtr filtr--wydarzenie" aria-pressed="true" data-typ="wydarzenie">Wydarzenia</button>
      </div>
      <div class="kal__siatka" role="group" aria-label="Kalendarz miesiąca"></div>
      <ol class="kal__lista"></ol>
      <noscript><p>Kalendarium wymaga JavaScriptu. Wszystkie mecze są w spisie powyżej.</p></noscript>
    </div>
    <script type="application/json" id="kalendarium-dane">{self.dane_kalendarium()}</script>
  </div>
</section>"""
        self.strona("terminarz.html", "Terminarz i wyniki",
                    "Terminarz, wyniki, tabela 2. ligi kobiet i kalendarium klubu Easy Wrap Volley Kobyłka.", tresc)

    def dane_kalendarium(self):
        zdarzenia = []
        for m in self.mecze:
            g, h = m["strony"]
            tytul = f"{g['krotko']} – {h['krotko']}" if h else g["krotko"]
            if m.get("wynik"):
                tytul += f" {m['wynik']}"
            zdarzenia.append({"d": m["data"].isoformat(), "g": m.get("godzina"), "typ": "mecz",
                              "t": tytul, "m": m.get("hala") or "", "w": not m["u_siebie"]})
        for w in C.WYDARZENIA:
            zdarzenia.append({"d": w["data"], "g": w.get("godzina"), "typ": "wydarzenie",
                              "t": w["tytul"], "m": w.get("miejsce") or ""})
        dni = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
        treningi = [{"dzien": dni.index(t["dzien"].lower()), "od": t["od"], "do": t["do"],
                     "t": f"Trening: {t['grupa']}", "m": t.get("hala") or ""}
                    for t in C.AKADEMIA.get("harmonogram", [])]
        dane = {"zdarzenia": zdarzenia, "treningi": treningi,
                "sezon_od": C.AKADEMIA.get("sezon_od"), "sezon_do": C.AKADEMIA.get("sezon_do"),
                "wolne": C.AKADEMIA.get("dni_wolne", [])}
        # „</” zamieniamy, żeby tekst nie zamknął przypadkiem znacznika <script>
        return json.dumps(dane, ensure_ascii=False).replace("</", "<\\/")

    # --- DRUŻYNY -----------------------------------------------------------
    def druzyny(self):
        def tresc(p):
            kadra = sorted([z for z in C.KADRA if z["druzyna"] == GLOWNA], key=lambda z: z["numer"])
            pozycje = [poz for poz in C.POZYCJE if any(z["pozycja"] == poz for z in kadra)]
            filtry = ('<div class="filtry" role="group" aria-label="Filtruj według pozycji">'
                      '<button class="filtr" aria-pressed="true" data-pozycja="wszystkie">Wszystkie</button>'
                      + "".join(f'<button class="filtr" aria-pressed="false" data-pozycja="{e(x)}">{e(x)}</button>' for x in pozycje)
                      + "</div>")
            sztab = "".join(
                f'<li class="osoba">{S.img(p, s.get("zdjecie"), s["imie"] + " " + s["nazwisko"], "osoba__foto") or f"<span class=osoba__inicjaly>{e(s["imie"][0] + s["nazwisko"][0])}</span>"}'
                f'<span class="osoba__rola">{e(s["funkcja"])}</span><strong>{e(s["imie"])} {e(s["nazwisko"])}</strong></li>'
                for s in C.SZTAB if s["druzyna"] == GLOWNA)
            dg = C.DRUZYNY[GLOWNA]
            return f"""
{S.plakat_podstrony(p, dg['nazwa'], dg['liga'], dg.get('zdjecie') or 'druzyny')}
<section class="sekcja" aria-labelledby="kadra-tytul">
  <div class="kontener">
    {S.naglowek_sekcji('Kadra', '2026/27', id_='kadra-tytul')}
    {S.prezentuje('kadra', p)}
    {filtry}
    <div class="kadra kadra--siatka" data-kadra>{''.join(S.karta_zawodniczki(p, z) for z in kadra)}</div>
  </div>
</section>
{f'''<section class="sekcja sekcja--biala" aria-labelledby="sztab-tytul"><div class="kontener">
  {S.naglowek_sekcji('Sztab', 'szkoleniowy', id_='sztab-tytul')}<ul class="osoby">{sztab}</ul></div></section>''' if sztab else ''}
"""
        self.strona("druzyny.html", "Drużyny", "Kadra drużyny Easy Wrap Volley Kobyłka – 2. liga kobiet.", tresc)

    # --- AKTUALNOŚCI -------------------------------------------------------
    def aktualnosci(self):
        def lista(p):
            karty = "".join(S.karta_newsa(p, n, i == 0) for i, n in enumerate(self.newsy))
            return f"""
{S.plakat_podstrony(p, 'Aktualności', 'Z życia klubu', 'aktualnosci')}
<section class="sekcja"><div class="kontener"><div class="newsy newsy--wszystkie">{karty}</div></div></section>"""
        self.strona("aktualnosci.html", "Aktualności", "Aktualności klubu Easy Wrap Volley Kobyłka.", lista)

        for i, n in enumerate(self.newsy):
            def artykul(p, n=n, i=i):
                d = date.fromisoformat(n["data"])
                # Zdjęcie newsa jest tłem nagłówka artykułu
                foto = S.img(p, n.get("zdjecie"), n["tytul"], "plakat__foto-img", lazy=False)
                inne = [x for x in self.newsy if x is not n][:2]
                return f"""
<article class="artykul">
  <header class="plakat{' plakat--z-foto' if foto else ''}">
    {f'<div class="plakat__tlo">{foto}</div>' if foto else ''}
    <div class="kontener">
    <p class="plakat__nad">{e(n['kategoria'])} · <time datetime="{d.isoformat()}">{e(S.data_pl(d))}</time></p>
    <h1 class="plakat__tytul plakat__tytul--artykul">{e(n['tytul'])}</h1></div></header>
  <div class="kontener artykul__kontener">
    {f'<p class="artykul__zajawka">{e(n["zajawka"])}</p>' if n.get('zajawka') and n.get('zrodlo') != 'fb' else ''}
    <div class="artykul__tresc">{S.podlinkuj_zawodniczki(p, S.akapity_fb(n['tresc']) if n.get('zrodlo') == 'fb' else S.akapity(n['tresc']))}</div>
    {''.join(f'<p><a class="btn btn--obrys" href="{p}{S.adres_meczu(m)}">Wynik i szczegóły meczu →</a></p>' for m in self.mecze if m.get('relacja') == n['adres'] and S.adres_meczu(m))}
    {S.przycisk_fb(n)}
    <p><a class="sekcja__link" href="{p}aktualnosci.html">← Wszystkie aktualności</a></p>
  </div>
</article>
<section class="sekcja sekcja--biala"><div class="kontener">
  {S.naglowek_sekcji('Czytaj', 'też')}
  <div class="newsy">{''.join(S.karta_newsa(p, x) for x in inne)}</div></div></section>"""
            baza = C.KLUB["adres_strony"].rstrip("/") + "/"
            obraz_n = ("img/" + n["zdjecie"]) if n.get("zdjecie") and S.jest_plik(n["zdjecie"]) else None
            DODATKI_SEO[f"aktualnosci/{n['adres']}.html"] = {
                "obraz": obraz_n, "typ": "article", "data": n["data"], "obrazy": [obraz_n] if obraz_n else [],
                "ld": [{"@context": "https://schema.org", "@type": "NewsArticle", "headline": n["tytul"][:110],
                        "datePublished": n["data"], "dateModified": n["data"],
                        "image": [baza + (obraz_n or "img/og-klub.jpg")],
                        "author": {"@type": "SportsOrganization", "name": C.KLUB["nazwa"], "url": baza},
                        "publisher": {"@type": "Organization", "name": C.KLUB["nazwa_prawna"] + " Kobyłka",
                                      "logo": {"@type": "ImageObject", "url": baza + "img/favicon-512.png"}},
                        "mainEntityOfPage": baza + f"aktualnosci/{n['adres']}.html",
                        "about": {"@type": "SportsTeam", "name": C.KLUB["nazwa"]}}]}
            self.strona(f"aktualnosci/{n['adres']}.html", n["tytul"], n.get("zajawka") or n["tytul"],
                        artykul, aktywna="aktualnosci.html")

    # --- AKADEMIA (osobna część strony) ------------------------------------
    def akademia(self):
        A = C.AKADEMIA
        p = ""
        grupy = "".join(
            f'<article class="grupa"><span class="grupa__wiek">{e(g["wiek"])}</span><h3>{e(g["nazwa"])}</h3><p>{e(g["opis"])}</p></article>'
            for g in A["grupy"])
        def karta_trenera(t):
            imie = f'{t["imie"]} {t["nazwisko"]}'
            z = S.zawodniczka_po_nazwisku(imie)
            profil = (f'<a class="ak-trener__link" href="{p}{S.adres_profilu(z)}">Profil zawodniczki →</a>'
                      if z and S.adres_profilu(z) else "")
            foto = (S.img(p, t.get("zdjecie"), imie, "ak-trener__img")
                    or f'<span class="ak-trener__inicjaly">{e(t["imie"][0] + t["nazwisko"][0])}</span>')
            return (f'<article class="ak-trener"><div class="ak-trener__foto">{foto}</div>'
                    f'<div class="ak-trener__opis"><span class="ak-trener__rola">{e(t.get("rola") or "Trener")}</span>'
                    f'<h3>{e(imie)}</h3><p>{e(t.get("opis") or "")}</p>{profil}</div></article>')
        trenerzy = "".join(karta_trenera(t) for t in A["trenerzy"])
        dni = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
        plan = sorted(A["harmonogram"], key=lambda t: (dni.index(t["dzien"].lower()), t["od"]))
        wiersze_planu = "".join(
            f'<tr><td>{e(t["dzien"].capitalize())}</td><td>{e(t["od"])}–{e(t["do"])}</td><td>{e(t["grupa"])}</td><td>{e(t.get("hala") or "")}</td></tr>'
            for t in plan)
        if wiersze_planu:
            plan_html = f"""<div class="tabela-ramka"><table class="tabela tabela--harmonogram">
        <caption class="ukryte">Plan treningów Akademii</caption>
        <thead><tr><th scope="col">Dzień</th><th scope="col">Godziny</th><th scope="col">Grupa</th><th scope="col">Miejsce</th></tr></thead>
        <tbody>{wiersze_planu}</tbody></table></div>"""
        else:
            plan_html = ('<div class="ak-info"><strong>Plan na sezon 2026/27 – wkrótce</strong>'
                         '<p>Godziny treningów dopasowujemy do grup po zapisie. Napisz do nas – odpowiemy z wolnymi miejscami i godzinami.</p></div>')
        temat = quote("Zapis do Akademii Siatkówki Volley")
        mail = (A.get("koordynator") or {}).get("email") or C.KLUB["email"]
        if A.get("formularz_google"):
            link = A["formularz_google"]
            osadz = link + ("&" if "?" in link else "?") + "embedded=true"
            formularz = f"""
<div class="formularz">
  <a class="btn btn--ak" href="{e(link)}" rel="noopener" target="_blank">Wypełnij formularz zgłoszeniowy ↗</a>
  <button class="btn btn--obrys" data-formularz="{e(osadz)}">Pokaż formularz tutaj</button>
  <p class="formularz__info">Formularz Google wczyta się dopiero po kliknięciu (Google może wtedy zapisać cookies).</p>
</div>"""
        else:
            formularz = (f'<div class="formularz"><a class="btn btn--ak" href="mailto:{e(mail)}?subject={temat}">'
                         f'Wyślij zgłoszenie e-mailem →</a>'
                         f'<p class="formularz__info">W wiadomości podaj imię córki, rok urodzenia i telefon do rodzica.</p></div>')
        cennik = "".join(f'<li class="ak-cena"><span>{e(c["co"])}</span><strong>{e(c["cena"])}</strong></li>' for c in A.get("cennik", []))
        fakty = "".join(f"<li>{e(x)}</li>" for x in A.get("fakty", []))
        k = A.get("koordynator") or {}
        kontakt = ""
        if k.get("imie"):
            kontakt += f'<p class="ak-osoba">{e(k["imie"])}</p>'
        if k.get("telefon"):
            kontakt += f'<a class="ak-kontakt__duzy" href="tel:{S.tel_link(k["telefon"])}">{e(k["telefon"])}</a>'
        if k.get("email"):
            kontakt += f'<a class="ak-kontakt__mail" href="mailto:{e(k["email"])}">{e(k["email"])}</a>'
        fb = (f'<a class="btn btn--fb" href="{e(A["facebook"])}" target="_blank" rel="noopener">Akademia na Facebooku ↗</a>'
              if A.get("facebook") else "")
        logo = (f'<img class="ak-hero__logo" src="img/{e(A["logo"])}" alt="Logo Akademii Siatkówki Volley" width="320" height="320">'
                if S.jest_plik(A.get("logo")) else "")
        om = A["ochrona_maloletnich"]
        dokument = f'<a class="btn btn--obrys" href="img/{e(om["dokument"])}">Pełne Standardy Ochrony Małoletnich (PDF)</a>' if S.jest_plik(om.get("dokument")) else ""
        punkty = "".join(f"<li>{e(x)}</li>" for x in om.get("dla_dzieci") or [])
        dla_dzieci = (f"""<div class="ochrona__dzieci">
        <h3>Wersja dla dzieci – Twoje prawa w Klubie</h3>
        <ul>{punkty}</ul>
        <p class="ochrona__telefon">Możesz też zadzwonić bezpłatnie i anonimowo: <strong>Telefon Zaufania dla Dzieci i Młodzieży
          <a href="tel:116111">116 111</a></strong> (całą dobę).</p>
      </div>""" if punkty else "")
        na = self.newsy_akademii
        karty_ak = "".join(S.karta_newsa("", n, i == 0, "akademia-aktualnosci", A.get("logo") or "favicon.svg")
                           for i, n in enumerate(na[:7]))
        wiecej_fb = (f'<p class="ak-przypis"><a href="{e(A["facebook"])}" rel="noopener" target="_blank">'
                     f'Więcej na Facebooku Akademii ↗</a></p>' if A.get("facebook") else "")
        sekcja_aktualnosci = (f"""<section class="sekcja ak-sekcja" id="aktualnosci" aria-labelledby="ak-news-tytul">
  <div class="kontener">
    <h2 class="ak-h2" id="ak-news-tytul">Aktualności</h2>
    <div class="newsy newsy--wszystkie">{karty_ak}</div>
    {wiecej_fb}
  </div>
</section>""" if na else "")
        mapa = C.HALA_DOMOWA.get("mapa")
        sekcja_grupy = (f'<div class="grupy pojaw">{grupy}</div>' if grupy else "")
        tresc = f"""
<section class="ak-hero" id="o-akademii" aria-labelledby="ak-tytul">
  <div class="kontener ak-hero__uklad">
    <div>
      <p class="ak-nad">Akademia Siatkówki Volley · Kobyłka</p>
      <h1 class="ak-tytul" id="ak-tytul">{e(A['haslo'])}</h1>
      <p class="ak-opis">{e(A['opis'])}</p>
      <ul class="ak-fakty">{fakty}</ul>
      <div class="ak-przyciski"><a class="btn btn--ak" href="#zapisy">Zapisz córkę →</a>
        <a class="btn btn--obrys btn--jasny" href="#grupa">Darmowy trening próbny</a></div>
    </div>
    {logo}
  </div>
  {f'<div class="kontener">{sekcja_grupy}</div>' if sekcja_grupy else ''}
</section>

{self.ak_dlaczego(A)}
{self.ak_wybor_klasy(A)}
<section class="sekcja ak-sekcja" id="cennik" aria-labelledby="cennik-tytul">
  <div class="kontener">
    <h2 class="ak-h2" id="cennik-tytul">Cennik</h2>
    <ul class="ak-ceny">{cennik}</ul>
    <p class="ak-przypis">Opłata miesięczna.</p>
  </div>
</section>

<section class="sekcja ak-sekcja ak-sekcja--biala" id="plan" aria-labelledby="plan-tytul">
  <div class="kontener">
    <h2 class="ak-h2" id="plan-tytul">Plan treningów</h2>
    {plan_html}
    <p class="ak-przypis">Treningi w hali przy PSP nr 3 w Kobyłce, ul. Załuskiego 57. Trening trwa 90 minut.</p>
  </div>
</section>
{f"""
<section class="sekcja ak-sekcja" id="trenerzy" aria-labelledby="trenerzy-tytul">
  <div class="kontener">
    <h2 class="ak-h2" id="trenerzy-tytul">Trenerzy</h2>
    <div class="ak-trenerzy">{trenerzy}</div>
  </div>
</section>""" if trenerzy else ''}
<section class="sekcja ak-sekcja ak-sekcja--biala" id="sciezka" aria-labelledby="sciezka-tytul">
  <div class="kontener">
    <h2 class="ak-h2" id="sciezka-tytul">Ścieżka rozwoju</h2>
    <p class="ak-wstep">Od pierwszego odbicia do meczu ligowego – w jednym klubie, w Kobyłce.</p>
    <ol class="ak-sciezka">
      <li><span class="ak-sciezka__nr">1</span><h3>Pierwsze odbicia</h3>
        <p>Nauka podstaw przez zabawę: odbicia, ruch na boisku i współpraca w drużynie. Zaczynamy od zera – wystarczą chęci.</p></li>
      <li><span class="ak-sciezka__nr">2</span><h3>Minisiatkówka</h3>
        <p>Gra w mniejszych składach na małym boisku. Więcej kontaktów z piłką, pierwsze mecze i pierwsza drużynowa radość.</p></li>
      <li class="ak-sciezka__cel"><span class="ak-sciezka__nr">3</span><h3>2. liga kobiet</h3>
        <p>Na końcu drogi czeka pierwsza drużyna klubu – {e(C.KLUB['nazwa'])}. Zajęcia Akademii prowadzi jej zawodniczka,
        więc dziewczynki na co dzień widzą, dokąd mogą dojść.</p>
        <a class="ak-sciezka__link" href="{S.START_DRUZYNY}">Poznaj drużynę →</a></li>
    </ol>
  </div>
</section>

<section class="sekcja ak-sekcja" id="zapisy" aria-labelledby="zapisy-tytul">
  <div class="kontener">
    <h2 class="ak-h2" id="zapisy-tytul">Zapisy</h2>
    <ol class="ak-kroki">
      <li><strong>{'Wypełnij formularz' if A.get('formularz_google') else 'Wyślij zgłoszenie'}</strong><span>Imię i rok urodzenia córki, kontakt do rodzica.</span></li>
      <li><strong>Odpowiemy</strong><span>Potwierdzimy miejsce i termin pierwszego treningu.</span></li>
      <li><strong>Przyjdź na trening</strong><span>Umowę uczestnictwa podpisujemy na miejscu, w hali.</span></li>
    </ol>
    {formularz}
    <div class="formularz__ramka" data-formularz-ramka></div>
    <details class="ak-rodo">
      <summary>Kto przetwarza dane ze zgłoszenia? (RODO)</summary>
      <p>Administratorem danych podanych w zgłoszeniu (dane rodzica i dziecka) jest {e(C.KLUB['nazwa_prawna'])}, {e(C.KLUB['adres'])},
      e-mail: <a href="mailto:{e(C.KLUB['email'])}">{e(C.KLUB['email'])}</a>. Dane wykorzystujemy, aby odpowiedzieć na zgłoszenie,
      przydzielić grupę i zawrzeć umowę uczestnictwa (art. 6 ust. 1 lit. b RODO), a także do kontaktu w sprawach zajęć (art. 6 ust. 1 lit. f RODO).
      Podanie danych jest dobrowolne, ale bez nich nie zapiszemy dziecka. Jeśli dziecko nie dołączy do zajęć, usuwamy zgłoszenie po zakończeniu sezonu.
      Masz prawo dostępu do danych, ich sprostowania, usunięcia, ograniczenia przetwarzania, sprzeciwu oraz skargi do Prezesa UODO.
      Więcej: <a href="polityka-prywatnosci.html">Polityka prywatności</a>.</p>
    </details>
  </div>
</section>

{sekcja_aktualnosci}
{self.ak_poradnik_sekcja()}
<section class="sekcja ak-sekcja ak-sekcja--biala" id="kontakt" aria-labelledby="kontakt-tytul">
  <div class="kontener ak-kontakt">
    <div>
      <h2 class="ak-h2" id="kontakt-tytul">Kontakt</h2>
      <p class="ak-rola">{e(k.get('rola') or 'Koordynator Akademii')}</p>
      {kontakt}
      <p class="ak-kontakt__tekst">Masz pytanie o zajęcia, wolne miejsca albo trening próbny? {'Zadzwoń, napisz e-mail' if k.get('telefon') else 'Napisz e-mail'}
      albo wiadomość prywatną na Facebooku Akademii.</p>
      <div class="ak-przyciski">{f'<a class="btn btn--ak" href="tel:{S.tel_link(k["telefon"])}">Zadzwoń →</a>' if k.get('telefon') else ''}{f'<a class="btn btn--obrys" href="mailto:{e(mail)}?subject={quote("Pytanie o Akademię Siatkówki Volley")}">Napisz e-mail</a>' if mail else ''}{fb}</div>
    </div>
    <div class="ak-karta">
      <h3>Gdzie trenujemy</h3>
      <p>Hala przy PSP nr 3 w Kobyłce<br>ul. Załuskiego 57, 05-230 Kobyłka</p>
      {f'<a class="btn btn--ak" href="{e(mapa)}" rel="noopener" target="_blank">Pokaż na mapie →</a>' if mapa else ''}
      {self.ak_dojazd()}
    </div>
  </div>
</section>

<section class="sekcja sekcja--ochrona" id="ochrona" aria-labelledby="ochrona-tytul">
  <div class="kontener ochrona">
    <div class="ochrona__ikona" aria-hidden="true">
      <svg viewBox="0 0 60 70"><path d="M30 2 56 10v24c0 17-11 28-26 34C15 62 4 51 4 34V10Z" fill="none" stroke="currentColor" stroke-width="4"/><path d="m18 36 9 9 16-18" fill="none" stroke="currentColor" stroke-width="5"/></svg>
    </div>
    <div>
      <h2 class="sekcja__tytul" id="ochrona-tytul">Bezpieczeństwo <span>dzieci</span></h2>
      <p>{e(om['tekst'])}</p>
      <p>Kontakt w sprawie standardów: <a href="mailto:{e(om['osoba_kontaktowa'])}">{e(om['osoba_kontaktowa'])}</a></p>
      {dokument}
      {dla_dzieci}
    </div>
  </div>
</section>"""
        pytania_ak = self.faq_akademii()
        DODATKI_SEO["akademia.html"] = {"ld": [S.faq_ld(pytania_ak)]}
        tresc = tresc + S.faq_html(pytania_ak, "Pytania", "rodziców", "faq--akademia")
        cel_zapisu = (f'href="{e(A["formularz_google"])}" rel="noopener" target="_blank"' if A.get("formularz_google")
                      else 'href="#zapisy"')
        tel = (A.get("koordynator") or {}).get("telefon")
        tresc += (f'<nav class="ak-pasek" aria-label="Szybkie zapisy"><a class="ak-pasek__zapis" {cel_zapisu}>Zapisz córkę →</a>'
                  + (f'<a class="ak-pasek__tel" href="tel:{S.tel_link(tel)}" aria-label="Zadzwoń: {e(tel)}">'
                     '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path fill="currentColor" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z"/></svg>Zadzwoń</a>'
                     if tel else '<a class="ak-pasek__plan" href="#plan">Plan treningów</a>')
                  + '</nav>')
        html = S.uklad_akademii("Akademia Siatkówki Volley Kobyłka – siatkówka dla dziewcząt i dzieci",
                                "Siatkówka dla dziewcząt z klas 3–6 SP w Kobyłce (blisko Wołomina, Marek i Zielonki) – "
                                "Akademia Siatkówki Volley. Wtorki i czwartki 16:15–17:45. Cennik i zapisy online.",
                                tresc, p, self.wersja, aktualnosci=bool(na))
        zapisz("akademia.html", html)

        # Podstrony aktualności Akademii (z postów FB)
        herb_ak = A.get("logo") or "favicon.svg"
        for n in na:
            pp = "../"
            foto = S.img(pp, n.get("zdjecie"), n["tytul"], "plakat__foto-img", lazy=False)
            d = date.fromisoformat(n["data"])
            inne = "".join(S.karta_newsa(pp, x, False, "akademia-aktualnosci", herb_ak) for x in [x for x in na if x is not n][:2])
            czytaj = (f'<section class="sekcja ak-sekcja"><div class="kontener"><h2 class="ak-h2">Czytaj też</h2>'
                      f'<div class="newsy">{inne}</div></div></section>' if inne else "") + self.ak_poradnik_sekcja(pp)
            naglowek = f'<div class="plakat__tlo">{foto}</div>' if foto else ""
            tekst_art, zrodlo = S.oczysc_post_akademii(S.akapity_fb(n['tresc']))
            zrodlo_html = (f'<aside class="art-zrodla"><h2>Źródło</h2><p>{zrodlo}</p></aside>' if zrodlo else "")
            sciezka_n = f"akademia-aktualnosci/{n['adres']}.html"
            obraz_n = S.src_img("", n.get("zdjecie")).split("?")[0] if n.get("zdjecie") and S.img("", n.get("zdjecie"), "", "") else None
            DODATKI_SEO[sciezka_n] = {"typ": "article", "data": n["data"], "obraz": obraz_n,
                                      "ld": [self.ak_artykul_ld(sciezka_n, n["tytul"], n.get("zajawka") or n["tytul"],
                                                                n["data"], obraz_n, None,
                                                                [re.sub(r"<[^>]+>", "", zrodlo)] if zrodlo else [])]}
            tresc_n = f"""
<article class="artykul artykul--akademia">
  <header class="plakat{' plakat--z-foto' if foto else ''}">
    {naglowek}
    <div class="kontener">
    <p class="plakat__nad">Akademia · <time datetime="{d.isoformat()}">{e(S.data_pl(d))}</time></p>
    <h1 class="plakat__tytul plakat__tytul--artykul">{e(n['tytul'])}</h1></div></header>
  <div class="kontener artykul__kontener">
    <div class="artykul__tresc">{tekst_art}</div>
    {zrodlo_html}
    {self.ak_ramka_zapisow(A, pp)}
    {S.przycisk_fb(n)}
    <p><a class="sekcja__link" href="{pp}akademia.html#aktualnosci">← Wszystkie aktualności Akademii</a></p>
  </div>
</article>
{czytaj}"""
            zapisz(f"akademia-aktualnosci/{n['adres']}.html",
                   S.uklad_akademii(f"{n['tytul']} – Akademia Siatkówki Volley", n.get("zajawka") or n["tytul"],
                                    tresc_n, pp, self.wersja, aktualnosci=True))


    # --- AKADEMIA: dodatkowe sekcje -------------------------------------------
    def ak_dlaczego(self, A):
        k = A.get("koordynator") or {}
        tr = (A.get("trenerzy") or [{}])[0]
        kafle = [
            ("dom", "Blisko domu", "Treningi w Kobyłce, w hali przy PSP nr 3 – bez dowożenia córki do innego miasta."),
            ("serce", "Tylko dla dziewcząt", "Grupa dziewcząt z klas 3–6 SP. Trening dopasowany do ich wieku i poziomu."),
            ("cena", "Jasny cennik", "Ceny podajemy wprost na stronie – wiesz, ile zapłacisz, zanim zapiszesz córkę."),
            ("pilka", "Trenerka z 2. ligi",
             f'Zajęcia prowadzi {e(tr.get("imie", ""))} {e(tr.get("nazwisko", ""))} – zawodniczka drużyny grającej w 2. lidze kobiet.'
             if tr.get("imie") else "Zajęcia prowadzą osoby związane z drużyną grającą w 2. lidze kobiet."),
            ("tarcza", "Bezpiecznie", 'Stosujemy <a href="#ochrona">Standardy Ochrony Małoletnich</a> – znasz zasady, które chronią Twoje dziecko.'),
            ("start", "Darmowy trening próbny", "Pierwszy trening jest bezpłatny – córka sprawdzi, czy siatkówka jej się podoba."),
        ]
        ikony = {
            "dom": '<path d="M3 11.5 12 4l9 7.5M5.5 9.5V20h13V9.5"/><path d="M10 20v-5h4v5"/>',
            "serce": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10Z"/>',
            "cena": '<path d="M4 12V5a1 1 0 0 1 1-1h7l8 8-8 8-8-8Z"/><circle cx="8.5" cy="8.5" r="1.5"/>',
            "pilka": '<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5c-2 3-2 6 0 8.5s2 5.5 0 8.5M4 9c3.5 1 7 .5 8 3M20 9c-3 1.5-5 3.5-8 3"/>',
            "tarcza": '<path d="M12 3 5 6v5.5c0 4.3 3 7.7 7 9.5 4-1.8 7-5.2 7-9.5V6l-7-3Z"/><path d="m9 12 2 2 4-4"/>',
            "start": '<path d="M5 12h12M13 7l5 5-5 5"/>',
        }
        html = "".join(
            f'<li class="ak-why__kafel"><svg viewBox="0 0 24 24" aria-hidden="true">{ikony[i]}</svg>'
            f'<h3>{t}</h3><p>{o}</p></li>' for i, t, o in kafle)
        return f"""
<section class="sekcja ak-sekcja ak-sekcja--biala" id="dlaczego" aria-labelledby="dlaczego-tytul">
  <div class="kontener">
    <h2 class="ak-h2" id="dlaczego-tytul">Dlaczego Akademia Volley</h2>
    <ul class="ak-why">{html}</ul>
  </div>
</section>"""

    def ak_wybor_klasy(self, A):
        """„W której klasie jest córka?” – po wyborze klasy pokazuje grupę, dni, godziny, cenę i przyciski."""
        grupy = A.get("grupy_klasy") or []
        if not grupy:
            return ""
        k = A.get("koordynator") or {}
        mail = k.get("email") or C.KLUB["email"]
        tel = k.get("telefon")
        form = A.get("formularz_google")
        ceny = " lub ".join(f'{e(c["cena"])} ({e(c["co"])})' for c in A.get("cennik", []))
        klasy = list(range(1, 9))
        radia = "".join(f'<input type="radio" name="klasa" id="kl-{n}" class="ak-klasa__radio" value="{n}">'
                        f'<label for="kl-{n}" class="ak-klasa__chip">{n}</label>' for n in klasy)
        panele = ""
        for g in grupy:
            dni = [t for t in A.get("harmonogram", []) if t.get("grupa") == g["nazwa"]]
            plan = "".join(f'<li><b>{e(t["dzien"].capitalize())}</b> {e(t["od"])}–{e(t["do"])}</li>' for t in dni)
            temat = quote("Trening próbny – Akademia Siatkówki Volley")
            tresc_maila = quote("Dzień dobry,\nchciał(a)bym umówić córkę na darmowy trening próbny.\n\n"
                                "Imię córki:\nKlasa:\nTelefon do rodzica:\n")
            przyciski = (f'<a class="btn btn--ak" href="{e(form)}" rel="noopener" target="_blank">Zapisz córkę →</a>' if form else
                         '<a class="btn btn--ak" href="#zapisy">Zapisz córkę →</a>')
            przyciski += f'<a class="btn btn--obrys" href="mailto:{e(mail)}?subject={temat}&amp;body={tresc_maila}">Umów trening próbny</a>'
            if tel:
                przyciski += f'<a class="btn btn--obrys" href="tel:{S.tel_link(tel)}">Zadzwoń: {e(tel)}</a>'
            panele += (f'<div class="ak-klasa__panel" data-dla="{" ".join(str(x) for x in g["klasy"])}">'
                       f'<p class="ak-klasa__nad">Grupa dla Twojej córki</p><h3>{e(g["nazwa"])}</h3>'
                       f'<ul class="ak-klasa__plan">{plan}</ul>'
                       f'<p class="ak-klasa__info">Hala przy PSP nr 3 w Kobyłce, ul. Załuskiego 57 · trening trwa 90 minut · {ceny}.</p>'
                       f'<p class="ak-klasa__proba">Pierwszy trening jest <b>bezpłatny</b>.</p>'
                       f'<div class="ak-przyciski">{przyciski}</div></div>')
        obslugiwane = {x for g in grupy for x in g["klasy"]}
        inne = " ".join(str(n) for n in klasy if n not in obslugiwane)
        kontakt = (f'<a class="btn btn--ak" href="tel:{S.tel_link(tel)}">Zadzwoń: {e(tel)}</a>' if tel else "") + \
                  f'<a class="btn btn--obrys" href="mailto:{e(mail)}?subject={quote("Pytanie o grupę – Akademia Siatkówki Volley")}">Napisz e-mail</a>'
        panele += (f'<div class="ak-klasa__panel ak-klasa__panel--brak" data-dla="{inne}">'
                   '<h3>Na razie nie mamy grupy dla tej klasy</h3>'
                   '<p>Zadzwoń albo napisz – porozmawiamy o możliwościach i damy znać, gdy pojawi się grupa dla córki.</p>'
                   f'<div class="ak-przyciski">{kontakt}</div></div>')
        css = "".join(f'.ak-klasa:has(#kl-{n}:checked) .ak-klasa__panel[data-dla~="{n}"]{{display:block}}' for n in klasy)
        css += "".join(f'.ak-klasa:has(#kl-{n}:checked) label[for="kl-{n}"]{{background:#1C6FD1;color:#fff;border-color:#1C6FD1}}' for n in klasy)
        return f"""
<section class="sekcja ak-sekcja" id="grupa" aria-labelledby="grupa-tytul">
  <div class="kontener">
    <h2 class="ak-h2" id="grupa-tytul">Sprawdź grupę dla córki</h2>
    <style>{css}</style>
    <div class="ak-klasa">
      <fieldset class="ak-klasa__wybor"><legend>W której klasie jest córka?</legend><div class="ak-klasa__chipy">{radia}</div></fieldset>
      <p class="ak-klasa__podpowiedz">Wybierz klasę, a pokażemy grupę, dni i godziny treningów.</p>
      {panele}
    </div>
  </div>
</section>"""

    def ak_dojazd(self):
        cel = quote("ul. ks. Marcina Załuskiego 57, 05-230 Kobyłka")
        miasta = [("Wołomin", "Wołomina"), ("Zielonka", "Zielonki"), ("Marki", "Marek"), ("Radzymin", "Radzymina"),
                  ("Warszawa Targówek", "Warszawy (Targówek)")]
        linki = "".join(f'<li><a href="https://www.google.com/maps/dir/?api=1&amp;origin={quote(m)}&amp;destination={cel}" '
                        f'rel="noopener" target="_blank">z {e(d)} →</a></li>' for m, d in miasta)
        return f'<h3 class="ak-dojazd__tytul">Dojazd z okolicy</h3><ul class="ak-dojazd">{linki}</ul>'

    def ak_poradnik_sekcja(self, p=""):
        karty = "".join(
            f'<li class="ak-poradnik__karta"><a href="{p}akademia-poradnik/{x["adres"]}.html">'
            f'<span class="ak-poradnik__nad">Poradnik</span><h3>{e(x["tytul"])}</h3><p>{e(x["zajawka"])}</p>'
            f'<span class="ak-poradnik__czytaj">Czytaj →</span></a></li>' for x in PR.PORADNIKI)
        return f"""
<section class="sekcja ak-sekcja ak-sekcja--biala" id="poradnik" aria-labelledby="poradnik-tytul">
  <div class="kontener">
    <h2 class="ak-h2" id="poradnik-tytul">Poradnik dla rodziców</h2>
    <ul class="ak-poradnik">{karty}</ul>
  </div>
</section>"""

    def ak_ramka_zapisow(self, A, p):
        k = A.get("koordynator") or {}
        tel = k.get("telefon")
        form = A.get("formularz_google")
        fakty = " · ".join(e(x) for x in A.get("fakty", [])[:2])
        przyciski = (f'<a class="btn btn--ak" href="{e(form)}" rel="noopener" target="_blank">Zapisz córkę →</a>' if form
                     else f'<a class="btn btn--ak" href="{p}akademia.html#zapisy">Zapisz córkę →</a>')
        przyciski += f'<a class="btn btn--obrys" href="{p}akademia.html#grupa">Darmowy trening próbny</a>'
        if tel:
            przyciski += f'<a class="btn btn--obrys" href="tel:{S.tel_link(tel)}">Zadzwoń: {e(tel)}</a>'
        return (f'<aside class="ak-ramka"><p class="ak-ramka__nad">Akademia Siatkówki Volley · Kobyłka</p>'
                f'<h2>Zapisz córkę na siatkówkę</h2><p>{fakty}. Hala przy PSP nr 3 w Kobyłce, ul. Załuskiego 57.</p>'
                f'<div class="ak-przyciski">{przyciski}</div></aside>')

    def ak_artykul_ld(self, sciezka, tytul, opis, data_iso, obraz, autor=None, zrodla=()):
        baza = C.KLUB["adres_strony"].rstrip("/") + "/"
        A = C.AKADEMIA
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": tytul[:110], "description": opis,
              "datePublished": data_iso, "dateModified": data_iso, "inLanguage": "pl-PL",
              "mainEntityOfPage": baza + sciezka,
              "publisher": {"@type": "SportsOrganization", "name": A.get("nazwa") or "Akademia Siatkówki Volley",
                            "url": baza + "akademia.html"},
              "author": ({"@type": "Person", "name": autor["imie"], "description": autor["opis"]} if autor else
                         {"@type": "SportsOrganization", "name": A.get("nazwa") or "Akademia Siatkówki Volley",
                          "url": baza + "akademia.html"})}
        if obraz:
            ld["image"] = baza + obraz
        if zrodla:
            ld["citation"] = [z[0] if isinstance(z, (list, tuple)) else z for z in zrodla]
        return ld

    def poradniki(self):
        A = C.AKADEMIA
        pp = "../"
        for x in PR.PORADNIKI:
            d = date.fromisoformat(x["data"])
            zrodla = "".join(f'<li>{e(t)}' + (f' – <a href="{e(u)}" rel="noopener" target="_blank">link</a>' if u else "") + '</li>'
                             for t, u in x.get("zrodla", []))
            inne = "".join(f'<li><a href="{y["adres"]}.html">{e(y["tytul"])}</a></li>' for y in PR.PORADNIKI if y is not x)
            tresc = f"""
<article class="artykul artykul--akademia artykul--poradnik">
  <header class="plakat"><div class="kontener">
    <p class="plakat__nad">Poradnik dla rodziców · <time datetime="{d.isoformat()}">{e(S.data_pl(d))}</time></p>
    <h1 class="plakat__tytul plakat__tytul--artykul">{e(x['tytul'])}</h1></div></header>
  <div class="kontener artykul__kontener">
    <div class="artykul__tresc">{x['tresc']}</div>
    {f'<aside class="art-zrodla"><h2>Źródła</h2><ol>{zrodla}</ol></aside>' if zrodla else ''}
    {self.ak_ramka_zapisow(A, pp)}
    <nav class="art-inne" aria-label="Inne poradniki"><h2>Inne poradniki</h2><ul>{inne}</ul></nav>
    <p><a class="sekcja__link" href="{pp}akademia.html#poradnik">← Wszystkie poradniki</a></p>
  </div>
</article>"""
            sciezka = f"akademia-poradnik/{x['adres']}.html"
            obraz = A.get("og_obraz")
            DODATKI_SEO[sciezka] = {"typ": "article", "data": x["data"],
                                    "ld": [self.ak_artykul_ld(sciezka, x["tytul"], x["opis"], x["data"], obraz,
                                                              None, x.get("zrodla", []))]}
            zapisz(sciezka, S.uklad_akademii(f"{x['tytul']} – Akademia Siatkówki Volley", x["opis"], tresc, pp,
                                             self.wersja, aktualnosci=True))

    # --- STRONA WYBORU (volleykobylka.pl) -----------------------------------
    def wybor(self):
        zapisz("index.html", S.strona_wyboru("", self.wersja))

    # --- POZNAJ MNIE (strona każdej zawodniczki z odpowiedziami na pytania) ---------
    def ciekawostka(self, p, kadra):
        """Losowa odpowiedź zawodniczki na stronie głównej („Poznaj nas”) – przy każdej wizycie inna."""
        wpisy = []
        for z in kadra:
            if not S.ma_odpowiedzi(z):
                continue
            for q, a in zip(C.PYTANIA, C.POZNAJ.get(f"{z['imie']} {z['nazwisko']}", [])):
                if str(a).strip():
                    wpisy.append({"q": q, "a": a, "k": f"#{z['numer']} {z['imie']} {z['nazwisko']}",
                                  "u": p + S.adres_profilu(z), "f": S.src_img(p, z["zdjecie"]) if z.get("zdjecie") else ""})
        if not wpisy:
            return ""
        w = wpisy[0]
        return (f'<aside class="ciek" data-ciekawostki="{e(json.dumps(wpisy, ensure_ascii=False))}">'
                f'<img class="ciek__foto" src="{e(w["f"])}" alt="" loading="lazy">'
                f'<div class="ciek__tresc"><p class="ciek__nad">Poznaj nas</p><p class="ciek__q">{e(w["q"])}</p>'
                f'<blockquote class="ciek__a">„{e(w["a"])}”</blockquote>'
                f'<a class="ciek__kto" href="{e(w["u"])}">{e(w["k"])} – poznaj ją →</a></div>'
                f'<button class="ciek__inne" type="button">Inne pytanie ↻</button></aside>')

    def profile(self):
        """Profil każdej zawodniczki: dane, kluby, MVP w sezonie i – jeśli są – odpowiedzi „Poznaj mnie”."""
        kadra = sorted([z for z in C.KADRA if z["druzyna"] == GLOWNA and S.adres_profilu(z)], key=lambda z: z["numer"])
        for i, z in enumerate(kadra):
            odp = C.POZNAJ.get(f"{z['imie']} {z['nazwisko']}", [])
            poprz, nast = kadra[i - 1], kadra[(i + 1) % len(kadra)]
            imie_nazwisko = f"{z['imie']} {z['nazwisko']}"
            mvp = [m for m in self.mecze if (m.get("mvp") or "").strip().lower() == imie_nazwisko.lower()]

            def tresc(p, z=z, odp=odp, poprz=poprz, nast=nast, mvp=mvp):
                qa = "".join(f'<div class="pm__qa"><dt>{e(q)}</dt><dd>{e(a)}</dd></div>'
                             for q, a in zip(C.PYTANIA, odp) if str(a).strip())
                foto = S.img(p, z.get("zdjecie"), f"{z['imie']} {z['nazwisko']}", "pm__foto", lazy=False)
                kapitan = ' · Kapitan' if z.get("kapitan") else ""
                fakty = [("Pozycja", z["pozycja"]), ("Numer", f"#{z['numer']}")]
                if z.get("wzrost"):
                    fakty.append(("Wzrost", f"{z['wzrost']} cm"))
                if z.get("zasieg"):
                    fakty.append(("Zasięg w ataku", f"{z['zasieg']} cm"))
                if z.get("u_nas"):
                    fakty.append(("Sezony w Kobyłce", z["u_nas"]))
                if mvp:
                    fakty.append(("MVP w sezonie", f"{len(mvp)}×"))
                fakty_html = "".join(f'<div><dt>{e(a)}</dt><dd>{e(b)}</dd></div>' for a, b in fakty)
                kluby = ""
                if z.get("kluby"):
                    kluby = ('<h2 class="pm__h2">Poprzednie kluby</h2><ul class="pm__kluby">'
                             + "".join(f"<li><span>{e(sz)}</span>{e(k)}</li>" for sz, k in z["kluby"]) + "</ul>")
                mvp_html = ""
                if mvp:
                    pozycje = []
                    for m in mvp:
                        rywal = m["strony"][1] if m["strony"][0].get("nasza") else m["strony"][0]
                        pozycje.append(f'<li><span>{m["data"].strftime("%d.%m.%Y")}</span>z {e(rywal["krotko"] if rywal else "")} '
                                       f'<b>{e(m.get("wynik") or "")}</b></li>')
                    mvp_html = f'<h2 class="pm__h2">MVP meczu</h2><ul class="pm__kluby">{"".join(pozycje)}</ul>'
                pytania = f'<h2 class="pm__h2">Poznaj mnie</h2><dl class="pm__lista">{qa}</dl>' if qa else ""
                nawig = ""
                if len(kadra) > 1:
                    nawig = (f'<nav class="pm__nawig" aria-label="Inne zawodniczki">'
                             f'<a href="{p}{S.adres_profilu(poprz)}">← #{e(poprz["numer"])} {e(poprz["imie"])} {e(poprz["nazwisko"])}</a>'
                             f'<a href="{p}{S.adres_profilu(nast)}">#{e(nast["numer"])} {e(nast["imie"])} {e(nast["nazwisko"])} →</a></nav>')
                ld = {"@context": "https://schema.org", "@type": "Person", "name": f"{z['imie']} {z['nazwisko']}",
                      "jobTitle": f"Siatkarka – {z['pozycja'].lower()}",
                      "memberOf": {"@type": "SportsTeam", "name": C.KLUB["nazwa"], "sport": "Volleyball"}}
                if z.get("wzrost"):
                    ld["height"] = f"{z['wzrost']} cm"
                return f"""
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<section class="pm"><div class="kontener pm__siatka">
  <div class="pm__lewa">
    <div class="pm__zdjecie">{foto}<span class="pm__nr" aria-hidden="true">{e(z['numer'])}</span></div>
  </div>
  <div class="pm__prawa">
    <p class="pm__nad">{e(z['pozycja'])} · #{e(z['numer'])}{kapitan}</p>
    <h1 class="pm__imie"><span>{e(z['imie'])}</span>{e(z['nazwisko'])}</h1>
    <dl class="pm__fakty">{fakty_html}</dl>
    {mvp_html}
    {kluby}
    {pytania}
    <p class="pm__wroc"><a class="btn btn--zolty" href="{p}druzyny.html">Cała kadra →</a></p>
  </div>
</div></section>
<section class="sekcja sekcja--biala"><div class="kontener">{nawig}</div></section>"""
            opis = (f"{imie_nazwisko} – {z['pozycja'].lower()} Easy Wrap Volley Kobyłka (#{z['numer']}), II liga kobiet"
                    + (f", {z['wzrost']} cm" if z.get("wzrost") else "")
                    + (f". Poprzednio: {', '.join(dict.fromkeys(k for _, k in z['kluby']))[:80]}" if z.get("kluby") else "")
                    + ".")
            og = None
            try:
                import grafika
                if z.get("zdjecie") and S.jest_plik(z["zdjecie"]):
                    og = f"img/og/zawodniczka-{S.adres_profilu(z).split('/')[-1][:-5]}.jpg"
                    os.makedirs(os.path.join(WYJSCIE, "img", "og"), exist_ok=True)
                    grafika.grafika_og_zawodniczki(z, os.path.join(FOLDER, "img", z["zdjecie"]), C.KLUB["nazwa"]) \
                        .save(os.path.join(WYJSCIE, og), "JPEG", quality=85, optimize=True)
            except Exception as blad:
                print(f"  UWAGA: obraz profilu {imie_nazwisko}: {blad}")
                og = None
            DODATKI_SEO[S.adres_profilu(z)] = {"obraz": og, "typ": "profile",
                                               "obrazy": ["img/" + z["zdjecie"]] if z.get("zdjecie") and S.jest_plik(z["zdjecie"]) else []}
            self.strona(S.adres_profilu(z), imie_nazwisko, opis, tresc, aktywna="druzyny.html",
                        pelny=f"{imie_nazwisko} – {z['pozycja'].lower()}, Easy Wrap Volley Kobyłka")

    # --- STATYSTYKI (ukryta strona, bez linku w menu) --------------------------
    def dziennik_wejsc_html(self):
        dz = getattr(S, "LICZNIK_DZIENNIK", {}) or {}
        if not dz:
            return ""
        maks = max(dz.values()) or 1
        wiersze = "".join(
            f'<div class="st-wiersz"><span class="st-nazwa">{MIESIACE_PL[int(m[5:]) - 1].capitalize()} {m[:4]}</span>'
            f'<span class="st-pasek"><i style="width:{round(w / maks * 100)}%"></i></span><b>{w:,}</b></div>'.replace(",", " ")
            for m, w in sorted(dz.items(), reverse=True))
        return (f'<h2 class="statystyki__h">Dziennik wejść – miesiąc po miesiącu</h2>'
                f'<div class="statystyki__lista">{wiersze}</div>'
                f'<p class="statystyki__przypis">Licznik w stopce strony liczy od zera od 1. dnia każdego miesiąca. '
                f'Wynik każdego miesiąca zostaje zapisany tutaj (aktualizacja kilka razy dziennie) oraz w pliku '
                f'dane/dziennik-wejsc.csv, który otworzysz w Excelu.</p>')

    def statystyki(self, strony):
        klucze = []
        for s in strony:
            k = "start" if s == "index.html" else s[:-5]
            k = re.sub(r"[^a-z0-9-]+", "_", k.lower())[:44]
            klucze.append((s, k))
        def tresc(p):
            return f"""
{S.plakat_podstrony(p, 'Statystyki', 'Odwiedziny strony – bez ciasteczek', 'kontakt')}
<section class="sekcja"><div class="kontener statystyki" data-statystyki='{e(json.dumps(klucze, ensure_ascii=False))}'>
  <label class="statystyki__miesiac">Miesiąc: <select data-st-miesiac></select></label>
  <div class="statystyki__kafle">
    <div class="statystyki__kafel"><span data-st="wszystko">–</span>wyświetleń podstron</div>
    <div class="statystyki__kafel"><span data-st="wejscia">–</span>wejść na stronę</div>
    <div class="statystyki__kafel"><span data-st="telefon">–</span>wejść z telefonu</div>
    <div class="statystyki__kafel"><span data-st="komputer">–</span>wejść z komputera</div>
  </div>
  {self.dziennik_wejsc_html()}
  <h2 class="statystyki__h">Skąd przychodzą</h2><div class="statystyki__lista" data-st-zrodla></div>
  <h2 class="statystyki__h">Najczęściej oglądane</h2><div class="statystyki__lista" data-st-strony></div>
  <p class="statystyki__przypis">Liczone od 3 listopada 2026. Bez ciasteczek i bez zapisywania danych osobowych –
  każde wejście dolicza 1 do licznika. Wejście = przyjście na stronę z zewnątrz (Google, Facebook, link, wpisany adres).
  Ta strona nie jest widoczna w menu ani w Google.</p>
</div></section>"""
        self.strona("statystyki.html", "Statystyki", "Statystyki odwiedzin strony.", tresc, aktywna="")

    # --- GALERIA -----------------------------------------------------------
    def galeria(self):
        def tresc(p):
            albumy = ""
            for a in sorted(C.GALERIA, key=lambda a: a["data"], reverse=True):
                folder = os.path.join(FOLDER, "img", "galeria", a["folder"])
                pliki = sorted(f for f in os.listdir(folder)
                               if f.lower().endswith((".webp", ".jpg", ".jpeg", ".png"))) if os.path.isdir(folder) else []
                d = date.fromisoformat(a["data"])
                if pliki:
                    zdjecia = "".join(
                        f'<a class="galeria__el" href="{p}img/galeria/{e(a["folder"])}/{e(f)}" data-lightbox>'
                        f'<img src="{p}img/galeria/{e(a["folder"])}/{e(f)}" alt="{e(a["tytul"])} – zdjęcie {i + 1}" loading="lazy" decoding="async"></a>'
                        for i, f in enumerate(pliki))
                else:
                    zdjecia = '<p class="pusto">Zdjęcia wkrótce.</p>'
                albumy += f"""
<section class="album pojaw"><h2 class="album__tytul">{e(a['tytul'])}</h2>
<p class="album__data"><time datetime="{d.isoformat()}">{e(S.data_pl(d))}</time></p>
<div class="galeria">{zdjecia}</div></section>"""
            return f"""
{S.plakat_podstrony(p, 'Galeria', 'Zdjęcia z meczów i treningów', 'galeria')}
<div class="sekcja"><div class="kontener">{albumy or '<p class="pusto">Galeria wkrótce.</p>'}</div></div>
<dialog class="lightbox" data-lightbox-okno aria-label="Podgląd zdjęcia">
  <img alt="">
  <button class="lightbox__zamknij" data-lightbox-zamknij aria-label="Zamknij">×</button>
  <button class="lightbox__nav lightbox__nav--l" data-lightbox-krok="-1" aria-label="Poprzednie zdjęcie">←</button>
  <button class="lightbox__nav lightbox__nav--p" data-lightbox-krok="1" aria-label="Następne zdjęcie">→</button>
</dialog>"""
        self.strona("galeria.html", "Galeria", "Zdjęcia z meczów i treningów Easy Wrap Volley Kobyłka.", tresc)

    # --- SPONSORZY ---------------------------------------------------------
    def sponsorzy(self):
        def tresc(p):
            return f"""
{S.plakat_podstrony(p, 'Sponsorzy', 'Dziękujemy, że gracie z nami', 'sponsorzy')}
{self.sponsorzy_html(p, pelna=True)}
<section class="sekcja"><div class="kontener cta">
  <h2 class="sekcja__tytul">Zostań <span>sponsorem</span></h2>
  <p>{e(C.SPONSORZY_TEKST)}</p>
  <a class="btn btn--zolty" href="mailto:{e(C.KLUB['email'])}?subject={quote('Współpraca sponsorska')}">Napisz do nas →</a>
</div></section>"""
        self.strona("sponsorzy.html", "Sponsorzy", "Sponsorzy i partnerzy klubu Easy Wrap Volley Kobyłka.", tresc)

    # --- O KLUBIE ----------------------------------------------------------
    def o_klubie(self):
        O = C.O_KLUBIE

        def tresc(p):
            trofea = "".join(f'<li><span class="trofeum__rok">{e(t["rok"])}</span><span>{e(t["opis"])}</span></li>'
                             for t in sorted(O["trofea"], key=lambda t: t["rok"], reverse=True))
            wartosci = "".join(f"<li>{e(w)}</li>" for w in O.get("wartosci", []))
            return f"""
{S.plakat_podstrony(p, 'O klubie', C.KLUB['nazwa_prawna'], 'o-klubie')}
{f'<div class="trofea" aria-label="Sukcesy"><ul class="kontener">{trofea}</ul></div>' if trofea else ''}
<section class="sekcja"><div class="kontener uklad-2">
  <div class="artykul__tresc">{S.akapity(O['historia'])}
    <div class="przyciski-cta"><a class="btn btn--zolty" href="{p}druzyny.html">Poznaj kadrę →</a>
    <a class="btn btn--obrys" href="{p}akademia.html">Akademia Siatkówki →</a></div></div>
  <div>
    {f'<ul class="wartosci">{wartosci}</ul>' if wartosci else ''}
    <dl class="dane-klubu">
      <dt>Nazwa</dt><dd>{e(C.KLUB['nazwa_prawna'])}</dd>
      <dt>Drużyna</dt><dd>{e(C.KLUB['nazwa'])}</dd>
      <dt>Adres</dt><dd>{e(C.KLUB['adres'])}</dd>
      <dt>E-mail</dt><dd><a href="mailto:{e(C.KLUB['email'])}">{e(C.KLUB['email'])}</a></dd>
    </dl>
  </div>
</div></section>"""
        pytania = self.faq_druzyny()
        DODATKI_SEO["o-klubie.html"] = {"ld": [S.faq_ld(pytania)]}
        tresc_z_faq = lambda p, t=tresc, q=pytania: t(p) + self.o_klubie_wiecej(p) + S.faq_html(q)
        self.strona("o-klubie.html", "O klubie", "Historia i sukcesy Klubu Sportowego Volley Kobyłka.", tresc_z_faq)

    def faq_akademii(self):
        A = C.AKADEMIA
        H = C.HALA_DOMOWA
        fakty = " ".join(A.get("fakty", []))
        pyt = []
        if A.get("cennik"):
            pyt.append(("Ile kosztują treningi siatkówki w Akademii?",
                        "; ".join(f"{e(c['co'])} – {e(c['cena'])}" for c in A["cennik"]) +
                        (". Bez wpisowego." if "wpisowego" in fakty else ".")))
        if any("klas" in x for x in A.get("fakty", [])):
            pyt.append(("Dla kogo są zajęcia?", e(next(x for x in A["fakty"] if "klas" in x)) +
                        " – w jednej grupie trenują dziewczynki w podobnym wieku."))
        if A.get("harmonogram"):
            dni_tr = sorted({(t["dzien"], t["od"], t["do"]) for t in A["harmonogram"]},
                            key=lambda x: ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"].index(x[0]))
            godz = {(x[1], x[2]) for x in dni_tr}
            if len(godz) == 1:
                od, do = godz.pop()
                mn = {"poniedziałek": "poniedziałki", "wtorek": "wtorki", "środa": "środy", "czwartek": "czwartki",
                      "piątek": "piątki", "sobota": "soboty", "niedziela": "niedziele"}
                lista = [mn.get(x[0].lower(), x[0]) for x in dni_tr]
                opis_dni = ("we " if lista[0].startswith("wt") else "w ") + " i ".join(lista)
                pyt.append(("Kiedy są treningi?", f"{opis_dni[0].upper() + opis_dni[1:]}, {od}–{do}. Pełny plan w sekcji "
                                                   '<a href="#plan">Plan treningów</a>.'))
        pyt.append(("Czy można przyjść na trening próbny?",
                    "Tak. Pierwszy trening jest bezpłatny – córka sprawdzi, czy siatkówka jej się podoba. "
                    'Umów go w sekcji <a href="#grupa">Sprawdź grupę dla córki</a>.'))
        pyt.append(("Czy córka musi umieć grać w siatkówkę?",
                    "Nie. Zapraszamy też dziewczynki, które dopiero zaczynają – na treningach uczymy podstaw od zera."))
        pyt.append(("Co zabrać na trening?",
                    "Strój sportowy, buty halowe z jasną, niebrudzącą podeszwą, butelkę wody i gumkę do związania włosów."))
        pyt.append(("Gdzie odbywają się treningi siatkówki dla dziewcząt?",
                    f"W hali: {e(H['nazwa'])}, {e(H['adres'])}. To Kobyłka w powiecie wołomińskim – blisko Wołomina, Marek i Zielonki."))
        if "90" in fakty:
            pyt.append(("Ile trwa trening?", "Jeden trening trwa 90 minut."))
        if "dziewcząt" in fakty:
            pyt.append(("Czy treningi są dla chłopców?", "Nie – zajęcia Akademii Siatkówki Volley są tylko dla dziewcząt."))
        if "sezon" in fakty:
            pyt.append(("Na jak długo zapisuje się dziecko?", "Umowę zawieramy na sezon: od września do czerwca."))
        if A.get("trenerzy"):
            osoby = " oraz ".join(f'{e(t["imie"])} {e(t["nazwisko"])}' for t in A["trenerzy"])
            t0 = A["trenerzy"][0]
            pyt.append(("Kto prowadzi treningi?",
                        f'Zajęcia prowadzi {osoby}' +
                        (" – rozgrywająca drużyny Easy Wrap Volley Kobyłka, która gra w 2. lidze kobiet."
                         if len(A["trenerzy"]) == 1 and S.zawodniczka_po_nazwisku(f'{t0["imie"]} {t0["nazwisko"]}') else ".") +
                        ' Więcej w sekcji <a href="#trenerzy">Trenerzy</a>.'))
        mail = (A.get("koordynator") or {}).get("email") or C.KLUB["email"]
        if A.get("formularz_google"):
            pyt.append(("Jak zapisać dziecko na siatkówkę?",
                        f'Wypełnij <a href="{e(A["formularz_google"])}" rel="noopener" target="_blank">formularz zgłoszeniowy</a> – '
                        'odpowiemy i potwierdzimy termin pierwszego treningu. Umowę podpisujemy na miejscu, w hali. '
                        f'Pytania: <a href="mailto:{e(mail)}">{e(mail)}</a>.'))
        else:
            pyt.append(("Jak zapisać dziecko na siatkówkę?",
                        f'Napisz na <a href="mailto:{e(mail)}">{e(mail)}</a> – podaj imię i rok urodzenia dziecka. '
                        'Szczegóły w sekcji <a href="#zapisy">Zapisy</a>.'))
        pyt.append(("Co, jeśli córka zachoruje?",
                    "Przy chorobie lub kontuzji trwającej cały miesiąc (z zaświadczeniem) opłata za ten miesiąc wynosi 50 zł, "
                    "a córka zachowuje miejsce w grupie."))
        pyt.append(("Czy opłata obowiązuje w ferie i święta?",
                    "Tak. Opłata miesięczna jest rozłożona równo na cały sezon, dlatego w ferie i przerwy świąteczne jest taka sama. "
                    "W wakacje zajęć nie ma."))
        if A.get("ochrona_maloletnich"):
            pyt.append(("Czy dzieci są w Akademii bezpieczne?",
                        "Tak. Klub stosuje Standardy Ochrony Małoletnich, a każda osoba pracująca z dziećmi ma aktualne "
                        'zaświadczenie o niekaralności. Więcej w sekcji <a href="#ochrona">Bezpieczeństwo dzieci</a>.'))
        return pyt

    def faq_druzyny(self):
        """Pytania i odpowiedzi z aktualnych danych strony (miejsce w tabeli, najbliższy mecz, hala)."""
        H = C.HALA_DOMOWA
        p = "/"
        pyt = [("Gdzie gra Easy Wrap Volley Kobyłka?",
                f"Mecze u siebie rozgrywamy w hali: {e(H['nazwa'])}, {e(H['adres'])}. "
                f'<a href="{e(H.get("mapa", ""))}" target="_blank" rel="noopener">Pokaż na mapie</a>.')]
        if C.KLUB.get("wstep_wolny"):
            pyt.append(("Ile kosztuje wstęp na mecz siatkówki w Kobyłce?",
                        "Wstęp na mecze Easy Wrap Volley Kobyłka u siebie jest wolny. Zapraszamy całe rodziny!"))
        liga = C.DRUZYNY[GLOWNA]["liga"]
        tekst = f"Easy Wrap Volley Kobyłka gra w rozgrywkach: {e(liga)} (siatkówka kobiet)."
        nasz = next((w for w in self.tabela() if w["nasz"]), None)
        if nasz:
            tekst += f" Po {nasz['mecze']} meczach zajmujemy {nasz['lp']}. miejsce w tabeli ({nasz['pkt']} pkt)."
        pyt.append(("W jakiej lidze gra Easy Wrap Volley Kobyłka?", tekst))
        m = self.najblizszy
        if m and m["strony"][1]:
            g, h = m["strony"]
            pyt.append(("Kiedy jest najbliższy mecz Easy Wrap Volley Kobyłka?",
                        f"{e(S.data_pl(m['data']))}{', godz. ' + e(m['godzina']) if m.get('godzina') else ''}: "
                        f"{e(g['nazwa'])} – {e(h['nazwa'])}"
                        f"{' (' + e(S.skrot_hali(m.get('hala'))) + ')' if m.get('hala') else ''}. "
                        f'Pełny terminarz: <a href="/terminarz.html">terminarz i wyniki</a>.'))
        pyt += [("Jak mieć terminarz meczów w telefonie?",
                 'Na stronie <a href="/terminarz.html#w-telefonie">Terminarz</a> dodaj kalendarz sezonu do telefonu '
                 '(iPhone, Android, Outlook). Nowe godziny i wyniki pojawią się w nim same.'),
                ("Jak zapisać córkę na siatkówkę w Kobyłce?",
                 'Treningi dla dziewcząt prowadzi <a href="/akademia.html">Akademia Siatkówki Volley</a> – '
                 'w hali przy PSP nr 3 w Kobyłce, ul. Załuskiego 57.'),
                ("Jak zostać sponsorem Easy Wrap Volley Kobyłka?",
                 f'Napisz do nas: <a href="mailto:{e(C.KLUB["email"])}">{e(C.KLUB["email"])}</a>. '
                 'Zobacz też <a href="/sponsorzy.html">naszych sponsorów</a>.')]
        return pyt

    def o_klubie_wiecej(self, p):
        """Stałe fakty o klubie z danych strony – więcej treści i linków dla wyszukiwarek."""
        kadra = [z for z in C.KADRA if z["druzyna"] == GLOWNA]
        linki = ", ".join(f'<a href="{p}{S.adres_profilu(z)}">{e(z["imie"])} {e(z["nazwisko"])}</a>'
                          for z in sorted(kadra, key=lambda z: z["nazwisko"]) if S.adres_profilu(z))
        tytularny = next((s_["nazwa"] for s_ in C.SPONSORZY.values() if s_.get("poziom") == "tytularny"), "Easy Wrap")
        return f"""
<section class="sekcja sekcja--biala"><div class="kontener artykul__tresc">
  <h2 class="sekcja__tytul">Siatkówka kobiet <span>w Kobyłce</span></h2>
  <p>{e(C.KLUB['nazwa_prawna'])} to klub siatkarski z Kobyłki w powiecie wołomińskim. Pierwsza drużyna – {e(C.KLUB['nazwa'])} –
  gra w rozgrywkach: {e(C.DRUZYNY[GLOWNA]['liga'])}. Sponsorem tytularnym zespołu jest {e(tytularny)}.
  Mecze u siebie rozgrywamy w hali przy PSP nr 3 w Kobyłce, ul. Załuskiego 57{', wstęp jest wolny' if C.KLUB.get('wstep_wolny') else ''}.</p>
  <p>W kadrze na sezon gra {len(kadra)} siatkarek: {linki}. Terminarz, wyniki i tabelę znajdziesz na stronie
  <a href="{p}terminarz.html">Terminarz i wyniki</a>, a zapowiedzi i relacje w <a href="{p}aktualnosci.html">Aktualnościach</a>.</p>
  <p>Szkolimy też dziewczęta: <a href="{p}akademia.html">Akademia Siatkówki Volley</a> prowadzi treningi siatkówki
  dla dziewcząt w Kobyłce – blisko Wołomina, Marek, Zielonki i Radzymina.</p>
  {self.przyjaciele_akapit()}
</div></section>"""

    def przyjaciele_akapit(self):
        lista = getattr(C, "PRZYJACIELE", [])
        if not lista:
            return ""
        linki = ", ".join(f'<a href="{e(x["www"])}" target="_blank" rel="noopener">{e(x["nazwa"])}</a> ({e(x["opis"].lower())})'
                          for x in lista)
        return f"<p>Sport i społeczność Kobyłki – zajrzyj też do: {linki}.</p>"

    # --- SKLEP -------------------------------------------------------------
    def sklep(self):
        def tresc(p):
            produkty = ""
            for i, pr in enumerate(C.SKLEP["produkty"]):
                temat = quote(f"Zamówienie: {pr['nazwa']}")
                przycisk = (f'<a class="btn btn--zolty" href="mailto:{e(C.KLUB["email"])}?subject={temat}">Zamów</a>'
                            if pr.get("dostepny") else '<span class="produkt__brak">Chwilowo niedostępny</span>')
                produkty += f"""
<article class="produkt">
  <div class="produkt__foto foto-{i % 4}">{S.img(p, pr.get('zdjecie'), pr['nazwa'], 'produkt__img')}</div>
  <div class="produkt__opis"><h3>{e(pr['nazwa'])}</h3>
  {f'<p class="produkt__rozmiary">Rozmiary: {e(pr["rozmiary"])}</p>' if pr.get('rozmiary') else ''}
  <p class="produkt__cena">{e(pr['cena'])}</p>{przycisk}</div>
</article>"""
            forma = (f'<a class="btn btn--obrys btn--ciemny" href="{e(C.SKLEP["formularz_google"])}" rel="noopener">Formularz zamówienia</a>'
                     if C.SKLEP.get("formularz_google") else "")
            return f"""
{S.plakat_podstrony(p, 'Sklep', 'Barwy klubowe', 'sklep')}
<section class="sekcja"><div class="kontener">
  <p class="sklep__info">{e(C.SKLEP['jak_zamowic'])} Płatność przy odbiorze – sklep nie przyjmuje płatności online.</p>
  {forma}
  <div class="produkty">{produkty}</div>
</div></section>"""
        self.strona("sklep.html", "Sklep", "Gadżety i koszulki klubowe Easy Wrap Volley Kobyłka.", tresc)

    # --- KONTAKT -----------------------------------------------------------
    def kontakt(self):
        def tresc(p):
            osoby = ""
            # Osoby z tym samym adresem co klub nie powtarzają e-maila – wystarczy jeden podpis pod adresem
            wspolne = [o for o in C.KONTAKT["osoby"] if o.get("email") == C.KLUB["email"] and not o.get("imie")]
            podpis = (f'<p class="kontakt__podpis">{e(" · ".join(o["rola"] for o in wspolne))}</p>' if wspolne else "")
            for o in C.KONTAKT["osoby"]:
                if o in wspolne:
                    continue
                imie = f"<strong>{e(o['imie'])}</strong>" if o.get("imie") else ""
                osoby += (f'<li><span class="osoba__rola">{e(o["rola"])}</span>{imie}'
                          f'<a href="mailto:{e(o["email"])}">{e(o["email"])}</a></li>')
            mapa = C.HALA_DOMOWA["mapa"]
            forma = (f'<a class="btn btn--zolty" href="{e(C.KONTAKT["formularz_google"])}" rel="noopener">Formularz kontaktowy</a>'
                     if C.KONTAKT.get("formularz_google") else "")
            return f"""
{S.plakat_podstrony(p, 'Kontakt', 'Napisz do nas', 'kontakt')}
<section class="sekcja"><div class="kontener uklad-2">
  <div>
    <p class="kontakt__mail"><a href="mailto:{e(C.KLUB['email'])}">{e(C.KLUB['email'])}</a></p>
    {podpis}
    {f'<ul class="kontakt__osoby">{osoby}</ul>' if osoby else ''}
    {forma}
    <ul class="kontakt__social">{S.social_linki("kontakt", True)}</ul>
    <p class="kontakt__rodo">Dane z wiadomości (adres e-mail, treść) wykorzystujemy tylko do odpowiedzi.
      Szczegóły: <a href="{p}polityka-prywatnosci.html">Polityka prywatności</a>.</p>
  </div>
  <div class="kontakt__karta">
    <h2>Klub</h2><p>{e(C.KLUB['nazwa_prawna'])}<br>{e(C.KLUB['adres'])}</p>
    <h2>Hala meczowa</h2><p>{e(C.HALA_DOMOWA['nazwa'])}<br>{e(C.HALA_DOMOWA['adres'])}</p>
    <a class="btn btn--zolty" href="{e(mapa)}" rel="noopener">Pokaż na mapie →</a>
  </div>
</div></section>"""
        self.strona("kontakt.html", "Kontakt", "Kontakt z klubem Easy Wrap Volley Kobyłka i Akademią Siatkówki Volley – e-mail, adres hali (ul. Załuskiego 57, Kobyłka), media społecznościowe.", tresc)

    # --- POLITYKA PRYWATNOŚCI ---------------------------------------------
    def polityka(self):
        def tresc(p):
            k = C.KLUB
            A = C.AKADEMIA
            mail = f'<a href="mailto:{e(k["email"])}">{e(k["email"])}</a>'
            rej = ", ".join(f"{n}: {e(k[x])}" for n, x in (("KRS", "krs"), ("NIP", "nip"), ("REGON", "regon")) if k.get(x))
            om = A["ochrona_maloletnich"]
            standardy = (f'<a href="{p}img/{e(om["dokument"])}">Standardy Ochrony Małoletnich (PDF)</a>'
                         if S.jest_plik(om.get("dokument")) else "Standardy Ochrony Małoletnich")
            return f"""
{S.plakat_podstrony(p, 'Polityka prywatności', 'i plików cookies', 'polityka')}
<section class="sekcja"><div class="kontener artykul__tresc polityka">
<p class="polityka__skrot"><strong>W skrócie:</strong> strona nie używa plików cookies, nie śledzi odwiedzających i nie ma reklam.
Dane osobowe dostajemy tylko wtedy, gdy sam(a) do nas napiszesz albo zapiszesz dziecko do Akademii.</p>

<h2>1. Administrator danych</h2>
<p>Administratorem danych osobowych jest <strong>{e(k['nazwa_prawna'])}</strong>, {e(k['adres'])}{', ' + rej if rej else ''}
(dalej: „Klub”). Klub prowadzi drużynę {e(k['nazwa'])} oraz {e(A.get('nazwa') or 'Akademię Siatkówki Volley')}.
Kontakt w sprawach danych osobowych: {mail}. Klub nie wyznaczył inspektora ochrony danych (nie ma takiego obowiązku).</p>

<h2>2. Kiedy i po co przetwarzamy dane</h2>
<ul>
<li><strong>Wiadomość e-mail do Klubu</strong> – adres e-mail, imię i nazwisko oraz treść wiadomości wykorzystujemy, aby odpowiedzieć
i prowadzić korespondencję (art. 6 ust. 1 lit. f RODO – prawnie uzasadniony interes, czyli kontakt z osobą, która do nas pisze).
Korespondencję przechowujemy do czasu zakończenia sprawy, a jeśli dotyczy umowy – przez okres jej trwania i przedawnienia roszczeń.</li>
<li><strong>Zgłoszenie do Akademii</strong> – dane rodzica (imię, nazwisko, telefon, e-mail) i dziecka (imię, nazwisko, rok urodzenia)
wykorzystujemy, aby przydzielić grupę, zawrzeć i wykonać umowę uczestnictwa oraz kontaktować się w sprawie zajęć
(art. 6 ust. 1 lit. b i f RODO). Dane uczestników przechowujemy przez czas uczestnictwa w zajęciach, a potem przez okres wymagany
przepisami podatkowymi i rachunkowymi oraz przedawnienia roszczeń. Zgłoszenia osób, które nie dołączyły, usuwamy po zakończeniu sezonu.</li>
<li><strong>Sponsorzy i partnerzy</strong> – dane osób kontaktowych firm wykorzystujemy do rozmów i wykonania umów (art. 6 ust. 1 lit. b i f RODO).</li>
<li><strong>Skład drużyny i wyniki</strong> – imiona, nazwiska, numery, pozycje i zdjęcia zawodniczek seniorskiej drużyny publikujemy
na podstawie ich zgody oraz w związku z udziałem w rozgrywkach (art. 6 ust. 1 lit. a i f RODO). Wyniki i składy meczowe są też jawne
w systemach Polskiego Związku Piłki Siatkowej i Wojewódzkiego Związku Piłki Siatkowej.</li>
</ul>
<p>Nie podejmujemy zautomatyzowanych decyzji i nie profilujemy odwiedzających.</p>

<h2>3. Wizerunek</h2>
<p>Publikujemy zdjęcia i filmy z meczów, treningów i wydarzeń klubowych. Wizerunek dzieci z Akademii publikujemy wyłącznie za pisemną zgodą
rodziców lub opiekunów, bez podawania nazwisk. Zgodę można w każdej chwili wycofać – usuniemy wtedy zdjęcie ze strony i z naszych profili.
Jeśli widzisz zdjęcie, które chcesz usunąć, napisz: {mail}.</p>
<p>Aktualności na stronie to posty z naszych profili na Facebooku (drużyny i Akademii). Strona sama kopiuje ich treść i zdjęcia
na nasz serwer – usunięcie posta na Facebooku usuwa go też ze strony przy najbliższej aktualizacji.</p>

<h2>4. Komu przekazujemy dane</h2>
<p>Danych nie sprzedajemy. Korzystają z nich tylko osoby działające w imieniu Klubu (zarząd, trenerzy, koordynator) oraz dostawcy usług:</p>
<ul>
<li><strong>Hosting strony – GitHub Pages</strong> (GitHub, Inc., USA). Serwer, podobnie jak każdy serwer WWW, zapisuje techniczne logi
(adres IP, czas wizyty, odwiedzana strona) w celach bezpieczeństwa. GitHub jest objęty programem EU–U.S. Data Privacy Framework
i stosuje standardowe klauzule umowne. Zasady: <a href="https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener" target="_blank">GitHub Privacy Statement</a>.</li>
<li><strong>Poczta e-mail – Simply.com</strong> (Simply.com A/S, Dania). Wiadomości wysłane na adresy Klubu w domenie
volleykobylka.pl są przechowywane na serwerach Simply.com w Unii Europejskiej.</li>
<li><strong>Formularze Google</strong> – jeśli zgłoszenie odbywa się przez formularz, wczytuje się on dopiero po kliknięciu przycisku.
Wtedy Google przetwarza dane wpisane w formularzu i może użyć własnych plików cookies (<a href="https://policies.google.com/privacy?hl=pl" rel="noopener" target="_blank">zasady Google</a>).</li>
<li><strong>Licznik wyświetleń</strong> – przy wejściu na stronę przeglądarka wysyła jedno zapytanie do serwisu Abacus
(abacus.jasoncameron.dev), który zwiększa ogólny licznik o 1 (tylko przy wejściu na stronę – przejścia między podstronami
tylko odczytują licznik). Serwis technicznie widzi adres IP, ale nie zapisuje cookies,
nie identyfikuje odwiedzających i nie zbiera statystyk o konkretnych osobach. Podstawa: art. 6 ust. 1 lit. f RODO
(informacja o popularności strony). Serwer licznika może znajdować się poza Europejskim Obszarem Gospodarczym.</li>
<li><strong>Organy i instytucje</strong> (np. urząd skarbowy, związki sportowe) – tylko gdy wymagają tego przepisy.</li>
</ul>

<h2>5. Pliki cookies i pamięć przeglądarki</h2>
<p><strong>Strona nie zapisuje plików cookies</strong> – ani własnych, ani reklamowych czy analitycznych (nie używamy Google Analytics,
pikseli Facebooka itp.). Dlatego nie wyświetlamy baneru zgody na cookies.</p>
<ul>
<li>Jedyną rzeczą, którą strona zapisuje w Twojej przeglądarce, jest znacznik w <em>pamięci sesji</em> (sessionStorage),
że zapowiedź najbliższego meczu została już pokazana – żeby nie wyskakiwała przy każdym kliknięciu. Znacznik nie zawiera danych osobowych,
nie jest nigdzie wysyłany i znika po zamknięciu karty. Jest niezbędny do działania tej funkcji – zgodnie z art. 399 Prawa komunikacji elektronicznej taki zapis nie wymaga zgody.</li>
<li>Czcionki strony są zapisane na naszym serwerze – nie pobieramy ich z Google Fonts.</li>
<li>Facebook, Instagram, YouTube i Mapy Google są tylko <strong>linkami</strong>. Te serwisy dostają Twoje dane (i mogą zapisać swoje cookies)
dopiero po przejściu na nie – wtedy obowiązują ich własne zasady prywatności.</li>
<li>Pamięć sesji i cookies możesz w każdej chwili wyczyścić lub zablokować w ustawieniach przeglądarki.</li>
</ul>

<h2>6. Twoje prawa</h2>
<p>Masz prawo do: dostępu do swoich danych i otrzymania ich kopii, sprostowania, usunięcia, ograniczenia przetwarzania, przeniesienia danych,
sprzeciwu wobec przetwarzania opartego na prawnie uzasadnionym interesie oraz cofnięcia zgody w dowolnym momencie (bez wpływu na wcześniejsze
przetwarzanie). Wystarczy napisać: {mail}. Odpowiemy w ciągu miesiąca.</p>
<p>Możesz też złożyć skargę do <strong>Prezesa Urzędu Ochrony Danych Osobowych</strong>, ul. Stawki 2, 00-193 Warszawa
(<a href="https://uodo.gov.pl" rel="noopener" target="_blank">uodo.gov.pl</a>).</p>

<h2>7. Ochrona dzieci</h2>
<p>Klub stosuje {standardy} – zasady bezpiecznych relacji, reagowania na krzywdzenie oraz ochrony danych i wizerunku dzieci.
Krótka wersja dla dzieci jest na stronie <a href="{p}akademia.html#ochrona">Akademii</a>.</p>

<h2>8. Zmiany</h2>
<p>Politykę aktualizujemy, gdy zmienia się sposób działania strony. Ostatnia aktualizacja: {POLITYKA_DATA}.</p>
</div></section>"""
        self.strona("polityka-prywatnosci.html", "Polityka prywatności i cookies",
                    "Polityka prywatności i plików cookies strony klubu KS Volley Kobyłka.", tresc)

    # --- 404 ---------------------------------------------------------------
    def nie_znaleziono(self):
        def tresc(p):
            return f"""
{S.plakat_podstrony(p, 'Aut!', 'Błąd 404 – nie ma takiej strony', '404')}
<section class="sekcja"><div class="kontener"><a class="btn btn--zolty" href="{p}index.html">Wróć na stronę główną →</a></div></section>"""
        # Strona 404 pokazuje się pod dowolnym błędnym adresem, więc linki muszą być pełne
        adres = (C.KLUB.get("adres_strony") or "").rstrip("/")
        self.strona("404.html", "Nie znaleziono strony", "Nie ma takiej strony.", tresc, aktywna="",
                    p=adres + "/" if adres else None)

    # --- PLIKI KALENDARZA (.ics) ------------------------------------------
    def kalendarze(self):
        """Pliki .ics: pojedyncze mecze (przycisk „Dodaj do kalendarza”) oraz cały sezon do SUBSKRYPCJI –
        telefon sam pobiera zmiany (nowe godziny, wyniki) co kilka godzin."""
        baza = C.KLUB["adres_strony"].rstrip("/") + "/"
        teraz = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        def ics(t):
            return str(t).replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")

        def zawin(linia):
            # RFC 5545: linie maks. 75 bajtów, kontynuacja od spacji
            b_ = linia.encode("utf-8")
            if len(b_) <= 75:
                return linia
            czesci, ak = [], b""
            for znak in linia:
                z = znak.encode("utf-8")
                if len(ak) + len(z) > (75 if not czesci else 74):
                    czesci.append(ak.decode("utf-8"))
                    ak = b""
                ak += z
            czesci.append(ak.decode("utf-8"))
            return "\r\n ".join(czesci)

        def wydarzenie(m):
            g, h = m["strony"]
            tytul = f"{g['krotko']} – {h['krotko']}" if h else g["krotko"]
            if m.get("wynik"):
                tytul += f" {m['wynik']}"
            elif not m.get("godzina"):
                tytul += " (godzina wkrótce)"
            miejsce = ", ".join(x for x in (m.get("hala"), m.get("adres")) if x)
            if m.get("godzina"):
                gg, mm = (int(x) for x in m["godzina"].split(":"))
                start = datetime(m["data"].year, m["data"].month, m["data"].day, gg, mm) - timedelta(hours=S.przesuniecie_pl(m["data"]))
                czas = [f"DTSTART:{start:%Y%m%dT%H%M00Z}", f"DTEND:{start + timedelta(hours=2):%Y%m%dT%H%M00Z}"]
            else:
                czas = [f"DTSTART;VALUE=DATE:{m['data']:%Y%m%d}", f"DTEND;VALUE=DATE:{m['data'] + timedelta(days=1):%Y%m%d}"]
            opis = [C.DRUZYNY.get(m["druzyna"], {}).get("liga", "")]
            if m.get("wynik"):
                opis.append(f"Wynik: {m['wynik']}" + (f" ({', '.join(m['sety'])})" if m.get("sety") else ""))
            if m.get("mvp"):
                opis.append(f"MVP: {m['mvp']}")
            if m.get("transmisja"):
                opis.append(f"Transmisja: {m['transmisja']}")
            opis.append(f"Terminarz: {baza}terminarz.html")
            linie = ["BEGIN:VEVENT", f"UID:{m['druzyna']}-{m['data']:%Y%m%d}@easywrapvolley", f"DTSTAMP:{teraz}",
                     *czas, f"SUMMARY:{ics(tytul)}", f"DESCRIPTION:{ics(chr(10).join(x for x in opis if x))}",
                     f"URL:{baza}terminarz.html", "TRANSP:TRANSPARENT"]
            if miejsce:
                linie.append(f"LOCATION:{ics(miejsce)}")
            linie.append("END:VEVENT")
            return "".join(zawin(x) + "\r\n" for x in linie)

        def plik(wydarzenia, nazwa=None):
            nag = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Easy Wrap Volley Kobylka//PL", "CALSCALE:GREGORIAN",
                   "METHOD:PUBLISH"]
            if nazwa:
                nag += [f"X-WR-CALNAME:{nazwa}", "X-WR-TIMEZONE:Europe/Warsaw",
                        f"X-WR-CALDESC:Mecze Easy Wrap Volley Kobyłka – aktualizuje się samo ({baza})",
                        "REFRESH-INTERVAL;VALUE=DURATION:PT3H", "X-PUBLISHED-TTL:PT3H"]
            return "".join(zawin(x) + "\r\n" for x in nag) + "".join(wydarzenia) + "END:VCALENDAR\r\n"

        for m in self.mecze:
            zapisz(f"kalendarz/{m['plik_ics']}", plik([wydarzenie(m)]))
        zapisz(f"kalendarz/{GLOWNA}-caly-sezon.ics",
               plik([wydarzenie(m) for m in self.mecze if m["druzyna"] == GLOWNA], "Easy Wrap Volley – mecze"))


# =====================================================================
# 4. URUCHOMIENIE
# =====================================================================
def newsy_z_fb(posty, kategoria):
    """Posty z FB → wpisy aktualności (tytuł, zajawka, treść, zdjęcie, link do posta)."""
    nazwy = [s["nazwa"] for s in C.SPONSORZY.values()]
    wynik, adresy = [], set()
    for post in posty:
        opis = zrodla.oczysc_opis(post.get("opis"), nazwy, C.POSTY_FB.get("usun_hashtagi", True))
        tytul, tresc, zajawka = zrodla.podziel_post(opis)
        if not tytul:
            continue
        czas = datetime.fromisoformat(post["czas"].replace("+0000", "+00:00")).astimezone()
        adres = f"{czas.date().isoformat()}-{zrodla.slug(tytul)}"   # adres z oryginału – linki się nie zmieniają
        pelny = tytul
        tytul = ladny_tytul(tytul)
        if tytul.rstrip("…") != pelny and pelny not in (tresc or ""):
            tresc = (pelny + "\n\n" + (tresc or "")).strip()
        if adres in adresy:
            adres += "-" + zrodla.klucz_posta("", post["id"])[1:6]
        adresy.add(adres)
        wynik.append({"adres": adres, "data": czas.date().isoformat(), "czas": czas.isoformat(),
                      "kategoria": kategoria, "tytul": tytul, "zajawka": zajawka, "tresc": tresc,
                      "zdjecie": post.get("zdjecie"), "link_fb": post.get("link"), "zrodlo": "fb"})
    return wynik


def podepnij_relacje(mecze, newsy):
    """Mecz bez relacji dostaje news z FB opublikowany do 2 dni po meczu, w którym jest jego wynik."""
    for m in mecze:
        if not m.get("wynik") or m.get("relacja"):
            continue
        a, b = m["wynik"].split(":")
        wzor = re.compile(rf"\b({a}\s*:\s*{b}|{b}\s*:\s*{a})\b")
        for n in sorted(newsy, key=lambda n: n.get("czas") or n["data"]):
            dni = (date.fromisoformat(n["data"]) - m["data"]).days
            if n.get("zrodlo") == "fb" and 0 <= dni <= 2 and wzor.search(n["tytul"] + " " + n["tresc"]):
                m["relacja"] = n["adres"]
                break


def podepnij_mvp(mecze, posty):
    """Mecz bez wpisanego MVP dostaje zawodniczkę z posta FB o nagrodzie MVP (do 4 dni po meczu).
    Nazwisko rozpoznawane też w odmianie („Adrianny Sitarskiej”)."""
    kadra = [z for z in C.KADRA if z["druzyna"] == GLOWNA]
    def rdzen(slowo):
        slowo = slowo.lower()
        return slowo[:-1] if len(slowo) > 4 else slowo
    for m in mecze:
        if not m.get("wynik") or m.get("mvp") or m["druzyna"] != GLOWNA:
            continue
        for post in sorted(posty or [], key=lambda x: x.get("czas") or ""):
            opis = post.get("opis") or ""
            if "mvp" not in opis.lower() or not post.get("czas"):
                continue
            dni = (date.fromisoformat(post["czas"][:10]) - m["data"]).days
            if not 0 <= dni <= 4:
                continue
            tekst = opis.lower()
            trafione = [z for z in kadra if re.search(r"\b" + re.escape(rdzen(z["nazwisko"])) + r"\w{0,4}\b", tekst)]
            if len(trafione) == 1:
                z = trafione[0]
                m["mvp"] = f'{z["imie"]} {z["nazwisko"]}'
                break


def mecz_do_zapowiedzi(mecz):
    """Data najbliższego meczu i wszystkie znane nazwy rywala – do rozpoznania posta z plakatem."""
    if mecz is None:
        return None
    gosp, gosc = mecz["strony"]
    rywal = gosc if gosp.get("nasza") else gosp
    nazwy = []
    if rywal:
        r = rywal.get("rywal") or {}
        nazwy = [rywal["nazwa"], rywal["krotko"]] + r.get("nazwy_w_zwiazkach", [])
    return {"data": mecz["data"], "godzina": mecz.get("godzina"), "nazwy_rywala": nazwy}


MIESIACE_PL = ["styczeń", "luty", "marzec", "kwiecień", "maj", "czerwiec", "lipiec", "sierpień", "wrzesień",
               "październik", "listopad", "grudzień"]
MIESIACE_PL_MIEJSC = ["styczniu", "lutym", "marcu", "kwietniu", "maju", "czerwcu", "lipcu", "sierpniu", "wrześniu",
                      "październiku", "listopadzie", "grudniu"]


def zapas_licznika(bez_internetu):
    """Licznik wejść w stopce liczy od zera każdego miesiąca (klucz „wejscia-RRRRMM” w serwisie Abacus).
    Przy każdej przebudowie (ok. 9 razy dziennie) pobieramy liczbę z bieżącego i poprzedniego miesiąca
    i zapisujemy w dzienniku: dane/licznik.json + dane/dziennik-wejsc.csv. Bieżąca liczba jest też zapasem
    pokazywanym w stopce, gdy darmowy serwis liczników nie odpowiada."""
    L = getattr(C, "LICZNIK", {}) or {}
    if not L.get("wlaczony"):
        return
    plik = os.path.join(FOLDER, "dane", "licznik.json")
    try:
        zapis = json.load(open(plik, encoding="utf-8"))
    except Exception:
        zapis = {}
    dziennik = zapis.get("miesiace") or {}
    teraz = DZIS
    biezacy = f"{teraz.year}-{teraz.month:02d}"
    pop = date(teraz.year - (teraz.month == 1), 12 if teraz.month == 1 else teraz.month - 1, 1)
    poprzedni = f"{pop.year}-{pop.month:02d}"
    zmiana = False
    if not bez_internetu:
        import urllib.request
        for mies in (poprzedni, biezacy):
            klucz = f'{L["przestrzen"]}/{L["klucz"]}-{mies.replace("-", "")}'
            try:
                with urllib.request.urlopen(f"https://abacus.jasoncameron.dev/get/{klucz}", timeout=20) as odp:
                    wartosc = int(json.load(odp).get("value") or 0)
            except Exception as blad:
                if getattr(blad, "code", None) == 404:
                    wartosc = 0                         # w tym miesiącu jeszcze nikt nie wszedł
                else:
                    print(f"  UWAGA: licznik wejść {mies} –", type(blad).__name__, "(zostaje ostatnia znana liczba)")
                    continue
            if mies == poprzedni and mies not in dziennik and wartosc == 0:
                continue                                 # nie dopisujemy pustych miesięcy sprzed startu licznika
            if wartosc > int(dziennik.get(mies) or 0):
                dziennik[mies] = wartosc
                zmiana = True
    if zmiana:
        zapis = {"miesiace": dict(sorted(dziennik.items())), "aktualizacja": DZIS.isoformat(),
                 "opis": "Liczba wejść na volleykobylka.pl w każdym miesiącu (wejście = przyjście na stronę z zewnątrz)."}
        json.dump(zapis, open(plik, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        with open(os.path.join(FOLDER, "dane", "dziennik-wejsc.csv"), "w", encoding="utf-8-sig") as f:
            f.write("Miesiąc;Rok;Wejścia\n")
            for m, w in sorted(dziennik.items()):
                r, mm = m.split("-")
                f.write(f"{MIESIACE_PL[int(mm) - 1]};{r};{w}\n")
    S.LICZNIK_ZAPAS = int(dziennik.get(biezacy) or 0)
    S.LICZNIK_MIESIAC = biezacy.replace("-", "")
    S.LICZNIK_DZIENNIK = dict(sorted(dziennik.items()))


def main():
    bez_internetu = "--bez-internetu" in sys.argv
    zapas_licznika(bez_internetu)
    print("Pobieram dane ze stron związkowych..." if not bez_internetu else "Tryb bez internetu – używam kopii danych.")
    dane, uwagi = zrodla.pobierz_dane(C.ZRODLA_ZWIAZKOWE, C.RYWALE, bez_internetu=bez_internetu)
    for u in uwagi:
        print("  UWAGA:", u)
    przygotuj_herby(bez_internetu)   # przed kopiowaniem img/, żeby nowe herby trafiły na serwer
    b = Budowa(dane)

    # Aktualności z Facebooka (drużyna i Akademia) – sprawdzane 2 razy dziennie
    nowe_fb_druzyny = None
    posty_fb_druzyny = []
    for czesc in ("druzyna", "akademia"):
        try:
            zapisane, nowe, uwaga = zrodla.aktualnosci_fb(czesc, C.POSTY_FB, bez_internetu)
        except Exception as blad:
            zapisane, nowe, uwaga = [], None, f"aktualności FB ({czesc}): {type(blad).__name__} – pomijam"
        if uwaga:
            print("  UWAGA:", uwaga)
        kategoria = (C.POSTY_FB.get(czesc) or {}).get("kategoria", "Klub")
        if czesc == "druzyna":
            nowe_fb_druzyny = nowe
            posty_fb_druzyny = zapisane
            b.newsy = sorted(C.NEWSY + newsy_z_fb(zapisane, kategoria),
                             key=lambda n: n.get("czas") or n["data"], reverse=True)
        else:
            b.newsy_akademii = newsy_z_fb(zapisane, kategoria)
        print(f"  Aktualności z FB ({czesc}): {len(zapisane)}" + (" – sprawdzono nowe posty" if nowe is not None else ""))
    podepnij_relacje(b.mecze, b.newsy)
    try:
        podepnij_mvp(b.mecze, posty_fb_druzyny)
    except Exception as blad:
        print(f"  UWAGA: MVP z postów FB: {type(blad).__name__} – pomijam")

    # Posty z Instagrama/Facebooka: zapowiedź meczu i zdjęcia wygranych.
    # Każdy błąd tylko pomija zdjęcie – nigdy nie zatrzymuje budowania strony.
    posty, uwaga = zrodla.pobierz_posty(C.META, bez_internetu)
    if posty is None and nowe_fb_druzyny:
        posty, uwaga = nowe_fb_druzyny, None    # te same posty z FB drużyny służą też do zapowiedzi
    if uwaga:
        print("  UWAGA:", uwaga)
    for m in b.mecze:
        if m.get("wygrana"):
            klucz = f"{m['druzyna']}-{m['data'].isoformat()}"
            try:
                m["zdjecie_wygranej"] = m.get("zdjecie_wygranej") or zrodla.zdjecie_wygranej(
                    klucz, m["data"], posty, C.ZDJECIA_WYGRANYCH)
            except Exception as blad:
                print(f"  UWAGA: zdjęcie wygranej {klucz}: {type(blad).__name__} – pomijam")
    # Grafika „Wynik meczu” dla każdego rozegranego meczu seniorek (powstaje raz, potem leży w img/grafiki/)
    try:
        import grafika
        grafika.zapisz_grafiki_wynikow(b.rozegrane, os.path.join(FOLDER, "img"), C.DRUZYNY[GLOWNA]["liga"],
                                        S.DNI, S.MIESIACE_DOP, C.KLUB.get("dopisek_grafiki"), S.inicjaly)
    except Exception as blad:
        print(f"  UWAGA: grafiki wyników: {type(blad).__name__}: {blad} – pomijam")
    try:
        b.zapowiedz = zrodla.pobierz_zapowiedz(C.ZAPOWIEDZ, posty, mecz_do_zapowiedzi(b.najblizszy))
    except Exception as blad:
        print(f"  UWAGA: zapowiedź: {type(blad).__name__} – pomijam")

    # Czyścimy folder wynikowy i kopiujemy pliki stałe (CSS, JS, zdjęcia)
    if os.path.isdir(WYJSCIE):
        shutil.rmtree(WYJSCIE)
    shutil.copytree(os.path.join(FOLDER, "zasoby"), os.path.join(WYJSCIE, "zasoby"))
    zmniejsz_zasoby(os.path.join(WYJSCIE, "zasoby"))
    if os.path.isdir(os.path.join(FOLDER, "img")):
        shutil.copytree(os.path.join(FOLDER, "img"), os.path.join(WYJSCIE, "img"))

    # Podgląd linku (Facebook, Messenger, WhatsApp): grafika z najbliższym meczem.
    # Nazwa pliku z datą meczu – nowy mecz = nowy adres, więc Facebook nie pokaże starego obrazka.
    global OG_ZAPOWIEDZ
    if b.najblizszy:
        try:
            import grafika
            z = S.postac_do_plakatu(b.najblizszy)
            plik = f"img/og/zapowiedz-{b.najblizszy['data'].isoformat()}.jpg"
            os.makedirs(os.path.join(WYJSCIE, "img", "og"), exist_ok=True)
            grafika.grafika_og(b.najblizszy, os.path.join(FOLDER, "img"),
                               os.path.join(FOLDER, "img", z["zdjecie"]) if z else None,
                               z, S.DNI, S.MIESIACE_DOP, S.inicjaly,
                               C.KLUB.get("wstep_wolny"), C.KLUB.get("dopisek_grafiki")).save(os.path.join(WYJSCIE, plik), "JPEG", quality=86, optimize=True)
            OG_ZAPOWIEDZ = plik
        except Exception as blad:
            print(f"  UWAGA: podgląd linku: {type(blad).__name__}: {blad} – zostaje ogólna grafika")

    b.wybor()
    b.strona_glowna()
    b.terminarz()
    b.druzyny()
    b.aktualnosci()
    b.akademia()
    b.poradniki()
    b.galeria()
    b.sponsorzy()
    b.profile()
    b.strony_meczow()
    b.o_klubie()
    b.sklep()
    b.kontakt()
    b.polityka()
    b.nie_znaleziono()
    b.kalendarze()
    baza = C.KLUB["adres_strony"].rstrip("/") + "/"
    zapisz("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {baza}sitemap.xml\n")
    # Mapa strony dla Google (Search Console) – wszystkie podstrony, najważniejsze na początku
    waga = {"index.html": "1.0", S.START_DRUZYNY: "0.9", "akademia.html": "0.9", "terminarz.html": "0.8",
            "druzyny.html": "0.7", "aktualnosci.html": "0.7", "kontakt.html": "0.6"}
    puste = set()
    if not S.galeria_ma_zdjecia():
        puste.add("galeria.html")
    if not S.sklep_ma_produkty():
        puste.add("sklep.html")
    def wpis(s_):
        ext = DODATKI_SEO.get(s_, {})
        data = ext.get("data") or DZIS.isoformat()
        obrazy = "".join(f"<image:image><image:loc>{baza}{o}</image:loc></image:image>" for o in ext.get("obrazy", []) if o)
        return (f"  <url><loc>{adres_pelny(s_)}</loc><lastmod>{data[:10]}</lastmod>"
                f"<priority>{waga.get(s_, '0.5')}</priority>{obrazy}</url>\n")
    lista_map = sorted(set(STRONY_HTML) - puste, key=lambda s_: (-float(waga.get(s_, '0.5')), s_))
    wpisy = "".join(wpis(s_) for s_ in lista_map)
    zapisz("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + wpisy + "</urlset>\n")
    zglos_indexnow([adres_pelny(s_) for s_ in lista_map])
    b.statystyki(sorted(set(STRONY_HTML)))   # po mapie strony – statystyki nie trafiają do Google
    # Ikona strony: favicon.ico w katalogu głównym (przeglądarki i Google szukają jej tam) + manifest
    if os.path.isfile(os.path.join(FOLDER, "img", "favicon.ico")):
        shutil.copy(os.path.join(FOLDER, "img", "favicon.ico"), os.path.join(WYJSCIE, "favicon.ico"))
    # Strona jak aplikacja: po „Dodaj do ekranu głównego” otwiera się bez paska przeglądarki
    zapisz("site.webmanifest", json.dumps({
        "name": "Volley Kobyłka – Easy Wrap Volley", "short_name": "Volley Kobyłka",
        "description": "Mecze, wyniki, tabela i kadra Easy Wrap Volley Kobyłka",
        "id": "./", "start_url": f"./{S.START_DRUZYNY}?z=aplikacja", "scope": "./",
        "display": "standalone", "orientation": "portrait",
        "theme_color": "#002F6C", "background_color": "#ffffff", "lang": "pl",
        "icons": [{"src": "img/favicon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
                  {"src": "img/favicon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"}],
        "shortcuts": [{"name": "Terminarz", "url": "./terminarz.html"},
                      {"name": "Tabela", "url": "./terminarz.html#tabela"},
                      {"name": "Kadra", "url": "./druzyny.html"},
                      {"name": "Akademia Siatkówki", "url": "./akademia.html"}],
    }, ensure_ascii=False))
    # Service worker: strona działa też bez internetu (ostatnio odwiedzone podstrony + terminarz)
    sw = open(os.path.join(FOLDER, "zasoby", "sw-szablon.js"), encoding="utf-8").read()
    sw = sw.replace("__WERSJA__", f"{b.wersja}-{datetime.now().strftime('%Y%m%d%H%M')}") \
           .replace("__START__", S.START_DRUZYNY).replace("__ZASOB_V__", b.wersja)
    zapisz("sw.js", sw)

    # IndexNow (Bing, Yandex, Seznam): plik z kluczem w katalogu głównym – pozwala szybko zgłaszać zmiany strony
    zapisz(f"{INDEXNOW_KLUCZ}.txt", INDEXNOW_KLUCZ)

    nm = b.najblizszy
    print(f"\nGotowe! Strona jest w folderze: {WYJSCIE}")
    print(f"  Meczów: {len(b.mecze)}, aktualności: {len(b.newsy)}")
    if nm:
        g, h = nm["strony"]
        print(f"  Najbliższy mecz: {nm['data']} {nm.get('godzina') or '(godzina wkrótce)'} – {g['krotko']} vs {h['krotko'] if h else ''}")


if __name__ == "__main__":
    main()
