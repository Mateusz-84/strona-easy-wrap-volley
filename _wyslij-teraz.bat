@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "SEO: siatkowka dla dzieci Kobylka (strona glowna, Akademia, O klubie)" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
