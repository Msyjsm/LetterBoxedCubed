# Changelog

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
