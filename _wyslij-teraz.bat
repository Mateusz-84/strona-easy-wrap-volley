@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Akademia: poprawki tekstow i skladni, darmowy trening probny po wczesniejszym zapisie" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
