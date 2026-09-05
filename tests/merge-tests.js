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
global.window = { addEventListener: () => {} };
global.unsafeWindow = {};
global.GM_getValue = (k, d) => Store.has(k) ? structuredClone(Store.get(k)) : d;
global.GM_setValue = (k, v) => Store.set(k, structuredClone(v));
global.GM_listValues = () => [...Store.keys()];
global.GM_xmlhttpRequest = () => { throw new Error('not used in tests'); };
global.document = {};
global.location = { hash: '' };
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

test('FoundWords union deduplicates overlap', () => {
  const key = 'LetterBoxedTracker_3001';
  put(key, ['APPLE','PEAR','PLUM']);
  T.MergeBackupIntoStorage(backup({[key]: ['PEAR','KIWI']}));
  eq(get(key), ['APPLE','KIWI','PEAR','PLUM'], 'FoundWords set union');
});

test('FoundTwofers union by normalized pair key', () => {
  const key = 'LetterBoxedCubed_FoundTwofers_3000';
  const separator = '\u001F';
  const first = `ALPHA${separator}APPLE`;
  const second = `APPLE${separator}ELM`;
  put(key, [first]);
  T.MergeBackupIntoStorage(backup({[key]: [first, second]}));
  eq(get(key), [first, second], 'FoundTwofers set union');
});

test('CustomWords union', () => {
  const key = 'LetterBoxedCubed_CustomWords_3000';
  put(key, ['FOO']);
  T.MergeBackupIntoStorage(backup({[key]: ['BAR','FOO']}));
  eq(get(key), ['BAR','FOO'], 'CustomWords set union');
});

test('Custom dictionary merges entries and keeps earliest honest AddedAt', () => {
  const key = T.CustomDictionaryStorageKey;
  put(key, [{Word:'FOO',Provenance:'User',AddedAt:'2026-09-02T12:00:00Z',FirstAddedPuzzleId:'2',FirstAddedPrintDate:'2026-09-02'}]);
  T.MergeBackupIntoStorage(backup({[key]: [
    {Word:'FOO',Provenance:'User',AddedAt:'2026-09-01T12:00:00Z',FirstAddedPuzzleId:'1',FirstAddedPrintDate:'2026-09-01'},
    {Word:'BAR',Provenance:'User',AddedAt:'2026-09-03T12:00:00Z',FirstAddedPuzzleId:'3',FirstAddedPrintDate:'2026-09-03'}
  ]}));
  const merged = get(key);
  assert(merged.length === 2, 'expected two custom dictionary entries');
  const foo = merged.find(x=>x.Word==='FOO');
  assert(foo.AddedAt === '2026-09-01T12:00:00Z', 'earliest AddedAt not retained');
  assert(foo.FirstAddedPuzzleId === '1', 'provenance should follow earliest dated add');
});

test('Puzzle metadata combines richer and newer facts without blanking local', () => {
  const key = T.PuzzleMetadataPrefix+'3000';
  put(key, {Version:1,PuzzleId:'3000',PrintDate:'2026-09-01',Date:'Sep 1',Sides:['ABC'],NytSolution:[],DictionaryCount:100,DictionaryHash:'OLD',LastSeenAt:'2026-09-01T00:00:00Z'});
  const incoming = {Version:1,PuzzleId:'3000',PrintDate:'2026-09-01',Date:null,Sides:[],NytSolution:['ONE','EIGHT'],DictionaryCount:105,DictionaryHash:'NEW',LastSeenAt:'2026-09-02T00:00:00Z'};
  T.MergeBackupIntoStorage(backup({[key]: incoming}));
  const merged = get(key);
  assert(merged.Date === 'Sep 1', 'non-empty local date was blanked');
  eq(merged.NytSolution, ['ONE','EIGHT'], 'richer NYT solution not merged');
  assert(merged.DictionaryCount === 105 && merged.DictionaryHash === 'NEW', 'newer dictionary metadata not preferred');
});

test('GUI state resolves each property independently by UpdatedAt', () => {
  const local = T.CreateEmptyGuiState();
  local.Settings.HidePar = {Value:false,UpdatedAt:'2026-09-02T10:00:00Z'};
  local.Settings.AnimationSpeed = {Value:0.4,UpdatedAt:'2026-09-02T13:00:00Z'};
  local.Sections.Hints = {Open:false,UpdatedAt:'2026-09-02T14:00:00Z'};
  const incoming = T.CreateEmptyGuiState();
  incoming.Settings.HidePar = {Value:true,UpdatedAt:'2026-09-02T12:00:00Z'};
  incoming.Settings.AnimationSpeed = {Value:0.9,UpdatedAt:'2026-09-02T11:00:00Z'};
  incoming.Sections.Hints = {Open:true,UpdatedAt:'2026-09-02T09:00:00Z'};
  const merged = T.MergeGuiStates(local,incoming);
  assert(merged.Settings.HidePar.Value === true, 'newer incoming HidePar should win');
  assert(merged.Settings.AnimationSpeed.Value === 0.4, 'newer local speed should win');
  assert(merged.Sections.Hints.Open === false, 'newer local Hints state should win');
});

test('GUI legacy null timestamp cannot beat real timestamp', () => {
  const local = T.CreateEmptyGuiState();
  local.Settings.HidePar = {Value:true,UpdatedAt:'2026-09-02T12:00:00Z'};
  const incoming = T.CreateEmptyGuiState();
  incoming.Settings.HidePar = {Value:false,UpdatedAt:null};
  assert(T.MergeGuiStates(local,incoming).Settings.HidePar.Value === true, 'null timestamp beat known timestamp');
});

test('v2 -> v3 migration preserves legacy GUI values without fabricating timestamps', () => {
  const old = {
    Format:'LetterBoxedCubedBackup',FormatVersion:2,ExportedAt:'2026-09-01T00:00:00Z',
    CurrentPuzzleId:'3000',PuzzleCount:0,Puzzles:[],CustomDictionary:[],
    StorageSnapshot:{
      [T.HideParStorageKey]: true,
      [T.LineDrawingSpeedStorageKey]: 0.25
    }
  };
  const migrated = T.MigrateBackupToCurrent(old);
  assert(migrated.FormatVersion === 3, 'migration did not reach v3');
  assert(migrated.GuiState.Settings.HidePar.Value === true, 'legacy HidePar not preserved');
  assert(migrated.GuiState.Settings.HidePar.UpdatedAt === null, 'migration fabricated HidePar timestamp');
  assert(migrated.GuiState.Settings.AnimationSpeed.Value === 0.25, 'legacy speed not preserved');
  assert(!Object.prototype.hasOwnProperty.call(migrated.GuiState.Sections, 'Hints'), 'migration fabricated disclosure state');
});

test('Cloud payload omits device-local panel width', () => {
  global.GameData = null;
  put(T.PanelWidthStorageKey, 700);
  put(T.LegacyPanelWidthStorageKey, 800);
  const data = T.BuildCloudSyncData();
  assert(!(T.PanelWidthStorageKey in data.StorageSnapshot), 'current panel width leaked to cloud');
  assert(!(T.LegacyPanelWidthStorageKey in data.StorageSnapshot), 'legacy panel width leaked to cloud');
});

for (const [name,status,detail] of results) {
  console.log(`${status}: ${name}`);
  if (detail) console.log(detail);
}
if (results.some(r=>r[1]==='FAIL')) process.exit(1);
console.log(`All ${results.length} merge tests passed.`);
