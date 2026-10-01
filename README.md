# TH Trainer

Base locale del portale di allenamento Texas Hold’em. Include configurazioni
salvate e mani heads-up complete con un bot di collaudo. Motore delle regole,
politica dei bot e futura analisi tramite solver sono componenti separati.

## Iterazione giocabile

Selezionare 2 posti e premere **Inizia mano heads-up**. Sono disponibili fold,
check, call, bet, raise e all-in, con passaggio tra preflop, flop, turn e river,
showdown, split pot e restituzione delle fiches non chiamate. Il raise indica
il totale sulla street; l'interfaccia mostra quanto verrà aggiunto.

- Bui 1/2 fiches, ossia 0,5/1 BB; stack iniziale 200 fiches (100 BB).
- Ogni nuova mano riparte da 100 BB e alterna il dealer. Non è ancora una
  sessione cash con stack trasferiti da una mano alla successiva.
- Il bot fa solo check/call per collaudare il motore. Non rappresenta uno
  stile realistico, un livello di abilità o una strategia GTO.
- Le preferenze di assistenza sono salvate, ma assistenza e analisi non sono
  ancora implementate. Le configurazioni da 3 a 6 posti non avviano mani.
- Carte proprie, board e retro delle carte sono disegnati in HTML/CSS, senza
  download esterni. Le carte del bot si rivelano solo allo showdown.
- A destra del tavolo compaiono la combinazione attuale, le migliori cinque
  carte disponibili e l'ultima mossa del bot con la street. Preflop sono
  descritte le carte iniziali. Non è una valutazione strategica della mano.
- Brevi animazioni evidenziano distribuzione, variazioni del piatto e azioni;
  si disattivano se il sistema richiede movimento ridotto.
- Le azioni si mostrano in sequenza: la tua mossa, il turno del bot, la sua
  risposta e poi le nuove carte. Il server fornisce snapshot intermedi della
  vista consentita, senza esporre il mazzo o carte coperte. Durante la sequenza
  i controlli sono bloccati; aggiornare la pagina ripristina lo stato finale.
- SQLite conserva lo stato completo e la cronologia. Il browser ricorda l'ID
  dell'ultima mano per ripristinarla dopo un aggiornamento o il riavvio del server.
  Non c'è ancora un archivio consultabile di tutte le mani.

Le azioni usano una revisione dello stato: richieste duplicate o provenienti
da una scheda rimasta indietro ricevono `409` e il tavolo viene aggiornato.

## Requisiti

- Python 3.11 o successivo
- Node.js compatibile con la versione di Vite nel lockfile, solo per compilare il frontend

## Avvio per sviluppo

Da PowerShell, nella cartella del progetto:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e "backend[dev]"
npm ci --prefix frontend
```

Avviare API e frontend in due terminali:

```powershell
.\.venv\Scripts\python -m uvicorn th_trainer.api:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend
```

```powershell
npm run dev --prefix frontend
```

Aprire l’indirizzo locale mostrato da Vite. Il proxy di sviluppo inoltra
`/api` a FastAPI. La documentazione dell’API è su
`http://127.0.0.1:8000/docs`.

L'opzione `--reload` ricarica il backend quando cambiano i file Python. Senza
questa opzione, riavviare il server dopo le modifiche: un frontend nuovo con
il vecchio backend può restituire `Method Not Allowed` all'avvio della mano.

## Uso locale con un solo server

```powershell
npm run build --prefix frontend
.\.venv\Scripts\python -m uvicorn th_trainer.api:app --host 127.0.0.1 --port 8000
```

Aprire `http://127.0.0.1:8000`. Dopo la build, Node.js non serve per
eseguire l’applicazione. Font, codice e dati non richiedono servizi esterni.

Il database SQLite viene creato in
`%LOCALAPPDATA%\TH_trainer\trainer.sqlite3` su Windows. Si può scegliere
un’altra directory locale impostando `TH_TRAINER_DATA_DIR` prima dell’avvio.
Il database è escluso da Git.

## Verifiche

```powershell
.\.venv\Scripts\python -m pytest backend/tests -q
npm run build --prefix frontend
```

## Struttura

- `backend/th_trainer/api.py`: API HTTP e distribuzione del frontend compilato.
- `backend/th_trainer/storage.py`: persistenza delle configurazioni in SQLite.
- `backend/th_trainer/game.py`: motore heads-up ed evaluator delle migliori 5 carte su 7.
- `backend/th_trainer/bots.py`: politica di collaudo check/call, da sostituire.
- `frontend/src/`: interfaccia Vue.
- `PRODUCT_DESIGN.md`: requisiti e decisioni di prodotto.

Il motore possiede lo stato completo della mano; il frontend riceve solo la
vista consentita al giocatore. Il mazzo futuro e le carte bruciate non sono
esposti dall'API. L’analisi GTO richiede un’integrazione verificata con un
solver locale: il risultato della mano non è una valutazione della decisione.
