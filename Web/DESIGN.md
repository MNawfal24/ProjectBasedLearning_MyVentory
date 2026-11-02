# MyVentory web direction

The dashboard is the back office for the same café that already uses the
MyVentory mobile app. Direction comes from that app's theme
(`Mobile/lib/widgets/app_theme.dart`) so the two read as one product.

## Identity

Back-office console for a café owner who checks it in the morning: revenue,
what sold, what is running low. Calm, dense, numeric. Not a marketing page.

## Palette

Two core colours plus one accent. Neutrals are surface, ink and line.

| Role | Light | Dark | Use |
|---|---|---|---|
| Primary | `#1E5AEF` | `#6E9BFF` | navigation, primary action, main series |
| Ink | `#111827` | `#E8EDF6` | headings, figures |
| Accent | `#A14A08` | `#F5B841` | stock attention only |
| Danger | `#DC2626` | `#FF7A7A` | out of stock, errors |
| Surface | `#FFFFFF` | `#141A24` | panels |
| Canvas | `#F4F7FB` | `#0C1118` | page background |
| Line | `#E2E8F2` | `#243040` | dividers, chart grid |

Blue is the app's existing brand colour, so the web does not get its own.
Amber appears only where stock needs attention, which keeps a single meaning
for it. Red is reserved for out-of-stock and failures.

## Typography

Poppins, the mobile app's typeface. Figures use tabular numerals so columns of
numbers line up in tables and KPI rows. No display or mono face: this is a
reading surface for numbers, not a terminal.

## Layout

- Persistent left rail on wide screens, top bar on narrow screens. The rail is
  the navigation and never scrolls away.
- Each page opens with one focal element: the trend panel on the dashboard, the
  ledger table on transactions.
- KPI figures sit in a single strip divided by lines, not four identical cards.
  A strip reads as one instrument; four cards read as a template.
- Section rhythm varies on purpose: full width trend, two thirds plus one third,
  then full width table.

## Dial

ENERGY 1 / RHYTHM 2 / MOTION 1

Calm surfaces because it is a data tool. Rhythm breaks in the composition
(wide chart, narrow side panel, wide table) rather than in decoration. Motion
is limited to hover, focus and loading states; no entrance animation.

## Reasons written down

- Blue primary: already the mobile app's brand colour, so web and phone agree.
- Amber accent only on stock attention: one colour, one meaning. The light value is
  darkened to #A14A08 so text on the soft tint clears 4.5:1.
- Tabular figures: numeric columns must align for scanning, which is the main
  task on this surface.
- Divider strip instead of KPI cards: four identical cards is the template
  pattern; a strip behaves like one instrument panel.
- Charts drawn as inline SVG instead of a chart library: three chart shapes are
  needed, and hand-written SVG keeps the bundle small and the code easy to
  change without a dependency's API.
- Light theme default with a working dark toggle: the owner checks the
  dashboard at 06:00 and again at closing, so both lights are real.
- No gradients, glass or glow: nothing here is decorative, and the mobile app
  does not use them either.
