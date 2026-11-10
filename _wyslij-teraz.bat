@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Karta Zapraszam pod zdjeciem zawodniczki (telefon)" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
