@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Nasza nazwa: FB na komputerze, IG na telefonie" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
