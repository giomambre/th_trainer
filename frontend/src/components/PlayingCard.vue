<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ card?: string | null; empty?: boolean }>()
const suits: Record<string, { symbol: string; name: string }> = {
  c: { symbol: '♣', name: 'fiori' }, d: { symbol: '♦', name: 'quadri' },
  h: { symbol: '♥', name: 'cuori' }, s: { symbol: '♠', name: 'picche' },
}
const rank = computed(() => props.card?.[0] === 'T' ? '10' : props.card?.[0] ?? '')
const suit = computed(() => suits[props.card?.[1] ?? ''] ?? { symbol: '', name: '' })
const red = computed(() => ['h', 'd'].includes(props.card?.[1] ?? ''))
const label = computed(() => props.empty ? 'Carta comune non distribuita' : !props.card ? 'Carta coperta' : `${rank.value} di ${suit.value.name}`)
const layouts: Record<string, [number, number][]> = {
  '2': [[50, 25], [50, 75]],
  '3': [[50, 25], [50, 50], [50, 75]],
  '4': [[32, 25], [68, 25], [32, 75], [68, 75]],
  '5': [[32, 25], [68, 25], [50, 50], [32, 75], [68, 75]],
  '6': [[32, 25], [68, 25], [32, 50], [68, 50], [32, 75], [68, 75]],
  '7': [[32, 25], [68, 25], [50, 37], [32, 50], [68, 50], [32, 75], [68, 75]],
  '8': [[32, 25], [68, 25], [50, 37], [32, 50], [68, 50], [50, 63], [32, 75], [68, 75]],
  '9': [[32, 23], [68, 23], [32, 41], [68, 41], [50, 50], [32, 59], [68, 59], [32, 77], [68, 77]],
  '10': [[32, 23], [68, 23], [50, 32], [32, 41], [68, 41], [32, 59], [68, 59], [50, 68], [32, 77], [68, 77]],
}
const pips = computed(() => layouts[rank.value] ?? [])
</script>

<template>
  <div class="playing-card" :class="{ red, back: !card && !empty, vacant: empty }" role="img" :aria-label="label">
    <template v-if="card && !empty">
      <span class="corner upper" aria-hidden="true"><strong>{{ rank }}</strong><span>{{ suit.symbol }}</span></span>
      <span v-if="pips.length" class="pip-field" aria-hidden="true">
        <span v-for="([x, y], index) in pips" :key="index" class="pip" :class="{ inverted: y > 50 }" :style="{ left: x + '%', top: y + '%' }">{{ suit.symbol }}</span>
      </span>
      <span v-else class="face" aria-hidden="true"><strong v-if="rank !== 'A'">{{ rank }}</strong><span>{{ suit.symbol }}</span></span>
      <span class="corner lower" aria-hidden="true"><strong>{{ rank }}</strong><span>{{ suit.symbol }}</span></span>
    </template>
    <span v-else-if="!empty" class="back-mark" aria-hidden="true">TH</span>
  </div>
</template>

<style scoped>
.playing-card { position: relative; width: var(--card-width, 64px); aspect-ratio: 5 / 7; flex: 0 0 auto; border-radius: 6px; background: #fffdf7; color: #202724; border: 1px solid #d8d6cc; box-shadow: 0 2px 3px #0002; font-family: Georgia, 'Times New Roman', serif; user-select: none; }
.red { color: #b52b35; }
.corner { position: absolute; display: flex; flex-direction: column; align-items: center; line-height: 1; gap: 1px; font-size: calc(var(--card-width, 64px) * .23); }
.corner strong { font-weight: 700; letter-spacing: -.06em; }
.corner span { font-size: .9em; }
.upper { left: 5%; top: 5%; }
.lower { right: 5%; bottom: 5%; transform: rotate(180deg); }
.pip-field { position: absolute; inset: 0; }
.pip { position: absolute; transform: translate(-50%, -50%); font-size: calc(var(--card-width, 64px) * .27); line-height: 1; }
.pip.inverted { transform: translate(-50%, -50%) rotate(180deg); }
.face { position: absolute; inset: 22% 24%; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 2px; }
.face strong { font-size: calc(var(--card-width, 64px) * .4); line-height: 1; font-weight: 400; }
.face > span { font-size: calc(var(--card-width, 64px) * .48); line-height: 1; }
.back { background: repeating-linear-gradient(45deg, #2e4036, #2e4036 3px, #344b3c 3px, #344b3c 5px); border: 3px solid #edece4; color: #e5eddc; }
.back::before { content: ''; position: absolute; inset: 5px; border: 1px solid #9faf97; border-radius: 2px; }
.back-mark { position: absolute; inset: 0; display: grid; place-items: center; font-family: 'Geist', sans-serif; font-size: calc(var(--card-width, 64px) * .22); letter-spacing: -.06em; font-weight: 600; }
.vacant { background: transparent; border: 1px dashed var(--input-border); box-shadow: none; }
</style>
