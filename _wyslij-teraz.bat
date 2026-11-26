@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Poprawka sklejonego adresu z linkiem w kartach meczow" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
