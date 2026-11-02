@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Plansza meczu: Zaprasza + numer i nazwisko zawodniczki" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
