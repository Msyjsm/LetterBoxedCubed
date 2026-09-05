# Data Model

## Export layers

The export contains two complementary layers:

1. A normalized representation intended for analysis, database import, NytPuzzleCorpus integration, and potential public/extended datasets.
2. `StorageSnapshot`, a raw preservation of LBC's GM/Tampermonkey records for disaster recovery and future migrations.

Backup schema v3 also carries a normalized top-level `GuiState` object.

## Merge-before-write

Imports and cloud sync are **merges**, not replacements. The same merge engine is used for both manual imports and Google Drive synchronization so the rules cannot silently drift apart.

Current merge rules:

- `FoundWords`: set union.
- solved Twofers: set union.
- per-puzzle custom words: set union.
- custom dictionary: merge by word while preserving honest provenance; unknown historical first-added timestamps stay unknown.
- puzzle metadata: prefer the more recently seen record, then enrich missing canonical fields from the other copy.
- Twofer cache: prefer the higher cache version, then the richer cache at equal version.
- portable GUI state: merge each individual setting/section by its own `UpdatedAt` timestamp; if both timestamps are unknown, the local value wins.
- physical panel width: device-local. An import can restore it only when the current device does not already have a preference; cloud sync omits it entirely.

Therefore two devices that independently discover disjoint words for the same puzzle converge on their union rather than overwriting one another.

## GUI state

Portable GUI state is stored under `LetterBoxedCubed_GuiState`:

```text
Version
Settings
  HidePar
  AnimationSpeed
  TwofersGrouped
Sections
  Hints
  HintFirstWords
  HintSecondWords
  Twofers
  WordsByLength
  FoundWords
  UnfoundWords
```

Each setting stores `{ Value, UpdatedAt }`. Each expandable section stores `{ Open, UpdatedAt }`.

The per-entry timestamp is deliberate: changing Animation Speed on one computer must not make an unrelated, newer Hints expansion choice from another computer disappear.

## Portable vs. device-local state

Player data and semantic GUI preferences are portable. Physical layout dimensions are device-local.

For example, a preferred LBC panel width that feels right on a widescreen desktop should not be pushed onto a laptop simply because both devices share the same player history.

Cloud credentials (`Endpoint` and shared `Secret`) are also local-only and are **never** included in export/backup data.

## Migration vs. enrichment

**Migration:** old stored shape/meaning is converted forward one schema version at a time.

**Enrichment:** authoritative canonical data becomes available later and fills an existing instance (for example a previously missing `NytSolution` when the same puzzle is loaded under a newer script).

Player history must not be inferred from the current DOM during enrichment.

## Migration rule

Each `prev -> curr` migration should document what changed, why, field mappings, assumptions, and anything that cannot be preserved. Old migrations are historical fossils: alter them only to fix actual migration bugs.

Backup schema v3 adds portable GUI state. The v2 -> v3 migration can recover legacy Hide Par and Animation Speed values if they existed, but their historical timestamps remain `null`; older backups did not contain trustworthy tree/group state, so none is invented.

## Unknown historical values

Do not manufacture precision. If an exact timestamp was never tracked, use `null`/explicit precision metadata rather than fabricating midnight or import-time values.
