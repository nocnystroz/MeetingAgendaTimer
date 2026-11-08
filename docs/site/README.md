# Strona projektu na ion301.com

- Metadane i opisy: `pages.json`. Treść: `pl.html` i `en.html`; znaczniki `{{PANEL_IMAGE}}` i `{{TIMER_IMAGE}}`
  zastępuje skrypt adresami lokalnych mediów WordPress.
- Opublikowane strony: PL ID 4760 pod hubem 2475, EN ID 4762 pod hubem 2478.
- `deploy.php` uruchamia się przez `wp eval-file`, na serwerze ion301.com,
  jako użytkownik witryny. Nie zawiera danych logowania i nie jest używany w aplikacji.
- Wymaga `/tmp/meeting-site-payload.json`: obiekt o kluczach `pl`, `en`,
  każdy z polami `parent`, `title`, `excerpt`, `content` (HTML z powyższych plików).
  Wymaga też `/tmp/meeting-agenda-{panel,timer}-{pl,en}.png`.
- Argument `prepare` zapisuje szkice; `publish` publikuje strony, dodaje karty
  do obu hubów i linki do odpowiednich menu stopki. Skrypt zapisuje kopię
  wcześniejszych danych w `/tmp/meeting-agenda-backup-*.json`.
- Osobny szablon `ion301-project-page.php` powstaje z aktualnego szablonu witryny,
  zachowując nawigację i stopkę, bez sekcji ofertowych. Wspólny szablon nie jest zmieniany.
- Przy nowym wydaniu aktualizuj bezpośrednie adresy paczek w obu plikach HTML.
  Najpierw opublikuj i sprawdź pliki wydania, następnie aktualizuj stronę.

- Publikacja dodaje projekt do grupy Narzędzia/Tools w `nav-pl` / `nav-en`,
  wspólnej dla górnego menu i mobilnej nawigacji. Nie zmienia przypisań
  starszych menu 123/122 ani struktury adresów.
