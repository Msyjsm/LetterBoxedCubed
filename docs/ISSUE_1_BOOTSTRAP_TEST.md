# Issue #1 bootstrap regression test

This branch removes Letter Boxed Cubed's terminal 20-second readiness timeout. NYT may legitimately remain on its pre-game splash screen indefinitely: `gameData` can already exist while `.lb-word-container` and `.lb-square-container` are not created until the player presses **Start Game**.

## Cold Tabs Outliner test

1. Use the Preview URL (`#lbc-preview`) in a Tabs Outliner saved/restored tab.
2. Start a fresh Chrome session and restore that tab.
3. Leave the NYT pre-game splash screen untouched for at least 20 seconds.
4. Confirm LBC does not emit the old fatal `Could not find Letter Boxed game data.` warning. Preview telemetry may record `wait-for-game-still-waiting` instead.
5. Press **Start Game** without reloading the page.
6. Confirm LBC initializes automatically when NYT creates the word and square containers.
7. Inspect `window.__LetterBoxedCubedBootstrapTrace`. Expected final milestones are `word-container-seen`, `square-container-seen`, `wait-for-game-ready`, and `initialize-complete`.

The readiness watcher uses a DOM MutationObserver for immediate game-container creation, plus a low-frequency poll and focus/pageshow/visibility checks as fallbacks. All listeners/observers are disconnected after readiness succeeds.
