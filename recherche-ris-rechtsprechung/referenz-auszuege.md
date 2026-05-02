# Referenz-Auszüge aus externen Quellen

> Per `Agent.md` werden **keine** vollständigen Fremd-Repos eingecheckt.
> Hier nur die für die Skill-Konstruktion relevanten Auszüge mit Quellenangabe.

## 1. shrinkwrap-legal/shrinkwrap-legal-api — `RisAdapterImpl.java`

Quelle: `https://github.com/shrinkwrap-legal/shrinkwrap-legal-api/blob/main/src/main/java/legal/shrinkwrap/api/adapter/ris/rest/RisAdapterImpl.java`

Wesentliche Konstanten und Methoden:

```java
private static final String RIS_BASE_URL = "https://data.bka.gv.at";
private static final String RIS_URL      = "https://www.ris.bka.gv.at";
private static final String RIS_API      = "/ris/api/v2.6";

private static final String RIS_VERSION_INFO = "/version";
private static final String RIS_APP_JUDIKATUR =
    "/Judikatur?Applikation={Applikation}&Rechtssatznummer={Rechtssatznummer}";
private static final String RIS_APP_JUDIKATUR_DOCNUMBER =
    "/Judikatur?Applikation={Applikation}&Suchworte={Suchworte}"
  + "&SucheNachRechtssatz=True&SucheNachText=True";
private static final String RIS_JUDIKATOR_HTML =
    "/Dokumente/{Applikation}/{Dokumentennummer}/{Dokumentennummer}.html";

// Methoden: getVersion(), getJustiz(app, rechtssatznummer), getJustiz(app),
//          getCaselawByDocNumberAsHtml(app, docNumber)
```

## 2. shrinkwrap-legal/shrinkwrap-legal-api — `OgdApplikationEnum.java`

```java
public enum OgdApplikationEnum {
    BundesrechtKonsolidiert("BrKons"),
    LandesrechtKonsolidiert("LrKons"),
    Justiz("Justiz"),
    VfGH("VfGH");
    // -- nicht abgedeckt: Vwgh, Bvwg, Lvwg, Dsk, AsylGH, Normenliste,
    //    Pvak, Gbk, Dok
}
```

## 3. shrinkwrap-legal/shrinkwrap-legal-api — `OgdQueryParam.java`

```java
public static final String APPLIKATION       = "Applikation";
public static final String SUCHWORTE         = "Suchworte";
public static final String DOCNUMBER         = "Dokumentennummer";
public static final String RECHTSSATZNUMMER  = "Rechtssatznummer";
public static final DateTimeFormatter QUERY_DATE_FORMATTER =
    DateTimeFormatter.ofPattern("yyyy-MM-dd");
```

## 4. philrox/ris-mcp-ts — Dokument-Präfix-Mapping

Quelle: `https://github.com/philrox/ris-mcp-ts/blob/main/src/client.ts`

```ts
const DOCUMENT_URL_PATTERNS: Record<string, string> = {
  NOR:   'https://ris.bka.gv.at/Dokumente/Bundesnormen/{nr}/{nr}.html',
  JJR:   'https://ris.bka.gv.at/Dokumente/Justiz/{nr}/{nr}.html',
  JWT:   'https://ris.bka.gv.at/Dokumente/Justiz/{nr}/{nr}.html',
  JWR:   'https://ris.bka.gv.at/Dokumente/Vwgh/{nr}/{nr}.html',
  JFR:   'https://ris.bka.gv.at/Dokumente/Vfgh/{nr}/{nr}.html',
  JFT:   'https://ris.bka.gv.at/Dokumente/Vfgh/{nr}/{nr}.html',
  BVWG:  'https://ris.bka.gv.at/Dokumente/Bvwg/{nr}/{nr}.html',
  LVWG:  'https://ris.bka.gv.at/Dokumente/Lvwg/{nr}/{nr}.html',
  DSB:   'https://ris.bka.gv.at/Dokumente/Dsk/{nr}/{nr}.html',
  GBK:   'https://ris.bka.gv.at/Dokumente/Gbk/{nr}/{nr}.html',
  PVAK:  'https://ris.bka.gv.at/Dokumente/Pvak/{nr}/{nr}.html',
  ASYLGH:'https://ris.bka.gv.at/Dokumente/AsylGH/{nr}/{nr}.html',
  // Bundesgesetzblätter:
  BGBLA: 'https://ris.bka.gv.at/Dokumente/BgblAuth/{nr}/{nr}.html',
  BGBL:  'https://ris.bka.gv.at/Dokumente/BgblAlt/{nr}/{nr}.html',
};

// Validierung: ^[A-Z][A-Z0-9_]+$, Länge 5–50.
const ALLOWED_DOCUMENT_HOSTNAMES = [
  'data.bka.gv.at', 'www.ris.bka.gv.at', 'ris.bka.gv.at'
];
```

## 5. philrox/ris-mcp-ts — Judikatur-Tool

Quelle: `https://github.com/philrox/ris-mcp-ts/blob/main/src/tools/judikatur.ts`

Pflicht: `gericht` + mindestens eines von `suchworte`, `norm`, `geschaeftszahl`.
Optional: `entscheidungsdatum_von`, `entscheidungsdatum_bis`, `seite`, `limit`.

`gericht`-Enum:
```
Justiz | Vfgh | Vwgh | Bvwg | Lvwg | Dsk | AsylGH | Normenliste
| Pvak | Gbk | Dok
```

Mapping `limit` → `DokumenteProSeite`: `10→Ten, 20→Twenty, 50→Fifty, 100→OneHundred`.

## 6. Differenz zur shrinkwrap-Implementierung

| Aspekt | shrinkwrap-legal-api | ris-mcp-ts | für Skill nötig |
|---|---|---|---|
| Applikationen | 4 (Justiz, VfGH, BrKons, LrKons) | 11 Gerichts-Werte | 11 |
| Suchparameter | Suchworte, Rechtssatznummer | + Norm, Geschäftszahl, Datum | + Norm, GZ, Datum |
| Pagination | nicht modelliert | `DokumenteProSeite`+`Seitennummer` | beides nötig |
| Doc-URL | nur HTML-Suffix | Präfix-Mapping | Mapping nutzen |
| SSRF-Schutz | – | Hostname-Whitelist | im Skill empfehlen |

→ Für einen produktiv nutzbaren Skill ist die Verbreiterung über
shrinkwrap-legal-api hinaus zwingend; `ris-mcp-ts` ist hier die solidere
Vorlage.
