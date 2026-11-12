# =====================================================================
#  GRAFIKA „WYNIK MECZU” – powstaje sama po każdym rozegranym meczu seniorek
#  Plik: img/grafiki/wynik-<data>-<wynik>.jpg (1080×1350 – format posta na FB/IG)
#  Mecz u siebie = wersja granatowa, wyjazd = błękitna (jak grafiki meczowe klubu).
#  Gospodarz zawsze pierwszy (u góry/po lewej).
# =====================================================================
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FOLDER = os.path.dirname(os.path.abspath(__file__))
FONTY = os.path.join(FOLDER, "grafika", "fonty")
W, H = 1080, 1350

GRANAT, GRANAT_C, BLEKIT, ZOLTY, BIALY = (0, 47, 108), (0, 26, 63), (6, 157, 223), (255, 199, 44), (255, 255, 255)


def _f(nazwa, rozmiar):
    return ImageFont.truetype(os.path.join(FONTY, nazwa), rozmiar)


def bebas(r):
    return _f("BebasNeue_400Regular.ttf", r)


def barlow(r, gruby=True):
    return _f("BarlowCondensed_700Bold.ttf" if gruby else "BarlowCondensed_600SemiBold.ttf", r)


def _hex(kolor):
    kolor = (kolor or "#3A4A63").lstrip("#")
    return tuple(int(kolor[i:i + 2], 16) for i in (0, 2, 4))


def _tlo(wyjazd):
    gora, dol = ((40, 170, 235), (6, 120, 190)) if wyjazd else ((0, 63, 140), GRANAT_C)
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(gora[i] * (1 - t) + dol[i] * t) for i in range(3)))
    # ukośne paski jak na stronie
    paski = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dp = ImageDraw.Draw(paski)
    for x in range(-H, W, 46):
        dp.polygon([(x, H), (x + 16, H), (x + 16 + H * 0.6, 0), (x + H * 0.6, 0)], fill=(255, 255, 255, 14))
    im.paste(paski, (0, 0), paski)
    return im


def _tarcza(tekst, kolor, rozmiar):
    sk = rozmiar / 70
    im = Image.new("RGBA", (int(60 * sk), int(70 * sk)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pkt = [(30, 2), (56, 10), (56, 34), (52, 47), (42, 59), (30, 68), (18, 59), (8, 47), (4, 34), (4, 10)]
    d.polygon([(x * sk, y * sk) for x, y in pkt], fill=_hex(kolor), outline=BIALY, width=max(2, int(3 * sk)))
    f = bebas(int((22 if len(tekst) <= 2 else 18 if len(tekst) == 3 else 14) * sk * 1.1))
    d.text((30 * sk, 38 * sk), tekst, font=f, fill=BIALY, anchor="mm")
    return im


def _herb(strona, rozmiar, sciezka_img, inicjaly=None):
    """Herb jako obraz RGBA o wysokości `rozmiar`."""
    plik = None
    if strona.get("nasza"):
        for kandydat in ("favicon-512.png", "herby/easy-wrap-volley.png"):
            if os.path.isfile(os.path.join(sciezka_img, kandydat)):
                plik = os.path.join(sciezka_img, kandydat)
                break
    else:
        r = strona.get("rywal") or {}
        if r.get("herb") and os.path.isfile(os.path.join(sciezka_img, r["herb"])):
            plik = os.path.join(sciezka_img, r["herb"])
    if plik:
        try:
            im = Image.open(plik).convert("RGBA")
            bb = im.getbbox()
            if bb:
                im = im.crop(bb)
            im.thumbnail((rozmiar, rozmiar), Image.LANCZOS)
            return im
        except Exception:
            pass
    if inicjaly:
        skrot = inicjaly(strona["krotko"])
    else:
        slowa = [w for w in strona["krotko"].replace(".", " ").split() if w[:1].isalpha()]
        skrot = ("".join(w[0] for w in slowa[:3]) or "?").upper()
    return _tarcza(skrot, (strona.get("rywal") or {}).get("kolor"), rozmiar)


def _cien(im, warstwa, xy):
    cien = Image.new("RGBA", warstwa.size, (0, 0, 0, 0))
    cien.paste((0, 10, 30, 110), (0, 0), warstwa.split()[3])
    cien = cien.filter(ImageFilter.GaussianBlur(14))
    im.paste(cien, (xy[0], xy[1] + 14), cien)
    im.paste(warstwa, xy, warstwa)


def _zawin(tekst, font, szer):
    slowa, linie, ak = tekst.upper().split(), [], ""
    for s in slowa:
        prop = (ak + " " + s).strip()
        if font.getlength(prop) <= szer or not ak:
            ak = prop
        else:
            linie.append(ak)
            ak = s
    return linie + [ak]


def grafika_wyniku(m, sciezka_img, liga, dni, miesiace, dopisek=None, inicjaly=None):
    """Tworzy obraz wyniku meczu `m` (słownik meczu z build.py). Zwraca obiekt PIL.Image."""
    gosp, gosc = m["strony"]
    wyjazd = not m.get("u_siebie")
    tekst = GRANAT_C if wyjazd else BIALY
    akcent = GRANAT_C if wyjazd else ZOLTY
    polprzezr = (0, 26, 63) if wyjazd else (255, 255, 255)
    im = _tlo(wyjazd).convert("RGBA")
    warstwa = Image.new("RGBA", im.size, (0, 0, 0, 0))      # półprzezroczyste elementy
    dw = ImageDraw.Draw(warstwa)

    # Plakietka wygrana/porażka
    wygrana = m.get("wygrana")
    etykieta = "WYGRANA!" if wygrana else "PORAŻKA"
    fe = barlow(42)
    sz = int(fe.getlength(etykieta)) + 64
    x0 = (W - sz) // 2
    if wygrana:
        dw.rounded_rectangle([x0, 196, x0 + sz, 260], radius=32, fill=(GRANAT_C if wyjazd else ZOLTY) + (255,))
    else:
        dw.rounded_rectangle([x0, 196, x0 + sz, 260], radius=32, outline=polprzezr + (200,), width=3)

    # Sety – półprzezroczyste „chipy”
    sety = m.get("sety") or []
    fs = barlow(46)
    szer = [int(fs.getlength(x)) + 48 for x in sety]
    xs = (W - (sum(szer) + 16 * max(0, len(sety) - 1))) // 2
    pozycje = []
    for s, sw in zip(sety, szer):
        dw.rounded_rectangle([xs, 960, xs + sw, 1030], radius=18, fill=polprzezr + (38,), outline=polprzezr + (90,), width=2)
        pozycje.append((xs + sw // 2, s))
        xs += sw + 16
    dw.line([(90, 1180), (W - 90, 1180)], fill=polprzezr + (80,), width=2)
    im = Image.alpha_composite(im, warstwa)
    d = ImageDraw.Draw(im)

    d.text((W // 2, 112), "WYNIK MECZU", font=bebas(150), fill=tekst, anchor="mm")
    d.text((W // 2, 229), etykieta, font=fe, anchor="mm",
           fill=(BIALY if wyjazd else GRANAT_C) if wygrana else tekst)

    # Herby i nazwy – gospodarz po lewej
    for i, s in enumerate((gosp, gosc)):
        cx = 280 if i == 0 else W - 280
        h = _herb(s, 240, sciezka_img, inicjaly)
        _cien(im, h, (cx - h.width // 2, 300 + (240 - h.height) // 2))
        d = ImageDraw.Draw(im)
        fn = bebas(60)
        for j, linia in enumerate(_zawin(s["krotko"], fn, 480)[:2]):
            d.text((cx, 590 + j * 58), linia, font=fn, fill=tekst, anchor="mm")

    # Wynik
    a, b = m["wynik"].split(":")
    fw = bebas(300)
    d.text((W // 2, 805), ":", font=bebas(190), fill=akcent, anchor="mm")
    d.text((W // 2 - 64, 810), a, font=fw, fill=tekst, anchor="rm")
    d.text((W // 2 + 64, 810), b, font=fw, fill=tekst, anchor="lm")

    for x, s in pozycje:
        d.text((x, 995), s, font=fs, fill=tekst, anchor="mm")

    dz = m["data"]
    d.text((W // 2, 1080), f"{dni[dz.weekday()].upper()}, {dz.day} {miesiace[dz.month - 1].upper()} {dz.year}",
           font=barlow(44), fill=tekst, anchor="mm")
    d.text((W // 2, 1132), liga.upper(), font=barlow(34, False), fill=tekst, anchor="mm")
    stopka = "EASY WRAP VOLLEY KOBYŁKA  ·  VOLLEYKOBYLKA.PL"
    if m.get("mvp"):
        stopka = f"MVP: {m['mvp'].upper()}  ·  VOLLEYKOBYLKA.PL"
    d.text((W // 2, 1232), stopka, font=barlow(36), fill=tekst, anchor="mm")
    if dopisek:
        d.text((W // 2, 1300), dopisek, font=barlow(26, False), fill=tekst, anchor="mm")
    return im.convert("RGB")


def zapisz_grafiki_wynikow(mecze, sciezka_img, liga, dni, miesiace, dopisek=None, inicjaly=None):
    """Dla każdego meczu z wynikiem tworzy grafikę (tylko raz – gdy pliku jeszcze nie ma).
    Ustawia m["grafika_wyniku"] = ścieżka względem img/."""
    folder = os.path.join(sciezka_img, "grafiki")
    os.makedirs(folder, exist_ok=True)
    for m in mecze:
        if not m.get("wynik") or not m.get("strony") or not m["strony"][1]:
            continue
        nazwa = f"wynik-{m['data'].isoformat()}-{m['wynik'].replace(':', '-')}{'-mvp' if m.get('mvp') else ''}.jpg"
        cel = os.path.join(folder, nazwa)
        if not os.path.isfile(cel):
            try:
                grafika_wyniku(m, sciezka_img, liga, dni, miesiace, dopisek, inicjaly).save(cel, "JPEG", quality=88, optimize=True)
                print(f"  Grafika wyniku: {nazwa}")
            except Exception as blad:
                print(f"  UWAGA: grafika wyniku {nazwa}: {type(blad).__name__}: {blad}")
                continue
        m["grafika_wyniku"] = f"grafiki/{nazwa}"


# =====================================================================
#  PODGLĄD LINKU (og:image) – zapowiedź najbliższego meczu, 1200×630
#  Pokazuje się, gdy ktoś wklei adres strony na Facebooku, w Messengerze,
#  WhatsAppie. Powstaje przy każdej przebudowie strony.
# =====================================================================
def _tlo_og(wyjazd, w, h):
    gora, dol = ((40, 170, 235), (6, 120, 190)) if wyjazd else ((0, 63, 140), GRANAT_C)
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for x in range(w):
        t = x / w
        d.line([(x, 0), (x, h)], fill=tuple(int(gora[i] * (1 - t) + dol[i] * t) for i in range(3)))
    paski = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dp = ImageDraw.Draw(paski)
    for x in range(-h, w, 40):
        dp.polygon([(x, h), (x + 14, h), (x + 14 + h * 0.6, 0), (x + h * 0.6, 0)], fill=(255, 255, 255, 14))
    im.paste(paski, (0, 0), paski)
    return im


def grafika_og(m, sciezka_img, plik_postaci, zawodniczka, dni, miesiace, inicjaly=None, wstep_wolny=False, dopisek=None):
    OW, OH = 1200, 630
    gosp, gosc = m["strony"]
    wyjazd = not m.get("u_siebie")
    tekst = GRANAT_C if wyjazd else BIALY
    akcent = GRANAT_C if wyjazd else ZOLTY
    im = _tlo_og(wyjazd, OW, OH).convert("RGBA")

    # wycięta zawodniczka przy prawej krawędzi
    if plik_postaci and os.path.isfile(plik_postaci):
        try:
            post = Image.open(plik_postaci).convert("RGBA")
            bb = post.getbbox()
            if bb:
                post = post.crop(bb)
            skala = (OH - 30) / post.height
            post = post.resize((int(post.width * skala), OH - 30), Image.LANCZOS)
            _cien(im, post, (OW - post.width + 10, 30))
        except Exception:
            pass

    d = ImageDraw.Draw(im)
    # etykieta
    etyk = "MECZ WYJAZDOWY" if wyjazd else "MECZ U SIEBIE"
    fe = barlow(30)
    sz = int(fe.getlength(etyk)) + 44
    d.rounded_rectangle([60, 48, 60 + sz, 98], radius=25, fill=(GRANAT_C if wyjazd else ZOLTY))
    d.text((60 + sz // 2, 73), etyk, font=fe, fill=(BIALY if wyjazd else GRANAT_C), anchor="mm")
    d.text((60 + sz + 20, 73), (m.get("liga") or "").upper(), font=barlow(26, False), fill=tekst, anchor="lm")

    # herby obok siebie z VS – gospodarz pierwszy
    for i, s in enumerate((gosp, gosc)):
        if not s:
            continue
        cx = 150 + i * 300
        h = _herb(s, 150, sciezka_img, inicjaly)
        _cien(im, h, (cx - h.width // 2, 130 + (150 - h.height) // 2))
        d = ImageDraw.Draw(im)
        fn = bebas(42)
        for j, linia in enumerate(_zawin(s["krotko"], fn, 270)[:2]):
            d.text((cx, 312 + j * 40), linia, font=fn, fill=tekst, anchor="mm")
    if gosc:
        d.text((300, 205), "VS", font=bebas(70), fill=akcent, anchor="mm")

    # data
    dz = m["data"]
    d.text((60, 470), str(dz.day), font=bebas(170), fill=tekst, anchor="ls")
    x = 60 + bebas(170).getlength(str(dz.day)) + 18
    d.text((x, 420), dni[dz.weekday()].upper(), font=bebas(52), fill=tekst, anchor="ls")
    d.text((x, 470), miesiace[dz.month - 1].upper(), font=bebas(52), fill=tekst, anchor="ls")

    godz = f"GODZ. {m['godzina']}" if m.get("godzina") else "GODZINA WKRÓTCE"
    hala = (m.get("hala") or "").upper()
    d.text((60, 520), godz, font=bebas(46), fill=akcent, anchor="ls")
    gx = 60 + bebas(46).getlength(godz) + 24
    if hala:
        fh = barlow(28)
        while fh.getlength(hala) > 640 - gx and len(hala) > 10:
            hala = hala[:-2]
        d.text((gx, 516), hala, font=fh, fill=tekst, anchor="ls")
    dolny = "VOLLEYKOBYLKA.PL"
    if wstep_wolny and m.get("u_siebie"):
        dolny = "WSTĘP WOLNY  ·  " + dolny
    d.text((60, 572), dolny, font=barlow(30), fill=tekst, anchor="ls")
    if dopisek:
        d.text((60, 606), dopisek, font=barlow(20, False), fill=tekst, anchor="ls")

    # karta „Zapraszam!” z numerem i nazwiskiem
    if zawodniczka and plik_postaci and os.path.isfile(plik_postaci):
        kx, ky, kw, kh = OW - 400, OH - 150, 360, 110
        karta = Image.new("RGBA", (kw + 40, kh + 60), (0, 0, 0, 0))
        dk = ImageDraw.Draw(karta)
        dk.rounded_rectangle([0, 30, kw, 30 + kh], radius=20, fill=GRANAT_C + (240,), outline=ZOLTY, width=3)
        dk.rounded_rectangle([18, 8, 196, 50], radius=12, fill=ZOLTY)
        dk.text((107, 29), "ZAPRASZAM!", font=bebas(32), fill=GRANAT_C, anchor="mm")
        dk.ellipse([22, 50, 102, 130], fill=ZOLTY)
        dk.text((62, 92), f"{zawodniczka['numer']}", font=bebas(52), fill=GRANAT_C, anchor="mm")
        dk.text((120, 74), zawodniczka["imie"].upper(), font=barlow(22), fill=(207, 227, 255), anchor="lm")
        dk.text((120, 106), zawodniczka["nazwisko"].upper(), font=bebas(48), fill=BIALY, anchor="lm")
        _cien(im, karta, (kx, ky - 30))
    return im.convert("RGB")
