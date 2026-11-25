@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Akademia: formularz zapisu na trening probny na stronie, nowe sekcje i CTA, FAQ, strony lokalne Kobylka Wolomin Marki Zielonka" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
