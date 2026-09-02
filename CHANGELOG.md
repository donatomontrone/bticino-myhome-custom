# Changelog

## 0.1.7 - Rafforzamento del livello di protocollo e dell'architettura

* Aggiunto un livello di protocollo OpenWebNet dedicato in `custom_components/bticino_myhome/protocol/`.
* Aggiunti il modello di frame analizzato (*parsed*) e immutabile, il parser, i builder di comandi e gli eventi semantici normalizzati.
* Il Gateway ora espone gli eventi OpenWebNet analizzati e normalizzati separatamente dallo stream di debug grezzo (*raw*).
* La Discovery utilizza gli eventi di protocollo normalizzati anziché analizzare direttamente i frame OpenWebNet.
* Le entità di Home Assistant utilizzano gli eventi normalizzati e i builder di comandi di protocollo anziché costruire esse stesse i frame OpenWebNet grezzi.
* Centralizzato il frame di verifica dello stato (*status-probe*) utilizzato dalla discovery attiva.
* Mantenuto un approccio conservativo per la discovery attiva: un probe da solo non crea mai un dispositivo, è sempre necessario un evento corrispondente.
* Il setup iniziale dell'integrazione non esegue più una scansione completa implicita quando l'inventario persistente è vuoto.
* Aggiunti test unitari per il livello di protocollo.
* Nessuna funzionalità aggiunta per WHO=22/media/diffusione sonora.

## 0.1.6

* Introdotto un motore di Discovery unificato con sorgenti passive, attive e manuali.
* Normalizzati i metadati di discovery includendo sorgente e funzionalità (capabilities).
* Le scansioni attive vengono accettate solo quando gli eventi di bus corrispondenti confermano la presenza del dispositivo.
* Aggiunta la registrazione manuale dei dispositivi per i terminali che non possono essere rilevati automaticamente.
* I risultati della discovery vengono uniti (merged) all'interno del Device Manager anziché sovrascrivere i dispositivi esistenti.
* Aggiunti i test unitari per il motore di discovery.

## 0.1.5

* Aggiunto il passive learning sicuro: ascolta i reali eventi OpenWebNet senza inviare comandi di discovery.
* Aggiunta la normalizzazione da evento a dispositivo per i valori WHO supportati.
* Aggiunta la registrazione dinamica delle entità quando un dispositivo appreso viene accettato.
* Aggiunte le opzioni nel Config Flow per eseguire una scansione attiva o il passive learning.
* Aggiunta la selezione multi-dispositivo dopo il passive learning.

## 0.1.4

* Aggiunto un `BticinoDeviceManager` di runtime dedicato per l'inventario dei dispositivi rilevati.
* Mantenuto il trasporto del gateway separato dalle logiche relative a dispositivi ed entità di Home Assistant.
* Aggiunta la diagnostica di Home Assistant con oscuramento delle credenziali e dei dati identificativi di rete e dispositivo.
* Corretto il cleanup duplicato di `async_will_remove_from_hass()` nell'entità di base.
* Esteso `.gitignore` per escludere gli artefatti di pytest, coverage e build.
* Rimossa dalla repository la cartella generata `.pytest_cache`.
* Rielaborato il README focalizzandosi su funzionamento local-first, installazione, diagnostica, risoluzione problemi e roadmap.
* Escluse esplicitamente dal campo di applicazione del progetto le funzionalità legate alla diffusione sonora/musica.
* Mantenuto `OWNd==0.7.49` come dipendenza fissa (pinned) per OpenWebNet.

## 0.1.3

* Corretta la dipendenza OWNd per puntare alla release pubblicata `OWNd==0.7.49`.
* Corretta la gestione del rilevamento gateway in OWNd (risultati di tipo `dict`).
* Migliorato il ciclo di vita della sessione eventi asincrona e la gestione della riconnessione.
* Aggiunto il monitor di frame OpenWebNet in sola lettura.
* Aggiunto il logging DEBUG dei frame RX/TX.
* Passato lo stato di runtime di ConfigEntry a `entry.runtime_data`.

## 0.1.2

* Fissata la dipendenza reale pubblicata `OWNd==0.7.49`.
* Allineato `gateway.py` con le API di OWNd 0.7.49.
* Confermato che tutti gli I/O TCP di OpenWebNet vengono eseguiti tramite stream asyncio di OWNd.
* Corretta la gestione dei risultati di rilevamento SSDP di OWNd (`find_gateways()` restituisce dizionari).
* Utilizzato `ConfigEntry.runtime_data` per lo stato di runtime del gateway/dispositivo.
* Vincolato il worker eventi persistente al ciclo di vita della config-entry di Home Assistant.
* Migliorati il reconnect/backoff della sessione eventi e la pulizia della sessione comandi.
* Rimossi dalla distribuzione gli artefatti generati `__pycache__`.
* Registrato il logger `OWNd` nel manifest.

## 0.1.1

* Aggiunto un monitor eventi OpenWebNet in sola lettura in `tools/openwebnet_monitor.py`.
* Aggiunto il logging DEBUG per i frame grezzi OpenWebNet RX/TX nel gateway.
* Documentato come catturare i frame reali per l'analisi del protocollo e dell'allarme.

## 0.1

* Corretto il problema per cui la discovery veniva eseguita ma il risultato non veniva salvato in `hass.data`, impedendo alle piattaforme di creare le entità.
* La discovery iniziale viene ora eseguita durante il setup se l'entry non contiene dispositivi persistiti.
* I dispositivi scoperti vengono persistiti nel ConfigEntry e non devono essere riscoperti a ogni riavvio.
* Aggiunta gestione esplicita del lifecycle delle connessioni OWNd.
* Aggiunta riconnessione automatica della sessione eventi.
* Aggiunta rimozione corretta dei listener quando un'entità viene scaricata.
* Gli stati delle entità non vengono più aggiornati in modo ottimistico subito dopo l'invio del comando: lo stato viene confermato dagli eventi OpenWebNet.
* L'allarme parte da stato sconosciuto invece di dichiararsi erroneamente disarmato dopo un riavvio.
* Config Flow con unique ID del gateway e persistenza della discovery.
* Rimossi campi Options non implementati realmente.
* Aggiornata l'integrazione per usare l'API effettiva di OWNd (`OWNGateway`, `OWNCommandSession`, `OWNEventSession`).
* Aggiunto un livello entity comune per disponibilità e lifecycle dei listener.
* Aggiornata la documentazione sull'indipendenza dal cloud.

---

## 0.1.7 - Protocol layer and architecture hardening

- Added a dedicated OpenWebNet protocol layer under `custom_components/bticino_myhome/protocol/`.
- Added immutable parsed frame model, parser, command builders and normalized semantic events.
- Gateway now exposes parsed/normalized OpenWebNet events separately from the raw debug stream.
- Discovery consumes normalized protocol events instead of parsing OpenWebNet frames itself.
- Home Assistant entities consume normalized events and protocol command builders instead of constructing raw OpenWebNet frames themselves.
- Centralized the status-probe frame used by active discovery.
- Kept active discovery conservative: a probe alone never creates a device; a matching event is required.
- Initial integration setup no longer performs an implicit full scan when the persistent inventory is empty.
- Added protocol unit tests.
- No WHO=22/media/sound-diffusion functionality added.

## 0.1.6

* Introduced a unified Discovery Engine with passive, active and manual sources.
* Normalized discovery metadata with source and capabilities.
* Active probes are accepted only when matching bus events confirm a device.
* Added manual device registration for endpoints that cannot be discovered automatically.
* Discovery results are merged into the Device Manager instead of replacing existing devices.
* Added discovery engine unit tests.

## 0.1.5 

* Added safe passive learning: listens to real OpenWebNet events without transmitting discovery commands.
* Added event-to-device normalization for supported WHO values.
* Added dynamic entity registration when a learned device is accepted.
* Added Config Flow options to run an active scan or passive learning.
* Added multi-device selection after passive learning.

## 0.1.4

* Added a dedicated runtime `BticinoDeviceManager` for the discovered-device inventory.
* Kept gateway transport separate from Home Assistant device/entity concerns.
* Added Home Assistant diagnostics with redaction of credentials and identifying network/device data.
* Fixed duplicate `async_will_remove_from_hass()` cleanup in the base entity.
* Expanded `.gitignore` to exclude pytest/coverage/build artifacts.
* Removed generated `.pytest_cache` content from the repository.
* Reworked the README around local-first operation, installation, diagnostics, troubleshooting and roadmap.
* Explicitly excluded music/sound-diffusion functionality from the project scope.
* Kept `OWNd==0.7.49` as the pinned OpenWebNet dependency.

## 0.1.3

* Corrected the OWNd dependency to the published `OWNd==0.7.49` release.
* Corrected OWNd gateway discovery handling (`dict` results).
* Improved asynchronous event-session lifecycle and reconnect handling.
* Added the OpenWebNet read-only frame monitor.
* Added DEBUG RX/TX frame logging.
* Switched ConfigEntry runtime state to `entry.runtime_data`.

## 0.1.2

* Pin the real published `OWNd==0.7.49` dependency.
* Align `gateway.py` with OWNd 0.7.49 APIs.
* Confirm all OpenWebNet TCP I/O is performed through OWNd asyncio streams.
* Fix OWNd SSDP discovery result handling (`find_gateways()` returns dictionaries).
* Use `ConfigEntry.runtime_data` for runtime gateway/device state.
* Tie the persistent event worker to the Home Assistant config-entry lifecycle.
* Improve event-session reconnect/backoff and command-session cleanup.
* Remove generated `__pycache__` artifacts from the distribution.
* Register the `OWNd` logger in the manifest.

## 0.1.1

* Added a read-only OpenWebNet event monitor under `tools/openwebnet_monitor.py`.
* Added DEBUG logging for raw OpenWebNet RX/TX frames in the gateway.
* Documented how to capture real frames for protocol/alarm analysis.

## 0.1

* Fixed the issue where discovery was performed but the result was not saved in `hass.data`, preventing platforms from creating entities.
* Initial discovery is now performed during setup if the entry does not contain persisted devices.
* Discovered devices are persisted in the ConfigEntry and do not need to be rediscovered at every restart.
* Added explicit management of OWNd connection lifecycle.
* Added automatic reconnection for the event session.
* Added proper removal of listeners when an entity is unloaded.
* Entity states are no longer optimistically updated right after sending a command: the state is confirmed by OpenWebNet events.
* The alarm starts from an unknown state instead of incorrectly declaring itself disarmed after a restart.
* Config Flow with gateway unique ID and discovery persistence.
* Removed Options fields that were not actually implemented.
* Updated the integration to use the actual OWNd API (`OWNGateway`, `OWNCommandSession`, `OWNEventSession`).
* Added a common entity layer for availability and listener lifecycle.
* Updated documentation regarding cloud independence.