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
- Agenda i ustawienia pozostają lokalne. Nie wymagać konta ani połączenia
  z internetem do korzystania z aplikacji.

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

## Stan początkowy

Repozytorium nie zawiera jeszcze implementacji. Utworzono `.venv`.
Próba pobrania PySide6 nie powiodła się z powodu niedostępności DNS/sieci
do PyPI w bieżącym środowisku. GTK jest dostępne lokalnie, ale nie realizuje
przyjętego kierunku aplikacji wieloplatformowej. Nie oznaczać instalacji
zależności ani uruchomienia interfejsu jako ukończonych.

Po zmianie uprawnień ponowiona próba `git init` zakończyła się powodzeniem.
Repozytorium używa gałęzi `main`; zapis metadanych Git jest już dostępny.
