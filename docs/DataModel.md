# Data Model

## Export layers

The export contains:

1. A normalized representation intended for analysis, database import, NytPuzzleCorpus integration, and potential public/extended datasets.
2. `StorageSnapshot`, a raw preservation of LBC's GM/Tampermonkey records for disaster recovery and future migrations.

## Migration vs. enrichment

**Migration:** old stored shape/meaning is converted forward one schema version at a time.

**Enrichment:** authoritative canonical data becomes available later and fills an existing instance (for example a previously missing `NytSolution` when the same puzzle is loaded under a newer script).

Player history must not be inferred from the current DOM during enrichment.

## Migration rule

Each `prev -> curr` migration should document what changed, why, field mappings, assumptions, and anything that cannot be preserved. Old migrations are historical fossils: alter them only to fix actual migration bugs.

## Unknown historical values

Do not manufacture precision. If an exact timestamp was never tracked, use `null`/explicit precision metadata rather than fabricating midnight or import-time values.
