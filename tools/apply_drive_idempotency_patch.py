from pathlib import Path


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Userscript
# ---------------------------------------------------------------------------
source_path = Path("LetterBoxedCubed.user.js")
source = source_path.read_text(encoding="utf-8")

source = replace_once(
    source,
    "// @version      1.13.1-beta.1",
    "// @version      1.13.1-beta.2",
    "version bump",
)

source = replace_once(
    source,
    "    const CloudSyncDebounceMs = 2500;\n    const CloudSyncProtocolVersion = 1;\n",
    "    const CloudSyncDebounceMs = 2500;\n    const CloudSyncProtocolVersion = 1;\n    const CloudSyncRequestTimeoutMs = 60000;\n",
    "cloud constants",
)

source = replace_once(
    source,
    "    let CloudSyncSuppressDirty = false;\n    let CloudCachedPayload = null;\n",
    "    let CloudSyncSuppressDirty = false;\n    let CloudSyncSessionId = null;\n    let CloudWriteSequence = 0;\n    let CloudCachedPayload = null;\n",
    "cloud globals",
)

source = replace_once(
    source,
    "        CloudSyncSuppressDirty = false;\n        CloudCachedPayload = null;\n",
    "        CloudSyncSuppressDirty = false;\n        CloudSyncSessionId = CreateCloudOpaqueId(\"session\");\n        CloudWriteSequence = 0;\n        CloudCachedPayload = null;\n",
    "cloud reset",
)

source = replace_once(
    source,
    "                timeout: 30000,",
    "                timeout: CloudSyncRequestTimeoutMs,",
    "bridge timeout",
)

source = replace_once(
    source,
    '''                onerror: () => Reject(\n                    new Error("Could not reach the Google Drive sync bridge.")\n                ),\n                ontimeout: () => Reject(\n                    new Error("Google Drive sync timed out.")\n                )\n''',
    '''                onerror: () => {\n                    const SyncError = new Error(\n                        "Could not reach the Google Drive sync bridge."\n                    );\n                    SyncError.IsCloudTransportError = true;\n                    SyncError.CloudAction = Action;\n                    Reject(SyncError);\n                },\n                ontimeout: () => {\n                    const SyncError = new Error(\n                        "Google Drive sync timed out."\n                    );\n                    SyncError.IsCloudTimeout = true;\n                    SyncError.IsCloudTransportError = true;\n                    SyncError.CloudAction = Action;\n                    Reject(SyncError);\n                }\n''',
    "bridge error metadata",
)

marker = '''    function HasCloudExportableData() {\n        return GetExportStorageKeys().some(\n            Key =>\n                !DeviceLocalStorageKeys.includes(Key) &&\n                GM_getValue(Key, null) !== null\n        );\n    }\n\n'''
helpers = marker + '''    function CreateCloudOpaqueId(Prefix = "id") {\n        let RandomPart = "";\n\n        try {\n            if (\n                typeof crypto !== "undefined" &&\n                typeof crypto.randomUUID === "function"\n            ) {\n                RandomPart = crypto.randomUUID();\n            }\n        } catch {}\n\n        if (!RandomPart) {\n            RandomPart =\n                `${Date.now().toString(36)}-` +\n                `${Math.random().toString(36).slice(2)}-` +\n                `${Math.random().toString(36).slice(2)}`;\n        }\n\n        return `${Prefix}-${RandomPart}`;\n    }\n\n    function CreateCloudWriteId() {\n        CloudWriteSequence++;\n        return [\n            CloudSyncSessionId || CreateCloudOpaqueId("session"),\n            "write",\n            CloudWriteSequence\n        ].join("-");\n    }\n\n    function CloudPayloadStorageMatches(First, Second) {\n        const FirstSnapshot = First?.StorageSnapshot;\n        const SecondSnapshot = Second?.StorageSnapshot;\n\n        if (\n            !FirstSnapshot ||\n            typeof FirstSnapshot !== "object" ||\n            !SecondSnapshot ||\n            typeof SecondSnapshot !== "object"\n        ) {\n            return false;\n        }\n\n        try {\n            return JSON.stringify(FirstSnapshot) ===\n                JSON.stringify(SecondSnapshot);\n        } catch {\n            return false;\n        }\n    }\n\n    function CloudWriteAlreadyApplied(Write, WriteId, LocalData) {\n        if (!Write || typeof Write !== "object") {\n            return false;\n        }\n\n        if (\n            WriteId &&\n            Write.LastWriteId &&\n            Write.LastWriteId === WriteId\n        ) {\n            return true;\n        }\n\n        return CloudPayloadStorageMatches(Write.Data, LocalData);\n    }\n\n    async function WriteGoogleDriveSnapshot(ExpectedRevision, LocalData) {\n        const WriteId = CreateCloudWriteId();\n        const Payload = {\n            ExpectedRevision,\n            WriteId,\n            WriterSessionId: CloudSyncSessionId,\n            Data: LocalData\n        };\n\n        let Write;\n\n        try {\n            Write = await GoogleDriveBridgeRequest("Write", Payload);\n        } catch (Error) {\n            if (!Error?.IsCloudTimeout) {\n                throw Error;\n            }\n\n            console.warn(\n                "[Letter Boxed Cubed] Drive write response timed out; verifying whether the server committed it.",\n                { ExpectedRevision, WriteId }\n            );\n\n            let Remote;\n            try {\n                Remote = await GoogleDriveBridgeRequest("Read");\n            } catch {\n                throw Error;\n            }\n\n            const RemoteRevision = Number(Remote.Revision) || 0;\n\n            if (CloudWriteAlreadyApplied(Remote, WriteId, LocalData)) {\n                console.info(\n                    "[Letter Boxed Cubed] Confirmed the timed-out Drive write had already succeeded.",\n                    { Revision: RemoteRevision, WriteId }\n                );\n                return {\n                    Status: "ok",\n                    Revision: RemoteRevision,\n                    UpdatedAt: Remote.UpdatedAt || null,\n                    LastWriteId: Remote.LastWriteId || WriteId,\n                    RecoveredFromTimeout: true\n                };\n            }\n\n            if (RemoteRevision !== ExpectedRevision) {\n                return {\n                    Status: "conflict",\n                    Revision: RemoteRevision,\n                    UpdatedAt: Remote.UpdatedAt || null,\n                    LastWriteId: Remote.LastWriteId || null,\n                    LastWriterSessionId:\n                        Remote.LastWriterSessionId || null\n                };\n            }\n\n            /*\n                The timed-out request did not commit. Retrying the SAME WriteId\n                is safe with the current bridge; an older bridge is still\n                protected by ExpectedRevision.\n            */\n            Write = await GoogleDriveBridgeRequest("Write", Payload);\n        }\n\n        if (Write.Status !== "conflict") {\n            return Write;\n        }\n\n        /*\n            A response can be lost after Drive commits a write. Verify the\n            resulting state before deciding that a revision mismatch represents\n            a genuinely different writer.\n        */\n        if (\n            WriteId &&\n            Write.LastWriteId &&\n            Write.LastWriteId === WriteId\n        ) {\n            return {\n                ...Write,\n                Status: "ok",\n                RecoveredFromReplay: true\n            };\n        }\n\n        const Remote = await GoogleDriveBridgeRequest("Read");\n        const RemoteRevision = Number(Remote.Revision) || 0;\n\n        if (CloudWriteAlreadyApplied(Remote, WriteId, LocalData)) {\n            console.info(\n                "[Letter Boxed Cubed] Resolved a Drive revision mismatch as this session's already-applied write.",\n                { ExpectedRevision, RemoteRevision, WriteId }\n            );\n            return {\n                Status: "ok",\n                Revision: RemoteRevision,\n                UpdatedAt: Remote.UpdatedAt || null,\n                LastWriteId: Remote.LastWriteId || WriteId,\n                RecoveredFromReplay: true\n            };\n        }\n\n        return {\n            ...Write,\n            Revision: RemoteRevision || (Number(Write.Revision) || 0),\n            LastWriteId: Remote.LastWriteId || Write.LastWriteId || null,\n            LastWriterSessionId:\n                Remote.LastWriterSessionId ||\n                Write.LastWriterSessionId ||\n                null\n        };\n    }\n\n'''
source = replace_once(source, marker, helpers, "cloud write helpers")

source = replace_once(
    source,
    '''            const Write = await GoogleDriveBridgeRequest(\n                "Write",\n                {\n                    ExpectedRevision: RemoteRevision,\n                    Data: LocalData\n                }\n            );\n''',
    '''            const Write = await WriteGoogleDriveSnapshot(\n                RemoteRevision,\n                LocalData\n            );\n''',
    "reconcile write helper",
)

source = replace_once(
    source,
    '''        const Write = await GoogleDriveBridgeRequest(\n            "Write",\n            {\n                ExpectedRevision: CloudExpectedRevision,\n                Data: LocalData\n            }\n        );\n''',
    '''        const Write = await WriteGoogleDriveSnapshot(\n            CloudExpectedRevision,\n            LocalData\n        );\n''',
    "automatic write helper",
)

source = source.replace(
    "Google Drive changed repeatedly during reconciliation. Click Drive: Sync again after the other LBC session is finished.",
    "Drive revision changed repeatedly during reconciliation. Click Drive: Sync again to reconcile the latest state.",
)

source = replace_once(
    source,
    '''            LastCloudSyncError = new Error(\n                `Google Drive changed in another LBC session (remote revision ${CloudSyncConflictRevision}). Click Drive: Sync to reconcile.`\n            );\n\n            console.warn(\n                "[Letter Boxed Cubed] Automatic Drive upload stopped because the remote revision changed.",\n                {\n                    ExpectedRevision: CloudExpectedRevision,\n                    RemoteRevision: CloudSyncConflictRevision\n                }\n            );\n''',
    '''            LastCloudSyncError = new Error(\n                `Drive revision changed since this LBC session last synchronized ` +\n                `(expected ${CloudExpectedRevision}, remote ${CloudSyncConflictRevision}). ` +\n                `Click Drive: Sync to reconcile.`\n            );\n\n            console.warn(\n                "[Letter Boxed Cubed] Automatic Drive upload stopped because the remote revision changed.",\n                {\n                    ExpectedRevision: CloudExpectedRevision,\n                    RemoteRevision: CloudSyncConflictRevision,\n                    LastWriteId: Write.LastWriteId || null,\n                    LastWriterSessionId:\n                        Write.LastWriterSessionId || null\n                }\n            );\n''',
    "conflict wording",
)

source = replace_once(
    source,
    '''        let AllowAutomaticFollowup = false;\n\n        try {\n            AllowAutomaticFollowup = IsReconciliation\n                ? await ReconcileGoogleDrive()\n                : await PushGoogleDriveChanges();\n''',
    '''        let AllowAutomaticFollowup = false;\n        let SyncSucceeded = false;\n        const SyncMode = Initial\n            ? "initial"\n            : (Manual ? "manual" : "automatic");\n        const SyncStartedAt = Date.now();\n\n        try {\n            SyncSucceeded = IsReconciliation\n                ? await ReconcileGoogleDrive()\n                : await PushGoogleDriveChanges();\n            AllowAutomaticFollowup = SyncSucceeded;\n''',
    "sync timing start",
)

source = replace_once(
    source,
    '''        } finally {\n            CloudSyncInFlight = false;\n            UpdateGoogleDriveButton();\n\n            const HadPendingChanges = CloudSyncPending;\n''',
    '''        } finally {\n            CloudSyncInFlight = false;\n            UpdateGoogleDriveButton();\n\n            if (SyncSucceeded) {\n                console.info(\n                    "[Letter Boxed Cubed] Google Drive sync complete.",\n                    {\n                        Mode: SyncMode,\n                        Revision: CloudExpectedRevision,\n                        DurationMs: Date.now() - SyncStartedAt,\n                        Dirty: CloudSyncDirty\n                    }\n                );\n            }\n\n            const HadPendingChanges = CloudSyncPending;\n''',
    "sync success logging",
)

source_path.write_text(source, encoding="utf-8")


# ---------------------------------------------------------------------------
# Apps Script bridge
# ---------------------------------------------------------------------------
bridge_path = Path("integrations/google-drive/Code.gs")
bridge = bridge_path.read_text(encoding="utf-8")

bridge = replace_once(
    bridge,
    '''        Revision: Number(Parsed.Revision) || 0,\n        UpdatedAt: Parsed.UpdatedAt || null,\n        Data: Parsed.Data || null\n''',
    '''        Revision: Number(Parsed.Revision) || 0,\n        UpdatedAt: Parsed.UpdatedAt || null,\n        LastWriteId: Parsed.LastWriteId || null,\n        LastWriterSessionId: Parsed.LastWriterSessionId || null,\n        Data: Parsed.Data || null\n''',
    "bridge read metadata",
)

bridge = replace_once(
    bridge,
    '''        Revision: 0,\n        UpdatedAt: null,\n        Data: Parsed\n''',
    '''        Revision: 0,\n        UpdatedAt: null,\n        LastWriteId: null,\n        LastWriterSessionId: null,\n        Data: Parsed\n''',
    "bridge legacy read metadata",
)

old_write = '''function WriteEnvelope_(Request) {\n  if (!Request.Data || Request.Data.Format !== "LetterBoxedCubedBackup") {\n    throw new Error("Write request did not contain an LBC backup payload.");\n  }\n\n  const Lock = LockService.getScriptLock();\n  Lock.waitLock(15000);\n\n  try {\n    const Current = ReadEnvelope_();\n    const ExpectedRevision = Number(Request.ExpectedRevision) || 0;\n\n    if (ExpectedRevision !== Current.Revision) {\n      return {\n        ProtocolVersion,\n        Status: "conflict",\n        Revision: Current.Revision,\n        UpdatedAt: Current.UpdatedAt || null\n      };\n    }\n\n    const Next = {\n      ProtocolVersion,\n      Revision: Current.Revision + 1,\n      UpdatedAt: new Date().toISOString(),\n      Data: Request.Data\n    };\n\n    const File = GetOrCreateBackupFile_();\n    File.setContent(JSON.stringify(Next, null, 2));\n\n    return {\n      ProtocolVersion,\n      Status: "ok",\n      Revision: Next.Revision,\n      UpdatedAt: Next.UpdatedAt\n    };\n  } finally {\n    Lock.releaseLock();\n  }\n}\n'''

new_write = '''function WriteEnvelope_(Request) {\n  if (!Request.Data || Request.Data.Format !== "LetterBoxedCubedBackup") {\n    throw new Error("Write request did not contain an LBC backup payload.");\n  }\n\n  const Lock = LockService.getScriptLock();\n  Lock.waitLock(15000);\n\n  try {\n    const Current = ReadEnvelope_();\n    const ExpectedRevision = Number(Request.ExpectedRevision) || 0;\n    const WriteId = String(Request.WriteId || "").trim() || null;\n    const WriterSessionId =\n      String(Request.WriterSessionId || "").trim() || null;\n\n    if (WriteId && Current.LastWriteId === WriteId) {\n      console.log(\n        `LBC Drive write replay accepted: ${WriteId} @ revision ${Current.Revision}`\n      );\n      return {\n        ProtocolVersion,\n        Status: "ok",\n        Revision: Current.Revision,\n        UpdatedAt: Current.UpdatedAt || null,\n        LastWriteId: Current.LastWriteId || null,\n        LastWriterSessionId: Current.LastWriterSessionId || null,\n        Replayed: true\n      };\n    }\n\n    if (ExpectedRevision !== Current.Revision) {\n      console.log(\n        `LBC Drive revision conflict: expected ${ExpectedRevision}, current ${Current.Revision}, write ${WriteId || "(legacy)"}`\n      );\n      return {\n        ProtocolVersion,\n        Status: "conflict",\n        Revision: Current.Revision,\n        UpdatedAt: Current.UpdatedAt || null,\n        LastWriteId: Current.LastWriteId || null,\n        LastWriterSessionId: Current.LastWriterSessionId || null\n      };\n    }\n\n    const Next = {\n      ProtocolVersion,\n      Revision: Current.Revision + 1,\n      UpdatedAt: new Date().toISOString(),\n      LastWriteId: WriteId,\n      LastWriterSessionId: WriterSessionId,\n      Data: Request.Data\n    };\n\n    const File = GetOrCreateBackupFile_();\n    File.setContent(JSON.stringify(Next));\n\n    console.log(\n      `LBC Drive write committed: revision ${Next.Revision}, write ${WriteId || "(legacy)"}`\n    );\n\n    return {\n      ProtocolVersion,\n      Status: "ok",\n      Revision: Next.Revision,\n      UpdatedAt: Next.UpdatedAt,\n      LastWriteId: Next.LastWriteId,\n      LastWriterSessionId: Next.LastWriterSessionId\n    };\n  } finally {\n    Lock.releaseLock();\n  }\n}\n'''
bridge = replace_once(bridge, old_write, new_write, "bridge write function")

bridge = replace_once(
    bridge,
    '''    Revision: 0,\n    UpdatedAt: null,\n    Data: null\n''',
    '''    Revision: 0,\n    UpdatedAt: null,\n    LastWriteId: null,\n    LastWriterSessionId: null,\n    Data: null\n''',
    "bridge empty metadata",
)

bridge_path.write_text(bridge, encoding="utf-8")


# ---------------------------------------------------------------------------
# Cloud tests
# ---------------------------------------------------------------------------
tests_path = Path("tests/cloud-sync-tests.js")
tests = tests_path.read_text(encoding="utf-8")

tests = replace_once(
    tests,
    '''    const Response = BridgeHandler(Request);\n    Options.onload({\n      status: 200,\n      responseText: JSON.stringify(Response)\n    });\n''',
    '''    const Response = BridgeHandler(Request);\n\n    if (Response?.__timeout) {\n      Options.ontimeout?.();\n      return;\n    }\n\n    Options.onload({\n      status: 200,\n      responseText: JSON.stringify(Response)\n    });\n''',
    "test timeout mock",
)

old_conflict_test = '''test('automatic revision conflict pauses uploads without polling or overwriting', async () => {\n  put('LetterBoxedTracker_3000', ['ALPHA']);\n  T.SetSession({Ready: true, ExpectedRevision: 7, Dirty: false, Status: 'Synced'});\n  T.MarkCloudSyncDirty();\n\n  BridgeHandler = Request => {\n    assert(Request.Action === 'Write', 'conflicting automatic sync should still be write-only');\n    return {Status: 'conflict', Revision: 8, Data: null};\n  };\n\n  await T.SyncWithGoogleDrive();\n\n  eq(actions(), ['Write'], 'conflict path unexpectedly issued additional cloud requests');\n  const State = T.GetState();\n  assert(State.ExpectedRevision === 7, 'conflict changed the session expected revision');\n  assert(State.ConflictRevision === 8, 'remote conflict revision was not retained');\n  assert(State.Dirty === true, 'conflicting local changes were incorrectly marked clean');\n  assert(State.Status === 'Conflict', 'conflict did not pause automatic sync');\n});\n'''

new_conflict_test = '''test('automatic revision conflict verifies once, then pauses without overwriting', async () => {\n  const key = 'LetterBoxedTracker_3000';\n  put(key, ['ALPHA']);\n  T.SetSession({Ready: true, ExpectedRevision: 7, Dirty: false, Status: 'Synced'});\n  T.MarkCloudSyncDirty();\n\n  BridgeHandler = Request => {\n    if (Request.Action === 'Write') {\n      return {Status: 'conflict', Revision: 8, LastWriteId: 'different-write'};\n    }\n    return {\n      Status: 'ok',\n      Revision: 8,\n      LastWriteId: 'different-write',\n      Data: backup({[key]: ['BETA']})\n    };\n  };\n\n  await T.SyncWithGoogleDrive();\n\n  eq(actions(), ['Write', 'Read'], 'conflict path should verify remote state once');\n  const State = T.GetState();\n  assert(State.ExpectedRevision === 7, 'conflict changed the session expected revision');\n  assert(State.ConflictRevision === 8, 'remote conflict revision was not retained');\n  assert(State.Dirty === true, 'conflicting local changes were incorrectly marked clean');\n  assert(State.Status === 'Conflict', 'conflict did not pause automatic sync');\n});\n'''

tests = replace_once(tests, old_conflict_test, new_conflict_test, "existing conflict test")

extra_tests = '''\ntest('timed-out write is recovered when Read reports the same WriteId', async () => {\n  const key = 'LetterBoxedTracker_3000';\n  put(key, ['ALPHA']);\n  T.SetSession({Ready: true, ExpectedRevision: 20, Dirty: false, Status: 'Synced'});\n  T.MarkCloudSyncDirty();\n\n  let remote = {Revision: 20, Data: backup({[key]: []}), LastWriteId: null};\n  let timedOutWriteId = null;\n\n  BridgeHandler = Request => {\n    if (Request.Action === 'Write') {\n      timedOutWriteId = Request.WriteId;\n      remote = {\n        Revision: 21,\n        Data: structuredClone(Request.Data),\n        LastWriteId: Request.WriteId,\n        LastWriterSessionId: Request.WriterSessionId\n      };\n      return {__timeout: true};\n    }\n    return {Status: 'ok', ...structuredClone(remote)};\n  };\n\n  await T.SyncWithGoogleDrive();\n\n  eq(actions(), ['Write', 'Read'], 'timeout recovery should verify with one Read');\n  assert(Boolean(timedOutWriteId), 'automatic write did not carry an idempotency WriteId');\n  const State = T.GetState();\n  assert(State.ExpectedRevision === 21, 'timeout recovery did not adopt committed revision');\n  assert(State.Dirty === false, 'timeout recovery left already-committed data dirty');\n  assert(State.Status === 'Synced', 'timeout recovery did not finish Synced');\n});\n\ntest('legacy bridge timeout recovery accepts identical remote data without LastWriteId', async () => {\n  const key = 'LetterBoxedTracker_3000';\n  put(key, ['ALPHA']);\n  T.SetSession({Ready: true, ExpectedRevision: 30, Dirty: false, Status: 'Synced'});\n  T.MarkCloudSyncDirty();\n\n  let remote = {Revision: 30, Data: backup({[key]: []})};\n\n  BridgeHandler = Request => {\n    if (Request.Action === 'Write') {\n      remote = {Revision: 31, Data: structuredClone(Request.Data)};\n      return {__timeout: true};\n    }\n    return {Status: 'ok', ...structuredClone(remote)};\n  };\n\n  await T.SyncWithGoogleDrive();\n\n  eq(actions(), ['Write', 'Read'], 'legacy timeout recovery should verify with one Read');\n  const State = T.GetState();\n  assert(State.ExpectedRevision === 31, 'legacy timeout recovery did not adopt committed revision');\n  assert(State.Dirty === false, 'legacy timeout recovery left identical data dirty');\n});\n\ntest('timed-out uncommitted write retries once with the same WriteId', async () => {\n  const key = 'LetterBoxedTracker_3000';\n  put(key, ['ALPHA']);\n  T.SetSession({Ready: true, ExpectedRevision: 40, Dirty: false, Status: 'Synced'});\n  T.MarkCloudSyncDirty();\n\n  const writeIds = [];\n  let writeCount = 0;\n\n  BridgeHandler = Request => {\n    if (Request.Action === 'Read') {\n      return {Status: 'ok', Revision: 40, Data: backup({[key]: [])};\n    }\n    writeCount++;\n    writeIds.push(Request.WriteId);\n    if (writeCount === 1) return {__timeout: true};\n    return {Status: 'ok', Revision: 41, LastWriteId: Request.WriteId};\n  };\n\n  await T.SyncWithGoogleDrive();\n\n  eq(actions(), ['Write', 'Read', 'Write'], 'uncommitted timeout should verify then retry once');\n  assert(writeIds.length === 2 && writeIds[0] === writeIds[1], 'retry did not reuse the same WriteId');\n  const State = T.GetState();\n  assert(State.ExpectedRevision === 41, 'retry success did not adopt revision');\n  assert(State.Dirty === false, 'retry success left data dirty');\n});\n'''

needle = "\n(async () => {\n  const results = [];\n"
if tests.count(needle) != 1:
    raise SystemExit("test insertion marker not unique")
tests = tests.replace(needle, extra_tests + needle, 1)

tests_path.write_text(tests, encoding="utf-8")


# ---------------------------------------------------------------------------
# Docs
# ---------------------------------------------------------------------------
doc_path = Path("docs/DRIVE_SYNC_PERFORMANCE_TESTING.md")
doc = doc_path.read_text(encoding="utf-8")
doc += '''\n\n## beta.2 timeout / idempotency regression tests\n\nA bridge execution can outlive the browser request and still commit successfully. beta.2 therefore:\n\n- raises the client request timeout from 30 to 60 seconds;\n- assigns every Write a unique `WriteId`;\n- retries the same payload with the same ID after an ambiguous timeout;\n- performs one exceptional Read to verify a timeout or revision mismatch;\n- treats matching `LastWriteId` (new bridge) or an identical remote `StorageSnapshot` (legacy bridge) as success;\n- keeps genuinely different remote state in Conflict until manual reconciliation; and\n- logs successful sync mode, revision, and duration for easier diagnosis.\n\nThe Apps Script bridge should be redeployed from the updated `integrations/google-drive/Code.gs`. The new bridge makes `WriteId` retries natively idempotent, exposes last-writer diagnostics, and minifies the Drive JSON to reduce write volume. The browser remains backward-compatible with the old bridge through snapshot verification.\n'''
doc_path.write_text(doc, encoding="utf-8")
