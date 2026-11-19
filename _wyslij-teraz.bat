@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Licznik wejsc: jedna wizyta liczona raz, licznik sie nie cofa; link do Map Google i wspolrzedne hali" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
