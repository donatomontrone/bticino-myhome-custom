# BTicino MyHome MH201

Integrazione Home Assistant locale per impianti **BTicino MyHome** tramite gateway **MH201** e protocollo **OpenWebNet**, senza cloud nel percorso di controllo.

Supporta scenari WHO=0, luci WHO=1 ON/OFF, tapparelle WHO=2, termoregolazione WHO=4, antifurto WHO=5 con target 4200C (partizioni e diagnostica comprese), apriporta WHO=6/HomeTouch e potenza attiva WHO=18.

WHO=22, dimmer WHO=1, WHO=3, audio, musica, media player e streaming audio/video sono fuori scope. Il ring HomeTouch verrà esposto solo dopo avere identificato un lifecycle call-start/call-end affidabile sul target reale.

Guida completa: `USAGE.md`.

---

Local Home Assistant integration for **BTicino MyHome** through the **MH201** gateway and **OpenWebNet**, with no cloud in the control path.

Supports WHO=0 scenarios, WHO=1 ON/OFF lighting, WHO=2 shutters, WHO=4 thermoregulation, WHO=5 4200C burglar alarm including partitions/diagnostics, WHO=6 HomeTouch door release and WHO=18 active power.

WHO=22, WHO=1 dimming, WHO=3, audio/music/media-player and A/V streaming are out of scope. HomeTouch ring state will be added only after a reliable real call lifecycle is identified.

See `USAGE.md` for the complete guide.
