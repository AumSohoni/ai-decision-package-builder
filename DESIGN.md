# DESIGN.md

> Visual system for the web console (`web/static/`). Generated from the shipped CSS. Operate mode: the tool should disappear into the task.

## World

A calm risk register, not a dashboard. The reference is a well-kept ledger: paper surface, ink text, thin rules instead of grids of cards, and a dark spine holding the sections. The one moment of warmth is the decision stamp — the point where a human takes responsibility.

## Palette (restrained)

Semantic vocabulary is fixed and state-rich; the accent is reserved for primary actions, current selection, and state.

| Token | Value | Use |
|---|---|---|
| `--paper` | `#f3f4f0` | page surface |
| `--paper-2` | `#eceee8` | inset wells, hover fills |
| `--surface` | `#fbfbf9` | form fields, decision block |
| `--ink` | `#141815` | primary text |
| `--ink-2` | `#3a423b` | secondary text |
| `--muted` | `#5b645c` | labels, meta, placeholder |
| `--line` / `--line-2` | `#dcdfd7` / `#c7cdc3` | hairline rules / control borders |
| `--rail` | `#121714` | left spine |
| `--accent` | `#1e5b48` | primary action, selection, completeness |
| `--danger` | `#9f3628` | rejection, missing fields |
| `--warn` | `#7d5200` | draft state, partial completeness |

Contrast: body, placeholder, and rail secondary text all clear 4.5:1. Status is never color-only (chip text, stamp text, audit column text all carry the word).

## Type

One family for the UI: **Public Sans** (system fallback), fixed rem scale at a 1.125-1.2 ratio. Headings carry their own weight — no kickers, no eyebrows, no section numbers beyond the real three-step sequence. **JetBrains Mono** appears only for data and measurement: case IDs, package IDs, similarity scores, timestamps, step numbers, and tabular figures. Monospace is never a costume.

## Layout

- Left spine (264px) with brand, section nav, and the "AI prepares. Humans decide." motto; collapses to a top bar under 1040px.
- Content column max ~1060px, structured as sections separated by hairline rules rather than cards.
- Depth is declared once: 1px borders define blocks; shadows appear only on focus. No card-inside-card, no shadow under a border.
- Responsive behavior is structural: the form and decision grids collapse to one column, the rail stacks, and the audit table scrolls horizontally inside its own wrapper rather than blowing out the page.

## Components

Every interactive control ships default, hover, focus, active, disabled, and loading states.

- **Buttons**: primary (accent fill), ghost (bordered), danger (bordered red for reject). Loading shows a spinner inside the button, never a spinner in the content area.
- **Fields**: bordered inputs on `--surface`, accent border plus a soft ring on focus, themed caret and placeholder.
- **Completeness**: a horizontal meter (no progress ring) with a mono score; level shifts accent → warn → danger.
- **Precedent**: ledger rows with a mono ID, title, meta line, and a small score bar; rules between rows.
- **Decision**: a single bordered block; after a decision it is replaced by a rotated stamp (approved/rejected) with reviewer, time, and reason.
- **Audit**: a data table, newest first, with a teaching empty state.

## Motion

Two authored moments, both state changes: the completeness meter scales in when analysis arrives (`transform: scaleX`, never a layout property), and the decision stamp settles with a slight rotation. Transitions are 150-400ms on transform, opacity, color, and border only. Everything collapses under `prefers-reduced-motion: reduce`.

## Browser surfaces

Themed selection (`--accent-soft`), caret (`--accent`), scrollbars, focus rings, and `tabular-nums` in data. These are treated as part of the design, not left to defaults.

## Bans observed

No gradient text, no glass or blur decoration, no colored side borders, no hard offset shadows, no progress rings, no emoji or Unicode-glyph icons (all icons are authored inline SVG in one stroke language), no modal. Branding is neutral.
