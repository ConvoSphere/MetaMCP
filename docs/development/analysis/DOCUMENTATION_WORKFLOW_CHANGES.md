# Dokumentations-Workflow Optimierung

## 🎯 Ziel

Die Dokumentation soll unabhängig von anderen CI/CD-Schritten gebaut werden und nur bei tatsächlichen Änderungen an relevanten Dateien ausgeführt werden.

## 🔧 Implementierte Änderungen

### 1. **Intelligente Änderungserkennung**

#### Neuer `check-changes` Job
```yaml
check-changes:
  name: Check for Documentation Changes
  outputs:
    should-build: ${{ steps.filter.outputs.changes }}
```

**Verwendet `dorny/paths-filter@v2` für präzise Änderungserkennung:**
- **Dokumentation:** `docs/**`, `mkdocs.yml`
- **Code:** `metamcp/**/*.py`, `pyproject.toml`, `requirements*.txt`, `scripts/generate_api_docs.py`

### 2. **Bedingte Ausführung**

#### Build-Job nur bei relevanten Änderungen
```yaml
build-docs:
  needs: check-changes
  if: needs.check-changes.outputs.should-build == 'true'
```

#### Deploy und Link-Check nur bei erfolgreichem Build
```yaml
deploy-docs:
  if: github.ref == 'refs/heads/main' && needs.build-docs.result == 'success'

link-check:
  if: needs.build-docs.result == 'success'
```

### 3. **Erweiterte Trigger-Bedingungen**

#### Zusätzliche relevante Dateien
- `pyproject.toml` - Änderungen an Projektabhängigkeiten
- `requirements*.txt` - Änderungen an Python-Abhängigkeiten  
- `scripts/generate_api_docs.py` - Änderungen am API-Dokumentationsgenerator

#### Erweiterte Branch-Unterstützung
- Jetzt auch für `develop` Branch aktiviert
- Bessere Unterstützung für Feature-Entwicklung

### 4. **Verbesserte Concurrency-Kontrolle**

```yaml
concurrency:
  group: "pages-${{ github.ref }}"
  cancel-in-progress: true
```

- **Branch-spezifische Gruppen:** Verhindert Konflikte zwischen verschiedenen Branches
- **Cancel-in-progress:** Neue Builds ersetzen laufende Builds für denselben Branch

### 5. **Konsistente Abhängigkeitsverwaltung**

#### UV-Integration
```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v1
  with:
    version: '1.0.0'

- name: Cache dependencies
  uses: actions/cache@v4
  with:
    key: docs-${{ runner.os }}-uv-${{ hashFiles('**/pyproject.toml', '**/requirements*.txt') }}
```

#### Virtuelle Umgebung
```yaml
- name: Install dependencies
  run: |
    uv venv
    source .venv/bin/activate
    uv pip install mkdocs mkdocs-material mkdocs-autorefs mkdocs-section-index
    uv pip install -r requirements.txt
```

### 6. **Artifact-Optimierung**

```yaml
- name: Upload documentation artifacts
  uses: actions/upload-artifact@v4
  with:
    name: documentation-${{ github.sha }}
    path: site/
    retention-days: 7  # Automatische Bereinigung nach 7 Tagen
```

## 📊 Workflow-Ablauf

### Vor den Änderungen
```
Push/PR → Alle Jobs parallel → Dokumentation immer gebaut
```

### Nach den Änderungen
```
Push/PR → check-changes → (nur bei relevanten Änderungen) → build-docs → deploy-docs + link-check
```

## 🚀 Vorteile

### 1. **Performance**
- ⚡ Keine unnötigen Dokumentations-Builds
- ⚡ Schnellere CI/CD-Pipeline
- ⚡ Reduzierte GitHub Actions Minuten

### 2. **Ressourceneffizienz**
- 💰 Geringere Kosten für GitHub Actions
- 💰 Weniger Speicherverbrauch
- 💰 Automatische Artifact-Bereinigung

### 3. **Entwicklerfreundlichkeit**
- 👨‍💻 Klare Trennung zwischen Code- und Dokumentations-Workflows
- 👨‍💻 Keine Blockierung durch Dokumentations-Builds
- 👨‍💻 Bessere Feedback-Zyklen

### 4. **Zuverlässigkeit**
- 🛡️ Unabhängige Ausführung von CI/CD und Dokumentation
- 🛡️ Keine Kaskadenfehler zwischen Workflows
- 🛡️ Bessere Fehlerisolierung

## 🔍 Technische Details

### Änderungserkennung
```yaml
filters: |
  docs:
    - 'docs/**'
    - 'mkdocs.yml'
  code:
    - 'metamcp/**/*.py'
    - 'pyproject.toml'
    - 'requirements*.txt'
    - 'scripts/generate_api_docs.py'
```

### Bedingte Logik
```yaml
# Nur bei relevanten Änderungen
if: needs.check-changes.outputs.should-build == 'true'

# Nur bei erfolgreichem Build
if: needs.build-docs.result == 'success'

# Nur auf main Branch deployen
if: github.ref == 'refs/heads/main' && needs.build-docs.result == 'success'
```

## 📈 Erwartete Verbesserungen

### Build-Zeiten
- **Vorher:** Dokumentation immer gebaut (~3-5 Minuten)
- **Nachher:** Nur bei Änderungen (~3-5 Minuten, aber seltener)

### Ressourcenverbrauch
- **Vorher:** 100% der Pushs/PRs
- **Nachher:** ~20-30% der Pushs/PRs (nur bei relevanten Änderungen)

### Entwicklererfahrung
- **Vorher:** Warten auf Dokumentations-Builds bei Code-Änderungen
- **Nachher:** Schnellere Feedback-Zyklen, Dokumentation nur bei Bedarf

## 🔗 Verwandte Workflows

### CI/CD Pipeline (`ci.yml`)
- ✅ Bleibt unabhängig von Dokumentation
- ✅ Fokus auf Code-Qualität, Tests, Security, Build, Deploy
- ✅ Keine Abhängigkeiten zur Dokumentation

### Dependency Updates (`dependency-update.yml`)
- ✅ Unabhängig von Dokumentation
- ✅ Automatische Abhängigkeitsaktualisierungen
- ✅ Separate Sicherheitsprüfungen

## 📝 Nächste Schritte

### Kurzfristig
1. **Monitoring:** Überwachung der Build-Häufigkeit
2. **Optimierung:** Feinabstimmung der Pfad-Filter
3. **Dokumentation:** Team-Schulung zu neuen Workflows

### Langfristig
1. **Metriken:** Sammeln von Performance-Daten
2. **Erweiterung:** Weitere intelligente Trigger-Bedingungen
3. **Integration:** Bessere Integration mit anderen Tools