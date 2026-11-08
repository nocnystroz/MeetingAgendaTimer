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
- [x] Dodać konfigurację projektu i zależności PySide6.
- [x] Zainstalować zależności w `.venv` i potwierdzić uruchomienie Qt.

## 1. Agenda i parser

- [x] Przygotować model punktu agendy oraz parser niezależny od GUI.
- [x] Obsłużyć tytuły z czasem trwania, np. `Wprowadzenie — 5 min`.
- [x] Obsłużyć przedziały godzinowe, np. `10:00–10:15 Wyniki`.
- [x] Obsłużyć polskie znaki, listy numerowane, wypunktowania i różne myślniki.
- [x] Dodać podgląd z tytułem, czasem i łączną długością spotkania.
- [x] Pokazać błędy z numerami wierszy; odrzucać niejednoznaczne dane.
- [x] Przetestować poprawne przykłady, puste dane, błędy, nakładanie przedziałów
      i przejście przez północ.

## 2. Logika odliczania

- [x] Wdrożyć start od teraz, automatyczne przejścia i zakończenie agendy.
- [x] Wdrożyć pauzę/wznowienie, restart oraz poprzedni/następny punkt.
- [x] Wdrożyć tryb godzinowy: oczekiwanie na start, późne dołączenie i przerwy.
- [x] Ustalić semantykę pauzy i ręcznego przejścia w trybie godzinowym.
- [x] Zapewnić poprawne odliczanie mimo opóźnień odświeżania i minimalizacji.
- [ ] Przetestować granice punktów i wielokrotne pauzy bez rzeczywistego czekania.
- [x] +1/+5 minut, przewidywana godzina końca i opóźnienie wobec pierwotnego planu.
- [x] Tryb automatyczny lub pozostanie na punkcie z licznikiem przekroczenia.
- [x] Opcjonalny sygnał końca, domyślnie wyłączony; zmiana trybu w trakcie.

## 3. Interfejs desktopowy

- [x] Okno edytora z polem do wklejenia agendy, przykładem i podglądem.
- [x] Osobne, skalowalne okno licznika z czytelnym tytułem i dużymi cyframi.
- [x] Wyświetlanie bieżącego i następnego punktu oraz stanu pauzy/końca.
- [x] Przełącznik „Zawsze na wierzchu”, możliwy do zmiany podczas odliczania.
- [ ] Minimalizacja do paska, obsługa klawiatury i długich tytułów.
- [x] Wizualne wyróżnienie zbliżającego się końca punktu.
- [x] Lokalny zapis agendy i ustawień oraz odporność na uszkodzony zapis.
- [x] Stałe identyfikatory punktów i zachowanie usuniętych danych w bieżącej sesji.
- [x] Edycja agendy, kolejności, czasu i tytułów w trakcie bez utraty danych.
- [x] Osobny wybór punktu do edycji/podglądu i osobna akcja przejścia licznika.
- [x] Obsługa usunięcia bieżącego punktu i ponownego wklejenia agendy.
- [x] Przełączanie widoku kompaktowego/pełnego, motywu i przypinania w trakcie.
- [x] Lokalne szablony agendy z opcjonalnymi notatkami przygotowawczymi.

## 4. Zasobnik i integracja z systemem

- [x] Ikona zasobnika/menu bar i menu: pokaż licznik, pokaż agendę,
      pauza/wznów, zakończ.
- [x] Osobna akcja schowania do zasobnika; odliczanie działa w tle.
- [x] Przywracanie okien i obsługa zamykania bez przypadkowej utraty dostępu.
- [x] Bezpieczne zachowanie przy braku dostępnego zasobnika.
- [ ] Rzeczywista weryfikacja Windows: pasek zadań, zasobnik, przypinanie.
- [ ] Rzeczywista weryfikacja macOS: Dock, pasek menu, przypinanie.
- [ ] Rzeczywista weryfikacja Linux: używane środowisko graficzne;
      opisać ograniczenia środowisk bez zasobnika oraz Waylanda.

## 5. Notatki, decyzje, zadania i odzyskiwanie

- [x] Edycja i podgląd notatek do każdego punktu przed spotkaniem i w jego trakcie.
- [x] Podgląd innego punktu nie zmienia odliczania; okno licznika bez prywatnych notatek.
- [x] Decyzje oraz zadania: treść, osoba odpowiedzialna, termin i stan wykonania.
- [x] Atomowy zapis po edycji (700 ms); zapis sesji jest synchroniczny, większe pliki wymagają dalszego pomiaru.
- [x] Odtworzenie bieżącego spotkania po awarii, z decyzją użytkownika o odzyskaniu.
- [x] Eksport do Markdown oraz PDF z wyborem treści i lokalizacji zapisu.
- [ ] Testy: zmiany kolejności/nazwy/usunięcia punktu zachowują właściwe notatki;
      zapis, odczyt, odzyskiwanie i eksport polskich znaków oraz długich treści.

## 6. Nagrywanie lokalne

- [x] Przejrzeć `audio-rozkminka`: wybór mikrofonu i wyjścia audio, miks lub
      rozdzielone kanały, poziomy źródeł oraz czas nagrania.
- [x] Przygotować interfejs backendu nagrywania niezależny od GUI i licznika.
- [ ] Wybrać backendy mikrofonu i dźwięku systemowego na każdy system;
      sprawdzić zależności, dystrybucję i potrzebne uprawnienia.
- [ ] Wybór źródeł i katalogu, test urządzeń, poziomy sygnału i kontrola głośności.
- [x] Start/stop oraz jawna pauza nagrania, niezależna od pauzy licznika.
- [x] Miks mikrofonu i spotkania lub kanały rozdzielone; format zapisu dobrany
      do dostępności, niezawodności i rozmiaru paczki.
- [x] Widoczny stan i czas nagrania w panelu oraz zasobniku; brak nagrywania w tle
      bez wcześniejszej akcji użytkownika.
- [ ] Strumieniowy zapis, poprawne zamknięcie pliku i odzyskanie zapisanej części
      po awarii; nie obiecywać odzyskania danych, których nie zapisano.
- [ ] Obsługa odłączenia urządzenia, odmowy uprawnień, braku miejsca i zamknięcia
      aplikacji podczas nagrywania. Brak obsługi audio nie blokuje reszty aplikacji.
- [x] Znaczniki punktów na osi nagrania, także po pauzach i powrotach do punktu.
- [ ] Rzeczywiste testy mikrofonu i dźwięku systemowego na Windows, macOS i Linux.

## 7. Opcjonalna transkrypcja API

- [x] Wybrać pierwszego dostawcę/model i sprawdzić jego aktualną dokumentację,
      limity, koszty i zasady przetwarzania przed implementacją.
- [x] Podłączenie własnego klucza: domyślnie pamięć sesji; opcjonalnie systemowy
      magazyn poświadczeń, bez zapisu jawnego w konfiguracji.
- [x] Wybór zakończonego nagrania i jawna akcja wysłania; podgląd dostawcy, pliku,
      rozmiaru oraz informacji o kosztach i przekazaniu danych poza urządzenie.
- [x] Wysyłać tylko potrzebne audio; bez automatycznej wysyłki notatek i agendy.
- [ ] Zadanie w tle: postęp, anulowanie, timeout, brak sieci, błędny klucz,
      limity pliku/API, bez automatycznego ponawiania płatnego zadania.
- [ ] Lokalny zapis i edycja transkrypcji, eksport oraz powiązanie fragmentów
      z punktami przez znaczniki czasu, jeśli dostawca je zwraca.
- [x] Bez znaczników czasu nie przedstawiać przypisania fragmentów jako pewnego.
- [x] Testy na mockach: brak wysyłki bez akcji, brak sekretów w logach/eksportach,
      błędy i anulowanie. Rzeczywisty test API dopiero z udostępnionym kluczem.
- [ ] Uzupełnić `PRIVACY.md` o faktycznie wybranego dostawcę, endpoint i przesyłane
      dane oraz dodać link do jego aktualnej polityki.

## 8. UX i budżet zasobów

- [x] Zbudować natywne Qt Widgets zgodnie z `docs/UX.md`: agenda + edytor,
      stałe sterowanie, prosty licznik, rozwijane opcje audio i API.
- [x] Systemowe fonty, jasny/ciemny/systemowy motyw i wybrane lokalne ikony SVG.
- [ ] Porównać minimalny PySide6-Essentials z potrzebnymi modułami audio;
      nie dołączać całego zestawu dodatków bez sprawdzenia konieczności.
- [x] Bez WebEngine, Electron, webowego serwera i lokalnych modeli AI.
- [x] Audio/API ładowane na żądanie, odświeżanie licznika 2–4 Hz, operacje
      dyskowe i sieciowe bez blokowania interfejsu.
- [ ] Zmierzyć start, RAM, CPU i wielkość paczki na każdym systemie/architekturze.
      Cele rdzenia: start ≤3 s, RAM ≤150 MiB, CPU spoczynkowe ≤1% jednego rdzenia,
      paczka rozpakowana ≤150 MiB; opisać sprzęt i metodę pomiaru.
- [ ] Osobne pomiary audio/API i godzinnej sesji; sprawdzić brak wzrostu RAM
      proporcjonalnego do długości nagrania i responsywność podczas eksportu.
- [ ] Przetestować klawiaturę, kontrast, skalowanie DPI i długie polskie tytuły.

## 9. Wydania bez instalatora

- [x] Przygotować budowanie paczek z dołączonym Pythonem i Qt.
- [x] Windows: przenośny ZIP z programem `.exe`, bez instalatora.
- [x] macOS: przenośna aplikacja `.app` w archiwum.
- [ ] Linux: przenośna paczka z plikiem uruchamiającym i bibliotekami;
      jawnie określić wspierane dystrybucje/bazę systemową.
- [ ] Określić wspierane architektury i budować każdą paczkę na właściwej platformie.
- [x] Dodać uruchamianie wersji źródłowej oraz pomocnicze skrypty dla
      PowerShell i powłoki POSIX, korzystające z `.venv`.
- [ ] Sprawdzić paczki na systemach bez zainstalowanego Pythona i Qt.
- [ ] Udokumentować systemowe komunikaty zaufania dla niepodpisanych paczek.
- [ ] Przygotować instrukcję po polsku z formatami agendy i obsługą okien.
- [ ] Dołączyć aktualną politykę prywatności, MIT projektu i noty/licencje
      faktycznie dołączanych zależności, bibliotek audio, kodeków i ikon.

## 10. Automatyczne zrzuty ekranu / okna

- [x] Dodać wybór ekranu lub okna i interwał w sekundach zmieniany w trakcie.
- [x] Lokalny zapis PNG w wybranym katalogu, jawny start/stop i limit liczby plików.
- [x] Powiązanie zrzutów z punktami agendy i podgląd listy z otwieraniem plików.
- [x] Przechwytywanie okna jako opcjonalny moduł; bez stałego strumienia wideo.
- [x] Zatrzymanie po błędzie bez przełączenia na cały pulpit.
- [x] Test syntetycznego obrazu, limitu i metadanych; rzeczywisty test z osobnym
      syntetycznym oknem na Linux X11 zakończył się zapisem PNG.
- [ ] Rzeczywiste testy Windows/macOS, odmowy uprawnień i zachowania Waylanda.
- [ ] Pomiar CPU i rozmiaru danych przy różnych interwałach i rozdzielczościach.

## 11. Pomysły odłożone — poza pierwszą wersją

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

## 12. Poprawki użyteczności i publikacja

- [x] Czytelne zaznaczenie list rozwijanych w jasnym motywie; zwykły delegate
      listy oraz test renderowanego obrazu zaznaczenia.
- [x] Rozszerzyć parser o tabelki TSV/CSV/Markdown, godziny rozpoczęcia,
      rozwinięte jednostki i czasy w nawiasach; testy formatów i błędów.
- [x] Kompaktowy licznik ok. 260 × 138 px z podstawowymi akcjami i pełnym widokiem.
- [x] Wersja z numeru commita w oknach i pasku stanu, metadane w paczce.
- [x] Polski, angielski, niemiecki i francuski, wybór i zapamiętanie języka.
- [x] Publiczne repozytorium GitHub z opisem, aktualnym kodem i uruchomionym CI.
- [x] Uruchomić CI i zbudować pozostałe paczki na właściwych systemach.
- [x] Dołączać krótkie instrukcje `README.txt` PL/EN dopasowane do systemu
      i wariantu; na macOS obok `.app`, przed uruchomieniem.

## Aktualny stan i ograniczenia weryfikacji

- Działa prototyp z dwoma oknami; testy GUI i logiki uruchamiane lokalnie.
- Zależności zainstalowano w `.venv`; wcześniejsze problemy sieci/Git usunięte.
- Nagrywanie zweryfikowano na syntetycznym źródle, urządzenia wykryto na Linux.
  Nie wykonano przechwycenia prywatnego mikrofonu ani płatnej transkrypcji API.
- API testowano z atrapami HTTP. Rzeczywisty test wymaga klucza użytkownika.
- Zrzut osobnego okna testowego na Linux X11 działa. macOS/Windows nie były
  tutaj uruchamiane. Konfiguracja CI nie jest dowodem wykonania tych testów.
- Core/full Linux zbudowane i sprawdzone; pomiary w `docs/VALIDATION.md`.
- Windows x64, macOS ARM64 i Linux x64 przeszły testy, budowanie i diagnostykę
  paczki w CI dla wersji 6. Testy rzeczywistych urządzeń pozostają otwarte.


## 13. Urządzenia, harmonogram i warunki

- [x] Automatyczna lista urządzeń po otwarciu audio, stany ładowania/błędu.
- [x] Domyślny komunikat zamiast pustej listy transkrypcji; widoczny dostawca OpenAI.
- [x] Start całego planu o wybranej dacie/godzinie i odliczanie do startu.
- [x] Numer commita w tytule i pasku, zachowany również w paczce bez Git.
- [x] Warunki w 4 językach, checkbox wymagany przy pierwszym uruchomieniu,
      lokalna wersjonowana akceptacja oraz ponowne pytanie po zmianie treści.
- [x] Pomoc: warunki, MIT, prywatność i zweryfikowany link Buy me a coffee.
- [x] Potwierdzić ukończenie budowania Windows i macOS w Actions, podać artefakty.

Gotowe artefakty i wyniki: https://github.com/nocnystroz/MeetingAgendaTimer/actions/runs/42414000793.
Pomiar wersji 6: core 149,6 MiB na dysku, 91,8 MiB RAM, start 0,34 s;
full 269,4 MiB na dysku, 99,7 MiB RAM, start 0,42 s (Linux, krótki pomiar).

## 14. Dwujęzyczny opis projektu — PL / EN

- [x] Przygotować opis repozytorium GitHub (About) po polsku i angielsku,
      z uwzględnieniem limitu długości tego pola.
- [x] Przygotować pełną treść `README.md` w dwóch wersjach językowych:
      polskiej i angielskiej, z czytelnymi odnośnikami do obu sekcji.
- [x] Zachować równoważny zakres obu wersji: funkcje, pobieranie, uruchamianie,
      formaty agendy, prywatność, warunki, licencja, ograniczenia i wsparcie.
- [x] Zapisać w `AGENTS.md` zasadę wspólnej aktualizacji PL/EN;
      krótki angielski wstęp nie zastępuje pełnej angielskiej wersji README.
- [x] Zmienić nazwę repozytorium na `MeetingAgendaTimer`, zaktualizować origin
      oraz adresy GitHub w dokumentacji. Nazwa aplikacji pozostaje bez zmian.
- [x] Rozszerzyć GitHub Topics do 20 tematów związanych z funkcjami i platformami;
      zapisać listę w `docs/github-topics.txt`, a opis About w `docs/github-description.txt`.

Weryfikacja dokumentacji: 10 odpowiadających sobie rozdziałów PL/EN,
6 przykładów agendy sprawdzonych parserem, zgodne polecenia, poprawne linki lokalne.
About ma 338 znaków, a zdalne metadane odpowiadają zapisanym plikom.

- [x] Nazwa repozytorium bez myślników: `MeetingAgendaTimer`; aktualne linki i origin.
- [x] Osobne zrzuty angielskiego interfejsu, agendy i notatek w sekcji EN README.

Weryfikacja instrukcji paczek: 77 testów i Ruff przeszły; sprawdzono renderowanie
3 systemów × 2 wariantów oraz położenie README w archiwach z atrapami bundli
(w tym obok macOS .app). Ten test nie budował natywnych plików ani Windows ZIP.
Nowe instrukcje trafią do kolejnych paczek; istniejące wydanie v7 ich nie zawiera.

## 15. Proste paczki, pomoc i strona projektu

- [x] Windows: ZIP z jednym folderem; w jego głównym katalogu gotowy EXE
      z ikoną aplikacji, README.txt i potrzebne biblioteki w podkatalogu.
- [x] macOS: analogicznie prosta paczka z jednym folderem, aplikacją .app
      z ikoną i README.txt obok; zachować uprawnienia i strukturę pakietu.
- [x] Menu Pomoc: estetyczna instrukcja obsługi offline z obrazami,
      w języku interfejsu (PL/EN/DE/FR), czytelne linki i nawigacja.
- [x] Menu Pomoc: „Zgłoś błąd / Przekaż opinię” prowadzące do zgłoszeń GitHub.
- [x] Scalić dublujące się „Obsługa i prywatność” i „Polityka prywatności”:
      osobna instrukcja oraz jedna pozycja polityki prywatności.
- [x] Konfiguracja skrótów klawiaturowych: edycja, wykrywanie konfliktów,
      przywrócenie domyślnych, lokalne zapamiętywanie i działanie obu okien.
- [x] Utworzyć stronę projektu w sekcji Narzędzia ion301.com zgodnie z lokalnymi
      instrukcjami /home/michal/geminicli_files/ion301-content-editing/;
      dodać link w menu Pomoc i dokumentacji.
- [x] Zweryfikować pomoc, skróty, ikony i układ archiwów; zbudować paczki
      na właściwych systemach i publikować wyłącznie potwierdzone wyniki.

Weryfikacja etapu 15: wersja 14 (`c808456`), 85 testów na każdym systemie,
Ruff i diagnostyka frozen (pomoc, skróty, PDF, brak żądań sieciowych) przeszły
na Windows x64, macOS ARM64 i Ubuntu 22.04 x64.
[CI](https://github.com/nocnystroz/MeetingAgendaTimer/actions/runs/42442836434).
Sprawdzono układ ZIP i obecność natywnych ikon. Lokalny Linux core: 149,9 MiB
po rozpakowaniu; diagnostyka poza źródłami również przeszła.
Strony PL/EN opublikowane pod /pl/narzedzia/meeting-agenda-timer/
i /en/tools/meeting-agenda-timer/; sprawdzone obrazy, linki z hubów i układ
na desktopie oraz przy szerokości 390 px. Testy sprzętu/uprawnień pozostają
oddzielnymi otwartymi zadaniami.

Paczki: [wydanie testowe 14](https://github.com/nocnystroz/MeetingAgendaTimer/releases/tag/v14).
W pobranych archiwach potwierdzono commit c808456, numer 14, brak zmian
roboczych i licencje zależności; ZIP-y przeszły kontrolę CRC. W ZIP macOS
zachowane są prawa wykonywania i 140 dowiązań symbolicznych. Do wydania
dołączono SHA256SUMS; strona projektu ma bezpośrednie przyciski pobierania
Windows ZIP, macOS ARM64 ZIP i Linux tar.gz.

- [x] Poprawić About na GitHubie: narzędzie do prowadzenia spotkań według
      agendy; odliczanie dotyczy czasu punktów, zamiast określenia „licznik spotkań”.
      Zachować pełny opis PL/EN zgodny z docs/github-description.txt.

## 16. Doprecyzowanie opisu i skróty globalne

- [ ] Opis PL/EN: odliczanie czasu pozostałego do końca poszczególnych punktów
      agendy spotkania. Wyraźne oznaczenie beta na stronie, GitHubie i w README.
- [ ] Link do projektu w górnym menu Narzędzia/Tools w PL/EN oraz poprawione
      opisy kart na hubach, tytuły i opisy metadanych strony.
- [ ] Globalne skróty sterowania działające, gdy aplikacja jest uruchomiona,
      również przy aktywnym oknie prezentacji: poprzedni/następny punkt,
      pauza/wznowienie, +1/+5 minut. Konfigurowalne, mniej kolizyjne domyślne
      kombinacje, widoczne konflikty i ograniczenia systemowe.
- [ ] Zwolnić rejestracje skrótów przy wyjściu; zaktualizować instrukcje PL/EN/DE/FR
      i sprawdzić działanie przy aktywnym innym oknie, bez przejmowania fokusu.
