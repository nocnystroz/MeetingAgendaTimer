# Licznik spotkaniowy

Lekka aplikacja desktopowa do prowadzenia spotkania: wklejasz agendę,
a osobne okno pokazuje aktualny punkt i czas pozostały do jego końca.
Panel prowadzącego ma łączyć notatki, decyzje, zadania i opcjonalne nagranie.

**Stan: planowanie, bez implementacji i gotowych paczek.** Poniższe funkcje
opisują uzgodniony zakres; nie są jeszcze dostępne. Postęp śledzimy
w [ROADMAP.md](ROADMAP.md), a zasady projektu w [AGENTS.md](AGENTS.md).

## Planowane funkcje

- Windows, macOS i Linux; osobne paczki przenośne bez instalatora.
- Wklejanie agendy z czasami trwania albo przedziałami godzinowymi i podgląd
  interpretacji z czytelnymi błędami.
- Osobny licznik: przypinanie, minimalizacja, schowanie do zasobnika/menu bar.
- Pauza, poprzedni/następny punkt, +1/+5 minut, przewidywany koniec i opóźnienie.
- Automatyczne przejścia albo licznik przekroczenia czasu; opcjonalny sygnał.
- Zmiany agendy i przełączanie widoków/motywów w trakcie bez resetu spotkania.
- Notatki przed spotkaniem i podczas niego, osobno do każdego punktu.
- Decyzje i zadania z osobą odpowiedzialną oraz terminem; eksport Markdown/PDF.
- Lokalne szablony oraz odzyskiwanie bieżącego spotkania po awarii.
- Nagrywanie mikrofonu i dźwięku spotkania, z wyborem dostępnych źródeł.
- Znaczniki punktów w nagraniu i opcjonalnej transkrypcji.
- Transkrypcja przez zewnętrzne API po podłączeniu własnego klucza
  i osobnym zatwierdzeniu wysłania wybranego nagrania.

## Przykładowe agendy

Czas od rozpoczęcia spotkania:

```text
Wprowadzenie — 5 min
Omówienie wyników — 15 min
Decyzje i następne kroki — 10 min
```

Harmonogram godzinowy:

```text
10:00–10:05 Wprowadzenie
10:05–10:20 Omówienie wyników
10:20–10:30 Decyzje i następne kroki
```

Przed startem użytkownik sprawdzi rozpoznane punkty. Dla godzin wybierze
realizację według zegara albo rozpoczęcie planu od teraz. Szczegóły zachowania
pauzy i zmian godzin wymagają implementacji oraz testów.

## Interfejs i lekkość

Panel prowadzącego: agenda po lewej, notatki/decyzje/zadania po prawej,
sterowanie w stałym miejscu. Osobny licznik do udostępniania nie wyświetla
prywatnych notatek ani ustawień API. Kierunek wizualny i źródła bibliotek:
[docs/UX.md](docs/UX.md).

Planowana baza to Python i natywne Qt Widgets/PySide6, mały własny motyw,
systemowe fonty i niewielki zestaw ikon. Bez osadzonej przeglądarki i lokalnych
modeli AI. Nagrywanie i API będą ładowane na żądanie. Budżety zasobów
w roadmapie są celami do pomiaru, a nie wynikami benchmarków.

## Uruchamianie i środowisko programistyczne

**Nie ma jeszcze programu do uruchomienia ani skryptu budowania.** Utworzono
lokalne `.venv`; zależności i konfiguracja projektu pozostają do dodania.
Nie instaluj bibliotek globalnie. Docelowa wersja źródłowa będzie uruchamiana
przez Python z `.venv`, z pomocniczym skryptem PowerShell na Windows.

Paczki dla użytkowników mają zawierać interpreter i potrzebne biblioteki,
bez instalowania Pythona, pip lub venv. Każdy system i architektura wymagają
własnego artefaktu oraz rzeczywistych testów. Wsparcie przechwytywania dźwięku
systemowego zależy od platformy i uprawnień; nie zostało jeszcze zweryfikowane.

## Prywatność i transkrypcja

Plan zakłada lokalną agendę, notatki i nagrania, bez konta i telemetrii.
Internet będzie potrzebny tylko do dobrowolnej transkrypcji. Samo wpisanie
klucza nie uruchomi wysyłania. Dostawca API nie został jeszcze wybrany;
usługa może naliczać opłaty na koncie użytkownika.

[PRIVACY.md](PRIVACY.md) opisuje projekt polityki i wymagania dla implementacji.
Przed wydaniem dokument trzeba uzgodnić z rzeczywistym zachowaniem programu.

## Poza pierwszą wersją

Nagrywanie wybranego monitora/okna pozostaje pomysłem do oceny kosztu zasobów.
Historia spotkań, archiwum i integracje Microsoft 365/Google Workspace
są odłożone; konta w tych usługach nie są potrzebne do obecnego zakresu.

## Inspiracja i licencja

Nagrywanie inspirowane funkcjonalnie lokalnym projektem `audio-rozkminka`:
mikrofon + dźwięk spotkania, miks lub rozdzielone kanały i widoczny czas nagrania.
Kod projektu referencyjnego nie został skopiowany.

Kod i dokumentacja tego projektu: [MIT](LICENSE). Zależności zachowują swoje
własne licencje; ich noty będą dołączone do paczek przy wyborze komponentów.
