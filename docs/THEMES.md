# Letter Boxed Cubed themes

LBC ships with two read-only presets: NYT Light and NYT Dark. Custom themes can be created from either preset and are stored in portable ThemeState so they can sync independently of word/history data.

## NYT Dark

NYT Dark is calibrated from the NYT mobile app appearance and adapts the web Letter Boxed page as closely as practical. The Letter Boxed board is canvas-rendered on the web, so its source bitmap needs special handling in dark mode.

Crossing between a non-inverted board theme and an inverted board theme intentionally reloads the Letter Boxed page after the new theme selection has been saved. This gives NYT a clean canvas lifecycle and avoids the race conditions and destructive double-inversion artifacts that occur when the already-painted board is recolored in place. Switching between themes that use the same board-inversion mode, or editing ordinary palette colors inside a custom theme, remains live and does not reload.

Dark native styling supplies the NYT game-level `--text` token and explicit caret colors. Because NYT's visible word-entry rule is not reliably the text field's own border, LBC also paints a non-layout-affecting inset underline on the existing text-field wrapper so the entry space remains visible on dark backgrounds. The square container overrides `--text` back to the canvas source color required by the dark-board transform.

Valid-word praise is rendered by LBC's relocated feedback proxy while the original NYT message remains the lifecycle source. Dark/native themes explicitly reset that proxy's opacity, clipping, animation/transition state, text/icon colors, background, and border so NYT's transient success-message styling cannot make the relocated toast disappear against a dark page.
