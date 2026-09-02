const fs = require('fs');
const vm = require('vm');

const path = require('path');
const sourcePath = path.resolve(__dirname, '..', 'LetterBoxedCubed.user.js');
let source = fs.readFileSync(sourcePath, 'utf8');

source = source.replace(
  /\n    Initialize\(\);\n\}\)\(\);\s*$/,
  `\n    globalThis.__LbcTest = {\n      MergeBackupIntoStorage, MergeStorageValue, MergeGuiStates,\n      MergeCustomDictionaryValues, MergePuzzleMetadataValues,\n      MigrateBackupToCurrent, MigrateBackupV2ToV3,\n      CreateEmptyGuiState, NormalizeGuiState, BuildCloudSyncData,\n      GuiStateStorageKey, PanelWidthStorageKey, LegacyPanelWidthStorageKey,\n      HideParStorageKey, LineDrawingSpeedStorageKey,\n      CustomDictionaryStorageKey, CustomWordsPrefix, PuzzleMetadataPrefix\n    };\n})();\n`
);

const Store = new Map();
global.window = {};
global.unsafeWindow = {};
global.GM_getValue = (k, d) => Store.has(k) ? structuredClone(Store.get(k)) : d;
global.GM_setValue = (k, v) => Store.set(k, structuredClone(v));
global.GM_listValues = () => [...Store.keys()];
global.GM_xmlhttpRequest = () => { throw new Error('not used in tests'); };
global.document = {};
global.location = {};
global.confirm = () => true;
global.alert = () => {};
global.prompt = () => null;

vm.runInThisContext(source, { filename: sourcePath });
const T = global.__LbcTest;

function reset() { Store.clear(); }
function put(k, v) { Store.set(k, structuredClone(v)); }
function get(k) { return Store.has(k) ? structuredClone(Store.get(k)) : undefined; }
function assert(cond, msg) { if (!cond) throw new Error(msg); }
function eq(actual, expected, msg) {
  const a = JSON.stringify(actual); const e = JSON.stringify(expected);
  if (a !== e) throw new Error(`${msg}\nactual=${a}\nexpected=${e}`);
}
function backup(snapshot, extra={}) {
  return {
    Format: 'LetterBoxedCubedBackup', FormatVersion: 3, ExportedAt: '2026-09-02T12:00:00Z',
    CurrentPuzzleId: '3000', PuzzleCount: 0, Puzzles: [], CustomDictionary: [],
    GuiState: T.CreateEmptyGuiState(), StorageSnapshot: snapshot, ...extra
  };
}

const results = [];
function test(name, fn) {
  try { reset(); fn(); results.push([name, 'PASS']); }
  catch (e) { results.push([name, 'FAIL', e.stack || String(e)]); }
}

test('FoundWords union: 10 + 23 disjoint = 33', () => {
  const key = 'LetterBoxedTracker_3000';
  const local = Array.from({length:10}, (_,i)=>`A${String(i).padStart(2,'0')}`);
  const incoming = Array.from({length:23}, (_,i)=>`B${String(i).padStart(2,'0')}`);
  put(key, local);
  T.MergeBackupIntoStorage(backup({[key]: incoming}));
  const merged = get(key);
  assert(merged.length === 33, `expected 33, got ${merged.length}`);
  assert(new Set(merged).size === 33, 'merged words are not unique');
});

test('FoundWords union removes overlap', () => {
  const key = 'LetterBoxedTracker_3000';
  put(key, ['CAT','DOG','EEL']);
  T.MergeBackupIntoStorage(backup({[key]: ['DOG','FOX','CAT']}));
  eq(get(key), ['CAT','DOG','EEL','FOX'], 'word union mismatch');
});

test('FoundTwofers union', () => {
  const key = 'LetterBoxedCubed_FoundTwofers_3000';
  put(key, ['ALPHA\u001FBETA']);
  T.MergeBackupIntoStorage(backup({[key]: ['GAMMA\u001FALPHA','ALPHA\u001FBETA']}));
  eq(get(key), ['ALPHA\u001FBETA','GAMMA\u001FALPHA'], 'twofer union mismatch');
});

test('CustomWords union', () => {
  const key = T.CustomWordsPrefix + '3000';
  put(key, ['LOVEBUG']);
  T.MergeBackupIntoStorage(backup({[key]: ['LOVEBUG','MOTHMAN']}));
  eq(get(key), ['LOVEBUG','MOTHMAN'], 'custom words union mismatch');
});

test('GUI state merges per field/section by timestamp', () => {
  const local = T.CreateEmptyGuiState();
  local.Settings.HidePar = {Value:false, UpdatedAt:'2026-09-02T10:00:00Z'};
  local.Settings.AnimationSpeed = {Value:0.7, UpdatedAt:'2026-09-02T12:00:00Z'};
  local.Sections.Hints = {Open:false, UpdatedAt:'2026-09-02T13:00:00Z'};
  const incoming = T.CreateEmptyGuiState();
  incoming.Settings.HidePar = {Value:true, UpdatedAt:'2026-09-02T11:00:00Z'};
  incoming.Settings.AnimationSpeed = {Value:0.2, UpdatedAt:'2026-09-02T11:30:00Z'};
  incoming.Sections.Hints = {Open:true, UpdatedAt:'2026-09-02T12:30:00Z'};
  incoming.Sections.Twofers = {Open:true, UpdatedAt:'2026-09-02T14:00:00Z'};
  const merged = T.MergeGuiStates(local, incoming);
  assert(merged.Settings.HidePar.Value === true, 'newer incoming HidePar should win');
  assert(merged.Settings.AnimationSpeed.Value === 0.7, 'newer local AnimationSpeed should win');
  assert(merged.Sections.Hints.Open === false, 'newer local Hints should win');
  assert(merged.Sections.Twofers.Open === true, 'incoming-only Twofers should survive');
});

test('GUI unknown timestamps prefer local', () => {
  const local = T.CreateEmptyGuiState();
  const incoming = T.CreateEmptyGuiState();
  local.Settings.HidePar = {Value:false, UpdatedAt:null};
  incoming.Settings.HidePar = {Value:true, UpdatedAt:null};
  const merged = T.MergeGuiStates(local, incoming);
  assert(merged.Settings.HidePar.Value === false, 'local unknown-time preference should win');
});

test('Custom dictionary unknown AddedAt remains unknown when merged with known', () => {
  const merged = T.MergeCustomDictionaryValues(
    [{Word:'LOVEBUG', Provenance:'User', AddedAt:null, FirstAddedPuzzleId:null, FirstAddedPrintDate:null}],
    [{Word:'LOVEBUG', Provenance:'User', AddedAt:'2026-09-02T12:00:00Z', FirstAddedPuzzleId:'3000', FirstAddedPrintDate:'2026-09-02'}]
  );
  assert(merged.length === 1, 'expected one custom word');
  assert(merged[0].AddedAt === null, 'unknown first timestamp must stay null');
  assert(merged[0].FirstAddedPuzzleId === null, 'unknown first puzzle must stay null');
});

test('Puzzle metadata takes newer record but enriches missing canonical fields', () => {
  const local = {Version:1, PuzzleId:'3000', PrintDate:'2026-09-01', Sides:['ABC'], NytSolution:['A','B'], LastSeenAt:'2026-09-02T12:00:00Z'};
  const incoming = {Version:2, PuzzleId:'3000', PrintDate:'2026-09-01', Sides:[], NytSolution:[], DictionaryCount:2222, LastSeenAt:'2026-09-02T13:00:00Z'};
  const merged = T.MergePuzzleMetadataValues(local, incoming);
  assert(merged.Version === 2, 'metadata version should max');
  eq(merged.Sides, ['ABC'], 'missing newer Sides should be enriched from older');
  eq(merged.NytSolution, ['A','B'], 'missing newer NYT solution should be enriched from older');
  assert(merged.DictionaryCount === 2222, 'newer dictionary count should survive');
});

test('Device-local panel width is not overwritten by import', () => {
  put(T.PanelWidthStorageKey, 500);
  T.MergeBackupIntoStorage(backup({[T.PanelWidthStorageKey]: 340}));
  assert(get(T.PanelWidthStorageKey) === 500, 'local panel width should remain 500');
});

test('v2 -> v3 migration preserves known legacy GUI values without invented timestamps', () => {
  const v2 = {
    Format:'LetterBoxedCubedBackup', FormatVersion:2, Puzzles:[], CustomDictionary:[],
    StorageSnapshot:{[T.HideParStorageKey]:true, [T.LineDrawingSpeedStorageKey]:0.4}
  };
  const v3 = T.MigrateBackupToCurrent(v2);
  assert(v3.FormatVersion === 3, 'schema should migrate to v3');
  assert(v3.GuiState.Settings.HidePar.Value === true, 'HidePar should migrate');
  assert(v3.GuiState.Settings.HidePar.UpdatedAt === null, 'HidePar timestamp should remain unknown');
  assert(v3.GuiState.Settings.AnimationSpeed.Value === 0.4, 'speed should migrate');
  assert(Object.keys(v3.GuiState.Sections).length === 0, 'must not fabricate historical tree states');
});

for (const row of results) {
  console.log(row[1], '-', row[0]);
  if (row[1] === 'FAIL') console.log(row[2]);
}
const failed = results.filter(r => r[1] === 'FAIL').length;
console.log(`\n${results.length - failed}/${results.length} tests passed`);
process.exitCode = failed ? 1 : 0;
