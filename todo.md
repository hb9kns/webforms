# agenda / todo

---

## Yargo's notes

_These are just copies from my personal notes._
_Some might therefore be in barely understandable German, sorry._
_-Yargo_

### Ideen/Plan

- mehrere Seiten moeglich, welche gemeinsame Basis teilen, evtl mit Get/Post-Argument oder fixem Seitennamen (wrapper CGI)
- Basisdatei: Flag (+/-/*), Indexnr, Name und weitere Infos
- ignoriert: Kommentarzeilen mit '#' und Leerzeilen
- jedes Basiselement genau 0 oder 1 mal pro Seite vorhanden
- Zugriffsrecht: admin, edit (b x Basis), view; externes Verwaltungs-Skript?
- Seitenstruktur: Header, Tabelle, Footer; nur server-side!
- Header: Link auf Basis-Edit (fuer admin), Sortierknoepfe
- Tabelle: Index/Name aus Basis, Rest frei (Textfelder ohne TAB), Edit- u Del-Knopf
- pro Seite ein File mit Tabellenzeilen, Felder durch TAB getrennt, erstes Feld mit Index aus Basis
- Zeilenschaltungen aus Eingabefeldern in ' // ' umwandeln, TAB in SPC
- Edit-Knopf: erzeugt Form mit dropdown fuer Basis und bevoelkerten Feldern fuer Rest
- Del-Knopf: Rueckfrage mit Anzeige des Basis-Feldes
- Footer: Neu-Knopf, erzeugt leeres Formular wie Edit-Knopf
- Basis-Edit: Tabelle wie fuer Seitn, aber Umblend- statt Del-Knopf (aendert Flag)
