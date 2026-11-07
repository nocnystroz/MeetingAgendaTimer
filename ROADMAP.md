# Plan prac — licznik spotkaniowy

## 0. Ustalenia i środowisko

- [x] Zapisać wymagania i założenia w `AGENTS.md`.
- [x] Uwzględnić Windows, macOS i Linux oraz uruchamianie bez instalatora.
- [x] Utworzyć lokalne środowisko programistyczne `.venv`.
- [x] Dodać ignorowanie środowiska, cache i artefaktów budowania.
- [x] Zainicjalizować repozytorium i wykonać pierwszy commit dokumentacji.
- [x] Rozszerzyć zakres o notatki, nagrania, transkrypcję API i zmiany na żywo.
- [x] Wybrać kierunek UX i udokumentować przegląd bibliotek GitHub w `docs/UX.md`.
- [x] Dodać `README.md`, `LICENSE` (MIT) oraz projekt polityki `PRIVACY.md`.
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
- [ ] +1/+5 minut, przewidywana godzina końca i opóźnienie wobec pierwotnego planu.
- [ ] Tryb automatyczny lub pozostanie na punkcie z licznikiem przekroczenia.
- [ ] Opcjonalny sygnał końca, domyślnie wyłączony; zmiana trybu w trakcie.

## 3. Interfejs desktopowy

- [ ] Okno edytora z polem do wklejenia agendy, przykładem i podglądem.
- [ ] Osobne, skalowalne okno licznika z czytelnym tytułem i dużymi cyframi.
- [ ] Wyświetlanie bieżącego i następnego punktu oraz stanu pauzy/końca.
- [ ] Przełącznik „Zawsze na wierzchu”, możliwy do zmiany podczas odliczania.
- [ ] Minimalizacja do paska, obsługa klawiatury i długich tytułów.
- [ ] Wizualne wyróżnienie zbliżającego się końca punktu.
- [ ] Lokalny zapis agendy i ustawień oraz odporność na uszkodzony zapis.
- [ ] Stałe identyfikatory punktów i historia zmian bieżącego spotkania.
- [ ] Edycja agendy, kolejności, czasu i tytułów w trakcie bez utraty danych.
- [ ] Osobny wybór punktu do edycji/podglądu i osobna akcja przejścia licznika.
- [ ] Obsługa usunięcia bieżącego punktu i ponownego wklejenia agendy.
- [ ] Przełączanie widoku kompaktowego/pełnego, motywu i przypinania w trakcie.
- [ ] Lokalne szablony agendy z opcjonalnymi notatkami przygotowawczymi.

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

## 5. Notatki, decyzje, zadania i odzyskiwanie

- [ ] Edycja i podgląd notatek do każdego punktu przed spotkaniem i w jego trakcie.
- [ ] Podgląd innego punktu nie zmienia odliczania; okno licznika bez prywatnych notatek.
- [ ] Decyzje oraz zadania: treść, osoba odpowiedzialna, termin i stan wykonania.
- [ ] Atomowy zapis z krótkim opóźnieniem po edycji, bez blokowania interfejsu.
- [ ] Odtworzenie bieżącego spotkania po awarii, z decyzją użytkownika o odzyskaniu.
- [ ] Eksport do Markdown oraz PDF z wyborem treści i lokalizacji zapisu.
- [ ] Testy: zmiany kolejności/nazwy/usunięcia punktu zachowują właściwe notatki;
      zapis, odczyt, odzyskiwanie i eksport polskich znaków oraz długich treści.

## 6. Nagrywanie lokalne

- [x] Przejrzeć `audio-rozkminka`: wybór mikrofonu i wyjścia audio, miks lub
      rozdzielone kanały, poziomy źródeł oraz czas nagrania.
- [ ] Przygotować interfejs backendu nagrywania niezależny od GUI i licznika.
- [ ] Wybrać backendy mikrofonu i dźwięku systemowego na każdy system;
      sprawdzić zależności, dystrybucję i potrzebne uprawnienia.
- [ ] Wybór źródeł i katalogu, test urządzeń, poziomy sygnału i kontrola głośności.
- [ ] Start/stop oraz jawna pauza nagrania, niezależna od pauzy licznika.
- [ ] Miks mikrofonu i spotkania lub kanały rozdzielone; format zapisu dobrany
      do dostępności, niezawodności i rozmiaru paczki.
- [ ] Widoczny stan i czas nagrania w panelu oraz zasobniku; brak nagrywania w tle
      bez wcześniejszej akcji użytkownika.
- [ ] Strumieniowy zapis, poprawne zamknięcie pliku i odzyskanie zapisanej części
      po awarii; nie obiecywać odzyskania danych, których nie zapisano.
- [ ] Obsługa odłączenia urządzenia, odmowy uprawnień, braku miejsca i zamknięcia
      aplikacji podczas nagrywania. Brak obsługi audio nie blokuje reszty aplikacji.
- [ ] Znaczniki punktów na osi nagrania, także po pauzach i powrotach do punktu.
- [ ] Rzeczywiste testy mikrofonu i dźwięku systemowego na Windows, macOS i Linux.

## 7. Opcjonalna transkrypcja API

- [ ] Wybrać pierwszego dostawcę/model i sprawdzić jego aktualną dokumentację,
      limity, koszty i zasady przetwarzania przed implementacją.
- [ ] Podłączenie własnego klucza: domyślnie pamięć sesji; opcjonalnie systemowy
      magazyn poświadczeń, bez zapisu jawnego w konfiguracji.
- [ ] Wybór zakończonego nagrania i jawna akcja wysłania; podgląd dostawcy, pliku,
      rozmiaru oraz informacji o kosztach i przekazaniu danych poza urządzenie.
- [ ] Wysyłać tylko potrzebne audio; bez automatycznej wysyłki notatek i agendy.
- [ ] Zadanie w tle: postęp, anulowanie, timeout, brak sieci, błędny klucz,
      limity pliku/API, bez automatycznego ponawiania płatnego zadania.
- [ ] Lokalny zapis i edycja transkrypcji, eksport oraz powiązanie fragmentów
      z punktami przez znaczniki czasu, jeśli dostawca je zwraca.
- [ ] Bez znaczników czasu nie przedstawiać przypisania fragmentów jako pewnego.
- [ ] Testy na mockach: brak wysyłki bez akcji, brak sekretów w logach/eksportach,
      błędy i anulowanie. Rzeczywisty test API dopiero z udostępnionym kluczem.
- [ ] Uzupełnić `PRIVACY.md` o faktycznie wybranego dostawcę, endpoint i przesyłane
      dane oraz dodać link do jego aktualnej polityki.

## 8. UX i budżet zasobów

- [ ] Zbudować natywne Qt Widgets zgodnie z `docs/UX.md`: agenda + edytor,
      stałe sterowanie, prosty licznik, rozwijane opcje audio i API.
- [ ] Systemowe fonty, jasny/ciemny/systemowy motyw i wybrane lokalne ikony SVG.
- [ ] Porównać minimalny PySide6-Essentials z potrzebnymi modułami audio;
      nie dołączać całego zestawu dodatków bez sprawdzenia konieczności.
- [ ] Bez WebEngine, Electron, webowego serwera i lokalnych modeli AI.
- [ ] Audio/API ładowane na żądanie, odświeżanie licznika 2–4 Hz, operacje
      dyskowe i sieciowe bez blokowania interfejsu.
- [ ] Zmierzyć start, RAM, CPU i wielkość paczki na każdym systemie/architekturze.
      Cele rdzenia: start ≤3 s, RAM ≤150 MiB, CPU spoczynkowe ≤1% jednego rdzenia,
      paczka rozpakowana ≤150 MiB; opisać sprzęt i metodę pomiaru.
- [ ] Osobne pomiary audio/API i godzinnej sesji; sprawdzić brak wzrostu RAM
      proporcjonalnego do długości nagrania i responsywność podczas eksportu.
- [ ] Przetestować klawiaturę, kontrast, skalowanie DPI i długie polskie tytuły.

## 9. Wydania bez instalatora

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
- [ ] Dołączyć aktualną politykę prywatności, MIT projektu i noty/licencje
      faktycznie dołączanych zależności, bibliotek audio, kodeków i ikon.

## 10. Pomysły odłożone — poza pierwszą wersją

- [ ] Ocenić opcjonalne nagrywanie wybranego monitora lub okna. Nie dodawać
      zależności do rdzenia przed decyzją o realizacji. Zmierzyć 5–15 FPS,
      kodowanie sprzętowe, CPU/GPU, dysk, synchronizację audio i uprawnienia.
- [ ] Ewentualna historia spotkań i wyszukiwanie w archiwum.
- [ ] Ewentualne integracje Microsoft 365/Google Workspace; brak kont i środowiska
      testowego Microsoft nie blokuje żadnego elementu obecnego zakresu.

## Kryteria gotowości pierwszej wersji

Użytkownik rozpakowuje paczkę dla swojego systemu, uruchamia program bez
instalacji, wkleja agendę, sprawdza podgląd i rozpoczyna odliczanie.
Osobne okno pokazuje poprawny tytuł i pozostały czas, automatycznie zmienia
punkt, daje się przypiąć, zminimalizować i schować do zasobnika oraz przywrócić.
Brak zasobnika nie powoduje utraty dostępu do działającego programu.
Wsparcie platform potwierdzają rzeczywiste testy, a ograniczenia są opisane.
Prowadzący może edytować agendę i notatki bez resetu spotkania, zapisywać
decyzje/zadania i wyeksportować podsumowanie. Nagrywanie jest lokalne i jawne,
a transkrypcja pozostaje opcjonalna. Podanie klucza nie powoduje wysyłki.
Audio/API nie blokują licznika. Odzyskiwanie danych dotyczy bieżącej sesji;
archiwum i integracje zewnętrzne pozostają poza zakresem pierwszej wersji.
Lekkość potwierdzają pomiary, nie samo użycie natywnych kontrolek.

## Aktualne przeszkody

- Poprzednia próba pobrania PySide6 do `.venv` zakończyła się błędem DNS.
  Po zmianie uprawnień nie powtarzano jeszcze instalacji. Implementacja
  i testy GUI pozostają otwarte; nie traktować starego błędu jako potwierdzenia
  obecnej niedostępności sieci.

Wcześniejsza blokada zapisu `.git` została usunięta; repozytorium zainicjalizowano
na gałęzi `main`.
