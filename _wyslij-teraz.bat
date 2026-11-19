@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "SEO: Siatkowka w Kobylce dla dzieci - jednolite haslo w tytulach i opisach" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
