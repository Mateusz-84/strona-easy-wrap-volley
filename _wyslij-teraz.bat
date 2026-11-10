@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Terminarz w telefonie - subskrypcja kalendarza" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
