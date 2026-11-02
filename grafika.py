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
        nazwa = f"wynik-{m['data'].isoformat()}-{m['wynik'].replace(':', '-')}.jpg"
        cel = os.path.join(folder, nazwa)
        if not os.path.isfile(cel):
            try:
                grafika_wyniku(m, sciezka_img, liga, dni, miesiace, dopisek, inicjaly).save(cel, "JPEG", quality=88, optimize=True)
                print(f"  Grafika wyniku: {nazwa}")
            except Exception as blad:
                print(f"  UWAGA: grafika wyniku {nazwa}: {type(blad).__name__}: {blad}")
                continue
        m["grafika_wyniku"] = f"grafiki/{nazwa}"
