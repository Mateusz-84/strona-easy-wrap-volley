# =====================================================================
#  SZABLONY.PY – WYGLĄD ELEMENTÓW STRONY (HTML)
# ---------------------------------------------------------------------
#  Tu są „klocki”, z których build.py składa podstrony:
#  układ strony (nagłówek, menu, stopka), karta meczu, karta zawodniczki,
#  tabela, plakat meczu itd.
#  Treści NIE wpisuje się tutaj – tylko w content.py.
#
#  Zmienna p = „prefiks ścieżki”: "" dla stron w folderze głównym,
#  "../" dla stron w podfolderach (np. aktualnosci/). Dzięki temu
#  linki do CSS, zdjęć i innych stron działają z każdego miejsca.
# =====================================================================

import os
from datetime import date, datetime, timedelta, timezone
from html import escape

import content as C

FOLDER = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------
# Polskie nazwy dni i miesięcy
# ---------------------------------------------------------------------
DNI_KROTKO = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nie"]
DNI = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
MIES_KROTKO = ["Sty", "Lut", "Mar", "Kwi", "Maj", "Cze", "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru"]
MIESIACE = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
            "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
MIESIACE_DOP = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
                "lipca", "sierpnia", "września", "października", "listopada", "grudnia"]

# Menu główne: (plik, nazwa, na_komputerze)
#   na_komputerze=False → pozycja jest tylko w menu na telefonie i w stopce,
#   żeby menu na komputerze miało 6 najważniejszych pozycji.
#   Galeria i Sklep pokazują się dopiero, gdy mają treść (zdjęcia / produkty).
# volleykobylka.pl (index.html) to strona wyboru: drużyna albo Akademia.
# Część drużyny zaczyna się od START_DRUZYNY, Akademia ma własną stronę akademia.html.
START_DRUZYNY = "easy-wrap-volley.html"
MENU = [
    (START_DRUZYNY, "Start", False),
    ("aktualnosci.html", "Aktualności", True),
    ("druzyny.html", "Drużyny", True),
    ("terminarz.html", "Terminarz", True),
    ("galeria.html", "Galeria", False),
    ("sklep.html", "Sklep", False),
    ("sponsorzy.html", "Sponsorzy", True),
    ("o-klubie.html", "O klubie", False),
    ("kontakt.html", "Kontakt", True),
]


# Ikony serwisów społecznościowych (proste znaki SVG w kolorze tekstu – currentColor)
IKONY_SOCIAL = {
    "facebook": ("Facebook", '<path fill="currentColor" d="M13.5 22v-8h2.7l.4-3.2h-3.1V8.8c0-.9.3-1.6 1.6-1.6h1.7V4.4c-.3 0-1.3-.1-2.5-.1-2.5 0-4.1 1.5-4.1 4.2v2.3H7.5V14h2.7v8z"/>'),
    "instagram": ("Instagram", '<rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="2"/>'
                               '<circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="2"/>'
                               '<circle cx="17.3" cy="6.7" r="1.3" fill="currentColor"/>'),
    "youtube": ("YouTube", '<path fill="currentColor" fill-rule="evenodd" d="M6 5h12a4 4 0 0 1 4 4v6a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V9a4 4 0 0 1 4-4zm4 3.8v6.4l5.6-3.2z"/>'),
}


def social_linki(klasa, z_lista=False, zrodlo=None, kto="klubu"):
    """Ikony Facebook / Instagram / YouTube z linkami do profili (domyślnie drużyny – C.KLUB)."""
    zrodlo = zrodlo or C.KLUB
    linki = []
    for klucz, (nazwa, ksztalt) in IKONY_SOCIAL.items():
        adres = zrodlo.get(klucz)
        if not adres:
            continue
        a = (f'<a class="ikona-social" href="{e(adres)}" target="_blank" rel="noopener" '
             f'aria-label="{nazwa} – profil {kto}" title="{nazwa}">'
             f'<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">{ksztalt}</svg></a>')
        linki.append(f"<li>{a}</li>" if z_lista else a)
    return "".join(linki)


def galeria_ma_zdjecia():
    for a in C.GALERIA:
        folder = os.path.join(FOLDER, "img", "galeria", a["folder"])
        if os.path.isdir(folder) and any(f.lower().endswith((".webp", ".jpg", ".jpeg", ".png")) for f in os.listdir(folder)):
            return True
    return False


def sklep_ma_produkty():
    return bool(C.SKLEP.get("produkty"))


def menu_pozycje():
    """Pozycje menu bez pustych działów (Galeria bez zdjęć, Sklep bez produktów)."""
    ukryte = set()
    if not galeria_ma_zdjecia():
        ukryte.add("galeria.html")
    if not sklep_ma_produkty():
        ukryte.add("sklep.html")
    return [m for m in MENU if m[0] not in ukryte]


def e(tekst):
    """Bezpieczne wstawienie tekstu do HTML (zamienia < > & " na encje)."""
    return escape(str(tekst)) if tekst is not None else ""


def data_pl(d, z_rokiem=True):
    """2026-10-24 → „24 października 2026”."""
    return f"{d.day} {MIESIACE_DOP[d.month - 1]}" + (f" {d.year}" if z_rokiem else "")


def przesuniecie_pl(d):
    """Polska strefa czasu: +02:00 latem (od ostatniej niedzieli marca do ostatniej niedzieli października)."""
    def ostatnia_niedziela(rok, miesiac):
        dzien = date(rok, miesiac, 31)
        return dzien - timedelta(days=(dzien.weekday() + 1) % 7)
    lato = ostatnia_niedziela(d.year, 3) <= d < ostatnia_niedziela(d.year, 10)
    return 2 if lato else 1


def iso_pl(d, godzina):
    """Data i godzina w formacie, który rozumie JavaScript, z polską strefą czasu."""
    g = godzina or "12:00"
    return f"{d.isoformat()}T{g}:00+0{przesuniecie_pl(d)}:00"


# ---------------------------------------------------------------------
# Zdjęcia i herby
# ---------------------------------------------------------------------
def jest_plik(sciezka):
    return bool(sciezka) and os.path.isfile(os.path.join(FOLDER, "img", sciezka))


def img(p, sciezka, alt, klasa="", lazy=True):
    """Znacznik <img> albo pusty tekst, gdy pliku nie ma (wtedy CSS pokaże grafikę zastępczą)."""
    if not jest_plik(sciezka):
        return ""
    ladowanie = ' loading="lazy" decoding="async"' if lazy else ' fetchpriority="high"'
    return f'<img class="{klasa}" src="{p}img/{e(sciezka)}" alt="{e(alt)}"{ladowanie}>'


def inicjaly(nazwa):
    slowa = [s for s in str(nazwa).replace(".", " ").split() if s]
    if not slowa:
        return "?"
    if slowa[0].isupper() and 2 <= len(slowa[0]) <= 4:
        return slowa[0]
    return "".join(s[0] for s in slowa[:2]).upper()


def skrot_hali(nazwa):
    """Związek podaje czasem kilka hal w jednym polu („hala A ; Hala dodatkowa: …”) – zostaw pierwszą."""
    if not nazwa:
        return ""
    n = nazwa.split(";")[0].strip()
    return n[:1].upper() + n[1:]


def licznik_html():
    """Mały licznik wyświetleń w stopce – liczbę wstawia main.js; bez JS/sieci element zostaje ukryty."""
    L = getattr(C, "LICZNIK", {}) or {}
    if not L.get("wlaczony"):
        return ""
    return (f'<span class="licznik-wysw" data-wyswietlenia="{e(L["przestrzen"])}/{e(L["klucz"])}" hidden>'
            f'<svg viewBox="0 0 24 24" width="13" height="13" aria-hidden="true"><path fill="currentColor" '
            f'd="M12 5C6.5 5 2.7 9.3 1.5 12c1.2 2.7 5 7 10.5 7s9.3-4.3 10.5-7C21.3 9.3 17.5 5 12 5zm0 11a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm0-6a2 2 0 1 0 0 4 2 2 0 0 0 0-4z"/></svg>'
            f'<span class="ukryte">Wyświetlenia strony: </span><span data-wyswietlenia-liczba></span></span>')


def herb_svg(tekst, kolor, klasa="herb"):
    rozmiar = 22 if len(tekst) <= 2 else 18 if len(tekst) == 3 else 14
    return (f'<svg class="{klasa}" viewBox="0 0 60 70" aria-hidden="true">'
            f'<path d="M30 2 56 10v24c0 17-11 28-26 34C15 62 4 51 4 34V10Z" fill="{e(kolor)}" stroke="#fff" stroke-width="3"/>'
            f'<text x="30" y="42" text-anchor="middle" font-family="Bebas Neue,Impact,sans-serif" '
            f'font-size="{rozmiar}" fill="#fff">{e(tekst)}</text></svg>')


def herb_nasz_svg(klasa="herb"):
    """Zastępczy herb klubu – podmień plik w img/herby/, a zniknie."""
    return (f'<svg class="{klasa}" viewBox="0 0 60 70" aria-hidden="true">'
            '<path d="M30 2 56 10v24c0 17-11 28-26 34C15 62 4 51 4 34V10Z" fill="#002F6C" stroke="#fff" stroke-width="3"/>'
            '<path d="M4 40 56 22v8L4 48Z" fill="#FFC72C"/>'
            '<path d="M30 6 33 22 27 30 32 44 28 66" fill="none" stroke="#069DDF" stroke-width="2.5"/>'
            '<text x="30" y="34" text-anchor="middle" font-family="Bebas Neue,Impact,sans-serif" font-size="18" fill="#fff">EWV</text></svg>')


def herb(p, druzyna, klasa="herb"):
    """Herb drużyny: nasz, rywala z content.RYWALE albo tarcza z inicjałami."""
    if druzyna is None:
        return ""
    if druzyna.get("nasza"):
        if jest_plik(C.KLUB["herb"]):
            return f'<img class="{klasa}" src="{p}img/{e(C.KLUB["herb"])}" alt="" aria-hidden="true">'
        return herb_nasz_svg(klasa)
    r = druzyna.get("rywal") or {}
    if jest_plik(r.get("herb")):
        return f'<img class="{klasa}" src="{p}img/{e(r["herb"])}" alt="" aria-hidden="true" loading="lazy">'
    return herb_svg(inicjaly(druzyna["krotko"]), r.get("kolor", "#3A4A63"), klasa)


# ---------------------------------------------------------------------
# Drobne elementy
# ---------------------------------------------------------------------
def sety_html(m):
    """Chipy setów; wygrany przez nas set jest wyróżniony."""
    if not m.get("sety"):
        return ""
    chipy = []
    for s in m["sety"]:
        try:
            a, b = (int(x) for x in s.split(":"))
        except ValueError:
            chipy.append(f"<span>{e(s)}</span>")
            continue
        nasz = (a > b) if m["u_siebie"] else (b > a)
        chipy.append(f'<span class="{"w" if nasz else ""}">{e(s)}</span>')
    return f'<div class="sety" aria-label="Wyniki setów">{"".join(chipy)}</div>'


def prezentuje(sekcja, p):
    """„Prezentowane przez [sponsor]” – jeśli w SPONSORZY ustawiono "prezentuje"."""
    for s in C.SPONSORZY.values():
        if s.get("prezentuje") == sekcja:
            logo = img(p, s.get("logo"), s["nazwa"], "prezentuje__logo") or f"<strong>{e(s['nazwa'])}</strong>"
            return f'<div class="prezentuje">Prezentowane przez {logo}</div>'
    return ""


def naglowek_sekcji(tytul, akcent="", link=None, link_tekst="", poziom="h2", id_=""):
    a = f" <span>{e(akcent)}</span>" if akcent else ""
    l = f'<a class="sekcja__link" href="{link}">{e(link_tekst)}</a>' if link else ""
    i = f' id="{id_}"' if id_ else ""
    return f'<div class="sekcja__glowa"><{poziom} class="sekcja__tytul"{i}>{e(tytul)}{a}</{poziom}>{l}</div>'


def zdjecie_naglowka(p, klucz):
    """Zdjęcie z content.ZDJECIA_NAGLOWKOW (albo bezpośrednia ścieżka w img/). Brak pliku = pusty tekst."""
    sciezka = C.ZDJECIA_NAGLOWKOW.get(klucz, klucz)
    return img(p, sciezka, "", "plakat__foto-img", lazy=False)


def plakat_podstrony(p, tytul, podtytul="", zdjecie=None, wariant=""):
    """
    Nagłówek podstrony w stylu plakatu.
    zdjecie: klucz z content.ZDJECIA_NAGLOWKOW (np. "terminarz") albo ścieżka w img/.
    Gdy pliku nie ma – sam tytuł na granatowym tle.
    """
    foto = zdjecie_naglowka(p, zdjecie) if zdjecie else ""
    return f"""
<section class="plakat {wariant}{' plakat--z-foto' if foto else ''}">
  {f'<div class="plakat__tlo" aria-hidden="true">{foto}</div>' if foto else ''}
  <div class="kontener">
    {f'<p class="plakat__nad">{e(podtytul)}</p>' if podtytul else ''}
    <h1 class="plakat__tytul">{e(tytul)}</h1>
  </div>
</section>"""


# ---------------------------------------------------------------------
# Górna belka – mini-tablica z licznikiem
#   Każdy kandydat (ostatni wynik, najbliższe mecze) jest w <template>.
#   JavaScript sam wybiera właściwy wg aktualnego czasu – dzięki temu
#   belka jest aktualna nawet między przebudowami strony.
# ---------------------------------------------------------------------
def belka(p, kandydaci):
    szablony = []
    for m in kandydaci:
        gosp, gosc = m["strony"]
        opis = f'{DNI_KROTKO[m["data"].weekday()]} {m["data"].strftime("%d.%m")}'
        if m.get("godzina"):
            opis += f' · {m["godzina"]}'
        if m.get("wynik"):  # wynik jest w środku zamiast „VS”, po prawej – wygrana/porażka
            prawa = f'<span class="belka__wynik">{"Wygrana" if m["wygrana"] else "Porażka"}</span>'
        else:
            prawa = ('<span class="licznik" data-licznik>'
                     '<span data-j="d">0<small>D</small></span><span data-j="h">00<small>G</small></span>'
                     '<span data-j="m">00<small>M</small></span><span data-j="s">00<small>S</small></span></span>')
        szablony.append(
            f'<template data-start="{iso_pl(m["data"], m.get("godzina"))}" '
            f'data-godzina="{"1" if m.get("godzina") else "0"}" data-rozegrany="{"1" if m.get("wynik") else "0"}">'
            f'<a class="belka__mecz" href="{p}terminarz.html">'
            f'{herb(p, gosp, "belka__herb")}<span class="belka__vs">{e(m["wynik"]) if m.get("wynik") else "VS"}</span>'
            f'{herb(p, gosc, "belka__herb") if gosc else ""}'
            f'<span class="belka__info">{e(opis)}<span class="ukryte"> {e(gosp["krotko"])} – {e(gosc["krotko"] if gosc else "")}</span></span></a>'
            f'{prawa}</template>')
    return f"""
<div class="belka" role="region" aria-label="Najbliższy mecz">
  <div class="kontener">
    <div class="belka__tablica" data-belka>{''.join(szablony)}</div>
    <nav class="belka__social" aria-label="Media społecznościowe">{social_linki("belka")}</nav>
  </div>
</div>"""


# ---------------------------------------------------------------------
# Układ każdej podstrony
# ---------------------------------------------------------------------
def glowa(pelny_tytul, opis, p, wersja, kolor="#002F6C", ikona="img/favicon.svg"):
    return f"""<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(pelny_tytul)}</title>
<meta name="description" content="{e(opis)}">
<meta name="theme-color" content="{kolor}">
<meta property="og:title" content="{e(pelny_tytul)}">
<meta property="og:description" content="{e(opis)}">
<meta property="og:locale" content="pl_PL">
<link rel="icon" href="{p}{ikona}">
<link rel="preload" href="{p}zasoby/fonty/bebas-neue-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{p}zasoby/fonty.css?v={wersja}">
<link rel="stylesheet" href="{p}zasoby/style.css?v={wersja}">
<script>document.documentElement.classList.add('js')</script>
<script src="{p}zasoby/main.js?v={wersja}" defer></script>
</head>"""


def logo_druzyny(p, wysokosc=48):
    return (f'<img src="{p}img/{e(C.KLUB["herb"])}" alt="" height="{wysokosc}">'
            if jest_plik(C.KLUB["herb"]) else herb_nasz_svg())


def uklad(tytul, opis, tresc, aktywna, p, belka_html, wersja):
    """Część DRUŻYNY (Easy Wrap Volley Kobyłka): własne logo, menu i FB/IG/YT."""
    menu = ""
    for plik, nazwa, glowne in menu_pozycje():
        biezaca = ' aria-current="page"' if plik == aktywna else ""
        klasa = "" if glowne else ' class="menu__dodatkowe"'
        menu += f'<li{klasa}><a href="{p}{plik}"{biezaca}>{e(nazwa)}</a></li>'
    skroty = "".join(f'<li><a href="{p}{plik}">{e(nazwa)}</a></li>'
                     for plik, nazwa, glowne in menu_pozycje() if not glowne and plik != START_DRUZYNY)
    pelny_tytul = C.KLUB["nazwa"] if aktywna == START_DRUZYNY else f"{tytul} – {C.KLUB['nazwa']}"
    rok = date.today().year
    return f"""{glowa(pelny_tytul, opis, p, wersja)}
<body class="strefa-druzyna">
<a class="przeskocz" href="#tresc">Przejdź do treści</a>
{belka_html}
<header class="naglowek">
  <div class="kontener">
    <a class="logo" href="{p}{START_DRUZYNY}">{logo_druzyny(p)}<span class="logo__tekst">{e(C.KLUB['nazwa_krotka'])}<small>Kobyłka</small></span></a>
    <button class="menu-przycisk" aria-expanded="false" aria-controls="menu"><span></span><span></span><span></span><span class="ukryte">Menu</span></button>
    <nav class="menu" id="menu" aria-label="Menu główne"><ul>{menu}</ul></nav>
  </div>
</header>
<main id="tresc">
{tresc}
</main>
<footer class="stopka">
  <div class="kontener">
    <div class="stopka__kolumny">
      <div><h2>{e(C.KLUB['nazwa'])}</h2><p>{e(C.KLUB['nazwa_prawna'])}<br>{e(C.KLUB['adres'])}</p></div>
      <div><h2>Kontakt</h2><p><a href="mailto:{e(C.KLUB['email'])}">{e(C.KLUB['email'])}</a>{f"<br>{e(C.KLUB['telefon'])}" if C.KLUB.get('telefon') else ''}</p></div>
      <div><h2>Obserwuj</h2><ul class="stopka__social">{social_linki("stopka", True)}</ul></div>
      <div><h2>Na skróty</h2><ul>
        {skroty}
        <li><a href="{p}sponsorzy.html">Zostań sponsorem</a></li>
        <li><a href="{p}akademia.html">Akademia Siatkówki Volley →</a></li>
        <li><a href="{p}akademia.html#ochrona">Ochrona małoletnich</a></li></ul></div>
    </div>
    <div class="stopka__dol"><span>© {rok} {e(C.KLUB['nazwa_prawna'])} · <a href="{p}index.html">volleykobylka.pl</a></span>
      {licznik_html()}
      <a href="{p}polityka-prywatnosci.html">Polityka prywatności i cookies</a></div>
  </div>
</footer>
</body>
</html>
"""


# Menu Akademii – jedna strona, przewijanie do sekcji
MENU_AKADEMII = [("o-akademii", "O Akademii"), ("cennik", "Cennik"), ("plan", "Plan treningów"),
                 ("zapisy", "Zapisy"), ("kontakt", "Kontakt")]


def uklad_akademii(tytul, opis, tresc, p, wersja):
    """Część AKADEMII SIATKÓWKI VOLLEY: własne logo, menu, stopka i tylko Facebook."""
    A = C.AKADEMIA
    menu = "".join(f'<li><a href="#{k}">{e(n)}</a></li>' for k, n in MENU_AKADEMII)
    logo = (f'<img src="{p}img/{e(A["logo"])}" alt="" width="52" height="52">' if jest_plik(A.get("logo")) else "")
    k = A.get("koordynator") or {}
    kontakt = "<br>".join(x for x in [
        e(k.get("imie") or ""),
        f'<a href="tel:{e((k.get("telefon") or "").replace(" ", ""))}">{e(k["telefon"])}</a>' if k.get("telefon") else "",
        f'<a href="mailto:{e(k["email"])}">{e(k["email"])}</a>' if k.get("email") else ""] if x)
    rok = date.today().year
    return f"""{glowa(f"{tytul}", opis, p, wersja, kolor="#1C6FD1", ikona=A.get("logo") and "img/" + A["logo"] or "img/favicon.svg")}
<body class="strefa-akademia">
<a class="przeskocz" href="#tresc">Przejdź do treści</a>
<div class="belka belka--akademia"><div class="kontener">
  <a class="belka__wroc" href="{p}index.html">← volleykobylka.pl</a>
  <a class="belka__druga" href="{p}{START_DRUZYNY}">Easy Wrap Volley Kobyłka – 2. liga ↗</a>
</div></div>
<header class="naglowek naglowek--akademia">
  <div class="kontener">
    <a class="logo" href="#tresc">{logo}<span class="logo__tekst">Akademia Siatkówki<small>Volley · Kobyłka</small></span></a>
    <button class="menu-przycisk" aria-expanded="false" aria-controls="menu"><span></span><span></span><span></span><span class="ukryte">Menu</span></button>
    <nav class="menu" id="menu" aria-label="Menu Akademii"><ul>{menu}</ul></nav>
  </div>
</header>
<main id="tresc">
{tresc}
</main>
<footer class="stopka stopka--akademia">
  <div class="kontener">
    <div class="stopka__kolumny">
      <div><h2>{e(A['nazwa'])}</h2><p>Hala sportowa<br>{e(C.KLUB['adres'])}</p></div>
      <div><h2>Kontakt</h2><p>{kontakt}</p></div>
      <div><h2>Obserwuj</h2><ul class="stopka__social">{social_linki("stopka", True, {"facebook": A.get("facebook")}, "Akademii")}</ul></div>
      <div><h2>Na skróty</h2><ul>
        <li><a href="#zapisy">Zapisy</a></li>
        <li><a href="#ochrona">Standardy ochrony małoletnich</a></li>
        <li><a href="{p}{START_DRUZYNY}">Easy Wrap Volley Kobyłka →</a></li></ul></div>
    </div>
    <div class="stopka__dol"><span>© {rok} {e(C.KLUB['nazwa_prawna'])} · <a href="{p}index.html">volleykobylka.pl</a></span>
      {licznik_html()}
      <a href="{p}polityka-prywatnosci.html">Polityka prywatności i cookies</a></div>
  </div>
</footer>
</body>
</html>
"""


def strona_wyboru(p, wersja):
    """volleykobylka.pl – tylko wybór: drużyna albo Akademia. Bez innych informacji."""
    A = C.AKADEMIA
    logo_ak = (f'<img class="wybor__logo wybor__logo--okragle" src="{p}img/{e(A["logo"])}" alt="" width="220" height="220">'
               if jest_plik(A.get("logo")) else "")
    logo_dr = (f'<img class="wybor__logo" src="{p}img/{e(C.KLUB["herb"])}" alt="" height="220">'
               if jest_plik(C.KLUB["herb"]) else herb_nasz_svg("wybor__logo"))
    rok = date.today().year
    return f"""{glowa("volleykobylka.pl – Easy Wrap Volley Kobyłka i Akademia Siatkówki Volley",
                 "Wybierz: drużyna Easy Wrap Volley Kobyłka (2. liga kobiet) albo Akademia Siatkówki Volley.", p, wersja)}
<body class="strefa-wybor">
<main class="wybor" id="tresc">
  <h1 class="ukryte">Co Cię interesuje?</h1>
  <a class="wybor__pole wybor__pole--druzyna" href="{p}{START_DRUZYNY}">
    {logo_dr}
    <span class="wybor__nazwa">Easy Wrap Volley<small>Kobyłka</small></span>
    <span class="wybor__opis">2. liga siatkówki kobiet</span>
    <span class="wybor__strzalka" aria-hidden="true">→</span>
  </a>
  <a class="wybor__pole wybor__pole--akademia" href="{p}akademia.html">
    {logo_ak}
    <span class="wybor__nazwa">Akademia Siatkówki<small>Volley</small></span>
    <span class="wybor__opis">Treningi dla dziewcząt</span>
    <span class="wybor__strzalka" aria-hidden="true">→</span>
  </a>
  <p class="wybor__dol"><span>© {rok} {e(C.KLUB['nazwa_prawna'])}</span>{licznik_html()}<a href="{p}polityka-prywatnosci.html">Polityka prywatności</a></p>
</main>
</body>
</html>
"""


# ---------------------------------------------------------------------
# Plakat najbliższego meczu (hero strony głównej)
# ---------------------------------------------------------------------
def postac_do_plakatu(m):
    """Wycięta zawodniczka na plakat meczu – co mecz inna (gdy mecz nie ma własnego zdjęcia)."""
    kandydatki = [z for z in C.KADRA if z["druzyna"] == "seniorki" and jest_plik(z.get("zdjecie"))]
    if not kandydatki:
        return None
    kandydatki.sort(key=lambda z: z["numer"])
    klucz = m["data"].toordinal() if m else date.today().toordinal()
    return kandydatki[klucz % len(kandydatki)]


def hero(p, m):
    # 1) własne zdjęcie meczu ("zdjecie_plakatu") albo domyślne z ZDJECIA_NAGLOWKOW → zdjęcie w ramce
    foto = img(p, (m or {}).get("zdjecie_plakatu"), "", "hero__foto", lazy=False) \
        or img(p, C.ZDJECIA_NAGLOWKOW.get("plakat_meczu"), "", "hero__foto", lazy=False)
    klasy = ["hero"]
    if foto:
        foto_html = f'<div class="hero__zdjecie hero__zdjecie--foto" aria-hidden="true">{foto}</div>'
        klasy.append("hero--z-foto")
    else:
        # 2) wycięta zawodniczka z kadry (co mecz inna) z wielkim numerem w tle
        z = postac_do_plakatu(m)
        if z:
            foto_html = (f'<div class="hero__postac" aria-hidden="true"><span class="hero__postac-nr">{e(z["numer"])}</span>'
                         f'<img class="hero__postac-img" src="{p}img/{e(z["zdjecie"])}" alt="" fetchpriority="high">'
                         f'<span class="hero__postac-podpis">#{e(z["numer"])} {e(z["imie"])} {e(z["nazwisko"])}</span></div>')
            klasy.append("hero--z-postacia")
        else:
            foto_html = ""

    if m is None:
        return f"""
<section class="{' '.join(klasy)}" id="hero">
  {foto_html}
  <div class="kontener"><div class="hero__tresc">
    <span class="hero__etykieta">{e(C.DRUZYNY['seniorki']['liga'])}</span>
    <h1 class="hero__tytul-sezon">Sezon<br>trwa</h1>
    <div class="hero__przyciski"><a class="btn btn--zolty" href="{p}terminarz.html">Terminarz i wyniki →</a></div>
  </div></div>
</section>"""

    gosp, gosc = m["strony"]
    wyjazd = not m["u_siebie"]
    if wyjazd:
        klasy.append("hero--wyjazd")
    d = m["data"]
    godzina = (f'<div class="hero__godzina"><strong>{e(m["godzina"])}</strong>godzina meczu</div>' if m.get("godzina")
               else '<div class="hero__godzina hero__godzina--brak"><strong>Godzina wkrótce</strong>ustala organizator</div>')
    miejsce = skrot_hali(m.get("hala")) or ("Hala do potwierdzenia" if wyjazd else C.HALA_DOMOWA["nazwa"])
    adres = m.get("adres") or ("" if wyjazd else C.HALA_DOMOWA["adres"])
    mapa = ("https://www.google.com/maps/search/?api=1&query=" + "+".join(adres.split())) if adres else None

    sponsor = ""
    s = C.SPONSORZY.get(m.get("sponsor_meczu") or "")
    if s:
        logo = img(p, s.get("logo"), s["nazwa"], "logo-sponsora__img") or e(s["nazwa"])
        sponsor = f'<div class="hero__sponsor">Sponsor meczu <span class="logo-sponsora">{logo}</span></div>'

    # Jeden główny przycisk, reszta jako lżejsze linki
    przyciski = [f'<a class="btn btn--zolty" href="{p}kalendarz/{m["plik_ics"]}" download>Dodaj do kalendarza</a>']
    if m.get("transmisja"):
        przyciski.append(f'<a class="hero__link" href="{e(m["transmisja"])}" rel="noopener">Transmisja ↗</a>')
    if mapa:
        przyciski.append(f'<a class="hero__link" href="{e(mapa)}" rel="noopener">Dojazd ↗</a>')

    druzyna_gosc = (f'<span class="hero__vs">vs</span><div class="hero__druzyna">{herb(p, gosc)}<span class="nazwa">{e(gosc["krotko"])}</span></div>'
                    if gosc else "")
    return f"""
<section class="{' '.join(klasy)}" id="hero" aria-labelledby="hero-tytul">
  {foto_html}
  <div class="kontener"><div class="hero__tresc">
    <div class="hero__gora"><span class="hero__etykieta">{'Mecz wyjazdowy' if wyjazd else 'Mecz u siebie'}</span>
    <span class="hero__liga">{e(m['liga'])}</span></div>
    <h1 class="ukryte" id="hero-tytul">Najbliższy mecz: {e(gosp['nazwa'])} – {e(gosc['nazwa'] if gosc else '')}, {e(data_pl(d))}</h1>
    <div class="hero__druzyny" aria-hidden="true">
      <div class="hero__druzyna">{herb(p, gosp)}<span class="nazwa">{e(gosp['krotko'])}</span></div>
      {druzyna_gosc}
    </div>
    <div class="hero__data">
      <span class="hero__dzien">{d.day}</span>
      <span class="hero__dzien-opis">{DNI[d.weekday()]}<span>{MIESIACE_DOP[d.month - 1]}</span></span>
    </div>
    <div class="hero__szczegoly">
      {godzina}
      <div class="hero__hala"><strong>{e(miejsce)}</strong>{e(adres)}</div>
    </div>
    <div class="hero__przyciski">{''.join(przyciski)}</div>
    {sponsor}
  </div></div>
</section>"""


# ---------------------------------------------------------------------
# Zapowiedź meczu – plakat z FB/IG pokazywany przez kilka sekund
#   Domyślnie ukryty (hidden) – pokazuje go JavaScript, więc bez JS nic nie zasłania strony.
# ---------------------------------------------------------------------
def okienko_zapowiedzi(p, z, konfig, mecz):
    if not z or not jest_plik(z.get("plik")) or mecz is None:
        return ""
    gosp, gosc = mecz["strony"]
    opis = f"Zapowiedź meczu {gosp['krotko']} – {gosc['krotko'] if gosc else ''}, {data_pl(mecz['data'])}"
    zrodlo = ""
    if z.get("link"):
        serwis = "Instagramie" if "instagram" in z["link"] else "Facebooku"
        zrodlo = f'<a class="zapowiedz__zrodlo" href="{e(z["link"])}" rel="noopener">Zobacz post na {serwis}</a>'
    raz = "1" if konfig.get("raz_na_wizyte", True) else "0"
    return f"""
<div class="zapowiedz" data-zapowiedz data-sekundy="{int(konfig.get('sekundy', 3))}" data-klucz="{e(z.get('klucz'))}"
     data-raz="{raz}" role="dialog" aria-modal="true" aria-label="{e(opis)}" hidden>
  <div class="zapowiedz__ramka">
    <img class="zapowiedz__img" src="{p}img/{e(z['plik'])}" alt="{e(opis)}" decoding="async">
    <button class="zapowiedz__zamknij" type="button" data-zapowiedz-zamknij aria-label="Zamknij zapowiedź">×</button>
    <div class="zapowiedz__pasek" aria-hidden="true"><span></span></div>
    {zrodlo}
  </div>
</div>"""


# ---------------------------------------------------------------------
# Karta meczu – „plakat” z wielką datą
# ---------------------------------------------------------------------
def karta_meczu(p, m):
    gosp, gosc = m["strony"]
    d = m["data"]
    klasy = ["mecz"]
    if m["druzyna"] != "seniorki":
        klasy.append("mecz--inne")
        typ = C.DRUZYNY.get(m["druzyna"], {}).get("krotko", "")
    elif m["u_siebie"]:
        typ = "Mecz u siebie"
    else:
        klasy.append("mecz--wyjazd")
        typ = "Mecz wyjazdowy"

    if m.get("najblizszy"):
        klasy.append("mecz--najblizszy")
    if m.get("wynik"):
        etykieta = ('<span class="wynik-etykieta">Wygrana</span>' if m["wygrana"]
                    else '<span class="wynik-etykieta wynik-etykieta--p">Porażka</span>')
        a, b = m["wynik"].split(":")
    elif d < date.today():  # mecz już był, związek jeszcze nie podał wyniku
        etykieta = '<span class="wynik-etykieta wynik-etykieta--p">Wynik wkrótce</span>'
        a = b = ""
    else:
        etykieta = f'<span class="mecz__godz">{e(m["godzina"])}</span>' if m.get("godzina") else ""
        a = b = ""

    def wiersz(strona, punkty):
        return (f'<div class="mecz__para">{herb(p, strona)}<span>{e(strona["krotko"])}</span>'
                f'{f"<b>{e(punkty)}</b>" if punkty != "" else ""}</div>')

    pary = wiersz(gosp, a) + (wiersz(gosc, b) if gosc else "")
    miejsce = skrot_hali(m.get("hala"))
    if m.get("adres") and not m["u_siebie"]:
        miejsce = (miejsce + " · " if miejsce else "") + m["adres"].split(",")[-1].strip()
    if not m.get("godzina") and not m.get("wynik") and d >= date.today():
        miejsce = "Godzina wkrótce" + (f" · {miejsce}" if miejsce else "")
    wstazka = '<div class="mecz__wstazka">Najbliższy mecz</div>' if m.get("najblizszy") else ""
    # Wygrany mecz: zdjęcie z posta o wygranej jako „znak wodny” w tle karty
    tlo = ""
    if m.get("wygrana") and jest_plik(m.get("zdjecie_wygranej")):
        klasy.append("mecz--z-tlem")
        tlo = f'<img class="mecz__tlo" src="{p}img/{e(m["zdjecie_wygranej"])}" alt="" aria-hidden="true" loading="lazy" decoding="async">'
    dodatki = ""
    if m.get("mvp"):
        dodatki += f'<div class="mecz__mvp">MVP: <strong>{e(m["mvp"])}</strong></div>'
    if m.get("relacja"):
        dodatki += f'<a class="mecz__link" href="{p}aktualnosci/{e(m["relacja"])}.html">Relacja →</a>'

    return f"""
<article class="{' '.join(klasy)}" data-druzyna="{e(m['druzyna'])}" data-stan="{'rozegrany' if m.get('wynik') else 'nadchodzacy'}">
  {tlo}{wstazka}<div class="mecz__gora"><span class="mecz__typ">{e(typ)}</span>{etykieta}</div>
  <div class="mecz__data"><span class="dz">{DNI_KROTKO[d.weekday()]}</span><span class="nr">{d.day}</span><span class="ms">{MIES_KROTKO[d.month - 1]}</span>
    <time class="ukryte" datetime="{d.isoformat()}">{e(data_pl(d))}</time></div>
  <div class="mecz__pary">{pary}</div>
  <div class="mecz__dol">{sety_html(m)}{e(miejsce)}{dodatki}</div>
</article>"""


# ---------------------------------------------------------------------
# Karta zawodniczki – gigantyczny numer, zdjęcie albo inicjały
# ---------------------------------------------------------------------
def karta_zawodniczki(p, z):
    zdjecie = img(p, z.get("zdjecie"), f"{z['imie']} {z['nazwisko']}", "zawodniczka__foto")
    if not zdjecie:  # NIGDY szara sylwetka – inicjały w barwach klubu
        zdjecie = f'<span class="zawodniczka__inicjaly" aria-hidden="true">{e(z["imie"][0] + z["nazwisko"][0])}</span>'
    szczegoly = []
    if z.get("w_klubie_od"):
        szczegoly.append(("W klubie od", z["w_klubie_od"]))
    if z.get("urodzona"):
        szczegoly.append(("Urodzona", date.fromisoformat(z["urodzona"]).strftime("%d.%m.%Y")))
    if z.get("wzrost"):
        szczegoly.append(("Wzrost", f"{z['wzrost']} cm"))
    dl = "".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a, b in szczegoly)
    wiecej = f'<div class="zawodniczka__wiecej"><div><dl>{dl}</dl></div></div>' if dl else ""
    kapitan = ' <span class="kapitan" title="Kapitan">C</span>' if z.get("kapitan") else ""
    return f"""
<article class="zawodniczka{'' if dl else ' zawodniczka--statyczna'}"{' tabindex="0"' if dl else ''} data-pozycja="{e(z['pozycja'])}">
  <span class="zawodniczka__numer" aria-hidden="true">{e(z['numer'])}</span>
  {zdjecie}
  <div class="zawodniczka__opis">
    <span class="zawodniczka__poz">{e(z['pozycja'])} · #{e(z['numer'])}{kapitan}</span>
    <h3><span>{e(z['imie'])}</span>{e(z['nazwisko'])}</h3>
    {wiecej}
  </div>
</article>"""


# ---------------------------------------------------------------------
# Tabela ligowa
# ---------------------------------------------------------------------
def tabela_html(p, wiersze, opis_druzyny, podpis):
    if not wiersze:
        return '<p class="pusto">Tabela pojawi się po pierwszej kolejce.</p>'
    tr = []
    for w in wiersze:
        d = opis_druzyny(w["nazwa"])
        tr.append(
            f'<tr{" class=nasz" if w["nasz"] else ""}><td>{w["lp"]}</td>'
            f'<td><span class="tabela__druzyna">{herb(p, d, "tabela__herb")}{e(d["krotko"])}</span></td>'
            f'<td>{w["mecze"]}</td><td class="ukryj-mobile">{w["zwyciestwa"]}</td>'
            f'<td class="ukryj-mobile">{w["sety_plus"]}:{w["sety_minus"]}</td><td class="pkt">{w["pkt"]}</td></tr>')
    return f"""
<div class="tabela-ramka"><table class="tabela">
  <caption class="ukryte">{e(podpis)}</caption>
  <thead><tr><th scope="col">#</th><th scope="col">Drużyna</th><th scope="col" title="Mecze">M</th>
  <th scope="col" class="ukryj-mobile" title="Zwycięstwa">Zw</th><th scope="col" class="ukryj-mobile">Sety</th><th scope="col">Pkt</th></tr></thead>
  <tbody>{''.join(tr)}</tbody>
</table></div>"""


# ---------------------------------------------------------------------
# Karta aktualności
# ---------------------------------------------------------------------
def karta_newsa(p, n, duza=False):
    d = date.fromisoformat(n["data"])
    foto = img(p, n.get("zdjecie"), n["tytul"], "news__img")
    if not foto:  # brak zdjęcia: herb klubu + kategoria zamiast pustego pola
        foto = (f'<img class="news__herb" src="{p}img/herby/easy-wrap-volley.png" alt="" aria-hidden="true" loading="lazy">'
                f'<span class="news__znak" aria-hidden="true">{e(n["kategoria"])}</span>')
    return f"""
<a class="news{' news--duzy' if duza else ''}{'' if n.get('zdjecie') and jest_plik(n.get('zdjecie')) else ' news--bez-foto'}" href="{p}aktualnosci/{e(n['adres'])}.html">
  <span class="news__foto foto-{sum(map(ord, n['adres'])) % 4}">{foto}</span>
  <div class="news__tresc"><span class="news__kat">{e(n['kategoria'])}<time datetime="{d.isoformat()}">{d.strftime('%d.%m.%Y')}</time></span>
  <h3>{e(n['tytul'])}</h3>{f"<p>{e(n['zajawka'])}</p>" if duza and n.get('zajawka') else ''}</div>
</a>"""


def akapity(tekst):
    """Zwykły tekst z content.py → akapity HTML (pusta linia = nowy akapit)."""
    czesci = [c.strip() for c in str(tekst or "").strip().split("\n\n") if c.strip()]
    return "".join(f"<p>{e(' '.join(c.split()))}</p>" for c in czesci)
