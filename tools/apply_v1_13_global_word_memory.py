from pathlib import Path


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def replace_exact_count(text, old, new, expected, label):
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} matches, found {count}")
    return text.replace(old, new)


def function_span(text, name):
    marker = f"    function {name}("
    start = text.find(marker)
    if start < 0:
        raise RuntimeError(f"function {name}: marker not found")
    brace = text.find("{", start)
    if brace < 0:
        raise RuntimeError(f"function {name}: opening brace not found")

    depth = 1
    i = brace + 1
    state = "code"
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if state == "code":
            if ch == "'":
                state = "single"
            elif ch == '"':
                state = "double"
            elif ch == "`":
                state = "template"
            elif ch == "/" and nxt == "/":
                state = "line_comment"
                i += 1
            elif ch == "/" and nxt == "*":
                state = "block_comment"
                i += 1
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return start, i + 1
        elif state in ("single", "double", "template"):
            if ch == "\\":
                i += 1
            elif (
                (state == "single" and ch == "'") or
                (state == "double" and ch == '"') or
                (state == "template" and ch == "`")
            ):
                state = "code"
        elif state == "line_comment":
            if ch == "\n":
                state = "code"
        elif state == "block_comment":
            if ch == "*" and nxt == "/":
                state = "code"
                i += 1
        i += 1

    raise RuntimeError(f"function {name}: closing brace not found")


def transform_function(text, name, transform):
    start, end = function_span(text, name)
    old = text[start:end]
    new = transform(old)
    if new == old:
        raise RuntimeError(f"function {name}: transform made no change")
    return text[:start] + new + text[end:]


source_path = Path("LetterBoxedCubed.user.js")
source = source_path.read_text(encoding="utf-8")

source = replace_once(
    source,
    "// @version      1.12.3",
    "// @version      1.13.0-beta.1",
    "version bump",
)

source = replace_once(
    source,
    '    const PuzzleMetadataPrefix = "LetterBoxedCubed_PuzzleMetadata_";\n\n',
    '    const PuzzleMetadataPrefix = "LetterBoxedCubed_PuzzleMetadata_";\n'
    '    const GlobalWordHistoryStorageKey = "LetterBoxedCubed_GlobalWordHistory";\n'
    '    const GlobalWordHistoryVersion = 1;\n\n',
    "global word constants",
)

source = replace_once(
    source,
    "        CustomDictionaryStorageKey,\n        HideParStorageKey,",
    "        CustomDictionaryStorageKey,\n        GlobalWordHistoryStorageKey,\n        HideParStorageKey,",
    "global word export key",
)

source = replace_once(
    source,
    "    let FoundWords = new Set();\n    let PuzzleSideByLetter = new Map();",
    "    let FoundWords = new Set();\n"
    "    let GlobalWordHistory = null;\n"
    "    let GlobalWordsByLetterMask = new Map();\n"
    "    let PreviouslyFoundWordsForPuzzle = new Set();\n"
    "    let KnownWordsForPuzzle = new Set();\n"
    "    let PuzzleSideByLetter = new Map();",
    "global word runtime state",
)

source = replace_exact_count(
    source,
    "        LoadFoundWords();\n        LoadCustomDictionary();",
    "        LoadFoundWords();\n        LoadGlobalWordHistory();\n        LoadCustomDictionary();",
    2,
    "load global word history in initialization/reload",
)

module = r'''
    // -------------------------------------------------------------------------
    // Global word history
    // -------------------------------------------------------------------------

    function CreateEmptyGlobalWordHistory() {
        return {
            Version: GlobalWordHistoryVersion,
            IndexedPuzzleIds: [],
            Words: {}
        };
    }

    function NormalizePuzzleIdList(RawIds) {
        /*
            Two distinct puzzle IDs are sufficient to answer the only
            provenance question LBC needs at runtime: "was this word found on
            some puzzle other than the current one?" Keeping at most two IDs
            prevents very common words from growing an unbounded provenance
            list over years of play while remaining merge-safe.
        */
        return [...new Set(
            (Array.isArray(RawIds) ? RawIds : [])
                .map(Value => String(Value || "").trim())
                .filter(Boolean)
        )]
            .sort(Alphabetically)
            .slice(0, 2);
    }

    function BuildWordLetterMask(Word) {
        let Mask = 0;
        for (const Letter of NormalizeWord(Word)) {
            const Bit = Letter.charCodeAt(0) - 65;
            if (Bit >= 0 && Bit < 26) {
                Mask |= (1 << Bit);
            }
        }
        return Mask >>> 0;
    }

    function BuildWordAdjacentPairs(Word) {
        const Normalized = NormalizeWord(Word);
        const Pairs = new Set();

        for (let Index = 0; Index < Normalized.length - 1; Index++) {
            const Left = Normalized[Index];
            const Right = Normalized[Index + 1];
            /* Side separation is symmetric, so AB and BA are one constraint. */
            Pairs.add(Left <= Right ? Left + Right : Right + Left);
        }

        return [...Pairs].sort(Alphabetically);
    }

    function BuildGlobalWordRecord(Word, PuzzleIds = []) {
        const Normalized = NormalizeWord(Word);
        if (Normalized.length < 3) {
            return null;
        }

        return {
            Word: Normalized,
            LetterMask: BuildWordLetterMask(Normalized),
            AdjacentPairs: BuildWordAdjacentPairs(Normalized),
            FirstLetter: Normalized[0],
            LastLetter: Normalized[Normalized.length - 1],
            PuzzleIds: NormalizePuzzleIdList(PuzzleIds)
        };
    }

    function NormalizeGlobalWordHistory(RawHistory) {
        const Result = CreateEmptyGlobalWordHistory();

        if (!RawHistory || typeof RawHistory !== "object" || Array.isArray(RawHistory)) {
            return Result;
        }

        Result.IndexedPuzzleIds = [...new Set(
            (Array.isArray(RawHistory.IndexedPuzzleIds)
                ? RawHistory.IndexedPuzzleIds
                : [])
                .map(Value => String(Value || "").trim())
                .filter(Boolean)
        )].sort(Alphabetically);

        const RawWords =
            RawHistory.Words &&
            typeof RawHistory.Words === "object" &&
            !Array.isArray(RawHistory.Words)
                ? RawHistory.Words
                : {};

        for (const [RawWord, RawRecord] of Object.entries(RawWords)) {
            const Word = NormalizeWord(RawRecord?.Word || RawWord);
            const Record = BuildGlobalWordRecord(
                Word,
                RawRecord?.PuzzleIds
            );
            if (Record) {
                Result.Words[Word] = Record;
            }
        }

        return Result;
    }

    function CanonicalizeGlobalWordHistory(History) {
        const Normalized = NormalizeGlobalWordHistory(History);
        const Words = {};

        for (const Word of Object.keys(Normalized.Words).sort(Alphabetically)) {
            Words[Word] = Normalized.Words[Word];
        }

        return {
            Version: GlobalWordHistoryVersion,
            IndexedPuzzleIds: [...Normalized.IndexedPuzzleIds].sort(Alphabetically),
            Words
        };
    }

    function MergeGlobalWordHistoryValues(LocalValue, IncomingValue) {
        const Local = NormalizeGlobalWordHistory(LocalValue);
        const Incoming = NormalizeGlobalWordHistory(IncomingValue);
        const Result = CreateEmptyGlobalWordHistory();

        Result.IndexedPuzzleIds = [...new Set([
            ...Local.IndexedPuzzleIds,
            ...Incoming.IndexedPuzzleIds
        ])].sort(Alphabetically);

        const Words = new Set([
            ...Object.keys(Local.Words),
            ...Object.keys(Incoming.Words)
        ]);

        for (const Word of [...Words].sort(Alphabetically)) {
            const PuzzleIds = NormalizePuzzleIdList([
                ...(Local.Words[Word]?.PuzzleIds || []),
                ...(Incoming.Words[Word]?.PuzzleIds || [])
            ]);
            const Record = BuildGlobalWordRecord(Word, PuzzleIds);
            if (Record) {
                Result.Words[Word] = Record;
            }
        }

        return CanonicalizeGlobalWordHistory(Result);
    }

    function IngestWordsIntoGlobalWordHistory(History, PuzzleId, Words) {
        const Id = String(PuzzleId || "").trim();
        if (!Id) {
            return false;
        }

        let Changed = false;
        const NormalizedWords = [...new Set(
            (Array.isArray(Words) ? Words : [...(Words || [])])
                .map(NormalizeWord)
                .filter(Word => Word.length >= 3)
        )];

        for (const Word of NormalizedWords) {
            const Existing = History.Words[Word];
            const PuzzleIds = NormalizePuzzleIdList([
                ...(Existing?.PuzzleIds || []),
                Id
            ]);
            const Record = BuildGlobalWordRecord(Word, PuzzleIds);

            if (!Existing || JSON.stringify(Existing) !== JSON.stringify(Record)) {
                History.Words[Word] = Record;
                Changed = true;
            }
        }

        if (!History.IndexedPuzzleIds.includes(Id)) {
            History.IndexedPuzzleIds.push(Id);
            History.IndexedPuzzleIds.sort(Alphabetically);
            Changed = true;
        }

        return Changed;
    }

    function RebuildGlobalWordHistoryFromTrackerStorage() {
        const History = CreateEmptyGlobalWordHistory();
        const Keys = typeof GM_listValues === "function"
            ? GM_listValues()
            : [];

        for (const Key of Keys) {
            if (!Key.startsWith("LetterBoxedTracker_")) {
                continue;
            }

            const PuzzleId = Key.substring("LetterBoxedTracker_".length);
            const Words = GM_getValue(Key, []);
            IngestWordsIntoGlobalWordHistory(History, PuzzleId, Words);
        }

        return CanonicalizeGlobalWordHistory(History);
    }

    function MergeTrackerKeysIntoStoredGlobalWordHistory(Keys) {
        const UniqueKeys = [...new Set(Keys || [])]
            .filter(Key => Key.startsWith("LetterBoxedTracker_"));

        if (UniqueKeys.length === 0) {
            return false;
        }

        const Raw = GM_getValue(GlobalWordHistoryStorageKey, null);
        let History =
            Raw?.Version === GlobalWordHistoryVersion
                ? NormalizeGlobalWordHistory(Raw)
                : RebuildGlobalWordHistoryFromTrackerStorage();
        let Changed = Raw?.Version !== GlobalWordHistoryVersion;

        for (const Key of UniqueKeys) {
            const PuzzleId = Key.substring("LetterBoxedTracker_".length);
            Changed = IngestWordsIntoGlobalWordHistory(
                History,
                PuzzleId,
                GM_getValue(Key, [])
            ) || Changed;
        }

        if (Changed) {
            GM_setValue(
                GlobalWordHistoryStorageKey,
                CanonicalizeGlobalWordHistory(History)
            );
        }

        return Changed;
    }

    function RebuildGlobalWordMaskIndex() {
        GlobalWordsByLetterMask = new Map();

        for (const Record of Object.values(GlobalWordHistory?.Words || {})) {
            const Mask = Number(Record.LetterMask) >>> 0;
            if (!GlobalWordsByLetterMask.has(Mask)) {
                GlobalWordsByLetterMask.set(Mask, []);
            }
            GlobalWordsByLetterMask.get(Mask).push(Record.Word);
        }
    }

    function BuildCurrentPuzzleLetterMask() {
        let Mask = 0;
        for (const Letter of PuzzleSideByLetter.keys()) {
            const Bit = Letter.charCodeAt(0) - 65;
            if (Bit >= 0 && Bit < 26) {
                Mask |= (1 << Bit);
            }
        }
        return Mask >>> 0;
    }

    function IsGlobalWordRecordValidForCurrentPuzzle(Record, PuzzleMask) {
        if (!Record || (Record.LetterMask & PuzzleMask) !== Record.LetterMask) {
            return false;
        }

        for (const Pair of Record.AdjacentPairs || []) {
            const LeftSide = PuzzleSideByLetter.get(Pair[0]);
            const RightSide = PuzzleSideByLetter.get(Pair[1]);
            if (
                LeftSide === undefined ||
                RightSide === undefined ||
                LeftSide === RightSide
            ) {
                return false;
            }
        }

        return true;
    }

    function RefreshKnownWordsForCurrentPuzzle() {
        PreviouslyFoundWordsForPuzzle = new Set();
        const PuzzleMask = BuildCurrentPuzzleLetterMask();

        /*
            A Letter Boxed board has 12 letters, so there are at most 4096
            letter-mask subsets. Looking up only those buckets keeps historical
            lookup effectively constant-time even as lifetime vocabulary grows.
        */
        let Subset = PuzzleMask;
        while (true) {
            for (const Word of GlobalWordsByLetterMask.get(Subset) || []) {
                const Record = GlobalWordHistory.Words[Word];
                const WasFoundElsewhere = (Record?.PuzzleIds || [])
                    .some(Id => Id !== PuzzleStorageId);

                if (
                    WasFoundElsewhere &&
                    IsGlobalWordRecordValidForCurrentPuzzle(Record, PuzzleMask)
                ) {
                    PreviouslyFoundWordsForPuzzle.add(Word);
                }
            }

            if (Subset === 0) {
                break;
            }
            Subset = ((Subset - 1) & PuzzleMask) >>> 0;
        }

        KnownWordsForPuzzle = new Set([
            ...PreviouslyFoundWordsForPuzzle,
            ...FoundWords
        ]);
    }

    function SaveGlobalWordHistory(QueueSync = true) {
        GlobalWordHistory = CanonicalizeGlobalWordHistory(GlobalWordHistory);
        GM_setValue(GlobalWordHistoryStorageKey, GlobalWordHistory);

        if (QueueSync) {
            ScheduleCloudSync();
        }
    }

    function UpdateGlobalWordHistoryFromCurrentPuzzle() {
        if (!GlobalWordHistory) {
            GlobalWordHistory = CreateEmptyGlobalWordHistory();
        }

        const Changed = IngestWordsIntoGlobalWordHistory(
            GlobalWordHistory,
            PuzzleStorageId,
            FoundWords
        );

        if (Changed) {
            SaveGlobalWordHistory(false);
            RebuildGlobalWordMaskIndex();
        }

        RefreshKnownWordsForCurrentPuzzle();
    }

    function LoadGlobalWordHistory() {
        const Raw = GM_getValue(GlobalWordHistoryStorageKey, null);
        let Changed = false;

        if (Raw?.Version === GlobalWordHistoryVersion) {
            GlobalWordHistory = NormalizeGlobalWordHistory(Raw);

            const Indexed = new Set(GlobalWordHistory.IndexedPuzzleIds);
            const Keys = typeof GM_listValues === "function"
                ? GM_listValues()
                : [];

            for (const Key of Keys) {
                if (!Key.startsWith("LetterBoxedTracker_")) {
                    continue;
                }

                const PuzzleId = Key.substring("LetterBoxedTracker_".length);
                if (Indexed.has(PuzzleId)) {
                    continue;
                }

                Changed = IngestWordsIntoGlobalWordHistory(
                    GlobalWordHistory,
                    PuzzleId,
                    GM_getValue(Key, [])
                ) || Changed;
                Indexed.add(PuzzleId);
            }
        } else {
            GlobalWordHistory = RebuildGlobalWordHistoryFromTrackerStorage();
            Changed = true;
        }

        Changed = IngestWordsIntoGlobalWordHistory(
            GlobalWordHistory,
            PuzzleStorageId,
            FoundWords
        ) || Changed;

        if (Changed) {
            SaveGlobalWordHistory(false);
        } else {
            GlobalWordHistory = CanonicalizeGlobalWordHistory(GlobalWordHistory);
        }

        RebuildGlobalWordMaskIndex();
        RefreshKnownWordsForCurrentPuzzle();

        console.log("[Letter Boxed Cubed] Global word memory loaded.", {
            IndexedPuzzles: GlobalWordHistory.IndexedPuzzleIds.length,
            LifetimeWords: Object.keys(GlobalWordHistory.Words).length,
            PreviouslyFoundPlayableToday: PreviouslyFoundWordsForPuzzle.size,
            KnownToday: KnownWordsForPuzzle.size
        });
    }

'''

marker = "    // -------------------------------------------------------------------------\n    // Found words\n    // -------------------------------------------------------------------------\n"
source = replace_once(source, marker, module + marker, "global word module insertion")

source = transform_function(
    source,
    "SaveFoundWords",
    lambda body: replace_once(
        body,
        "        GM_setValue(\n            WordStorageKey,\n            [...FoundWords].sort(Alphabetically)\n        );\n\n        ScheduleCloudSync();",
        "        GM_setValue(\n            WordStorageKey,\n            [...FoundWords].sort(Alphabetically)\n        );\n\n        UpdateGlobalWordHistoryFromCurrentPuzzle();\n        ScheduleCloudSync();",
        "SaveFoundWords global update",
    ),
)

for name in [
    "CalculateTwoferHintStats",
    "GetTwoferCategory",
    "GetTwoferWordVisibility",
]:
    source = transform_function(
        source,
        name,
        lambda body, name=name: body.replace(
            "FoundWords.has(",
            "KnownWordsForPuzzle.has("
        ),
    )


def patch_render_panel(body):
    body = body.replace("FoundWords.has(", "KnownWordsForPuzzle.has(")
    body = replace_once(
        body,
        "        const UnfoundWords =\n",
        "        const KnownWordsForDisplay =\n"
        "            [...KnownWordsForPuzzle]\n"
        "                .sort(Alphabetically);\n\n"
        "        const UnfoundWords =\n",
        "RenderPanel known display insertion",
    )
    body = replace_once(
        body,
        "            FoundDictionaryWords,\n            UnfoundWords\n        );",
        "            KnownWordsForDisplay,\n            UnfoundWords\n        );",
        "RenderPanel found display argument",
    )
    return body


source = transform_function(source, "RenderPanel", patch_render_panel)


def patch_hint_tree(body):
    body = body.replace("FoundWords.has(", "KnownWordsForPuzzle.has(")
    body = replace_once(
        body,
        '                Item.className =\n                    "lb-cubed-potential-word lb-cubed-potential-word-found";\n\n',
        '                Item.className =\n                    "lb-cubed-potential-word lb-cubed-potential-word-found";\n\n'
        '                if (PreviouslyFoundWordsForPuzzle.has(Word)) {\n'
        '                    Item.classList.add("lb-cubed-potential-word-previously-found");\n'
        '                    Item.title = "Previously found on another Letter Boxed puzzle";\n'
        '                }\n\n',
        "hint previous-word styling",
    )
    return body


source = transform_function(source, "CreatePotentialWordHintTree", patch_hint_tree)


def patch_word_tree(body):
    body = replace_once(
        body,
        "                Item.textContent = Word;\n\n                if (Redacted) {",
        "                Item.textContent = Word;\n\n"
        "                if (!Redacted && PreviouslyFoundWordsForPuzzle.has(Word)) {\n"
        "                    Item.classList.add(\"lb-cubed-word-previously-found\");\n"
        "                    Item.title = \"Previously found on another Letter Boxed puzzle\";\n"
        "                }\n\n"
        "                if (Redacted) {",
        "found tree previous-word styling",
    )
    return body


source = transform_function(source, "CreateWordTree", patch_word_tree)


def patch_twofer_word_element(body):
    return replace_once(
        body,
        "        Item.textContent = Word;\n\n        if (!Visible) {",
        "        Item.textContent = Word;\n\n"
        "        if (Visible && PreviouslyFoundWordsForPuzzle.has(Word)) {\n"
        "            Item.classList.add(\"lb-cubed-twofer-word-previously-found\");\n"
        "            Item.title = \"Previously found on another Letter Boxed puzzle\";\n"
        "        }\n\n"
        "        if (!Visible) {",
        "twofer previous-word styling",
    )


source = transform_function(source, "CreateTwoferWordElement", patch_twofer_word_element)

source = transform_function(
    source,
    "MergeStorageValue",
    lambda body: replace_once(
        body,
        '        if (Key.startsWith("LetterBoxedCubed_FoundTwofers_")) {',
        '        if (Key === GlobalWordHistoryStorageKey) {\n'
        '            return MergeGlobalWordHistoryValues(LocalValue, IncomingValue);\n'
        '        }\n\n'
        '        if (Key.startsWith("LetterBoxedCubed_FoundTwofers_")) {',
        "global history merge semantics",
    ),
)


def patch_merge_backup(body):
    body = replace_once(
        body,
        "        let ChangedKeys = 0;\n        let ConsideredKeys = 0;",
        "        let ChangedKeys = 0;\n"
        "        let ConsideredKeys = 0;\n"
        "        const ChangedTrackerKeys = [];",
        "merge backup tracker accumulator",
    )
    body = replace_once(
        body,
        "                ChangedKeys++;\n            }\n        }\n\n        return {",
        "                ChangedKeys++;\n"
        "                if (Key.startsWith(\"LetterBoxedTracker_\")) {\n"
        "                    ChangedTrackerKeys.push(Key);\n"
        "                }\n"
        "            }\n"
        "        }\n\n"
        "        if (MergeTrackerKeysIntoStoredGlobalWordHistory(ChangedTrackerKeys)) {\n"
        "            ChangedKeys++;\n"
        "        }\n\n"
        "        return {",
        "merge backup incremental history index",
    )
    return body


source = transform_function(source, "MergeBackupIntoStorage", patch_merge_backup)

source = replace_once(
    source,
    "            FoundWords: FoundWords.size,\n            FoundTwofers: FoundTwofers.size,",
    "            FoundWords: FoundWords.size,\n"
    "            PreviouslyFoundWordsForPuzzle: PreviouslyFoundWordsForPuzzle.size,\n"
    "            KnownWordsForPuzzle: KnownWordsForPuzzle.size,\n"
    "            LifetimeGlobalWords: Object.keys(GlobalWordHistory?.Words || {}).length,\n"
    "            FoundTwofers: FoundTwofers.size,",
    "initialization global word diagnostics",
)

css_anchor = """            .lb-cubed-found-word {
                background: rgba(255, 255, 255, 0.25);
                color: rgb(42, 20, 20);
            }
"""
css_replacement = css_anchor + """
            .lb-cubed-found-word.lb-cubed-word-previously-found,
            .lb-cubed-potential-word.lb-cubed-potential-word-previously-found,
            .lb-cubed-twofer-word.lb-cubed-twofer-word-previously-found {
                background: rgba(74, 31, 31, 0.16);
            }
"""
source = replace_once(source, css_anchor, css_replacement, "previous word CSS")

source_path.write_text(source, encoding="utf-8")

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

test_path = Path("tests/merge-tests.js")
tests = test_path.read_text(encoding="utf-8")

tests = replace_once(
    tests,
    "      CustomDictionaryStorageKey, CustomWordsPrefix, PuzzleMetadataPrefix\n",
    "      CustomDictionaryStorageKey, CustomWordsPrefix, PuzzleMetadataPrefix,\n"
    "      GlobalWordHistoryStorageKey, GlobalWordHistoryVersion,\n"
    "      BuildGlobalWordRecord, MergeGlobalWordHistoryValues,\n"
    "      RebuildGlobalWordHistoryFromTrackerStorage\n",
    "test exports for global history",
)

new_tests = r'''
test('Global word history merge unions cross-puzzle provenance without duplicating words', () => {
  const local = {
    Version:T.GlobalWordHistoryVersion,
    IndexedPuzzleIds:['100'],
    Words:{ALPHA:T.BuildGlobalWordRecord('ALPHA',['100'])}
  };
  const incoming = {
    Version:T.GlobalWordHistoryVersion,
    IndexedPuzzleIds:['200'],
    Words:{
      ALPHA:T.BuildGlobalWordRecord('ALPHA',['200']),
      BETA:T.BuildGlobalWordRecord('BETA',['200'])
    }
  };
  const merged = T.MergeGlobalWordHistoryValues(local,incoming);
  eq(merged.IndexedPuzzleIds, ['100','200'], 'indexed puzzle IDs should union');
  eq(Object.keys(merged.Words), ['ALPHA','BETA'], 'word keys should union');
  eq(merged.Words.ALPHA.PuzzleIds, ['100','200'], 'same word should retain two-puzzle provenance');
});

test('Legacy tracker records can seed the global word history index', () => {
  put('LetterBoxedTracker_100', ['ALPHA','BETA']);
  put('LetterBoxedTracker_200', ['BETA','GAMMA']);
  const rebuilt = T.RebuildGlobalWordHistoryFromTrackerStorage();
  eq(rebuilt.IndexedPuzzleIds, ['100','200'], 'legacy puzzles were not indexed');
  eq(Object.keys(rebuilt.Words), ['ALPHA','BETA','GAMMA'], 'legacy words were not deduplicated globally');
  eq(rebuilt.Words.BETA.PuzzleIds, ['100','200'], 'cross-puzzle provenance missing');
  assert(Number.isInteger(rebuilt.Words.BETA.LetterMask), 'letter mask was not precomputed');
  assert(Array.isArray(rebuilt.Words.BETA.AdjacentPairs), 'adjacency constraints were not precomputed');
});

test('Cloud payload includes persistent global word history', () => {
  const history = {
    Version:T.GlobalWordHistoryVersion,
    IndexedPuzzleIds:['100'],
    Words:{ALPHA:T.BuildGlobalWordRecord('ALPHA',['100'])}
  };
  put(T.GlobalWordHistoryStorageKey, history);
  const data = T.BuildCloudSyncData();
  assert(T.GlobalWordHistoryStorageKey in data.StorageSnapshot, 'global history omitted from cloud payload');
});

'''

tests = replace_once(
    tests,
    "test('Cloud payload omits device-local panel width', () => {",
    new_tests + "test('Cloud payload omits device-local panel width', () => {",
    "global history tests",
)

test_path.write_text(tests, encoding="utf-8")

# -----------------------------------------------------------------------------
# Changelog / preview testing docs
# -----------------------------------------------------------------------------

changelog_path = Path("CHANGELOG.md")
changelog = changelog_path.read_text(encoding="utf-8")
changelog = replace_once(
    changelog,
    "# Changelog\n\n## 1.12.3",
    """# Changelog

## 1.13.0-beta.1
- Added persistent global word memory for issue #11. Existing `LetterBoxedTracker_*` puzzle histories are indexed once into a versioned global vocabulary; later discoveries update the index incrementally instead of rescanning every prior puzzle on each page load.
- Each lifetime word stores a compact Letter Boxed signature: a 26-bit letter mask plus distinct adjacent-letter constraints. Current-board lookup enumerates at most the 4096 subsets of the board's 12-letter mask, then validates side adjacency, keeping lookup fast as lifetime history grows.
- Previously found words that are playable on the current board now count as known in Found Words, completion/longest statistics, Words by Length, Hints, and partial Twofer discovery, with a subtly darker background and tooltip identifying historical discoveries.
- Historical knowledge never writes current-puzzle `FoundTwofers`. If both halves of a current valid Twofer are already known independently (including entirely from prior puzzles), the existing `Individually Found` spoiler-hidden state and `Valid solution independently found?` indicator apply without auto-solving the pair.
- Global word history is included in backup/Google Drive data and merges by word/provenance union. Imports from older clients that contain changed legacy tracker keys also update the global index incrementally.

## 1.12.3""",
    "changelog v1.13 beta",
)
changelog_path.write_text(changelog, encoding="utf-8")

docs_path = Path("docs/PREVIEW_TESTING.md")
docs = docs_path.read_text(encoding="utf-8")
section = r'''## v1.13 global word memory checks

The `feature/global-word-memory-v1.13.0` preview is the sole-feature v1.13 development branch for issue #11. The current source is `1.13.0-beta.1`.

- On first load, existing `LetterBoxedTracker_*` puzzle histories should seed `LetterBoxedCubed_GlobalWordHistory`; subsequent loads should reuse that index and only ingest tracker puzzle IDs not already marked indexed.
- A word found on a prior puzzle that is structurally playable on today's board should already appear in **Found Words** with a subtly darker background and a `Previously found on another Letter Boxed puzzle` tooltip.
- Historical playable words should count toward **Completion**, **Longest Found**, exact **Words by Length**, and the **First Words / Second Words** Hint counters and lists.
- One historically known half of a valid current Twofer should put that row in **Partially Found** and reveal only the known half. The historically revealed half should use the darker previous-word styling.
- If both halves of a valid current Twofer are known independently, including when both were found entirely on older puzzles, **Valid solution independently found?** should be checked and the pair itself should remain spoiler-hidden in **Individually Found**. It must not be added to the current puzzle's `FoundTwofers` until that exact chain is actually completed today.
- A Twofer genuinely completed today must still move to **Found** normally even when one or both words were already known historically.
- Finding a word for the first time today should keep the existing chartreuse discovery fade; if that same word was also known from an older puzzle, historical styling should remain after the fade completes.
- Export/Drive sync should include the global history record. Merging two devices with different lifetime vocabularies should union words and cross-puzzle provenance rather than choosing one device wholesale.
- Preview-only version/debug controls should still be injected by `tools/build_preview.py`; production source on the feature branch should retain only the inert preview hooks.

'''
docs = replace_once(
    docs,
    "## v1.12 QoL bundle checks\n",
    section + "## v1.12 QoL bundle checks\n",
    "v1.13 preview testing section",
)
docs_path.write_text(docs, encoding="utf-8")
