# Plan prac — licznik spotkaniowy

## 0. Ustalenia i środowisko

- [x] Zapisać wymagania i założenia w `AGENTS.md`.
- [x] Uwzględnić Windows, macOS i Linux oraz uruchamianie bez instalatora.
- [x] Utworzyć lokalne środowisko programistyczne `.venv`.
- [x] Dodać ignorowanie środowiska, cache i artefaktów budowania.
- [x] Zainicjalizować repozytorium i wykonać pierwszy commit dokumentacji.
- [ ] Dodać konfigurację projektu i zależności PySide6.
- [ ] Zainstalować zależności w `.venv` i potwierdzić uruchomienie Qt.

## 1. Agenda i parser

- [ ] Przygotować model punktu agendy oraz parser niezależny od GUI.
- [ ] Obsłużyć tytuły z czasem trwania, np. `Wprowadzenie — 5 min`.
- [ ] Obsłużyć przedziały godzinowe, np. `10:00–10:15 Wyniki`.
- [ ] Obsłużyć polskie znaki, listy numerowane, wypunktowania i różne myślniki.
- [ ] Dodać podgląd z tytułem, czasem i łączną długością spotkania.
- [ ] Pokazać błędy z numerami wierszy; odrzucać niejednoznaczne dane.
- [ ] Przetestować poprawne przykłady, puste dane, błędy, nakładanie przedziałów
      i przejście przez północ.

## 2. Logika odliczania

- [ ] Wdrożyć start od teraz, automatyczne przejścia i zakończenie agendy.
- [ ] Wdrożyć pauzę/wznowienie, restart oraz poprzedni/następny punkt.
- [ ] Wdrożyć tryb godzinowy: oczekiwanie na start, późne dołączenie i przerwy.
- [ ] Ustalić semantykę pauzy i ręcznego przejścia w trybie godzinowym.
- [ ] Zapewnić poprawne odliczanie mimo opóźnień odświeżania i minimalizacji.
- [ ] Przetestować granice punktów i wielokrotne pauzy bez rzeczywistego czekania.

## 3. Interfejs desktopowy

- [ ] Okno edytora z polem do wklejenia agendy, przykładem i podglądem.
- [ ] Osobne, skalowalne okno licznika z czytelnym tytułem i dużymi cyframi.
- [ ] Wyświetlanie bieżącego i następnego punktu oraz stanu pauzy/końca.
- [ ] Przełącznik „Zawsze na wierzchu”, możliwy do zmiany podczas odliczania.
- [ ] Minimalizacja do paska, obsługa klawiatury i długich tytułów.
- [ ] Wizualne wyróżnienie zbliżającego się końca punktu.
- [ ] Lokalny zapis agendy i ustawień oraz odporność na uszkodzony zapis.

## 4. Zasobnik i integracja z systemem

- [ ] Ikona zasobnika/menu bar i menu: pokaż licznik, pokaż agendę,
      pauza/wznów, zakończ.
- [ ] Osobna akcja schowania do zasobnika; odliczanie działa w tle.
- [ ] Przywracanie okien i obsługa zamykania bez przypadkowej utraty dostępu.
- [ ] Bezpieczne zachowanie przy braku dostępnego zasobnika.
- [ ] Rzeczywista weryfikacja Windows: pasek zadań, zasobnik, przypinanie.
- [ ] Rzeczywista weryfikacja macOS: Dock, pasek menu, przypinanie.
- [ ] Rzeczywista weryfikacja Linux: używane środowisko graficzne;
      opisać ograniczenia środowisk bez zasobnika oraz Waylanda.

## 5. Wydania bez instalatora

- [ ] Przygotować budowanie paczek z dołączonym Pythonem i Qt.
- [ ] Windows: przenośny ZIP z programem `.exe`, bez instalatora.
- [ ] macOS: przenośna aplikacja `.app` w archiwum.
- [ ] Linux: przenośna paczka z plikiem uruchamiającym i bibliotekami;
      jawnie określić wspierane dystrybucje/bazę systemową.
- [ ] Określić wspierane architektury i budować każdą paczkę na właściwej platformie.
- [ ] Dodać uruchamianie wersji źródłowej oraz pomocnicze skrypty dla
      PowerShell i powłoki POSIX, korzystające z `.venv`.
- [ ] Sprawdzić paczki na systemach bez zainstalowanego Pythona i Qt.
- [ ] Udokumentować systemowe komunikaty zaufania dla niepodpisanych paczek.
- [ ] Przygotować instrukcję po polsku z formatami agendy i obsługą okien.

## Kryteria gotowości pierwszej wersji

Użytkownik rozpakowuje paczkę dla swojego systemu, uruchamia program bez
instalacji, wkleja agendę, sprawdza podgląd i rozpoczyna odliczanie.
Osobne okno pokazuje poprawny tytuł i pozostały czas, automatycznie zmienia
punkt, daje się przypiąć, zminimalizować i schować do zasobnika oraz przywrócić.
Brak zasobnika nie powoduje utraty dostępu do działającego programu.
Wsparcie platform potwierdzają rzeczywiste testy, a ograniczenia są opisane.

## Aktualne przeszkody

- Pobranie PySide6 do `.venv` nie powiodło się: brak rozwiązywania DNS
  dla PyPI w bieżącym środowisku. Implementacja i testy GUI pozostają otwarte.

Wcześniejsza blokada zapisu `.git` została usunięta; repozytorium zainicjalizowano
na gałęzi `main`.
