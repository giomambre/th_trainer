# Portale di allenamento al poker — Product design document

- **Versione:** bozza 0.2
- **Stato:** proposta da discutere con i due fondatori
- **Data:** 30 settembre 2026

## 1. Scopo e posizionamento

Il prodotto è un portale gratuito per chi conosce già le regole del Texas Hold’em No Limit e vuole migliorare giocando sessioni cash game contro bot. Deve offrire il ritmo e la continuità di una partita reale, con strumenti di analisi che aiutino a interpretare le decisioni senza appesantire il tavolo.

Si usano solo fiches e importi virtuali, privi di valore monetario. Non sono previsti depositi, prelievi, premi in denaro o partite con soldi reali. Il prodotto non è un corso introduttivo alle regole.

L’obiettivo formativo è distinguere la qualità di una decisione dal risultato della singola mano: una scelta ragionevole può perdere, e una scelta debole può vincere.

## 2. Percorso del giocatore

### Configurazione della sessione

Il giocatore sceglie il numero di posti, da 2 a 6 nella visione completa, il livello generale di difficoltà e lo stile della partita. Può poi modificare livello e stile di ogni bot. Il tavolo mostra le caratteristiche impostate in modo riconoscibile, senza suggerire che lo stile determini ogni singola azione.

La prima esperienza usa una sola configurazione di bui e stack virtuali. Importi, ricarica dello stack e numero di posti effettivamente disponibili nella prima versione restano decisioni aperte.

Prima di iniziare, il giocatore seleziona una modalità:

- **Non assistita:** nessun suggerimento strategico durante la mano; analisi disponibile a mano conclusa.
- **Assistita:** durante la mano sono disponibili spiegazioni contestuali su regole, dimensioni delle puntate e comportamenti osservati. Le ipotesi strategiche sono dichiarate come tali.

La modalità scelta deve restare visibile e modificabile tra una mano e la successiva. Il comportamento del sistema in caso di modifica durante una mano va definito prima dell’implementazione.

### Mano in corso

Il tavolo deve rendere leggibili carte personali e comuni, posizione, stack, piatto, bui, puntata da chiamare, giocatore di turno e azioni disponibili. Per le puntate variabili deve mostrare l’intervallo consentito dalle regole e l’importo che verrà impegnato prima della conferma.

Il motore di gioco gestisce distribuzione, ordine di azione, round di puntata, fold, check, call, bet, raise, all-in, showdown, piatti secondari e divisione dei piatti. Deve impedire azioni illegali e conservare una sequenza ordinata degli eventi della mano. Il supporto a tavoli con più di due posti richiede in particolare la corretta gestione di turni, all-in e side pot.

I bot prendono decisioni usando solo informazioni che un avversario al tavolo potrebbe conoscere: carte proprie, carte comuni, azioni pubbliche, stack e storico osservabile. Non accedono alle carte coperte del giocatore né a dati futuri. Possono adattarsi a tendenze rilevate nel tempo; la finestra di osservazione e l’effetto concreto di livello e stile restano da definire e testare.

Le modifiche alla configurazione dei bot durante la sessione devono avere un momento di applicazione esplicito nell’interfaccia. **Proposta tecnica:** applicarle dalla mano successiva, così una mano già avviata mantiene condizioni coerenti.

### Fine mano e revisione

Al termine si mostrano esito, vincitori, variazioni degli stack e cronologia delle azioni. L’analisi evidenzia poche decisioni rilevanti e spiega quali informazioni erano disponibili al momento della scelta. Può indicare alternative plausibili, ma non deduce la qualità della scelta dalle carte rivelate dopo. (usare anche GTO ma scelte giuste si intende anche giusta in base alle giocate del player precendente sapecndo che non tutti giocano GTO)

È previsto un solo livello di approfondimento, comprensibile senza strumenti avanzati di studio del poker. Una valutazione strategica deve dichiarare almeno le ipotesi da cui dipende; se il sistema non dispone di una base sufficiente, deve evitare un giudizio netto.

## 3. Assistenza e analisi

Le spiegazioni distinguono quattro categorie:

1. **Regola:** conseguenza certa delle regole del gioco.
2. **Calcolo:** dato verificabile, per esempio importo da chiamare o dimensione del piatto.
3. **Osservazione:** frequenza o sequenza di azioni effettivamente registrate.
4. **Interpretazione:** possibile lettura dello stile avversario o della scelta strategica, con incertezza esplicita.

Durante la mano, assistenza e bot devono rispettare la stessa separazione tra informazioni pubbliche e nascoste. L’assistenza non rivela carte ignote al giocatore né usa lo showdown futuro per suggerimenti retrospettivi presentati come disponibili in tempo reale.

Per giudicare le decisioni non basta il risultato in fiches. Prima di introdurre voti, punteggi o etichette come “errore”, occorre definire un criterio riproducibile e spiegabile. Nella prima versione sono preferibili osservazioni motivate e alternative contestuali a un punteggio numerico privo di metodo validato.

## 4. Cronologia e progressi

Il portale conserva sessioni e mani, così il giocatore può ritrovarle dopo aver chiuso e riaperto l’applicazione. Per ogni mano servono almeno configurazione del tavolo, giocatori e stack iniziali, eventi in ordine, carte mostrate allo showdown, esito e dati necessari a ricostruire il riepilogo. La scelta di cosa conservare delle carte non mostrate va definita insieme al modello di accesso ai dati.

La schermata dei progressi mostra inizialmente pochi indicatori: mani e sessioni giocate, andamento delle fiches virtuali e situazioni contrassegnate per revisione. I risultati economici restano separati dalle valutazioni delle decisioni. I dettagli possono includere andamento nel tempo, ricorrenze e risultati contro livelli o stili di bot, purché sia chiaro quando il campione è troppo piccolo per trarre conclusioni.

## 5. Interfaccia e accessibilità

L’atmosfera di riferimento è quella di un moderno strumento di studio del poker, come GTO Wizard, con un’interfaccia più immediata. Il progetto deve avere identità visiva propria. Tavolo e controlli di gioco hanno priorità; analisi e statistiche compaiono su richiesta o nei momenti di revisione.

La lingua dell’interfaccia è l’italiano (ma i nomi dei posti , flop river check tutto in inglese). Stato del turno, azioni, importi e caratteristiche dei bot devono essere distinguibili anche senza basarsi solo sul colore. Testi e controlli devono restare leggibili su un laptop comune. Le animazioni non devono ritardare le decisioni o impedire di consultare le informazioni essenziali.

## 6. Ambito della prima versione

La prima versione giocabile comprende: avvio di una sessione cash game, almeno un tavolo heads-up, bot configurabili, entrambe le modalità di assistenza, mani complete secondo le regole, riepilogo e cronologia persistente. L’architettura del motore di gioco deve consentire l’estensione fino a sei posti senza cambiare il modello delle regole.

Esercizi su situazioni specifiche, percorsi guidati e analisi strategiche avanzate sono possibili sviluppi successivi. Tornei, altre varianti, multiplayer tra persone e gioco con denaro reale sono fuori dall’ambito attuale. La pubblicazione online verrà valutata dopo la validazione dell’esperienza locale.

## 7. Criteri di validazione

La prima esperienza è pronta per una prova con utenti quando un giocatore può configurare il tavolo, completare più mani senza interrompersi per errori di regole, distinguere le due modalità, consultare il riepilogo e ritrovare le mani dopo il riavvio.

Prima di ampliare le funzioni, vanno verificati almeno tre aspetti:

- **Correttezza:** ordine delle azioni, importi, all-in, showdown e assegnazione dei piatti producono esiti coerenti, inclusi i casi limite pertinenti al numero di posti supportato.
- **Comprensibilità:** un giocatore che conosce le regole capisce di chi è il turno, quanto costa continuare e perché un’azione è disponibile o esclusa.
- **Utilità formativa:** le spiegazioni aiutano a rivedere una decisione senza presentare ipotesi come certezze o confondere vincita e qualità della scelta.

## 8. Decisioni aperte

Prima di fissare schermate e criteri di analisi occorre decidere:

- bui, stack iniziale e regole di ricarica delle fiches virtuali;
- numero di posti della prima versione oltre al minimo heads-up;
- significato operativo dei livelli e degli stili dei bot, e come misurarne la differenza;
- durata della memoria dei bot e dati osservabili che alimentano l’adattamento;
- applicazione delle modifiche a bot e modalità quando una mano è in corso;
- contenuto preciso dell’assistenza durante la mano e del riepilogo finale;
- metodo per selezionare le decisioni da rivedere e, in futuro, valutarle;
- indicatori prioritari nella pagina dei progressi.

Le decisioni prese vanno riportate qui con il loro effetto sull’esperienza e sui criteri di validazione.

## 9. Iterazione tecnica del 1 ottobre 2026

Il primo motore implementa mani heads-up con bui 1/2 fiches e stack di 200
fiches, pari a 100 BB. Gli importi ammessi sono multipli di una fiche, quindi
0,5 BB. Le puntate possono assumere qualsiasi importo legale in questa unità;
non sono limitate a sizing predefiniti. Il raise indica il totale sulla street.

L'iterazione comprende turni, round di puntata, all-in, showdown, split pot,
restituzione delle fiches non chiamate, cronologia e ripristino locale della
mano. Ogni nuova mano riparte da 100 BB e alterna il dealer: la continuità
degli stack tra mani resta da implementare. I tavoli multiway e i side pot
non sono ancora disponibili.

L'avversario attuale è esclusivamente un bot di collaudo check/call.
Modellazione realistica di stile e abilità, adattamento e analisi GTO ed
exploitative restano requisiti centrali da implementare e validare. La
politica di collaudo non viene usata per giudicare decisioni del giocatore.
