# Letter Boxed Cubed themes

LBC ships with two read-only presets: NYT Light and NYT Dark. Custom themes can be created from either preset and are stored in portable ThemeState so they can sync independently of word/history data.

## NYT Dark

NYT Dark is calibrated from the NYT mobile app appearance and adapts the web Letter Boxed page as closely as practical. The Letter Boxed board is canvas-rendered on the web, so its source bitmap needs special handling in dark mode.

Crossing between a non-inverted board theme and an inverted board theme intentionally reloads the Letter Boxed page after the new theme selection has been saved. This gives NYT a clean canvas lifecycle and avoids the race conditions and destructive double-inversion artifacts that occur when the already-painted board is recolored in place. Switching between themes that use the same board-inversion mode, or editing ordinary palette colors inside a custom theme, remains live and does not reload.

Dark native styling supplies the NYT game-level `--text` token and explicit caret colors. Because NYT's visible word-entry rule is not reliably the text field's own border, LBC paints a non-layout-affecting centered underline on the existing text-field wrapper. Its width follows the measured Letter Boxed square-container width rather than spanning the entire text-input column, so it stays visually aligned with the board/outer-letter footprint. The square container overrides `--text` back to the canvas source color required by the dark-board transform.

Valid-word praise is rendered by an LBC-owned relocated feedback proxy while the original NYT message remains only the lifecycle source. The visible proxy deliberately does not inherit NYT's `lb-message-box` / `success-message` classes, because those classes own transient animation/clip/opacity state that can strand a cloned toast invisibly under theme overrides. LBC copies only the authoritative message text and supplies its own small theme-aware surface, typography, border, and positioning. This keeps praise visible in both light and dark themes without depending on NYT's transient rendering state.

Preview-only beta version text also adapts its contrast to the active Letter Boxed page background. A relative-luminance threshold switches the normally dark gray label to a lighter gray on sufficiently dark custom/NYT Dark backgrounds.

Dark-mode toast timing note: NYT can retire its native success node before Cubed's 400ms history-settling window completes. Cubed therefore snapshots the praise text/lifecycle immediately, finishes history settling independently of the native node, and guarantees its own proxy at least 600ms of visible time once shown. This preserves stable placement without depending on NYT's shorter dark-mode toast lifetime.

The Preview transient-element trace confirmed the timing difference directly: in the failing NYT Dark case the native `Awesome!` source was cleared about 230ms after it became a success message, before Cubed's proxy was ever created; in the working NYT Light case Cubed created the proxy about 160ms after source detection and kept it visible for roughly 600ms. Beta.13 therefore treats the captured praise lifecycle as authoritative even after the native source disappears.

The Preview full-debug-bundle helper also now reports the current `InternalPanelLayoutStage` rather than the removed beta.3-era `InternalPanelLayoutMode`; a guarded fallback bundle is copied/logged if any future diagnostic field throws.
