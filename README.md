# BTicino MyHome MH201 for Home Assistant

Integrazione Home Assistant **locale** per impianti BTicino MyHome raggiungibili tramite gateway **MH201** e protocollo **OpenWebNet**.

**Versione prevista per questo rilascio: 0.3.0.**

[Guida installazione e utilizzo](USAGE.md) · [Roadmap tecnica](docs/roadmap.md) · [Note protocollo](docs/protocol.md) · [Changelog](CHANGELOG.md)

---

## Italiano

### Cos'è

BTicino MyHome MH201 collega Home Assistant direttamente al gateway MH201 sulla rete locale, usando OpenWebNet. Il percorso di controllo non utilizza cloud BTicino, Netatmo o Legrand.

L'integrazione mantiene una sessione OpenWebNet per i comandi e una sessione separata per gli eventi. Gli stati Home Assistant vengono aggiornati da eventi o risposte reali ricevute dal BUS: un comando trasmesso **non viene considerato prova** che il dispositivo abbia cambiato stato.

### Stato del progetto

La superficie software è coperta da test automatici su Home Assistant 2025.1 / Python 3.12 e Home Assistant 2026.9 / Python 3.14, con Ruff, mypy, pytest, Hassfest e validazione HACS.

L'ultimo baseline software prima del rilascio 0.3.0 contiene **165 test** con **73,51% di coverage**. La validazione su un impianto Home Assistant reale e su un MH201 fisico resta separata: le funzioni protocol-sensitive sono indicate come hardware-validation-pending finché non vengono confermate con traffico reale.

### Funzioni supportate

| WHO | Area | Supporto attuale |
| --- | --- | --- |
| 0 | Scenari | Attivazione scenari e device trigger Home Assistant |
| 1 | Luci | Solo ON/OFF e rilevamento stato |
| 2 | Tapparelle / automazione | Apri, chiudi, stop; posizione 0–100% solo per attuatori avanzati con DIM=10/DIM=11 |
| 4 | Termoregolazione | Climate, temperatura, setpoint, modalità/protezioni e profili heating/cooling supportati dal modello OpenWebNet implementato |
| 5 | Antifurto 4200C | Stato centrale, arm/disarm, 8 partizioni, inserimento selettivo, attivazione/parzializzazione partizione, diagnostica batteria/rete e allarmi tecnici |
| 6 | Videocitofonia / HomeTouch | Apriporta reference-backed e acquisizione diagnostica raw WHO=6/7 |
| 7 | Multimedia VDE | Riconosciuto come famiglia camera/multimedia; nessuna entità audio/video/camera |
| 18 | Energy Management | Sensore read-only di potenza attiva DIM=113 in watt per endpoint `5N` documentati |

### Cosa non fa

Sono esclusi intenzionalmente dal progetto:

- WHO=22;
- media player, audio, musica e diffusione sonora;
- dimmer, brightness e transition WHO=1;
- WHO=3: non fa parte del modello Energy di questa integrazione; l'energia usa esclusivamente WHO=18;
- streaming audio/video e piattaforma camera per HomeTouch/VDE;
- stato “campanello in corso” finché non viene identificato un lifecycle call-start/call-end affidabile sul target MH201 + HomeTouch.

### Modello MH201 e OpenWebNet

```text
Home Assistant
      |
   ConfigEntry
      |
      +-- MH201 (hub)
      |      +-- sessione comandi
      |      +-- sessione eventi
      |
      +-- Device Manager
             +-- endpoint WHO/WHERE
             +-- endpoint WHO/WHERE
```

La sintassi OpenWebNet è isolata in `custom_components/bticino_myhome/protocol/`. I platform Home Assistant consumano eventi normalizzati e non interpretano direttamente stringhe wire-format.

Moduli protocollo dedicati:

- `automation.py` — WHO=2 tapparelle avanzate;
- `thermoregulation.py` — WHO=4;
- `alarm.py` — WHO=5 / target 4200C;
- `door_entry.py` — WHO=6 apriporta;
- `energy.py` — WHO=18 potenza attiva.

### Discovery e configurazione dispositivi

L'MH201 può essere rilevato tramite SSDP oppure configurato manualmente con host/IP, porta OpenWebNet e password opzionale. La porta predefinita è `20000`.

I dispositivi possono essere aggiunti in tre modi:

1. **Scansione automatica conservativa**: usa solo probe supportati e non crea endpoint senza evidenza coerente.
2. **Apprendimento passivo**: ascolta il BUS senza inviare comandi; durante la finestra di ascolto si usano i comandi fisici da identificare.
3. **Aggiunta manuale**: registra WHO, WHERE, tipo dispositivo e opzioni specifiche.

La rimozione è sempre esplicita: una mancata risposta durante una scansione non cancella automaticamente dispositivi già configurati.

### Antifurto 4200C

WHO=5 è modellato specificamente per il target BTicino 4200C:

- stato centrale ENGAGED/DISENGAGED;
- eventi di allarme supportati dalla tabella WHAT ufficiale;
- partizioni 1–8, con stato attiva/parzializzata;
- arm totale e disarm totale;
- arm con elenco delle partizioni che devono restare attive;
- attivazione o parzializzazione di una singola partizione;
- diagnostica read-only per problema batteria e presenza rete;
- allarmi tecnici AUX 1–9 come entità diagnostiche disabilitate di default.

I comandi di controllo 4200C sono reference-backed e testati software-side, ma rimangono **hardware-validation-pending** sul percorso reale 4200C → BUS → MH201.

### HomeTouch 7"

Il target videocitofonico è volutamente minimale: **aprire la porta** e, in futuro, **sapere quando qualcuno suona**. Non sono previsti audio o video.

Il comando apriporta WHO=6 è implementato come superficie reference-backed. Il sensore raw WHO=6/7, disabilitato di default, serve a catturare il traffico necessario a identificare in modo affidabile l'inizio e la fine di una chiamata HomeTouch. Non viene inventato un binary sensor “ring” usando WHAT non documentati.

### Energy Management

L'Energy Management del progetto usa **WHO=18**. La superficie attuale espone la potenza attiva DIM=113 in watt sugli endpoint energy meter `5N` documentati. Non viene eseguito polling periodico e non vengono creati valori ottimistici.

Totalizzatori e altre dimensioni WHO=18 restano fuori dal rilascio finché unità, reset semantics e comportamento reale sul target non sono sufficientemente validati.

### Installazione

Per la procedura HACS, configurazione del gateway, discovery, aggiunta manuale, allarme, apriporta, Energy Management, diagnostica e troubleshooting usa la guida dedicata:

**[USAGE.md — Installazione e manuale d'uso](USAGE.md)**

### Riferimenti tecnici

Fonte primaria: documentazione ufficiale Legrand/BTicino **OpenWebNet Local Interoperability**:

- https://developer.legrand.com/local-interoperability/

Il comportamento viene inoltre confrontato con implementazioni MyHOME mature, senza copiarne automaticamente semantiche non documentate:

- https://github.com/anotherjulien/MyHOME
- https://github.com/mantovanellimatteo/MyHOME
- https://github.com/Dav41K9/ha-MyHOME
- OWNd e binding OpenWebNet di openHAB vengono usati come ulteriori cross-check quando pertinenti.

Repository del progetto:

- https://github.com/donatomontrone/bticino-myhome-mh201

---

## English

### What it is

BTicino MyHome MH201 is a **local** Home Assistant integration for BTicino MyHome installations reachable through an **MH201** gateway and the **OpenWebNet** protocol. The control path does not use the BTicino, Netatmo or Legrand cloud.

The integration keeps a command OpenWebNet session and a separate event session. Home Assistant state is updated from actual BUS events or status responses: sending a command is **not treated as proof** that the physical device changed state.

### Project status

The software surface is automatically tested against Home Assistant 2025.1 / Python 3.12 and Home Assistant 2026.9 / Python 3.14, with Ruff, mypy, pytest, Hassfest and HACS validation.

The latest pre-0.3.0 software baseline contains **165 tests** and **73.51% coverage**. Validation on a real Home Assistant installation and physical MH201 remains a separate final step; protocol-sensitive features stay hardware-validation-pending until confirmed with real traffic.

### Supported features

| WHO | Area | Current support |
| --- | --- | --- |
| 0 | Scenarios | Scenario activation and Home Assistant device triggers |
| 1 | Lighting | ON/OFF and state only |
| 2 | Automation / shutters | Open, close, stop; 0–100% position only for advanced actuators exposing DIM=10/DIM=11 |
| 4 | Thermoregulation | Climate, temperature, setpoint, supported operation/protection modes and heating/cooling profiles |
| 5 | 4200C burglar alarm | Central state, arm/disarm, 8 partitions, selective arm, per-partition active/partialized control, battery/network and technical-alarm diagnostics |
| 6 | Door entry / HomeTouch | Reference-backed door release and raw WHO=6/7 diagnostics |
| 7 | VDE multimedia | Recognized as the camera/multimedia family; no audio/video/camera entity |
| 18 | Energy Management | Read-only DIM=113 active-power sensor in watts for documented `5N` endpoints |

### Intentionally unsupported

The following are deliberately outside project scope:

- WHO=22;
- media player, audio, music and sound diffusion;
- WHO=1 dimmer/brightness/transition control;
- WHO=3; Energy Management is modeled only through WHO=18;
- audio/video streaming and camera entities for HomeTouch/VDE;
- a doorbell-ring state until a reliable call-start/call-end lifecycle is identified for MH201 + HomeTouch.

### Architecture

```text
Home Assistant
      |
   ConfigEntry
      |
      +-- MH201 hub
      |      +-- command session
      |      +-- event session
      |
      +-- Device Manager
             +-- WHO/WHERE endpoint
             +-- WHO/WHERE endpoint
```

OpenWebNet wire-format knowledge is kept inside `custom_components/bticino_myhome/protocol/`. Home Assistant platforms consume normalized events instead of parsing raw frames themselves.

### Discovery and device setup

The MH201 can be discovered through SSDP or configured manually with host/IP, OpenWebNet port and optional password. The default port is `20000`.

Endpoints can be added through conservative active discovery, passive BUS learning, or manual WHO/WHERE registration. Removal is explicit; a missing discovery reply never automatically deletes a configured endpoint.

### 4200C burglar alarm

WHO=5 is modeled around the BTicino 4200C target: central state, partitions 1–8, alarm evidence, full arm/disarm, selected-active-partition arm, per-partition active/partialized control, battery/network diagnostics and technical alarm AUX 1–9 diagnostics.

Control commands are reference-backed and software-tested but remain **hardware-validation-pending** on the actual 4200C → BUS → MH201 path.

### HomeTouch 7"

The requested door-entry scope is intentionally limited to **door release** and, later, **ring detection**. Audio/video is not a target. WHO=6 door release is implemented as a reference-backed surface; the disabled-by-default raw WHO=6/7 diagnostic sensor is intended to identify the actual call-start/call-end lifecycle before a ring binary sensor is added.

### Energy Management

Energy Management uses **WHO=18**. The current production surface exposes DIM=113 active power in watts for documented `5N` energy-meter endpoints. No periodic polling or optimistic measurement is used.

### Installation and usage

See the bilingual step-by-step manual:

**[USAGE.md — Installation and complete usage guide](USAGE.md)**

### Technical references

Primary source: official Legrand/BTicino **OpenWebNet Local Interoperability** documentation:

- https://developer.legrand.com/local-interoperability/

Additional mature references used for cross-checking where relevant:

- https://github.com/anotherjulien/MyHOME
- https://github.com/mantovanellimatteo/MyHOME
- https://github.com/Dav41K9/ha-MyHOME
- OWNd and the openHAB OpenWebNet binding.

Project repository:

- https://github.com/donatomontrone/bticino-myhome-mh201

---

## License

See [LICENSE](LICENSE).
