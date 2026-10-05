# Letter Boxed Cubed themes

LBC ships with two read-only presets: NYT Light and NYT Dark. Custom themes can be created from either preset and are stored in portable ThemeState so they can sync independently of word/history data.

## NYT Dark

NYT Dark is calibrated from the NYT mobile app appearance and adapts the web Letter Boxed page as closely as practical. The Letter Boxed board is canvas-rendered on the web, so its source bitmap needs special handling in dark mode.

Crossing between a non-inverted board theme and an inverted board theme intentionally reloads the Letter Boxed page after the new theme selection has been saved. This gives NYT a clean canvas lifecycle and avoids the race conditions and destructive double-inversion artifacts that occur when the already-painted board is recolored in place. Switching between themes that use the same board-inversion mode, or editing ordinary palette colors inside a custom theme, remains live and does not reload.

Dark native styling also supplies the NYT game-level `--text` token and explicit caret/border colors to keep the Letter Boxed word-entry underline and caret visible. The square container overrides that token back to the canvas source color required by the dark-board transform.
