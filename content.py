# =====================================================================
#  CONTENT.PY – WSZYSTKIE TREŚCI STRONY EASY WRAP VOLLEY KOBYŁKA
# ---------------------------------------------------------------------
#  To jedyny plik, który edytujesz na co dzień.
#  Po zmianie uruchom:  python build.py   → gotowa strona w folderze "strona/"
#  (Na GitHubie strona buduje się i wgrywa sama – patrz INSTRUKCJA.md)
#
#  ZASADY:
#   • Tekst zawsze w cudzysłowie: "Anna"
#   • Każdy element listy kończy się przecinkiem: { ... },
#   • Daty:  "2026-10-24"  (rok-miesiąc-dzień),  godziny: "18:00"
#   • Pusta wartość = None  (bez cudzysłowu), np. brak zdjęcia: "zdjecie": None
#   • Zdjęcia wrzucaj do folderu img/ (najlepiej WebP), tu wpisz ścieżkę
#     względem img/, np. "zawodniczki/anna-nowak.webp"
#   • Brakujące zdjęcie NIE psuje strony – pojawi się grafika zastępcza.
#
#  Dane oznaczone „PRZYKŁAD” trzeba podmienić na prawdziwe.
# =====================================================================


# ---------------------------------------------------------------------
# 1. DANE KLUBU
# ---------------------------------------------------------------------
KLUB = {
    "nazwa": "Easy Wrap Volley Kobyłka",
    "nazwa_krotka": "Easy Wrap Volley",
    "volleybox": "https://women.volleybox.net/pl/klub-sportowy-volley-kobylka-t18343",  # profil drużyny na Volleybox
    "nazwa_prawna": "Klub Sportowy Volley",
    "adres": "ul. ks. Marcina Załuskiego 57, 05-230 Kobyłka",
    "email": "kontakt@volleykobylka.pl",
    "telefon": None,                         # brak – wpisz, gdy będzie
    # Dane rejestrowe – pokazują się w polityce prywatności (administrator danych)
    "krs": "0000921839", "nip": "1251723179", "regon": "389970100",
    "herb": "herby/easy-wrap-volley.svg",    # oficjalny herb z księgi znaku – gdy wrzucisz ten plik, ma pierwszeństwo
    # Dopóki nie ma pliku powyżej, herb pobiera się z VolleyStation (raz, potem leży w img/herby/)
    "herb_volleystation": "https://assets.volleystation.com/website/teams/2248406/badge.png",
    "facebook": "https://www.facebook.com/101162122310332",   # strona Easy Wrap Volley (adres po ID strony)
    "instagram": "https://instagram.com/easy_wrap_volley_kobylka",
    "youtube": "https://youtube.com/@ks_Volley",
    "adres_strony": "https://volleykobylka.pl/",
    "opis": "Easy Wrap Volley Kobyłka – klub siatkówki kobiet z Kobyłki. 2. liga kobiet, "
            "Akademia Siatkówki Volley dla dzieci i młodzieży.",
}

# Hala, w której gramy u siebie (używana przy meczach wpisanych ręcznie)
HALA_DOMOWA = {
    "nazwa": "Hala Sportowa przy PSP nr 3 w Kobyłce",
    "adres": "ul. ks. Marcina Załuskiego 57, Kobyłka",
    "mapa": "https://www.google.com/maps/search/?api=1&query=ul.+ks.+Marcina+Za%C5%82uskiego+57+Kobyłka",
}

# Zdjęcia w nagłówkach stron (ścieżki względem img/).
#   Wystarczy wrzucić plik o podanej nazwie do img/naglowki/ – pojawi się sam.
#   Brak pliku = nagłówek bez zdjęcia (sam tytuł na granatowym tle).
#   Najlepiej poziome zdjęcia ok. 1600×1000 px w formacie WebP.
ZDJECIA_NAGLOWKOW = {
    "plakat_meczu": "naglowki/plakat-meczu.webp",   # plakat na stronie głównej (gdy mecz nie ma własnego "zdjecie_plakatu")
    "terminarz":    "naglowki/terminarz.webp",
    "druzyny":      "naglowki/druzyny.webp",
    "aktualnosci":  "naglowki/aktualnosci.webp",
    "galeria":      "naglowki/galeria.webp",
    "sponsorzy":    "naglowki/sponsorzy.webp",
    "o-klubie":     "naglowki/o-klubie.webp",
    "sklep":        "naglowki/sklep.webp",
    "kontakt":      "naglowki/kontakt.webp",
    "polityka":     None,
    "404":          None,
}

# ---------------------------------------------------------------------
# POSTY Z INSTAGRAMA / FACEBOOKA (oficjalne API Meta)
#   Strona sama bierze zdjęcia z postów klubu – rozpoznaje je po hashtagach.
#   Wymaga tokenu Meta (sekret META_TOKEN na GitHubie) – patrz INSTRUKCJA.md.
#   Bez tokenu wszystko działa dalej – zdjęcia można wrzucać ręcznie.
# ---------------------------------------------------------------------
META = {
    "zrodlo": "instagram",              # "instagram" albo "facebook"
    "instagram_id": None,               # ID konta firmowego IG (w cudzysłowie), np. "17841400000000000"
    "facebook_id": None,                # ID strony FB, np. "100000000000000"
}

# AKTUALNOŚCI Z FACEBOOKA – same się dodają, osobno dla drużyny i dla Akademii.
#   Strona sprawdza nowe posty 9 razy na dobę (o godzinach z listy "godziny", czas polski).
#   Z opisu posta znika część z oznaczeniami sponsorów (wszystko pod kreską „_________”),
#   dopiski typu @obserwujący i hashtagi na końcu. Zdjęcie posta zapisuje się na naszym serwerze.
#   Wymaga tokenów stron FB w sekrecie GitHuba META_TOKEN (oba tokeny, kolejność dowolna) – patrz INSTRUKCJA.md.
#   Bez tokenu strona pokazuje ostatnio zapisane posty (dane/aktualnosci_fb_*.json).
POSTY_FB = {
    "wlaczone": True,
    "godziny": [2, 4, 7, 9, 12, 14, 16, 18, 22],  # o której sprawdzać nowe posty (czas polski)
    "ile": 12,                          # ile ostatnich postów pokazywać
    "usun_hashtagi": True,              # hashtagi na końcu opisu nie trafiają na stronę
    # "strona" = fragment nazwy strony na Facebooku – po nim strona rozpoznaje, który token jest czyj
    # "id" = numer strony na Facebooku (potrzebny, gdy dostęp do strony jest przez konto firmowe Meta)
    "druzyna":  {"kategoria": "Seniorki", "strona": "Easy Wrap Volley", "id": "101162122310332"},
    "akademia": {"kategoria": "Akademia", "strona": "Akademia Siatkówki Volley", "id": "108955808681291"},
}

# Zapowiedź meczu – plakat pokazywany przez kilka sekund po wejściu na stronę główną.
#   Strona szuka posta z plakatem NAJBLIŻSZEGO meczu. Post jest uznany za zapowiedź, gdy:
#    • ma zdjęcie i ukazał się w ciągu "dni_przed" dni przed meczem,
#    • w opisie jest nazwa lub miasto rywala (np. „ŁKS”, „Łódź”), data meczu (np. „17.10”)
#      albo jedno ze "slowa_zapowiedzi".
#   Hashtagi klubu (np. #100LatSportuWkobylce) tylko pomagają wybrać, gdy pasuje kilka postów.
#   Jeśli plakat się nie pojawia – dopisz w opisie posta np. „Zapowiedź” albo nazwę rywala.
ZAPOWIEDZ = {
    "wlaczona": True,
    "dni_przed": 7,
    "slowa_zapowiedzi": ["zapowiedź", "zapowiedz", "#zapowiedz"],
    "hashtagi_klubu": ["#100LatSportuWkobylce", "#EasyWrapVolley"],
    "plik_reczny": None,                # np. "zapowiedz/kalisz.webp" – ma pierwszeństwo przed FB/IG
    "sekundy": 3,                       # jak długo widać plakat
    "raz_na_wizyte": True,              # True = pokaż tylko przy pierwszym wejściu (nie po każdym odświeżeniu)
}

# Zdjęcie w tle karty WYGRANEGO meczu („znak wodny”).
#   Źródło: post opublikowany do kilku dni po meczu z hashtagiem (np. #wygrana).
#   Ręcznie: wrzuć zdjęcie do img/wyniki/ z nazwą <drużyna>-<data meczu>,
#   np. img/wyniki/seniorki-2026-10-17.webp (albo .jpg) – pojawi się samo.
ZDJECIA_WYGRANYCH = {
    "wlaczone": True,
    "hashtagi": ["#wygrana", "#zwyciestwo", "#zwycięstwo", "#wynik"],
    "dni_po_meczu": 3,                  # ile dni po meczu szukać posta
}



# ---------------------------------------------------------------------
# 2. DRUŻYNY  (klucz, np. "seniorki", używany niżej przy meczach i kadrze)
# ---------------------------------------------------------------------
DRUZYNY = {
    "seniorki": {
        "nazwa": "Easy Wrap Volley Kobyłka",
        "krotko": "Seniorki",
        "liga": "2. liga kobiet · grupa 2",
        "opis": "Pierwsza drużyna klubu. Gramy w 2. lidze kobiet (grupa 2).",
        "zdjecie": None,                     # zdjęcie drużynowe, np. "druzyny/seniorki.webp"
    },
    "akademia": {
        "nazwa": "Akademia Siatkówki Volley",
        "krotko": "Akademia",
        "liga": "Turnieje i rozgrywki młodzieżowe",
        "opis": "Grupy dziecięce i młodzieżowe.",
        "zdjecie": None,
    },
}


# ---------------------------------------------------------------------
# 3. AUTOMATYCZNE POBIERANIE ZE STRON ZWIĄZKOWYCH
#   build.py sam pobiera daty, godziny, hale, wyniki, sety i tabelę.
#   NIE trzeba ich wpisywać ręcznie.
#   Gdy strona związku nie działa, użyte zostaną ostatnio pobrane dane
#   (plik dane/kopia_zwiazkowa.json) – strona nigdy nie zostanie „wyczyszczona”.
#
#   SKĄD CO BIERZEMY:
#   • terminarz i godzina meczu  → WSMWZPS (mazowiecki związek)
#   • tabela, wyniki i sety      → PZPS (2. liga kobiet, grupa 2)
#   • mecze, których nie ma w WSMWZPS (wyjazdy poza Mazowsze) → lista meczów PZPS
# ---------------------------------------------------------------------
ZRODLA_ZWIAZKOWE = [
    {
        "druzyna": "seniorki",                          # klucz z DRUZYNY

        # Terminarz – System Obsad Sędziowskich WSMWZPS
        "terminarz": "https://obsady.wsmwzps.pl/index.php?mode=4&type=12",
        "terminarz_sekcja": "II liga kobiet",           # nagłówek sekcji na tej stronie
        "nazwa_w_terminarzu": "EASY WRAP Volley Kobyłka",

        # Tabela i wyniki – System Obsad Sędziowskich PZPS
        "tabela": "https://sedziowie.pzps.pl/system/index.php?mode=12&type=8",
        "tabela_grupa": "Grupa 2",
        "nazwa_w_tabeli": "EASY WRAP Volley Kobyłka",

        # Zapas: pełna lista meczów PZPS (też mecze poza Mazowszem, hala)
        "terminarz_zapasowy": "https://sedziowie.pzps.pl/system/mecze-II-liga-kobiet/",

        # Godzina z minutami ":33" (np. 17:33) to w systemie obsad znacznik
        # „godzina jeszcze nieustalona” – strona pokaże wtedy „godzina wkrótce”.
        "godzina_zastepcza_minuty": "33",
    },
    # Kolejna drużyna (np. 3. liga) = kolejny taki blok
]


# ---------------------------------------------------------------------
# 4. RYWALE
#   Ten sam klub bywa różnie nazwany w WSMWZPS i PZPS – w "nazwy_w_zwiazkach"
#   są wszystkie warianty. Dzięki temu strona łączy mecze z obu źródeł
#   i pokazuje krótką nazwę oraz herb.
#
#   HERBY:
#   • "herb_volleystation" – adres logo z VolleyStation. Przy budowaniu logo
#     pobiera się RAZ do img/herby/<klucz>.png (lub .jpg) i potem leży w repozytorium.
#     Adres znajdziesz na stronie 2ligakobiet.volleystation.com: prawy klik na
#     logo drużyny → „Kopiuj adres obrazu”.
#   • "herb" – własny plik w img/herby/ (ma pierwszeństwo przed VolleyStation).
#   • bez obu – tarcza z inicjałami w kolorze "kolor".
#   VOLLEYBOX: "volleybox" – profil drużyny na women.volleybox.net (nazwa drużyny w tabeli i przy meczach staje się linkiem).
#   Nowy rywal, którego tu nie ma, też się wyświetli (pełną nazwą).
# ---------------------------------------------------------------------
VS = "https://assets.volleystation.com/website/teams/"
VB_PROFIL = "https://women.volleybox.net/pl/"           # skrót do profili drużyn na Volleybox   # skrót do adresów logo

RYWALE = {
    "varsovia":    {"skrot": "AZS AWF Varsovia", "herb": None, "volleybox": VB_PROFIL + "azs-awf-warszawa-t5635",
                    "kolor": "#7A1F2B",
                    "herb_volleystation": VS + "2248407/badge.jpg",
                    "nazwy_w_zwiazkach": ["AZS AWF Varsovia", "AZS AWF Warszawa"]},
    "aleksandrow": {"skrot": "Libero Aleksandrów Ł.", "herb": None, "volleybox": VB_PROFIL + "libero-vip-gwarant-aleksandrow-lodzki-t2015",
                    "kolor": "#C8102E",
                    "herb_volleystation": VS + "2248408/badge.png",
                    "nazwy_w_zwiazkach": ["Libero VIP Gwarant Aleksandrów Łódzki",
                                          "Libero VIP Biesiadowo Aleksandrów Łódzki"]},
    "mos-wola":    {"skrot": "MOS Wola AZS", "herb": None, "volleybox": VB_PROFIL + "azs-warszawa-t16855",
                    "kolor": "#1B5E20",
                    "herb_volleystation": VS + "2248410/badge.png",
                    "nazwy_w_zwiazkach": ["MOS Wola AZS Warszawa", "AZS Warszawa"]},
    "bielsk":      {"skrot": "TPS Bielsk Podlaski", "herb": None, "volleybox": VB_PROFIL + "tps-bielsk-podlaski-t28872",
                    "kolor": "#0D47A1",
                    "herb_volleystation": VS + "2248412/badge.jpg",
                    "nazwy_w_zwiazkach": ["TPS Bielsk Podlaski", "Towarzystwo Piłki Siatkowej Bielsk Podlaski"]},
    "lks-lodz":    {"skrot": "ŁKS AZS UMED Łódź", "herb": None, "volleybox": VB_PROFIL + "lks-lodz-ii-t12781",
                    "kolor": "#B71C1C",
                    "herb_volleystation": VS + "2248414/badge.png",
                    "nazwy_w_zwiazkach": ["ŁKS AZS UMED Łódź"]},
    "kalisz":      {"skrot": "MKS Kalisz II", "herb": None, "volleybox": VB_PROFIL + "energa-mks-kalisz-ii-t14031",
                    "kolor": "#E65100",
                    "herb_volleystation": VS + "2248416/badge.png",
                    "nazwy_w_zwiazkach": ["MKS Kalisz II", "Energa MKS Kalisz II"]},
    "krotka":      {"skrot": "MUKS Krótka", "herb": None, "volleybox": VB_PROFIL + "muks-krotka-mysiadlo-t19526",
                    "kolor": "#4A148C",
                    "herb_volleystation": VS + "2248417/badge.png",
                    "nazwy_w_zwiazkach": ["MUKS Krótka", "MUKS Krótka Mysiadło"]},
    "barycz":      {"skrot": "Barycz Janków P.", "herb": None, "volleybox": VB_PROFIL + "glks-barycz-jankow-przygodzki-t20015",
                    "kolor": "#00695C",
                    "herb_volleystation": VS + "2248415/badge.jpeg",
                    "nazwy_w_zwiazkach": ["MAPEI BARYCZ Janków Przygodzki", "GLKS Barycz Janków Przygodzki"]},
    "lask":        {"skrot": "Łaskovia Łask", "herb": None, "volleybox": VB_PROFIL + "sms-ostrow-laskovia-lask-t22245",
                    "kolor": "#283593",
                    "herb_volleystation": VS + "2248413/badge.png",
                    "nazwy_w_zwiazkach": ["SMS Ostrów Łaskovia Łask", "ŁMLKS Łaskovia Łask"]},
    "legionovia":  {"skrot": "Legionovia II", "herb": None, "volleybox": VB_PROFIL + "pge-lts-legionovia-legionowo-t17345",
                    "kolor": "#AD1457",
                    "herb_volleystation": VS + "2248411/badge.png",
                    "nazwy_w_zwiazkach": ["PGE LTS Legionovia Legionowo II", "PGE LTS Legionovia Legionowo 2"]},
    "raszyn":      {"skrot": "Orlęta Raszyn", "herb": None, "volleybox": VB_PROFIL + "uks-orleta-raszyn-t28575",
                    "kolor": "#2E7D32",
                    "herb_volleystation": VS + "2248409/badge.png",
                    "nazwy_w_zwiazkach": ["GKS Orlęta Raszyn", "UKS Orlęta Raszyn"]},
}


# ---------------------------------------------------------------------
# 5. MECZE – UZUPEŁNIENIA I MECZE SPOZA ZWIĄZKU
#
#   A) UZUPEŁNIENIE meczu ligowego (pobranego automatycznie):
#      wpisz "druzyna" i "data" meczu oraz to, czego związek nie podaje:
#      sponsor meczu, zdjęcie na plakat, MVP, link do relacji, transmisja.
#      Możesz też poprawić godzinę – wpisana tu wygrywa ze związkiem.
#
#   B) MECZ SPOZA ZWIĄZKU (sparing, turniej Akademii):
#      wpisz komplet: druzyna, data, godzina, gospodarz, gosc, hala.
#      Po meczu: "wynik": "3:1" (gospodarz:gość), "sety": ["25:21", ...]
# ---------------------------------------------------------------------
MECZE = [
    # A) uzupełnienie meczu ligowego
    {
        "druzyna": "seniorki", "data": "2026-10-24",
        "sponsor_meczu": "easy-wrap",                   # klucz z SPONSORZY albo None
        "zdjecie_plakatu": "plakaty/zawodniczka.webp",  # wycięta postać; brak pliku = grafika zastępcza
        "transmisja": "https://youtube.com/@ks_Volley",
        "mvp": None,
        "relacja": None,                                # adres newsa po meczu
    },
    {
        "druzyna": "seniorki", "data": "2026-10-17",
        "mvp": None,                                    # np. "Klaudia Kucharska"
        "relacja": None,                                # relacja z FB podpina się sama (post z wynikiem)
    },

    # B) turniej Akademii – wzór (odkomentuj i uzupełnij, gdy będzie prawdziwy):
    # {
    #     "druzyna": "akademia", "data": "2026-11-08", "godzina": "10:00",
    #     "gospodarz": "Turniej Akademii", "gosc": None,
    #     "hala": "Hala Sportowa przy PSP nr 3 w Kobyłce",
    # },
]


# ---------------------------------------------------------------------
# 6. KADRA – sezon 2026/27
#   Imiona i nazwiska wg VolleyStation, numery i pozycje wg trenera (18.10.2026).
#   zdjecie: plik z img/zawodniczki/ (wycięta postać, WebP, przezroczyste tło)
#            None → stylowa karta z numerem i inicjałami w barwach klubu
#   Opcjonalnie (pokażą się po najechaniu / dotknięciu karty):
#     "urodzona": "2001-03-12", "w_klubie_od": 2021, "wzrost": 181
#   Kapitan: "kapitan": True
# ---------------------------------------------------------------------
KADRA = [
    # Rozgrywające
    {"druzyna": "seniorki", "numer": 7,  "imie": "Natalia",   "nazwisko": "Bielińska",       "pozycja": "Rozgrywająca", "zdjecie": "zawodniczki/natalia-bielinska.webp"},
    {"druzyna": "seniorki", "numer": 20, "imie": "Zuzanna",   "nazwisko": "Kałkowska",       "pozycja": "Rozgrywająca", "zdjecie": "zawodniczki/zuzanna-kalkowska.webp"},
    # Atakujące
    {"druzyna": "seniorki", "numer": 14, "imie": "Nikola",    "nazwisko": "Gutowska",        "pozycja": "Atakująca",    "zdjecie": "zawodniczki/nikola-gutowska-mecz.webp"},
    {"druzyna": "seniorki", "numer": 17, "imie": "Natalia",   "nazwisko": "Dąbrowska",       "pozycja": "Atakująca",    "zdjecie": "zawodniczki/natalia-dabrowska-mecz.webp"},
    # Przyjmujące
    {"druzyna": "seniorki", "numer": 2,  "imie": "Julia",     "nazwisko": "Grzelak",         "pozycja": "Przyjmująca",  "zdjecie": "zawodniczki/julia-grzelak.webp"},
    {"druzyna": "seniorki", "numer": 6,  "imie": "Kamila",    "nazwisko": "Wrzosek",         "pozycja": "Przyjmująca",  "zdjecie": "zawodniczki/kamila-wrzosek-mecz.webp"},
    {"druzyna": "seniorki", "numer": 10, "imie": "Kaja",      "nazwisko": "Klepacz",         "pozycja": "Przyjmująca",  "zdjecie": "zawodniczki/kaja-klepacz-mecz.webp"},
    {"druzyna": "seniorki", "numer": 21, "imie": "Matylda",   "nazwisko": "Woźny",           "pozycja": "Przyjmująca",  "zdjecie": "zawodniczki/matylda-wozny-mecz.webp"},
    # Środkowe
    {"druzyna": "seniorki", "numer": 11, "imie": "Natalia",   "nazwisko": "Pietruszkiewicz", "pozycja": "Środkowa",     "zdjecie": "zawodniczki/natalia-pietruszkiewicz-mecz.webp"},
    {"druzyna": "seniorki", "numer": 12, "imie": "Wiktoria",  "nazwisko": "Sztylko",         "pozycja": "Środkowa",     "zdjecie": "zawodniczki/wiktoria-sztylko.webp"},
    {"druzyna": "seniorki", "numer": 22, "imie": "Adrianna",  "nazwisko": "Sitarska",        "pozycja": "Środkowa",     "zdjecie": "zawodniczki/adrianna-sitarska-mecz.webp"},
    # Libero
    {"druzyna": "seniorki", "numer": 8,  "imie": "Klaudia",   "nazwisko": "Kucharska",       "pozycja": "Libero",       "zdjecie": "zawodniczki/klaudia-kucharska-mecz.webp", "kapitan": True},
    {"druzyna": "seniorki", "numer": 23, "imie": "Małgorzata", "nazwisko": "Czajka",         "pozycja": "Libero",       "zdjecie": "zawodniczki/malgorzata-czajka-mecz.webp"},
]

# Kolejność pozycji na stronie Drużyny
POZYCJE = ["Rozgrywająca", "Atakująca", "Przyjmująca", "Środkowa", "Libero"]

# Sztab szkoleniowy – DO UZUPEŁNIENIA. Pusta lista = sekcja „Sztab” się nie pokazuje.
#   Wzór: {"druzyna": "seniorki", "imie": "Jan", "nazwisko": "Kowalski", "funkcja": "Trener", "zdjecie": None},
SZTAB = [
]


# ---------------------------------------------------------------------
# 7. AKTUALNOŚCI
#   adres: krótka nazwa bez polskich znaków i spacji → aktualnosci/adres.html
#   tresc: zwykły tekst; pusta linia = nowy akapit
#   Najnowsze na górze strony układają się same (wg daty).
# ---------------------------------------------------------------------
NEWSY = [
    {
        "adres": "easy-wrap-sponsorem-tytularnym",
        "data": "2026-09-01",
        "kategoria": "Klub",
        "tytul": "Easy Wrap sponsorem tytularnym",
        "zajawka": "Easy Wrap jest sponsorem tytularnym drużyny seniorek w sezonie 2026/27.",
        "zdjecie": None,
        "tresc": """
Easy Wrap jest sponsorem tytularnym naszej drużyny seniorek w sezonie 2026/27.
Dlatego w rozgrywkach 2. ligi kobiet występujemy jako Easy Wrap Volley Kobyłka.

Dziękujemy za wsparcie!
""",
    },
]


# ---------------------------------------------------------------------
# 8. SPONSORZY  (poziom: "tytularny" / "strategiczny" / "partner")
#   prezentuje: nazwa sekcji, przy której pokaże się „prezentowane przez”:
#   "tabela", "kadra", "akademia", "terminarz" albo None
# ---------------------------------------------------------------------
#   logo: plik w img/sponsorzy/ (PNG/SVG/WebP), np. "sponsorzy/easy-wrap.webp" – dopóki brak, widać nazwę
#   poziom: "tytularny", "strategiczny", "techniczny" (partner techniczny) albo "partner"
SPONSORZY = {
    "easy-wrap":  {"nazwa": "Easy Wrap", "poziom": "tytularny", "logo": "sponsorzy/easy-wrap.webp", "www": "https://easywrap.pl", "prezentuje": None},
    "miasto":     {"nazwa": "Miasto Kobyłka", "poziom": "strategiczny", "logo": "sponsorzy/miasto.webp", "www": "https://kobylka.pl", "prezentuje": None},
    "pit-radwar": {"nazwa": "PIT-RADWAR", "poziom": "strategiczny", "logo": "sponsorzy/pit-radwar.webp", "www": "https://pitradwar.com", "prezentuje": None},
    "vexar":      {"nazwa": "VEXAR ATHLETIC", "poziom": "techniczny", "logo": "sponsorzy/vexar.webp", "www": None, "prezentuje": None},
    "dorol":      {"nazwa": "Dorol", "poziom": "partner", "logo": "sponsorzy/dorol.webp", "www": "https://dorol.pl", "prezentuje": None},
    "fhr":        {"nazwa": "FHR", "poziom": "partner", "logo": "sponsorzy/fhr.webp", "www": "https://fhr.com.pl", "prezentuje": None},
    "fortisgo":   {"nazwa": "fortisGO", "poziom": "partner", "logo": "sponsorzy/fortisgo.webp", "www": "https://fortisgo.com", "prezentuje": None},
    "impression": {"nazwa": "Impression Studio Reklamy", "poziom": "partner", "logo": "sponsorzy/impression-czarne.webp", "www": "https://impression4you.pl", "prezentuje": None},
    "kriva":      {"nazwa": "Kriva HiTech Beauty", "poziom": "partner", "logo": "sponsorzy/kriva.webp", "www": "https://kriva-hitechbeauty.pl/", "prezentuje": None},
    "racbus":     {"nazwa": "Racbus", "poziom": "partner", "logo": "sponsorzy/racbus.webp", "www": "https://racbus.pl", "prezentuje": None},
    "zdrofit":    {"nazwa": "Zdrofit", "poziom": "partner", "logo": "sponsorzy/zdrofit.webp", "www": "https://zdrofit.pl", "prezentuje": None},
    "sp3":        {"nazwa": "SP nr 3 im. Karola Wojtyły w Kobyłce", "poziom": "partner", "logo": "sponsorzy/sp3.webp", "www": "https://sp3kobylka.pl", "prezentuje": None},
    "osir":       {"nazwa": "OSiR „Wicher” w Kobyłce", "poziom": "partner", "logo": "sponsorzy/osir.webp", "www": None, "prezentuje": None},
    "osp":        {"nazwa": "OSP Kobyłka", "poziom": "partner", "logo": "sponsorzy/osp.webp", "www": None, "prezentuje": None},
}

# Licznik wyświetleń w stopce (darmowy serwis Abacus, bez konta i bez cookies).
#   wlaczony: False – licznik znika ze strony.
#   klucz: zmiana nazwy = licznik od zera.
LICZNIK = {"wlaczony": True, "przestrzen": "volleykobylka-pl", "klucz": "odwiedziny"}   # nowy klucz = licznik od zera (reset 28.10.2026)

SPONSORZY_TEKST = ("Wspierasz lokalny sport? Pokaż swoją markę na meczach 2. ligi, "
                   "w mediach klubu i na koszulkach Akademii. Napisz do nas.")


# ---------------------------------------------------------------------
# 9. KALENDARIUM – wydarzenia (mecze i treningi dodają się same)
#   typ: "wydarzenie" (inne typy: mecze z MECZE i związku, treningi z AKADEMIA)
# ---------------------------------------------------------------------
#   Wzór: {"data": "2026-12-20", "godzina": "17:00", "tytul": "Wigilia klubowa", "miejsce": "Hala przy PSP nr 3"},
WYDARZENIA = [
]


# ---------------------------------------------------------------------
# 10. AKADEMIA SIATKÓWKI VOLLEY
# ---------------------------------------------------------------------
AKADEMIA = {
    # Akademia ma na stronie własną część (akademia.html): własne logo, menu i stopkę – tylko Facebook.
    "nazwa": "Akademia Siatkówki Volley",
    "logo": "akademia/logo.webp",               # logo z profilu Akademii na Facebooku
    "facebook": "https://www.facebook.com/profile.php?id=100087224682607",
    # Koordynator projektu – kontakt w sekcji „Kontakt”. Puste pola się nie pokazują.
    "koordynator": {"imie": None, "rola": "Koordynator Akademii", "telefon": None,
                    "email": "akademia@volleykobylka.pl"},
    "haslo": "Dołącz do nas!",
    "opis": "Treningi siatkówki dla dziewcząt w hali przy ul. Załuskiego 57 w Kobyłce. Bez wpisowego.",
    # Cennik i najważniejsze zasady – pokazują się w pierwszym ekranie strony Akademii
    "cennik": [
        {"co": "2 treningi w tygodniu", "cena": "180 zł / mies."},
        {"co": "1 trening w tygodniu", "cena": "130 zł / mies."},
    ],
    "fakty": ["Trening trwa 90 minut", "Bez wpisowego", "Zajęcia tylko dla dziewcząt", "Umowa na sezon (wrzesień–czerwiec)"],
    "formularz_google": None,   # wklej link do formularza Google, np. "https://docs.google.com/forms/d/e/.../viewform"
    "zdjecie": None,            # zdjęcie do nagłówka, np. "akademia/hero.webp"
    # Grupy – DO UZUPEŁNIENIA. Pusta lista = sekcja się nie pokazuje.
    #   Wzór: {"nazwa": "Mini Volley", "wiek": "7–10 lat", "opis": "Zabawa z piłką i pierwsze odbicia."},
    "grupy": [
    ],
    # Trenerzy – DO UZUPEŁNIENIA. Pusta lista = sekcja się nie pokazuje.
    #   Wzór: {"imie": "Jan", "nazwisko": "Kowalski", "opis": "Trener II klasy.", "zdjecie": None},
    "trenerzy": [
    ],
    # Harmonogram treningów – pojawi się też w kalendarium (w okresie sezonu)
    "sezon_od": "2026-09-01",
    "sezon_do": "2027-06-20",
    "dni_wolne": ["2026-11-11", "2026-12-24", "2026-12-25", "2026-12-26", "2026-12-31", "2027-01-01", "2027-01-06"],
    # Harmonogram – DO UZUPEŁNIENIA. Pusta lista = sekcja się nie pokazuje.
    #   Wzór: {"grupa": "Mini Volley", "dzien": "poniedziałek", "od": "16:00", "do": "17:30", "hala": "Hala przy PSP nr 3"},
    "harmonogram": [
    ],
    "ochrona_maloletnich": {
        "tekst": "Klub stosuje Standardy Ochrony Małoletnich. Każda osoba pracująca z dziećmi "
                 "ma aktualne zaświadczenie o niekaralności i jest sprawdzona w Rejestrze Sprawców "
                 "Przestępstw na Tle Seksualnym. Masz wątpliwości lub niepokoi Cię czyjeś zachowanie? "
                 "Napisz do osoby odpowiedzialnej za standardy.",
        "dokument": "dokumenty/standardy-ochrony-maloletnich.pdf",   # pełna wersja (w folderze img/)
        # Wersja skrócona dla dzieci (wymóg ustawy) – prostym językiem, na podstawie Standardów Klubu
        "dla_dzieci": [
            "Każdy w Klubie traktuje Cię z szacunkiem. Nikt nie może Cię bić, popychać, wyzywać, ośmieszać ani na Ciebie krzyczeć (chyba że ostrzega przed niebezpieczeństwem).",
            "Trener może Cię dotknąć tylko wtedy, gdy pomaga w ćwiczeniu lub poprawia ułożenie ciała – zawsze jawnie. Jeśli coś jest dla Ciebie nieprzyjemne, masz prawo powiedzieć „nie”.",
            "Trenerzy nie spotykają się z Tobą prywatnie i nie zapraszają Cię do domu. Rozmawiamy na treningach i w hali.",
            "Twoje zdjęcia i informacje o Tobie są chronione – publikujemy je tylko za zgodą rodzica.",
            "Jeśli ktoś sprawia Ci przykrość albo coś Cię niepokoi – w Klubie, w domu czy w internecie – powiedz rodzicowi, trenerowi albo osobie, której ufasz. Pomożemy.",
        ],
        "osoba_kontaktowa": "kontakt@volleykobylka.pl",
    },
}


# ---------------------------------------------------------------------
# 11. SKLEP (bez płatności – przycisk „Zamów” otwiera e-mail)
# ---------------------------------------------------------------------
SKLEP = {
    "jak_zamowic": "Napisz do nas z nazwą produktu i rozmiarem. Odbiór na meczu u siebie.",
    "formularz_google": None,
    # Produkty – DO UZUPEŁNIENIA. Pusta lista = sklep znika z menu i strony głównej.
    #   Wzór: {"nazwa": "Koszulka kibica 2026/27", "cena": "89 zł", "rozmiary": "XS–XXL", "zdjecie": None, "dostepny": True},
    "produkty": [
    ],
}


# ---------------------------------------------------------------------
# 12. GALERIA
#   Zdjęcia wrzuć do img/galeria/<folder>/ – strona sama je znajdzie.
# ---------------------------------------------------------------------
#   Galeria znika z menu, dopóki żaden album nie ma zdjęć.
#   Wzór: {"tytul": "ŁKS AZS UMED Łódź – Easy Wrap Volley", "data": "2026-10-17", "folder": "2026-10-17-lodz"},
GALERIA = [
]


# ---------------------------------------------------------------------
# 13. O KLUBIE
# ---------------------------------------------------------------------
O_KLUBIE = {
    "historia": """
Klub Sportowy Volley z Kobyłki powstał w 2021 roku. Skupiamy się na szkoleniu młodzieży,
wspieraniu zawodniczek i udziale w rozgrywkach seniorskich.

Nasza pierwsza drużyna gra w 2. lidze kobiet jako Easy Wrap Volley Kobyłka.
Szkolimy dziewczęta w Akademii Siatkówki Volley i organizujemy obozy sportowe.
""",
    # Pasek sukcesów – DO UZUPEŁNIENIA. Pusta lista = pasek się nie pokazuje.
    #   Wzór: {"rok": 2025, "opis": "Awans do 2. ligi"},
    "trofea": [
    ],
    "wartosci": ["Zaangażowanie", "Pasja", "Determinacja", "Ambicja"],
}


# ---------------------------------------------------------------------
# 14. KONTAKT
# ---------------------------------------------------------------------
KONTAKT = {
    "osoby": [
        {"rola": "Sprawy klubu i sponsorzy", "imie": None, "email": "kontakt@volleykobylka.pl"},
        {"rola": "Zapisy do Akademii", "imie": None, "email": "akademia@volleykobylka.pl"},
    ],
    "formularz_google": None,
}
