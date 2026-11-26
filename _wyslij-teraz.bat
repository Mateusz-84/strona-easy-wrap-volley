@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Akademia: ujednolicone zdanie o umowie po treningu probnym" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
