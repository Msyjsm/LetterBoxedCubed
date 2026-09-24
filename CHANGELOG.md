# Changelog

## 1.13.0
- Added persistent global word memory: words found on earlier puzzles are recognized when valid on the current board and participate in Found Words, statistics, Words by Length, Hints, and partial/independent Twofer states without auto-solving exact pairs.
- Added compact per-word Letter Boxed signatures and a versioned lifetime-history index so current-board historical lookup remains fast without rescanning every past puzzle on normal startup.
- Added chronological Browse History backfill so each archived day inherits only words found on earlier days, with historical styling/provenance and live-current-day parity checks.
- Added Google Drive/export merge support for global word history and historical projections, preserving unioned vocabulary and earliest provenance.
- Suppressed new-word discovery highlighting when a word was already known from an earlier puzzle.
- Preview-only tooling now includes the safe History Test sandbox for deterministic historical/twofer testing; preview/debug/test code remains excluded from the production userscript.

## 1.13.0-beta.2
- Backfilled Browse History chronologically so each retained puzzle inherits only words actually found on earlier puzzles that are structurally valid on that day's sides; future discoveries are never allowed to leak backward.
- Browse History now renders inherited words with the same darker previously-found styling used by the live panel, including solved-twofer constituents and first-found provenance tooltips when available. Completion/Longest/Found Words use the day's known-word projection.
- Today's Browse History record is overlaid from the live local puzzle before rendering, then sanity-checked against the live Known/Previously Found sets; any mismatch is logged and the live values win so the two views remain identical.
- Added a versioned, cloud-synced historical projection cache so the retroactive backfill persists instead of reparsing every retained day on every normal page load.
- Suppressed new-word highlight animations when a word is first entered on the current day but was already known from an earlier puzzle; newly solved twofers still receive their own twofer highlight.

## 1.13.0-beta.1
- Added persistent global word memory for issue #11. Existing `LetterBoxedTracker_*` puzzle histories are indexed once into a versioned global vocabulary; later discoveries update the index incrementally instead of rescanning every prior puzzle on each page load.
- Each lifetime word stores a compact Letter Boxed signature: a 26-bit letter mask plus distinct adjacent-letter constraints. Current-board lookup enumerates at most the 4096 subsets of the board's 12-letter mask, then validates side adjacency, keeping lookup fast as lifetime history grows.
- Previously found words that are playable on the current board now count as known in Found Words, completion/longest statistics, Words by Length, Hints, and partial Twofer discovery, with a subtly darker background and tooltip identifying historical discoveries.
- Historical knowledge never writes current-puzzle `FoundTwofers`. If both halves of a current valid Twofer are already known independently (including entirely from prior puzzles), the existing `Individually Found` spoiler-hidden state and `Valid solution independently found?` indicator apply without auto-solving the pair.
- Global word history is included in backup/Google Drive data and merges by word/provenance union. Imports from older clients that contain changed legacy tracker keys also update the global index incrementally.

## 1.12.3
- Replaced the corrupted generated logo Base64 with a byte-for-byte encoding of the original uploaded temporary logo (4,406 bytes; SHA-256 `4198a3a363878ed16e09937ccc71a5277bd4fd431ac4cbed1508a5bb70b1402f`).
- Added release validation for Base64 length, decoded byte length, SHA-256, PNG signature/chunk boundaries, and every PNG chunk CRC so future image-byte corruption fails CI instead of shipping.

## 1.12.2
- Fixed the embedded-logo canvas remaining transparent when PNG decoding completed before the newly constructed canvas had been attached to the DOM. Canvas pixels can be drawn while detached and persist after insertion, so logo rendering no longer depends on `Canvas.isConnected`.

## 1.12.1
- Fixed the temporary cube logo rendering as Chrome's broken-image placeholder on NYT. The PNG remains embedded byte-for-byte, but LBC now decodes it locally with `createImageBitmap()` and paints it to a canvas instead of assigning a CSP-blockable `data:` URL to an `<img>`.
- The logo canvas keeps the existing responsive square sizing logic, transparency, and 20-96px display range without external hosting or CORS dependencies.

## 1.12.0
- Released the completed v1.12 QoL/layout bundle after the beta.1-beta.20 preview cycle.
- Replaced the bordered pixel-size logo prototype with Nathan's temporary cube PNG. The exact image is embedded in the userscript and scales with the natural LBC header height while preserving its square aspect ratio.
- Moved the preview version label, TI/GB DOM debugger, and bootstrap diagnostics out of the production userscript into `tools/preview_runtime.js`. `tools/build_preview.py` now injects that module (and its `GM_info` grant) only into preview builds, so official releases do not ship the debugger implementation or UI.

## 1.12.0-beta.20
- Decoupled success-toast relocation from NYT's native toast rectangle: praise now remains in the lower slot for exactly one rendered history line and relocates above TI as soon as history wraps to line two.
- Anchored normal lower praise in the calibrated spare second-history-line slot, ending just inside the par's normal top margin. A visible par still pushes GB down, but showing/hiding the par no longer changes the toast's lower position or relocation threshold.
- Kept the 90px baseline history geometry and 22px structural TI/GB gutter unchanged; no additional toast-only whitespace is added.

## 1.12.0-beta.19
- Reserved the visible direct-child par prompt's full outer height in the fixed TI grid track, so an unhidden par pushes GB (and its normal-position success toast) downward instead of overlapping it.
- Par visibility/DOM-shape changes now trigger a targeted layout recalculation; hiding the par immediately collapses the extra space again without reintroducing general gameplay-driven GB movement.

## 1.12.0-beta.18
- Corrected title scaling so the captured native left offset is divided by CSS zoom, keeping the title bar's rendered left edge stationary while it grows/shrinks to the right.
- Fixed Compact title layout's 24px gap override by targeting the actual `#letter-boxed-container.pz-section` element rather than a nonexistent descendant `.pz-section`.
- Reposition the preview version label and Show/Hide Debug Pane control after header/title scaling changes so they stay attached to LBC as page geometry moves.
- Added a bottom-of-Display **Footer size** control (0%-200%, Reset = 100%) that proportionally scales the native `footer.pz-footer` and hides it at 0%.

## 1.12.0-beta.17
- Restored centered alignment for the zero-word `Try to solve in X words` par while preserving the alternate nested no-words DOM handling.
- Anchored the Letter Boxed title region to its captured native left edge before applying CSS zoom, so resize percentages grow/shrink to the right instead of recentering toward the viewport middle.
- Compact title layout now also removes the parent `.pz-section` top margin, reclaiming NYT's otherwise persistent 24px vertical gap.
- Preview's version label and Show/Hide Debug Pane button now use document-absolute positioning so they scroll with LBC; the debug pane itself remains fixed to the viewport.

## 1.12.0-beta.16
- Fixed the remaining double-toast/re-fade bug: Cubed no longer keys a valid-word toast to the live accepted-word count, which changes while NYT asynchronously commits the same accepted word to history. One non-empty native-toast lifecycle now owns one monotonic proxy generation.
- Cubed now keeps its praise proxy hidden until the accepted-word history count advances (with a 400ms safety ceiling), then measures the settled history geometry once and reveals the proxy in its final location. This prevents the normal-position flash followed by a jump above TI when a submission creates a new wrapped history line.

## 1.12.0-beta.15
- Suppress NYT valid-word praise by DOM location from the moment a native `.lb-message-box` is inserted, rather than waiting for NYT to add the later `success-message` class. This closes the one-paint race that caused a native toast followed by Cubed's proxy.
- Hardened native-toast suppression with visibility, opacity, clipping, animation, and transition overrides while preserving the source element's layout geometry for proxy positioning.
- Broadened native praise discovery to the square-container message box (and direct word-container non-error fallback) without affecting nested `error-message` validation feedback.

## 1.12.0-beta.14
- Made Cubed the sole renderer of valid-word praise while its TI/GB layout is active: NYT's native success box is suppressed before paint, then a proxy appears after a 60ms settle delay so accepted-word wrapping is already final before placement is chosen.
- Added stable per-submission toast identity using accepted-word count plus message text. Repeated NYT mutations for the same accepted word now reposition the existing proxy instead of recreating it and restarting the fade.
- When relocation is unnecessary, the proxy mirrors NYT's final rendered toast rectangle; when history would collide, it uses Cubed's above-TI position.

## 1.12.0-beta.13
- Replaced the parent-relative relocated success-toast positioning with a game-container-level proxy placed from live viewport geometry immediately above the text-entry wrapper; the native GB toast is hidden only after the proxy is populated and positioned.
- Removed the nested history scrollbars: `.lb-list-container` is now a non-scrolling fixed-height flex shell, `.lb-word-list-length` stays pinned, and only `.lb-word-list-container` owns vertical scrolling.
- Updated toast/history collision measurement to use the inner word-history viewport rather than the outer container that also contains the pinned word count.

## 1.12.0-beta.12
- Corrected the TI/GB grid track to include NYT's native TI top/bottom margins. The four geometry dumps showed that the board/history overlap was exactly the uncounted TI margin, so GB now begins after the visible TI rather than after its smaller nominal grid row.
- Added a fixed 22px TI/GB grip gutter derived from the existing 11px grip-line offset, centering the horizontal grip between the history lane and GB instead of placing it inside either region.
- Restored direct pointer interaction on the accepted-word history scroller, whose computed `pointer-events: none` was preventing scrollbar dragging/wheel targeting.
- Preserved the `success-message` class on relocated valid-word feedback and gave its proxy an explicit above-input position instead of relying on NYT's parent-dependent absolute positioning.
- Preview builds now show their exact runtime version in gray just above LBC, left-aligned with the logo placeholder. The header date now sits directly below Drive sync status beside the logo.

## 1.12.0-beta.11
- Removed NYT's native vertical margins from the square container while Cubed owns the TI/GB grid, preventing GB/canvas content from being pulled upward into the reserved history lane and blocking its scrollbar.
- Repositioned the draggable TI/GB grip into the gutter immediately below the history lane instead of anchoring it above the square container's native box.
- Added collision-aware valid-word feedback placement: if NYT's success message would crowd visible accepted-word history, Cubed mirrors it into the text-field wrapper where NYT already displays invalid-submission messages, with a small clearance buffer.
- Refreshed the generated Preview from the finalized beta.11 implementation commit after the one-shot patch workflow completed.

## 1.12.0-beta.10
- Recalibrated TI/GB spacing so the closest safe layout is displayed as 0px while preserving a 90px internal history-lane baseline; Reset now returns to 0px instead of the obsolete 16px value.
- Made the accepted-word history lane an exact-height scroll viewport rather than a flex-inferred remainder, so scrolling should begin before history can visually enter GB territory.
- Stopped structurally valid NYT-invalid submissions from rebuilding the entire LBC panel; the custom-dictionary header control now updates in place, preserving any active new-word highlight fade.

## 1.12.0-beta.9
- Raised the TI/GB horizontal resize-grip line above the GB top letters using the same visual offset as LBC's vertical grip lines.
- Made LBC's left and right vertical resize-grip lines symmetric outside the panel edges.
- Moved the Preview debugger farther right so LBC's right grip line is centered in an equal gutter between LBC and the debugger.
- Fixed the Preview debugger Show/Hide control with an explicit display override and right-aligned its external toggle with the Settings button.

## 1.12.0-beta.8
- Restored NYT invalid-submission feedback by allowing nested `.lb-message-box` popups to escape the fixed TI history-lane clipping while keeping accepted-word overflow inside its own scroller.
- Moved the Preview DOM debugger to the right of LBC and added an external Show/Hide Debug Pane toggle above LBC near Settings; mutation capture continues while the pane is hidden.

## 1.12.0-beta.7
- Added a Preview-only live TI/GB DOM inspector to the left of LBC, including per-element visibility overrides, selected outerHTML, and a mutation log that retains transient additions/removals.
- Added keyboard QoL shortcuts: Escape clicks NYT Restart, while Delete repeatedly invokes NYT Delete until one current-word boundary is reached.
- Kept the DOM inspector out of Production; it is intentionally development instrumentation for diagnosing transient NYT feedback elements and layout behavior.

## 1.12.0-beta.6
- Narrowed Hide par to the two actual NYT par-prompt DOM shapes so validation feedback such as "Too short" and "Not a valid word" remains visible.

## 1.12.0-beta.5
- Reworked TI/GB spacing into a fixed-height, scrollable accepted-word history lane so word wrapping cannot move the board.
- Removed the one-frame 0x0 logo-placeholder measurement that caused LBC to blink on word acceptance.
- Made Hide par independent of LBC layout state and the no-words DOM variant.
- Added Preview-only bootstrap telemetry for reproducing issue #1.

## 1.12.0-beta.4
- Fixed the TI/GB gap dead zone by preventing CSS Grid auto-track stretching and applying the preference as the actual TI-to-GB row gap.
- Fixed Hide par before the first accepted word by supporting NYT's alternate no-words par DOM placement.

## 1.12.0-beta.3
- Decoupled LBC from the TI/GB grid row sizing so the game board is no longer pinned to the bottom of the LBC panel.
- Kept the adjustable TI/GB spacing inside `.lb-list-container`, so each pixel of gap should now move the actual left-side layout immediately.
- Increased Settings text sizing to 12px and reduced the visual width of native number-input steppers where Chrome permits styling them.
- Replaced the temporary `Word Log` text with a live bordered square logo placeholder that reports its current pixel side length.

## 1.12.0-beta.2
- Reworked the TI-to-letter-box gap control to compact NYT's `.lb-list-container` instead of changing the outer grid row gap.
- Reorganized Settings into Feedback & animation, Display, and Sync; folded NYT page-layout controls into Display and clarified control labels.
- Replaced the beta title/byline and Yesterday proxy behaviors with Compact title layout and Hide Yesterday/Help row.
- Added new-word highlights to Completion and Longest Found, including tied-longest additions.
- Expanded Words by Length to one row per exact length present in the dictionary.

## 1.12.0-beta.1
- Moved Hide Par, animation controls, Google Drive actions, Export, and Import into a compact Settings menu; added a lightweight Drive status beside Word Log.
- Added an optional draggable TI-to-GB layout-gap handle with a stored precise gap setting.
- Added per-word solved/total Twofer progress to First/Second Hints and strike-through when a positional word is fully exhausted.
- Added configurable chartreuse fade highlights for newly found words and solved Twofers, including the matching Words by Length row.
- Added proportional resize/hide controls and on-page drag handles for NYT's global header and Letter Boxed title area.
- Added Settings toggles to place the byline and a Yesterday proxy beside the date.

## 1.11.0
- Added Google Drive synchronization through a user-owned Apps Script bridge with startup sync, read-merge-write semantics, revision-conflict retry, and local-only credentials.
- Made manual import and cloud sync merge-safe so independent devices union Found Words, solved Twofers, custom words, and compatible metadata instead of overwriting one another.
- Added portable GUI-state persistence and per-setting/per-section timestamps for conflict-safe multi-device merging; physical panel width remains device-local.
- Added Browse History for spoiler-safe, found-only cloud history with first/previous/next/last navigation and top-of-viewport modal anchoring.
- Fixed escaped newline text in dialogs and alerts.
- Added backup schema v3, migration support, regression tests, Drive documentation, preview-channel tooling, and release documentation.

## 1.11.0-beta.2
- Added Browse History, which reads the synced Google Drive backup and renders prior puzzle data in an LBC-style found-only history viewer.
- Added first/previous/next/last history navigation and defaulted the viewer to the most recent retained puzzle before the current day.
- Kept history spoiler-safe by omitting unfound/partially found data and not exposing the stored NYT solution merely because it exists in the cloud backup.
- Fixed UI strings that accidentally displayed escaped `\n` text instead of real line breaks.
- Documented that production and Preview userscripts have separate Tampermonkey GM-storage scopes.

## 1.11.0-beta.1
- Added merge-safe import semantics so independent device histories converge instead of overwriting same-day player data.
- Added backup schema v3 and versioned portable GUI state for Hide Par, Animation Speed, Twofer grouping, and expandable/collapsed sections.
- Added per-setting/per-section timestamps for conflict-safe GUI merging across devices.
- Added Google Drive synchronization through a user-owned Google Apps Script bridge, including revision-conflict retry.
- Kept physical panel width and cloud credentials device-local.
- Added merge regression tests, including the 10 + 23 disjoint found-word case.

## 1.10.2
- Tightened TI spacing, added Hide Par, renamed Animation Speed, and repaired feedback/par alignment.
## 1.10.1
- Stabilized TI/GB vertical layout so accepted words do not move GB.
## 1.10.0
- Added custom dictionary/provenance, experimental animation speed, backup schema v2, migration, and metadata enrichment.
## 1.9.0
- Added export/import, normalized puzzle export, raw StorageSnapshot, and durable metadata.
## 1.8.0
- Stacked TI+GB as the left meta-column; added container-query LBC responsiveness and improved resizing.
## 1.7.0
- Added NYT Solution annotation and persistent panel resizing.
## 1.6.2
- Restored native Twofers disclosure arrow and alignment.
## 1.6.1
- Limited First/Second hint lists to player-found candidates.
## 1.6.0
- Added separate Hints, nested hint nodes, grouped Twofers, and Group/Ungroup.
## 1.5.0
- Added light Twofer hints. (Historical reconstruction.)
## 1.4.0
- Added Twofer calculation/caching and exact-chain tracking. (Historical reconstruction.)
## 1.3.0
- Compact completion stats, collapsible Words by Length, side-by-side Found/Unfound. (Historical reconstruction.)
## 1.2.0
- Preserve NYT widths and position Word Log to the right. (Historical reconstruction.)
## 1.1.0
- First integrated side-by-side game layout. (Historical reconstruction.)
## 1.0.0
- Initial persistent word tracker. (Historical reconstruction.)