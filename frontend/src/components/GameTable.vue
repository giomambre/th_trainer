<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import PlayingCard from './PlayingCard.vue'

defineProps<{ seats: number }>()
type Legal = { fold?: boolean; check?: boolean; call?: number; to_call?: number; raise_min?: number | null; raise_max?: number | null; short_all_in?: boolean; betting_action?: 'bet' | 'raise' }
type Hand = {
  id: string; revision: number; dealer: number; street: string; board: string[]; actor: number | null; pot: number;
  players: { name: string; stack: number; bet: number; cards: (string | null)[] }[];
  legal: Legal;
  history: { sequence: number; street: string; player: number | null; action: string; amount: number }[];
  result: { winners: number[]; reason: string; pot: number; categories: string[] | null; deltas: number[] } | null;
  hero_hand: { name: string; detail: string; cards: string[]; board_plays: boolean };
  playback?: { kind: string; hand: Hand }[];
}
const hand = ref<Hand | null>(null)
const busy = ref(false)
const error = ref('')
const restoring = ref(true)
const raiseBB = ref(2)
const phase = ref<'idle' | 'setup' | 'bot' | 'action' | 'deal' | 'award'>('idle')
const narration = ref('')
const actingPlayer = ref<number | null>(null)
let live = true
onBeforeUnmount(() => { live = false })
const pause = (ms: number) => new Promise<void>(resolve => window.setTimeout(resolve, ms))
const activePlayer = computed(() => phase.value === 'idle' ? hand.value?.actor : phase.value === 'bot' ? 1 : phase.value === 'action' ? actingPlayer.value : null)
const storageKey = 'th-trainer-hand'
const botActions = new Set(['check', 'call', 'bet', 'raise', 'fold'])
const lastBotAction = computed(() => hand.value?.history.filter(event => event.player === 1 && botActions.has(event.action)).at(-1))
const botActionText = computed(() => {
  const event = lastBotAction.value
  if (!event) return 'In attesa della prima azione'
  const name = event.action[0]!.toUpperCase() + event.action.slice(1)
  return event.amount ? `${name} ${bb(event.amount)} BB` : name
})
const cardText = (card: string) => (card[0] === 'T' ? '10' : card[0]) + ({ c: '♣', d: '♦', h: '♥', s: '♠' }[card[1]!] ?? '')
const cardName = (card: string) => (card[0] === 'T' ? '10' : card[0]) + ' di ' + ({ c: 'fiori', d: 'quadri', h: 'cuori', s: 'picche' }[card[1]!] ?? '')
const bb = (chips: number) => new Intl.NumberFormat('it-IT', { maximumFractionDigits: 1 }).format(chips / 2)
const raiseCost = computed(() => Math.max(0, raiseBB.value * 2 - (hand.value?.players[0]?.bet ?? 0)))
const validRaise = computed(() => {
  const legal = hand.value?.legal
  const total = raiseBB.value * 2
  return Number.isInteger(total) && legal?.raise_min != null && legal.raise_max != null && total >= legal.raise_min && total <= legal.raise_max
})
const status = computed(() => {
  const h = hand.value
  if (!h) return ''
  if (!h.result) return 'Il tuo turno'
  if (h.result.winners.length === 2) return 'Split pot'
  return h.result.winners[0] === 0 ? 'Hai vinto la mano' : 'Bot test vince la mano'
})

function receive(value: Hand) {
  phase.value = 'idle'
  narration.value = ''
  hand.value = value
  raiseBB.value = (value.legal.raise_min ?? 4) / 2
  try { localStorage.setItem(storageKey, value.id) } catch { /* No browser storage: server persistence still works. */ }
}

async function present(value: Hand) {
  try { localStorage.setItem(storageKey, value.id) } catch { /* Browser storage is optional. */ }
  for (const frame of value.playback ?? []) {
    if (!live) return
    const event = frame.hand.history.at(-1)
    if (event?.player === 1 && botActions.has(frame.kind)) {
      phase.value = 'bot'
      actingPlayer.value = 1
      narration.value = 'Turno di Bot test'
      await pause(900)
      if (!live) return
    }
    hand.value = frame.hand
    actingPlayer.value = event?.player ?? null
    if (frame.kind === 'setup') {
      phase.value = 'setup'
      narration.value = 'Distribuzione delle carte e assegnazione dei bui'
      await pause(650)
    } else if (frame.kind === 'deal') {
      phase.value = 'deal'
      narration.value = `Distribuzione del ${frame.hand.street}`
      await pause(800)
    } else if (frame.kind === 'award') {
      phase.value = 'award'
      narration.value = 'Showdown e assegnazione del piatto'
      if (frame.hand.result?.reason === 'fold') narration.value = 'Assegnazione del piatto dopo il fold'
      await pause(650)
    } else if (frame.kind === 'refund') {
      phase.value = 'action'
      narration.value = 'Restituzione delle fiches non chiamate'
      await pause(350)
    } else {
      phase.value = 'action'
      const who = event?.player === 1 ? 'Bot test' : 'Tu'
      const action = frame.kind[0]!.toUpperCase() + frame.kind.slice(1)
      narration.value = `${who}: ${action}${event?.amount ? ' ' + bb(event.amount) + ' BB' : ''}`
      await pause(event?.player === 1 ? 900 : 450)
    }
  }
  if (live) receive(value)
}

async function responseHand(response: Response): Promise<Hand> {
  const data = await response.json()
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Richiesta non valida.')
  return data as Hand
}

async function start() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    await present(await responseHand(await fetch('/api/hands', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dealer: hand.value ? 1 - hand.value.dealer : 0 }),
    })))
  } catch (cause) { error.value = cause instanceof Error ? cause.message : 'Impossibile avviare la mano.' }
  finally { busy.value = false }
}

async function act(action: string, total?: number) {
  if (!hand.value || busy.value) return
  busy.value = true
  error.value = ''
  try {
    const response = await fetch(`/api/hands/${hand.value.id}/actions`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, raise_to: total, revision: hand.value.revision }),
    })
    if (response.status === 409) {
      receive(await responseHand(await fetch(`/api/hands/${hand.value.id}`)))
      throw new Error('La mano è stata aggiornata. Controlla il tavolo e ripeti la scelta.')
    }
    await present(await responseHand(response))
  } catch (cause) { error.value = cause instanceof Error ? cause.message : 'Azione non inviata. Riprova.' }
  finally { busy.value = false }
}

async function restore() {
  restoring.value = true
  error.value = ''
  let id: string | null = null
  try { id = localStorage.getItem(storageKey) } catch { /* Browser storage is optional. */ }
  try {
    if (id) {
      const response = await fetch(`/api/hands/${encodeURIComponent(id)}`)
      if (response.status === 404) {
        try { localStorage.removeItem(storageKey) } catch { /* Browser storage is optional. */ }
      }
      else receive(await responseHand(response))
    }
  } catch { error.value = 'Impossibile ripristinare la mano locale. Riprova prima di avviarne una nuova.' }
  finally { restoring.value = false }
}
onMounted(restore)
</script>

<template>
  <section class="game-section" aria-labelledby="game-title" :aria-busy="busy || restoring">
    <header class="game-heading">
      <div><h2 id="game-title">Tavolo heads-up</h2><p>100 BB per giocatore · Bui 0,5 / 1 BB</p></div>
      <span class="test-label">Bot di collaudo: check / call</span>
    </header>
    <p v-if="restoring" class="game-note" role="status">Ripristino della mano…</p>
    <template v-else-if="hand">
      <div class="table-layout">
      <div class="felt" :class="{ 'bot-turn': phase === 'bot' }">
        <div class="table-announcement" role="status" aria-live="polite"><span>{{ phase === 'idle' ? status : narration }}</span><span v-if="phase === 'bot'" class="turn-progress" aria-hidden="true"></span></div>
        <div class="player opponent" :class="{ active: activePlayer === 1 }">
          <div class="player-meta"><strong>{{ hand.players[1]!.name }}</strong><span class="position">{{ hand.dealer === 1 ? 'BTN / SB' : 'BB' }}</span><span>{{ bb(hand.players[1]!.stack) }} BB</span></div>
          <div class="hole-cards"><span v-for="(card, i) in hand.players[1]!.cards" :key="hand.id + ':' + i + ':' + (card ?? 'back')" class="card-slot" :style="{ '--deal-delay': i * 70 + 'ms' }"><PlayingCard :card="card" /></span></div>
          <p v-if="phase === 'bot'" class="bot-action-badge waiting">Il bot deve agire</p>
          <p v-else-if="lastBotAction" :key="hand.id + ':' + lastBotAction.sequence" class="bot-action-badge">{{ botActionText }} <span>{{ lastBotAction.street }}</span></p>
          <p v-else class="bot-action-placeholder">In attesa del turno</p>
          <span class="bet-label">{{ hand.players[1]!.bet && !hand.result ? 'Puntata ' + bb(hand.players[1]!.bet) + ' BB' : '\u00a0' }}</span>
        </div>
        <div class="board-area">
          <p class="street">{{ hand.street }}</p>
          <div class="board" aria-label="Carte comuni"><span v-for="i in 5" :key="hand.id + ':' + i + ':' + (hand.board[i - 1] ?? 'empty')" class="card-slot" :class="{ 'empty-slot': !hand.board[i - 1] }" :style="{ '--deal-delay': hand.street === 'flop' ? (i - 1) * 70 + 'ms' : '0ms' }"><PlayingCard :card="hand.board[i - 1]" :empty="!hand.board[i - 1]" /></span></div>
          <p class="pot">{{ hand.result ? 'Piatto assegnato' : 'Pot' }} <strong :key="hand.id + ':' + hand.pot" class="pot-value">{{ bb(hand.pot) }} BB</strong></p>
        </div>
        <div class="player hero" :class="{ active: activePlayer === 0 }">
          <span class="bet-label">{{ hand.players[0]!.bet && !hand.result ? 'Puntata ' + bb(hand.players[0]!.bet) + ' BB' : '\u00a0' }}</span>
          <div class="hole-cards"><span v-for="(card, i) in hand.players[0]!.cards" :key="hand.id + ':' + i + ':' + card" class="card-slot" :style="{ '--deal-delay': 100 + i * 70 + 'ms' }"><PlayingCard :card="card" /></span></div>
          <div class="player-meta"><strong>Tu</strong><span class="position">{{ hand.dealer === 0 ? 'BTN / SB' : 'BB' }}</span><span>{{ bb(hand.players[0]!.stack) }} BB</span></div>
        </div>
      </div>
      <aside class="table-insights" aria-label="La tua mano e le azioni del bot">
        <section class="hand-readout" aria-live="polite" aria-atomic="true">
          <h3>La tua mano</h3>
          <strong :key="hand.hero_hand.name" class="hand-name">{{ hand.hero_hand.name }}</strong>
          <p>{{ hand.hero_hand.detail }}</p>
          <ul class="best-cards" :aria-label="hand.board.length ? 'Migliori cinque carte disponibili' : 'Le tue carte'">
            <li v-for="card in hand.hero_hand.cards" :key="card" :class="{ 'red-suit': ['h', 'd'].includes(card[1]!) }" :aria-label="cardName(card)">{{ cardText(card) }}</li>
          </ul>
          <p v-if="hand.hero_hand.board_plays" class="board-note">Il board gioca: la combinazione è già nelle carte comuni.</p>
          <small>{{ hand.board.length ? 'Migliori 5 carte tra le tue e il board attuale.' : 'Carte iniziali, prima del flop.' }}</small>
        </section>
        <section class="bot-readout" aria-live="polite" aria-atomic="true">
          <h3>{{ phase === 'bot' ? 'Turno del bot' : 'Ultima mossa del bot' }}</h3>
          <div :key="hand.id + ':' + (lastBotAction?.sequence ?? 0)" class="bot-action-detail">
            <strong>{{ phase === 'bot' ? 'Azione in arrivo…' : botActionText }}</strong>
            <span v-if="lastBotAction && phase !== 'bot'">{{ lastBotAction.street }}</span>
          </div>
          <p>Il bot di collaudo risponde con check o call.</p>
        </section>
      </aside>
      </div>
      <div class="decision" aria-live="polite">
        <strong>{{ busy ? narration || 'Invio della mossa…' : status }}</strong>
        <span v-if="busy">Le azioni si riattivano al tuo turno.</span>
        <span v-else-if="!hand.result">{{ hand.legal.to_call ? 'Da chiamare: ' + bb(hand.legal.call ?? 0) + ' BB' : 'Puoi fare check.' }}</span>
        <span v-else>{{ hand.result.reason === 'fold' ? 'Mano conclusa per fold.' : hand.result.categories?.join(' / ') }} Il tuo saldo: {{ (hand.result.deltas[0] ?? 0) > 0 ? '+' : '' }}{{ bb(hand.result.deltas[0] ?? 0) }} BB.</span>
      </div>
      <div v-if="!hand.result && !busy" class="actions">
        <div class="basic-actions">
          <button v-if="hand.legal.fold" class="secondary" :disabled="busy" @click="act('fold')">Fold</button>
          <button v-if="hand.legal.check" :disabled="busy" @click="act('check')">Check</button>
          <button v-if="hand.legal.call" :disabled="busy" @click="act('call')">Call {{ bb(hand.legal.call) }} BB</button>
        </div>
        <form v-if="hand.legal.raise_min != null" class="raise-controls" @submit.prevent="validRaise && act('raise', raiseBB * 2)">
          <label for="raise-total">{{ hand.legal.betting_action === 'raise' ? 'Raise' : 'Bet' }} a (BB)</label>
          <div class="raise-row">
            <input id="raise-total" v-model.number="raiseBB" type="number" step="0.5" :min="hand.legal.raise_min / 2" :max="(hand.legal.raise_max ?? 0) / 2" :disabled="busy" required aria-describedby="raise-help" />
            <button type="submit" :disabled="busy || !validRaise">{{ hand.legal.betting_action === 'raise' ? 'Raise' : 'Bet' }}</button>
            <button type="button" class="secondary" :disabled="busy" @click="act('raise', hand!.legal.raise_max!)">All-in</button>
          </div>
          <small id="raise-help">Totale sulla street: da {{ bb(hand.legal.raise_min) }} a {{ bb(hand.legal.raise_max ?? 0) }} BB. Impegni {{ bb(raiseCost) }} BB.{{ hand.legal.short_all_in ? ' Disponibile solo un all-in inferiore al raise minimo.' : '' }}</small>
        </form>
      </div>
      <div v-else-if="busy" class="actions-pending" role="status">{{ phase === 'bot' ? 'Il turno è del bot.' : 'Mano in corso…' }}</div>
      <button v-else class="start-button" :disabled="seats !== 2" @click="start">Nuova mano · 100 BB</button>
      <details class="hand-history"><summary>Cronologia della mano</summary>
        <ol><li v-for="event in hand.history" :key="event.sequence"><span>{{ event.street }}</span> {{ event.player == null ? 'Tavolo' : event.player === 0 ? 'Tu' : 'Bot test' }} · {{ event.action }}{{ event.amount ? ' ' + bb(event.amount) + ' BB' : '' }}</li></ol>
      </details>
    </template>
    <div v-else class="game-empty">
      <div class="sample-cards" aria-label="Esempio di carte, non una mano distribuita"><PlayingCard card="As" /><PlayingCard card="Kh" /><PlayingCard /></div>
      <p>Avvia una mano per vedere carte, turni e azioni disponibili.</p>
      <button class="start-button" :disabled="busy || seats !== 2 || !!error" @click="start">{{ busy ? 'Distribuzione…' : 'Inizia mano heads-up' }}</button>
    </div>
    <p v-if="error" class="message error" role="alert">{{ error }} <button v-if="!hand" type="button" class="retry-button" @click="restore">Riprova</button></p>
    <p class="game-note">{{ seats !== 2 ? 'Seleziona 2 posti per avviare una mano. ' : '' }}Ogni nuova mano riparte da 100 BB; il dealer alterna. Lo stato è salvato in locale. Assistenza e analisi non sono ancora disponibili.</p>
  </section>
</template>

<style scoped>
.game-section { border: 1px solid var(--border); border-radius: 1rem; background: var(--surface); padding: 1.5rem; margin-bottom: 2.5rem; }
.game-heading { display: flex; justify-content: space-between; align-items: start; gap: 1rem; margin-bottom: 1.25rem; }
.game-heading p, .test-label { color: var(--muted); font-size: .75rem; line-height: 1.5; margin: .4rem 0 0; }
.test-label { text-align: right; }
.table-layout { display: grid; grid-template-columns: minmax(0, 1fr) 230px; align-items: start; gap: 1.5rem; }
.table-insights { padding-top: .5rem; min-width: 0; }
.table-insights h3 { margin: 0 0 .8rem; color: var(--muted); font-size: .75rem; font-weight: 500; }
.table-insights p { margin: .6rem 0; color: var(--muted); font-size: .8rem; line-height: 1.6; }
.table-insights small { display: block; color: var(--muted); font-size: .7rem; line-height: 1.6; }
.hand-name { display: block; font-size: 1.3rem; font-weight: 600; letter-spacing: -.025em; animation: readout-in 250ms ease-out; }
.best-cards { display: flex; flex-wrap: wrap; gap: .4rem; list-style: none; margin: 1rem 0; padding: 0; }
.best-cards li { border: 1px solid var(--input-border); border-radius: .3rem; padding: .35rem .4rem; font-size: .8rem; font-weight: 500; background: var(--input-background); }
.best-cards .red-suit { color: var(--card-red, #f1a6a8); }
:global(:root[data-theme='light']) .best-cards .red-suit { --card-red: #a0222d; }
.board-note { color: var(--accent-text) !important; }
.bot-readout { margin-top: 1.5rem; padding-top: 1.25rem; border-top: 1px solid var(--border); }
.bot-action-detail { border-left: 3px solid var(--accent-text); padding: .5rem .75rem; animation: action-highlight 650ms ease-out; }
.bot-action-detail strong { display: block; font-size: 1.1rem; }
.bot-action-detail span { display: block; margin-top: .35rem; color: var(--muted); font-size: .7rem; text-transform: capitalize; }
.bot-action-badge { margin: 0; padding: .35rem .65rem; border: 1px solid var(--selected-border); border-radius: var(--radius); color: var(--accent-text); background: var(--selected-background); font-size: .85rem; font-weight: 600; animation: action-highlight 650ms ease-out; }
.bot-action-badge span { margin-left: .5rem; color: var(--muted); font-size: .65rem; font-weight: 400; text-transform: capitalize; }
.card-slot { display: block; animation: card-deal 360ms cubic-bezier(.2,.7,.2,1) both; animation-delay: var(--deal-delay, 0ms); }
.card-slot.empty-slot { animation: none; }
.pot-value { display: inline-block; animation: pot-update 300ms ease-out; }
@keyframes card-deal { from { opacity: 0; transform: translateY(-12px) rotate(-4deg) scale(.96); } to { opacity: 1; transform: translateY(0) rotate(0) scale(1); } }
@keyframes action-highlight { 0% { background-color: var(--selected-background); transform: translateY(-3px); } 100% { transform: translateY(0); } }
@keyframes pot-update { from { transform: translateY(3px); opacity: .45; } to { transform: translateY(0); opacity: 1; } }
@keyframes readout-in { from { opacity: .4; transform: translateY(3px); } to { opacity: 1; transform: translateY(0); } }
.felt { background: var(--table); border: 5px solid var(--border); outline: 1px solid var(--input-border); border-radius: 2.5rem; padding: 1rem; display: grid; justify-items: center; gap: 1rem; }
.table-announcement { position: relative; min-height: 2.3rem; width: min(100%, 380px); text-align: center; padding: .55rem .75rem; border-radius: .5rem; background: var(--surface); font-size: .8rem; font-weight: 500; overflow: hidden; }
.turn-progress { position: absolute; height: 3px; left: 0; bottom: 0; width: 100%; background: var(--accent); transform-origin: left; animation: turn-wait 900ms linear both; }
@keyframes turn-wait { from { transform: scaleX(0); } to { transform: scaleX(1); } }
.player { display: grid; grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: 'meta cards' 'action bet'; align-items: center; gap: .5rem .9rem; width: min(100%, 340px); padding: .85rem; background: var(--surface); border: 1px solid var(--input-border); border-radius: .8rem; transition: border-color 180ms ease, box-shadow 180ms ease; }
.player.active { border-color: var(--accent); box-shadow: 0 0 0 2px var(--selected-border); }
.player-meta { grid-area: meta; display: flex; flex-direction: column; align-items: flex-start; gap: .4rem; font-size: .8rem; font-variant-numeric: tabular-nums; }
.player-meta > span:last-child { font-size: 1rem; font-weight: 600; }
.player .hole-cards { grid-area: cards; }
.player .bet-label { grid-area: bet; text-align: right; }
.bot-action-badge, .bot-action-placeholder { grid-area: action; min-height: 2rem; }
.bot-action-placeholder { margin: 0; font-size: .7rem; color: var(--muted); display: flex; align-items: center; }
.bot-action-badge { padding: .35rem .45rem; font-size: .8rem; }
.bot-action-badge span { display: block; margin: .2rem 0 0; }
.bot-action-badge.waiting { color: var(--text); font-weight: 400; }
.hero { grid-template-areas: 'meta cards' 'bet bet'; }
.hero .bet-label { text-align: center; }
.position { border: 1px solid var(--input-border); padding: .2rem .4rem; border-radius: .3rem; font-size: .65rem; }
.active .player-meta strong::after { content: ' · turno'; font-weight: 400; color: var(--accent-text); }
.hole-cards, .board, .sample-cards { display: flex; justify-content: center; gap: .4rem; }
.opponent .hole-cards { --card-width: 50px; }
.hero .hole-cards { --card-width: 70px; }
.board-area { text-align: center; }
.street { margin: 0 0 .6rem; text-transform: capitalize; font-size: .75rem; color: var(--muted); }
.pot { margin: .75rem 0 .3rem; font-size: .8rem; color: var(--muted); }
.pot strong { color: var(--text); padding-left: .5rem; font-size: 1rem; font-variant-numeric: tabular-nums; }
.bet-label { font-size: .7rem; min-height: 1em; color: var(--muted); }
.decision { display: flex; justify-content: space-between; align-items: baseline; gap: .75rem; margin: 1.25rem 0; font-size: .9rem; }
.decision > span { font-size: .8rem; color: var(--muted); line-height: 1.5; }
.actions { display: grid; grid-template-columns: minmax(150px, .7fr) minmax(0, 1fr); gap: 1.5rem; align-items: start; }
.actions-pending { display: flex; align-items: center; justify-content: center; min-height: 105px; border: 1px solid var(--border); border-radius: var(--radius); color: var(--muted); font-size: .85rem; }
.basic-actions { display: flex; gap: .5rem; }
.secondary { background: transparent; border-color: var(--input-border); color: var(--text); }
.secondary:hover { background: var(--hover-background); }
.raise-controls > label { font-size: .75rem; margin-bottom: .4rem; }
.raise-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: .5rem; }
input { width: 100%; min-width: 0; font: inherit; font-size: .9rem; border: 1px solid var(--input-border); border-radius: var(--radius); padding: .7rem; background: var(--input-background); color: var(--text); }
.raise-controls small { display: block; margin-top: .5rem; font-size: .7rem; line-height: 1.6; color: var(--muted); }
.game-note { margin: 1rem 0 0; color: var(--muted); font-size: .72rem; line-height: 1.6; }
.game-empty { padding: 1rem 0; text-align: center; }
.game-empty p { font-size: .85rem; color: var(--muted); line-height: 1.6; }
.sample-cards { --card-width: 70px; margin: .5rem 0 1rem; }
.start-button { width: auto; display: block; margin: 1rem auto 0; }
.hand-history { border-top: 1px solid var(--border); margin-top: 1.25rem; padding-top: 1rem; font-size: .75rem; }
summary { cursor: pointer; padding: .25rem 0; }
summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; }
.hand-history ol { max-height: 12rem; overflow-y: auto; padding-left: 1.3rem; line-height: 1.9; }
.hand-history li > span { display: inline-block; width: 4rem; color: var(--muted); }
@media (max-width: 820px) {
  .table-layout { grid-template-columns: 1fr; gap: 1rem; }
  .table-insights { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  .bot-readout { margin: 0; padding: 0 0 0 1rem; border-top: 0; border-left: 1px solid var(--border); }
  .actions { grid-template-columns: 1fr; gap: 1rem; }
  .game-section { padding: 1rem; }
  .game-heading, .decision { flex-direction: column; gap: .4rem; }
  .test-label { text-align: left; margin: 0; }
}
@media (max-width: 480px) {
  .table-insights { grid-template-columns: 1fr; }
  .bot-readout { padding: 1rem 0 0; border-left: 0; border-top: 1px solid var(--border); }
  .board { --card-width: 42px; gap: 4px; }
  .hero .hole-cards { --card-width: 60px; }
  .felt { border-radius: 1.5rem; border-width: 3px; padding: .75rem .25rem; }
  .player { padding: .65rem; gap: .4rem .5rem; }
  .opponent .hole-cards { --card-width: 42px; }
  .player-meta { font-size: .75rem; }
  .raise-row { grid-template-columns: minmax(0, 1fr) 1fr 1fr; gap: .35rem; }
  .raise-row button { padding-inline: .5rem; }
}
</style>
