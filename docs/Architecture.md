# Architecture

## Runtime sources

LBC reads canonical puzzle facts from `unsafeWindow.gameData` and live player state from the rendered Letter Boxed DOM. `ourSolution` is used only for official-solution annotation, not as a general spoiler source.

## Terminology

- **TI:** text-input / accepted-word area.
- **GB:** game-board area.
- **LBC:** Letter Boxed Cubed companion area.

## State distinctions

- `FoundWords`: any NYT-accepted dictionary word observed during play.
- `FoundTwofers`: exact ordered two-word chains actually completed.
- Custom dictionary entries: user-approved vocabulary outside NYT's dictionary, with provenance.

Finding both words independently is not equivalent to solving that Twofer.

## Twofers

Twofers are calculated from NYT's puzzle dictionary and cached per puzzle. Candidate pairs require word 1's last letter to equal word 2's first letter and their combined letter masks to cover all puzzle letters.

## Responsive layout

The outer page treats TI+GB as a left meta-column beside LBC where space permits, then stacks the meta-columns when necessary. Inside LBC, CSS **container queries** respond to LBC's own manually resizable width rather than merely the viewport width.

## Panel-width preference

Drag-time clamping prevents impossible cursor positions from becoming hidden future preferences. Render-time clamping separately ensures a valid saved preference can temporarily shrink when the environment is smaller and return when room becomes available.

## Animation speed

The board is canvas-rendered, so the current Animation Speed mechanism is experimental and may require DevTools Performance telemetry for a more exact hook.

## Backup and merge pipeline

Manual import and cloud synchronization both pass through the same `MergeBackupIntoStorage()` path. This is intentional: transport changes how a backup arrives, not how two histories are reconciled.

Monotonic player discoveries (found words, solved Twofers, per-puzzle custom words) merge by set union. Canonical metadata, derived caches, and GUI preferences use type-specific merge rules described in `DataModel.md`.

## Portable GUI state

GUI preferences are persisted in a versioned `GuiState` object. Each setting and expandable section has its own timestamp so conflict resolution occurs at the smallest meaningful level rather than treating the entire UI as one last-writer-wins blob.

Panel width remains device-local because it describes physical layout rather than semantic player preference.

## Google Drive synchronization

Google Drive transport uses a user-owned Google Apps Script web app. LBC talks to the bridge with `GM_xmlhttpRequest`; the bridge reads/writes a backup JSON file in the user's Drive.

The bridge maintains a monotonically increasing cloud `Revision`. A client reads revision N, merges it locally, and writes with `ExpectedRevision: N`. If another device has already written N+1, the bridge returns a conflict and the client repeats read -> merge -> write. This prevents the classic two-device lost-update race while keeping reconciliation logic inside LBC itself.

The bridge endpoint and high-entropy shared secret are local-only configuration and are never included in backups or cloud payloads.
