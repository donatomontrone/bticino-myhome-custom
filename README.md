# BTicino MyHome — Home Assistant

Integrazione custom per collegare un gateway **BTicino MH201** a Home Assistant tramite **OpenWebNet direttamente sulla LAN**.

L'integrazione non usa le API cloud BTicino/Legrand/Netatmo per il controllo dei dispositivi. Home Assistant apre una connessione TCP al gateway OpenWebNet, normalmente sulla porta `20000`.

## Cosa gestisce

- luci BUS/SCS (`WHO=1`)
- tapparelle/tende/automazione (`WHO=2`)
- gestione carichi (`WHO=3`)
- allarme 4200C (`WHO=5`, nei limiti di ciò che espone il gateway/OWNd)
- videocitofonia come segnalazione evento (`WHO=7`)
- apertura serratura (`WHO=7`, comando write-only)
- richiamo scenari OpenWebNet (`WHO=0`)
- sensore diagnostico con ultimo frame citofonico grezzo


## Indipendenza dal cloud

Questo è uno degli obiettivi principali dell'integrazione.

Il percorso di controllo è:

```text
Home Assistant
      │
      │ TCP / OpenWebNet
      ▼
BTicino MH201
      │
      │ BUS/SCS
      ▼
Dispositivi BTicino
```

Non è:

```text
Home Assistant → Internet → BTicino Cloud → Impianto
```

Di conseguenza, se il cloud BTicino/Netatmo/Legrand è indisponibile, **il controllo locale da Home Assistant può continuare a funzionare**. La condizione è che:

1. Home Assistant sia acceso;
2. Home Assistant riesca a raggiungere il MH201 sulla LAN;
3. il MH201 sia acceso e collegato al BUS/SCS;
4. la rete locale continui a funzionare.

Se invece cade la LAN o il MH201 non è raggiungibile, nessuna integrazione software locale può comandare il BUS attraverso quel gateway.

La perdita di Internet comporta invece la perdita delle funzioni che richiedono Internet, per esempio accesso remoto a Home Assistant tramite Home Assistant Cloud, servizi cloud del produttore e integrazioni che non hanno un percorso locale.

## Discovery e persistenza

La versione 0.1.2 corregge un problema importante delle versioni legacy 0.1 e 0.1.1: la discovery veniva eseguita ma il risultato non veniva poi passato alle piattaforme Home Assistant.

Ora il flusso è:

```text
Config Flow
    ↓
connessione locale al MH201
    ↓
discovery attiva + ascolto passivo
    ↓
dispositivi trovati
    ↓
persistenza nel ConfigEntry
    ↓
setup delle piattaforme HA
```

Al riavvio Home Assistant vengono usati i dispositivi già trovati in precedenza. La discovery non viene quindi eseguita ogni volta.

Per una nuova scansione è disponibile l'Options Flow dell'integrazione.

Nota: alcuni dispositivi/eventi OpenWebNet possono essere rilevabili soltanto tramite attività sul bus. Per questi casi è possibile aumentare i secondi di ascolto passivo durante la discovery e, per il citofono, effettuare una chiamata durante la scansione.

## Stato e affidabilità

La versione 0.1.2 evita di dichiarare un dispositivo acceso semplicemente perché Home Assistant ha inviato il comando.

Per esempio:

```text
HA → ON
     │
     ▼
   MH201
     │
     ▼
evento OpenWebNet
     │
     ▼
stato HA = ON
```

Questo evita stati falsi dopo un comando fallito o quando il dispositivo non risponde.

La sessione eventi viene inoltre mantenuta attiva con riconnessione automatica e le entità diventano non disponibili quando il gateway perde la connessione.

## Installazione

Attraverso HACS:

1. HACS → Integrazioni → Repository personalizzate.
2. Aggiungi questa repository come integrazione.
3. Installa **BTicino MyHome MH201**.
4. Riavvia Home Assistant.
5. Impostazioni → Dispositivi e servizi → Aggiungi integrazione → **BTicino MyHome**.

In alternativa copia `custom_components/bticino_myhome` in `/config/custom_components/` e riavvia Home Assistant.

## Gateway

Il MH201 deve essere raggiungibile dalla stessa rete locale di Home Assistant. BTicino documenta la configurazione Ethernet del MH201 e l'uso dell'indirizzo IP nella rete locale.

La porta OpenWebNet normalmente utilizzata è `20000`.

La password è quella OpenWebNet configurata sul gateway. Se l'impianto usa una password diversa da quella di fabbrica, inserirla nel Config Flow.

## Citofono

OpenWebNet permette di ricevere gli eventi della videocitofonia, ma questa integrazione non trasporta audio/video.

Sono disponibili:

- binary sensor per l'inizio/fine chiamata;
- pulsante per il comando di apertura serratura;
- sensore diagnostico con l'ultimo frame `WHO=7` ricevuto.

## Scenari

Gli scenari sono trattati come comandi write-only. La versione corrente registra una serie di indirizzi candidati (`1..30`) e li espone come scene HA.

Questa parte è volutamente conservativa: la discovery degli scenari non deve essere confusa con una lettura certa della configurazione interna di Home+Project.

## Limiti importanti

- La discovery automatica dei dispositivi non è equivalente a una lettura completa della configurazione di Home+Project.
- Alcuni dispositivi o topologie BUS possono richiedere discovery passiva o configurazione manuale futura.
- Il comando serratura non fornisce, da solo, una conferma fisica che la porta sia stata effettivamente aperta.
- Il supporto all'allarme dipende dai messaggi realmente esposti dal gateway e dal BUS.
- I dispositivi di terze parti non vengono gestite da questa integrazione: usare l'integrazione proprietaria o della community del brand se presente in Home Assistant.

## Struttura

```text
custom_components/bticino_myhome/
├── __init__.py
├── entity.py
├── gateway.py
├── discovery.py
├── config_flow.py
├── const.py
├── light.py
├── cover.py
├── switch.py
├── alarm_control_panel.py
├── binary_sensor.py
├── button.py
├── sensor.py
├── scene.py
├── strings.json
└── manifest.json
```

## Dipendenze

- Home Assistant 2025.1 o successivo
- `OWNd==0.7.49` by [_@anotherjulien_](https://github.com/anotherjulien)
- gateway BTicino/Legrand compatibile OpenWebNet

OWNd è una libreria locale di comunicazione OpenWebNet; la [repository originale](https://github.com/anotherjulien/OWNd) la descrive come event listener e command forwarder per OpenWebNet e la indica come pensata anche per integrazioni Home Assistant.

## Monitor dei frame OpenWebNet

La repository include `tools/openwebnet_monitor.py`, un monitor in sola lettura pensato per analizzare i frame evento reali del proprio MH201. Il monitor apre una sessione OpenWebNet EVENT e **non invia comandi**.

Richiede Python e la dipendenza `OWNd` installata. Esempio:

```bash
python tools/openwebnet_monitor.py 192.168.1.50
```

La password viene richiesta in modo interattivo. Per salvare una cattura:

```bash
python tools/openwebnet_monitor.py 192.168.1.50 --output cattura-openwebnet.txt
```

Per una sessione limitata nel tempo:

```bash
python tools/openwebnet_monitor.py 192.168.1.50 --seconds 300 --output cattura-openwebnet.txt
```

### Catturare anche i frame TX dell'integrazione

L'integrazione registra i frame OpenWebNet in ingresso e in uscita a livello `DEBUG`. In Home Assistant puoi abilitare temporaneamente:

```yaml
logger:
  default: warning
  logs:
    custom_components.bticino_myhome.gateway: debug
```

Riavvia Home Assistant o ricarica il logger, esegui le operazioni che vuoi analizzare e poi copia dal log le righe `OpenWebNet RX:` e `OpenWebNet TX:`. **Non condividere password o credenziali**.

Per studiare l'allarme, è preferibile iniziare con il monitor in sola lettura e osservare inserimento, disinserimento, eventi di zona e ripristino. I comandi di test dell'allarme vanno eseguiti solo secondo le procedure previste dal proprio impianto.


_Sviluppato in VibeCoding con Claude/ChatGPT_

---

# BTicino MyHome — Home Assistant

Custom integration for connecting a **BTicino MH201** gateway to Home Assistant via **OpenWebNet directly over the LAN**.

The integration does not use BTicino/Legrand/Netatmo cloud APIs to control devices. Home Assistant opens a TCP connection to the OpenWebNet gateway, normally on port `20000`.

## What it supports

- BUS/SCS lights (`WHO=1`)
- shutters/blinds/automation (`WHO=2`)
- load management (`WHO=3`)
- 4200C alarm system (`WHO=5`, within the limits of what the gateway/OWNd exposes)
- video intercom as an event notification (`WHO=7`)
- door lock opening (`WHO=7`, write-only command)
- OpenWebNet scenario activation (`WHO=0`)
- diagnostic sensor with the latest raw intercom frame


## Cloud independence

This is one of the main goals of the integration.

The control path is:

```text
Home Assistant
      │
      │ TCP / OpenWebNet
      ▼
BTicino MH201
      │
      │ BUS/SCS
      ▼
BTicino Devices
```

It is not:

```text
Home Assistant → Internet → BTicino Cloud → System
```

As a result, if the BTicino/Netatmo/Legrand cloud is unavailable, **local control from Home Assistant can continue to work**. The requirements are:

1. Home Assistant is running;
2. Home Assistant can reach the MH201 over the LAN;
3. the MH201 is powered on and connected to the BUS/SCS;
4. the local network continues to operate.

If the LAN goes down or the MH201 becomes unreachable, no local software integration can control the BUS through that gateway.

Loss of Internet connectivity does, however, affect features that require Internet access, such as remote access to Home Assistant through Home Assistant Cloud, the manufacturer's cloud services, and integrations that do not provide a local control path.

## Discovery and persistence

Version 0.1.2 fixes an important issue present in legacy versions 0.1 and 0.1.1: discovery was performed, but the result was not subsequently passed to the Home Assistant platforms.

The flow is now:

```text
Config Flow
    ↓
local connection to MH201
    ↓
active discovery + passive listening
    ↓
devices found
    ↓
persistence in ConfigEntry
    ↓
HA platform setup
```

After a Home Assistant restart, devices previously discovered are reused. Discovery is therefore not performed every time.

A new scan can be triggered through the integration's Options Flow.

Note: some OpenWebNet devices/events may only be detectable through activity on the bus. In these cases, the passive listening duration can be increased during discovery and, for the intercom, a call can be placed while the scan is running.

## State and reliability

Version 0.1.2 avoids declaring a device as turned on simply because Home Assistant has sent the command.

For example:

```text
HA → ON
     │
     ▼
   MH201
     │
     ▼
OpenWebNet event
     │
     ▼
HA state = ON
```

This prevents false states after a failed command or when the device does not respond.

The event session is also kept active with automatic reconnection, and entities become unavailable when the gateway loses its connection.

## Installation

Through HACS:

1. HACS → Integrations → Custom repositories.
2. Add this repository as an integration.
3. Install **BTicino MyHome MH201**.
4. Restart Home Assistant.
5. Settings → Devices & services → Add Integration → **BTicino MyHome**.

Alternatively, copy `custom_components/bticino_myhome` into `/config/custom_components/` and restart Home Assistant.

## Gateway

The MH201 must be reachable from the same local network as Home Assistant. BTicino documents the MH201 Ethernet configuration and the use of its IP address on the local network.

The OpenWebNet port normally used is `20000`.

The password is the OpenWebNet password configured on the gateway. If the system uses a password different from the factory default, enter it in the Config Flow.

## Intercom

OpenWebNet allows video intercom events to be received, but this integration does not transport audio or video.

The following are available:

- binary sensor for call start/end;
- button for the door lock opening command;
- diagnostic sensor containing the latest received `WHO=7` frame.

## Scenarios

Scenarios are treated as write-only commands. The current version registers a set of candidate addresses (`1..30`) and exposes them as HA scenes.

This part is deliberately conservative: scenario discovery should not be confused with a definitive reading of the internal Home+Project configuration.

## Important limitations

- Automatic device discovery is not equivalent to a complete reading of the Home+Project configuration.
- Some devices or BUS topologies may require passive discovery or future manual configuration.
- The door lock command does not, by itself, provide physical confirmation that the door was actually opened.
- Alarm support depends on the messages actually exposed by the gateway and the BUS.
- Third-party devices are not managed by this integration: use the manufacturer's integration or the relevant community integration if available in Home Assistant.

## Structure

```text
custom_components/bticino_myhome/
├── __init__.py
├── entity.py
├── gateway.py
├── discovery.py
├── config_flow.py
├── const.py
├── light.py
├── cover.py
├── switch.py
├── alarm_control_panel.py
├── binary_sensor.py
├── button.py
├── sensor.py
├── scene.py
├── strings.json
└── manifest.json
```

## Dependencies

- Home Assistant 2025.1 or later
- `OWNd==0.7.49` by [_@anotherjulien_](https://github.com/anotherjulien)
- BTicino/Legrand gateway compatible with OpenWebNet

OWNd is a local OpenWebNet communication library; the [original repository](https://github.com/anotherjulien/OWNd) describes it as an event listener and command forwarder for OpenWebNet and states that it is also intended for Home Assistant integrations.

## OpenWebNet Frame Monitor

The repository includes `tools/openwebnet_monitor.py`, a read-only monitor designed to analyze the actual event frames generated by your MH201. The monitor opens an OpenWebNet EVENT session and **does not send commands**.

It requires Python and the `OWNd` dependency to be installed. Example:

```bash
python tools/openwebnet_monitor.py 192.168.1.50
```

The password is requested interactively. To save a capture:

```bash
python tools/openwebnet_monitor.py 192.168.1.50 --output openwebnet-capture.txt
```

For a time-limited session:

```bash
python tools/openwebnet_monitor.py 192.168.1.50 --seconds 300 --output openwebnet-capture.txt
```

### Capturing TX frames from the integration as well

The integration logs incoming and outgoing OpenWebNet frames at the `DEBUG` level. In Home Assistant, you can temporarily enable:

```yaml
logger:
  default: warning
  logs:
    custom_components.bticino_myhome.gateway: debug
```

Restart Home Assistant or reload the logger, perform the operations you want to analyze, and then copy the `OpenWebNet RX:` and `OpenWebNet TX:` lines from the log. **Do not share passwords or credentials**.

When investigating the alarm system, it is preferable to start with the read-only monitor and observe arming, disarming, zone events, and restoration events. Alarm test commands should only be performed according to the procedures applicable to your own installation.


_Developed using VibeCoding with Claude/ChatGPT_

