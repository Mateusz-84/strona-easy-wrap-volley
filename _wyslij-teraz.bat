@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Nazwy druzyn linkuja do Volleybox, bez innych odnosnikow" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
