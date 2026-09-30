# Portale di allenamento al poker — Design document

**Versione:** bozza 0.1  
**Stato:** base di discussione, da rivedere con i due fondatori  
**Data:** 30 settembre 2026

## 1. Visione

Creare un portale gratuito in cui chi conosce già le regole del Texas Hold’em No Limit possa migliorare giocando partite cash game complete contro bot. L’esperienza deve assomigliare a una vera sessione di poker, ma aiutare il giocatore a capire le proprie decisioni e il comportamento degli avversari.

La porta d’ingresso è semplice: si sceglie il tavolo, si impostano i bot, si decide se ricevere assistenza e si inizia a giocare. Le spiegazioni e le statistiche devono essere utili senza trasformare il tavolo in una schermata tecnica difficile da leggere.

Il portale usa esclusivamente fiches e importi **virtuali**, privi di valore monetario. Non prevede depositi, prelievi, premi in denaro o gioco con soldi reali.

## 2. Destinatari e obiettivo

Il prodotto si rivolge a giocatori di livelli diversi che conoscono almeno le regole di base e vogliono migliorare con la pratica. Non nasce come corso introduttivo alle regole del poker.

L’obiettivo è permettere al giocatore di:

- prendere decisioni in una partita completa, dal preflop allo showdown;
- riconoscere stili e cambiamenti nel comportamento degli avversari;
- rivedere le mani e capire le decisioni importanti;
- osservare i propri progressi e gli errori ricorrenti nel tempo.

Il prodotto non deve confondere il risultato economico di una singola mano con la qualità della decisione presa.

## 3. Esperienza principale

### Prima della partita

Il giocatore avvia una sessione cash game e sceglie un tavolo da **2 a 6 posti** nella visione completa del prodotto. Può impostare un livello generale di difficoltà e uno stile generale della partita. Può inoltre personalizzare livello e stile dei singoli bot. Le caratteristiche del tavolo e di ciascun bot devono restare chiaramente riconoscibili durante il gioco.

Non sono previste molte fasce di puntata: l’esperienza iniziale presenta **una sola configurazione intuitiva di bui e stack virtuali**. Gli importi esatti saranno definiti in una revisione successiva.

Il giocatore sceglie una delle due modalità:

- **Partita non assistita:** prende le decisioni senza suggerimenti durante la mano e riceve un riepilogo al termine.
- **Partita assistita:** durante la mano può leggere spiegazioni sui comportamenti osservati nei bot e sul contesto delle decisioni. Il supporto deve distinguere osservazioni, ipotesi e fatti certi.

### Durante la partita

Il tavolo mostra subito le informazioni necessarie per decidere: carte personali, carte comuni, posizione, stack, piatto, bui, puntata corrente, azioni disponibili e turno di gioco. Le azioni non consentite dalle regole non devono apparire come scelte valide.

La partita segue le regole del Texas Hold’em No Limit, comprese le situazioni di all-in, i piatti secondari e la divisione del piatto quando necessaria. Il ritmo deve favorire il gioco: animazioni e spiegazioni non devono rallentare inutilmente ogni mano.

I bot hanno livelli di difficoltà e stili distinguibili. Adattano le proprie decisioni ai comportamenti osservati nel giocatore, senza conoscere le sue carte nascoste. Il giocatore può modificare le impostazioni generali e quelle di un singolo bot anche durante una sessione. Resta da definire se un cambiamento effettuato a mano iniziata avrà effetto subito o dalla mano successiva.

### Dopo la mano

Alla conclusione della mano il giocatore vede l’esito, può rivedere le azioni principali e riceve un’analisi comprensibile delle proprie decisioni. È previsto **un solo livello di approfondimento**: abbastanza informativo per imparare, ma leggibile senza richiedere conoscenze avanzate di software per il poker.

Le spiegazioni devono evitare giudizi fondati soltanto sulle carte emerse dopo la decisione. Dove il sistema propone una lettura dell’avversario o una linea strategica, deve rendere chiaro che si tratta di una valutazione basata sulle informazioni disponibili e su determinate ipotesi, non di una verità universale.

## 4. Progressi del giocatore

Il portale conserva la cronologia delle mani e mostra i progressi nel tempo. La visione comprende almeno:

- numero di mani e sessioni giocate;
- risultati in fiches virtuali, separati dalla valutazione delle decisioni;
- decisioni e situazioni da rivedere;
- andamento nel tempo;
- punti forti e difficoltà ricorrenti;
- risultati contro diversi livelli e stili di bot.

La schermata iniziale dei progressi deve evidenziare pochi dati utili; il resto può essere consultato nei dettagli. I criteri con cui si giudica una decisione dovranno essere spiegabili al giocatore.

## 5. Stile e accessibilità

Il riferimento di atmosfera è GTO Wizard: un ambiente contemporaneo dedicato allo studio del poker. Il portale deve però risultare **più immediato e meno tecnico**. Il tavolo e le azioni hanno priorità visiva; analisi e statistiche compaiono quando servono, senza occupare continuamente lo spazio di gioco.

Il linguaggio dell’interfaccia è italiano. Carte, puntate, turni e stati dei bot devono essere riconoscibili anche senza affidarsi soltanto al colore. Testi e controlli devono restare leggibili su un normale laptop.

Il design deve avere una propria identità; il riferimento a GTO Wizard serve a orientare lo stile, non a copiarne marchio o schermate.

## 6. Confini del prodotto

**Al centro della prima versione:** partite cash game complete contro bot, scelta tra modalità assistita e non assistita, configurazione dei bot, riepilogo delle mani e primi progressi personali.

**Possibili sviluppi successivi:** esercizi su situazioni specifiche, percorsi di allenamento, analisi strategiche più avanzate e pubblicazione online. Queste idee non devono complicare l’avvio della prima esperienza di gioco.

**Fuori dall’ambito attuale:** tornei, altre varianti del poker, partite con denaro reale e funzionalità social o multiplayer tra persone. Un’eventuale versione online verrà progettata quando il prodotto locale sarà convincente.

## 7. Principi per le spiegazioni strategiche

1. Separare regole certe, calcoli verificabili, osservazioni del comportamento dei bot e ipotesi strategiche.
2. Durante una mano, l’assistenza non deve conoscere né rivelare carte che il giocatore non può vedere.
3. Una decisione non va giudicata solo dal risultato finale della mano.
4. Evitare etichette come “mossa perfetta” o “errore certo” quando esistono più linee ragionevoli.
5. Privilegiare spiegazioni utili per la mano successiva rispetto a grandi quantità di numeri.

## 8. Prima esperienza da validare

La prima esperienza giocabile è riuscita se un utente può aprire il portale, configurare una partita, giocare mani complete contro bot, distinguere chiaramente le due modalità di assistenza, leggere il riepilogo di una mano e ritrovare la propria cronologia dopo aver chiuso e riaperto il portale.

La versione iniziale può partire da un tavolo a due posti, purché il percorso verso tavoli fino a sei posti resti parte esplicita del prodotto. Prima di ampliare le funzioni, bisogna verificare che la partita sia corretta, comprensibile e piacevole da giocare.

## 9. Decisioni ancora aperte

Questi punti non bloccano la visione di base, ma andranno definiti prima di rifinire le relative schermate o analisi:

- configurazione precisa dei bui, dello stack e dell’eventuale ricarica di fiches virtuali;
- numero di posti disponibile nella prima esperienza giocabile;
- significato concreto dei livelli e degli stili dei bot;
- durata della memoria con cui i bot si adattano al giocatore;
- momento in cui diventano effettive le modifiche ai bot durante una mano;
- contenuto esatto dell’assistenza durante la mano e del riepilogo finale;
- priorità dei dati da mostrare nella schermata dei progressi;
- ruolo futuro degli esercizi separati dalle partite complete.

Questo documento va aggiornato quando viene presa una decisione sul prodotto, mantenendo visibile ciò che è già deciso e ciò che resta aperto.
