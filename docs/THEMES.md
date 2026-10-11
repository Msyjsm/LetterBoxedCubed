# Letter Boxed Cubed themes

LBC ships with two immutable presets, **NYT Light** and **NYT Dark**, plus portable custom themes. Custom definitions and the active selection live in the versioned `LetterBoxedCubed_ThemeState` record and sync independently of word/history data.

## ThemeState v2 and the beta.21 three-color model

ThemeState remains at v2 for backup/cloud compatibility, but beta.21 deliberately simplifies the user-facing Letter Boxed palette. Custom themes expose only three directly editable Letter Boxed colors:

- **Primary (background)** - the Letter Boxed page/game-shell background.
- **Secondary (board)** - the interior board/node fill anchor.
- **Tertiary (active / used)** - active/used node and connector accent.

Letter Boxed **Text / Outline** is derived automatically from Primary. LBC computes Primary's relative luminance and chooses black for a light Primary or white for a dark Primary. That same derived light/dark decision drives board state disambiguation and the error-toast palette.

The older stored `LbForeground` and `BoardMatchesBackground` fields remain readable for migration and sync compatibility, but they are no longer independent Letter Boxed controls in the beta.21 theme editor. New custom themes always treat Primary, Secondary and Tertiary as independent colors.

The built-in presets are calibrated as follows:

| Preset | Primary | Secondary | Tertiary | Derived Text / Outline |
| --- | --- | --- | --- | --- |
| NYT Light | `#E3A5A3` | `#FFFFFF` | native coral `#E8A9A0` | black |
| NYT Dark | `#121212` | `#121212` | `#DA5D57` | white |

## Letter Boxed state truth table

The board is stateful, so the three palette colors do not map one-to-one to every visible element. Beta.21 follows the native NYT Light/Dark semantics below.

| Element | Light semantic | Dark semantic |
| --- | --- | --- |
| Text Input | derived black | derived white |
| LB Background | Primary | Primary |
| GB Board Background | Secondary | Secondary |
| GB Board Outline | derived black | derived white |
| GB Letters - unused | white | white |
| GB Node Outline - unused | derived black | derived white |
| GB Node Background - unused | Secondary | Secondary |
| GB Letters - active | derived black, bold | Tertiary |
| GB Node Outline - active | Tertiary | Tertiary |
| GB Node Background - active | Secondary | Secondary |
| GB Letters - used | derived black, unbold | Tertiary |
| GB Node Outline - used | derived black | Tertiary |
| GB Node Background - used | Tertiary | Tertiary |
| Letter connectors | Tertiary | Tertiary |
| Success toast foreground | black | black |
| Success toast background | white | white |
| Error toast foreground | white | Primary |
| Error toast background | black | derived Text Input |

On mobile, NYT exposes one additional board state: **Current Letter / Last Entered**. Its node remains the most recently entered letter both before and after word submission. In a light theme its outline is Tertiary and its fill is black. In a dark theme its outline is Tertiary and its fill is white.

The error-toast dark-mode rule intentionally differs from NYT's stock gray error surface: beta.21 uses the derived Text Input color as the background and Primary as the foreground. With the stock dark preset, that means white on black.

## Letter Boxed Cubed colors

The LBC side of a custom theme still exposes **Background**, **Heading background**, **Text** and **Border**. LBC Background can be linked with **Same as Letter Boxed Background**. LBC Text can be linked with **Same as Letter Boxed Text**; Letter Boxed Text means the black/white value derived from Primary, not another editable LB swatch.

Both links are enabled in the built-in presets and are inherited when a custom theme is duplicated from them. When linked, the dependent LBC picker follows the Letter Boxed semantic source live. Muted LBC text is derived by mixing LBC Text toward LBC Background, and secondary LBC accent surfaces are derived from LBC Background and its contrast pole.

The Hints `None found yet.` empty-state text is normal LBC Text, not muted text.

## Highlights and NYT Solution

Custom themes expose **NYT solution**, **New item** and **Redacted**. NYT-solution heading text is a hue-preserving darker shade of a light solution color or lighter tint of a dark solution color. The `★` uses that same derived heading color and is 5px larger than the neighboring heading text while remaining vertically centered.

The NYT Solution color applies only to the solution card itself and its heading/star. The actual First Word / Second Word row inside the card uses exactly the same Twofer word styling and redaction rules as every other Twofer. An unrevealed solution word therefore remains opaque/redacted rather than inheriting the solution-card foreground. Redacted elements also explicitly set `-webkit-text-fill-color` so an inherited browser text-fill rule cannot accidentally reveal them.

## Semantic affine board transform

The visible Letter Boxed board is a single canvas. LBC does not mutate its bitmap. Instead, it applies one SVG `feColorMatrix` compositor whose three source anchors are the colors NYT's native Light renderer already paints:

- source black -> derived **Text / Outline**;
- source white -> **Secondary**;
- source active coral (`#E8A9A0`) -> **Tertiary**.

This maps board fill, outlines, node fills and connectors continuously without per-pixel reads or bitmap repair. Light, Dark and custom themes all run through this same compositor in beta.21, including NYT Light itself. That removes the old special case where switching back to Light could expose stale source state left by a previously active theme.

### Source-color collisions

The native source renderer reuses the same RGB values for elements that have different dark-mode semantics. Beta.21 resolves only those collisions and leaves all other canvas painting untouched.

For dark themes, a narrowly scoped Canvas2D text shim intercepts only single A-Z board `fillText` / `strokeText` calls. Native-white unused glyphs are normalized to the black source anchor so they remain derived white after the matrix, while native-black active/used glyphs are normalized to the coral source anchor so they become Tertiary.

Used nodes require one additional dark-mode distinction: NYT paints their fill with native coral but their outline with native black, while the target dark truth table wants both surfaces Tertiary. A scoped `stroke()` shim detects that exact coral-fill + black-outline paint pair and temporarily promotes only that outline to the coral source anchor. The mobile Current/Last node already arrives as coral outline + black fill, so the matrix naturally yields Tertiary outline + derived-white fill without another special case.

These shims are state-color disambiguators, not the old bitmap-repair architecture: there is no `getImageData()` pixel walk, inversion pass, or post-render bitmap mutation.

## Live theme switching

Every theme application updates the semantic CSS variables and the affine matrix, then queues a short resize-based renderer refresh. NYT redraws its canvas through the same semantic hooks, so switching Light -> Dark -> custom -> Light in the middle of a puzzle is intended to preserve the current unused/active/used states rather than requiring a page reload.

Because board behavior ultimately depends on NYT's live canvas renderer, mid-puzzle switching is part of the required acceptance testing rather than something static tests alone can prove.

## Native shell, input and controls

The surrounding page, toolbar, generated `Game-module_gameContainer__*` wrapper and other native Letter Boxed surfaces use Primary plus the derived Text / Outline color. The word-entry label, typed word, underline and visible caret use derived Text Input - black for light themes, white for dark themes - rather than Tertiary.

LBC themes NYT's real `.lb-text-field-underline`; it does not paint a duplicate synthetic line. NYT's visible insertion cursor is a `.lb-text-field__caret` span, so that element and its pseudo-elements are explicitly themed as well. Native opacity, filters, text shadows and blend treatment are normalized where necessary so the selected semantic color is not silently altered by NYT presentation CSS.

LBC's sliders, checkboxes, number-input steppers, scrollbars and draggable resize/gap handles are theme-aware. The page scrollbar uses Letter Boxed Primary / derived Text. LBC, Settings and History scrollbars use LBC Background for the track and LBC Text for thumb/buttons. Number inputs use right-aligned values, always-visible steppers, compact maximum-digit sizing and one extra character of left-side breathing room.

## Toasts and congrats modal

Success and error feedback use separate semantic palettes rather than sharing the board accent. Success is always black on white. Light-mode errors are white on black. Dark-mode errors use derived Text Input for their background and Primary for their foreground.

Valid-word praise still uses LBC's source-independent lifecycle/placement proxy so the captured NYT praise survives even if NYT removes its native source element before LBC's history-settling window finishes.

The congratulations modal remains NYT's white modal surface. In dark themes, `button[data-testid="modal-close"]` is explicitly kept transparent with a black close icon so the generic dark-page button treatment cannot produce black-on-black.

## Browse History and other LBC surfaces

Browse History reuses the same themed Completion / Longest Found stat-card treatment as the live LBC dashboard, including heading background, value text, muted labels and borders. Preview-only beta version text continues to adapt its contrast to the Letter Boxed Primary background.

## Google Drive response safety

The Apps Script bridge is expected to return JSON. If Google/Apps Script transiently returns an HTML page instead - for example an authorization/error/interstitial response beginning with `<!DOCTYPE html>` - LBC detects that before parsing or merging any data. It retries the same request once after a short delay; Write retries retain the same idempotency `WriteId`. If the bridge still returns HTML, sync stops with a descriptive error. The HTML response is never imported into the LBC storage snapshot or written into the synced data payload.

## Preview board diagnostics

Preview builds expose board diagnostics in the Debug Pane. **Copy Board Source Snapshot** reads the unfiltered source bitmap once and reports common source RGBA values together with the active theme variables, renderer-facing values, SVG matrix and computed canvas filter. **Start Board Canvas Trace** / **Stop + Copy Board Trace** records board Canvas2D text draws after typing/deleting a letter. **Copy Full Debug Bundle** includes the board diagnostics alongside layout/runtime state.

These are diagnostic reads only; they do not alter the production userscript or mutate the board bitmap.

## Migration

ThemeState v2 is retained so existing synced beta themes do not require a storage-schema fork. v1 palette keys continue to normalize into the v2 record shape. Older `BoardMatchesBackground` / `InvertBoard` information is still understood while reading legacy data, but the beta.21 editor no longer exposes a Board/Background linkage and new custom themes use independent Primary and Secondary values.

Existing theme IDs, timestamps and tombstones remain intact for merge-safe Drive sync. Existing custom LBC Background/Text link flags are retained. The user-facing LBC text-link label is now **Same as Letter Boxed Text** because that source color is derived from Primary.

## Beta.21 acceptance checklist

The static regression suite checks the semantic machinery, but visual acceptance requires exercising the actual NYT renderer. In Preview, verify at minimum:

1. On a fresh puzzle, all unused GB letters/node/board colors match the truth table before any typing.
2. Type through several letters and compare active letter, active node, connector and Text Input states.
3. Submit at least one word and compare used letter/node states against still-unused and currently-active nodes.
4. Without reloading, switch **NYT Light -> NYT Dark -> a custom theme -> NYT Light** while the puzzle already contains both used and active state, and repeat the switch more than once.
5. On mobile, verify the Current Letter / Last Entered node before and after submitting a word.
6. Verify success and error toasts separately in Light and Dark.
7. Verify an unrevealed NYT Solution remains redacted while only its card/heading use the solution highlight.
8. Verify `None found yet.` uses LBC Text.
9. Open the congratulations modal in Dark and confirm its close X remains black on the white modal.
10. Recheck LBC/Settings/History scrollbars and compact number inputs, then verify a transient HTML Drive response still fails safely rather than entering backup data.
