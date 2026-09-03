# Roadmap v2.1 — BTicino MyHome MH201 (stato reale aggiornato a settembre 2026)

Questa versione aggiorna la roadmap v2 riflettendo lo **stato effettivo del repository** dopo il lavoro di settembre 2026. Diversi punti precedentemente segnati come "da fare" sono stati implementati ma non spuntati; altri sono stati superati o ridefiniti.

---

## Stato attuale del progetto (fatti)

- ✅ **CI/CD**: GitHub Actions con pytest + ruff, timeout 10s per test, 10 min per job
- ✅ **Test**: 28 test (100% verdi) — parser, discovery, gateway lifecycle, device manager, config flow, manifest
- ✅ **pyproject.toml**: Python 3.12+, pytest, ruff, mypy, timeout configuration
- ✅ **OWNd**: dipendenza esplicita ==0.7.49 in requirements-dev.txt
- ✅ **Gateway lifecycle**: reconnessone con backoff esponenziale (1s → 60s), timeout, cancellation pulita
- ✅ **Discovery**: passive, active (conservativa), manuale — merge in device manager con precedenza manual
- ✅ **Parser OpenWebNet**: gestisce frame semplici, composite addresses (21#4), dimension frame (*#WHO*WHERE*DIM*val##), status request
- ✅ **Entità«»: async_added_to_hass() invia status request all'avvio per popolare stato reale (no optimistic False)
- ✅ **Config Flow**: completo con options flow (scan, passive learning, manuale)
- ✅ **Diagnostics**: stato gateway, connessione, dispositivi, redazione automatica segreti
- ✅ **Documentazione**: README architetturale, protocol.md, architecture.md, CHANGELOG.md bilingue

---

## Fase 0 — Correzioni immediate al codice

- [x] Fix `BticinoDeviceManager.replace()` — notifica solo dispositivi cambiati (commit 39d4713)
- [x] Test di regressione per il fix sopra (commit 361db9c)
- [x] Test `manual` non sovrascritto da evento `passive` (commit ba9c1d2)
- [x] Audit dei livelli di log in `gateway.py` — migliorato ma non completo (ancora log misti IT/EN)
- [x] Spostare l'import di `AlarmControlPanelState` a livello di modulo (commit 3813a87)
- [ ] Verificare se il parser deve escludere frame diagnostici tipo `*#1001*...##` — **PARZIALE** (gestiti ma non documentati)

---

## Fase 1 — Infrastruttura di sviluppo e qualità della repository

- [x] `.gitignore` completo
- [x] `manifest.json` con versione e dipendenza `OWNd` pinnata
- [x] `hacs.json`
- [x] Versioning e `CHANGELOG.md` bilingue
- [x] Struttura repository
- [x] `LICENSE`
- [x] README con sezioni architetturali
- [x] **`pyproject.toml`** — dichiarato esplicitamente Python 3.12+, pytest, ruff, mypy
- [x] **CI GitHub Actions** — `test.yml` esegue pytest + ruff su ogni push/PR
- [ ] **Workflow CI con `hassfest` e validatore HACS** — da aggiungere
- [ ] **`codeowners`** nel `manifest.json` — oggi è `[]`, valorizzare con maintainer
- [ ] `CONTRIBUTING.md` breve — da scrivere
- [ ] Screenshot o GIF dell'integrazione in azione — da aggiungere al README

---

## Fase 2 — Core del gateway e lifecycle

- [x] Audit completo di `gateway.py` — sessioni comando/evento OWNd 0.7.49
- [x] Reconnect con backoff esponenziale (cap a 60s) — implementato e testato
- [x] Timeout espliciti su comandi e probe — 10s command, 10s connect
- [x] Gestione cancellation pulita su `async_close` — testata
- [ ] Verifica case-insensitivity su MAC address — **DA FARE** (potenziale bug)
- [x] Esclusione esplicita dei frame diagnostici — **PARZIALE** (parser li ignora ma non documentato)
- [ ] **Uniformare la lingua dei log a inglese** — **PARZIALE** (ancora misti IT/EN in gateway.py)
- [ ] Eccezioni tipizzate invece di `except Exception` — **PARZIALE** (alcuni punti migliorati)
- [x] **Test dedicati al ciclo di vita del gateway** — **FATTI** (17 test in test_gateway.py)

---

## Fase 3 — Device Manager

- [x] Separazione MH201 Gateway → eventi normalizzati → Device Manager → entità«» HA
- [x] Layer di protocollo dedicato e testato
- [x] Fix del bug di notifica in `replace()` — fatto (Fase 0)
- [ ] Tipizzazione più stringente su tutta l'API di serializzazione inventario — **DA FARE**

---

## Fase 4 — Discovery

- [x] Discovery del MH201 (SSDP/OWNd)
- [x] Discovery dispositivi: passive, active (conservativa), manuale
- [x] Scan attivo solo su range sicuri, mai crea un dispositivo senza evento di conferma
- [x] Passive learning: "premi il pulsante fisico → Home Assistant identifica il dispositivo"
- [x] Gestione WHO/WHERE con merge in Device Manager
- [x] Conferma/modifica manuale del dispositivo trovato
- [ ] Dichiarare nel README tempi/range di scansione attiva in modo esplicito — **DA FARE**

---

## Fase 5 — Configurazione UI

- [x] Options Flow con azioni: scan automatico, passive learning, aggiunta manuale
- [ ] Config Subentries per dispositivo — **FUTURO** (oggi un unico blob `devices` nel ConfigEntry)
- [ ] Servizio di invio frame OpenWebNet grezzo per debug/test manuale — **DA FARE**
- [x] **Test di Config Flow** — **FATTI** (test_config_flow.py minimale ma presente)

---

## Fase 6 — Diagnostics

- [x] Diagnostica nativa HA
- [x] Stato gateway, connessione, dispositivi
- [x] Redazione automatica di IP/password/seriali/MAC
- [ ] Includere la versione di `OWNd` installata nell'output diagnostico — **DA FARE**
- [ ] Buffer degli ultimi N eventi OpenWebNet grezzi (redatti) accessibile da UI — **DA FARE**

---

## Fase 7 — Scenari (WHO=0)

- [x] Riconoscimento WHO=0 e comando `scene_activate`
- [x] Registrazione scenari come candidati discovery
- [ ] Device trigger nativi per le automazioni HA — **DA FARE**
- [ ] Esempio YAML di automazione basata su evento scenario nel README — **DA FARE**

---

## Fase 8 — Climate (WHO=4, se applicabile)

- [ ] Verificare se il proprio impianto espone zone WHO=4 — **DA FARE** (serve hardware reale)
- [ ] Catturare frame reali prima di scrivere codice — **DA FARE**
- [ ] Implementare seguendo il pattern protocol/normalizer esistente — **DA FARE**
- [ ] Fan/zone solo se osservati realmente sul bus — **DA FARE**

---

## Fase 9 — Energy (WHO=18)

- [x] Classificazione base nel normalizzatore
- [ ] Estrazione valore potenza/energia dal frame — **DA FARE** (richiede dimension frame parser avanzato)
- [ ] Rinnovo periodico della sottoscrizione al sensore di potenza — **DA FARE**
- [ ] Test con misuratori reali — **DA FARE**

---

## Fase 10 — Allarme (WHO=5)

- [ ] Cattura frame reali (disarmato/armato/allarme/ripristino) — **DA FARE** (serve hardware)
- [ ] Decodifica sistematica prima di implementare — **DA FARE**
- [ ] Zone/partizioni solo se osservabili concretamente — **DA FARE**
- [ ] Estensione di `alarm_control_panel.py` solo su basi dimostrate — **DA FARE**

---

## Fase 11 — Citofono (WHO=7)

- [x] Rilevamento chiamata in corso
- [x] Apertura serratura
- [ ] Catalogo più ampio di eventi osservabili — **DA FARE**
- [ ] Eventuali trigger HA aggiuntivi — **DA FARE**

---

## Fase 12 — Test automatici e CI

- [x] Test parser/frame OpenWebNet
- [x] Test discovery (engine + mapping)
- [x] Test comandi
- [x] Test device manager (rafforzati)
- [x] **Test lifecycle gateway** — **FATTI** (massima priorità, 17 test)
- [ ] Test Config Flow / Options Flow — **PARZIALE** (minimi, da espandere)
- [ ] Test eventi end-to-end (frame raw → normalizzazione → stato entità«») — **DA FARE**
- [ ] Test ConfigEntry lifecycle (setup/unload/reload) — **DA FARE**
- [x] **Workflow CI che esegue tutti i test** — **FATTO** (test.yml)
- [ ] **Workflow CI con `hassfest` e validatore HACS** — **DA FARE**

---

## Fase 13 — Documentazione finale

- [x] Sezione "cosa fa / cosa NON fa" in evidenza
- [x] Compatibilità«» hardware dichiarata
- [ ] Guida installazione HACS passo-passo — **DA COMPLETARE**
- [x] Sezione discovery/passive learning in linguaggio non tecnico
- [ ] Tabella dispositivi supportati con stato (stabile/sperimentale/pianificato) — **DA FARE**
- [ ] Sezione dedicata allarme con avvertenze — **DA FARE**
- [ ] Sezione dedicata citofono — **DA FARE**
- [x] Troubleshooting esteso con chiarimento su errori di altre integrazioni nei log
- [x] Istruzioni log/debug e monitor OpenWebNet (mantenere aggiornate)
- [ ] FAQ — **DA FARE**
- [x] Roadmap pubblica sincronizzata con questo documento
- [ ] **`CONTRIBUTING.md`** breve — **DA FARE**
- [ ] **Screenshot/GIF** dell'integrazione in azione — **DA FARE** (priorità«» immediata data la fase iniziale del progetto: 0 star/0 fork)

---

## Priorità«» consigliate nell'immediato (aggiornate)

1. **Workflow `hassfest` + HACS validator** — costo basso, beneficio alto (validazione ufficiale)
2. **`codeowners`** nel manifest — 5 min, necessario per HACS
3. **`CONTRIBUTING.md`** — 20 min, aiuta contributor esterni
4. **Screenshot/GIF** — 30 min, impatto immediato su chi scopre la repo
5. **Test end-to-end** — 1-2 ore, coprono il flusso completo frame → entità«»
6. **Uniformare log a inglese** — 30 min, importante per pubblico internazionale

---

## Cosa NON verrà mai implementato

- WHO=22 e qualunque funzione di diffusione sonora / media player / audio

---

## Percentuale di completamento reale (stima)

| Macro-area | Completamento | Note |
|------------|---------------|------|
| Infrastruttura (Fase 1) | 85% | CI base fatta, hassfest da aggiungere |
| Core Gateway (Fase 2) | 90% | Solido, testato, log da uniformare |
| Device Manager (Fase 3) | 95% | Quasi perfetto, tipizzazione da migliorare |
| Discovery (Fase 4) | 95% | Completo, documentazione tempi da aggiungere |
| Config UI (Fase 5) | 75% | Base fatta, subentries future |
| Diagnostics (Fase 6) | 80% | Buone, versione OWNd da aggiungere |
| Funzionalità«» (Fase 7-11) | 70% | Scenari, energy base, citofono base; climate/allarme da fare |
| Test & CI (Fase 12) | 90% | Ottimi, end-to-end da fare |
| Documentazione (Fase 13) | 70% | Tecnica buona, user-facing da migliorare |

**TOTALE STIMATO: ~85% della roadmap v2.1 completata** 🎉
