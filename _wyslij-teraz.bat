@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Zdjecia: wersja w adresie (nowe zdjecia od razu widoczne), przygotowanie Poznaj nas" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
