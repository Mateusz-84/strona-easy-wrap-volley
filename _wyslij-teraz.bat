@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Aktualnosci z FB 9 razy na dobe" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
