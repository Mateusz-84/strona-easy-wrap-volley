@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "SEO, statystyki, wynik na zywo, grafiki wynikow, strona dla sponsorow, poprawki jakosci" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
