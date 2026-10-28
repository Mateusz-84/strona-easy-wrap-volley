@echo off
rem Wysyla zmiany na GitHuba bez pytan (opis automatyczny). Mozna usunac.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Aktualnosci z Facebooka (druzyna i Akademia), RODO" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
