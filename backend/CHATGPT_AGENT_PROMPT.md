# ChatGPT Agent Prompt für iterative DAX Datenextraktion

Verwende diesen Prompt in ChatGPT, um einen Agenten zu erstellen, der **Schritt für Schritt** alle DAX-Unternehmen abarbeitet.

## System Prompt für Custom GPT oder "Aktienvergleich DAX Datenextractor"

```
Du bist ein Finanz-Datenextractor Agent für DAX-Unternehmen. 

AUFGABE:
Extrahiere Finanzschätzungen für deutsche DAX-Unternehmen von finanzen.net, 
einen Datensatz nach dem anderen. Du wirst iterativ durch eine Liste gehen.

PROZESS:
1. Der Benutzer gibt dir eine Unternehmensliste mit ISIN und URL
2. Du fragst: "Starten wir mit [UNTERNEHMEN 1]?" - warte auf "ja"
3. Besuche die Schätzungsseite für dieses Unternehmen
4. Extrahiere für Fiscal Years 2024, 2025, 2026:
   - Umsatz (in Millionen EUR)
   - Dividende (pro Aktie)
   - Dividendenrendite (in %)
   - Gewinn je Aktie (EPS)
   - KGV (P/E Ratio)
   - Mittleres Kursziel
5. Gib Daten im CSV-Format aus
6. Speichere Daten in einer laufenden CSV-Tabelle
7. Frage: "Fertig mit [UNTERNEHMEN 1]. Weiter mit [UNTERNEHMEN 2]?"
8. Wiederhole bis alle abgearbeitet

FORMAT FÜR JEDES UNTERNEHMEN:
```
isin,title,fiscal_year,revenue_amount,dividend,dividend_yield_percent,eps,pe_ratio,avg_price_target,currency,source_url
DE0005140008,Deutsche Telekom,2024,120000,0.70,2.5,2.50,15.5,40.50,EUR,https://...
DE0005140008,Deutsche Telekom,2025,125000,0.75,2.6,2.70,16.0,41.00,EUR,https://...
```

REGELN:
- Nutze immer EXAKTE ISINs
- Greife auf https://www.finanzen.net/aktien/[unternehmen] zu
- Suche die "Schätzungen" Sektion (Umsatz, Gewinn, Dividenden)
- Für Kursziele: Suche "Kursziele" oder "Durchschnittliches Kursziel"
- Zahlen in Millionen (z.B. "Revenue 120B" → 120000)
- Deutsche Zahlenformat (1.234,56) → in Dezimalformat konvertieren (1234.56)
- "NV" bei fehlenden Werten verwenden
- Arbeite konsistent, ein Unternehmen nach dem anderen
- Fasse nach jedem Unternehmen die Daten in einer Zeile zusammen
- Speichere alle Daten in einer laufenden CSV-Tabelle

ZIEL:
Alle 40 DAX-Unternehmen erfolgreich durchgehen und eine komplette CSV-Datei mit allen Schätzungen erstellen.
```

## Benutzerprompt zum Starten

Kopiere diesen Prompt und sende ihn an deinen DAX-Agent in ChatGPT:

---

### Initial Prompt (1. Nachricht)

```
Ich möchte, dass du iterativ Finanzschätzungen für alle 40 DAX-Unternehmen von finanzen.net extrahierst.

Hier ist die Liste:

rank,isin,ticker,name,sector,url
1,DE0007236101,SIE,Siemens,Industriekonglomerat,https://www.finanzen.net/aktien/siemens-aktie
2,DE0007164600,SAP,SAP SE,Software,https://www.finanzen.net/aktien/sap-aktie
3,DE0008404005,ALV,Allianz SE,Versicherungen,https://www.finanzen.net/aktien/allianz-aktie
4,DE0006062144,MUN,Munich Re,Versicherungen,https://www.finanzen.net/aktien/munich-re-aktie
5,DE0005140008,DTE,Deutsche Telekom,Telekommunikation,https://www.finanzen.net/aktien/deutsche-telekom-aktie
6,DE0005103006,BAS,BASF SE,Chemie,https://www.finanzen.net/aktien/basf-aktie
7,DE0005933931,BMW,BMW AG,Automobilhersteller,https://www.finanzen.net/aktien/bmw-aktie
8,DE0006095006,MBG,Mercedes-Benz Group,Automobilhersteller,https://www.finanzen.net/aktien/mercedes-benz-aktie
9,DE0008092008,DAI,Daimler Truck,Automobilhersteller,https://www.finanzen.net/aktien/daimler-truck-aktie
10,DE0005557508,IFX,Infineon,Halbleiter,https://www.finanzen.net/aktien/infineon-aktie
...
[Kopiere die komplette Liste aus dax_companies_list.csv]

Starten wir mit Unternehmen #1 (Siemens, DE0007236101)?

ANLEITUNG:
- Ein Unternehmen nach dem anderen
- Extrahiere fiscal years 2024, 2025, 2026
- Gib jedes Unternehmen als CSV-Reihe(n) aus
- Sammle alles in einer CSV-Tabelle
- Frage nach jedem: "Fertig mit [Name]. Sollen wir mit [Nächstes Unternehmen] weitermachen?"
```

### Weitere Prompts (nach jedem Unternehmen)

```
ja, weiter mit [nächstes Unternehmen]
```

oder 

```
zeige mir die CSV bisher
```

oder

```
speichern und beenden
```

---

## Workflow Schritt-für-Schritt

### Phase 1: Agent Starten
1. Gehe zu ChatGPT
2. Erstelle oder öffne einen Custom GPT mit dem oberen "System Prompt"
3. Sende den "Initial Prompt" mit der kompletten DAX-Liste

### Phase 2: Iterativ Daten sammeln
1. ChatGPT fragt nach Unternehmen #1
2. Du antwortest: "ja"
3. Agent extrahiert Daten → gibt CSV aus
4. Agent fragt nach Unternehmen #2
5. Du antwortest: "ja"
6. Wiederhole für alle 40 Unternehmen

**Dauer:** ~30-45 Minuten für alle 40 Unternehmen (~1 Min pro Unternehmen)

### Phase 3: CSV Exportieren
Nach allen Unternehmen:
1. Frage: "Zeige mir die komplette CSV-Tabelle"
2. ChatGPT gibt die gesamte CSV aus
3. Kopiere die komplette Tabelle
4. Speichere als `dax_all_estimates.csv`

### Phase 4: Daten in Supabase Importieren
```bash
cd /path/to/backend
python -m src.import_estimates --file dax_all_estimates.csv --index DAX
```

---

## Beispiel-Dialog

### Nachricht 1 (Du):
```
Ich möchte iterativ alle DAX-Unternehmen abarbeiten.
Starten wir mit Siemens (DE0007236101)?
https://www.finanzen.net/aktien/siemens-aktie
```

### Nachricht 2 (ChatGPT Agent):
```
Perfekt! Ich extrahiere jetzt die Schätzungen für Siemens...

Hier sind die Daten:

isin,title,fiscal_year,revenue_amount,dividend,dividend_yield_percent,eps,pe_ratio,avg_price_target,currency,source_url
DE0007236101,Siemens,2024,75000,4.50,3.2,8.50,18.5,165.00,EUR,https://www.finanzen.net/aktien/siemens-aktie
DE0007236101,Siemens,2025,78000,4.80,3.3,9.20,19.0,170.00,EUR,https://www.finanzen.net/aktien/siemens-aktie
DE0007236101,Siemens,2026,81000,5.10,3.4,10.00,19.5,175.00,EUR,https://www.finanzen.net/aktien/siemens-aktie

✓ Fertig mit Siemens!
Weiter mit SAP (DE0007164600)?
```

### Nachricht 3 (Du):
```
ja
```

### Nachricht 4 (ChatGPT Agent):
```
Extrahiere jetzt SAP...

isin,title,fiscal_year,revenue_amount,dividend,dividend_yield_percent,eps,pe_ratio,avg_price_target,currency,source_url
DE0007164600,SAP SE,2024,35000,1.90,1.8,5.50,28.0,210.00,EUR,https://www.finanzen.net/aktien/sap-aktie
DE0007164600,SAP SE,2025,37500,2.05,1.9,6.00,29.0,220.00,EUR,https://www.finanzen.net/aktien/sap-aktie
DE0007164600,SAP SE,2026,40000,2.20,2.0,6.50,30.0,230.00,EUR,https://www.finanzen.net/aktien/sap-aktie

✓ Fertig mit SAP!
Weiter mit Allianz (DE0008404005)?
```

---

## Tipps für Erfolg

### ✅ Gute Praktiken
- **Kleine Pausen:** Nach 10 Unternehmen → Frage "Zeige mir die Zwischenbilanz"
- **Konsistenz:** Nutze immer die gleiche Spaltenreihenfolge
- **Validierung:** Wenn Daten fehlen → "NV" verwenden
- **Backup:** Nach 20 Unternehmen → CSV speichern für Sicherheit

### ❌ Zu vermeiden
- Mehrere Unternehmen in einem Prompt
- Vage Links ("erste DAX Aktie")
- Unterschiedliche Jahresangaben (immer 2024, 2025, 2026)

---

## Alternative: Batch-Mode

Falls iterativ zu langsam ist, kannst du auch Batches machen:

```
Extrahiere ALLE dieser 10 Unternehmen:
1. Siemens
2. SAP
3. Allianz
...
(10 Unternehmen)

Gib für JEDES die CSV-Reihen aus.
```

Dann iterativ weitere 10er Batches.

---

## Danach: Import in Claude Code

Sobald du die komplette CSV hast:

```bash
# Auf deinem PC im Terminal:
cd /path/to/Aktienvergleich/backend
python -m src.import_estimates --file dax_all_estimates.csv --index DAX
```

Das importiert alle 40 Unternehmen mit ihren Schätzungen und berechnet automatisch CAGR!
