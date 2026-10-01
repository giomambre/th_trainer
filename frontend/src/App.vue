<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import GameTable from './components/GameTable.vue'

type AssistanceMode = 'assisted' | 'unassisted'

type Session = {
  id: string
  created_at: string
  seats: number
  assistance_mode: AssistanceMode
}

const seats = ref(2)
const assistanceMode = ref<AssistanceMode>('assisted')
const sessions = ref<Session[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const loadError = ref('')
const notice = ref('')
const theme = ref<'dark' | 'light'>('dark')
const botPositions: Record<number, string[]> = {
  2: ['top'],
  3: ['top-left', 'top-right'],
  4: ['top', 'left', 'right'],
  5: ['top-left', 'top-right', 'left', 'right'],
  6: ['top', 'top-left', 'top-right', 'left', 'right'],
}
const previewBots = computed(() => botPositions[seats.value] ?? [])

function applyTheme(value: 'dark' | 'light') {
  theme.value = value
  document.documentElement.dataset.theme = value
  try {
    localStorage.setItem('th-trainer-theme', value)
  } catch {
    // The theme remains usable when browser storage is unavailable.
  }
}

async function loadSessions() {
  loading.value = true
  loadError.value = ''
  try {
    const response = await fetch('/api/sessions')
    if (!response.ok) throw new Error('Impossibile leggere le sessioni locali.')
    sessions.value = (await response.json()) as Session[]
  } catch (cause) {
    loadError.value = cause instanceof Error ? cause.message : 'Errore imprevisto.'
  } finally {
    loading.value = false
  }
}

async function createSession() {
  if (saving.value) return
  saving.value = true
  error.value = ''
  notice.value = ''
  try {
    const response = await fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        seats: seats.value,
        assistance_mode: assistanceMode.value,
      }),
    })
    if (!response.ok) throw new Error('Impossibile salvare la sessione.')
    notice.value = 'Configurazione salvata in locale.'
    await loadSessions()
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : 'Errore imprevisto.'
  } finally {
    saving.value = false
  }
}

function formattedDate(value: string): string {
  return new Intl.DateTimeFormat('it-IT', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

onMounted(() => {
  try {
    applyTheme(localStorage.getItem('th-trainer-theme') === 'light' ? 'light' : 'dark')
  } catch {
    applyTheme('dark')
  }
  loadSessions()
})
</script>

<template>
  <a class="skip-link" href="#main">Vai al contenuto</a>
  <div class="shell">
    <header class="topbar">
      <div class="brand"><span class="brand-mark">TH</span><span>Trainer</span></div>
      <div class="header-tools">
        <span class="local-badge">Solo sul tuo computer</span>
        <button class="theme-button" type="button" @click="applyTheme(theme === 'dark' ? 'light' : 'dark')">
          {{ theme === 'dark' ? 'Tema chiaro' : 'Tema scuro' }}
        </button>
      </div>
    </header>

    <main id="main">
      <section class="intro">
        <p class="eyebrow">Texas Hold’em / No Limit</p>
        <h1>Prepara il tavolo.</h1>
        <p>
          Gioca una mano heads-up o salva una configurazione per il tuo tavolo.
        </p>
      </section>

      <GameTable :seats="seats" />

      <div class="columns">
        <section class="panel" aria-labelledby="new-session-title">
          <div class="panel-heading">
            <div>
              <h2 id="new-session-title">Configura il tavolo</h2>
            </div>
          </div>

          <form :aria-busy="saving" @submit.prevent="createSession">
            <label for="seats">Posti al tavolo</label>
            <select id="seats" v-model.number="seats">
              <option v-for="count in 5" :key="count" :value="count + 1">
                {{ count + 1 }} posti
              </option>
            </select>

            <fieldset>
              <legend>Modalità di assistenza</legend>
              <label class="radio-row">
                <input v-model="assistanceMode" type="radio" value="assisted" />
                <span><strong>Assistita</strong><small>Preferenza salvata; assistenza ancora da implementare</small></span>
              </label>
              <label class="radio-row">
                <input v-model="assistanceMode" type="radio" value="unassisted" />
                <span><strong>Non assistita</strong><small>Preferenza salvata; analisi ancora da implementare</small></span>
              </label>
            </fieldset>

            <button type="submit" :disabled="saving">
              {{ saving ? 'Salvataggio…' : 'Salva configurazione' }}
            </button>
          </form>
          <p v-if="notice" class="message success" role="status">{{ notice }}</p>
          <p v-if="error" class="message error" role="alert">{{ error }}</p>
        </section>

        <section class="panel" aria-labelledby="sessions-title">
          <figure class="table-preview" aria-labelledby="table-preview-caption">
            <div class="preview-table" aria-hidden="true">
              <div class="table-center"><strong>{{ seats }}</strong><span>posti</span></div>
              <div v-for="(position, index) in previewBots" :key="index" class="preview-seat" :class="'seat-' + position">
                Bot {{ index + 1 }}
              </div>
              <div class="preview-seat seat-player">Tu</div>
            </div>
            <figcaption id="table-preview-caption">Anteprima: tu e {{ seats - 1 }} bot.</figcaption>
          </figure>
          <div class="panel-heading">
            <div>
              <h2 id="sessions-title">Configurazioni salvate</h2>
            </div>
          </div>

          <div v-if="loading" class="skeleton-list" role="status" aria-label="Caricamento delle configurazioni">
            <div v-for="row in 3" :key="row" class="skeleton-row"><span></span><span></span></div>
          </div>
          <div v-else-if="loadError" class="empty">
            <p class="message error" role="alert">{{ loadError }}</p>
            <button class="retry-button" type="button" @click="loadSessions">Riprova</button>
          </div>
          <div v-else-if="sessions.length === 0" class="empty">
            <h3>Nessuna configurazione salvata.</h3>
            <p>Le configurazioni che salvi compariranno in questo elenco.</p>
          </div>
          <ul v-else class="session-list">
            <li v-for="session in sessions" :key="session.id">
              <div>
                <strong>{{ session.seats }} posti · {{ session.assistance_mode === 'assisted' ? 'Assistita' : 'Non assistita' }}</strong>
                <small>{{ formattedDate(session.created_at) }}</small>
              </div>
              <span>Configurata</span>
            </li>
          </ul>
          <p class="panel-note">Questo elenco contiene configurazioni, non mani giocate.</p>
        </section>
      </div>
      <footer class="app-footer"><span>TH Trainer</span><span>Solo fiches virtuali. Nessun denaro reale.</span></footer>
    </main>
  </div>
</template>
