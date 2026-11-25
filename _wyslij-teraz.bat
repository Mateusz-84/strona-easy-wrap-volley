@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Akademia: w formularzu rok urodzenia coreczki zamiast klasy" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
