# Letter Boxed Cubed

A Tampermonkey userscript that augments The New York Times' Letter Boxed with persistent player data, spoiler-conscious Twofer analysis, custom vocabulary, backup/restore, and a responsive companion dashboard.

**Authorship:** Nathan Burgdorff + Ari (ChatGPT)

> Independent project; not affiliated with or endorsed by The New York Times.

## Highlights

- Persistent per-puzzle Found Words and spoiler-redacted Unfound Words.
- Exhaustive two-word solution ("Twofer") calculation/caching.
- Found / partially found / individually found / unfound Twofer grouping.
- First-word and second-word hint progress without exposing unfound candidates.
- `⭐ NYT Solution` annotation from `gameData.ourSolution` when the official answer is a Twofer.
- Completion, longest-word, and word-length statistics.
- Resizable responsive LBC dashboard.
- TI/GB/LBC layout management (`TI` = text input, `GB` = game board, `LBC` = Letter Boxed Cubed).
- Export/import with normalized data plus raw disaster-recovery `StorageSnapshot`.
- Merge-safe multi-device player data: imports union discoveries instead of overwriting them.
- Versioned backup migrations and canonical-data enrichment.
- Persistent portable GUI state for controls and expandable sections.
- User custom dictionary/provenance.
- Experimental Animation Speed and Hide Par controls.
- Google Drive synchronization via a user-owned Google Apps Script bridge (currently in v1.11 beta development).

## Install

Copy `LetterBoxedCubed.user.js` into Tampermonkey (or a compatible userscript manager). A workplace-friendly `.txt` copy is kept for releases under `workplace-copy/`.

## Google Drive sync

The v1.11 development branch can keep player data and portable GUI state synchronized through a small Google Apps Script bridge that runs under the player's own Google account. The bridge writes a visible `Letter Boxed Cubed/LetterBoxedCubedCloudBackup.json` file in Google Drive.

See `docs/GoogleDriveSync.md` for setup and security details.

## History fidelity

The preserved Git history contains version commits/tags from `v1.0.0` through `v1.10.2`; later source-only maintenance commits added license/namespace metadata and v1.10.3.

Exact retained generated artifacts are used from `v1.6.0` onward. The original downloadable files for `v1.0.0` through `v1.5.0` were no longer retained when this repository was assembled, so those six commits are explicitly marked **historical reconstructions from the chat requirements**. They preserve the feature progression but are not guaranteed byte-for-byte identical to the originally generated source.

Convenient snapshots of represented releases are also in `versions/`.

## Data philosophy

- **Migration** changes old data because the stored schema/meaning changed.
- **Enrichment** fills authoritative canonical facts that become available later without rewriting player history.
- **Merge** combines independent device histories monotonically wherever possible rather than treating one copy as authoritative.
- Unknown historical information stays unknown; do not manufacture precision just to satisfy a newer schema.

See `docs/Architecture.md` and `docs/DataModel.md`.

## License

Letter Boxed Cubed is licensed under **GPL-3.0-or-later**, matching its Greasy Fork publication. See `LICENSE` for the GPLv3 license text. You may redistribute and/or modify the project under GPL version 3 or, at your option, any later version.
