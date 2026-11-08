# Licznik spotkaniowy — ustalenia projektu

## Cel

Desktopowy program do prowadzenia spotkania według wklejonej agendy. Osobne
okno pokazuje tytuł aktualnego punktu i czas pozostały do jego zakończenia.
Interfejs i komunikaty domyślnie po polsku.

## Wymagania użytkownika

- Obsługa Windows, macOS i Linux.
- Wklejanie agendy jako tekstu, rozpoznanie punktów i przypisanych czasów.
- Osobne okno odliczania z tytułem bieżącego punktu.
- Przełączana opcja „Zawsze na wierzchu”.
- Minimalizacja do paska oraz niezależna możliwość schowania do zasobnika
  systemowego; na macOS odpowiednik w pasku menu i Docku.
- Przywracanie okna z zasobnika oraz jawna opcja zakończenia programu.
- Uruchamianie bez instalatora. Użytkownik dopuszcza uruchamianie przez Python
  lub PowerShell. PowerShell dotyczy sposobu uruchomienia na Windows;
  aplikacja ma działać również na pozostałych systemach.
- Środowisko programistyczne: lokalne Python `.venv`, bez commitowania do Git.
- Utrzymywanie planu w `ROADMAP.md` oraz commitowanie ukończonych fragmentów pracy.
- Notatki do poszczególnych punktów: tworzenie przed spotkaniem, edycja
  i podgląd podczas spotkania.
- Nagrywanie spotkania, inspirowane projektem
  `/home/michal/geminicli_files/audio-rozkminka/`.
- Opcjonalna transkrypcja po podłączeniu przez użytkownika własnego klucza API.
- Dodawanie czasu (+1/+5 minut), godzina końca i opóźnienie względem planu.
- Decyzje i zadania z osobą odpowiedzialną oraz terminem przy punktach agendy.
- Eksport podsumowania do Markdown i PDF.
- Znaczniki łączące punkty agendy z pozycjami w nagraniu i transkrypcji.
- Oddzielny widok prowadzącego i widok licznika do udostępniania.
- Zmiana agendy, ustawień i przełączanie widoków podczas spotkania.
- Lekka aplikacja: mały narzut pamięci, CPU, zależności i rozmiaru paczek.
- Motyw ciemny, jasny i domyślny systemowy. Wybór zapamiętywany lokalnie;
  systemowy reaguje na zmianę schematu systemu, jeśli platforma go udostępnia.
- Wersja aplikacji: numer commita (git rev-list --count HEAD), widoczny w tytułach okien i pasku
  stanu; zapisany w paczce przenośnej podczas budowania.
- Dokumentacja: `README.md`, `PRIVACY.md` i `LICENSE`; licencja MIT
  wybrana przez użytkownika.
- Lokalne szablony agendy, odzyskiwanie po awarii, opcjonalny sygnał końca
  oraz tryb przekroczenia czasu zamiast automatycznego przejścia.
- Historia spotkań oraz integracje Microsoft 365/Google Workspace odłożone
  na później; nie są zależnością pierwszej wersji ani warunkiem jej testowania.

## Przyjęte założenia implementacyjne

Poniższe rozwiązania są propozycją techniczną, a nie dodatkowymi wymaganiami użytkownika.

- Python i PySide6/Qt jako wspólna baza interfejsu dla trzech systemów.
  Nie wybierać GTK jako docelowej technologii, ponieważ priorytetem jest
  obsługa wszystkich trzech systemów.
- Wersja przenośna zawiera interpreter i biblioteki: użytkownik nie musi
  instalować Pythona, tworzyć venv ani uruchamiać pip. Osobny artefakt dla
  każdego systemu i obsługiwanej architektury; nie zakładać jednego pliku
  wykonywalnego działającego na wszystkich platformach.
- Uruchamianie źródeł przez Python pozostaje ścieżką dla programisty lub
  użytkownika mającego interpreter. Zależności instaluje się do `.venv`.
- Opcjonalny skrypt PowerShell służy do uruchomienia na Windows, bez
  zmieniania globalnej polityki wykonywania skryptów.
- Obsłużyć co najmniej `Omówienie wyników — 15 min` oraz
  `10:00–10:15 Omówienie wyników`. Przed startem pokazać podgląd interpretacji.
- Błędnych i nierozpoznanych wierszy nie pomijać po cichu: pokazać ich numery
  i wskazówkę poprawy. Nie wymagać zewnętrznej usługi AI do parsowania.
- Dla czasów trwania odliczać od naciśnięcia Start. Dla agendy godzinowej
  wyraźnie rozróżnić harmonogram według zegara i realizację od teraz.
- Zaplanować pauzę/wznowienie, restart, poprzedni/następny punkt oraz
  automatyczne przejście do następnego punktu po upływie czasu.
- Agenda, notatki, ustawienia i nagrania pozostają lokalne. Odliczanie,
  notatki i nagrywanie nie wymagają konta ani internetu. Wyjątkiem jest
  dobrowolna transkrypcja przez wybrane API.

## Notatki, zmiany na żywo i eksport

- Każdy punkt otrzymuje stały identyfikator. Zmiana nazwy lub kolejności
  nie może przepinać notatek, decyzji, zadań ani znaczników do innego punktu.
- Podgląd notatek innego punktu nie przełącza bieżącego punktu odliczania.
- Zmiany nazwy, notatek, kolejności i przyszłych punktów są możliwe w trakcie.
  Usunięcie bieżącego punktu wymaga wskazania następcy; jego dane pozostają
  w historii spotkania. Ponowne wklejenie agendy nie nadpisuje po cichu notatek.
- +1/+5 minut wydłuża punkt i pozostały plan. Pokazywać plan pierwotny
  i plan po zmianach. Ręczne przejście jest osobną akcją od wyboru do edycji.
- Pauza licznika nie pauzuje nagrania. Znaczniki wiązać z rzeczywistą pozycją
  w pliku, również po pauzach i wielokrotnych powrotach do tego samego punktu.
- Eksport obejmuje wybrane przez użytkownika notatki, decyzje i zadania.
  Nigdy nie zawiera kluczy API. Zapis i eksport nie wymagają serwera.
- Tryb zakończenia punktu wybierany podczas spotkania: automatyczne przejście
  lub pozostanie na punkcie z licznikiem przekroczenia, np. `+02:30`.
- Opcjonalny sygnał końca domyślnie wyłączony, możliwy do zmiany w trakcie.
- Lokalne szablony zapisują agendę i opcjonalne notatki przygotowawcze;
  nie kopiują nagrań, transkrypcji, wykonanych zadań ani kluczy API.
- Odzyskiwanie dotyczy bieżącego spotkania. Nie oznacza budowania archiwum
  spotkań. Po awarii zaproponować odzyskanie, bez automatycznego wznowienia
  nagrania lub wysyłania do API.

## Nagrywanie i transkrypcja

- Projekt referencyjny sprawdzono jako inspirację funkcjonalną: mikrofon
  i dźwięk spotkania, osobne poziomy głośności, kanały rozdzielone lub miks,
  lokalny zapis oraz widoczny czas nagrania. Nie kopiować kodu bez sprawdzenia
  jego licencji i nie przenosić identyfikatorów urządzeń autora.
- Rozdzielić przechwytywanie mikrofonu od dźwięku systemowego. Wybór urządzeń,
  podgląd poziomów i test przed nagraniem; żadnego automatycznego nagrywania.
- Dźwięk systemowy wymaga osobnych backendów i testów na Windows, macOS
  i Linux. Brak tej możliwości nie blokuje licznika i notatek. Nie zakładać,
  że linuxowe skrypty PulseAudio/PipeWire działają na pozostałych systemach.
- Użytkownik widzi stan nagrywania również po schowaniu okna. Obsłużyć
  odmowę uprawnień, odłączenie urządzenia, brak miejsca i bezpieczne zamknięcie.
- Transkrypcja pierwszej wersji: wybrane, zakończone nagranie; streaming
  nie jest wymaganiem. Dostawca i model API pozostają do wybrania.
- Podanie klucza nie wysyła danych. Przed wysłaniem pokazać plik, dostawcę
  i zakres przesyłanych danych; wysyłać tylko po osobnej akcji użytkownika.
- Klucz domyślnie tylko w pamięci sesji. Opcjonalny zapis wyłącznie
  w systemowym magazynie poświadczeń; bez działającego magazynu tryb sesyjny.
- Nie umieszczać kluczy, audio i treści spotkań w logach. Nie wysyłać
  notatek i agendy do transkrypcji bez odrębnej, uzasadnionej funkcji.
- Obsłużyć timeout, anulowanie, limit wielkości pliku, błąd klucza i limity API;
  nie powtarzać automatycznie żądań mogących spowodować kolejne opłaty.

## UX i lekkość

- Szczegółowy kierunek UX i przegląd bibliotek: `docs/UX.md`.
- Panel prowadzącego: agenda po lewej, notatki/decyzje/zadania po prawej,
  sterowanie spotkaniem w stałym miejscu; nagrywanie i API w rozwijanym panelu.
- Okno licznika: tytuł, duże cyfry, postęp i następny punkt. Bez notatek,
  transkrypcji, kluczy i nazw prywatnych plików; ten widok można udostępniać.
- Jasny/ciemny/systemowy motyw, kompaktowy/pełny widok oraz przypinanie
  przełączane w trakcie, bez restartu i resetowania odliczania/nagrywania.
- Natywne Qt Widgets, systemowe fonty, mały własny QSS i wybrane ikony SVG.
  Bez Electron, WebEngine, serwera WWW, lokalnych modeli AI i frameworka WWW.
- Rozważyć PySide6-Essentials dla rdzenia. Dodatkowe moduły/audio ładować
  dopiero przy użyciu i pakować wyłącznie potrzebne składniki.
- Odświeżanie licznika 2–4 razy na sekundę; brak aktywnego odpytywania sieci.
  Audio zapisywać strumieniowo, bez trzymania całego nagrania w RAM.
- Cele początkowe, jeszcze niezmierzone: start do 3 s, RAM rdzenia do 150 MiB,
  CPU spoczynkowe średnio do 1% jednego rdzenia, paczka rdzenia do 150 MiB
  po rozpakowaniu na platformę/architekturę. Mierzyć także osobno audio/API;
  raportować przekroczenia zamiast deklarować lekkość bez pomiaru.
- Do paczek dołączać licencje zależności; MIT projektu nie zmienia licencji Qt,
  kodeków ani ikon.

## Automatyczne zrzuty ekranu / okna

- Zapis PNG co wskazaną liczbę sekund, z wyborem ekranu albo konkretnego okna.
- Jawny start/stop, zmiana interwału w trakcie i limit liczby plików.
- Pliki wyłącznie lokalne, z czasem wykonania i stałym identyfikatorem punktu.
  Nie wysyłać obrazów do transkrypcji ani innej usługi bez osobnej funkcji.
- Zrzut ekranu korzysta z QtGui. Wybrane okno korzysta z opcjonalnego
  QtMultimedia, uruchamianego tylko na czas pobrania pojedynczej klatki.
- Brak obrazu lub uprawnień zatrzymuje cykl. Nie przełączać automatycznie
  wybranego okna na przechwytywanie całego pulpitu.
- Zamykanie panelu zrzutów nie zatrzymuje cyklu; stan jest widoczny w głównym
  oknie i zasobniku. Przy wyjściu zatrzymać cykl i dokończyć zapis obrazu.
- Nagrywanie wideo pozostaje poza zakresem; zrzuty to osobna funkcja.

## Poza pierwszą wersją

- Nagrywanie wideo wybranego monitora/okna: pomysł do oceny, bez decyzji o wdrożeniu.
  Ewentualny osobny moduł ładowany na żądanie, pomiary CPU/GPU/dysku,
  synchronizacja z audio i osobne testy uprawnień każdego systemu.
- Historia spotkań, wyszukiwanie w archiwum oraz integracje Microsoft 365
  i Google Workspace: ewentualny przyszły etap. Nie wymagać kont ani testów
  w tych środowiskach dla obecnego zakresu.

## Zasady pracy i weryfikacji

- Oddzielić parser agendy i logikę czasu od interfejsu oraz integracji systemowych.
- Obliczać pozostały czas na podstawie zegara, nie przez odejmowanie sekundy
  przy każdym odświeżeniu. Przetestować pauzę, opóźnienia odświeżania,
  koniec agendy, przerwy między punktami i przejście przez północ.
- Ustalić i opisać zachowanie pauzy oraz ręcznego przechodzenia w trybie
  harmonogramu godzinowego, zanim ten tryb zostanie uznany za gotowy.
- Gdy zasobnik nie jest dostępny, nie ukrywać jedynego sposobu dostępu
  do aplikacji; zapewnić minimalizację i czytelny komunikat.
- Zapisywać dane w katalogu danych użytkownika, aby aplikacja mogła
  działać z katalogu bez praw zapisu. Zapisywać atomowo.
- Nie commitować `.venv`, cache, danych użytkownika ani wyników budowania.
- W `ROADMAP.md` oznaczać jako wykonane tylko rzeczy rzeczywiście ukończone.
- Testy logiki nie zastępują testów okien, zasobnika i paczek na każdym systemie.
- Nie deklarować sprawdzenia systemu lub architektury bez rzeczywistego testu.
- Commitować spójne ukończone etapy; nie publikować ani nie wysyłać zmian
  do zdalnego repozytorium bez polecenia użytkownika.

## Stan implementacji

Działa prototyp Python/Qt: parser, silnik czasu, dwa okna, lokalne notatki,
decyzje/zadania, eksport, szablony i odzyskiwanie. Audio i transkrypcja
są opcjonalne i ładowane na żądanie; API testowano na atrapach. Przechwycenie
osobnego syntetycznego okna na Linux X11 zakończyło się zapisem PNG.
Szczegóły i nieukończone testy: `ROADMAP.md` oraz `docs/VALIDATION.md`.

Zależności zainstalowano w `.venv`. Repozytorium działa na gałęzi `main`.
Wcześniejsze błędy sieci i zapisu Git nie są aktualną blokadą.

## Rozszerzenie językowe

Użytkownik zamówił polski, angielski, niemiecki i francuski. Najpierw ukończyć
poprawki kontrastu list, formatów agendy i rozmiaru trybu kompaktowego, następnie
dodać języki i zbudować paczki pozostałych systemów. Repozytorium GitHub ma
być publiczne; użytkownik zezwolił na publikację i opis repozytorium.

## Dalsze wymagania użytkownika

- Wybrana data i godzina rozpoczęcia całego planu, niezależnie od godzin w agendzie.
- Automatyczne wykrywanie źródeł po otwarciu panelu audio; widoczne stany ładowania
  i błędu, a nie pusta lista. Informacja o braku zapisanych transkrypcji i dostawcy API.
- Warunki użytkowania w Pomocy oraz obowiązkowa akceptacja przy pierwszym
  uruchomieniu. Nagrywając i robiąc zrzuty użytkownik oświadcza, że ma zgodę
  uczestników i wymagane uprawnienia. Akceptacja lokalna, wersjonowana treścią.
- W Pomocy: MIT, polityka prywatności i https://buymeacoffee.com/m.slawinski
  (adres zweryfikowany w README projektu referencyjnego).
- Repozytorium publiczne: https://github.com/nocnystroz/MeetingAgendaTimer.
  Publikacja i budowanie Windows/macOS przez GitHub Actions są autoryzowane.

## Dokumentacja PL / EN

- `README.md` zawiera pełne, równoważne sekcje polską i angielską,
  z odnośnikami do obu wersji na początku pliku.
- Zmieniając funkcje, instrukcje lub ograniczenia w README, aktualizować obie
  sekcje w tym samym etapie pracy. Krótki angielski wstęp nie zastępuje tłumaczenia.
- Opis GitHub About jest dwujęzyczny (PL / EN), mieści się w limicie 350 znaków
  i odpowiada treści zapisanej w `docs/github-description.txt`.
- Repozytorium nazywa się `MeetingAgendaTimer`; nazwy aplikacji i jej katalogu
  danych pozostają bez zmian. GitHub Topics odpowiadają `docs/github-topics.txt`.
- Opis i README odróżniają zaimplementowane funkcje od testów rzeczywistego
  sprzętu oraz testów z atrapami. Nie rozszerzać deklaracji wsparcia platform
  lub dostępności paczek ponad potwierdzone wyniki.

- Zrzuty w polskiej części README pokazują polski interfejs, a w angielskiej
  angielski interfejs oraz angielską przykładową agendę i notatki.

## Instrukcje w paczkach przenośnych

- Każda paczka Windows, macOS i Linux zawiera własne krótkie `README.txt`
  w językach PL/EN, dostępne bez internetu i dobrane automatycznie przy budowaniu.
- Instrukcja leży obok pliku wykonywalnego, a na macOS obok `.app`, tak aby
  można ją było przeczytać przed uruchomieniem. Pełne README projektu pozostaje
  dołączone jako dokumentacja szczegółowa.
- Opisać rozpakowanie całego archiwum, właściwy plik do uruchomienia,
  wymagania danego systemu, uprawnienia mikrofonu i przechwytywania obrazu,
  lokalizację danych oraz link do pełnej dokumentacji i wydań.
- Uwzględnić brak podpisu/notaryzacji, jeśli dotyczy danej paczki, bez zalecania
  globalnego wyłączania zabezpieczeń systemu; nie wymagać instalowania Pythona.
- Instrukcje rozróżniają warianty core/full oraz potwierdzone architektury
  i ograniczenia. Zmieniając sposób pakowania, aktualizować obie wersje językowe.

## Uproszczenie paczek i Pomocy

- Windows: ZIP z jednym folderem, w nim EXE z ikoną aplikacji w głównym katalogu.
  macOS: ZIP z jednym folderem zawierającym .app z ikoną i README.txt obok.
- Pomoc offline ze zrzutami i nawigacją w języku interfejsu (PL/EN/DE/FR).
  Menu zawiera jedną politykę prywatności, warunki, licencję, zgłoszenia GitHub,
  wsparcie oraz stronę projektu w sekcji Narzędzia ion301.com.
- Skróty klawiaturowe konfigurowalne, z wykrywaniem konfliktów, wyłączaniem
  i przywracaniem domyślnych; zapis w shortcuts.json, działanie obu okien.
- Strony projektu: /pl/narzedzia/meeting-agenda-timer/ i /en/tools/meeting-agenda-timer/.
  Zgłoszenia otwierać w przeglądarce bez automatycznej wysyłki danych.
