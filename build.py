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
    for plik in ("style.css", "main.js"):
        with open(os.path.join(FOLDER, "zasoby", plik), "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:8]


# =====================================================================
# 3. PODSTRONY
# =====================================================================
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
            # Na stronie głównej: kapitan + kolejne zawodniczki wg numeru (razem 4)
            kadra = sorted([z for z in C.KADRA if z["druzyna"] == GLOWNA],
                           key=lambda z: (not z.get("kapitan"), z["numer"]))[:4]
            newsy = self.newsy[:3]
            sponsorzy = self.sponsorzy_html(p)
            return f"""
{S.okienko_zapowiedzi(p, self.zapowiedz, C.ZAPOWIEDZ, self.najblizszy)}
{S.hero(p, self.najblizszy)}
<section class="sekcja sekcja--odbiorcy" aria-label="Dla kogo">
  <div class="kontener"><div class="odbiorcy pojaw">
    <a class="panel panel--seniorki" href="{p}druzyny.html">
      <span class="panel__nr" aria-hidden="true">01</span>
      <small>2. liga siatkówki kobiet</small><h2>{e(C.KLUB['nazwa'])}</h2>
      <p>Terminarz, wyniki, kadra i tabela.</p><span class="panel__strzalka" aria-hidden="true">↗</span></a>
    <a class="panel panel--akademia" href="{p}akademia.html">
      <span class="panel__nr" aria-hidden="true">02</span>
      <small>Trenuj z nami</small><h2>Akademia Siatkówki Volley</h2>
      <p>{e(C.AKADEMIA['opis'])}</p><span class="panel__strzalka" aria-hidden="true">↗</span></a>
  </div></div>
</section>

<section class="sekcja sekcja--bez-gory" aria-labelledby="mecze-tytul">
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
    <div class="kadra pojaw">{''.join(S.karta_zawodniczki(p, z) for z in kadra)}</div>
    <p class="przesun" aria-hidden="true">Przesuń</p>
  </div>
</section>

<section class="sekcja" aria-labelledby="bento-tytul">
  <div class="kontener">
    {S.naglowek_sekcji('Więcej', 'niż mecz', id_='bento-tytul')}
    <div class="bento pojaw">
      <a class="kafel kafel--akademia" href="{p}akademia.html"><span class="kafel__foto foto-a">{S.img(p, C.AKADEMIA.get('zdjecie'), '', 'kafel__img')}</span>
        <small>Akademia Siatkówki Volley</small><span class="kafel__slowo">Dołącz!</span><small>Zapisy trwają – pierwszy trening gratis →</small></a>
      <a class="kafel" href="{p}galeria.html"><span class="kafel__foto foto-b"></span><span class="kafel__slowo">Galeria</span><small>Zdjęcia z meczów</small></a>
      <a class="kafel" href="{p}sklep.html"><span class="kafel__foto foto-c"></span><span class="kafel__slowo">Sklep</span><small>Koszulki, szaliki</small></a>
      <a class="kafel" href="{p}sponsorzy.html"><span class="kafel__foto foto-d"></span><span class="kafel__slowo">Sponsorzy</span><small>Zostań partnerem</small></a>
      <a class="kafel kafel--kontakt" href="{p}kontakt.html"><span class="kafel__foto foto-e"></span><span class="kafel__slowo">Kontakt</span><small>{e(C.KLUB['email'])}</small></a>
    </div>
  </div>
</section>

<section class="sekcja sekcja--bez-gory" aria-labelledby="news-tytul">
  <div class="kontener">
    {S.naglowek_sekcji('Aktualności', '', p + 'aktualnosci.html', 'Wszystkie', id_='news-tytul')}
    <div class="newsy pojaw">{''.join(S.karta_newsa(p, n, i == 0) for i, n in enumerate(newsy))}</div>
  </div>
</section>
{sponsorzy}"""
        self.strona("index.html", C.KLUB["nazwa"], C.KLUB["opis"], tresc)

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
        poziomy = [("tytularny", "Sponsor tytularny"), ("strategiczny", "Sponsorzy strategiczni"), ("partner", "Partnerzy")]
        bloki = ""
        for klucz, nazwa in poziomy:
            lista = [s for s in C.SPONSORZY.values() if s["poziom"] == klucz]
            if not lista:
                continue
            loga = ""
            for s in lista:
                wnetrze = S.img(p, s.get("logo"), s["nazwa"], "logo-sp__img") or f"<span>{e(s['nazwa'])}</span>"
                if klucz == "tytularny":
                    wnetrze = f"<small>Sponsor tytularny</small>{wnetrze}"
                tag = f'a href="{e(s["www"])}" rel="noopener"' if s.get("www") else "div"
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
            inne = "".join(
                f'<a class="panel panel--akademia" href="{p}akademia.html"><small>{e(d["liga"])}</small><h2>{e(d["nazwa"])}</h2>'
                f'<p>{e(d["opis"])}</p><span class="panel__strzalka" aria-hidden="true">↗</span></a>'
                for k, d in C.DRUZYNY.items() if k != GLOWNA)
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
<section class="sekcja" aria-labelledby="inne-tytul">
  <div class="kontener">{S.naglowek_sekcji('Pozostałe', 'drużyny', id_='inne-tytul')}<div class="odbiorcy">{inne}</div></div>
</section>"""
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
    {f'<p class="artykul__zajawka">{e(n["zajawka"])}</p>' if n.get('zajawka') else ''}
    <div class="artykul__tresc">{S.akapity(n['tresc'])}</div>
    <p><a class="sekcja__link" href="{p}aktualnosci.html">← Wszystkie aktualności</a></p>
  </div>
</article>
<section class="sekcja sekcja--biala"><div class="kontener">
  {S.naglowek_sekcji('Czytaj', 'też')}
  <div class="newsy">{''.join(S.karta_newsa(p, x) for x in inne)}</div></div></section>"""
            self.strona(f"aktualnosci/{n['adres']}.html", n["tytul"], n.get("zajawka") or n["tytul"],
                        artykul, aktywna="aktualnosci.html")

    # --- AKADEMIA ----------------------------------------------------------
    def akademia(self):
        A = C.AKADEMIA

        def tresc(p):
            grupy = "".join(
                f'<article class="grupa"><span class="grupa__wiek">{e(g["wiek"])}</span><h3>{e(g["nazwa"])}</h3><p>{e(g["opis"])}</p></article>'
                for g in A["grupy"])
            trenerzy = "".join(
                f'<li class="osoba">{S.img(p, t.get("zdjecie"), t["imie"] + " " + t["nazwisko"], "osoba__foto") or f"<span class=osoba__inicjaly>{e(t["imie"][0] + t["nazwisko"][0])}</span>"}'
                f'<strong>{e(t["imie"])} {e(t["nazwisko"])}</strong><span class="osoba__rola">{e(t["opis"])}</span></li>'
                for t in A["trenerzy"])
            dni = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
            plan = sorted(A["harmonogram"], key=lambda t: (dni.index(t["dzien"].lower()), t["od"]))
            harmonogram = "".join(
                f'<tr><td>{e(t["dzien"].capitalize())}</td><td>{e(t["od"])}–{e(t["do"])}</td><td>{e(t["grupa"])}</td><td class="ukryj-mobile">{e(t.get("hala") or "")}</td></tr>'
                for t in plan)
            if A.get("formularz_google"):
                link = A["formularz_google"]
                osadz = link + ("&" if "?" in link else "?") + "embedded=true"
                formularz = f"""
<div class="formularz">
  <a class="btn btn--zolty" href="{e(link)}" rel="noopener" target="_blank">Otwórz formularz zapisu</a>
  <button class="btn btn--obrys" data-formularz="{e(osadz)}">Pokaż formularz tutaj</button>
  <p class="formularz__info">Formularz Google wczyta się dopiero po kliknięciu (Google może wtedy zapisać cookies).</p>
</div>"""
            else:
                formularz = (f'<p class="formularz__info">Formularz zapisu wkrótce. Do tego czasu napisz: '
                             f'<a href="mailto:{e(C.KLUB["email"])}?subject={quote("Zapis do Akademii")}">{e(C.KLUB["email"])}</a></p>')
            om = A["ochrona_maloletnich"]
            dokument = f'<a class="btn btn--obrys" href="{p}img/{e(om["dokument"])}">Pobierz standardy (PDF)</a>' if S.jest_plik(om.get("dokument")) else ""
            return f"""
<section class="plakat plakat--akademia">
  <div class="kontener plakat__uklad">
    <div>
      <p class="plakat__nad">Akademia Siatkówki Volley</p>
      <h1 class="plakat__tytul plakat__tytul--mega">{e(A['haslo'])}</h1>
      <p class="plakat__opis">{e(A['opis'])}</p>
      <a class="btn btn--granat" href="#zapisy">Zapisz dziecko →</a>
    </div>
    <div class="plakat__foto">{S.img(p, A.get('zdjecie'), 'Trening Akademii Siatkówki Volley', 'plakat__img', lazy=False)}</div>
  </div>
</section>
<section class="sekcja" aria-labelledby="grupy-tytul">
  <div class="kontener">
    {S.naglowek_sekcji('Grupy', 'wiekowe', id_='grupy-tytul')}
    {S.prezentuje('akademia', p)}
    <div class="grupy pojaw">{grupy}</div>
  </div>
</section>
<section class="sekcja sekcja--biala" aria-labelledby="harm-tytul">
  <div class="kontener uklad-2">
    <div>
      {S.naglowek_sekcji('Harmonogram', '', p + 'terminarz.html#kalendarium', 'Kalendarium', id_='harm-tytul')}
      <div class="tabela-ramka"><table class="tabela tabela--harmonogram">
        <caption class="ukryte">Harmonogram treningów Akademii</caption>
        <thead><tr><th scope="col">Dzień</th><th scope="col">Godziny</th><th scope="col">Grupa</th><th scope="col" class="ukryj-mobile">Miejsce</th></tr></thead>
        <tbody>{harmonogram}</tbody></table></div>
    </div>
    <div>
      {S.naglowek_sekcji('Trenerzy', '', id_='trenerzy-tytul', poziom='h2')}
      <ul class="osoby osoby--pionowo">{trenerzy}</ul>
    </div>
  </div>
</section>
<section class="sekcja" id="zapisy" aria-labelledby="zapisy-tytul">
  <div class="kontener">
    {S.naglowek_sekcji('Zapisy', 'online', id_='zapisy-tytul')}
    {formularz}
    <div class="formularz__ramka" data-formularz-ramka></div>
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
    </div>
  </div>
</section>"""
        self.strona("akademia.html", "Akademia Siatkówki Volley",
                    "Akademia Siatkówki Volley w Kobyłce – treningi dla dzieci od 7 lat. Zapisy online.", tresc)

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
  <div class="artykul__tresc">{S.akapity(O['historia'])}</div>
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
            for o in C.KONTAKT["osoby"]:
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
    <ul class="kontakt__osoby">{osoby}</ul>
    {forma}
    <ul class="kontakt__social">
      <li><a href="{C.KLUB['facebook']}" rel="noopener">Facebook</a></li>
      <li><a href="{C.KLUB['instagram']}" rel="noopener">Instagram</a></li>
      <li><a href="{C.KLUB['youtube']}" rel="noopener">YouTube</a></li>
    </ul>
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
            return f"""
{S.plakat_podstrony(p, 'Polityka prywatności', 'i plików cookies', 'polityka')}
<section class="sekcja"><div class="kontener artykul__tresc polityka">
<p><em>Wzór – przed publikacją warto sprawdzić go z osobą znającą RODO.</em></p>
<h2>Administrator danych</h2>
<p>Administratorem danych jest {e(k['nazwa_prawna'])}, {e(k['adres'])}, e-mail: <a href="mailto:{e(k['email'])}">{e(k['email'])}</a>.</p>
<h2>Jakie dane zbieramy</h2>
<p>Sama strona nie zbiera danych osobowych i nie ustawia własnych plików cookies. Nie używamy narzędzi analitycznych ani reklamowych.</p>
<p>Dane podajesz nam tylko wtedy, gdy wypełnisz formularz Google (np. zapis do Akademii) albo napiszesz e-mail. Wykorzystujemy je wyłącznie do odpowiedzi, organizacji zajęć i kontaktu z rodzicami (art. 6 ust. 1 lit. b, c i f RODO). Dane z formularzy przechowujemy przez czas uczestnictwa w zajęciach i okres wymagany przepisami.</p>
<h2>Usługi zewnętrzne</h2>
<ul>
<li><strong>Google Fonts</strong> – czcionki strony są pobierane z serwerów Google; przeglądarka przekazuje przy tym adres IP.</li>
<li><strong>Formularze Google</strong> – wczytują się dopiero po kliknięciu przycisku; Google może wtedy zapisać swoje cookies (zasady: policies.google.com).</li>
<li><strong>Facebook, Instagram, YouTube</strong> – na stronie są tylko linki; dane trafiają do tych serwisów dopiero po przejściu na nie.</li>
<li><strong>Serwer (hosting)</strong> – dostawca serwera może zapisywać standardowe logi (adres IP, czas wizyty) w celach bezpieczeństwa.</li>
</ul>
<h2>Twoje prawa</h2>
<p>Masz prawo do dostępu do swoich danych, ich sprostowania, usunięcia, ograniczenia przetwarzania, przeniesienia oraz sprzeciwu. Możesz też złożyć skargę do Prezesa Urzędu Ochrony Danych Osobowych. W sprawach danych pisz na: <a href="mailto:{e(k['email'])}">{e(k['email'])}</a>.</p>
<h2>Wizerunek</h2>
<p>Na stronie publikujemy zdjęcia z meczów i treningów. Zdjęcia dzieci publikujemy wyłącznie za zgodą rodziców. Jeśli chcesz usunąć zdjęcie, napisz do nas.</p>
</div></section>"""
        self.strona("polityka-prywatnosci.html", "Polityka prywatności i cookies",
                    "Polityka prywatności i plików cookies strony klubu.", tresc)

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

    # Posty z Instagrama/Facebooka: zapowiedź meczu i zdjęcia wygranych.
    # Każdy błąd tylko pomija zdjęcie – nigdy nie zatrzymuje budowania strony.
    posty, uwaga = zrodla.pobierz_posty(C.META, bez_internetu)
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
