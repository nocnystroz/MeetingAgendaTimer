# Licznik spotkaniowy

Lokalna aplikacja desktopowa do prowadzenia spotkań według agendy. Osobny
licznik pokazuje bieżący punkt i pozostały czas, a panel prowadzącego pozwala
zapisywać notatki, decyzje i zadania.

**Prototyp do testów — wersja aplikacji to skrócony hash commita.** Działa lokalnie na Linux X11. Kod i skrypty
budowania obejmują Windows i macOS, ale tych platform nie przetestowano jeszcze
na rzeczywistych urządzeniach. Szczegóły: [ROADMAP.md](ROADMAP.md)
i [docs/VALIDATION.md](docs/VALIDATION.md).

## Uruchomienie bez instalatora

Gotową paczkę dla swojego systemu należy rozpakować i uruchomić:

- Windows: `Licznik-Spotkaniowy.exe`.
- macOS: `Licznik-Spotkaniowy.app`.
- Linux: plik wykonywalny `Licznik-Spotkaniowy` w rozpakowanym katalogu.

Paczka zawiera interpreter i biblioteki. Nie wymaga instalowania Pythona,
pip ani venv. Nie przenoś samego pliku wykonywalnego bez towarzyszących bibliotek.
Lokalne wyniki budowania znajdują się w `dist/` i nie są commitowane.
Nie publikowano jeszcze wydań ani nie uruchamiano zdalnego CI.

Wariant **core** zawiera licznik, notatki, eksport, transkrypcję plików
skompresowanych oraz zrzuty całego ekranu. Wariant **full** dodaje nagrywanie,
przygotowanie WAV do transkrypcji, magazyn klucza i przechwytywanie wybranego
okna. Zainstalowanie modułu nie uruchamia go w tle.

Niepodpisane paczki mogą wywołać komunikat SmartScreen lub Gatekeeper.
Nie zmieniaj globalnej polityki bezpieczeństwa systemu. Obecne paczki lokalne
nie mają podpisu wydawcy ani notaryzacji Apple. Wsparcie Linux zależy także
od systemowych bibliotek pulpitu i serwera dźwięku; sprawdź walidację.

## Uruchomienie ze źródeł

Wymagany Python 3.11+ i [uv](https://docs.astral.sh/uv/). Środowisko projektu to `.venv`.

```bash
uv sync --frozen --extra dev --extra audio --extra keyring --extra capture
uv run python -m meeting_timer
```

Można również użyć `./uruchom.sh` na Linux/macOS lub `./uruchom.ps1`
w PowerShell na Windows po utworzeniu środowiska. Skrypty nie instalują bibliotek
ani nie zmieniają polityki wykonywania. Gdy PowerShell blokuje skrypty, uruchom
bezpośrednio `.venv\Scripts\python.exe -m meeting_timer`.

Alternatywa bez uv: `python -m venv .venv`, a następnie interpreterem z tego
środowiska wykonaj `-m pip install -e ".[audio,keyring,capture,dev]"`.
Na Linux audio wymaga działającego PulseAudio lub PipeWire z kompatybilnością
PulseAudio i biblioteki `libpulse`. Dźwięk systemowy na macOS wymaga dostępnego
źródła loopback/urządzenia wirtualnego; aplikacja nie instaluje sterowników.

## Agenda i sterowanie

Wybierz **Wklej**, wprowadź plan, sprawdź podgląd i zastosuj:

```text
Wprowadzenie — 5 min
Omówienie wyników — 15 min
Decyzje i następne kroki — 10 min
```

Możesz też podać godziny:

```text
10:00–10:05 Wprowadzenie
10:05–10:20 Omówienie wyników
10:20–10:30 Decyzje i następne kroki
```

Możesz wklejać także tabelki z Excela/Sheets (tabulatory), CSV z przecinkiem
lub średnikiem oraz tabelki Markdown. Nagłówki `Temat` i `Czas (min)` pozwalają
podać samą liczbę minut. Obsługiwane są również `15 minut — Wyniki`,
`Wyniki 1h30min`, `Wyniki (00:15:00)` i `Wyniki [15:00]` (MM:SS).

Lista samych godzin rozpoczęcia wyznacza czas punktów na podstawie następnego:

```text
10:00 Wyniki
10:15 Decyzje
10:25 Koniec
```

Ostatni punkt musi mieć czas trwania albo końcowy wiersz `HH:MM Koniec`.
Nierozpoznane linie nie są pomijane. Standardowe nagłówki i separatory tabeli
są rozpoznawane jako struktura.

Czasy trwania obsługują `h`, `godz`, `min`, `m`, `sek`, `s` oraz części minuty,
np. `1,5 min`. Nie mieszaj czasów trwania i przedziałów w jednej agendzie.
Nierozpoznane wiersze wymagają poprawy — nie są pomijane.

- **Plan od teraz**: czas biegnie po naciśnięciu Rozpocznij.
- **Według godzin agendy**: wybierz datę pierwszego punktu; późny start pomija
  upłynięte punkty, a przerwy i oczekiwanie są widoczne w liczniku.
- Pauza zatrzymuje plan. Wznowienie i ręczne przejście przesuwają pozostały
  harmonogram także w trybie godzinowym. Restart umożliwia ponowny start.
- **+1 / +5 min** wydłuża bieżący punkt i prognozę końca. Plan początkowy
  pozostaje punktem odniesienia dla wyświetlanego opóźnienia/przyspieszenia.
- Wyłączenie automatycznych przejść zatrzymuje temat z licznikiem przekroczenia.
  Ponowne włączenie synchronizuje punkt z aktualną pozycją w zmodyfikowanym planie.
- **Ctrl+Enter**: start/pauza; **Ctrl+N**: agenda; **Ctrl+S**: kopia JSON;
  **Ctrl+O**: otwarcie; **Ctrl+E**: eksport; **Ctrl+Q**: zakończenie.

Wybór punktu na liście służy do podglądu i edycji. Licznik przełącza dopiero
**Przejdź do wybranego punktu**, Poprzedni lub Następny. W trakcie można zmieniać
nazwy, czasy i treści oraz przestawiać przyszłe punkty. Usunięte punkty pozostają
w danych bieżącej sesji. Ponowne wklejenie agendy zatrzymuje licznik,
zachowuje stare notatki w danych sesji i nie zatrzymuje osobnego nagrania.

## Licznik i notatki

**Pokaż licznik** otwiera osobne okno z przełącznikami **Zawsze na wierzchu**
i **Kompaktowy**. Widok kompaktowy ma około 260 × 138 px, pokazuje krótki tytuł,
czas i przyciski pauzy, przypinania, panelu oraz powrotu do pełnego widoku. Przełączanie i zmiana motywu nie resetują czasu.
Standardowy przycisk minimalizacji chowa do paska; **Schowaj** do zasobnika.
Przy braku zasobnika aplikacja minimalizuje okno zamiast tracić do niego dostęp.
Zamknięcie licznika przywraca panel prowadzącego.

Notatki, decyzje i zadania przypisane są do stałych identyfikatorów punktów.
Menu **Spotkanie** zawiera zapis kopii, lokalne szablony i eksport Markdown/PDF
z wyborem treści. JSON przechowuje odnośniki do nagrań i PNG, nie ich zawartość.
Po przeniesieniu plików trzeba zachować lub odtworzyć właściwe lokalizacje.

Zapis po edycji następuje po 700 ms, a pozycja działającego licznika co 5 s.
Po awarii program proponuje odzyskanie w pauzie, bez uruchamiania nagrywania/API.
Niezapisane ostatnie zmiany mogą wymagać odtworzenia. Panel do udostępniania
nie wyświetla notatek ani klucza; sam tytuł punktu nadal może być poufny.

## Nagrywanie i transkrypcja

Rozwiń **Nagrywanie i transkrypcja**, wykryj źródła, wybierz mikrofon i/lub
źródło spotkania oraz przetestuj poziomy. Wybierz miks mono lub rozdzielone
kanały i katalog. **Nagraj** wymaga potwierdzenia; nagranie jest lokalnym WAV
PCM 16-bit / 48 kHz. Osobna pauza audio usuwa te fragmenty z zapisu.
Pauza licznika nie zatrzymuje nagrania. Zmiana źródeł wymaga jawnego nowego segmentu.

Znaczniki punktów zapisują pozycję w nagraniu; znajdziesz je w zakładce
**Nagrania** i pliku `.markers.json`. Każdy segment ma limit ok. 3,8 GB,
po którym trzeba jawnie rozpocząć kolejny. Przy błędzie urządzenia lub dysku
aplikacja zachowuje to, co udało się zapisać; nie gwarantuje odzyskania
ostatniego bloku po awarii zasilania.

Transkrypcja korzysta z OpenAI (`gpt-transcribe`) i wymaga własnego klucza API.
Podanie klucza nie wysyła danych. Wybierz zakończony plik i potwierdź dostawcę,
zakres oraz możliwość kosztów. WAV z aplikacji dzielony jest lokalnie na części
do 5 minut / mono 16 kHz; inne obsługiwane pliki muszą mieścić się w limicie 24 MB.
Nie ma automatycznych ponowień. Przy anulowaniu lub błędzie zachowywane są
odebrane fragmenty, a już naliczonych kosztów nie można cofnąć.

Wynik można poprawić, ręcznie przypisać do punktu i wyeksportować. Gdy API
nie zwraca dokładnych znaczników, program nie przypisuje zdań automatycznie.
Dokumentacja integracji: [OpenAI — file transcription](https://developers.openai.com/api/docs/guides/speech-to-text).

## Automatyczne zrzuty

**Zrzuty…** pozwala wybrać ekran albo wykryte okno, interwał 1–86400 sekund,
limit plików i katalog. PNG zapisuje się na początku, a potem co wskazany czas.
Interwał można zmienić podczas pracy. Limit domyślnie wynosi 200 i zatrzymuje
cykl bez usuwania poprzednich obrazów. Zrzuty są widoczne przy punkcie agendy.

Zamknięcie okna ustawień nie zatrzymuje zrzutów — użyj **Zatrzymaj**.
Stan pozostaje w panelu i zasobniku. Brak uprawnień/obrazu zatrzymuje cykl,
bez zamiany wybranego okna na cały pulpit. Wybrane okno wymaga dodatku capture;
przechwytywanie Waylanda oraz zachowanie okien zminimalizowanych zależą od
backendu/systemu i wymagają dalszych testów. Na macOS może pojawić się prośba
o uprawnienie do nagrywania ekranu. Chroniona treść może być niedostępna.

Zrzuty nie są nagraniem wideo i nigdy nie trafiają do transkrypcji API.

## Dane, testy i budowanie

Katalog danych: Linux `$XDG_DATA_HOME/licznik-spotkaniowy` lub
`~/.local/share/licznik-spotkaniowy`; Windows `%LOCALAPPDATA%/licznik-spotkaniowy`;
macOS `~/Library/Application Support/licznik-spotkaniowy`.
Możesz wskazać inny przez `MEETING_TIMER_DATA_DIR`. Nagrania i zrzuty domyślnie
trafiają do podkatalogów `recordings` i `screenshots`. Otwórz katalog z menu.

```bash
uv run pytest -q
uv run ruff check meeting_timer tests scripts run.py
uv run python scripts/build_portable.py --core
uv run python scripts/build_portable.py
```

Buduj na docelowym systemie i architekturze. Wersja pełna wymaga dodatków
`audio`, `keyring`, `capture`. `.github/workflows/check.yml` przygotowuje testy
oraz budowanie na trzech systemach, bez automatycznego publikowania wydania.

[Prywatność](PRIVACY.md) · [MIT](LICENSE) · [Licencje zależności](THIRD_PARTY.md)
· [Założenia](AGENTS.md) · [UX](docs/UX.md).

Historia spotkań, integracje MS/Google i nagrywanie wideo pozostają odłożone.
Inspiracja funkcjonalna audio: lokalny projekt `audio-rozkminka`; nie kopiowano kodu.


## Identyfikacja wersji

Tytuły okien i prawy koniec paska stanu pokazują hash commita. Wersja źródłowa
odczytuje go z Git; `*` oznacza niezacommitowane zmiany. Paczka przenośna
ma wersję utrwaloną przy budowaniu, także bez dostępu do Git.
