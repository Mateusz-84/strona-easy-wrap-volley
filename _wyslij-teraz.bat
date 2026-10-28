@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Favicon klubu i nowe wyciecia zdjec zawodniczek" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
