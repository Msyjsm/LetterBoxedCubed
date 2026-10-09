const fs = require('fs');
const vm = require('vm');
const path = require('path');

const sourcePath = path.resolve(__dirname, '..', 'LetterBoxedCubed.user.js');
let source = fs.readFileSync(sourcePath, 'utf8');

source = source.replace(
  /\n    Initialize\(\);\n\}\)\(\);\s*$/,
  `\n    globalThis.__LbcCloudTest = {\n      BuildCloudSyncData, SyncWithGoogleDrive, ScheduleCloudSync,\n      MarkCloudSyncDirty, ResetCloudSyncSessionState,\n      MigrateBackupToCurrent, BuildGlobalWordRecord,\n      MergeGlobalWordHistoryValues, CreateEmptyGuiState,\n      GlobalWordHistoryStorageKey, PanelWidthStorageKey,\n      LegacyPanelWidthStorageKey,\n      SetConfig(Config) { GoogleDriveConfig = Config; },\n      SetSession(State = {}) {\n        CloudSyncSessionReady = Boolean(State.Ready);\n        CloudExpectedRevision = State.ExpectedRevision ?? null;\n        CloudSyncConflictRevision = State.ConflictRevision ?? null;\n        CloudSyncDirty = Boolean(State.Dirty);\n        CloudSyncGeneration = Number(State.Generation) || 0;\n        CloudSyncPending = Boolean(State.Pending);\n        CloudSyncStatus = State.Status || (State.Ready ? 'Synced' : 'Ready');\n        CloudCachedPayload = null;\n        CloudCachedPayloadGeneration = -1;\n      },\n      GetState() {\n        return {\n          Ready: CloudSyncSessionReady,\n          ExpectedRevision: CloudExpectedRevision,\n          ConflictRevision: CloudSyncConflictRevision,\n          Dirty: CloudSyncDirty,\n          Generation: CloudSyncGeneration,\n          Pending: CloudSyncPending,\n          Status: CloudSyncStatus,\n          LastError: LastCloudSyncError?.message || null,\n          TimerActive: Boolean(CloudSyncTimer)\n        };\n      }\n    };\n})();\n`
);

if (!source.includes('globalThis.__LbcCloudTest')) {
  throw new Error('Could not inject cloud-sync test exports.');
}

const Store = new Map();
const Requests = [];
let BridgeHandler = null;

global.window = { addEventListener: () => {} };
global.unsafeWindow = {};
global.document = {
  getElementById: () => null,
  querySelector: () => null,
  querySelectorAll: () => []
};
global.location = { hash: '' };
global.confirm = () => true;
global.alert = () => {};
global.prompt = () => null;
global.GM_getValue = (k, d) => Store.has(k) ? structuredClone(Store.get(k)) : d;
global.GM_setValue = (k, v) => Store.set(k, structuredClone(v));
global.GM_listValues = () => [...Store.keys()];
global.GM_xmlhttpRequest = Options => {
  const Request = JSON.parse(Options.data);
  Requests.push(structuredClone(Request));

  if (!BridgeHandler) {
    throw new Error(`Unexpected bridge request: ${Request.Action}`);
  }

  try {
    const Response = BridgeHandler(Request);

    if (Response?.__timeout) {
      Options.ontimeout?.();
      return;
    }

    Options.onload({
      status: Response?.__status ?? 200,
      responseText: Object.prototype.hasOwnProperty.call(Response || {}, '__raw')
        ? String(Response.__raw)
        : JSON.stringify(Response)
    });
  } catch (Error) {
    Options.onerror?.(Error);
  }
};

vm.runInThisContext(source, { filename: sourcePath });
const T = global.__LbcCloudTest;

const Config = {
  Version: 1,
  Endpoint: 'https://script.google.com/macros/s/test/exec',
  Secret: 'test-secret',
  Enabled: true
};

function put(k, v) { Store.set(k, structuredClone(v)); }
function get(k) { return Store.has(k) ? structuredClone(Store.get(k)) : undefined; }
function assert(cond, msg) { if (!cond) throw new Error(msg); }
function eq(actual, expected, msg) {
  const a = JSON.stringify(actual);
  const e = JSON.stringify(expected);
  if (a !== e) throw new Error(`${msg}\nactual=${a}\nexpected=${e}`);
}
function backup(snapshot, extra = {}) {
  return {
    Format: 'LetterBoxedCubedBackup',
    FormatVersion: 4,
    ExportedAt: '2026-09-28T00:00:00Z',
    CurrentPuzzleId: '3000',
    PuzzleCount: 0,
    Puzzles: [],
    CustomDictionary: [],
    GuiState: T.CreateEmptyGuiState(),
    StorageSnapshot: snapshot,
    ...extra
  };
}
function reset() {
  Store.clear();
  Requests.length = 0;
  BridgeHandler = null;
  T.ResetCloudSyncSessionState();
  T.SetConfig(structuredClone(Config));
}
function actions() { return Requests.map(Request => Request.Action); }

const tests = [];
function test(name, fn) { tests.push([name, fn]); }

test('clean automatic sync does literally no cloud work', async () => {
  T.SetSession({Ready: true, ExpectedRevision: 7, Dirty: false, Status: 'Synced'});
  BridgeHandler = Request => { throw new Error(`unexpected ${Request.Action}`); };

  await T.SyncWithGoogleDrive();

  eq(actions(), [], 'clean automatic sync should not issue Read or Write');
  assert(T.GetState().Dirty === false, 'clean automatic sync became dirty');
});

test('transient Apps Script HTML response retries once with the same idempotent WriteId', async () => {
  const key = 'LetterBoxedTracker_3000';
  put(key, ['ALPHA']);
  T.SetSession({Ready: true, ExpectedRevision: 7, Dirty: false, Status: 'Synced'});
  T.MarkCloudSyncDirty();

  let count = 0;
  BridgeHandler = Request => {
    count++;
    if (count === 1) {
      return {__raw: '<!DOCTYPE html><html><body>temporary Apps Script page</body></html>'};
    }
    return {Status: 'ok', Revision: 8};
  };

  await T.SyncWithGoogleDrive();

  eq(actions(), ['Write', 'Write'], 'HTML response should retry the same Write once');
  assert(Requests[0].WriteId === Requests[1].WriteId, 'HTML retry changed the idempotency WriteId');
  const State = T.GetState();
  assert(State.ExpectedRevision === 8, 'HTML retry did not retain successful revision');
  assert(State.Dirty === false, 'HTML retry left successful data dirty');
  assert(State.Status === 'Synced', 'HTML retry did not finish Synced');
});

test('dirty automatic sync is push-only and increments expected revision', async () => {
  put('LetterBoxedTracker_3000', ['ALPHA']);
  T.SetSession({Ready: true, ExpectedRevision: 7, Dirty: false, Status: 'Synced'});
  T.MarkCloudSyncDirty();

  BridgeHandler = Request => {
    assert(Request.Action === 'Write', 'automatic sync unexpectedly polled Drive');
    assert(Request.ExpectedRevision === 7, 'automatic push used wrong expected revision');
    assert(Request.Data.Puzzles.length === 0, 'cloud payload should not build normalized puzzle views');
    eq(Request.Data.StorageSnapshot['LetterBoxedTracker_3000'], ['ALPHA'], 'tracker missing from cloud snapshot');
    return {Status: 'ok', Revision: 8};
  };

  await T.SyncWithGoogleDrive();

  eq(actions(), ['Write'], 'dirty automatic sync should issue exactly one Write');
  const State = T.GetState();
  assert(State.ExpectedRevision === 8, 'successful push did not retain new revision');
  assert(State.Dirty === false, 'successful push did not clear dirty state');
  assert(State.Status === 'Synced', 'successful push did not return to Synced');
});

test('automatic revision conflict verifies once, then pauses without overwriting', async () => {
  const key = 'LetterBoxedTracker_3000';
  put(key, ['ALPHA']);
  T.SetSession({Ready: true, ExpectedRevision: 7, Dirty: false, Status: 'Synced'});
  T.MarkCloudSyncDirty();

  BridgeHandler = Request => {
    if (Request.Action === 'Write') {
      return {Status: 'conflict', Revision: 8, LastWriteId: 'different-write'};
    }
    return {
      Status: 'ok',
      Revision: 8,
      LastWriteId: 'different-write',
      Data: backup({[key]: ['BETA']})
    };
  };

  await T.SyncWithGoogleDrive();

  eq(actions(), ['Write', 'Read'], 'conflict path should verify remote state once');
  const State = T.GetState();
  assert(State.ExpectedRevision === 7, 'conflict changed the session expected revision');
  assert(State.ConflictRevision === 8, 'remote conflict revision was not retained');
  assert(State.Dirty === true, 'conflicting local changes were incorrectly marked clean');
  assert(State.Status === 'Conflict', 'conflict did not pause automatic sync');
});

test('manual sync reconciles a prior automatic conflict with one Read when states already match', async () => {
  const key = 'LetterBoxedTracker_3000';
  put(key, ['ALPHA']);
  T.SetSession({
    Ready: true,
    ExpectedRevision: 7,
    ConflictRevision: 8,
    Dirty: true,
    Generation: 1,
    Status: 'Conflict'
  });

  BridgeHandler = Request => {
    assert(Request.Action === 'Read', 'manual reconciliation should begin with a Read');
    return {Status: 'ok', Revision: 8, Data: backup({[key]: ['ALPHA']})};
  };

  await T.SyncWithGoogleDrive({Manual: true});

  eq(actions(), ['Read'], 'matching manual reconciliation should not rewrite Drive');
  const State = T.GetState();
  assert(State.ExpectedRevision === 8, 'manual reconcile did not accept remote revision');
  assert(State.ConflictRevision === null, 'manual reconcile did not clear conflict');
  assert(State.Dirty === false, 'matching manual reconcile did not clear dirty state');
  assert(State.Status === 'Synced', 'manual reconcile did not finish Synced');
});

test('initial sync reads once and performs no write when cloud already matches local', async () => {
  const key = 'LetterBoxedTracker_3000';
  put(key, ['ALPHA']);

  BridgeHandler = Request => {
    assert(Request.Action === 'Read', 'matching initial sync should only Read');
    return {Status: 'ok', Revision: 12, Data: backup({[key]: ['ALPHA']})};
  };

  await T.SyncWithGoogleDrive({Initial: true});

  eq(actions(), ['Read'], 'matching initial sync unnecessarily wrote Drive');
  const State = T.GetState();
  assert(State.Ready === true, 'initial sync did not mark session ready');
  assert(State.ExpectedRevision === 12, 'initial sync did not retain cloud revision');
  assert(State.Dirty === false, 'matching initial sync should finish clean');
});

test('initial sync seeds empty Drive exactly once from local data', async () => {
  const key = 'LetterBoxedTracker_3000';
  put(key, ['ALPHA']);

  BridgeHandler = Request => {
    if (Request.Action === 'Read') {
      return {Status: 'ok', Revision: 0, Data: null};
    }
    assert(Request.Action === 'Write', 'expected initial seed Write');
    assert(Request.ExpectedRevision === 0, 'initial seed used wrong expected revision');
    eq(Request.Data.StorageSnapshot[key], ['ALPHA'], 'initial seed omitted local tracker');
    return {Status: 'ok', Revision: 1};
  };

  await T.SyncWithGoogleDrive({Initial: true});

  eq(actions(), ['Read', 'Write'], 'empty Drive should get one Read and one seed Write');
  const State = T.GetState();
  assert(State.ExpectedRevision === 1, 'seed write did not retain revision 1');
  assert(State.Dirty === false, 'seed write should finish clean');
});

test('cloud payload is lossless snapshot-only and excludes device-local widths', async () => {
  put('LetterBoxedTracker_3000', ['ALPHA']);
  put(T.PanelWidthStorageKey, 700);
  put(T.LegacyPanelWidthStorageKey, 800);
  const Data = T.BuildCloudSyncData();

  eq(Data.Puzzles, [], 'cloud payload should skip normalized puzzle construction');
  eq(Data.StorageSnapshot['LetterBoxedTracker_3000'], ['ALPHA'], 'cloud snapshot lost tracker data');
  assert(!(T.PanelWidthStorageKey in Data.StorageSnapshot), 'current panel width leaked to cloud');
  assert(!(T.LegacyPanelWidthStorageKey in Data.StorageSnapshot), 'legacy panel width leaked to cloud');
});

test('current-schema backup migration is a zero-copy fast path', async () => {
  const Current = backup({'LetterBoxedTracker_3000': ['ALPHA']});
  const Migrated = T.MigrateBackupToCurrent(Current);
  assert(Migrated === Current, 'current-schema backup was cloned/migrated unnecessarily');
});

test('current-version global history merge reuses signatures and only unions provenance', async () => {
  const LocalRecord = T.BuildGlobalWordRecord('ALPHA', ['100']);
  const IncomingRecord = T.BuildGlobalWordRecord('ALPHA', ['200']);
  LocalRecord.LetterMask = 123456;
  LocalRecord.AdjacentPairs = ['ZZ'];

  const Merged = T.MergeGlobalWordHistoryValues(
    {Version: 1, IndexedPuzzleIds: ['100'], Words: {ALPHA: LocalRecord}},
    {Version: 1, IndexedPuzzleIds: ['200'], Words: {ALPHA: IncomingRecord}}
  );

  assert(Merged.Words.ALPHA.LetterMask === 123456, 'merge rebuilt current-version letter mask');
  eq(Merged.Words.ALPHA.AdjacentPairs, ['ZZ'], 'merge rebuilt current-version adjacency signature');
  eq(Merged.Words.ALPHA.PuzzleIds, ['100', '200'], 'merge failed to union provenance');
});

test('timed-out write is recovered when Read reports the same WriteId', async () => {
  const key = 'LetterBoxedTracker_3000';
  put(key, ['ALPHA']);
  T.SetSession({Ready: true, ExpectedRevision: 20, Dirty: false, Status: 'Synced'});
  T.MarkCloudSyncDirty();

  let remote = {Revision: 20, Data: backup({[key]: []}), LastWriteId: null};
  let timedOutWriteId = null;

  BridgeHandler = Request => {
    if (Request.Action === 'Write') {
      timedOutWriteId = Request.WriteId;
      remote = {
        Revision: 21,
        Data: structuredClone(Request.Data),
        LastWriteId: Request.WriteId,
        LastWriterSessionId: Request.WriterSessionId
      };
      return {__timeout: true};
    }
    return {Status: 'ok', ...structuredClone(remote)};
  };

  await T.SyncWithGoogleDrive();

  eq(actions(), ['Write', 'Read'], 'timeout recovery should verify with one Read');
  assert(Boolean(timedOutWriteId), 'automatic write did not carry an idempotency WriteId');
  const State = T.GetState();
  assert(State.ExpectedRevision === 21, 'timeout recovery did not adopt committed revision');
  assert(State.Dirty === false, 'timeout recovery left already-committed data dirty');
  assert(State.Status === 'Synced', 'timeout recovery did not finish Synced');
});

test('legacy bridge timeout recovery accepts identical remote data without LastWriteId', async () => {
  const key = 'LetterBoxedTracker_3000';
  put(key, ['ALPHA']);
  T.SetSession({Ready: true, ExpectedRevision: 30, Dirty: false, Status: 'Synced'});
  T.MarkCloudSyncDirty();

  let remote = {Revision: 30, Data: backup({[key]: []})};

  BridgeHandler = Request => {
    if (Request.Action === 'Write') {
      remote = {Revision: 31, Data: structuredClone(Request.Data)};
      return {__timeout: true};
    }
    return {Status: 'ok', ...structuredClone(remote)};
  };

  await T.SyncWithGoogleDrive();

  eq(actions(), ['Write', 'Read'], 'legacy timeout recovery should verify with one Read');
  const State = T.GetState();
  assert(State.ExpectedRevision === 31, 'legacy timeout recovery did not adopt committed revision');
  assert(State.Dirty === false, 'legacy timeout recovery left identical data dirty');
});

test('timed-out uncommitted write retries once with the same WriteId', async () => {
  const key = 'LetterBoxedTracker_3000';
  put(key, ['ALPHA']);
  T.SetSession({Ready: true, ExpectedRevision: 40, Dirty: false, Status: 'Synced'});
  T.MarkCloudSyncDirty();

  const writeIds = [];
  let writeCount = 0;

  BridgeHandler = Request => {
    if (Request.Action === 'Read') {
      return {Status: 'ok', Revision: 40, Data: backup({[key]: []})};
    }
    writeCount++;
    writeIds.push(Request.WriteId);
    if (writeCount === 1) return {__timeout: true};
    return {Status: 'ok', Revision: 41, LastWriteId: Request.WriteId};
  };

  await T.SyncWithGoogleDrive();

  eq(actions(), ['Write', 'Read', 'Write'], 'uncommitted timeout should verify then retry once');
  assert(writeIds.length === 2 && writeIds[0] === writeIds[1], 'retry did not reuse the same WriteId');
  const State = T.GetState();
  assert(State.ExpectedRevision === 41, 'retry success did not adopt revision');
  assert(State.Dirty === false, 'retry success left data dirty');
});

(async () => {
  const results = [];

  for (const [name, fn] of tests) {
    try {
      reset();
      await fn();
      results.push([name, 'PASS']);
    } catch (Error) {
      results.push([name, 'FAIL', Error.stack || String(Error)]);
    }
  }

  for (const [name, status, detail] of results) {
    console.log(`${status}: ${name}`);
    if (detail) console.log(detail);
  }

  if (results.some(Result => Result[1] === 'FAIL')) {
    process.exit(1);
  }

  console.log(`All ${results.length} cloud sync tests passed.`);
})();
