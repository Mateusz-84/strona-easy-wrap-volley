# =====================================================================
#  USTAW-SEKRETY-FTP.PS1 – wpisanie danych serwera FTP do GitHuba
# ---------------------------------------------------------------------
#  Uruchom w terminalu:   .\ustaw-sekrety-ftp.ps1
#  Przy każdym pytaniu wklej wartość (Ctrl+V) i naciśnij Enter.
#  Wpisywany tekst jest niewidoczny – to normalne.
#  Wartości trafiają WYŁĄCZNIE do zaszyfrowanych sekretów repozytorium
#  na GitHubie. Nie są zapisywane na dysku ani w żadnym pliku.
#  Dane dostaniesz od firmy hostingowej (panel hostingu → FTP).
# =====================================================================

$repo = "Mateusz-84/strona-easy-wrap-volley"
$gh = "C:\Program Files\GitHub CLI\gh.exe"

Write-Host ""
Write-Host "1/4  Adres serwera FTP, np. ftp.twojhosting.pl" -ForegroundColor Yellow
& $gh secret set FTP_SERWER --repo $repo

Write-Host ""
Write-Host "2/4  Nazwa użytkownika FTP" -ForegroundColor Yellow
& $gh secret set FTP_UZYTKOWNIK --repo $repo

Write-Host ""
Write-Host "3/4  Hasło FTP (nie będzie widoczne podczas wpisywania)" -ForegroundColor Yellow
& $gh secret set FTP_HASLO --repo $repo

Write-Host ""
Write-Host "4/4  Folder strony na serwerze, np. public_html/ (z ukośnikiem na końcu)" -ForegroundColor Yellow
& $gh secret set FTP_FOLDER --repo $repo

Write-Host ""
Write-Host "Gotowe. Zapisane sekrety:" -ForegroundColor Green
& $gh secret list --repo $repo
