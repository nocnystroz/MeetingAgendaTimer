# Walidacja wersji 0.1

Data: 2026-11-07. Tylko wykonane lokalnie próby, bez deklarowania wsparcia
platform na podstawie samego kodu lub konfiguracji CI.

## Wykonane

- Linux x86_64, X11/XFCE, host z glibc 2.43; Python 3.13.14, Qt/PySide6 6.12.0.
- 77 testów logiki/GUI/audio/API/zrzutów przeszło. GUI testowano także na
  offscreen; nie zastępuje to testów integracji z menedżerem okien.
- Rzeczywisty panel i licznik wyświetlono na pulpicie Linux.
- Zasobnik wykryty jako dostępny na tym pulpicie.
- Qt WindowCapture zapisał PNG osobnego, syntetycznego okna procesu testowego
  i zatrzymał cykl po limicie jednego zrzutu. Nie przechwytywano prywatnych okien.
- WAV testowano na syntetycznych danych; fizyczne źródła audio wykryto,
  ale nie nagrywano prywatnego mikrofonu ani dźwięku użytkownika.
- API sprawdzono na atrapach, w tym kody błędów, anulowanie przed wysyłką,
  limit i strumieniowanie. Nie użyto rzeczywistego klucza ani płatnego żądania.

## Pomiary lokalne — wersja 6

Linux x86_64 / XFCE / X11. Paczka uruchomiona z tymczasowego katalogu danych,
poza źródłami i bez venv. Pomiar procesu przez /proc, 10 s spoczynku po starcie,
z ciepłą pamięcią podręczną. Do katalogu testowego wpisano syntetyczną akceptację
warunków, aby mierzyć sam start panelu; nie zmieniano zgody użytkownika.
Nie jest to pomiar godzinnej sesji/audio/API ani szczytu pamięci podczas startu.

| Wariant | Start | RAM RSS | CPU jednego rdzenia | Rozpakowana paczka |
| --- | --- | --- | --- | --- |
| Core | 0,34 s | 91,8 MiB | 0,7% | 149,6 MiB |
| Full | 0,42 s | 99,7 MiB | 0,6% | 269,4 MiB |

Cele rdzenia start/RAM/CPU/rozmiar spełnione na tym hoście. Full ma większą
paczkę przez audio, NumPy i Qt Multimedia; nie przypisujemy mu wyniku core.
Paczki obu wariantów przeszły diagnostykę GUI, PDF, języków, zasobów warunków
oraz modułów poza katalogiem źródeł i bez venv.

Na rzeczywistym pulpicie Linux potwierdzono włączanie/wyłączanie stanu ABOVE,
minimalizację, schowanie do zasobnika i przywrócenie. Po poprawkach wykryto
2 mikrofony i 4 źródła loopback (listy zawierają też opcję braku wyboru),
a kompaktowy licznik miał rzeczywiste wymiary 260 × 138 px.

## CI trzech systemów

[Przebieg dla wersji 6](https://github.com/nocnystroz/licznik-spotkaniowy/actions/runs/42414000793)
zakończył się sukcesem dla wszystkich trzech zadań:

- Windows x64: testy, ZIP bez instalatora i uruchomienie spakowanego GUI.
- macOS ARM64: testy, archiwum .app i uruchomienie spakowanego GUI.
- Ubuntu 22.04 x64: testy, tar.gz i uruchomienie spakowanego GUI.

Każdy wariant przeszedł 77 testów źródeł oraz diagnostykę frozen poza źródłami.
Macierz korzysta z Pythona 3.13; wersja patch może różnić się od lokalnej.
Nie oznacza to testu fizycznego mikrofonu, prawdziwego API, platformowych
uprawnień ani każdego środowiska graficznego. Te elementy pozostają otwarte.
Pierwszy przebieg wykrył problem wyrównania OpenBLAS po strip na Ubuntu;
pełna paczka Linux zachowuje teraz oryginalne biblioteki i przeszła ponowny test.

## Otwarte

- Rzeczywiste testy urządzeń audio, klucza API i uprawnień na fizycznym Windows/macOS.
- Wayland, wiele monitorów/DPI i zamykanie/minimalizacja przechwytywanego okna.
- Godzinna sesja z nagrywaniem oraz długie notatki i brak miejsca na dysku.
- Paczki na czystych systemach bez Pythona/Qt i kompletność zależności natywnych.
- Weryfikacja not/licencji konkretnego artefaktu przed publiczną dystrybucją.
