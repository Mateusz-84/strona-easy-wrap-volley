@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wyslij-na-github.ps1" -Opis "Wydajnosc i SEO: herby i grafiki WebP, wymiary obrazkow, lastmod w mapie, tytul strony glownej, dane strukturalne, sklejone napisy, literowki" -BezPauzy > "%~dp0strona\ostatnie-wysylanie.txt" 2>&1
