# Polityka prywatności — projekt przed implementacją

Data: 2026-11-07.

Ten dokument opisuje przyjęty sposób przetwarzania danych w planowanej
aplikacji Licznik spotkaniowy. Obecnie repozytorium zawiera dokumentację,
bez działającej aplikacji. Poniższe zasady są wymaganiami dla przyszłej
implementacji; przed wydaniem należy sprawdzić ich zgodność z kodem i uzupełnić
informacje o wybranym dostawcy API. Dokument nie potwierdza zgodności
z konkretnymi przepisami ani zasadami organizacji użytkownika.

## Dane lokalne

Aplikacja ma przechowywać na urządzeniu użytkownika:

- agendę, czasy i zmiany punktów;
- notatki przygotowawcze i sporządzane podczas spotkania;
- decyzje, zadania, wskazane osoby i terminy;
- szablony, ustawienia i dane odzyskiwania bieżącej sesji;
- nagrania, znaczniki czasu, otrzymane transkrypcje i eksporty.

Autor aplikacji nie prowadzi w planowanej architekturze serwera odbierającego
te dane. Podstawowe funkcje nie wymagają konta, telemetrii ani sieci.
Nie planuje się automatycznego raportowania awarii zawierającego treści spotkań.
Przechowywanie na dysku nie oznacza automatycznego szyfrowania plików.
Inni użytkownicy urządzenia, kopie zapasowe lub synchronizacja folderów
mogą wpływać na dostępność danych poza aplikacją.

## Nagrywanie

Nagrywanie zaczyna się po działaniu użytkownika. Program ma pokazać źródła,
stan nagrania i jego czas, także w zasobniku po schowaniu okna. Uprawnienia
systemu do mikrofonu/przechwytywania dźwięku nie zastępują decyzji o rozpoczęciu.

Użytkownik powinien poinformować uczestników i upewnić się, że nagrywanie
oraz ewentualna wysyłka do dostawcy są dozwolone w jego sytuacji i organizacji.
Nagranie może obejmować głosy innych osób oraz dźwięki z wybranego źródła
systemowego, również niezwiązane ze spotkaniem.

Pauza licznika nie zatrzymuje automatycznie nagrania. Stan i kontrolki nagrywania
muszą być osobne. Nagrywanie ekranu nie należy do zakresu pierwszej wersji.

## Opcjonalna transkrypcja poza urządzeniem

Transkrypcja przez API będzie wyłączona bez konfiguracji i osobnego zlecenia.
Wprowadzenie klucza nie stanowi zlecenia wysyłki.

Przed każdym nowym zleceniem program ma wskazać dostawcę, wybrany plik,
zakres danych i możliwość naliczenia opłat na koncie użytkownika. Wysyłane
ma być potrzebne audio i techniczne parametry zadania, a nie agenda, notatki
czy zadania. Dostawca otrzyma także informacje konieczne do obsługi połączenia
i uwierzytelnienia. Program nie ma pośredniczyć przez serwer autora.

Dostawca i model nie zostały wybrane. Przed udostępnieniem funkcji trzeba
w tym dokumencie podać usługę, endpoint, faktyczny zakres danych, odnośniki
do polityki i zasad retencji oraz sposób ewentualnego usuwania danych u dostawcy.
Nie zakładać zerowej retencji, konkretnej lokalizacji danych ani zakazu ich
używania do treningu bez sprawdzenia warunków usługi i konta.

Anulowanie może zatrzymać dalszą wysyłkę lub oczekiwanie, lecz nie cofnie
danych już przekazanych ani nie gwarantuje anulowania kosztu. Ponowne wysłanie
może wiązać się z kolejną opłatą; nie będzie wykonywane automatycznie.

## Klucze API

Domyślnie klucz ma pozostawać w pamięci bieżącej sesji. Opcjonalne zapamiętanie
ma korzystać wyłącznie z magazynu poświadczeń systemu. Jeśli nie jest dostępny,
pozostaje tryb sesyjny. Klucze nie mogą trafiać do plików spotkania, szablonów,
eksportów, repozytorium ani logów. Użytkownik musi móc usunąć zapamiętany klucz;
jego unieważnienie następuje w panelu dostawcy API.

## Zapis, eksport i usuwanie

Dokładne katalogi danych zostaną opisane po implementacji dla każdego systemu.
Program ma pokazywać lokalizację plików i umożliwiać usunięcie danych sesji,
notatek, nagrania, transkrypcji oraz plików odzyskiwania. Dane lokalne pozostają
do usunięcia przez użytkownika; nie planuje się automatycznej wysyłki lub archiwum.
Pliki tymczasowe transkrypcji należy usuwać po zakończeniu/anulowaniu zadania.

Eksporty Markdown/PDF i kopie zapisane poza katalogiem aplikacji wymagają
osobnego usunięcia. Usunięcie lokalnego pliku nie usuwa jego kopii zapasowych
ani danych wcześniej przekazanych zewnętrznemu dostawcy. Zwykłe usunięcie
nie gwarantuje nieodwracalnego wymazania danych z nośnika.

## Widoki i integracje

Widok do udostępniania ma pokazywać licznik i tytuł, bez notatek i sekretów.
Sam tytuł punktu także może być poufny — użytkownik wybiera udostępniane okno.
Przełączenie okna w aplikacji nie zmienia automatycznie wyboru w komunikatorze.

Integracje Microsoft 365/Google Workspace oraz archiwum spotkań nie są
planowane w pierwszej wersji. Ich dodanie wymaga aktualizacji tej polityki.
