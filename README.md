# 🗞 Personal AI Newspaper

Ein automatisierter Pipeline, der eingehende Gmail-Newsletter in einen kuratierten, täglichen Markdown-Digest verwandelt.

---

## Projektstruktur

```
personal_ai_newspaper/
├── .env.example              # Pfad zu Google OAuth2 Credentials
├── .gitignore
├── requirements.txt          # Python-Dependencies
│
├── config/
│   ├── __init__.py           # Config Loader (settings.yaml + .env)
│   └── settings.yaml         # Pipeline-Konfiguration (Zeitfenster, Labels)
│
├── src/
│   ├── main.py               # Einstiegspunkt – orchestriert die gesamte Pipeline
│   ├── mail/
│   │   ├── fetcher.py        # Gmail-Zugriff via Gmail API (OAuth2), Label-Filterung
│   │   └── labeler.py        # Verarbeitete Mails mit "processed"-Label markieren
│   ├── processing/
│   │   ├── deduplicator.py   # Deduplication ähnlicher Inhalte
│   │   └── clusterer.py      # Thematisches Clustering verwandter Artikel
│   ├── ai/
│   │   ├── summarizer.py     # Konsolidierte Zusammenfassung pro Cluster
│   │   └── prompts.py        # Prompt-Templates für LLM-Aufrufe
│   └── output/
│       └── generator.py      # Markdown-Datei generieren
│
├── data/
│   ├── raw/                  # Rohdaten der abgerufenen Mails (Debugging)
│   └── newsletter/           # Generierte .md-Digests
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
Gmail → Fetch → Deduplicate → Cluster → Summarize → Markdown
```

### 1. Mail Ingestion (`src/mail/`) ✅
- Zugriff auf Gmail-Postfach via **Gmail API** (OAuth2)
- Filterung nach Label `Tech_Newsletter`
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

### 5. State Management (`src/mail/labeler.py`) ✅
- Verarbeitete Mails werden in Gmail mit Label `processed` markiert
- Keine doppelte Verarbeitung bei erneutem Run

---

## Konfiguration

| Datei | Zweck |
|---|---|
| `.env` | Pfad zu `credentials.json` (nicht im Repo) |
| `config/settings.yaml` | Zeitfenster, Gmail-Labels, Max. Ergebnisse |

---

## Setup

```bash
# 1. Repository klonen
git clone <repo-url>
cd personal_ai_newspaper

# 2. Virtual Environment erstellen
python3 -m venv .venv
source .venv/bin/activate

# 3. Dependencies installieren
pip install -r requirements.txt

# 4. Google OAuth2 Credentials einrichten
#    → Google Cloud Console: Gmail API aktivieren
#    → OAuth2 Desktop Credentials erstellen
#    → JSON herunterladen und als credentials.json ins Projektroot legen
cp .env.example .env

# 5. Erster Run – öffnet Browser für OAuth-Login
python3 -m src.main
```

> **Hinweis:** Beim ersten Run öffnet sich ein Browserfenster für den Google OAuth-Login.
> Der Token wird in `data/token.json` gecacht – danach ist kein erneuter Login nötig.

---

## Offene Entscheidungen

- [ ] Wie lang darf der Output maximal sein?
- [ ] Links zu Originalquellen im Output — ja oder nein?
