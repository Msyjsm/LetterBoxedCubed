# Google Drive Sync

> Google Drive sync is available in LBC v1.11 and later.

Letter Boxed Cubed can synchronize its portable player data and GUI state through a small Google Apps Script bridge owned by the user. The actual cloud backup is stored as a visible JSON file in a `Letter Boxed Cubed` folder in the user's Google Drive.

## Why a bridge?

LBC runs on `nytimes.com`, which Nathan Burgdorff does not own. Google's OAuth policies require web-app JavaScript origins/redirects to use domains the developer owns or is authorized to use, and Google's browser token model uses short-lived access tokens that eventually require another user-driven authorization gesture. A user-owned Apps Script bridge avoids both problems: Apps Script receives Drive permission once, while LBC talks only to the user's deployed bridge.

## One-time setup (limited-scope Drive bridge)

See the public-facing [Google Drive Sync setup page](https://nathanburgdorff.com/lbc/google-drive-sync/) for an illustrated/user-friendly path.

1. Open the **read-only reference script**: https://script.google.com/d/1fldV7mLrlVhthGEwtipBGShe1buO49Gw_QdmWWtoiBno-ZTvbpVD7-Pz/edit?usp=sharing. Make a private copy or create a new Apps Script project. **The source of this reference project does not auto-update from GitHub.** Verify it contains the latest files before authorizing permissions.
2. Replace `Code.gs` with [the latest checked-in bridge](../integrations/google-drive/Code.gs).
3. In Apps Script **Project Settings**, enable displaying the manifest, and replace `appsscript.json` with [this file](../integrations/google-drive/appsscript.json). It deliberately declares two scopes: `drive.file` and `script.external_request`, plus the Drive API v3 advanced service. If you are using a standard Google Cloud project, enable its Drive API if needed.
4. Run `Setup()` from the Apps Script editor and grant only the displayed permissions. It creates an **app-owned** Drive folder/file and prints the sync secret to the execution log.
5. Choose **Deploy > New deployment > Web app**. Set **Execute as: Me** and **Who has access: Anyone**.
6. Copy the `/exec` URL and your generated sync secret into LBC's **Settings > Sync > Drive: Setup** prompts.

The endpoint is public, but every request is gated by your high-entropy sync secret. Treat both as sensitive. The secret is only stored in Apps Script Properties and local Tampermonkey storage; it is excluded from exports, Drive backup payloads, and the independent local recovery mirror.

### Why `drive.file` is not just a manifest edit

The original bridge used Apps Script `DriveApp`, which demands broader Drive authorization. The restricted bridge now uses **Advanced Drive API v3** for folder and file creation and writes. To read the backup text, it uses `UrlFetchApp.fetch()` against the **Google Drive REST API** with `ScriptApp.getOAuthToken()`, because the Advanced Drive service does not reliably return raw files with `alt=media`. This needs the additional Apps Script `script.external_request` permission, although the code targets only Google's Drive API. **Do not reintroduce `DriveApp` when fixing an error** or you will lose the scope benefit.

### Upgrading an existing `DriveApp` bridge

Files created/located under the old broad `DriveApp` authorization may not be accessible via `drive.file`. The new script deliberately **refuses to silently replace an inaccessible stored backup with an empty one**. If you already have a Drive connection:

1. **Export a complete LBC backup locally first.**
2. Replace Code.gs and appsscript.json, run `Setup()`.
3. If it says your previous backup is inaccessible, run `StartFreshLimitedScopeBackupAfterExport()`, then `Setup()`. This creates a fresh limited-scope folder/file but **does not delete the previous Drive backup**.
4. Use LBC's existing local history (or import your export) to seed the new Drive backup with a manual sync. Recheck a second device after that.

This is a protocol-compatible migration of the bridge's storage implementation, not a data format change. We should still verify Apps Script permissions and deployment with a second Google account before public launch.

### Local fallback and independent recovery mirror

Tampermonkey `GM_*` storage remains the **primary, always-on local record**, whether Drive is enabled or not. Recent builds additionally maintain a **best-effort localStorage mirror of puzzle words, Twofers, and custom vocabulary**, limited to approximately 1.8 million JSON characters. Unlike Tampermonkey storage, that mirror is readable by code on the NYT origin and may be removed by clearing website data. It never contains your Drive URL or sync secret, and cannot replace manual Export for guaranteed recovery.

The mirror is refreshed on startup, on persistent player changes, and after successful Drive synchronization (including initial reconciliation). If `localStorage` is unavailable or over quota, LBC retains the previous mirror and continues normally. In **Settings > Sync > Recover Local Backup**, players can explicitly merge the mirror into GM storage and reload. LBC never overwrites the primary history automatically from this mirror.

## What happens on connection and page load?

LBC uses Tampermonkey/GM storage (`GM_getValue`, `GM_setValue`, and `GM_listValues`), not page `localStorage`, for its retained player data.

When Drive is first configured, LBC immediately reconciles local and cloud state. On later page loads, an enabled Drive connection performs one startup Read/merge. After that startup reconciliation, LBC does **not** poll Drive during ordinary play.

Durable local changes such as newly found words, solved Twofers, custom dictionary additions, and portable GUI-state changes mark the cloud state dirty. Those changes are debounced and then pushed to Drive. If nothing changed, automatic sync performs no export work and makes no Drive request.

### Preview namespace caveat

The Preview userscript intentionally has a different Tampermonkey `@namespace` (and a different script name) from the production userscript. Tampermonkey therefore gives Preview and production separate GM-storage scopes. Preview can fully test cloud synchronization for data stored by Preview, but it cannot automatically read the existing production script's historical GM records.

For testing production history in Preview, export from production and import that backup into Preview; imports are merge-safe. Production retains its normal namespace and therefore keeps the existing production GM history when an updated version ships.

## Sync behavior

The normal session model is event-driven:

1. On startup, LBC performs one Drive Read and merges remote state into local storage.
2. The returned cloud revision becomes the expected revision for this browser session.
3. Local durable changes mark the cloud state dirty.
4. A debounced automatic sync sends a **Write only**; it does not re-read Drive first.
5. A successful Write advances the expected revision and clears dirty state.
6. With no further local changes, Drive remains completely idle.

The header button forces a manual reconciliation Read/merge and may Write if the merged state differs. Shift-click it to reconfigure or disconnect the current browser.

### Optimistic concurrency and idempotent Writes

Every cloud envelope has a monotonically increasing revision. Automatic Writes include the revision this session expects. A genuinely different remote state is never blindly overwritten.

Starting with the v1.13.1 bridge/client work, every Write also carries a unique `WriteId` and writer-session ID. The bridge persists the last accepted IDs. Replaying the same `WriteId` is idempotent: the bridge returns the already-committed success without incrementing the revision again.

This specifically protects against an ambiguous network timeout. A browser request can time out even though Apps Script continues running and successfully commits the write afterward. If a Write times out, LBC performs one exceptional verification Read:

- matching `LastWriteId` means the timed-out Write already succeeded;
- with a legacy bridge, an identical remote `StorageSnapshot` also proves the intended state landed;
- an unchanged remote revision means LBC can retry the same `WriteId`; and
- genuinely different remote state becomes a Conflict and waits for manual reconciliation.

The client currently allows up to 60 seconds for a bridge request before invoking this recovery path. Successful syncs log their mode, revision, and duration in the console for diagnostics.

The bridge stores its JSON in compact form rather than pretty-printing it, reducing the bytes DriveApp must rewrite on every push.

## Browse History

Browse History uses the already-reconciled local data during a normal session; opening it does not poll Google Drive. The history viewer presents retained puzzle data in the same LBC-style display used for the live puzzle.

The viewer opens on the most recent retained puzzle before the currently active day when possible. Navigation controls are:

- `<<` first retained puzzle
- `<` previous puzzle
- `>` next puzzle
- `>>` last retained puzzle

History intentionally shows only player-known data. Global word memory can project valid words found on earlier days into later historical puzzles, but it never allows knowledge from a future puzzle to leak backward.

## Merge rules

Monotonic player discoveries are unioned, never replaced:

- Found Words: set union.
- Found Twofers: set union.
- Per-puzzle custom words: set union.
- Custom dictionary: merge by word while preserving honest first-added provenance.
- Puzzle metadata: prefer newer/richer canonical information without removing older non-empty facts.
- Twofer caches: prefer the newer cache version, or the richer cache at the same version.
- Global word history: union word provenance while reusing current-version letter/adjacency signatures.
- Historical word projection: union compatible chronological backfills.

Portable GUI settings use per-setting timestamps, so changing Animation Speed on one device does not cause an unrelated, newer Hints expand/collapse action on another device to overwrite it.

Physical layout values such as panel width are device-local. They remain in manual disaster-recovery exports but are deliberately omitted from Google Drive sync so a laptop cannot rewrite a desktop monitor's preferred dimensions.

## Backup format

Routine Google Drive sync uses a versioned `LetterBoxedCubedBackup` containing the lossless portable `StorageSnapshot`. It deliberately skips rebuilding the heavier normalized `Puzzles` analysis view during every push. Manual Export can still generate the richer analysis/export representation when requested.

The backup is wrapped in a cloud envelope containing a protocol version, monotonically increasing revision, update timestamp, and - on the current bridge - last Write/session IDs. The cloud connection URL and secret are never part of that payload.
