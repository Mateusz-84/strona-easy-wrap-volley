@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Rywale: tylko linki Volleybox (bez stron klubow)" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
