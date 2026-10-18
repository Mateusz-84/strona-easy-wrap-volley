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
    "nazwa_prawna": "Klub Sportowy Volley",
    "adres": "ul. ks. Marcina Załuskiego 57, 05-230 Kobyłka",
    "email": "ks.volley.kobylka@gmail.com",
    "telefon": None,                         # brak – wpisz, gdy będzie
    "herb": "herby/easy-wrap-volley.svg",    # oficjalny herb z księgi znaku – gdy wrzucisz ten plik, ma pierwszeństwo
    # Dopóki nie ma pliku powyżej, herb pobiera się z VolleyStation (raz, potem leży w img/herby/)
    "herb_volleystation": "https://assets.volleystation.com/website/teams/2248406/badge.png",
    "facebook": "https://facebook.com/easywrapvolley",
    "instagram": "https://instagram.com/easy_wrap_volley_kobylka",
    "youtube": "https://youtube.com/@ks_Volley",
    "adres_strony": None,                    # np. "https://volleykobylka.pl" – gdy będzie domena
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

# Hasła na przesuwanych taśmach (między sekcjami)
TASMA_1 = ["Jedna drużyna", "Jedno miasto", "Easy Wrap Volley", "Kobyłka gra razem"]
TASMA_2 = ["#EasyWrapVolley", "Przyjdź na mecz", "Wstęp wolny", "Hala przy PSP nr 3"]


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
#   Nowy rywal, którego tu nie ma, też się wyświetli (pełną nazwą).
# ---------------------------------------------------------------------
VS = "https://assets.volleystation.com/website/teams/"   # skrót do adresów logo

RYWALE = {
    "varsovia":    {"skrot": "AZS AWF Varsovia", "herb": None, "kolor": "#7A1F2B",
                    "herb_volleystation": VS + "2248407/badge.jpg",
                    "nazwy_w_zwiazkach": ["AZS AWF Varsovia", "AZS AWF Warszawa"]},
    "aleksandrow": {"skrot": "Libero Aleksandrów Ł.", "herb": None, "kolor": "#C8102E",
                    "herb_volleystation": VS + "2248408/badge.png",
                    "nazwy_w_zwiazkach": ["Libero VIP Gwarant Aleksandrów Łódzki",
                                          "Libero VIP Biesiadowo Aleksandrów Łódzki"]},
    "mos-wola":    {"skrot": "MOS Wola AZS", "herb": None, "kolor": "#1B5E20",
                    "herb_volleystation": VS + "2248410/badge.png",
                    "nazwy_w_zwiazkach": ["MOS Wola AZS Warszawa", "AZS Warszawa"]},
    "bielsk":      {"skrot": "TPS Bielsk Podlaski", "herb": None, "kolor": "#0D47A1",
                    "herb_volleystation": VS + "2248412/badge.jpg",
                    "nazwy_w_zwiazkach": ["TPS Bielsk Podlaski", "Towarzystwo Piłki Siatkowej Bielsk Podlaski"]},
    "lks-lodz":    {"skrot": "ŁKS AZS UMED Łódź", "herb": None, "kolor": "#B71C1C",
                    "herb_volleystation": VS + "2248414/badge.png",
                    "nazwy_w_zwiazkach": ["ŁKS AZS UMED Łódź"]},
    "kalisz":      {"skrot": "MKS Kalisz II", "herb": None, "kolor": "#E65100",
                    "herb_volleystation": VS + "2248416/badge.png",
                    "nazwy_w_zwiazkach": ["MKS Kalisz II", "Energa MKS Kalisz II"]},
    "krotka":      {"skrot": "MUKS Krótka", "herb": None, "kolor": "#4A148C",
                    "herb_volleystation": VS + "2248417/badge.png",
                    "nazwy_w_zwiazkach": ["MUKS Krótka", "MUKS Krótka Mysiadło"]},
    "barycz":      {"skrot": "Barycz Janków P.", "herb": None, "kolor": "#00695C",
                    "herb_volleystation": VS + "2248415/badge.jpeg",
                    "nazwy_w_zwiazkach": ["MAPEI BARYCZ Janków Przygodzki", "GLKS Barycz Janków Przygodzki"]},
    "lask":        {"skrot": "Łaskovia Łask", "herb": None, "kolor": "#283593",
                    "herb_volleystation": VS + "2248413/badge.png",
                    "nazwy_w_zwiazkach": ["SMS Ostrów Łaskovia Łask", "ŁMLKS Łaskovia Łask"]},
    "legionovia":  {"skrot": "Legionovia II", "herb": None, "kolor": "#AD1457",
                    "herb_volleystation": VS + "2248411/badge.png",
                    "nazwy_w_zwiazkach": ["PGE LTS Legionovia Legionowo II", "PGE LTS Legionovia Legionowo 2"]},
    "raszyn":      {"skrot": "Orlęta Raszyn", "herb": None, "kolor": "#2E7D32",
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
        "relacja": "wygrana-w-lodzi",
    },

    # B) turniej Akademii – PRZYKŁAD
    {
        "druzyna": "akademia", "data": "2026-11-08", "godzina": "10:00",
        "gospodarz": "Turniej Mini Volley U12", "gosc": None,
        "hala": "Hala Sportowa przy PSP nr 3 w Kobyłce",
    },
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
    {"druzyna": "seniorki", "numer": 7,  "imie": "Natalia",   "nazwisko": "Bielińska",       "pozycja": "Rozgrywająca", "zdjecie": None},
    {"druzyna": "seniorki", "numer": 20, "imie": "Zuzanna",   "nazwisko": "Kałkowska",       "pozycja": "Rozgrywająca", "zdjecie": None},
    # Atakujące
    {"druzyna": "seniorki", "numer": 14, "imie": "Nikola",    "nazwisko": "Gutowska",        "pozycja": "Atakująca",    "zdjecie": None},
    {"druzyna": "seniorki", "numer": 17, "imie": "Natalia",   "nazwisko": "Dąbrowska",       "pozycja": "Atakująca",    "zdjecie": None},
    # Przyjmujące
    {"druzyna": "seniorki", "numer": 2,  "imie": "Julia",     "nazwisko": "Grzelak",         "pozycja": "Przyjmująca",  "zdjecie": None},
    {"druzyna": "seniorki", "numer": 6,  "imie": "Kamila",    "nazwisko": "Wrzosek",         "pozycja": "Przyjmująca",  "zdjecie": None},
    {"druzyna": "seniorki", "numer": 10, "imie": "Kaja",      "nazwisko": "Klepacz",         "pozycja": "Przyjmująca",  "zdjecie": None},
    {"druzyna": "seniorki", "numer": 21, "imie": "Matylda",   "nazwisko": "Woźny",           "pozycja": "Przyjmująca",  "zdjecie": None},
    # Środkowe
    {"druzyna": "seniorki", "numer": 11, "imie": "Natalia",   "nazwisko": "Pietruszkiewicz", "pozycja": "Środkowa",     "zdjecie": None},
    {"druzyna": "seniorki", "numer": 12, "imie": "Wiktoria",  "nazwisko": "Sztylko",         "pozycja": "Środkowa",     "zdjecie": None},
    {"druzyna": "seniorki", "numer": 22, "imie": "Adrianna",  "nazwisko": "Sitarska",        "pozycja": "Środkowa",     "zdjecie": None},
    # Libero
    {"druzyna": "seniorki", "numer": 8,  "imie": "Klaudia",   "nazwisko": "Kucharska",       "pozycja": "Libero",       "zdjecie": None, "kapitan": True},
    {"druzyna": "seniorki", "numer": 23, "imie": "Małgorzata", "nazwisko": "Czajka",         "pozycja": "Libero",       "zdjecie": None},
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
        "adres": "wygrana-w-lodzi",
        "data": "2026-10-17",
        "kategoria": "Seniorki",          # Seniorki / Akademia / Klub
        "tytul": "Trzy punkty z Łodzi! Wygrywamy 3:1",
        "zajawka": "Pewne zwycięstwo na wyjeździe z ŁKS AZS UMED Łódź.",
        "zdjecie": None,
        "tresc": """
PRZYKŁAD – tu wpisz relację z meczu.

Drugi akapit relacji.
""",
    },
    {
        "adres": "nowa-grupa-mini-volley",
        "data": "2026-10-14",
        "kategoria": "Akademia",
        "tytul": "Nowa grupa Mini Volley od listopada",
        "zajawka": "Ruszają zapisy dzieci w wieku 7–9 lat.",
        "zdjecie": None,
        "tresc": """
PRZYKŁAD – opis nowej grupy.
""",
    },
    {
        "adres": "easy-wrap-sponsorem-tytularnym",
        "data": "2026-09-01",
        "kategoria": "Klub",
        "tytul": "Easy Wrap sponsorem tytularnym",
        "zajawka": "Kolejny sezon razem z naszym sponsorem tytularnym.",
        "zdjecie": None,
        "tresc": """
PRZYKŁAD – treść informacji.
""",
    },
]


# ---------------------------------------------------------------------
# 8. SPONSORZY  (poziom: "tytularny" / "strategiczny" / "partner")
#   prezentuje: nazwa sekcji, przy której pokaże się „prezentowane przez”:
#   "tabela", "kadra", "akademia", "terminarz" albo None
# ---------------------------------------------------------------------
SPONSORZY = {
    "easy-wrap": {"nazwa": "Easy Wrap", "poziom": "tytularny", "logo": None, "www": None, "prezentuje": None},
    "miasto":    {"nazwa": "Miasto Kobyłka", "poziom": "strategiczny", "logo": None, "www": None,
                  "prezentuje": "akademia"},                              # PRZYKŁAD
    "partner-1": {"nazwa": "Partner 1", "poziom": "partner", "logo": None, "www": None, "prezentuje": "tabela"},  # PRZYKŁAD
    "partner-2": {"nazwa": "Partner 2", "poziom": "partner", "logo": None, "www": None, "prezentuje": None},      # PRZYKŁAD
}

SPONSORZY_TEKST = ("Wspierasz lokalny sport? Pokaż swoją markę na meczach 2. ligi, "
                   "w mediach klubu i na koszulkach Akademii. Napisz do nas.")


# ---------------------------------------------------------------------
# 9. KALENDARIUM – wydarzenia (mecze i treningi dodają się same)
#   typ: "wydarzenie" (inne typy: mecze z MECZE i związku, treningi z AKADEMIA)
# ---------------------------------------------------------------------
WYDARZENIA = [
    {"data": "2026-11-11", "godzina": "12:00", "tytul": "Bieg Niepodległości z klubem", "miejsce": "Kobyłka"},  # PRZYKŁAD
    {"data": "2026-12-20", "godzina": "17:00", "tytul": "Wigilia klubowa", "miejsce": "Hala przy PSP nr 3"},   # PRZYKŁAD
]


# ---------------------------------------------------------------------
# 10. AKADEMIA SIATKÓWKI VOLLEY
# ---------------------------------------------------------------------
AKADEMIA = {
    "haslo": "Dołącz do nas!",
    "opis": "Treningi siatkówki dla dziewcząt i chłopców od 7 lat. Pierwszy trening za darmo.",
    "formularz_google": None,   # wklej link do formularza Google, np. "https://docs.google.com/forms/d/e/.../viewform"
    "zdjecie": None,            # zdjęcie do nagłówka, np. "akademia/hero.webp"
    "grupy": [                  # PRZYKŁAD
        {"nazwa": "Mini Volley", "wiek": "7–10 lat", "opis": "Zabawa z piłką, koordynacja i pierwsze odbicia."},
        {"nazwa": "Młodziczki",  "wiek": "11–13 lat", "opis": "Technika, gra 4×4 i pierwsze turnieje."},
        {"nazwa": "Kadetki",     "wiek": "14–16 lat", "opis": "Rozgrywki ligowe i przygotowanie do gry seniorskiej."},
    ],
    "trenerzy": [               # PRZYKŁAD
        {"imie": "Ewa", "nazwisko": "Nowak", "opis": "Trenerka II klasy, prowadzi grupy Mini Volley.", "zdjecie": None},
    ],
    # Harmonogram treningów – pojawi się też w kalendarium (w okresie sezonu)
    "sezon_od": "2026-09-01",
    "sezon_do": "2027-06-20",
    "dni_wolne": ["2026-11-11", "2026-12-24", "2026-12-25", "2026-12-26", "2026-12-31", "2027-01-01", "2027-01-06"],
    "harmonogram": [            # PRZYKŁAD
        {"grupa": "Mini Volley", "dzien": "poniedziałek", "od": "16:00", "do": "17:00", "hala": "Hala przy PSP nr 3"},
        {"grupa": "Młodziczki",  "dzien": "środa",        "od": "17:00", "do": "18:30", "hala": "Hala przy PSP nr 3"},
        {"grupa": "Kadetki",     "dzien": "czwartek",     "od": "18:30", "do": "20:00", "hala": "Hala przy PSP nr 3"},
    ],
    "ochrona_maloletnich": {
        "tekst": "Klub stosuje Standardy Ochrony Małoletnich. Każda osoba pracująca z dziećmi "
                 "ma aktualne zaświadczenie o niekaralności i jest sprawdzona w Rejestrze Sprawców "
                 "Przestępstw na Tle Seksualnym. Masz wątpliwości lub niepokoi Cię czyjeś zachowanie? "
                 "Napisz do osoby odpowiedzialnej za standardy.",
        "dokument": None,                         # np. "dokumenty/standardy-ochrony-maloletnich.pdf" (w folderze img/)
        "osoba_kontaktowa": "ks.volley.kobylka@gmail.com",
    },
}


# ---------------------------------------------------------------------
# 11. SKLEP (bez płatności – przycisk „Zamów” otwiera e-mail)
# ---------------------------------------------------------------------
SKLEP = {
    "jak_zamowic": "Napisz do nas z nazwą produktu i rozmiarem. Odbiór na meczu u siebie.",
    "formularz_google": None,
    "produkty": [               # PRZYKŁAD
        {"nazwa": "Koszulka kibica 2026/27", "cena": "89 zł", "rozmiary": "XS–XXL", "zdjecie": None, "dostepny": True},
        {"nazwa": "Szalik klubowy", "cena": "45 zł", "rozmiary": None, "zdjecie": None, "dostepny": True},
        {"nazwa": "Bluza z kapturem", "cena": "149 zł", "rozmiary": "S–XL", "zdjecie": None, "dostepny": False},
    ],
}


# ---------------------------------------------------------------------
# 12. GALERIA
#   Zdjęcia wrzuć do img/galeria/<folder>/ – strona sama je znajdzie.
# ---------------------------------------------------------------------
GALERIA = [
    {"tytul": "ŁKS AZS UMED Łódź – Easy Wrap Volley", "data": "2026-10-17", "folder": "2026-10-17-lodz"},  # PRZYKŁAD
]


# ---------------------------------------------------------------------
# 13. O KLUBIE
# ---------------------------------------------------------------------
O_KLUBIE = {
    "historia": """
PRZYKŁAD – historia klubu. Klub Sportowy Volley z Kobyłki szkoli dziewczęta i chłopców,
a pierwsza drużyna kobiet gra w 2. lidze pod nazwą Easy Wrap Volley Kobyłka.

Kolejny akapit historii.
""",
    "trofea": [                 # PRZYKŁAD – pasek trofeów
        {"rok": 2025, "opis": "Awans do 2. ligi"},
        {"rok": 2024, "opis": "Mistrzostwo 3. ligi"},
    ],
    "wartosci": ["Szacunek", "Ambicja", "Wspólnota"],
}


# ---------------------------------------------------------------------
# 14. KONTAKT
# ---------------------------------------------------------------------
KONTAKT = {
    "osoby": [                  # PRZYKŁAD
        {"rola": "Sprawy klubu i sponsorzy", "imie": None, "email": "ks.volley.kobylka@gmail.com"},
        {"rola": "Zapisy do Akademii", "imie": None, "email": "ks.volley.kobylka@gmail.com"},
    ],
    "formularz_google": None,
}
