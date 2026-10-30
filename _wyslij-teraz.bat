@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Animacja wejscia: elementy planszy pojawiaja sie po kolei" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
