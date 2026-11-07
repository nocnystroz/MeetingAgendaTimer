# Walidacja wersji 0.1

Data: 2026-11-07. Tylko wykonane lokalnie próby, bez deklarowania wsparcia
platform na podstawie samego kodu lub konfiguracji CI.

## Wykonane

- Linux x86_64, X11/XFCE, host z glibc 2.43; Python 3.13.14, Qt/PySide6 6.12.0.
- 38 testów logiki/GUI/audio/API/zrzutów przeszło. GUI testowano także na
  offscreen; nie zastępuje to testów integracji z menedżerem okien.
- Rzeczywisty panel i licznik wyświetlono na pulpicie Linux.
- Zasobnik wykryty jako dostępny na tym pulpicie.
- Qt WindowCapture zapisał PNG osobnego, syntetycznego okna procesu testowego
  i zatrzymał cykl po limicie jednego zrzutu. Nie przechwytywano prywatnych okien.
- WAV testowano na syntetycznych danych; fizyczne źródła audio wykryto,
  ale nie nagrywano prywatnego mikrofonu ani dźwięku użytkownika.
- API sprawdzono na atrapach, w tym kody błędów, anulowanie przed wysyłką,
  limit i strumieniowanie. Nie użyto rzeczywistego klucza ani płatnego żądania.

## W trakcie

Budowanie core/full i pomiary zasobów. Wyniki zostaną dopisane po wykonaniu.

## Otwarte

- Rzeczywiste testy Windows/macOS, urządzeń audio, klucza i uprawnień.
- Wayland, wiele monitorów/DPI i zamykanie/minimalizacja przechwytywanego okna.
- Godzinna sesja z nagrywaniem oraz długie notatki i brak miejsca na dysku.
- Paczki na czystych systemach bez Pythona/Qt i kompletność zależności natywnych.
- Weryfikacja not/licencji konkretnego artefaktu przed publiczną dystrybucją.
