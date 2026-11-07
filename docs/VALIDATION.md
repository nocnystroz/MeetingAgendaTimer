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

## Pomiary lokalne (wcześniejszy prototyp przed ostatnimi zmianami UI)

Linux x86_64 / XFCE / X11. Paczka uruchomiona z tymczasowego katalogu danych,
poza źródłami i bez venv. Pomiar procesu przez /proc, 10 s spoczynku po starcie,
z ciepłą pamięcią podręczną. Nie jest to pomiar godzinnej sesji/audio/API.

| Wariant | Start | RAM RSS | CPU jednego rdzenia | Rozpakowana paczka |
| --- | --- | --- | --- | --- |
| Core | 0,42 s | 83,7 MiB | 0,6% | 148,9 MiB |
| Full | 0,28 s | 95,3 MiB | 0,7% | 251,0 MiB |

Paczki obu wariantów przeszły diagnostykę GUI, PDF i modułów poza źródłami.
Po dodaniu języków, warunków i ostatnich poprawek paczki wymagają ponownego
zbudowania. CI oraz aktualne artefakty: https://github.com/nocnystroz/licznik-spotkaniowy/actions.

Na rzeczywistym pulpicie Linux potwierdzono włączanie/wyłączanie stanu ABOVE,
minimalizację, schowanie do zasobnika i przywrócenie. Po poprawkach wykryto
2 mikrofony i 4 źródła loopback (listy zawierają też opcję braku wyboru),
a kompaktowy licznik miał rzeczywiste wymiary 260 × 138 px.

## Otwarte

- Rzeczywiste testy Windows/macOS, urządzeń audio, klucza i uprawnień.
- Wayland, wiele monitorów/DPI i zamykanie/minimalizacja przechwytywanego okna.
- Godzinna sesja z nagrywaniem oraz długie notatki i brak miejsca na dysku.
- Paczki na czystych systemach bez Pythona/Qt i kompletność zależności natywnych.
- Weryfikacja not/licencji konkretnego artefaktu przed publiczną dystrybucją.
