# Letter Boxed Cubed themes

LBC ships with two immutable presets, **NYT Light** and **NYT Dark**, plus portable custom themes. Custom definitions and the active selection live in the versioned `LetterBoxedCubed_ThemeState` record and sync independently of word/history data.

## ThemeState v2 semantic palette

ThemeState v2 describes what a color *means* rather than exposing implementation-specific CSS colors.

### Letter Boxed

- **Background** - page/game shell surrounding the board.
- **Board** - the white/dark filled region inside the GB square and node interiors.
- **Same as Background** - when enabled, Board tracks Background live and its picker is disabled.
- **Foreground** - neutral text, lines, borders, board letters, square outline, node outlines and word-entry rule.
- **Foreground (active)** - current/submitted paths and active/used board details.

NYT Light intentionally keeps its white Board separate from the pink web Background. NYT Dark intentionally ties Board to its `#121212` Background. Custom themes inherit that relationship from the preset/theme they are duplicated from.

### Letter Boxed Cubed

Custom themes expose **Background**, **Heading background**, **Text** and **Border**. Background has a **Same as Letter Boxed Background** relationship and Text has **Same as Letter Boxed Foreground**; both relationships are enabled in the two built-in presets and are inherited by custom themes duplicated from them. When a relationship is enabled, the dependent picker is disabled and follows its Letter Boxed source live. Existing beta custom themes that predate these flags infer the relationship only when the two stored colors already match, so intentionally independent colors are not overwritten.

Muted text is derived by mixing Text toward Background. Secondary accent surfaces are derived by shifting Background toward whichever black/white pole provides contrast.

### Highlights

Custom themes expose **NYT solution**, **New item** and **Redacted**. NYT-solution text is a hue-preserving darker shade of a light solution color or lighter tint of a dark solution color rather than being washed toward generic black/white. Its `★` uses the same derived color and is rendered 5px larger than the neighboring label while remaining vertically centered. Redacted blocks use one opaque color for background, text, border and selection so spoilers remain unreadable. Success/error indicators are fixed green/red rather than theme-editable.

## Semantic affine board transform

The visible web Letter Boxed board is a single canvas. Earlier betas tried to create dark mode by inverting the completed bitmap, normalizing canvas text calls, and occasionally walking the whole pixel buffer. That approach caused source-color races, double inversion during live theme changes, forced reloads, and expensive synchronous `getImageData()` work on slower hardware.

ThemeState v2 never mutates the canvas bitmap. Instead, LBC installs one SVG `feColorMatrix` compositor filter and updates its matrix whenever a native/custom theme changes. The matrix is solved as an affine RGB transformation anchored to three known colors in NYT's native Light renderer:

- source black -> theme **Foreground**;
- source white -> theme **Board**;
- source active coral (`#E8A9A0`) -> theme **Foreground (active)**.

Antialiased and blended pixels transform continuously between those anchors. Because NYT remains free to repaint its normal source canvas underneath the filter, theme changes are live: there is no board-inversion checkbox, bitmap repair, or Light/Dark reload boundary.

Preview diagnostics exposed one unavoidable source-palette collision: NYT paints both the board fill and inactive board-letter glyphs with native white. A color matrix cannot send one identical source RGB value to two different semantic destinations. LBC therefore adds one narrowly-scoped Canvas2D text shim: only single A-Z `fillText`/`strokeText` calls on the Letter Boxed board whose source paint is native white are temporarily normalized to native black. The affine matrix then maps those glyphs to **Foreground**, while the untouched white board fill still maps to **Board**. This is not the old bitmap-repair architecture: there is no pixel walk, `getImageData()` mutation, inversion, repaint polling, or path/node interception.

When a theme is first applied to an already-painted board, LBC issues a short resize-based renderer refresh so NYT repaints through the semantic text shim. Subsequent NYT redraws automatically use the same hook.

## Native shell and control details

The surrounding page, toolbar, generated outer `Game-module_gameContainer__*` wrapper and other native UI surfaces use Letter Boxed Background/Foreground directly. LBC themes NYT's real `.lb-text-field-underline` instead of painting a second synthetic line on the input wrapper. NYT's visible insertion cursor is a `.lb-text-field__caret` span rather than the browser-native caret, so that element and its pseudo-elements are explicitly themed to Foreground too. Native text fill, opacity, filter and blend treatment are normalized so the DOM Foreground matches the matrix-rendered GB Foreground instead of retaining NYT's lighter/tinted text treatment.

LBC's sliders, checkboxes, number-input steppers, scrollbars and draggable resize/gap handles are theme-aware. The control `color-scheme` follows the current LBC background brightness, while accent/track/thumb/handle colors come from semantic LBC palette values. Scrollbar thumbs/buttons now follow semantic Text/Foreground rather than the legacy maroon Border color. Number inputs share one compact presentation: right-aligned values, always-visible steppers, a small value-to-stepper gap, widths derived from the control's maximum digit count, and one extra character of left-side breathing room at that maximum width.

Transient valid and invalid word messages retain NYT's normal geometry/typography but use **Foreground (active)** as their background and **Board** as their text/icon color. Valid-word praise still uses LBC's source-independent lifecycle/placement proxy; the proxy snapshots praise immediately because NYT can retire its native source before Cubed's history-settling window completes.

Browse History reuses the same themed Completion / Longest Found stat-card treatment as the main LBC dashboard, including heading background, value text, muted labels and borders.

Preview-only beta version text continues to adapt its contrast to the Letter Boxed Background.

## Google Drive response safety

The Apps Script bridge is expected to return JSON. If Google/Apps Script transiently returns an HTML page instead (for example an authorization/error/interstitial response beginning with `<!DOCTYPE html>`), LBC detects that before parsing or merging any data. It retries the same request once after a short delay; Write retries retain the same idempotency `WriteId`. If the bridge still returns HTML, sync stops with a descriptive error. The HTML response is never imported into the LBC storage snapshot or written into the synced data payload.

## Preview board diagnostics

Preview builds expose two board-specific diagnostics in the Debug Pane. **Copy Board Source Snapshot** reads the unfiltered source bitmap once and reports the most common RGBA values together with the active theme variables, renderer-facing `--text` values, SVG matrix and computed canvas filter. **Start Board Canvas Trace** temporarily records `fillText`/`strokeText` calls made specifically to the Letter Boxed board canvas; after starting it, type or delete at least one board letter to force NYT to repaint, then use **Stop + Copy Board Trace**. These tools are preview-only and do not alter the production userscript.

## Migration

ThemeState v1 custom themes migrate automatically. Old `InvertBoard` is interpreted only during migration: Dark-derived themes become `BoardMatchesBackground=true`, while other themes remain independent. Old palette keys are mapped into the semantic v2 fields; obsolete editable muted/accent/success/error values are discarded in favor of derived/fixed behavior. Existing theme IDs and per-theme timestamps/tombstones are retained for merge-safe Drive sync.

## Preview acceptance checklist

Verify live NYT Light <-> NYT Dark switching without a reload; independent Background/Board behavior in a Light-derived custom theme; Board tracking while Same as Background is checked; LBC Background/Text semantic links; neutral and active GB colors during typing and after submission; exact DOM-vs-GB Foreground parity; the native word-entry underline and visible caret; theme-aware sliders/checkboxes/scrollbars/number steppers/drag handles; compact number inputs; the generated outer game-container background; valid/invalid message colors; NYT-solution tint/shade and larger star; custom Redacted color; Browse History Completion / Longest Found cards matching their main-dashboard counterparts; and a transient HTML Drive response failing safely rather than being treated as backup JSON.
