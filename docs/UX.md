# Kierunek UX i dobór komponentów

Stan: projekt interfejsu, 2026-11-07. Nie ma jeszcze działającego GUI
ani pomiarów. Poniższy wybór ogranicza zakres zależności, a nie dowodzi
osiągnięcia budżetów wydajności.

## Układ i wygląd

Natywne Qt Widgets, spokojny wygląd: grafitowe lub jasne tło, jeden akcent
turkusowy, bursztynowe ostrzeżenie o końcu punktu. Czerwień dla przekroczenia,
błędu i stanu nagrywania, zawsze z opisem/ikoną, nigdy wyłącznie kolorem.
Systemowe fonty, duże cyfry o stałej szerokości i wygodne odstępy.
Jasny/ciemny/systemowy motyw przełączany na żywo. Standardowa ramka okna
zachowuje systemowe przeciąganie, skalowanie i minimalizację.

```text
PANEL PROWADZĄCEGO
┌──────────────────────┬──────────────────────────────────┐
│ Agenda               │ Wybrany punkt do podglądu/edycji │
│ 1. Wprowadzenie      │ Notatki | Decyzje | Zadania       │
│ 2. Wyniki  ← trwa    │                                  │
│ 3. Następne kroki    │ Treść notatek...                 │
├──────────────────────┴──────────────────────────────────┤
│ Poprzedni  Pauza  Następny  +1 min  +5 min   08:42      │
│ Koniec 10:32 · opóźnienie 2 min                         │
│ ▸ Nagrywanie i transkrypcja    Pokaż licznik   Eksport   │
└─────────────────────────────────────────────────────────┘

LICZNIK DO UDOSTĘPNIANIA
┌────────────────────────────────────┐
│ 2 / 3 · Omówienie wyników           │
│               08:42                │
│ ━━━━━━━━━━━━━━━━━━━─────────────── │
│ Dalej: Następne kroki              │
│ Pauza  +1 min  Przypnij  Schowaj    │
└────────────────────────────────────┘
```

Wąski panel prowadzącego przechodzi na zakładki zamiast ściskać edytor.
Tryb kompaktowy licznika zostawia tytuł, czas i niezbędne akcje.
Ikony mają podpisy lub podpowiedzi; najważniejsze akcje są dostępne z klawiatury.
Brak zbędnych animacji, wykresów i stale rysowanej wizualizacji dźwięku.

## Zmiany podczas spotkania

Kliknięcie agendy wybiera punkt do podglądu. Dopiero „Przejdź do punktu”
zmienia odliczanie. Dzięki temu prowadzący może przygotować następny temat
bez przerywania obecnego. Zapisywanie notatek pokazuje dyskretny stan zapisu
i konkretny błąd, jeśli zapis się nie udał.

Zmiana kolejności dotyczy przyszłego planu. +1/+5 minut aktualizuje prognozę,
zachowując pierwotne godziny do obliczania opóźnienia. Usuwanie bieżącego
punktu pokazuje konsekwencję i wybór następcy; nie kasuje notatek/nagrań.
Ponowne wklejenie planu wymaga podglądu zmian zamiast bezwarunkowego nadpisania.

Motyw, wielkość okna, przypinanie, podgląd notatek i tryb końca punktu
zmieniają się bez restartu sesji. Zmiana źródła audio podczas nagrywania
tworzy jawnie nowy segment po zatwierdzeniu; nie podmienia urządzenia po cichu.
Zmiana ustawień API dotyczy następnego zlecenia, nie już wysłanego nagrania.

## Nagrywanie i API

Panel rozwijany: źródła, krótki test poziomów, lokalizacja, start/stop,
czas i stan zapisu. Podczas nagrywania stałe oznaczenie „Nagrywanie” także
w panelu i zasobniku. Zmiana widoku nie uruchamia ani nie zatrzymuje nagrania.

Transkrypcja jest osobnym krokiem dla zakończonego pliku. Ekran przed wysyłką
pokazuje usługę, plik, rozmiar i informację o opłatach. Bez klucza reszta
programu działa normalnie. Błąd API nie przerywa spotkania ani nagrania.

## Przegląd GitHub i decyzja

Źródła sprawdzone 2026-11-07. To przegląd dokumentacji repozytoriów,
bez instalacji, audytu bezpieczeństwa i benchmarków.

| Komponent | Co wnosi | Decyzja dla tego projektu |
| --- | --- | --- |
| [PySide6-Essentials](https://github.com/pyside/pyside-setup/blob/dev/README.pyside6_essentials.md) | Wariant z podstawowymi modułami Qt, w tym Widgets | Kandydat dla rdzenia; sprawdzić zależności audio osobno |
| [Tabler Icons](https://github.com/tabler/tabler-icons) | Ikony SVG na licencji MIT | Wybrać kilkanaście plików, bez biblioteki Python i całego zestawu |
| [PyQtDarkTheme](https://github.com/5yutan5/PyQtDarkTheme) | Gotowy płaski motyw dla Qt/PySide | Inspiracja; na start własny mały QSS, bez tej zależności |
| [superqt](https://github.com/pyapp-kit/superqt) | Dodatkowe komponenty dla Qt/Python | Nie dodawać, dopóki nie pojawi się konkretna potrzeba |
| [QtAwesome](https://github.com/spyder-ide/qtawesome) | Ikony oparte na fontach dla Qt | Zrezygnować na start: wybrane SVG wystarczą |

Wybrany kierunek: standardowe widgety, własna paleta/QSS i wybrane Tabler SVG.
Nie kopiować cudzego motywu jako własnego. Przy dołączeniu ikon zachować ich
notę licencyjną. Licencja MIT projektu nie zastępuje licencji zależności.
Przed dodaniem każdego komponentu sprawdzić wersję, zgodność, licencję
i faktyczny wpływ na rozmiar oraz start paczki.

## Budżet zasobów i weryfikacja

Cele początkowe rdzenia: start ≤3 s, RAM ≤150 MiB, spoczynek ≤1% jednego rdzenia,
paczka rozpakowana ≤150 MiB. To cele do walidacji, nie obecne parametry.
Mierzyć wersję spakowaną na każdym systemie, odnotowując sprzęt, architekturę,
wersję OS i zależności. Osobno mierzyć nagrywanie, transkrypcję i eksport.

Odświeżanie licznika 2–4 Hz z rzeczywistym pomiarem upływu czasu, audio
zapisywane strumieniowo, sieć na żądanie, brak lokalnego modelu AI.
Sprawdzić responsywność po godzinie, długą agendę/notatki i przywracanie okien.
Rozmiaru paczki z opcjonalnymi backendami audio nie ukrywać w wyniku rdzenia.

Nagrywanie ekranu pozostaje poza pierwszą wersją. Jeśli wróci do zakresu,
porównać 5–15 FPS i kodowanie sprzętowe na rzeczywistych urządzeniach;
wyłączony moduł nie powinien uruchamiać przechwytywania ani kodera.
