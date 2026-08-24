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
- Versioned backup migrations and canonical-data enrichment.
- User custom dictionary/provenance.
- Experimental Animation Speed and Hide Par controls.

## Install

Copy `LetterBoxedCubed.user.js` into Tampermonkey (or a compatible userscript manager). A workplace-friendly `.txt` copy is in `workplace-copy/`.

## History fidelity

The Git history contains version commits/tags from `v1.0.0` through `v1.10.2`.

Exact retained generated artifacts are used from `v1.6.0` onward. The original downloadable files for `v1.0.0` through `v1.5.0` were no longer retained when this repository was assembled, so those six commits are explicitly marked **historical reconstructions from the chat requirements**. They preserve the feature progression but are not guaranteed byte-for-byte identical to the originally generated source.

Convenient snapshots of every represented version are also in `versions/`.

## Data philosophy

- **Migration** changes old data because the stored schema/meaning changed.
- **Enrichment** fills authoritative canonical facts that become available later without rewriting player history.
- Unknown historical information stays unknown; do not manufacture precision just to satisfy a newer schema.

See `docs/Architecture.md` and `docs/DataModel.md`.

## License

The userscript is already published on Greasy Fork under a copyleft license. The exact license identifier/text was not available while this package was assembled, so it has intentionally not been guessed. Add the exact Greasy Fork license before publishing this GitHub repository publicly.
