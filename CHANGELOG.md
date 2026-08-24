# Changelog

## 0.1.2

- Pin the real published `OWNd==0.7.49` dependency.
- Align `gateway.py` with OWNd 0.7.49 APIs.
- Confirm all OpenWebNet TCP I/O is performed through OWNd asyncio streams.
- Fix OWNd SSDP discovery result handling (`find_gateways()` returns dictionaries).
- Use `ConfigEntry.runtime_data` for runtime gateway/device state.
- Tie the persistent event worker to the Home Assistant config-entry lifecycle.
- Improve event-session reconnect/backoff and command-session cleanup.
- Remove generated `__pycache__` artifacts from the distribution.
- Register the `OWNd` logger in the manifest.

## 0.1.1

- Added a read-only OpenWebNet event monitor under `tools/openwebnet_monitor.py`.
- Added DEBUG logging for raw OpenWebNet RX/TX frames in the gateway.
- Documented how to capture real frames for protocol/alarm analysis.


## 0.1

- Corretto il problema per cui la discovery veniva eseguita ma il risultato non veniva salvato in `hass.data`, impedendo alle piattaforme di creare le entità.
- La discovery iniziale viene ora eseguita durante il setup se l'entry non contiene dispositivi persistiti.
- I dispositivi scoperti vengono persistiti nel ConfigEntry e non devono essere riscoperti a ogni riavvio.
- Aggiunta gestione esplicita del lifecycle delle connessioni OWNd.
- Aggiunta riconnessione automatica della sessione eventi.
- Aggiunta rimozione corretta dei listener quando un'entità viene scaricata.
- Gli stati delle entità non vengono più aggiornati in modo ottimistico subito dopo l'invio del comando: lo stato viene confermato dagli eventi OpenWebNet.
- L'allarme parte da stato sconosciuto invece di dichiararsi erroneamente disarmato dopo un riavvio.
- Config Flow con unique ID del gateway e persistenza della discovery.
- Rimossi campi Options non implementati realmente.
- Aggiornata l'integrazione per usare l'API effettiva di OWNd (`OWNGateway`, `OWNCommandSession`, `OWNEventSession`).
- Aggiunto un livello entity comune per disponibilità e lifecycle dei listener.
- Aggiornata la documentazione sull'indipendenza dal cloud.