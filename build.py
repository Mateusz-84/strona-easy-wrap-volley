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
from szablony import e       # noqa: E402

WYJSCIE = os.path.join(FOLDER, "strona")
GLOWNA = "seniorki"          # drużyna pokazywana w belce i na plakacie
DZIS = date.today()


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
        return {"nazwa": C.KLUB["nazwa"], "krotko": C.KLUB["nazwa_krotka"], "nasza": True}
    for r in C.RYWALE.values():
        warianty = {zrodla.norm(x) for x in r.get("nazwy_w_zwiazkach", [])} | {zrodla.norm(r["skrot"])}
        if n in warianty:
            return {"nazwa": nazwa, "krotko": r["skrot"], "rywal": r, "nasza": False}
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
def zapisz(sciezka, tekst):
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

    # --- wspólny układ ---------------------------------------------------
    def strona(self, plik, tytul, opis, tresc, aktywna=None, p=None):
        if p is None:
            p = "../" * plik.count("/")
        kandydaci = self.rozegrane[-1:] + self.nadchodzace[:4]
        html = S.uklad(tytul, opis, tresc(p), aktywna or plik, p, S.belka(p, kandydaci), self.wersja)
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
<section class="sekcja" aria-labelledby="mecze-tytul">
  <div class="kontener" data-filtrowanie>
    {S.naglowek_sekcji('Mecze', 'i wyniki', p + 'terminarz.html', 'Pełny terminarz', id_='mecze-tytul')}
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
      {S.tabela_html(p, self.tabela(), opis_druzyny, C.DRUZYNY[GLOWNA]['liga'])}
    </div>
  </div>
</section>

<section class="sekcja sekcja--biala" aria-labelledby="kadra-tytul">
  <div class="kontener">
    {S.naglowek_sekcji('Nasza', 'kadra', p + 'druzyny.html', 'Wszystkie zawodniczki', id_='kadra-tytul')}
    {S.prezentuje('kadra', p)}
    <div class="kadra kadra--losowa pojaw" data-losowa-kadra>{''.join(S.karta_zawodniczki(p, z) for z in kadra)}</div>
    <p class="przesun" aria-hidden="true">Przesuń</p>
  </div>
</section>

<section class="sekcja" aria-labelledby="bento-tytul">
  <div class="kontener">
    {S.naglowek_sekcji('Więcej', 'niż mecz', id_='bento-tytul')}
    <div class="bento pojaw">{self.kafle(p)}</div>
  </div>
</section>

<section class="sekcja sekcja--bez-gory" aria-labelledby="news-tytul">
  <div class="kontener">
    {S.naglowek_sekcji('Aktualności', '', p + 'aktualnosci.html', 'Wszystkie', id_='news-tytul')}
    <div class="newsy pojaw">{''.join(S.karta_newsa(p, n, i == 0) for i, n in enumerate(newsy))}</div>
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
        wszystkie = [f"{p}img/{z['zdjecie']}" for z in C.KADRA
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
{S.plakat_podstrony(p, 'Terminarz i wyniki', C.DRUZYNY[GLOWNA]['liga'], 'terminarz')}
<nav class="skroty" aria-label="Na tej stronie"><div class="kontener">
  <a href="#nadchodzace">Nadchodzące</a><a href="#wyniki">Wyniki</a><a href="#tabela">Tabela</a><a href="#kalendarium">Kalendarium</a>
</div></nav>
<section class="sekcja" aria-labelledby="nadchodzace">
  <div class="kontener" data-filtrowanie>
    {S.naglowek_sekcji('Nadchodzące', 'mecze', id_='nadchodzace')}
    {S.prezentuje('terminarz', p)}
    {self.filtry_druzyn()}
    <div class="mecze mecze--siatka">{karty_przed}</div>
    <h2 class="sekcja__tytul sekcja__tytul--drugi" id="wyniki">Wyniki</h2>
    <div class="mecze mecze--siatka">{karty_po}</div>
    {info}
  </div>
</section>
<section class="sekcja sekcja--biala" id="tabela" aria-labelledby="tabela-tytul">
  <div class="kontener">
    {S.naglowek_sekcji('Tabela', C.DRUZYNY[GLOWNA]['liga'], id_='tabela-tytul')}
    {S.prezentuje('tabela', p)}
    {S.tabela_html(p, self.tabela(), opis_druzyny, C.DRUZYNY[GLOWNA]['liga'])}
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
      <div class="kal__siatka" role="grid" aria-label="Kalendarz miesiąca"></div>
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
    <div class="artykul__tresc">{S.akapity_fb(n['tresc']) if n.get('zrodlo') == 'fb' else S.akapity(n['tresc'])}</div>
    {S.przycisk_fb(n)}
    <p><a class="sekcja__link" href="{p}aktualnosci.html">← Wszystkie aktualności</a></p>
  </div>
</article>
<section class="sekcja sekcja--biala"><div class="kontener">
  {S.naglowek_sekcji('Czytaj', 'też')}
  <div class="newsy">{''.join(S.karta_newsa(p, x) for x in inne)}</div></div></section>"""
            self.strona(f"aktualnosci/{n['adres']}.html", n["tytul"], n.get("zajawka") or n["tytul"],
                        artykul, aktywna="aktualnosci.html")

    # --- AKADEMIA (osobna część strony) ------------------------------------
    def akademia(self):
        A = C.AKADEMIA
        p = ""
        grupy = "".join(
            f'<article class="grupa"><span class="grupa__wiek">{e(g["wiek"])}</span><h3>{e(g["nazwa"])}</h3><p>{e(g["opis"])}</p></article>'
            for g in A["grupy"])
        trenerzy = "".join(
            f'<li class="osoba">{S.img(p, t.get("zdjecie"), t["imie"] + " " + t["nazwisko"], "osoba__foto") or f"<span class=osoba__inicjaly>{e(t["imie"][0] + t["nazwisko"][0])}</span>"}'
            f'<strong>{e(t["imie"])} {e(t["nazwisko"])}</strong><span class="osoba__rola">{e(t["opis"])}</span></li>'
            for t in A["trenerzy"])
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
  <a class="btn btn--ak" href="{e(link)}" rel="noopener" target="_blank">Wypełnij zgłoszenie</a>
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
            kontakt += f'<a class="ak-kontakt__duzy" href="tel:{e(k["telefon"].replace(" ", ""))}">{e(k["telefon"])}</a>'
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
        <a class="btn btn--obrys btn--jasny" href="#cennik">Zobacz cennik</a></div>
    </div>
    {logo}
  </div>
  {f'<div class="kontener">{sekcja_grupy}</div>' if sekcja_grupy else ''}
</section>

<section class="sekcja ak-sekcja" id="cennik" aria-labelledby="cennik-tytul">
  <div class="kontener">
    <h2 class="ak-h2" id="cennik-tytul">Cennik</h2>
    <ul class="ak-ceny">{cennik}</ul>
    <p class="ak-przypis">Opłata miesięczna, umowa na sezon (wrzesień–czerwiec). Bez wpisowego.</p>
  </div>
</section>

<section class="sekcja ak-sekcja ak-sekcja--biala" id="plan" aria-labelledby="plan-tytul">
  <div class="kontener">
    <h2 class="ak-h2" id="plan-tytul">Plan treningów</h2>
    {plan_html}
    <p class="ak-przypis">Treningi w hali sportowej przy ul. ks. Marcina Załuskiego 57 w Kobyłce. Trening trwa 90 minut.</p>
    {f'<ul class="osoby osoby--pionowo">{trenerzy}</ul>' if trenerzy else ''}
  </div>
</section>

<section class="sekcja ak-sekcja" id="zapisy" aria-labelledby="zapisy-tytul">
  <div class="kontener">
    <h2 class="ak-h2" id="zapisy-tytul">Zapisy</h2>
    <ol class="ak-kroki">
      <li><strong>Wyślij zgłoszenie</strong><span>Imię córki, rok urodzenia, telefon do rodzica.</span></li>
      <li><strong>Odpowiemy</strong><span>Podamy grupę, godziny i termin pierwszego treningu.</span></li>
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
<section class="sekcja ak-sekcja ak-sekcja--biala" id="kontakt" aria-labelledby="kontakt-tytul">
  <div class="kontener ak-kontakt">
    <div>
      <h2 class="ak-h2" id="kontakt-tytul">Kontakt</h2>
      <p class="ak-rola">{e(k.get('rola') or 'Koordynator Akademii')}</p>
      {kontakt}
      <div class="ak-przyciski">{fb}</div>
    </div>
    <div class="ak-karta">
      <h3>Gdzie trenujemy</h3>
      <p>Hala sportowa<br>{e(C.KLUB['adres'])}</p>
      {f'<a class="btn btn--ak" href="{e(mapa)}" rel="noopener" target="_blank">Pokaż na mapie →</a>' if mapa else ''}
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
        html = S.uklad_akademii("Akademia Siatkówki Volley – Kobyłka",
                                "Akademia Siatkówki Volley w Kobyłce – treningi siatkówki dla dziewcząt. Cennik, plan treningów, zapisy i kontakt.",
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
                      f'<div class="newsy">{inne}</div></div></section>' if inne else "")
            naglowek = f'<div class="plakat__tlo">{foto}</div>' if foto else ""
            tresc_n = f"""
<article class="artykul artykul--akademia">
  <header class="plakat{' plakat--z-foto' if foto else ''}">
    {naglowek}
    <div class="kontener">
    <p class="plakat__nad">Akademia · <time datetime="{d.isoformat()}">{e(S.data_pl(d))}</time></p>
    <h1 class="plakat__tytul plakat__tytul--artykul">{e(n['tytul'])}</h1></div></header>
  <div class="kontener artykul__kontener">
    <div class="artykul__tresc">{S.akapity_fb(n['tresc'])}</div>
    {S.przycisk_fb(n)}
    <p><a class="sekcja__link" href="{pp}akademia.html#aktualnosci">← Wszystkie aktualności Akademii</a></p>
  </div>
</article>
{czytaj}"""
            zapisz(f"akademia-aktualnosci/{n['adres']}.html",
                   S.uklad_akademii(f"{n['tytul']} – Akademia Siatkówki Volley", n.get("zajawka") or n["tytul"],
                                    tresc_n, pp, self.wersja, aktualnosci=True))

    # --- STRONA WYBORU (volleykobylka.pl) -----------------------------------
    def wybor(self):
        zapisz("index.html", S.strona_wyboru("", self.wersja))

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
        self.strona("o-klubie.html", "O klubie", "Historia i sukcesy Klubu Sportowego Volley Kobyłka.", tresc)

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
        self.strona("kontakt.html", "Kontakt", "Kontakt z klubem Easy Wrap Volley Kobyłka.", tresc)

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
        def wydarzenie(m):
            g, h = m["strony"]
            tytul = f"{g['krotko']} – {h['krotko']}" if h else g["krotko"]
            miejsce = ", ".join(x for x in (m.get("hala"), m.get("adres")) if x)
            if m.get("godzina"):
                gg, mm = (int(x) for x in m["godzina"].split(":"))
                start = datetime(m["data"].year, m["data"].month, m["data"].day, gg, mm) - timedelta(hours=S.przesuniecie_pl(m["data"]))
                czas = f"DTSTART:{start:%Y%m%dT%H%M00Z}\r\nDTEND:{start + timedelta(hours=2):%Y%m%dT%H%M00Z}"
            else:
                czas = f"DTSTART;VALUE=DATE:{m['data']:%Y%m%d}\r\nDTEND;VALUE=DATE:{m['data'] + timedelta(days=1):%Y%m%d}"
            def ics(t):
                return str(t).replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")
            return (f"BEGIN:VEVENT\r\nUID:{m['druzyna']}-{m['data']:%Y%m%d}@easywrapvolley\r\n"
                    f"DTSTAMP:{m['data']:%Y%m%d}T000000Z\r\n{czas}\r\nSUMMARY:{ics(tytul)}\r\n"
                    f"LOCATION:{ics(miejsce)}\r\nEND:VEVENT\r\n")

        def plik(wydarzenia):
            return ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Easy Wrap Volley Kobylka//PL\r\n"
                    "CALSCALE:GREGORIAN\r\n" + "".join(wydarzenia) + "END:VCALENDAR\r\n")

        for m in self.mecze:
            zapisz(f"kalendarz/{m['plik_ics']}", plik([wydarzenie(m)]))
        zapisz(f"kalendarz/{GLOWNA}-caly-sezon.ics",
               plik([wydarzenie(m) for m in self.mecze if m["druzyna"] == GLOWNA]))


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
        adres = f"{czas.date().isoformat()}-{zrodla.slug(tytul)}"
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


def main():
    bez_internetu = "--bez-internetu" in sys.argv
    print("Pobieram dane ze stron związkowych..." if not bez_internetu else "Tryb bez internetu – używam kopii danych.")
    dane, uwagi = zrodla.pobierz_dane(C.ZRODLA_ZWIAZKOWE, C.RYWALE, bez_internetu=bez_internetu)
    for u in uwagi:
        print("  UWAGA:", u)
    przygotuj_herby(bez_internetu)   # przed kopiowaniem img/, żeby nowe herby trafiły na serwer
    b = Budowa(dane)

    # Aktualności z Facebooka (drużyna i Akademia) – sprawdzane 2 razy dziennie
    nowe_fb_druzyny = None
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
            b.newsy = sorted(C.NEWSY + newsy_z_fb(zapisane, kategoria),
                             key=lambda n: n.get("czas") or n["data"], reverse=True)
        else:
            b.newsy_akademii = newsy_z_fb(zapisane, kategoria)
        print(f"  Aktualności z FB ({czesc}): {len(zapisane)}" + (" – sprawdzono nowe posty" if nowe is not None else ""))
    podepnij_relacje(b.mecze, b.newsy)

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
    try:
        b.zapowiedz = zrodla.pobierz_zapowiedz(C.ZAPOWIEDZ, posty, mecz_do_zapowiedzi(b.najblizszy))
    except Exception as blad:
        print(f"  UWAGA: zapowiedź: {type(blad).__name__} – pomijam")

    # Czyścimy folder wynikowy i kopiujemy pliki stałe (CSS, JS, zdjęcia)
    if os.path.isdir(WYJSCIE):
        shutil.rmtree(WYJSCIE)
    shutil.copytree(os.path.join(FOLDER, "zasoby"), os.path.join(WYJSCIE, "zasoby"))
    if os.path.isdir(os.path.join(FOLDER, "img")):
        shutil.copytree(os.path.join(FOLDER, "img"), os.path.join(WYJSCIE, "img"))

    b.wybor()
    b.strona_glowna()
    b.terminarz()
    b.druzyny()
    b.aktualnosci()
    b.akademia()
    b.galeria()
    b.sponsorzy()
    b.o_klubie()
    b.sklep()
    b.kontakt()
    b.polityka()
    b.nie_znaleziono()
    b.kalendarze()
    zapisz("robots.txt", "User-agent: *\nAllow: /\n")

    nm = b.najblizszy
    print(f"\nGotowe! Strona jest w folderze: {WYJSCIE}")
    print(f"  Meczów: {len(b.mecze)}, aktualności: {len(b.newsy)}")
    if nm:
        g, h = nm["strony"]
        print(f"  Najbliższy mecz: {nm['data']} {nm.get('godzina') or '(godzina wkrótce)'} – {g['krotko']} vs {h['krotko'] if h else ''}")


if __name__ == "__main__":
    main()
