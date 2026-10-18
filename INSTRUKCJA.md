# Strona Easy Wrap Volley Kobyłka – instrukcja obsługi

Ta instrukcja jest dla osoby, która prowadzi stronę, ale nie jest programistą.
Na co dzień edytujesz **jeden plik: `content.py`**.

---

## 1. Jak to działa

```
 strony związków (WSMWZPS, PZPS)          content.py (Twoje treści)
              │                                    │
              └──────────► build.py ◄──────────────┘
                              │
                        folder strona/  ──► serwer FTP (Twoja strona w internecie)
```

- **Terminarz i godziny meczów** pobierają się same z WSMWZPS
  (`obsady.wsmwzps.pl`). Wyjazdów poza Mazowsze tam nie ma, więc te mecze
  dociągane są z listy meczów PZPS.
- **Tabela 2. ligi kobiet (grupa 2), wyniki i sety** pobierają się same z PZPS
  (`sedziowie.pzps.pl`).
- **Hala i adres** najbliższych meczów pobierają się z PZPS.
- Robi to **GitHub Actions** – automatycznie co 2 godziny, po każdej Twojej
  zmianie oraz na żądanie. Zbudowana strona sama trafia na serwer FTP.
- Jeśli strona związku nie działa albo zmieni wygląd, używana jest **ostatnia
  dobra kopia** danych (`dane/kopia_zwiazkowa.json`). Strona klubu nigdy nie
  zostanie pusta.
- Godzina typu **17:33** to w systemie obsad znak „godzina jeszcze
  nieustalona”. Strona pokazuje wtedy „godzina wkrótce”, a licznik w belce
  liczy dni.

### Pliki projektu

| Plik / folder | Co to jest | Czy ruszać? |
|---|---|---|
| `content.py` | wszystkie treści: kadra, newsy, sponsorzy, Akademia… | **TAK** |
| `img/` | zdjęcia, herby, logotypy | **TAK** (wrzucasz pliki) |
| `zasoby/style.css` | kolory i wygląd | rzadko (np. kolor żółty) |
| `szablony.py` | wygląd elementów (HTML) | raczej nie |
| `build.py` | składa stronę | nie |
| `zrodla.py` | pobiera dane ze związków | nie |
| `dane/kopia_zwiazkowa.json` | ostatnia kopia danych ze związków | nie (aktualizuje się sam) |
| `strona/` | gotowa strona – to wgrywa się na FTP | nie (powstaje sam) |

---

## 2. Pierwsze uruchomienie (jednorazowo)

### 2.1. Repozytorium na GitHubie
1. Załóż konto na <https://github.com> (najlepiej klubowe, na adres klubu).
2. Kliknij **New repository** → nazwa np. `strona-klubu` → wybierz **Private** → **Create**.
3. Na stronie repozytorium kliknij **uploading an existing file** i przeciągnij
   **całą zawartość** folderu projektu (razem z folderami `.github`, `dane`,
   `img`, `zasoby`). Kliknij **Commit changes**.
   > Folder `.github` bywa ukryty w Windows. W Eksploratorze: Widok → Pokaż →
   > Ukryte elementy. Wygodniej jest użyć programu **GitHub Desktop**.

### 2.2. Dane do serwera FTP
W repozytorium: **Settings → Secrets and variables → Actions → New repository secret**.
Dodaj cztery sekrety (dane dostaniesz od firmy hostingowej):

| Nazwa | Przykład |
|---|---|
| `FTP_SERWER` | `ftp.twojhosting.pl` |
| `FTP_UZYTKOWNIK` | `klub@twojhosting.pl` |
| `FTP_HASLO` | hasło do FTP |
| `FTP_FOLDER` | `public_html/` (folder strony na serwerze, **z ukośnikiem na końcu**) |

Domyślnie strona wgrywa się szyfrowanym połączeniem **FTPS**. Jeśli serwer go
nie obsługuje (błąd połączenia w Actions), dodaj na tej samej stronie w zakładce
**Variables** zmienną `FTP_PROTOKOL` o wartości `ftp`.

### 2.3. Pierwsze wgranie
Zakładka **Actions** → **Aktualizacja strony** → **Run workflow**.
Po ok. minucie zielony znaczek ✓ = strona jest na serwerze.
Czerwony ✗ → kliknij w niego i przeczytaj, który krok się nie udał (zwykle złe dane FTP).

> **Ważne:** GitHub wyłącza automatyczne uruchomienia, gdy w repozytorium przez
> 60 dni nic się nie dzieje. W sezonie to nie grozi (kopia danych zapisuje się
> po każdej zmianie u związków). Po przerwie letniej sprawdź zakładkę Actions
> i w razie potrzeby kliknij **Enable workflow**.

---

## 3. Edycja treści – najprościej przez przeglądarkę

1. Otwórz repozytorium na github.com → kliknij `content.py` → ikonka ołówka ✏️.
2. Zmień, co trzeba (zasady poniżej).
3. Kliknij **Commit changes**.
4. Po ok. minucie strona w internecie jest zaktualizowana.

**Zasady pisania w `content.py`:**
- tekst zawsze w cudzysłowie: `"Anna"`,
- każdy element listy kończy się przecinkiem `},`,
- data: `"2026-10-24"`, godzina: `"18:00"`,
- brak wartości: `None` (bez cudzysłowu).

Jeśli coś zepsujesz (np. zgubisz cudzysłów), Actions pokaże czerwony ✗
i **stara strona zostanie na serwerze bez zmian**. Popraw błąd i zapisz jeszcze raz.

---

## 4. Jak dodać mecz

### Mecz ligowy (2. liga)
**Nic nie robisz** – pojawi się sam ze strony związku.

Chcesz dodać sponsora meczu, zdjęcie na plakat, MVP albo link do transmisji?
Dopisz w `MECZE` wpis z **datą tego meczu**:

```python
{
    "druzyna": "seniorki", "data": "2026-11-07",
    "sponsor_meczu": "easy-wrap",                      # klucz z SPONSORZY
    "zdjecie_plakatu": "plakaty/anna-nowak.webp",      # plik w img/plakaty/
    "transmisja": "https://youtube.com/@ks_Volley",
},
```

Wpisana tu godzina (`"godzina": "18:00"`) ma pierwszeństwo przed związkiem.
Przydaje się, gdy znasz godzinę wcześniej niż system obsad.

### Sparing, turniej Akademii (mecz spoza związku)
```python
{
    "druzyna": "akademia", "data": "2026-11-08", "godzina": "10:00",
    "gospodarz": "Turniej Mini Volley U12", "gosc": None,
    "hala": "Hala Sportowa przy PSP nr 3 w Kobyłce",
},
```
Sparing z rywalem: `"gospodarz": "Easy Wrap Volley Kobyłka", "gosc": "UKS Przykład"`.

### Nowy rywal (np. po zmianie grupy)
Dopisz go w `RYWALE` ze wszystkimi wersjami nazwy (WSMWZPS i PZPS potrafią
nazywać ten sam klub inaczej):
```python
"przyklad": {"skrot": "UKS Przykład", "herb": None, "kolor": "#C8102E",
             "herb_volleystation": VS + "2248999/badge.png",
             "nazwy_w_zwiazkach": ["UKS Przykład Warszawa", "Przykład Warszawa"]},
```

**Herb z VolleyStation:** otwórz <https://2ligakobiet.volleystation.com/pl/schedule/>,
kliknij prawym przyciskiem logo drużyny → **Kopiuj adres obrazu**. Wklej ten
adres w `"herb_volleystation"` (cały adres w cudzysłowie albo, jak wyżej, sam
koniec po `VS +`).
Przy najbliższym budowaniu logo **pobierze się raz** i zapisze w `img/herby/`
jako mały plik (240 px). Potem strona nie odpytuje już VolleyStation.

- Chcesz odświeżyć logo (klub zmienił herb)? Usuń jego plik z `img/herby/`.
  Przy następnym budowaniu pobierze się na nowo.
- Własny plik herbu ma pierwszeństwo: wrzuć go do `img/herby/` i wpisz
  `"herb": "herby/przyklad.webp"`.
- Bez herbu pojawi się tarcza z inicjałami w kolorze `"kolor"`.

Uwaga: do pobierania samych logo służy osobny serwer `assets.volleystation.com`.
Strona terminarza VolleyStation blokuje automatyczne programy, więc terminarz
i wyniki dalej pobieramy ze związków.

---

## 5. Jak wpisać wynik

- **Mecz ligowy** – nic nie robisz. Wynik i sety pojawią się same, gdy związek
  je opublikuje (zwykle tego samego wieczoru).
- **MVP i relacja** – w `MECZE` przy dacie meczu:
  `"mvp": "Anna Nowak", "relacja": "wygrana-w-lodzi"` (adres newsa).
- **Mecz spoza związku** – dopisz do jego wpisu:
  `"wynik": "3:1", "sety": ["25:21", "23:25", "25:19", "25:22"]`
  (zawsze **gospodarz : gość**, tak jak na stronach związku).

Belka na górze strony sama przełącza się z licznika na wynik i z powrotem na
kolejny mecz.

---

## 6. Jak dodać zawodniczkę

W `KADRA` dopisz:
```python
{"druzyna": "seniorki", "numer": 18, "imie": "Ola", "nazwisko": "Nowicka",
 "pozycja": "Środkowa", "urodzona": "2005-02-14", "w_klubie_od": 2026, "wzrost": 185,
 "zdjecie": None},
```
- `pozycja`: Rozgrywająca / Atakująca / Przyjmująca / Środkowa / Libero.
- `urodzona`: `None`, jeśli zawodniczka nie chce podawać daty.
- `zdjecie`: najlepiej **wycięta postać na przezroczystym tle** (WebP lub PNG,
  ok. 800×1000 px) w `img/zawodniczki/`, np. `"zawodniczki/ola-nowicka.webp"`.
  Bez zdjęcia pojawi się karta z numerem i inicjałami w barwach klubu.
- Kapitan: dopisz `"kapitan": True`.
- Odejście z klubu: usuń cały wpis (od `{` do `},`).
- Pisownię imion i nazwisk porównuj ze stroną drużyny na VolleyStation
  (<https://2ligakobiet.volleystation.com/pl/teams/2103883-EASYW/>).
  Skład trzeba przepisać ręcznie, bo VolleyStation blokuje automatyczne
  pobieranie. Pozycji z VolleyStation nie przepisuj: obecnie wszystkie
  zawodniczki mają tam błędnie pozycję „przyjmująca”.

---

## 7. Jak dodać news

Na początku listy `NEWSY` dopisz:
```python
{
    "adres": "wygrana-z-kaliszem",       # bez polskich znaków i spacji
    "data": "2026-10-24",
    "kategoria": "Seniorki",             # Seniorki / Akademia / Klub
    "tytul": "Wygrywamy z Kaliszem!",
    "zajawka": "Jedno zdanie, które zachęci do czytania.",
    "zdjecie": "newsy/kalisz.webp",      # albo None
    "tresc": """
Pierwszy akapit.

Drugi akapit – pusta linia oznacza nowy akapit.
""",
},
```
News pojawi się pod adresem `aktualnosci/wygrana-z-kaliszem.html`.
Strona sama układa newsy od najnowszego.

---

## 8. Zdjęcia

- Format **WebP** (najlżejszy). Zamiana z JPG: <https://squoosh.app> (jakość 75–80).
- Szerokość: newsy i galeria ok. **1600 px**, kadra ok. **800 px**.
- Galeria: utwórz folder `img/galeria/2026-10-24-kalisz/`, wrzuć zdjęcia
  i dopisz album w `GALERIA`. Strona sama znajdzie wszystkie zdjęcia z folderu.
- **Zdjęcia w nagłówkach stron** wystarczy wrzucić do `img/naglowki/` pod
  nazwami z `ZDJECIA_NAGLOWKOW` w `content.py`. Pojawią się same:

  | Plik | Gdzie się pokaże |
  |---|---|
  | `plakat-meczu.webp` | plakat najbliższego meczu na stronie głównej |
  | `terminarz.webp`, `druzyny.webp`, `aktualnosci.webp`, `galeria.webp`, `sponsorzy.webp`, `o-klubie.webp`, `sklep.webp`, `kontakt.webp` | nagłówek danej podstrony |

  Najlepsze są **poziome** zdjęcia ok. 1600×1000 px. Tekst leży na lewej
  części i dole zdjęcia (pod przyciemnieniem), więc ważne rzeczy, np. twarze,
  najlepiej mieć po prawej. Bez pliku nagłówek jest po prostu granatowy.
- Plakat konkretnego meczu: w `MECZE` przy dacie meczu wpisz
  `"zdjecie_plakatu": "plakaty/kalisz.webp"`. Ma pierwszeństwo przed
  `plakat-meczu.webp`.
- Zdjęcie newsa (`"zdjecie"` w `NEWSY`) jest tłem nagłówka artykułu.
- Zdjęcia dzieci publikuj tylko za zgodą rodziców.

---

## 9. Inne rzeczy w `content.py`

- **Formularz zapisu do Akademii:** utwórz formularz w Google Forms →
  Wyślij → ikona łańcucha → skopiuj link → wklej w `AKADEMIA["formularz_google"]`.
- **Sponsor** – dopisz w `SPONSORZY`, logo (SVG/PNG/WebP) wrzuć do
  `img/sponsorzy/`. `"prezentuje": "tabela"` doda napis
  „Prezentowane przez…” przy tabeli (działa też `"kadra"`, `"akademia"`, `"terminarz"`).
- **Treningi Akademii** – `AKADEMIA["harmonogram"]`. Pojawiają się też
  w kalendarium. Dni bez treningów (święta) wpisz w `dni_wolne`.
- **Wydarzenia klubowe** – `WYDARZENIA` (pojawiają się w kalendarium).

---

## 9a. Zdjęcia z Instagrama / Facebooka

Strona sama bierze zdjęcia z postów klubu.

**Zapowiedź meczu.** Plakat (taki jak grafika „MECZ WYJAZDOWY” klubu) pokazuje
się na **3 sekundy** po wejściu na stronę główną, raz na wizytę. Można go
zamknąć krzyżykiem, kliknięciem albo klawiszem Esc. Strona sama znajduje post
z plakatem **najbliższego meczu**. Post musi:
- mieć zdjęcie,
- ukazać się w ciągu 7 dni przed meczem i przed jego godziną,
- mieć w opisie **nazwę lub miasto rywala** (np. „Łódź”, „ŁKS”, „Kalisz”;
  odmiana też się liczy, np. „do Łodzi”) **albo datę meczu** (np. „24.10”)
  **albo słowo „zapowiedź”**.

Posty z wynikiem (np. „3:1”, „wygrana”) i zwykłe posty z samym hashtagiem
klubu (`#100LatSportuWkobylce`), np. z treningu, nie są brane pod uwagę.
**Jeśli plakat się nie pojawia, dopisz w opisie posta nazwę rywala albo słowo
„Zapowiedź”.**

**Zdjęcie wygranej.** Post z hashtagiem `#wygrana` (albo `#wynik`,
`#zwyciestwo`), opublikowany w dniu meczu lub do 3 dni po nim, daje zdjęcie,
które pojawia się jako **znak wodny w tle karty wygranego meczu**.

Ustawienia (czas wyświetlania, słowa, hashtagi) zmienisz w `content.py`,
w sekcjach `ZAPOWIEDZ` i `ZDJECIA_WYGRANYCH`.

### Bez podłączania Meta (ręcznie)
- **Zapowiedź:** wrzuć plakat do `img/zapowiedz/` i wpisz w `content.py`:
  `"plik_reczny": "zapowiedz/kalisz.webp"`. Po meczu zmień z powrotem na `None`.
- **Zdjęcie wygranej:** wrzuć zdjęcie do `img/wyniki/` z nazwą
  `<drużyna>-<data meczu>`, np. `img/wyniki/seniorki-2026-10-24.webp`.
  Pojawi się samo na karcie tego meczu (tylko jeśli mecz był wygrany).

### Podłączenie Instagrama lub Facebooka (jednorazowo)
Instagram i Facebook nie pozwalają pobierać postów zwykłym programem.
Potrzebny jest **token** z oficjalnego API Meta. Robi to osoba, która
administruje stroną klubu na Facebooku.

1. Konto Instagram klubu musi być **firmowe lub twórcy** i połączone ze stroną
   klubu na Facebooku (Instagram → Ustawienia → Typ konta).
2. Wejdź na <https://developers.facebook.com>, kliknij **Moje aplikacje →
   Utwórz aplikację** i wybierz typ **Firmowa**.
3. Otwórz **Narzędzia → Graph API Explorer**. Wybierz swoją aplikację, kliknij
   **Generate Access Token** i zaznacz uprawnienia: `pages_show_list`,
   `pages_read_engagement` oraz dla Instagrama `instagram_basic`.
4. W **Access Token Debugger** kliknij **Extend Access Token**. To token
   długoterminowy.
5. W Graph API Explorer wklej ten token i wpisz zapytanie `me/accounts`.
   Przy stronie klubu zobaczysz `access_token` (to **token strony**, który nie
   wygasa) oraz `id` (to **ID strony FB**).
6. Dla Instagrama wpisz zapytanie `<ID strony>?fields=instagram_business_account`.
   Zwrócone `id` to **ID konta IG**.
7. Na GitHubie: **Settings → Secrets and variables → Actions → New repository
   secret**. Nazwa: `META_TOKEN`, wartość: token strony z punktu 5.
8. W `content.py`, w sekcji `META`, wpisz `"instagram_id"` albo `"facebook_id"`
   i ustaw `"zrodlo"`.

> **Tokenu nigdy nie wpisuj do `content.py`.** Ten plik widzi każdy, kto ma
> dostęp do repozytorium. Token trzymaj tylko w sekretach GitHuba.

Wygląd paneli Meta zmienia się co jakiś czas. Jeśli któregoś przycisku nie ma,
szukaj nazw uprawnień podanych wyżej.

Pobrane zdjęcia zapisują się w `img/zapowiedz/` i `img/wyniki/` i zostają
w repozytorium. Gdy API Meta nie odpowiada, strona używa ostatnio zapisanych.

---

## 10. Podgląd na własnym komputerze (opcjonalnie)

1. Zainstaluj Pythona **3.12 lub nowszego** z <https://www.python.org/downloads/>.
   Przy instalacji zaznacz **„Add python.exe to PATH”**.
2. W folderze projektu kliknij w pasek adresu Eksploratora, wpisz `cmd` i Enter.
3. Wpisz polecenie:
   ```bash
   python build.py
   ```
4. Otwórz plik `strona/index.html` w przeglądarce.

Jeśli będziesz pobierać nowe herby na swoim komputerze, zainstaluj raz
bibliotekę do zmniejszania obrazków poleceniem `pip install pillow`. Bez niej
herb zapisze się w pełnym, dużym rozmiarze. Na GitHubie Pillow instaluje się sam.

Bez internetu (z ostatnią kopią danych): `python build.py --bez-internetu`.
Sam test pobierania ze związków: `python zrodla.py`.

---

## 11. Ręczne wgranie przez FTP (gdyby GitHub nie działał)

1. Zbuduj stronę na komputerze (punkt 10).
2. Zainstaluj **FileZilla** (<https://filezilla-project.org>).
3. Połącz się: serwer, użytkownik, hasło od hostingu.
4. Po prawej wejdź do folderu strony (zwykle `public_html`).
5. Po lewej otwórz folder `strona` i przeciągnij **całą jego zawartość**
   (nie sam folder) na prawą stronę. Zgódź się na nadpisanie.

---

## 12. Gdy coś nie działa

| Objaw | Co zrobić |
|---|---|
| Czerwony ✗ w Actions, krok „Zbuduj stronę” | Błąd w `content.py` – komunikat pokazuje numer linii. Najczęściej brak przecinka lub cudzysłowu. |
| Czerwony ✗, krok „Wgraj na serwer FTP” | Sprawdź sekrety FTP (punkt 2.2) albo ustaw `FTP_PROTOKOL` = `ftp`. |
| W logu „UWAGA: … używam ostatniej kopii” | Strona związku nie odpowiadała albo zmieniła wygląd. Strona klubu działa na starych danych. Jeśli trwa to kilka dni, trzeba poprawić `zrodla.py`. |
| Rywal ma długą nazwę zamiast skrótu | Dopisz nową wersję nazwy w `RYWALE` → `nazwy_w_zwiazkach`. |
| Nowy sezon / inna liga lub grupa | Zmień adresy i nazwę grupy w `ZRODLA_ZWIAZKOWE` oraz `DRUZYNY["seniorki"]["liga"]`. |

---

## 13. Do uzupełnienia przed startem

- [ ] Kolor żółty z księgi znaku → `zasoby/style.css`, linia `--zolty:` (teraz tymczasowy `#FFC72C`).
- [ ] Herb klubu w wysokiej jakości z księgi znaku → `img/herby/easy-wrap-volley.svg`. Do tego czasu używany jest herb pobrany z VolleyStation (`img/herby/easy-wrap-volley.png`).
- [x] Kadra seniorek 2026/27 (13 zawodniczek, kapitan: Klaudia Kucharska).
- [ ] Sztab szkoleniowy seniorek → `SZTAB` w `content.py`.
- [ ] Opcjonalnie przy zawodniczkach: zdjęcia, data urodzenia, „w klubie od”, wzrost.
- [ ] Wszystko oznaczone w `content.py` jako **PRZYKŁAD**: newsy, sponsorzy, Akademia, sklep, historia.
- [ ] Link do formularza Google Akademii.
- [ ] Dokument „Standardy Ochrony Małoletnich” (PDF) → `img/dokumenty/` i wpis w `AKADEMIA`.
- [ ] Sprawdzenie polityki prywatności przez osobę znającą RODO.
- [ ] Zdjęcia do nagłówków → `img/naglowki/` (punkt 8), przede wszystkim `plakat-meczu.webp`.
- [ ] Opcjonalnie: token Meta (`META_TOKEN`) i ID konta IG/FB – zapowiedzi i zdjęcia wygranych z postów (punkt 9a).
- [x] Herby rywali z grupy 2 – pobrane z VolleyStation (`img/herby/`).
