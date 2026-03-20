# 🗞 Personal AI Newspaper

Ein automatisierter Pipeline, der eingehende Gmail-Newsletter in einen kuratierten, täglichen Markdown-Digest verwandelt.

---

## Projektstruktur

```
personal_ai_newspaper/
├── .env.example              # API-Keys, Gmail-Credentials
├── requirements.txt          # Python-Dependencies
│
├── config/
│   ├── settings.yaml         # Pipeline-Konfiguration (Zeitfenster, Labels, Output-Länge)
│   └── interests.yaml        # Persönliches Interessenprofil für Relevanz-Filterung
│
├── src/
│   ├── main.py               # Einstiegspunkt – orchestriert die gesamte Pipeline
│   ├── mail/
│   │   ├── fetcher.py        # Gmail-Zugriff via Gemini CLI, Label-Filterung
│   │   └── labeler.py        # Verarbeitete Mails mit "processed"-Label markieren
│   ├── processing/
│   │   ├── filter.py         # Relevanz-Filterung anhand Interessenprofil
│   │   ├── deduplicator.py   # Deduplication ähnlicher Inhalte
│   │   └── clusterer.py      # Thematisches Clustering verwandter Artikel
│   ├── ai/
│   │   ├── summarizer.py     # Konsolidierte Zusammenfassung pro Cluster
│   │   └── prompts.py        # Prompt-Templates für LLM-Aufrufe
│   └── output/
│       └── generator.py      # Markdown-Datei generieren (Obsidian/reMarkable-optimiert)
│
├── data/
│   ├── raw/                  # Rohdaten der abgerufenen Mails (Debugging)
│   └── output/               # Generierte .md-Digests
│
└── tests/
    ├── test_mail.py
    ├── test_processing.py
    └── test_ai.py
```

---

## Pipeline

Die Pipeline wird über `src/main.py` orchestriert und durchläuft folgende Schritte:

```
Gmail → Fetch → Filter → Deduplicate → Cluster → Summarize → Markdown
```

### 1. Mail Ingestion (`src/mail/`)
- Zugriff auf Gmail-Postfach via **Gemini CLI**
- Filterung nach Label `tech_newsletter`
- Verarbeitung der Mails der letzten 84 Stunden (konfigurierbar in `config/settings.yaml`)
- Bereits verarbeitete Mails (Label `processed`) werden übersprungen

### 2. Processing (`src/processing/`)
- **Deduplication:** Gleiche oder stark ähnliche Inhalte aus verschiedenen Quellen werden zusammengeführt
- **Clustering:** Thematisch verwandte Artikel werden gruppiert

### 3. AI Summarization (`src/ai/`)
- Pro Cluster wird eine konsolidierte Zusammenfassung erstellt
- Fokus auf Insights, nicht auf reines Kürzen

### 4. Output (`src/output/`)
- Eine `.md`-Datei pro Run in `data/newsletter/newsletter_markdown`
- Thematisch strukturiert mit klaren Sections pro Cluster
- Quellenangabe pro Cluster (welche Newsletter haben dieses Thema behandelt)

### 5. State Management (`src/mail/labeler.py`)
- Verarbeitete Mails werden in Gmail mit Label `processed` markiert
- Keine doppelte Verarbeitung bei erneutem Run

---

## Konfiguration

| Datei | Zweck |
|---|---|
| `.env` | API-Keys, Secrets (nicht im Repo) |
| `config/settings.yaml` | Zeitfenster, Gmail-Labels, Output-Limits |
| `config/interests.yaml` | Persönliches Interessenprofil für Relevanz-Filterung |

---

## Setup

```bash
# 1. Repository klonen
git clone <repo-url>
cd personal_ai_newspaper

# 2. Virtual Environment erstellen
python -m venv .venv
source .venv/bin/activate

# 3. Dependencies installieren
pip install -r requirements.txt

# 4. Environment-Variablen konfigurieren
cp .env.example .env
# → .env mit eigenen Credentials befüllen

# 5. Interessenprofil anpassen
# → config/interests.yaml bearbeiten
```

## Ausführung

```bash
python -m src.main
```

Der generierte Digest wird in `data/output/` abgelegt.

---

## Offene Entscheidungen

- [ ] Wie wird das Interessenprofil definiert — statisch in `interests.yaml` oder dynamisch?
- [ ] Wie lang darf der Output maximal sein?
- [ ] Links zu Originalquellen im Output — ja oder nein?
