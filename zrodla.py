# =====================================================================
#  ZRODLA.PY – POBIERANIE DANYCH ZE STRON ZWIĄZKOWYCH
# ---------------------------------------------------------------------
#  Tego pliku zwykle NIE trzeba ruszać. Adresy stron ustawia się
#  w content.py (sekcja ZRODLA_ZWIAZKOWE).
#
#  Co robi:
#   1. WSMWZPS (obsady.wsmwzps.pl)  → terminarz i godziny meczów
#   2. PZPS lista meczów            → pełny terminarz (też wyjazdy poza Mazowsze)
#   3. PZPS tabele i wyniki         → tabela grupy, wyniki i sety
#   4. PZPS strona meczu            → hala i adres najbliższych meczów
#
#  Każdy udany odczyt zapisuje się w dane/kopia_zwiazkowa.json.
#  Jeśli któraś strona nie odpowiada albo zmieni wygląd, używana jest
#  ostatnia dobra kopia – strona klubu nigdy nie zostanie pusta.
#
#  Używa tylko bibliotek wbudowanych w Pythona (nic nie trzeba instalować).
# =====================================================================

import html
import json
import os
import re
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone

FOLDER = os.path.dirname(os.path.abspath(__file__))
PLIK_KOPII = os.path.join(FOLDER, "dane", "kopia_zwiazkowa.json")

# Przedstawiamy się stronie związku uczciwie, kim jesteśmy
NAGLOWKI = {"User-Agent": "StronaEasyWrapVolleyKobylka/1.0 (aktualizacja terminarza klubu)"}

# Ile dni do przodu sprawdzać halę na stronie pojedynczego meczu
DNI_HALI = 30


# ---------------------------------------------------------------------
# Narzędzia
# ---------------------------------------------------------------------
def pobierz(url):
    """Pobiera stronę i zwraca jej treść jako tekst."""
    zapytanie = urllib.request.Request(url, headers=NAGLOWKI)
    with urllib.request.urlopen(zapytanie, timeout=25) as odp:
        return odp.read().decode("utf-8", errors="replace")


def czysc(tekst):
    """Usuwa znaczniki HTML i nadmiarowe spacje."""
    tekst = re.sub(r"<[^>]+>", " ", tekst)
    return re.sub(r"\s+", " ", html.unescape(tekst)).strip()


def norm(nazwa):
    """Ujednolica nazwę drużyny do porównań (małe litery, pojedyncze spacje)."""
    nazwa = czysc(nazwa).lower()
    nazwa = re.sub(r"\s+2$", " ii", nazwa)  # „Legionowo 2” = „Legionowo II”
    return nazwa


def godzina_z(tekst, minuty_zastepcze=None):
    """Zwraca (godzina, czy_pewna). Godzina z minutami zastępczymi (np. :33) jest niepewna."""
    m = re.search(r"(\d{1,2}):(\d{2})", czysc(tekst))
    if not m:
        return None, False
    g = f"{int(m.group(1)):02d}:{m.group(2)}"
    if minuty_zastepcze and m.group(2) == minuty_zastepcze:
        return None, False
    return g, True


def wczytaj_kopie():
    try:
        with open(PLIK_KOPII, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def zapisz_kopie(kopia):
    os.makedirs(os.path.dirname(PLIK_KOPII), exist_ok=True)
    with open(PLIK_KOPII, "w", encoding="utf-8") as f:
        json.dump(kopia, f, ensure_ascii=False, indent=1, sort_keys=True)


# ---------------------------------------------------------------------
# 1. WSMWZPS – terminarz
# ---------------------------------------------------------------------
WIERSZ_MECZU = re.compile(
    r'<tr>\s*<td>\s*<a href="([^"]+)">\s*(\d+)\s*</a>.*?</td>\s*'   # link i numer
    r"<td>\s*(\d{4}-\d\d-\d\d)(.*?)</td>\s*"                       # data i godzina
    r"<td>\s*<b>(.*?)</b>\s*</td>\s*<td>.*?</td>\s*"               # gospodarz
    r"<td>\s*<b>(.*?)</b>",                                        # gość
    re.S,
)


def parsuj_wsmwzps(strona, sekcja, nasza, minuty_zastepcze):
    # Sekcja zaczyna się nagłówkiem <h2> z nazwą ligi i trwa do następnego <h2>
    poczatek = re.search(r"<h2>\s*<a[^>]*>\s*" + re.escape(sekcja) + r"\s*</a>\s*</h2>", strona)
    if not poczatek:
        raise ValueError(f"WSMWZPS: nie znaleziono sekcji „{sekcja}”")
    koniec = strona.find("<h2>", poczatek.end())
    fragment = strona[poczatek.end(): koniec if koniec > 0 else None]

    mecze = []
    for link, nr, dzien, godz, gosp, gosc in WIERSZ_MECZU.findall(fragment):
        if norm(nasza) not in (norm(gosp), norm(gosc)):
            continue
        godzina, pewna = godzina_z(godz, minuty_zastepcze)
        mecze.append({
            "data": dzien, "godzina": godzina, "godzina_pewna": pewna,
            "gospodarz": czysc(gosp), "gosc": czysc(gosc),
        })
    if not mecze:
        raise ValueError("WSMWZPS: nie znaleziono żadnego naszego meczu")
    return mecze


# ---------------------------------------------------------------------
# 2. PZPS – lista meczów (pełny terminarz)
# ---------------------------------------------------------------------
def parsuj_pzps_liste(strona, nasza):
    mecze = []
    for link, nr, dzien, godz, gosp, gosc in WIERSZ_MECZU.findall(strona):
        if norm(nasza) not in (norm(gosp), norm(gosc)):
            continue
        godzina, pewna = godzina_z(godz)
        mecze.append({
            "id": link.replace("//", "/"), "nr": int(nr), "data": dzien,
            "godzina": godzina, "godzina_pewna": pewna,
            "gospodarz": czysc(gosp), "gosc": czysc(gosc),
        })
    if not mecze:
        raise ValueError("PZPS: na liście meczów nie ma naszej drużyny")
    return mecze


# ---------------------------------------------------------------------
# 3. PZPS – tabela i wyniki grupy
# ---------------------------------------------------------------------
WIERSZ_TABELI = re.compile(
    r"<tr><td>(\d+)</td><td>([^<]+)</td>" + r"<td>(\d+)</td>" * 7 + r"</tr>"
)
WIERSZ_WYNIKU = re.compile(
    r'<tr><td><a href="([^"]+)">\d+</a></td><td>\s*(\d{4}-\d\d-\d\d)</td>'
    r"<td>\s*<b>(.*?)</b>\s*</td><td>-</td><td>\s*<b>(.*?)</b></td>"
    r"<td><b>(\d+):(\d+)</b>\s*(?:\(([^)]*)\))?",
    re.S,
)


def parsuj_pzps_tabele(strona, grupa, nasza):
    poczatek = re.search(r'<a name="[^"]*"></a>\s*<b>\s*' + re.escape(grupa) + r"\s*</b>", strona)
    if not poczatek:
        raise ValueError(f"PZPS: nie znaleziono „{grupa}” na stronie tabel")
    koniec = strona.find("<a name=", poczatek.end())
    fragment = strona[poczatek.end(): koniec if koniec > 0 else None]

    tabela = []
    for lp, nazwa, m, pkt, zw, sw, sp, mw, mp in WIERSZ_TABELI.findall(fragment):
        tabela.append({
            "lp": int(lp), "nazwa": czysc(nazwa), "mecze": int(m), "pkt": int(pkt),
            "zwyciestwa": int(zw), "sety_plus": int(sw), "sety_minus": int(sp),
            "male_plus": int(mw), "male_minus": int(mp),
            "nasz": norm(nazwa) == norm(nasza),
        })
    if not tabela:
        raise ValueError("PZPS: tabela grupy jest pusta lub zmienił się jej wygląd")

    wyniki = {}
    for link, dzien, gosp, gosc, a, b, sety in WIERSZ_WYNIKU.findall(fragment):
        if norm(nasza) not in (norm(gosp), norm(gosc)):
            continue
        if a == "0" and b == "0":
            continue  # mecz jeszcze nierozegrany
        wyniki[link.replace("//", "/")] = {
            "data": dzien, "wynik": f"{a}:{b}",
            "sety": [s.strip() for s in sety.split(",") if s.strip()],
        }
    return tabela, wyniki


# ---------------------------------------------------------------------
# 4. PZPS – strona pojedynczego meczu (hala, adres, godzina)
# ---------------------------------------------------------------------
def parsuj_pzps_mecz(strona):
    tekst = re.sub(r"<[^>]+>", "|", strona)
    tekst = re.sub(r"\s+", " ", html.unescape(tekst))
    m = re.search(r"Mecz rozgrywany w(.*?)godzina meczu:(.*?)\|\s*\|", tekst)
    if not m:
        return None
    czesci = [c.strip(" ,") for c in m.group(1).split("|") if c.strip(" ,")]
    godzina, pewna = godzina_z(m.group(2))
    return {
        "adres": czesci[0] if czesci else None,
        "hala": " ".join(czesci[1:]) or None,
        "godzina": godzina if pewna else None,
    }


# ---------------------------------------------------------------------
# 5. HERBY Z VOLLEYSTATION
#   Logo pobiera się tylko wtedy, gdy nie ma go jeszcze w img/herby/.
#   Potem leży w repozytorium – nie odpytujemy VolleyStation co 2 godziny.
# ---------------------------------------------------------------------
ROZSZERZENIA = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/svg+xml": ".svg"}


def herb_z_volleystation(klucz, url):
    """Herb: 240 px wystarczy (wyświetla się najwyżej ~90 px)."""
    return pobierz_obraz("herby", klucz, url, 240)


def pobierz_obraz(podfolder, klucz, url, rozmiar):
    """
    Pobiera obrazek RAZ do img/<podfolder>/<klucz>.<rozszerzenie> i zmniejsza do `rozmiar` px.
    Zwraca ścieżkę względem img/ (np. "herby/kalisz.webp") albo None.
    """
    folder = os.path.join(FOLDER, "img", podfolder)
    for rozszerzenie in set(ROZSZERZENIA.values()):
        if os.path.isfile(os.path.join(folder, klucz + rozszerzenie)):
            return f"{podfolder}/{klucz}{rozszerzenie}"   # już pobrany wcześniej
    if not url:
        return None
    zapytanie = urllib.request.Request(url, headers=NAGLOWKI)
    with urllib.request.urlopen(zapytanie, timeout=25) as odp:
        typ = odp.headers.get_content_type()
        dane = odp.read(2_000_001)
    if typ not in ROZSZERZENIA or len(dane) > 2_000_000:
        raise ValueError(f"to nie jest obrazek albo jest za duży ({typ}, {len(dane)} B)")
    os.makedirs(folder, exist_ok=True)
    time.sleep(0.5)

    # Zmniejszamy i zapisujemy jako lekki WebP.
    # Wymaga biblioteki Pillow (na GitHubie instaluje się sama). Bez niej zapisujemy oryginał.
    if typ != "image/svg+xml":
        try:
            import io
            from PIL import Image
            obraz = Image.open(io.BytesIO(dane))
            obraz = obraz.convert("RGBA") if obraz.mode in ("P", "LA", "RGBA") else obraz.convert("RGB")
            obraz.thumbnail((rozmiar, rozmiar))
            obraz.save(os.path.join(folder, klucz + ".webp"), "WEBP", quality=82)
            return f"{podfolder}/{klucz}.webp"
        except ImportError:
            pass
    with open(os.path.join(folder, klucz + ROZSZERZENIA[typ]), "wb") as f:
        f.write(dane)
    return f"{podfolder}/{klucz}{ROZSZERZENIA[typ]}"


# ---------------------------------------------------------------------
# 6. ZAPOWIEDŹ MECZU Z INSTAGRAMA / FACEBOOKA (oficjalne API Meta)
#   Instagram i Facebook nie pozwalają czytać postów zwykłym skryptem.
#   Używamy Graph API z tokenem strony klubu (sekret META_TOKEN).
#   Zapowiedź dopasowujemy do KONKRETNEGO najbliższego meczu (rywal, data, termin posta).
# ---------------------------------------------------------------------
API_META = "https://graph.facebook.com"
MIESIACE_DOP = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca",
                "sierpnia", "wrzesnia", "pazdziernika", "listopada", "grudnia"]
# Słowa w nazwach klubów, które nic nie mówią o rywalu (są w nazwach wielu drużyn)
OGOLNE_SLOWA = {"azs", "uks", "mks", "muks", "sms", "gks", "tps", "pge", "lts", "kss", "glks", "mlks",
                "volley", "siatkowka", "klub", "sportowy", "towarzystwo", "pilki", "siatkowej",
                "akademia", "energa", "mapei", "libero", "vip", "gwarant", "biesiadowo", "rockfin", "johnnybros",
                "biofarm", "enea", "trio", "molo", "skarpa"}


def bez_ogonkow(tekst):
    """„Łódź Kalisz” → „lodz kalisz” – porównujemy bez polskich znaków i wielkości liter."""
    import unicodedata
    tekst = (tekst or "").lower().replace("ł", "l")
    return "".join(z for z in unicodedata.normalize("NFD", tekst) if unicodedata.category(z) != "Mn")


def slowa_rywala(nazwy):
    """Charakterystyczne słowa z nazw rywala (np. „lodz”, „umed”, „kalisz”) – min. 4 litery."""
    slowa = set()
    for nazwa in nazwy:
        for slowo in re.findall(r"[a-z0-9]+", bez_ogonkow(nazwa)):
            if len(slowo) >= 4 and slowo not in OGOLNE_SLOWA and not slowo.isdigit():
                slowa.add(slowo)
    # Krótkie, ale jednoznaczne skróty (np. „ŁKS”) – tylko gdy są pierwszym słowem nazwy
    for nazwa in nazwy:
        pierwsze = re.findall(r"[a-z0-9]+", bez_ogonkow(nazwa))[:1]
        if pierwsze and len(pierwsze[0]) >= 3 and pierwsze[0] not in OGOLNE_SLOWA:
            slowa.add(pierwsze[0])
    return slowa


def wspomina(slowa_szukane, wyrazy):
    """
    Czy któryś wyraz z opisu pasuje do słowa rywala – z polską odmianą:
    „lodz” pasuje do „lodzi”, „kalisz” do „kaliszem”, „legionowo” do „legionowie”.
    Skróty 3-literowe (np. „lks”) muszą pasować dokładnie.
    """
    for s in slowa_szukane:
        rdzen = s if len(s) <= 4 else s[:max(4, len(s) - 2)]
        for w in wyrazy:
            if (w == s) if len(s) <= 3 else w.startswith(rdzen):
                return True
    return False


def wybierz_post_zapowiedzi(posty, mecz, konfig):
    """
    posty: lista {id, opis, obraz, link, czas}
    mecz:  {"data": date, "nazwy_rywala": [...]}
    Zwraca post z plakatem tego meczu albo None.
    """
    dzien = mecz["data"]
    rywal = slowa_rywala(mecz.get("nazwy_rywala", []))
    daty = {f"{dzien.day}.{dzien.month:02d}", f"{dzien.day:02d}.{dzien.month:02d}",
            f"{dzien.day} {MIESIACE_DOP[dzien.month - 1]}"}
    slowa = [bez_ogonkow(s) for s in konfig.get("slowa_zapowiedzi", [])]
    hashtagi = [bez_ogonkow(h) for h in konfig.get("hashtagi_klubu", [])]

    # Początek meczu (jeśli znamy godzinę) – post opublikowany później to już nie zapowiedź
    start = None
    if mecz.get("godzina"):
        g, m = (int(x) for x in mecz["godzina"].split(":"))
        start = datetime(dzien.year, dzien.month, dzien.day, g, m).astimezone()

    kandydaci = []
    for post in posty:
        if not post.get("obraz") or not post.get("czas"):
            continue
        czas = datetime.fromisoformat(post["czas"].replace("+0000", "+00:00")).astimezone()
        opublikowany = czas.date()
        if not 0 <= (dzien - opublikowany).days <= konfig.get("dni_przed", 7):
            continue          # za wcześnie albo już po meczu
        if start and czas >= start:
            continue          # opublikowany w trakcie lub po meczu
        opis = bez_ogonkow(post.get("opis"))
        if re.search(r"\b[0-3]\s*:\s*[0-3]\b", opis) or re.search(r"wygr|przegr|zwyciest|porazk", opis):
            continue          # post z wynikiem, nie zapowiedź
        wyrazy = set(re.findall(r"[a-z0-9]+", opis))
        o_rywalu = wspomina(rywal, wyrazy)
        o_dacie = any(d in opis for d in daty)
        zapowiedz = any(s in opis for s in slowa)
        if not (o_rywalu or o_dacie or zapowiedz):
            continue          # np. zdjęcia z treningu z tym samym hashtagiem klubu
        punkty = 3 * o_rywalu + 3 * o_dacie + 2 * zapowiedz + any(h in opis for h in hashtagi)
        kandydaci.append((punkty, opublikowany, post))
    if not kandydaci:
        return None
    return max(kandydaci, key=lambda k: (k[0], k[1]))[2]


def posty_meta(meta, token):
    """Pobiera ostatnie posty z IG albo FB i sprowadza je do jednego formatu."""
    if meta["zrodlo"] == "instagram":
        pola = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"
        url = f"{API_META}/{meta['instagram_id']}/media?fields={pola}&limit=30&access_token={token}"
        dane = json.loads(pobierz(url))
        return [{"id": d["id"], "opis": d.get("caption"), "link": d.get("permalink"), "czas": d.get("timestamp"),
                 "obraz": d.get("thumbnail_url") if d.get("media_type") == "VIDEO" else d.get("media_url")}
                for d in dane.get("data", [])]
    pola = "id,message,full_picture,permalink_url,created_time"
    url = f"{API_META}/{meta['facebook_id']}/posts?fields={pola}&limit=30&access_token={token}"
    dane = json.loads(pobierz(url))
    return [{"id": d["id"], "opis": d.get("message"), "link": d.get("permalink_url"),
             "czas": d.get("created_time"), "obraz": d.get("full_picture")}
            for d in dane.get("data", [])]


def pobierz_posty(meta, bez_internetu=False):
    """
    Jedno zapytanie do Meta na całe budowanie. Zwraca (lista_postów albo None, uwaga).
    None = nie wiemy nic nowego (brak tokenu, brak internetu, błąd) → używamy zapisanych plików.
    """
    token = token_meta("druzyna")
    ident = meta.get("instagram_id") if meta.get("zrodlo") == "instagram" else meta.get("facebook_id")
    if bez_internetu:
        return None, None
    if not token or not ident:
        return None, "posty FB/IG: brak tokenu META_TOKEN lub ID konta – używam zapisanych zdjęć"
    try:
        return posty_meta(meta, token), None
    except Exception as blad:
        # Nie pokazujemy tokenu w logach – tylko rodzaj błędu
        return None, f"posty FB/IG: nie udało się odczytać ({type(blad).__name__}) – używam zapisanych zdjęć"


def pobierz_zapowiedz(konfig, posty, mecz):
    """
    Zwraca {plik, link, opis, klucz, czas, mecz} albo None.
    mecz: {"data": date, "nazwy_rywala": [...]} – najbliższy mecz (albo None).
    Wynik zapisuje w dane/zapowiedz.json, żeby przy awarii API użyć ostatniego plakatu –
    ale tylko jeśli dotyczy tego samego meczu.
    """
    plik_zapisu = os.path.join(FOLDER, "dane", "zapowiedz.json")
    if not konfig.get("wlaczona") or mecz is None:
        return None
    if konfig.get("plik_reczny"):
        return {"plik": konfig["plik_reczny"], "link": None, "opis": "", "klucz": konfig["plik_reczny"],
                "czas": None, "mecz": mecz["data"].isoformat()}
    if posty is None:  # brak nowych danych – ostatni zapisany plakat, jeśli to ten sam mecz
        try:
            with open(plik_zapisu, encoding="utf-8") as f:
                zapis = json.load(f) or None
        except (OSError, ValueError):
            return None
        return zapis if zapis and zapis.get("mecz") == mecz["data"].isoformat() else None
    post = wybierz_post_zapowiedzi(posty, mecz, konfig)
    if post is None:
        wynik = None   # brak plakatu dla tego meczu = brak okienka
    else:
        klucz = "post-" + re.sub(r"[^0-9A-Za-z_-]", "", post["id"])
        plik = pobierz_obraz("zapowiedz", klucz, post["obraz"], 1080)
        wynik = {"plik": plik, "link": post.get("link"), "opis": (post.get("opis") or "")[:300],
                 "klucz": klucz, "czas": post["czas"], "mecz": mecz["data"].isoformat()}
        # Sprzątamy stare plakaty, żeby repozytorium nie puchło
        folder = os.path.join(FOLDER, "img", "zapowiedz")
        for nazwa in os.listdir(folder):
            if not nazwa.startswith(klucz + "."):
                os.remove(os.path.join(folder, nazwa))
    os.makedirs(os.path.dirname(plik_zapisu), exist_ok=True)
    with open(plik_zapisu, "w", encoding="utf-8") as f:
        json.dump(wynik, f, ensure_ascii=False, indent=1)
    return wynik


def post_o_wygranej(posty, dzien_meczu, hashtagi, dni_po_meczu):
    """Najwcześniejszy post ze zdjęciem i hashtagiem, opublikowany od dnia meczu do `dni_po_meczu` dni później."""
    tagi = [t.lower() for t in hashtagi]
    kandydaci = []
    for post in posty:
        if not post.get("obraz") or not post.get("czas"):
            continue
        if not any(t in (post.get("opis") or "").lower() for t in tagi):
            continue
        dzien = datetime.fromisoformat(post["czas"].replace("+0000", "+00:00")).astimezone().date()
        if 0 <= (dzien - dzien_meczu).days <= dni_po_meczu:
            kandydaci.append((dzien, post))
    return min(kandydaci, key=lambda x: x[0])[1] if kandydaci else None


def zdjecie_wygranej(klucz, dzien_meczu, posty, konfig):
    """
    Ścieżka zdjęcia wygranego meczu (względem img/) albo None.
    Najpierw plik już leżący w img/wyniki/ (pobrany wcześniej albo wrzucony ręcznie),
    potem – jeśli są nowe posty – pobranie zdjęcia z posta.
    """
    gotowe = pobierz_obraz("wyniki", klucz, None, 0)
    if gotowe or not posty or not konfig.get("wlaczone"):
        return gotowe
    post = post_o_wygranej(posty, dzien_meczu, konfig["hashtagi"], konfig["dni_po_meczu"])
    return pobierz_obraz("wyniki", klucz, post["obraz"], 900) if post else None


# ---------------------------------------------------------------------
# 7. AKTUALNOŚCI Z FACEBOOKA (drużyna i Akademia – osobne strony FB)
#   Posty pobieramy oficjalnym Graph API tokenem strony (sekrety na GitHubie).
#   Sprawdzamy tylko o wybranych godzinach (np. 7:00 i 19:00) – między nimi
#   strona korzysta z zapisanej kopii dane/posty_fb_<część>.json.
#   Z opisu usuwamy część z oznaczeniami sponsorów (wszystko pod kreską
#   „_________”), dopiski typu @obserwujący i końcowe hashtagi.
# ---------------------------------------------------------------------
WERSJA_API = "v26.0"
# Linia-separator: kilka podkreśleń, kresek lub kropek
SEPARATOR = re.compile(r"^[ \t]*[_\-–—=~.•*]{4,}[ \t]*$", re.M)
OZNACZENIA = re.compile(r"@(obserwujący|obserwujacy|followers|highlight|wszyscy|everyone)\b", re.I)
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D\u20E3\u2190-\u21FF\u2300-\u23FF]+")


def _litery(tekst):
    return len(re.findall(r"[^\W\d_]", tekst))


def linia_sponsorow(linia, nazwy_sponsorow):
    """Czy linia to same nazwy sponsorów/oznaczenia (gdy w poście zabrakło kreski-separatora)."""
    przed = _litery(linia)
    if przed < 12:
        return False
    reszta = linia.lower()
    for nazwa in sorted(nazwy_sponsorow, key=len, reverse=True):
        reszta = reszta.replace(nazwa.lower(), " ")
    reszta = re.sub(r"@\S+|#\S+", " ", reszta)
    return _litery(reszta) <= przed * 0.25


def oczysc_opis(opis, nazwy_sponsorow=(), usun_hashtagi=True):
    """Opis posta bez części ze sponsorami, oznaczeń @obserwujący i końcowych hashtagów."""
    tekst = (opis or "").replace("\r\n", "\n")
    tekst = SEPARATOR.split(tekst, maxsplit=1)[0]          # wszystko pod kreską = sponsorzy
    tekst = OZNACZENIA.sub("", tekst)
    linie = [l.rstrip() for l in tekst.split("\n")]
    # Od końca: puste linie, same hashtagi, same nazwy sponsorów
    while linie:
        l = linie[-1].strip()
        same_hashtagi = l and all(s.startswith("#") for s in l.split())
        oznaczenie = l.startswith("@") and len(l) < 60      # np. „@liderzy wśród fanów”
        if not l or (usun_hashtagi and same_hashtagi) or oznaczenie or linia_sponsorow(l, nazwy_sponsorow):
            linie.pop()
            continue
        break
    tekst = "\n".join(linie)
    if usun_hashtagi:   # hashtagi doklejone na końcu ostatniego zdania
        tekst = re.sub(r"(\s+#[^\s#]+)+\s*$", "", tekst)
    tekst = re.sub(r"[ \t]+\n", "\n", tekst)
    return re.sub(r"\n{3,}", "\n\n", tekst).strip()


def bez_emoji(tekst):
    return re.sub(r"\s{2,}", " ", EMOJI.sub(" ", tekst or "")).strip(" -–—:|•")


def podziel_post(opis):
    """(tytuł, treść, zajawka) z oczyszczonego opisu posta."""
    linie = [l for l in opis.split("\n")]
    while linie and not bez_emoji(linie[0]):
        linie.pop(0)
    if not linie:
        return "", "", ""
    pierwsza = bez_emoji(linie[0])
    reszta = "\n".join(linie[1:]).strip()
    if len(pierwsza) > 100:   # długi pierwszy akapit – tytułem jest pierwsze zdanie
        zdanie = re.split(r"(?<=[.!?])\s", pierwsza, maxsplit=1)[0]
        if len(zdanie) > 100:
            zdanie = zdanie[:97].rsplit(" ", 1)[0] + "…"
        tytul, do_zajawki, reszta = zdanie, (pierwsza[len(zdanie):] + "\n" + reszta).strip(), opis.strip()
    else:
        tytul, do_zajawki = pierwsza, reszta
    zdania = [bez_emoji(x) for x in do_zajawki.split("\n") if bez_emoji(x)]
    plaski = " ".join(z if z[-1] in ".!?…:;," else z + "." for z in zdania)
    zajawka = plaski if len(plaski) <= 170 else plaski[:167].rsplit(" ", 1)[0] + "…"
    return tytul, reszta, zajawka


def slug(tekst, dlugosc=48):
    s = re.sub(r"[^a-z0-9]+", "-", bez_ogonkow(tekst)).strip("-")
    return (s[:dlugosc].rstrip("-")) or "post"


def klucz_posta(czesc, ident):
    import hashlib
    return f"{czesc}-" + hashlib.sha1(ident.encode()).hexdigest()[:10]


def pora_sprawdzic(sprawdzono, godziny, teraz=None):
    """Czy minęła kolejna godzina sprawdzania (np. 7:00 lub 19:00) od ostatniego sprawdzenia."""
    if not sprawdzono:
        return True
    teraz = teraz or datetime.now().astimezone()
    try:
        ostatnio = datetime.fromisoformat(sprawdzono)
    except ValueError:
        return True
    if ostatnio.tzinfo is None:
        ostatnio = ostatnio.astimezone()
    sloty = [datetime.combine(teraz.date() - timedelta(days=d), datetime.min.time()).replace(hour=h).astimezone()
             for d in (0, 1) for h in godziny]
    ostatni_slot = max(s for s in sloty if s <= teraz)
    return ostatnio < ostatni_slot


def blad_meta(blad):
    """Czytelny opis błędu z Graph API (kod i komunikat Facebooka – bez tokenu)."""
    opis = type(blad).__name__
    try:
        import urllib.error
        if isinstance(blad, urllib.error.HTTPError):
            dane = json.loads(blad.read().decode("utf-8", "replace") or "{}").get("error", {})
            opis = f"HTTP {blad.code}, kod {dane.get('code')}/{dane.get('error_subcode')}: {dane.get('message', '')[:160]}"
    except Exception:
        pass
    return opis


def token_meta(czesc="druzyna"):
    """
    Tokeny stron FB z sekretu META_TOKEN na GitHubie.
    W sekrecie mogą być DWA tokeny oddzielone spacją lub nową linią:
    pierwszy – strona drużyny, drugi – strona Akademii.
    (Osobny sekret META_TOKEN_AKADEMIA też działa, jeśli jest przekazany do budowania.)
    """
    surowy = os.environ.get("META_TOKEN") or ""
    # Tokeny Meta zaczynają się od „EAA” – dzięki temu działa też wklejka z cudzysłowami lub „access_token:”
    tokeny = re.findall(r"EAA[0-9A-Za-z]+", surowy) or [x for x in re.split(r"[\s,;\"']+", surowy) if x]
    if czesc == "akademia":
        return os.environ.get("META_TOKEN_AKADEMIA") or (tokeny[1] if len(tokeny) > 1 else None)
    return tokeny[0] if tokeny else None


def posty_strony_fb(token, ile):
    """Ostatnie posty strony FB, do której należy token (token strony → /me)."""
    pola = "id,message,full_picture,permalink_url,created_time"
    url = f"{API_META}/{WERSJA_API}/me/posts?fields={pola}&limit={ile}&access_token={token}"
    dane = json.loads(pobierz(url))
    return [{"id": d["id"], "opis": d.get("message") or "", "link": d.get("permalink_url"),
             "czas": d.get("created_time"), "obraz": d.get("full_picture")}
            for d in dane.get("data", [])]


def aktualnosci_fb(czesc, konfig, bez_internetu=False):
    """
    Zwraca (posty_z_kopii, nowe_posty_z_API albo None, uwaga).
    posty_z_kopii: [{id, opis, czas, link, zdjecie}] – zdjęcia już leżą w img/posty/.
    """
    plik = os.path.join(FOLDER, "dane", f"posty_fb_{czesc}.json")
    try:
        with open(plik, encoding="utf-8") as f:
            kopia = json.load(f)
    except (OSError, ValueError):
        kopia = {"sprawdzono": None, "posty": []}
    token = token_meta(czesc)
    if bez_internetu or not konfig.get("wlaczone"):
        return kopia["posty"], None, None
    if not token:
        brak = "drugiego tokenu w sekrecie META_TOKEN" if czesc == "akademia" else "sekretu META_TOKEN"
        return kopia["posty"], None, f"aktualności FB ({czesc}): brak {brak} – pokazuję zapisane posty"
    if not pora_sprawdzic(kopia.get("sprawdzono"), konfig.get("godziny", [7, 19])):
        return kopia["posty"], None, None
    try:
        nowe = posty_strony_fb(token, konfig.get("ile", 12))
    except Exception as blad:
        return kopia["posty"], None, f"aktualności FB ({czesc}): nie udało się odczytać ({blad_meta(blad)}) – pokazuję zapisane posty"

    stare = {p["id"]: p for p in kopia["posty"]}
    posty = []
    for n in nowe:
        if not (n["opis"] or "").strip():
            continue                      # same zdjęcia bez opisu – pomijamy
        klucz = klucz_posta(czesc, n["id"])
        zdjecie = None
        try:
            zdjecie = pobierz_obraz("posty", klucz, n.get("obraz"), 1200)
        except Exception as blad:
            print(f"  UWAGA: zdjęcie posta {klucz}: {type(blad).__name__} – bez zdjęcia")
            zdjecie = (stare.get(n["id"]) or {}).get("zdjecie")
        posty.append({"id": n["id"], "opis": n["opis"], "czas": n["czas"], "link": n["link"], "zdjecie": zdjecie})

    # Sprzątamy zdjęcia postów, które wypadły z listy (tylko tej części strony)
    folder = os.path.join(FOLDER, "img", "posty")
    uzywane = {os.path.basename(p["zdjecie"]) for p in posty if p.get("zdjecie")}
    if os.path.isdir(folder):
        for nazwa in os.listdir(folder):
            if nazwa.startswith(czesc + "-") and nazwa not in uzywane:
                os.remove(os.path.join(folder, nazwa))
    os.makedirs(os.path.dirname(plik), exist_ok=True)
    with open(plik, "w", encoding="utf-8") as f:
        json.dump({"sprawdzono": datetime.now().astimezone().isoformat(timespec="minutes"), "posty": posty},
                  f, ensure_ascii=False, indent=1)
    return posty, nowe, None


# ---------------------------------------------------------------------
# Łączenie źródeł
# ---------------------------------------------------------------------
def ten_sam_mecz(a, b, aliasy):
    """Czy dwa wpisy z różnych źródeł to ten sam mecz (ta sama para gospodarz–gość)."""
    def klucz(nazwa):
        n = norm(nazwa)
        return aliasy.get(n, n)
    return klucz(a["gospodarz"]) == klucz(b["gospodarz"]) and klucz(a["gosc"]) == klucz(b["gosc"])


def polacz(pzps, wsm, wyniki, aliasy):
    """Terminarz bazowy z PZPS + godziny/daty z WSMWZPS + wyniki z tabeli PZPS."""
    mecze = [dict(m, zrodlo="PZPS") for m in pzps]
    po_dacie = {m["data"]: m for m in mecze}

    for w in wsm:
        cel = po_dacie.get(w["data"])
        if cel is None or not ten_sam_mecz(cel, w, aliasy):
            # mecz przełożony – szukamy tej samej pary drużyn
            cel = next((m for m in mecze if ten_sam_mecz(m, w, aliasy)), None)
        if cel is None:
            mecze.append(dict(w, zrodlo="WSMWZPS"))
            continue
        cel["data"] = w["data"]                       # WSMWZPS jest główny dla terminu
        if w["godzina_pewna"]:
            cel["godzina"], cel["godzina_pewna"] = w["godzina"], True
        cel["zrodlo"] = "WSMWZPS+PZPS"

    for m in mecze:
        wynik = wyniki.get(m.get("id"))
        if wynik:
            m["wynik"], m["sety"] = wynik["wynik"], wynik["sety"]

    mecze.sort(key=lambda m: (m["data"], m.get("godzina") or "99:99"))
    return mecze


def aliasy_z(rywale):
    """Słownik: każda znana nazwa rywala → jedna wspólna nazwa (pierwsza z listy)."""
    aliasy = {}
    for r in rywale.values():
        nazwy = [norm(n) for n in r.get("nazwy_w_zwiazkach", [])]
        for n in nazwy:
            aliasy[n] = nazwy[0]
    return aliasy


# ---------------------------------------------------------------------
# GŁÓWNA FUNKCJA – wywoływana przez build.py
# ---------------------------------------------------------------------
def pobierz_dane(zrodla, rywale, bez_internetu=False):
    """
    Zwraca słownik: { "seniorki": {"mecze": [...], "tabela": [...], "pobrano": "..."} }
    oraz listę komunikatów (ostrzeżeń) do wyświetlenia przy budowaniu.
    """
    kopia = wczytaj_kopie()
    hale = kopia.setdefault("_hale", {})
    komunikaty = []
    wynik = {}
    aliasy = aliasy_z(rywale)

    for z in zrodla:
        klucz = z["druzyna"]
        stara = kopia.get(klucz, {})
        czesci = {}

        def sprobuj(nazwa, funkcja):
            if bez_internetu:
                czesci[nazwa] = stara.get(nazwa)
                return
            try:
                czesci[nazwa] = funkcja()
            except Exception as blad:  # strona nie działa lub zmieniła wygląd
                komunikaty.append(f"[{klucz}] {nazwa}: {blad} – używam ostatniej kopii")
                czesci[nazwa] = stara.get(nazwa)

        sprobuj("pzps_lista", lambda: parsuj_pzps_liste(pobierz(z["terminarz_zapasowy"]), z["nazwa_w_tabeli"]))
        sprobuj("wsmwzps", lambda: parsuj_wsmwzps(
            pobierz(z["terminarz"]), z["terminarz_sekcja"], z["nazwa_w_terminarzu"],
            z.get("godzina_zastepcza_minuty")))

        def tabela_i_wyniki():
            t, w = parsuj_pzps_tabele(pobierz(z["tabela"]), z["tabela_grupa"], z["nazwa_w_tabeli"])
            return {"tabela": t, "wyniki": w}
        sprobuj("pzps_tabela", tabela_i_wyniki)

        tw = czesci.get("pzps_tabela") or {"tabela": [], "wyniki": {}}
        mecze = polacz(czesci.get("pzps_lista") or [], czesci.get("wsmwzps") or [], tw["wyniki"], aliasy)

        # Hala i adres – tylko dla najbliższych meczów, raz pobrane zostają w kopii
        dzis = date.today()
        for m in mecze:
            mid = m.get("id")
            if not mid or m.get("wynik"):
                continue
            dni = (date.fromisoformat(m["data"]) - dzis).days
            if not bez_internetu and 0 <= dni <= DNI_HALI and (mid not in hale or not m.get("godzina")):
                try:
                    adres = "https://sedziowie.pzps.pl" + mid
                    info = parsuj_pzps_mecz(pobierz(adres))
                    if info:
                        hale[mid] = info
                    time.sleep(1)  # nie obciążamy serwera związku
                except Exception as blad:
                    komunikaty.append(f"[{klucz}] hala meczu {m['data']}: {blad}")
            info = hale.get(mid) or {}
            m["hala"], m["adres"] = info.get("hala"), info.get("adres")
            if not m.get("godzina") and info.get("godzina"):
                m["godzina"], m["godzina_pewna"] = info["godzina"], True

        teraz = datetime.now().isoformat(timespec="minutes")
        nowa = {k: v for k, v in czesci.items() if v}
        nowa["pobrano"] = teraz if not komunikaty else stara.get("pobrano", teraz)
        kopia[klucz] = nowa
        wynik[klucz] = {"mecze": mecze, "tabela": tw["tabela"], "pobrano": nowa["pobrano"]}

    if not bez_internetu:
        zapisz_kopie(kopia)
    return wynik, komunikaty


# Uruchomienie samego pliku = test pobierania:  python zrodla.py
if __name__ == "__main__":
    import sys
    sys.path.insert(0, FOLDER)
    import content
    dane, uwagi = pobierz_dane(content.ZRODLA_ZWIAZKOWE, content.RYWALE)
    for u in uwagi:
        print("UWAGA:", u)
    for druzyna, d in dane.items():
        print(f"\n== {druzyna}: {len(d['mecze'])} meczów, tabela: {len(d['tabela'])} drużyn")
        for m in d["mecze"]:
            print(f"  {m['data']} {m.get('godzina') or '--:--'}  {m['gospodarz']} – {m['gosc']}"
                  f"  {m.get('wynik', '')} {' '.join(m.get('sety', []))}  [{m['zrodlo']}]")
