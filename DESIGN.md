# DESIGN.md

> Visual system for the web console (`web/static/`). Generated from the shipped CSS. Operate mode: the tool should disappear into the task.

## World

A risk operations console, not a dashboard. The reference is a security operations desk: dark surface, monospaced telemetry, hairline rules, and a status strip that reports which engine is live. The single moment of ceremony is the decision stamp, where a named human takes responsibility.

## Palette (restrained)

Semantic vocabulary is fixed and state-rich; the signal teal is reserved for live/positive state and primary actions.

| Token | Value | Use |
|---|---|---|
| `--bg` / `--bg-2` | `#0a0e0d` / `#0d1211` | page surfaces |
| `--panel` / `--panel-2` | `#111615` / `#151b19` | blocks, raised rows |
| `--well` | `#0c110f` | inset wells |
| `--line` / `--line-2` | `#202826` / `#2c3633` | hairline rules / control borders |
| `--text` / `--text-2` | `#e6ede9` / `#aab7b1` | primary / secondary text |
| `--muted` / `--dim` | `#7d8b85` / `#85938d` | labels, meta, placeholder |
| `--signal` | `#3ddc97` | live state, primary action, completeness |
| `--amber` | `#e8b84b` | draft state, partial completeness |
| `--red` | `#f0685a` | rejection, missing fields |

Contrast: body, placeholder, and muted meta all clear 4.5:1 against their surfaces. Status is never color-only (chip text, stamp text, audit column text all carry the word).

## Type

One family for the UI: **Public Sans** (system fallback). **JetBrains Mono** appears only for data and measurement: case IDs, package IDs, similarity scores, timestamps, step indices, and the UTC clock. Functional text floors at 12px. Headings carry their own weight — no kickers, no eyebrows, no section numbers beyond the real step sequence.

## Layout

- Left spine (rail) with brand, indexed nav (`01`–`04`), the engine status strip, and a UTC clock; collapses to a top bar under 1040px.
- A readout strip above the analysis view reports engine, completeness, precedent count, and request latency.
- Content column structured as sections separated by hairline rules rather than cards.
- Depth is declared once: 1px borders define blocks. No chromatic glow shadows, no card-inside-card, no shadow under a border.
- Responsive behavior is structural: the form and decision grids collapse to one column, the rail stacks, and the audit table scrolls horizontally inside its own wrapper rather than blowing out the page.

## Components

Every interactive control ships default, hover, focus, active, disabled, and loading states.

- **Status strip**: engine name, model, and a static dot (amber = mock, signal = live). Not a pulsing indicator — the value is stable per session.
- **Buttons**: primary (signal fill), ghost (bordered), danger (bordered red for reject). Loading shows a spinner inside the button, never a spinner in the content area.
- **Mode switch**: a labeled toggle that flips the analysis between the mock and real engine; disabled when no key is present.
- **Fields**: bordered inputs on wells, signal border plus a soft ring on focus, themed caret and placeholder.
- **Completeness**: a horizontal meter (no progress ring) with a mono score; level shifts signal → amber → red.
- **Precedent**: ledger rows with a mono ID, title, meta line, and a small score bar; rules between rows.
- **Decision**: a single bordered block; after a decision it is replaced by a rotated stamp (approved/rejected) with reviewer, time, and reason.
- **Audit**: a data table, newest first, with a teaching empty state.

## Motion

Two authored moments, both state changes: the completeness meter scales in when analysis arrives (`transform: scaleX`, never a layout property), and the decision stamp settles with a slight rotation. Transitions are 150-400ms on transform, opacity, color, and border only. Everything collapses under `prefers-reduced-motion: reduce`.

## Browser surfaces

Themed selection, caret (`--signal`), scrollbars, focus rings, and `tabular-nums` in data. These are treated as part of the design, not left to defaults.

## Bans observed

No gradient text, no glass or blur decoration, no colored glow shadows, no colored side borders, no hard offset shadows, no progress rings, no pulsing status dots, no emoji or Unicode-glyph icons (all icons are authored inline SVG in one stroke language), no modal. Branding is neutral.
