# Polityka prywatności — Licznik spotkaniowy 0.1

Data: 2026-11-07.

Ten dokument opisuje lokalny prototyp aplikacji Licznik spotkaniowy.
Zakres testów i ograniczenia są opisane w `docs/VALIDATION.md`. Przed publicznym
wydaniem należy ponownie sprawdzić zgodność dokumentu z kodem i konfiguracją
konkretnych paczek. Nie stanowi on potwierdzenia zgodności z przepisami ani
zasadami organizacji użytkownika.

## Dane lokalne

Aplikacja przechowuje na urządzeniu użytkownika:

- agendę, czasy i zmiany punktów;
- notatki przygotowawcze i sporządzane podczas spotkania;
- decyzje, zadania, wskazane osoby i terminy;
- szablony, ustawienia i dane odzyskiwania bieżącej sesji;
- nagrania, znaczniki czasu, otrzymane transkrypcje i eksporty;
- automatyczne zrzuty ekranu/okna PNG z czasem wykonania i powiązaniem z punktem.

Autor aplikacji nie prowadzi w obecnej architekturze serwera odbierającego
te dane. Podstawowe funkcje nie wymagają konta, telemetrii ani sieci.
Nie planuje się automatycznego raportowania awarii zawierającego treści spotkań.
Przechowywanie na dysku nie oznacza automatycznego szyfrowania plików.
Inni użytkownicy urządzenia, kopie zapasowe lub synchronizacja folderów
mogą wpływać na dostępność danych poza aplikacją.

## Nagrywanie

Nagrywanie zaczyna się po działaniu użytkownika. Program pokazuje źródła,
stan nagrania i jego czas, także w zasobniku po schowaniu okna. Uprawnienia
systemu do mikrofonu/przechwytywania dźwięku nie zastępują decyzji o rozpoczęciu.

Użytkownik powinien poinformować uczestników i upewnić się, że nagrywanie
oraz ewentualna wysyłka do dostawcy są dozwolone w jego sytuacji i organizacji.
Nagranie może obejmować głosy innych osób oraz dźwięki z wybranego źródła
systemowego, również niezwiązane ze spotkaniem.

Pauza licznika nie zatrzymuje automatycznie nagrania. Stan i kontrolki nagrywania
muszą być osobne. Nagrywanie ekranu nie należy do zakresu pierwszej wersji.

## Opcjonalna transkrypcja poza urządzeniem

Transkrypcja przez API nie uruchamia się bez klucza i osobnego zlecenia.
Wprowadzenie klucza nie stanowi zlecenia wysyłki.

Przed każdym nowym zleceniem program ma wskazać dostawcę, wybrany plik,
zakres danych i możliwość naliczenia opłat na koncie użytkownika. Wysyłane
ma być potrzebne audio i techniczne parametry zadania, a nie agenda, notatki
czy zadania. Dostawca otrzyma także informacje konieczne do obsługi połączenia
i uwierzytelnienia. Program nie ma pośredniczyć przez serwer autora.

Dostawca: OpenAI. Domyślny model: `gpt-transcribe`.
Endpoint: `https://api.openai.com/v1/audio/transcriptions`.
Przekazywane są audio, klucz w nagłówku uwierzytelnienia, nazwa modelu oraz
informacje techniczne połączenia. Plik ma ogólną nazwę `audio.*` w żądaniu;
oryginalna nazwa pliku, agenda i notatki nie są wysyłane. Zrzuty PNG również
nie są wysyłane. Dłuższe WAV dzielone są lokalnie na części do 5 minut i
przygotowywane jako PCM mono 16 kHz. Dla plików skompresowanych obowiązuje
limit wysyłki 24 MB. Każdy fragment jest osobnym żądaniem.

Zasady przetwarzania i retencji zależą od usługi i ustawień konta:
[OpenAI — data controls](https://developers.openai.com/api/docs/guides/your-data).
Użytkownik powinien sprawdzić aktualne warunki przed wysyłką. Aplikacja nie
zapewnia zerowej retencji, określonego regionu ani usuwania danych po stronie
OpenAI. Może usunąć jedynie dane lokalne. Nie dokonano rzeczywistej wysyłki
w ramach lokalnej walidacji prototypu.

Anulowanie może zatrzymać dalszą wysyłkę lub oczekiwanie, lecz nie cofnie
danych już przekazanych ani nie gwarantuje anulowania kosztu. Ponowne wysłanie
może wiązać się z kolejną opłatą; nie będzie wykonywane automatycznie.

## Klucze API

Domyślnie klucz pozostaje w pamięci bieżącej sesji. Opcjonalne zapamiętanie
korzysta wyłącznie z magazynu poświadczeń systemu. Jeśli nie jest dostępny,
pozostaje tryb sesyjny. Klucze nie mogą trafiać do plików spotkania, szablonów,
eksportów, repozytorium ani logów. Użytkownik musi móc usunąć zapamiętany klucz;
jego unieważnienie następuje w panelu dostawcy API.

## Zapis, eksport i usuwanie

Katalog danych: Linux `$XDG_DATA_HOME/licznik-spotkaniowy` albo
`~/.local/share/licznik-spotkaniowy`; Windows `%LOCALAPPDATA%/licznik-spotkaniowy`;
macOS `~/Library/Application Support/licznik-spotkaniowy`. Zmienna
`MEETING_TIMER_DATA_DIR` pozwala wskazać inny katalog. Menu Spotkanie umożliwia
jego otwarcie. Domyślne podkatalogi to `recordings`, `screenshots` i `transcripts`.
Użytkownik może wybrać inne katalogi nagrań/zrzutów i miejsca eksportu.

`session.json` zawiera aktualną sesję, ustawienia i dane odzyskiwania.
`session-before-open.json` lub `session-discarded.json` mogą zachowywać
poprzedni stan, a `session-damaged-*.json` nieczytelne dane. Nie jest to
archiwum spotkań. Aby usunąć dane, zamknij aplikację i usuń odpowiednie pliki
w katalogu danych oraz wybranych miejscach nagrań, zrzutów i eksportów.
Zapamiętany klucz usuwa się przyciskiem Usuń klucz lub w magazynie systemu.
Unieważnienie klucza następuje u dostawcy.

Dane pozostają na dysku do usunięcia przez użytkownika. Limit liczby zrzutów
zatrzymuje zapis, ale nie usuwa poprzednich PNG. Tymczasowe fragmenty audio
w `.transcription-cache/job-*` są usuwane po zakończeniu/anulowaniu zadania;
pozostałości po awarii są sprzątane przy następnym uruchomieniu, jeśli pozwalają
na to prawa zapisu. Odebrane fragmenty transkrypcji pozostają w `transcripts`
także po niedokończeniu całego zadania.

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

## Automatyczne zrzuty

Start wymaga osobnego potwierdzenia źródła, interwału i limitu. Zamykanie
panelu ustawień nie zatrzymuje cyklu; stan pozostaje widoczny w panelu
prowadzącego i zasobniku. Zakończenie programu zatrzymuje zrzuty. Brak obrazu
zatrzymuje cykl bez przełączenia na cały ekran. PNG mogą zawierać treści innych
aplikacji, dane osób trzecich i tytuły okien. Użytkownik wybiera źródło i odpowiada
za to, co utrwala. Program nie analizuje, nie redaguje i nie szyfruje tych obrazów.
Nie są wysyłane do API. Nagrywanie wideo pozostaje poza zakresem tej wersji.
