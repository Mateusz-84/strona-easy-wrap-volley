@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Profile Volleybox druzyn, nasza nazwa: FB / IG na telefonie" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
