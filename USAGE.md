# BTicino MyHome MH201 — Installation and Usage Guide

Guida pratica bilingue per installare e usare l'integrazione Home Assistant **BTicino MyHome MH201**.

[README](README.md) · [Roadmap](docs/roadmap.md) · [Protocol notes](docs/protocol.md)

---

# Italiano

## 1. A cosa serve

Questa integrazione permette a Home Assistant di comunicare **localmente** con un impianto BTicino MyHome tramite gateway **MH201** e protocollo **OpenWebNet**.

Non utilizza il cloud per il percorso di controllo. Home Assistant comunica direttamente con l'MH201 sulla LAN, normalmente sulla porta TCP `20000`.

Le funzioni principali attualmente disponibili sono:

- scenari WHO=0;
- luci WHO=1, solo ON/OFF;
- tapparelle WHO=2, comprese le posizioni avanzate quando il dispositivo le supporta;
- termoregolazione WHO=4;
- antifurto WHO=5, con target BTicino 4200C;
- apriporta WHO=6 per il target HomeTouch;
- diagnostica raw WHO=6/7 per identificare il lifecycle della chiamata citofonica;
- potenza attiva WHO=18.

## 2. Requisiti

Prima di iniziare servono:

1. Home Assistant compatibile con la release dell'integrazione. La CI verifica Home Assistant 2025.1 e 2026.9.
2. Un gateway BTicino MH201 raggiungibile dalla stessa rete di Home Assistant.
3. Porta OpenWebNet raggiungibile, normalmente `20000`.
4. Password OpenWebNet, se configurata sul gateway.
5. HACS installato, se si desidera l'installazione consigliata tramite HACS.

## 3. Installazione con HACS

### 3.1 Aggiungere la repository personalizzata

1. Apri **HACS** in Home Assistant.
2. Apri il menu delle repository personalizzate. La posizione esatta può cambiare leggermente in base alla versione di HACS.
3. Inserisci:

   `https://github.com/donatomontrone/bticino-myhome-mh201`

4. Seleziona la categoria **Integration**.
5. Conferma.

### 3.2 Installare l'integrazione

1. Cerca **BTicino MyHome MH201** in HACS.
2. Apri la scheda dell'integrazione.
3. Seleziona **Download** / **Install**.
4. Installa l'ultima release disponibile.
5. Riavvia Home Assistant quando richiesto.

## 4. Aggiungere l'MH201 a Home Assistant

Dopo il riavvio:

1. Vai in **Impostazioni → Dispositivi e servizi**.
2. Seleziona **Aggiungi integrazione**.
3. Cerca **BTicino MyHome MH201**.

### 4.1 Discovery SSDP

Se Home Assistant rileva automaticamente l'MH201, verrà proposta una configurazione scoperta. Controlla:

- indirizzo del gateway;
- porta OpenWebNet;
- password, se necessaria.

Conferma per creare la ConfigEntry.

### 4.2 Configurazione manuale

Se l'MH201 non viene trovato automaticamente, inserisci:

- **Host/IP**: indirizzo locale dell'MH201;
- **Porta**: normalmente `20000`;
- **Password OpenWebNet**: lascia vuoto solo se il gateway non la richiede.

L'integrazione prova la connessione prima di salvare la configurazione.

## 5. Aggiungere i dispositivi MyHome

L'installazione iniziale dell'MH201 **non esegue automaticamente una scansione completa del BUS**. I dispositivi vengono gestiti dalle Opzioni dell'integrazione.

Apri:

**Impostazioni → Dispositivi e servizi → BTicino MyHome MH201 → Configura / Opzioni**.

Sono disponibili quattro modalità operative.

### 5.1 Scansione automatica

La scansione automatica esegue solo probe conservativi supportati dal progetto. Un endpoint non viene creato solo perché un indirizzo potrebbe esistere: deve esserci evidenza OpenWebNet coerente.

Puoi impostare anche una breve finestra aggiuntiva di ascolto eventi.

Gli scenari possono essere inclusi durante la finestra di discovery abilitando l'opzione dedicata.

### 5.2 Apprendimento passivo

Questa è la modalità più sicura per identificare dispositivi già presenti sul BUS.

1. Scegli **Apprendi dai comandi fisici**.
2. Imposta il tempo di ascolto.
3. Avvia l'apprendimento.
4. Durante l'ascolto usa fisicamente i comandi BTicino che vuoi identificare: interruttori, tapparelle, scenari ecc.
5. Alla fine seleziona gli endpoint rilevati che vuoi salvare.

Durante l'apprendimento passivo l'integrazione ascolta il traffico senza inviare comandi di discovery.

### 5.3 Aggiunta manuale

Usa l'aggiunta manuale quando conosci già WHO e WHERE del dispositivo o quando una famiglia non deve essere sottoposta a scansione ampia.

Campi principali:

- **WHO**: famiglia OpenWebNet;
- **WHERE**: indirizzo OpenWebNet esatto del dispositivo;
- **Tipo dispositivo**: superficie Home Assistant da creare;
- **Nome**: opzionale.

Tipi utilizzabili nel perimetro attuale:

| Tipo | WHO tipico | Note |
| --- | --- | --- |
| Scenario | 0 | Attivazione scenario |
| Luce | 1 | Solo ON/OFF |
| Tapparella | 2 | Apri/chiudi/stop; opzione avanzata per posizione |
| Termoregolazione | 4 | Profilo heating/cooling configurabile |
| Allarme | 5 | Target 4200C; normalmente endpoint centrale WHERE `0` |
| Videocitofonia / apriporta | 6 | Target HomeTouch; apriporta e diagnostica raw |
| Energia | 18 | Potenza attiva su endpoint `5N` documentati |

**WHO=3 non è supportato e non viene usato per l'Energy Management.**

### 5.4 Rimuovere un dispositivo

Scegli **Rimuovi dispositivi configurati**, seleziona gli endpoint e conferma.

La rimozione è esplicita. Un dispositivo non viene eliminato automaticamente solo perché non risponde a una scansione.

## 6. Luci WHO=1

Il supporto WHO=1 è volutamente limitato a:

- accensione;
- spegnimento;
- stato ON/OFF ricevuto dal BUS.

Dimmer, brightness e transition non fanno parte del progetto.

L'entità non aggiorna ottimisticamente lo stato dopo un comando: attende un evento o una risposta OpenWebNet.

## 7. Tapparelle WHO=2

Tutte le tapparelle supportate espongono:

- apri;
- chiudi;
- stop.

Per un attuatore avanzato, durante l'aggiunta manuale abilita **Controllo posizione tapparella avanzata** solo se il dispositivo supporta lo stato DIM=10 e il comando GoToLevel DIM=11.

In quel caso Home Assistant espone anche **SET_POSITION** 0–100%.

La posizione `255` OpenWebNet viene trattata come sconosciuta, non come una percentuale stimata.

## 8. Termoregolazione WHO=4

Per una zona climate aggiunta manualmente puoi scegliere il profilo:

- solo riscaldamento;
- solo raffrescamento;
- riscaldamento e raffrescamento.

Il profilo serve a non esporre modalità che l'impianto non supporta. Ad esempio una zona KW4691 usata solo per riscaldamento a pavimento deve essere configurata come **heating only**.

La superficie supporta il modello software implementato per:

- temperatura corrente;
- setpoint;
- modalità OFF / manuale / programmazione compatibili con il profilo;
- protezione antigelo/termica dove pertinente;
- scrittura setpoint DIM=14;
- stato uscite/valvole DIM=19 in forma conservativa.

Anche qui non vengono usati aggiornamenti ottimistici.

## 9. Antifurto WHO=5 — target BTicino 4200C

Aggiungi il sistema come dispositivo manuale WHO=5, tipo **Allarme**, normalmente con WHERE centrale `0`.

Home Assistant crea:

- un `alarm_control_panel`;
- 8 sensori di partizione;
- diagnostica batteria;
- diagnostica presenza rete;
- sensori di allarme tecnico AUX 1–9, disabilitati di default per evitare di riempire inutilmente l'interfaccia.

### 9.1 Stato centrale

Lo stato viene ricavato da evidenza WHO=5 ricevuta dal BUS:

- ENGAGED → armato;
- DISENGAGED → disarmato;
- eventi di intrusione/tamper/panic supportati → triggered.

### 9.2 Arm e disarm totale

Usa i normali comandi dell'entità `alarm_control_panel`:

- **Arm away** → inserimento totale;
- **Disarm** → disinserimento totale.

Il comando inviato non cambia lo stato Home Assistant da solo: l'integrazione aspetta il feedback OpenWebNet.

### 9.3 Inserimento con partizioni selezionate

L'azione Home Assistant:

`bticino_myhome.arm_alarm_partitions`

richiede:

- `config_entry_id`: il gateway MH201 configurato;
- `partitions`: elenco delle partizioni 1–8 che devono restare attive.

Le partizioni non selezionate vengono parzializzate secondo la sintassi OpenWebNet legacy reference-backed utilizzata dal progetto.

### 9.4 Attivare o parzializzare una singola partizione

Usa:

`bticino_myhome.set_alarm_partition`

Campi:

- `config_entry_id`;
- `partition`: numero 1–8;
- `active: true` per renderla attiva;
- `active: false` per parzializzarla.

### 9.5 Diagnostica 4200C

La richiesta completa `*#5*0##` viene usata per l'hydration delle diagnostiche centrali.

Le entità espongono:

- **Problema batteria**: attivo con WHAT=4 o WHAT=10, ripristinato da WHAT=5;
- **Connettività rete**: presente con WHAT=7, assente con WHAT=6;
- **Allarme tecnico AUX N**: attivo con WHAT=12 su `#N`, ripristinato da WHAT=13 sullo stesso `#N`.

I sensori AUX tecnici sono disabilitati di default e possono essere abilitati dalla pagina delle entità se utili nell'impianto.

Il WHAT=14 “no reception / ACK peripheral device” non viene trasformato in uno stato persistente finché non viene stabilito un lifecycle di reset affidabile sul target reale.

**Importante:** arm/disarm e partizionamento sono software-tested e reference-backed, ma devono ancora essere validati fisicamente con la centrale 4200C attraverso MH201.

## 10. HomeTouch 7" / apriporta

Il progetto non tenta di fornire audio o video.

La superficie attuale include:

- pulsante **Apriporta** WHO=6;
- sensore diagnostico raw WHO=6/7, disabilitato di default.

Il sensore raw serve a catturare il traffico reale HomeTouch/MH201 quando qualcuno suona. Un binary sensor “campanello” verrà aggiunto solo dopo avere identificato frame ripetibili di inizio e fine chiamata.

## 11. Energy Management WHO=18

Per un energy meter documentato usa un WHERE `5N`, con `N` nel range previsto dalla specifica OpenWebNet.

La superficie attuale crea un sensore Home Assistant:

- device class: `POWER`;
- unità: watt;
- state class: `MEASUREMENT`;
- sorgente: DIM=113 Active Power.

Il sensore viene inizializzato tramite richiesta DIM=113 e poi aggiornato solo da evidenza OpenWebNet. Non esegue polling periodico.

## 12. Scenari WHO=0

Gli scenari configurati possono essere attivati da Home Assistant e usati anche come device trigger nelle automazioni quando l'evento corrispondente viene osservato.

La discovery non crea automaticamente una lista arbitraria di scenari possibili: vengono mantenuti quelli osservati o aggiunti esplicitamente.

## 13. Azione avanzata `send_frame`

Per debug e validazione è disponibile:

`bticino_myhome.send_frame`

Campi:

- `config_entry_id`;
- `frame`: frame OpenWebNet completo;
- `is_status_request`: abilita solo quando la risposta deve essere reinserita nel percorso di normalizzazione dello stato.

Esempio di frame ON luce:

`*1*1*21##`

Usa questa azione solo se conosci la sintassi OpenWebNet. Non è un sostituto delle entità Home Assistant normali.

## 14. Diagnostica Home Assistant

Dalla pagina dell'integrazione puoi scaricare le diagnostics Home Assistant. I campi sensibili noti, inclusi password, host/IP e identificativi hardware, vengono redatti.

Per logging temporaneo più dettagliato:

```yaml
logger:
  default: warning
  logs:
    custom_components.bticino_myhome.gateway: debug
```

Non pubblicare password o capture non revisionate.

## 15. Capture OpenWebNet

La repository contiene un monitor read-only della sessione EVENT:

```bash
python tools/openwebnet_monitor.py 192.168.1.50 --output capture.txt
```

Per una cattura limitata nel tempo:

```bash
python tools/openwebnet_monitor.py 192.168.1.50 --seconds 300 --output capture.txt
```

La capture reale è particolarmente utile per:

- validare WHO=4 sul proprio impianto;
- confermare i comandi 4200C WHO=5;
- identificare ring start/end HomeTouch;
- confermare il comportamento dei dispositivi WHO=18.

Non provocare volontariamente condizioni di allarme pericolose solo per generare traffico.

## 16. Troubleshooting

### L'integrazione non trova l'MH201

- verifica che Home Assistant e MH201 siano sulla stessa rete raggiungibile;
- prova l'aggiunta manuale con IP e porta `20000`;
- verifica la password OpenWebNet;
- controlla firewall/VLAN.

### Il gateway si configura ma non vedo dispositivi

La configurazione del gateway non implica una scansione completa del BUS. Apri le Opzioni e usa scan, apprendimento passivo o aggiunta manuale.

### Un comando funziona ma lo stato non cambia subito

È intenzionale. L'integrazione non usa stato ottimistico. Home Assistant aspetta l'evidenza OpenWebNet di ritorno.

### Il ring HomeTouch non compare

Non è ancora esposto come binary sensor: serve prima una capture affidabile del lifecycle di chiamata sul target reale.

### Alcune diagnostiche allarme non sono visibili

Gli allarmi tecnici AUX 1–9 sono disabilitati di default. Apri la pagina del dispositivo/entità e abilita solo quelli utili.

## 17. Limitazioni prima della validazione reale

La release software non sostituisce la prova fisica. Restano da verificare in un ambiente reale:

- clean install e upgrade Home Assistant;
- restart / reload ConfigEntry;
- riconnessione prolungata MH201;
- status query WHO=1 sul gateway reale;
- posizione tapparelle avanzate WHO=2;
- termoregolazione WHO=4;
- comandi e diagnostica 4200C WHO=5;
- apriporta e ring lifecycle HomeTouch;
- misure WHO=18.

---

# English

## 1. Purpose

This integration lets Home Assistant communicate **locally** with a BTicino MyHome installation through an **MH201** gateway using **OpenWebNet**. The control path does not rely on the cloud.

Current main surfaces are WHO=0 scenarios, WHO=1 ON/OFF lighting, WHO=2 shutters, WHO=4 thermoregulation, WHO=5 4200C burglar alarm, WHO=6 door release/HomeTouch diagnostics and WHO=18 active power.

## 2. Requirements

You need:

1. A supported Home Assistant version. CI currently validates Home Assistant 2025.1 and 2026.9.
2. A BTicino MH201 reachable from Home Assistant on the local network.
3. OpenWebNet TCP access, normally port `20000`.
4. The OpenWebNet password if your gateway requires one.
5. HACS for the recommended installation method.

## 3. Install with HACS

1. Open **HACS**.
2. Open the custom repositories dialog.
3. Add `https://github.com/donatomontrone/bticino-myhome-mh201` as an **Integration** repository.
4. Open **BTicino MyHome MH201**.
5. Download/install the latest release.
6. Restart Home Assistant.

## 4. Add the MH201 integration

Open **Settings → Devices & services → Add integration** and search for **BTicino MyHome MH201**.

If SSDP discovery finds the gateway, confirm its OpenWebNet port and password. Otherwise enter the MH201 host/IP, port (normally `20000`) and optional password manually.

The integration tests the gateway before saving the ConfigEntry.

## 5. Add MyHome endpoints

Initial gateway setup does not automatically perform a full BUS scan. Open the integration **Options** and choose one of these actions:

- **Automatic scan** — conservative supported probes only;
- **Passive learning** — listen to BUS traffic while you operate physical controls;
- **Manual add** — register a known WHO/WHERE endpoint;
- **Remove** — explicitly remove configured endpoints.

Manual endpoint families in the current scope are scenario WHO=0, light WHO=1, cover WHO=2, climate WHO=4, alarm WHO=5, door entry WHO=6 and energy WHO=18.

**WHO=3 is not supported. Energy Management is WHO=18 only.**

## 6. WHO=1 lighting

WHO=1 is intentionally ON/OFF only. Brightness, dimmer and transition control are outside project scope. State remains evidence-driven from OpenWebNet events/status responses.

## 7. WHO=2 shutters

All supported shutters expose open/close/stop. Enable the manual **advanced shutter** option only for actuators that provide DIM=10 status/position and DIM=11 GoToLevel. Advanced covers expose Home Assistant position control 0–100%. OpenWebNet level 255 remains unknown rather than being estimated.

## 8. WHO=4 thermoregulation

Manual climate endpoints can be restricted to heating only, cooling only, or heating+cooling. The current software model covers temperature, setpoint, compatible modes/protections, DIM=14 setpoint writes and conservative DIM=19 output state handling. State is not updated optimistically.

## 9. WHO=5 — BTicino 4200C

Add the alarm as a manual WHO=5 **Alarm** endpoint, normally using central WHERE `0`.

Home Assistant exposes:

- one `alarm_control_panel`;
- partitions 1–8;
- battery-problem diagnostic;
- network-connectivity diagnostic;
- technical-alarm AUX 1–9 diagnostics, disabled by default.

Use the alarm entity for full arm/disarm. Use `bticino_myhome.arm_alarm_partitions` for a selected active-partition mask and `bticino_myhome.set_alarm_partition` to activate or partialize a single partition.

Battery state follows WHAT 4/5/10, network state follows WHAT 6/7, and technical alarms follow WHAT 12/13 for the matching auxiliary `#N`.

Control commands are reference-backed and software-tested but remain hardware-validation-pending on a real 4200C through MH201.

## 10. HomeTouch / door entry

The project intentionally does not expose audio/video. Current support is a reference-backed WHO=6 **Door release** button plus a disabled-by-default raw WHO=6/7 diagnostic sensor.

Ring indication is intentionally pending until a repeatable call-start/call-end lifecycle is identified on the actual HomeTouch/MH201 installation.

## 11. WHO=18 Energy Management

For documented `5N` energy-meter endpoints, the integration exposes read-only DIM=113 active power in watts with Home Assistant `POWER` / `MEASUREMENT` semantics. No periodic polling or optimistic value is used.

## 12. WHO=0 scenarios

Configured/observed scenarios can be activated and used as Home Assistant device triggers. The integration does not manufacture an arbitrary scenario address range during discovery.

## 13. Advanced raw frame action

`bticino_myhome.send_frame` can send a raw OpenWebNet frame through a selected ConfigEntry. Set `is_status_request` only when returned data frames should be normalized as state evidence.

Example light ON frame:

`*1*1*21##`

Use this action for controlled diagnostics only.

## 14. Diagnostics and logging

Home Assistant diagnostics redact known sensitive fields. Temporary gateway debug logging can be enabled with:

```yaml
logger:
  default: warning
  logs:
    custom_components.bticino_myhome.gateway: debug
```

## 15. OpenWebNet capture tool

Read-only EVENT-session monitoring:

```bash
python tools/openwebnet_monitor.py 192.168.1.50 --output capture.txt
```

Bounded capture:

```bash
python tools/openwebnet_monitor.py 192.168.1.50 --seconds 300 --output capture.txt
```

Use captures to validate the target installation, especially WHO=5 4200C control and the HomeTouch ring lifecycle.

## 16. Troubleshooting

If the MH201 is not discovered, try manual host/port configuration and verify VLAN/firewall/password settings. If the gateway is configured but no endpoints appear, use Options → scan/passive learning/manual add. If an entity does not change state immediately after a command, remember that this integration deliberately waits for OpenWebNet evidence instead of using optimistic state.

## 17. Remaining real-world validation

Before calling the complete system hardware-validated, test clean install/upgrade, ConfigEntry restart/reload, prolonged MH201 reconnect behavior and all protocol-sensitive device families on the physical installation.

---

Primary protocol source: https://developer.legrand.com/local-interoperability/

Project repository: https://github.com/donatomontrone/bticino-myhome-mh201
