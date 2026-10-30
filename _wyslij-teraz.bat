@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Strona glowna: nizsza plansza meczu, aktualnosci zaraz pod nia" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
