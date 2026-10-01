# Frontend design direction

Taste skill: .agents/skills/design-taste-frontend/SKILL.md.

This is an evolution of the local poker setup screen. It keeps the existing
Vue, TypeScript and CSS stack, Geist font, TH wordmark and green accent.
It is a product screen; marketing photography and scroll narratives do not
serve its task. Taste's dense-product scope limit applies to the future table.

- DESIGN_VARIANCE: 5. The configuration and archive have distinct hierarchy.
- MOTION_INTENSITY: 3. Brief motion communicates dealing, pot updates and actions.
- VISUAL_DENSITY: 5. Controls should fit a normal laptop without a large hero.

The initial audit found decorative step numbers and a status dot with no live
state, repeated heading labels, and an empty-state dash. These are removed.
A live seat diagram explains the selected configuration. A separate heads-up
table renders actual backend state; larger saved configurations remain setup only.

Theme tokens provide complete light and dark modes. Green is the only brand
accent; error red has a semantic role. Container radii are 1rem, controls
.65rem and the wordmark .4rem. Text and control colors require AA contrast.
Fonts are bundled locally. Layout collapses to one column below 768px.

## Playing table

Keep the same tokens and typography. Put the opponent above the board and
the hero below it; the active player also carries a textual turn indicator.
Cards use classic ivory faces, black clubs/spades and red diamonds/hearts,
with rank and suit in opposite corners, numbered pips and lettered court cards.
Backs have a local CSS pattern; undelivered community cards have dashed slots.
All cards have accessible names; hidden cards never have identifying labels.
Actions sit outside the felt, with the call cost, total raise and incremental
cost visible before confirmation. Mobile stacks the actions and reduces card
widths without horizontal scrolling. No perpetual motion or decorative imagery.

The right sidebar shows the hero's current combination and best available
five cards, based exclusively on hole cards and the current board. Before
the flop it describes the starting cards instead. A board-playing hand is
explicitly identified. The latest real bot action stays visible beside its
seat and in the sidebar, with its street to avoid suggesting a new action.
Card entry is staggered by 70ms; action and pot feedback last less than 700ms.
All animation respects the global prefers-reduced-motion override. On mobile
the sidebar moves below the felt and stacks vertically on narrow phones.

## Sequential actions

The API includes transient snapshots of the permitted player view, frozen
after each public event. The frontend presents each action before the next:
hero action 450ms, bot turn 900ms, bot action 900ms, street deal 800ms, award
650ms. These snapshots are for presentation; only the final revision accepts
new input. Reloading restores the authoritative final state directly.
The seat panels have clear borders and a visible active-player outline. A
persistent announcement above them names the current action or next turn.
No card, category or result from a later snapshot appears early. Reduced
motion disables visual animation while retaining the readable action order.
