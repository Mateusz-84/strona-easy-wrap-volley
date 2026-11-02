@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Ochrona adresow e-mail przed botami" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
