# BTicino MyHome MH201 — Home Assistant

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

La versione 0.4.2 corregge un problema importante della 0.3: la discovery veniva eseguita ma il risultato non veniva poi passato alle piattaforme Home Assistant.

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

Al riavvio Home Assistant vengono usati i dispositivi già persistiti. La discovery non viene quindi eseguita ogni volta.

Per una nuova scansione è disponibile l'Options Flow dell'integrazione.

Nota: alcuni dispositivi/eventi OpenWebNet possono essere rilevabili soltanto tramite attività sul bus. Per questi casi è possibile aumentare i secondi di ascolto passivo durante la discovery e, per il citofono, effettuare una chiamata durante la scansione.

## Stato e affidabilità

La versione 0.4 evita di dichiarare un dispositivo acceso semplicemente perché Home Assistant ha inviato il comando.

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

Con HACS:

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

Per il video bisogna configurare separatamente il percorso IP supportato dal proprio posto esterno, per esempio ONVIF/RTSP se disponibile sul modello e firmware installati.

## Scenari

Gli scenari sono trattati come comandi write-only. La versione corrente registra una serie di indirizzi candidati (`1..30`) e li espone come scene HA.

Questa parte è volutamente conservativa: la discovery degli scenari non deve essere confusa con una lettura certa della configurazione interna di Home+Project.

## Limiti importanti

- La discovery automatica dei dispositivi non è equivalente a una lettura completa della configurazione di Home+Project.
- Alcuni dispositivi o topologie BUS possono richiedere discovery passiva o configurazione manuale futura.
- Il comando serratura non fornisce, da solo, una conferma fisica che la porta sia stata effettivamente aperta.
- Il supporto all'allarme dipende dai messaggi realmente esposti dal gateway e dal BUS.
- Le lampadine Philips Hue non vengono gestite da questa integrazione: usare l'integrazione Hue di Home Assistant.

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
- `OWNd==0.7.49`
- gateway BTicino/Legrand compatibile OpenWebNet, nel caso specifico MH201

OWNd è una libreria locale di comunicazione OpenWebNet; la repository originale la descrive come event listener e command forwarder per OpenWebNet e la indica come pensata anche per integrazioni Home Assistant.

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
