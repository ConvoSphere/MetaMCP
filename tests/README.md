# Teststruktur für MetaMCP

Dieses Verzeichnis enthält alle automatisierten Tests für das MetaMCP-Projekt. Die Tests sind nach Testarten gegliedert, um Wartbarkeit und Übersichtlichkeit zu gewährleisten.

## Ordnerstruktur

- `unit/`         – Unittests für einzelne Funktionen, Klassen und Module (ohne externe Abhängigkeiten)
- `integration/`  – Integrationstests für das Zusammenspiel mehrerer Komponenten oder externe Systeme (z.B. API, DB)
- `regression/`   – Regressionstests zur Absicherung von Bugfixes und wiederkehrenden Fehlerfällen
- `blackbox/`     – Blackbox- und End-to-End-Tests (z.B. REST/MCP-API, Container-Tests)

## Tests ausführen

- **Alle Tests:**
  ```bash
  pytest
  ```
- **Nur Unittests:**
  ```bash
  pytest tests/unit
  ```
- **Nur Integrationstests:**
  ```bash
  pytest tests/integration
  ```
- **Nur Regressionstests:**
  ```bash
  pytest tests/regression
  ```
- **Nur Blackbox-Tests:**
  ```bash
  pytest tests/blackbox
  ```

## Hinweise
- Gemeinsame Fixtures und Hilfsfunktionen können in den jeweiligen `conftest.py`-Dateien abgelegt werden.
- Die Migration bestehender Tests in die neue Struktur erfolgt schrittweise. 