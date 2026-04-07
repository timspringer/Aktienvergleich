# ChatGPT Custom GPT Setup für Autonome DAX Datensammlung

Dieser Guide zeigt, wie du einen **autonomen ChatGPT-Agenten** erstellst, der:
- Automatisch durch alle DAX-Unternehmen iteriert
- Für jedes Unternehmen Schätzungen von finanzen.net extrahiert
- **Direkt in deine Supabase-Datenbank speichert**
- Ohne manuelle Zwischenschritte

## Architektur

```
ChatGPT Custom GPT (Agent)
  ↓
Extrahiert Daten von finanzen.net
  ↓
Sendet JSON an deine API (via POST /api/submit-estimate)
  ↓
API speichert in Supabase (companies, estimates, metrics)
  ↓
Dashboard zeigt Daten an
```

## Schritt 1: API Server Starten

Der API Server muss laufen, damit ChatGPT Daten speichern kann.

### 1.1 Lokal testen

```bash
cd backend

# Installiere Flask
pip install flask flask-cors

# Starte API Server
python -m src.api_server
```

Output:
```
======================================================================
Aktienvergleich API Server
======================================================================
Starting server on port 5000...
For ChatGPT integration, expose with:
  ngrok http 5000
  Then add https://[ngrok-url] to ChatGPT Custom Action
======================================================================
```

✅ Verifizieren:
```bash
curl http://localhost:5000/health
# Sollte zurückgeben: {"status":"ok","timestamp":"..."}
```

### 1.2 Expose mit ngrok (für ChatGPT)

ChatGPT kann nicht auf `localhost:5000` zugreifen. Du musst den Port exposen:

```bash
# Installiere ngrok (https://ngrok.com)
brew install ngrok  # Mac
# oder Windows: ngrok.exe http 5000

# In separatem Terminal
ngrok http 5000
```

Output:
```
Session Status                online
Session Expires               2 hours 50 minutes
Version                       3.0.0
Region                        us
Forwarding                    https://YOUR-ID.ngrok.io -> http://localhost:5000
```

**Wichtig:** Kopiere die `https://YOUR-ID.ngrok.io` URL - du brauchst sie für ChatGPT!

### 1.3 In Production deployen (optional)

Du kannst auch direkt auf Render deployen:

```bash
# In render.yaml hinzufügen:
services:
  - type: web
    name: aktienvergleich-api
    runtime: python
    pythonVersion: "3.11"
    buildCommand: pip install -r backend/requirements.txt
    startCommand: cd backend && python -m src.api_server
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: API_PORT
        value: "5000"
```

Dann erhältst du eine Public URL wie `https://aktienvergleich-api.onrender.com`

## Schritt 2: ChatGPT Custom GPT Erstellen

### 2.1 Gehe zu ChatGPT

1. Öffne https://chatgpt.com
2. Gehe zu **"Explore"** → **"Create a GPT"**
3. Oder öffne direkt deine Custom GPTs

### 2.2 Konfiguriere den GPT

**Name:**
```
DAX Datensammler
```

**Description:**
```
Ein autonomer Agent, der Finanzschätzungen für alle DAX-Unternehmen von finanzen.net sammelt und direkt in die Datenbank speichert.
```

**Instructions:**

Kopiere diesen System Prompt:

```
Du bist der "DAX Datensammler" - ein autonomer Agent für Finanzschätzungen.

HAUPTAUFGABE:
Iterativ durch alle 40 DAX-Unternehmen gehen und für jedes Unternehmen:
1. Extrahiere Schätzungen von finanzen.net
2. Sende Daten via API direkt in die Supabase-Datenbank
3. Gehe zum nächsten Unternehmen

PROZESS PRO UNTERNEHMEN:
1. Besuche die finanzen.net URL für das Unternehmen
2. Extrahiere "Schätzungen" Sektion:
   - Fiscal Years: 2024, 2025, 2026
   - Umsatz (Revenue/Millionen EUR)
   - Dividende (pro Aktie)
   - Dividendenrendite (%)
   - EPS (Gewinn je Aktie)
   - KGV (P/E Ratio)
   - Kursziel (Average Price Target)
3. Sende JSON an die API: /api/submit-estimate
4. Warte auf Bestätigung
5. Frage: "[Name] saved! Next: [Nächstes Unternehmen]? (yes/no/show-status)"

JSON FORMAT FÜR API:
```json
{
  "index": "DAX",
  "isin": "DE0005140008",
  "title": "Deutsche Telekom",
  "currency": "EUR",
  "source_url": "https://www.finanzen.net/aktien/deutsche-telekom-aktie",
  "estimates": [
    {
      "fiscal_year": 2024,
      "revenue_amount": 120000,
      "dividend": 0.70,
      "dividend_yield_percent": 2.5,
      "eps": 2.50,
      "pe_ratio": 15.5,
      "avg_price_target": 40.50
    },
    {
      "fiscal_year": 2025,
      "revenue_amount": 125000,
      "dividend": 0.75,
      "dividend_yield_percent": 2.6,
      "eps": 2.70,
      "pe_ratio": 16.0,
      "avg_price_target": 41.00
    },
    {
      "fiscal_year": 2026,
      "revenue_amount": 130000,
      "dividend": 0.80,
      "dividend_yield_percent": 2.7,
      "eps": 2.90,
      "pe_ratio": 16.5,
      "avg_price_target": 42.00
    }
  ]
}
```

REGELN:
- Nutze exakte ISINs und Unternehmensnamen
- Zahlen in Millionen (z.B. "120B" → 120000)
- "NV" für fehlende Werte (in JSON: null oder omit field)
- Deutsche Zahlenformat (1.234,56) → dezimal (1234.56)
- Arbeite systematisch, nacheinander
- Nach API-Fehler: Versuche es erneut, dann log error

DIALOG:
Du: "Starte mit Siemens (DE0007236101)?"
Benutzer: "ja"
Du: [Extrahiere] → [Sende zu API] → "Siemens gespeichert! Weiter mit SAP? (ja/nein)"
Benutzer: "ja"
Du: [Wiederholen für alle 40]

VERFÜGBARE BEFEHLE:
- "ja" = Nächstes Unternehmen
- "nein" = Stop
- "status" = Zeige Fortschritt
- "skip [ISIN]" = Überspringen und nächstes
- "csv" = Zeige gesammelte Daten
```

### 2.3 Konfiguriere Actions (wichtig!)

1. Scrolle in deinem Custom GPT zu **"Actions"**
2. Klick auf **"Create new action"** oder **"+ Create action"**
3. Wähle **"Authenticate via API key"** ❌ NEIN!
   → Wähle stattdessen **"No authentication"** ✅
4. Gib in **"Authentication"** ein:
   ```
   Type: None
   ```

5. Unter **"Import from URL"** kopiere diese URL:
   ```
   https://YOUR-NGROK-URL/openapi.json
   ```
   Oder **YOUR-SUPABASE-API-URL** wenn auf Production

6. Klick **"Import"**

7. Der OpenAPI Schema wird importiert. Du solltest sehen:
   - ✅ POST /api/submit-estimate
   - ✅ GET /api/status
   - ✅ GET /api/list-indexes

8. **Wichtig:** Unter "Available functions" prüfe, dass nur folgende checked sind:
   - ✅ submitEstimate (POST)
   - ✅ getStatus (GET)
   - ✅ listIndexes (GET)

9. Speichere den GPT

## Schritt 3: Teste den GPT

### 3.1 Erste Test-Nachricht

Öffne deinen neuen GPT und schreibe:

```
Hallo! Fangen wir mit Siemens an?
```

Der GPT sollte antworten:
```
Perfekt! Ich starte die Datensammlung für Siemens (DE0007236101).
Ich besuche jetzt https://www.finanzen.net/aktien/siemens-aktie ...

Ich extrahiere die Schätzungen für 2024-2026...

Extrahiert! Sende jetzt die Daten...

[Zeigt die JSON die gesendet wird]

Siemens erfolgreich gespeichert! 

Weiter mit SAP SE (DE0007164600)? (ja/nein)
```

### 3.2 Verifiziere in Supabase

Nach jeder Antwort kannst du in deinem **Supabase Dashboard** prüfen:

```sql
-- Schau die neu erstellte Company
SELECT * FROM companies WHERE title = 'Siemens' LIMIT 1;

-- Schau die Estimates
SELECT * FROM estimates WHERE company_id = '[id]' ORDER BY fiscal_year;

-- Schau die Metrics
SELECT * FROM metrics WHERE company_id = '[id]';
```

Die Daten sollten sofort dort sein!

## Schritt 4: Starte die vollständige Sammlung

### 4.1 Alle 40 Unternehmen durchgehen

Einfach immer **"ja"** antworten:

```
Benutzer: ja
GPT: [Extrahiert Unternehmen #2] → gespeichert → "Weiter mit [#3]?"
Benutzer: ja
GPT: [Extrahiert Unternehmen #3] → gespeichert → "Weiter mit [#4]?"
...
```

**Dauer:** ~1-2 Minuten pro Unternehmen = 40-80 Minuten total

### 4.2 Kontrolle während des Prozesses

Zwischendrin kannst du schreiben:
```
status
```

Der GPT zeigt dann:
```
Fortschritt:
- Unternehmen verarbeitet: 5/40
- Estimates gespeichert: 15
- Fehler: 0
```

Oder:
```
skip DE0005103006
```

Um ein Unternehmen zu überspringen und beim nächsten weiterzumachen.

### 4.3 Abbrechen

```
nein
```

Beendet den Prozess. Du kannst später weitermachen - der GPT speichert keine States, aber deine Datenbank hat alle bisherigen Daten!

## Schritt 5: Dashboard aktualisieren

Nach der Sammlung werden die Daten **automatisch** im Frontend angezeigt:

1. Öffne https://deine-vercel-url.com
2. Login mit Supabase Auth
3. Dashboard zeigt alle 40 DAX-Unternehmen mit Schätzungen
4. Filter und Sorte nach Metriken

## Troubleshooting

### Problem: "Function not found" Fehler

**Lösung:**
1. Prüfe dass ngrok läuft: `ngrok http 5000`
2. API Server läuft: `python -m src.api_server`
3. URL in ChatGPT ist korrekt: `https://YOUR-ID.ngrok.io/openapi.json`
4. ChatGPT Actions sind korrekt importiert

### Problem: "No authentication" Status 401

**Lösung:**
- API braucht KEINE Authentication (openapi.json hat `"security": []`)
- Stelle sicher "No authentication" ist in ChatGPT Actions gesetzt

### Problem: Daten werden nicht in Supabase gespeichert

**Lösung:**
1. Prüfe API Logs:
   ```bash
   # Im Terminal wo api_server läuft
   # Sollte POST requests zeigen
   ```
2. Prüfe Supabase Logs in Dashboard
3. Prüfe dass SUPABASE_URL und SUPABASE_KEY korrekt sind

### Problem: "Unknown index: DAX"

**Lösung:**
- Stelle sicher dass DAX Index in Supabase Database existiert
- Oder erstelle mit SQL:
  ```sql
  INSERT INTO indices (name, display_name, region, currency)
  VALUES ('DAX', 'DAX', 'Germany', 'EUR');
  ```

## Erweiterte Optionen

### Multi-Index Support

Der GPT kann auch andere Indexes machen:

```
Jetzt machen wir MDAX. Starten mit [Unternehmen 1]?
```

Einfach "ja" sagen - der GPT wird MDAX-Unternehmen mit `"index": "MDAX"` senden.

### Batch Processing

Falls du mehrere Unternehmen auf einmal verarbeiten möchtest:

```
Mache die nächsten 5: Siemens, SAP, Allianz, Munich Re, Deutsche Telekom
```

Der GPT wird dann alle 5 hintereinander machen.

### Pause & Resume

Du kannst jederzeit pausieren:

```
Pausieren
```

Und später fortfahren:

```
Weitermachen mit [ISIN]
```

Der GPT merkt sich nicht welche er gemacht hat, aber deine DB weiß es!

## Success Metrics

✅ **Erfolgreich** wenn:
- ✓ Alle 40 DAX-Unternehmen haben Einträge in `companies` table
- ✓ Jedes Unternehmen hat 3 Rows in `estimates` table (2024, 2025, 2026)
- ✓ Jedes Unternehmen hat 1 Row in `metrics` table mit CAGR berechnet
- ✓ Dashboard zeigt alle Daten und ist sortierbar/filterbar
- ✓ Keine Fehler in API Logs

## Nächste Schritte

Nach DAX kannst du:

1. **MDAX machen:** 40 weitere Mid-Cap Unternehmen
2. **SDAX machen:** 70 weitere Small-Cap Unternehmen
3. **International:** USA (SPX) oder Europe (STOXX50) mit Yahoo Finance links

Du kannst den gleichen GPT nutzen - er funktioniert mit jedem Index!

---

## Schnell-Referenz

```bash
# Terminal 1: API Server
cd backend
python -m src.api_server

# Terminal 2: ngrok
ngrok http 5000
# Kopiere https://YOUR-ID.ngrok.io

# Dann:
1. Erstelle Custom GPT in ChatGPT
2. Importiere openapi.json via Actions
3. Schreibe "ja" für 40+ Runden
4. Fertig! Daten sind in Supabase
```
