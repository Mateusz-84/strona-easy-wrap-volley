@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Strona wyboru: plansze odslaniaja od razu wybrana strone" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
