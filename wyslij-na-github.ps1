# =====================================================================
#  WYSLIJ-NA-GITHUB.PS1 – wysłanie zmian strony na GitHuba jednym kliknięciem
# ---------------------------------------------------------------------
#  Najprościej: kliknij dwa razy plik „WYSLIJ NA GITHUB.bat” w tym folderze.
#  (albo w terminalu:  .\wyslij-na-github.ps1 )
#
#  Co robi skrypt:
#   1. pokazuje, które pliki zmieniłeś,
#   2. pyta o krótki opis zmian (Enter = opis z datą),
#   3. zapisuje zmiany (commit),
#   4. pobiera to, co w międzyczasie zapisał GitHub (nowe dane ze związków),
#   5. wysyła Twoje zmiany na GitHuba,
#   6. otwiera stronę „Actions”, gdzie widać budowanie i publikację strony.
#  Po zielonym ptaszku w „Actions” (1–2 min) nowa wersja jest w internecie.
# =====================================================================

param(
    [string]$Opis = "",          # opis zmian podany z góry (wtedy skrypt nie pyta)
    [switch]$BezPauzy            # nie czekaj na Enter na końcu
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
Set-Location -LiteralPath $PSScriptRoot

$adresActions = "https://github.com/Mateusz-84/strona-easy-wrap-volley/actions"

function Koniec([int]$kod) {
    if (-not $BezPauzy) { Write-Host ""; Read-Host "Naciśnij Enter, aby zamknąć" | Out-Null }
    exit $kod
}

function Blad([string]$tekst) {
    Write-Host ""
    Write-Host "BŁĄD: $tekst" -ForegroundColor Red
    Koniec 1
}

Write-Host ""
Write-Host "=== Wysyłanie strony Easy Wrap Volley na GitHuba ===" -ForegroundColor Cyan
Write-Host ""

# --- 0. Czy jest Git? -------------------------------------------------
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Blad "Nie znaleziono programu Git. Zainstaluj go ze strony https://git-scm.com i uruchom skrypt ponownie."
}
git rev-parse --is-inside-work-tree *> $null
if ($LASTEXITCODE -ne 0) { Blad "Ten folder nie jest repozytorium Git. Skrypt musi leżeć w folderze strony." }

# Gdyby wcześniej coś zostało w połowie (przerwane pobieranie zmian), posprzątaj
if ((Test-Path ".git/rebase-merge") -or (Test-Path ".git/rebase-apply")) {
    Write-Host "Kończę przerwaną wcześniej operację…" -ForegroundColor Yellow
    git rebase --abort *> $null
}

# --- 1. Co się zmieniło? ----------------------------------------------
$zmiany = git status --porcelain
if ($zmiany) {
    Write-Host "Zmienione pliki:" -ForegroundColor Yellow
    git status --short
    Write-Host ""

    # --- 2. Opis zmian -------------------------------------------------
    if (-not $Opis) {
        $Opis = Read-Host "Krótki opis zmian (Enter = opis automatyczny)"
    }
    if (-not $Opis.Trim()) {
        $Opis = "Zmiany na stronie " + (Get-Date -Format "yyyy-MM-dd HH:mm")
    }

    # --- 3. Zapisanie zmian (commit) ----------------------------------
    git add -A
    git commit -q -m $Opis
    if ($LASTEXITCODE -ne 0) { Blad "Nie udało się zapisać zmian (commit)." }
    Write-Host "Zapisano zmiany: $Opis" -ForegroundColor Green
} else {
    Write-Host "Brak nowych zmian w plikach – sprawdzam, czy coś czeka na wysłanie." -ForegroundColor Yellow
}

# --- 4. Pobranie zmian z GitHuba (dane ze związków zapisane przez automat)
Write-Host ""
Write-Host "Pobieram najnowszą wersję z GitHuba…"
git pull --rebase -q origin main
if ($LASTEXITCODE -ne 0) {
    git rebase --abort *> $null
    Blad ("Twoje zmiany kolidują z wersją na GitHubie (ten sam fragment pliku zmieniony w dwóch miejscach). " +
          "Twoje zmiany są bezpieczne, zapisane lokalnie. Poproś Claude o pomoc albo napisz, który plik zmieniałeś.")
}

# --- 5. Czy jest co wysłać? -------------------------------------------
$doWyslania = [int](git rev-list --count "origin/main..HEAD")
if ($doWyslania -eq 0) {
    Write-Host ""
    Write-Host "Wszystko jest już na GitHubie – nie ma czego wysyłać." -ForegroundColor Green
    Koniec 0
}

# --- 6. Wysłanie ------------------------------------------------------
Write-Host "Wysyłam na GitHuba ($doWyslania zapis(y))…"
git push -q origin HEAD:main
if ($LASTEXITCODE -ne 0) {
    Blad ("Nie udało się wysłać zmian. Sprawdź internet. Jeśli pojawiło się okno logowania do GitHuba – " +
          "zaloguj się i uruchom skrypt jeszcze raz.")
}

Write-Host ""
Write-Host "GOTOWE! Zmiany są na GitHubie." -ForegroundColor Green
Write-Host "Za 1–2 minuty strona przebuduje się sama. Postęp widać w zakładce Actions:"
Write-Host $adresActions -ForegroundColor Cyan
if (-not $BezPauzy) { Start-Process $adresActions }
Koniec 0
