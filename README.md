# SSH Sentinel – Mini-SIEM für SSH-Logs

SSH Sentinel ist eine kleine FastAPI-Webanwendung für eine Cyber-Security-Modularbeit. Sie liest typische OpenSSH-Einträge aus `auth.log`, erkennt einfache verdächtige Muster und zeigt das Ergebnis als übersichtliche HTML-Seite oder als JSON an.

> Die Anwendung ist eine nachvollziehbare Demo-Analyse. Sie ersetzt weder ein produktives SIEM noch Intrusion-Detection- oder andere Sicherheitswerkzeuge.

## Funktionsumfang

- Drag-and-drop oder Dateiauswahl für UTF-8-Dateien mit `.log` oder `.txt` (maximal 2 MB)
- Parser für fehlgeschlagene, ungültige und erfolgreiche SSH-Anmeldungen
- Unterstützung für IPv4, IPv6, Syslog- und ISO-Zeitstempel
- regelbasierte Erkennung verdächtiger IP-Adressen und Benutzer
- Risiko-Score von 0 bis 100 mit detaillierter Punkteaufschlüsselung
- markierte Originalzeilen inklusive Markierungsgrund
- HTML-Oberfläche und JSON-API mit derselben Analyse-Logik
- Beispieldatei und automatisierte Tests

## Projektstruktur

```text
modularbeit_mini_siem/
├── main.py                     # Einstiegspunkt und FastAPI-Konfiguration
├── routes.py                   # HTML-Routen, JSON-API und Upload-Validierung
├── service.py                  # Verbindet Parser, Detektor und Scoring
├── parser.py                   # Wandelt SSH-Logzeilen in strukturierte Events um
├── detector.py                 # Erkennungsregeln und konfigurierbare Schwellenwerte
├── scorer.py                   # Berechnet Risiko-Score und Risiko-Level
│
├── models/
│   ├── __init__.py             # Exportiert die verwendeten Datenmodelle
│   └── analysis.py             # Pydantic-Modelle für Events und Ergebnisse
│
├── templates/
│   ├── base.html               # Gemeinsames HTML-Grundgerüst
│   ├── index.html              # Startseite mit Datei-Upload
│   └── result.html             # Darstellung des Analyseergebnisses
│
├── static/
│   ├── style.css               # Responsives Design der Weboberfläche
│   └── upload.js               # Drag-and-drop und Browser-Validierung
│
├── examples/
│   ├── auth_good.log           # Beispiel ohne auffälliges Angriffsmuster
│   ├── auth_short_bad.log      # Kurzes Beispiel mit verdächtigen SSH-Events
│   └── auth_long_bad.log       # Umfangreicheres Angriffsszenario
│
├── tests/
│   ├── test_parser.py          # Tests der unterstützten Logformate
│   ├── test_analysis.py        # Tests der Regeln und Risikoauswertung
│   └── test_api.py             # Tests der HTML-Seiten und JSON-API
│
├── requirements.txt            # Python-Abhängigkeiten mit festen Versionen
├── README.md                   # Installation, Nutzung und Dokumentation
└── .gitignore                  # Von Git ausgeschlossene lokale Dateien
```

### Verarbeitungskette

Die Verantwortlichkeiten sind bewusst getrennt. Eine hochgeladene Datei durchläuft die Anwendung in folgender Reihenfolge:

```text
Browser / JSON-Client
        │
        ▼
routes.py      Datei empfangen und validieren
        │
        ▼
service.py     Analyse koordinieren
        │
        ├── parser.py      Logzeilen in SSH-Events umwandeln
        ├── detector.py    verdächtige Muster erkennen
        └── scorer.py      Risiko-Score berechnen
        │
        ▼
AnalysisResult
        │
        ├── result.html    Ausgabe als Ergebnisseite
        └── FastAPI       Ausgabe als JSON
```

## Installation und Start

Voraussetzung ist Python 3.10 oder neuer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Danach ist die Oberfläche unter [http://127.0.0.1:8000](http://127.0.0.1:8000) erreichbar. Die interaktive FastAPI-Dokumentation liegt unter [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Zum Ausprobieren stehen drei Dateien zur Verfügung:

- `examples/auth_good.log` für eine weitgehend unauffällige Analyse
- `examples/auth_short_bad.log` für ein kurzes Angriffsszenario
- `examples/auth_long_bad.log` für eine umfangreichere verdächtige Aktivität

## JSON-API

`POST /api/analyze` erwartet die Datei als Multipart-Feld `log_file`:

```bash
curl -X POST \
  -F "log_file=@examples/auth_short_bad.log" \
  http://127.0.0.1:8000/api/analyze
```

Ein Health-Check steht unter `GET /api/health` zur Verfügung.

## Erkennungsregeln und Punkte

Die Demo betrachtet alle erkannten Ereignisse innerhalb einer hochgeladenen Datei. Sie besitzt noch kein gleitendes Zeitfenster. Die Schwellenwerte stehen als Konstanten oben in `detector.py` und lassen sich leicht ändern.

| Regel | Auslösung | Punkte pro Treffer |
|---|---|---:|
| Mehrfache Fehlversuche je IP | mindestens 5 fehlgeschlagene Logins | 25 Basis + 2 je weiterem Fehler, maximal 40 |
| Hohes Volumen je IP | mindestens 10 Login-Events | 15 Basis + 1 je weiterem Event, maximal 25 |
| Häufig angegriffener Benutzer | mindestens 6 Login-Events für ein Konto | 15 Basis + 2 je weiterem Event, maximal 25 |
| Erfolg nach Fehlversuchen | erfolgreicher Login nach mindestens 3 Fehlern derselben IP | 30 je Sequenz |

Die Punkte aller Treffer werden addiert. Der ausgegebene Gesamtscore wird bei 100 begrenzt. Die Aufschlüsselung zeigt die ungekürzten Beiträge der Regeln, damit die Bewertung überprüfbar bleibt.

| Gesamtscore | Risiko-Level |
|---:|---|
| 0–19 | NIEDRIG |
| 20–49 | MITTEL |
| 50–74 | HOCH |
| 75–100 | KRITISCH |

Der Alarmstatus ist aktiv, sobald mindestens eine Regel ausgelöst wurde. Deshalb kann ein einzelner Regel-Treffer mit weniger als 20 Punkten bereits einen Alarm bei niedrigem Gesamtrisiko erzeugen.

### Erfolgreicher Login nach Fehlversuchen

Diese Regel verfolgt die Ereignisse jeder IP in Dateireihenfolge. Sobald nach drei oder mehr fehlgeschlagenen Versuchen ein erfolgreicher Login derselben IP folgt, werden die Fehler und der Erfolg gemeinsam markiert. Nach dem Erfolg beginnt für diese IP eine neue Sequenz. Das ist bewusst eine einfache Korrelation für Demonstrationszwecke.

## Unterstützte Logmuster

Beispiele:

```text
Jul 31 09:12:10 host sshd[1110]: Failed password for invalid user admin from 203.0.113.45 port 41101 ssh2
Jul 31 09:12:20 host sshd[1111]: Accepted publickey for deploy from 2001:db8::10 port 41102 ssh2
Jul 31 09:12:30 host sshd[1112]: Invalid user test from 198.51.100.77 port 50201
2026-07-31T09:12:40+02:00 host sshd[1113]: Failed password for root from 198.51.100.22 port 50202 ssh2
```

Nicht erkannte Zeilen bleiben unberücksichtigt, zählen aber in der Anzeige der gesamten Dateizeilen mit.

## Tests

```bash
pytest -q
```

Die Tests decken Parser-Varianten, die Beispielanalyse, einen unauffälligen Log sowie HTML- und JSON-Endpunkte ab.

## Erweiterungsmöglichkeiten

- Zeitfenster pro Regel statt dateiweiter Zählung
- zusätzliche Muster wie Port-Scans, ungewöhnliche Uhrzeiten oder Geo-IP-Anreicherung
- persistente Speicherung von Analysen
- Export als CSV/PDF oder Versand von Alarmen
- konfigurierbare Schwellenwerte über Umgebungsvariablen
- Datei-Streaming für grössere Logs

Parser, Detektor und Scorer sind absichtlich getrennt. Eine neue Logsyntax wird in `parser.py`, eine neue Regel in `detector.py` und eine andere Klassifizierung in `scorer.py` ergänzt, ohne die Webrouten ändern zu müssen.
