@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Nowe zdjecie Natalii Bielinskiej" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
