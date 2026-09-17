# Changelog

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