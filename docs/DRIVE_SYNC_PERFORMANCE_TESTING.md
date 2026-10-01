# v1.13.1 Drive sync performance testing

This checklist covers issue #28 and the v1.13.1 event-driven Google Drive sync redesign.

## Why this exists

A Chrome Performance trace on an older ThinkPad showed repeated roughly 2.9-second main-thread tasks inside `SyncWithGoogleDrive()`. The dominant costs were rebuilding normalized historical puzzle exports, repeatedly normalizing historical/global word data, recomputing word signatures, sorting large collections, and then merging the same material back from Drive. Disabling Drive sync removed the gameplay lag entirely.

## New sync model

- LBC performs one Drive read/reconciliation after initialization.
- It does not poll Drive again during the session.
- Local synced changes mark cloud state dirty.
- Dirty changes are debounced into a push-only Write.
- A clean automatic sync is a true no-op: no export construction, normalization, Drive request, merge, or sorting.
- Manual **Drive: Sync** remains a full Read -> merge -> optional Write reconciliation.
- Automatic Writes use the Drive revision retained from the initial/manual Read. A revision conflict pauses automatic uploads rather than overwriting another LBC instance; manual Sync reconciles it.
- Browse History uses the locally merged session state and no longer performs another Drive Read when opened.

The existing Apps Script bridge already performs atomic ExpectedRevision checking under its script lock, so no remote lock-token lifecycle is necessary.

## Serialization changes

- Cloud payloads are lossless `StorageSnapshot` backups and deliberately omit the expensive normalized `Puzzles` analysis view (`Puzzles: []`).
- Full manual Export still constructs normalized puzzle records for analysis/database import.
- Historical projection normalization is reused across a full export instead of repeated for every puzzle.
- Current-version global-history and historical-projection records use trusted clone/merge paths rather than rebuilding deterministic metadata on every merge.
- Existing global word signatures are retained; only provenance is unioned during a current-version merge.
- Current-schema backups skip unnecessary migration cloning.
- Preview History Test still pauses persistence/sync; if it interrupted a real pending push, exiting the sandbox resumes that push.

## Automated coverage

Every preview build now runs:

```text
node --check LetterBoxedCubed.user.js
node tests/merge-tests.js
node tests/cloud-sync-tests.js
```

The cloud-sync regression suite covers:

- clean automatic sync -> zero Drive requests
- dirty automatic sync -> one Write and zero Reads
- revision increment after successful Write
- stale automatic Write -> Conflict without polling/overwrite
- manual reconciliation after conflict
- matching initial state -> one Read and zero Writes
- empty Drive -> one Read plus one seed Write
- snapshot-only cloud payload and exclusion of device-local panel widths
- current-schema migration fast path
- reuse of current-version global-word signatures while merging provenance

## Manual old-laptop test

Use the Preview URL (`#lbc-preview`) with Google Drive enabled.

1. Reload Letter Boxed and allow the initial Drive reconciliation to finish. The header should reach **Drive: Synced** / **Drive: ✓**.
2. Play normally for at least a minute, including typing, deleting, expanding/collapsing LBC sections, and leaving the page idle. There should be no recurring multi-second pauses.
3. Find one new word. The Drive status should briefly become **Pending**, then **Syncing**, then **Synced**. Gameplay should remain responsive while this happens.
4. Leave the puzzle unchanged afterward. No further cloud activity should occur merely because time passes.
5. Open Browse History. It should open from local retained data without initiating another Drive Read.
6. Click manual **Drive: Sync** once. This is the operation that should intentionally perform a fresh remote reconciliation.
7. Optionally capture another 30-60 second Chrome Performance trace with Drive enabled. The previous repeated ~2.9-second `SyncWithGoogleDrive()` tasks should be absent.

For an especially direct network check, filter DevTools Network for the Apps Script bridge. After the initial reconciliation, ordinary idle time should show no requests; a local change should produce a Write without a preceding Read.


## beta.2 timeout / idempotency regression tests

A bridge execution can outlive the browser request and still commit successfully. beta.2 therefore:

- raises the client request timeout from 30 to 60 seconds;
- assigns every Write a unique `WriteId`;
- retries the same payload with the same ID after an ambiguous timeout;
- performs one exceptional Read to verify a timeout or revision mismatch;
- treats matching `LastWriteId` (new bridge) or an identical remote `StorageSnapshot` (legacy bridge) as success;
- keeps genuinely different remote state in Conflict until manual reconciliation; and
- logs successful sync mode, revision, and duration for easier diagnosis.

The Apps Script bridge should be redeployed from the updated `integrations/google-drive/Code.gs`. The new bridge makes `WriteId` retries natively idempotent, exposes last-writer diagnostics, and minifies the Drive JSON to reduce write volume. The browser remains backward-compatible with the old bridge through snapshot verification.
