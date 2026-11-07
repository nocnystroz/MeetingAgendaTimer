# Komponenty zewnętrzne

Kod aplikacji jest objęty MIT w `LICENSE`. Biblioteki i zasoby zachowują
własne licencje. Paczki są katalogami z bibliotekami współdzielonymi,
a nie statycznym scaleniem Qt z kodem aplikacji.

| Komponent | Zastosowanie | Źródło licencji i kodu |
| --- | --- | --- |
| Python | Interpreter w paczce | https://www.python.org/downloads/ · PSF License |
| PySide6 / Shiboken / Qt | Natywne okna i opcjonalne przechwytywanie | https://code.qt.io/cgit/pyside/pyside-setup.git/ · https://www.qt.io/licensing/open-source-lgpl-obligations |
| Tabler Icons | Wybrane lokalne SVG | https://github.com/tabler/tabler-icons · MIT, tekst w `meeting_timer/assets/Tabler-LICENSE.txt` |
| SoundCard | Opcjonalny dostęp do urządzeń audio | https://github.com/bastibe/SoundCard · BSD-3-Clause |
| NumPy / CFFI | Opcjonalne przetwarzanie audio i interfejs natywny | https://numpy.org/ · https://cffi.readthedocs.io/ |
| keyring i jego zależności | Opcjonalny magazyn kluczy | https://github.com/jaraco/keyring |
| certifi | Certyfikaty TLS do transkrypcji | https://github.com/certifi/python-certifi · MPL-2.0 |
| FFmpeg z Qt Multimedia | Backend przechwytywania okna | https://ffmpeg.org/ · wariant i licencje zależą od paczki Qt |

Skrypt budowania dołącza metadane i dostępne noty z zainstalowanych pakietów
oraz teksty w `licenses/`. Wyniki należy sprawdzić przed dystrybucją;
manifest zainstalowanych komponentów może obejmować również opcjonalne
pakiety niewykorzystane w wariancie core. Nie jest to certyfikat zgodności.
Wynikowy katalog `third-party-licenses` towarzyszy paczce przenośnej.

Pełny kod aplikacji oraz `uv.lock` znajdują się w tym repozytorium. Wersje
bibliotek w konkretnej paczce zapisuje `third-party-licenses/components.json`.
Przy dystrybucji zachować noty Qt i jego modułów oraz możliwość wymiany
odpowiednich bibliotek współdzielonych. Zależności używane tylko do testów
i budowania nie stanowią dodatkowych wymagań użytkownika końcowego.
