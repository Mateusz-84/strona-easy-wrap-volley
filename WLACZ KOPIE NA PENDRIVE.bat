@echo off
rem Jednorazowe ustawienie automatycznej kopii strony na pendrive KINGSTON (E:)
rem Dla innego pendrive: zmien litere E: ponizej
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0kopia-pendrive.ps1" -Ustaw -Dysk E: > "%~dp0strona\ustawienie-kopii.txt" 2>&1
