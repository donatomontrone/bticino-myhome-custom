# BTicino MyHome MH201

Integrazione custom per Home Assistant che comunica direttamente con il gateway **BTicino MH201** tramite **OpenWebNet sulla rete locale**.

Supporta luci, tapparelle/automazione, gestione carichi, allarme 4200C, segnalazione citofono, apertura serratura e richiamo scenari.

La comunicazione dell'integrazione è **locale**: non usa le API cloud BTicino, Netatmo o Legrand. Se Internet o il cloud del produttore non sono disponibili, Home Assistant può continuare a comandare l'impianto finché Home Assistant, la LAN e il MH201 restano raggiungibili.
