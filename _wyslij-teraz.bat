@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Ukryty dubel posta FORTIS GO MVP MECZU (lista ukryj w content.py)" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
