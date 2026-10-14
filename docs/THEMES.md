# Letter Boxed Cubed themes

LBC ships with two immutable presets, **NYT Light** and **NYT Dark**, plus portable custom themes. Custom definitions and the active selection live in the versioned `LetterBoxedCubed_ThemeState` record and sync independently of word/history data.

## The Letter Boxed color triad

Every themed Letter Boxed view is defined by exactly three user-facing colors:

- **Background** - the surrounding Letter Boxed page/game color.
- **Foreground** - the primary text/outline color.
- **Highlight** - the third contrasting color used for the board surface in Light themes and active/used states in Dark themes.

The stored palette retains the older internal keys `LbBackground`, `LbForeground`, and `LbActive` for backward-compatible ThemeState v2 sync, but the settings UI exposes them only as Background, Foreground, and Highlight. `LbBoard` remains readable for older synced records but is not an independently editable Letter Boxed theme color.

Background luminance alone selects the semantic **Light** or **Dark** mapping column. The current cutoff is relative luminance `0.38`. Foreground and Highlight are never synthesized from Background; all rendered Letter Boxed states resolve to one of the three selected colors.

| Element | Light theme | Dark theme |
| --- | --- | --- |
| Text input | Foreground | Foreground |
| LB background | Background | Background |
| GB board background | Highlight | Background |
| GB board outline | Foreground | Foreground |
| GB letters - unused | Highlight | Foreground |
| GB node outline - unused | Foreground | Foreground |
| GB node background - unused | Highlight | Background |
| GB letters - active | Foreground (bold) | Highlight |
| GB node outline - active | Background | Highlight |
| GB node background - active | Highlight | Background |
| GB letters - used | Foreground (unbold) | Highlight |
| GB node outline - used | Foreground | Highlight |
| GB node background - used | Background | Highlight |
| Letter-line connectors | Background | Highlight |
| Mobile current/last node outline | Background | Highlight |
| Mobile current/last node background | Foreground | Foreground |
| Success toast foreground | Foreground | Background |
| Success toast background | Highlight | Foreground |
| Error toast foreground | Highlight | Background |
| Error toast background | Foreground | Highlight |

The built-in presets therefore begin as:

- **NYT Light:** Background salmon, Foreground black, Highlight white.
- **NYT Dark:** Background near-black, Foreground near-white, Highlight red.

These are preset values only. The state rules above never contain special-case target colors.

## Native NYT Light as the zero-override baseline

The built-in **NYT Light** preset deliberately does not theme NYT's native Letter Boxed UI at all. LBC removes its board canvas hooks/filter and native-page theme class, allowing NYT to render its own Light presentation directly. This avoids needless compositor/hook work and gives us an authoritative visual baseline.

When NYT Light is active, LBC samples NYT's live computed Background and Foreground after removing any previous custom-theme overrides. This keeps LBC's linked panel colors calibrated to the actual current NYT page rather than an old hardcoded salmon value. Duplicating NYT Light copies those sampled live colors into the new custom theme; Highlight remains the preset's white board anchor. The resulting custom copy **does** use LBC's theming pipeline, so an untouched Light-derived custom theme remains a parity test: it should be visually indistinguishable from native NYT Light.

Switching from a Dark semantic board to Light (or vice versa) changes how NYT's source canvas paints have to be interpreted. A synthetic `resize` event alone does not reliably repaint that canvas, so beta.23 gives the square container a one-frame 1px width nudge and restores its exact previous inline width immediately afterward. That real geometry change wakes NYT's ResizeObserver and forces the board to repaint under the new semantic source mapping instead of leaving letters missing until the next keystroke. Switching from a themed Dark board back to built-in NYT Light also restores the original Canvas2D methods before the repaint.

## Semantic canvas transform

The visible web Letter Boxed board is a single canvas. LBC leaves NYT drawing its normal Light source palette and uses one SVG affine color-matrix filter for custom themes and NYT Dark.

NYT's source palette has three useful anchors: source black, source white, and source active coral. They are mapped as follows:

- **Light semantic theme:** source black -> Foreground; source white -> Highlight; source coral -> Background.
- **Dark semantic theme:** source black -> Foreground; source white -> Background; source coral -> Highlight.

Antialiased and blended pixels transform continuously between those anchors. Normal rendering remains filter-only. The one deliberate exception is a Light/Dark semantic-mode switch: NYT does not repaint the canvas for synthetic resize events, so LBC performs a single bounded source-pixel repair in the four outer letter-label bands before swapping modes. The board square, nodes, and connectors are never touched by that repair, and same-mode theme switches do no bitmap work.

NYT reuses some source paints for semantically different things. In Dark semantic themes, a narrowly-scoped Canvas2D shim disambiguates only those collisions before the matrix runs: white single-letter source glyphs are normalized to the source-black anchor, black active/used single-letter glyphs to the source-coral anchor, and the used-node black outline paired with an active fill is promoted to the source-coral anchor. These are **source-palette identifiers**, not rendered theme colors; their final visible colors still come only from Background / Foreground / Highlight.

The mobile current/last-letter node naturally falls out of the same mapping: native coral outline plus native black fill becomes Background/Foreground in Light semantic themes and Highlight/Foreground in Dark semantic themes.

## Toasts

Success and error feedback share one LBC-owned toast presentation path. Native NYT feedback nodes are used only as lifecycle/text sources and are hidden while a proxy is visible. Both proxy types use the same placement function, so their position follows the same history-line rule rather than success and error occupying unrelated slots.

The entire proxy fades as one unit through opacity. Child text, pseudo-elements, and NYT's native message animations are suppressed on the proxy, preventing the previous white-corner flashes and text-only fades. Beta.23 adds explicit `6px 10px` toast padding so the proxy no longer collapses tightly around its letters.

If a success appears while an error toast is still visible, or an error appears while a success is still visible, the older proxy is removed immediately rather than cross-fading two messages. The newer toast owns the shared slot at once.

Toast colors come only from the Letter Boxed triad:

- Light success: Foreground on Highlight.
- Light error: Highlight on Foreground.
- Dark success: Background on Foreground.
- Dark error: Background on Highlight.

No success/error target color is independently hardcoded.

## Letter Boxed Cubed panel colors

The LBC panel has its own configurable Background, Foreground, Highlight, and Headings colors because its information-density and control surfaces are distinct from the native game. Background, Foreground, and Highlight can each optionally use the corresponding Letter Boxed color via a unified "Use Letter Boxed color" checkbox. Muted text and secondary control accents are derived from the LBC panel palette.

Highlights remain separate LBC concepts: NYT solution, New item, and Redacted. NYT-solution coloring is confined to the NYT Solution container/heading; the actual first/second-word cells retain ordinary Twofer revealed/redacted styling so the official answer cannot leak through. Redacted blocks use one opaque color for background, text, border, selection, and WebKit text fill.

## Native shell and control details

When a theme is actively applied to NYT, surrounding page surfaces use Background and ordinary native text/controls use Foreground. The current word-entry label/text/rule/caret use Foreground. The win modal keeps NYT's white modal surface; in Dark semantic mode its close X resolves to Background so it remains visible without introducing a separate literal close-button color.

LBC's sliders, checkboxes, number-input steppers, scrollbars, and draggable resize/gap handles remain theme-aware through the LBC panel palette. Preview-only beta version text continues to adapt its contrast to the Letter Boxed Background.

## Migration

ThemeState remains version 2 for compatibility with the current beta sync format. Existing custom themes keep their IDs, timestamps, and tombstones. The old `LbBoard`/BoardMatchesBackground representation is accepted on load, but Letter Boxed editing now treats Background / Foreground / Highlight as the authoritative triad. New custom themes copied from a preset preserve those three colors exactly instead of deriving Foreground from Background.

## Preview acceptance checklist

Test the following without reloading between theme changes where possible:

1. Built-in NYT Light visually matches NYT with LBC's native theming disabled.
2. Duplicate NYT Light into a custom theme without changing any colors; the page, board, and linked LBC colors should remain visually identical.
3. Switch native Light -> custom Light -> NYT Dark -> custom Dark -> native Light mid-puzzle without typing or submitting anything between switches; all 12 side letters must remain visible immediately.
4. At each switch inspect unused, active, used, and current/last-letter node states plus connector lines; no letter should disappear while waiting for new input.
5. Verify a success and an error toast in both Light and Dark semantic modes: whole rectangle/text fade together, `6px 10px` breathing room, no corner flash, correct triad colors, and identical placement rules.
6. Trigger opposite toast types in quick succession and verify the older toast disappears immediately when the newer one arrives.
7. Verify Hints empty text, NYT Solution redaction, and the win-modal close X remain correct.
8. Verify a transient HTML Google Drive response still fails safely rather than being treated as backup JSON.
