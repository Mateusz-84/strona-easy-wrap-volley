@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Linki do stron klubow rywali w tabeli i terminarzu" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
