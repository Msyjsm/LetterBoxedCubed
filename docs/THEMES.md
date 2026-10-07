# Letter Boxed Cubed themes

LBC ships with two immutable presets, **NYT Light** and **NYT Dark**, plus portable custom themes. Custom definitions and the active selection live in the versioned `LetterBoxedCubed_ThemeState` record and sync independently of word/history data.

## ThemeState v2 semantic palette

ThemeState v2 describes what a color *means* rather than exposing implementation-specific CSS colors.

### Letter Boxed

- **Background** - page/game shell surrounding the board.
- **Board** - the white/dark filled region inside the GB square and node interiors.
- **Same as background** - when enabled, Board tracks Background live and its picker is disabled.
- **Foreground** - neutral text, lines, borders, board letters, square outline, node outlines and word-entry rule.
- **Foreground (active)** - current/submitted paths and active/used board details.

NYT Light intentionally keeps its white Board separate from the pink web Background. NYT Dark intentionally ties Board to its `#121212` Background. Custom themes inherit that relationship from the preset/theme they are duplicated from.

### Letter Boxed Cubed

Custom themes expose **Background**, **Heading background**, **Text** and **Border**. Muted text is derived by mixing Text toward Background. Secondary accent surfaces are derived by shifting Background toward whichever black/white pole provides contrast.

### Highlights

Custom themes expose **NYT solution**, **New item** and **Redacted**. NYT-solution text (including its `★`) is derived toward a contrasting light/dark shade. Redacted blocks use one opaque color for background, text, border and selection so spoilers remain unreadable. Success/error indicators are fixed green/red rather than theme-editable.

## Semantic affine board transform

The visible web Letter Boxed board is a single canvas. Earlier betas tried to create dark mode by inverting the completed bitmap, normalizing canvas text calls, and occasionally walking the whole pixel buffer. That approach caused source-color races, double inversion during live theme changes, forced reloads, and expensive synchronous `getImageData()` work on slower hardware.

ThemeState v2 never mutates the canvas bitmap. Instead, LBC installs one SVG `feColorMatrix` compositor filter and updates its matrix whenever a native/custom theme changes. The matrix is solved as an affine RGB transformation anchored to three known colors in NYT's native Light renderer:

- source black -> theme **Foreground**;
- source white -> theme **Board**;
- source active coral (`#E8A9A0`) -> theme **Foreground (active)**.

Antialiased and blended pixels transform continuously between those anchors. Because NYT remains free to repaint its normal source canvas underneath the filter, theme changes are live: there is no board-inversion checkbox, bitmap repair, Canvas2D monkeypatch, or Light/Dark reload boundary.

The square container is deliberately kept on NYT's neutral black source `--text` while board theming is active so NYT continues drawing the expected source palette before composition.

## Native shell details

The surrounding page, toolbar, generated outer `Game-module_gameContainer__*` wrapper and other native UI surfaces use Letter Boxed Background/Foreground directly. LBC themes NYT's real `.lb-text-field-underline` instead of painting a second synthetic line on the input wrapper.

Valid-word praise still uses LBC's source-independent lifecycle/placement proxy while preserving NYT's native toast presentation classes. The proxy snapshots praise immediately because NYT Dark can retire its native source before Cubed's history-settling window completes.

Preview-only beta version text continues to adapt its contrast to the Letter Boxed Background.

## Migration

ThemeState v1 custom themes migrate automatically. Old `InvertBoard` is interpreted only during migration: Dark-derived themes become `BoardMatchesBackground=true`, while other themes remain independent. Old palette keys are mapped into the semantic v2 fields; obsolete editable muted/accent/success/error values are discarded in favor of derived/fixed behavior. Existing theme IDs and per-theme timestamps/tombstones are retained for merge-safe Drive sync.

## Preview acceptance checklist

For the first v2 Preview pass, verify live NYT Light <-> NYT Dark switching without a reload; independent Background/Board behavior in a Light-derived custom theme; Board tracking while Same as background is checked; neutral and active GB colors during typing and after submission; the native word-entry underline; the generated outer game-container background; toast behavior; NYT-solution contrast/star color; and custom Redacted color.
