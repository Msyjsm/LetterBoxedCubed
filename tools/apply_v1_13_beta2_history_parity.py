from pathlib import Path


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def replace_count(text, old, new, expected, label):
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} matches, found {count}")
    return text.replace(old, new)


source_path = Path("LetterBoxedCubed.user.js")
source = source_path.read_text(encoding="utf-8")

source = replace_once(
    source,
    "// @version      1.13.0-beta.1",
    "// @version      1.13.0-beta.2",
    "version bump",
)

source = replace_once(
    source,
    '    const GlobalWordHistoryStorageKey = "LetterBoxedCubed_GlobalWordHistory";\n    const GlobalWordHistoryVersion = 1;\n',
    '    const GlobalWordHistoryStorageKey = "LetterBoxedCubed_GlobalWordHistory";\n'
    '    const GlobalWordHistoryVersion = 1;\n'
    '    const HistoricalWordProjectionStorageKey =\n'
    '        "LetterBoxedCubed_HistoricalWordProjection";\n'
    '    const HistoricalWordProjectionVersion = 1;\n',
    "historical projection constants",
)

source = replace_once(
    source,
    '        CustomDictionaryStorageKey,\n        GlobalWordHistoryStorageKey,\n        HideParStorageKey,\n',
    '        CustomDictionaryStorageKey,\n        GlobalWordHistoryStorageKey,\n'
    '        HistoricalWordProjectionStorageKey,\n        HideParStorageKey,\n',
    "export historical projection",
)

source = replace_once(
    source,
    '    let FoundWords = new Set();\n    let GlobalWordHistory = null;\n    let GlobalWordsByLetterMask = new Map();\n',
    '    let FoundWords = new Set();\n    let GlobalWordHistory = null;\n'
    '    let HistoricalWordProjection = null;\n    let GlobalWordsByLetterMask = new Map();\n',
    "historical projection state",
)

source = replace_count(
    source,
    '        LoadGlobalWordHistory();\n        LoadCustomDictionary();\n',
    '        LoadGlobalWordHistory();\n        RefreshHistoricalWordProjectionFromStorage();\n'
    '        LoadCustomDictionary();\n',
    2,
    "initialize and reload projection refresh",
)

found_words_block = '''        const FoundWordsForPuzzle = Array.isArray(
            StorageSnapshot[WordKey]
        )
            ? [...StorageSnapshot[WordKey]]
                .map(NormalizeWord)
                .filter(Boolean)
                .sort(Alphabetically)
            : [];
'''

found_words_replacement = found_words_block + '''
        const HistoricalProjection = NormalizeHistoricalWordProjection(
            StorageSnapshot[HistoricalWordProjectionStorageKey]
        );
        const HistoricalProjectionEntry =
            HistoricalProjection.Puzzles[PuzzleId] || null;
        const ProjectedPreviousWords =
            HistoricalProjectionEntry?.PreviouslyFoundWords || [];
        const ProjectedKnownWords = [...new Set([
            ...FoundWordsForPuzzle,
            ...ProjectedPreviousWords
        ])].sort(Alphabetically);
'''

source = replace_once(
    source,
    found_words_block,
    found_words_replacement,
    "puzzle export projection lookup",
)

source = replace_once(
    source,
    '''            FoundWords: FoundWordsForPuzzle,
            FoundTwofers: FoundTwofersForPuzzle,
''',
    '''            FoundWords: FoundWordsForPuzzle,
            PreviouslyFoundWords: IsCurrentPuzzle
                ? [...PreviouslyFoundWordsForPuzzle].sort(Alphabetically)
                : [...ProjectedPreviousWords],
            KnownWords: IsCurrentPuzzle
                ? [...KnownWordsForPuzzle].sort(Alphabetically)
                : ProjectedKnownWords,
            PreviousWordOrigins:
                HistoricalProjectionEntry?.Origins || {},
            FoundTwofers: FoundTwofersForPuzzle,
''',
    "normalized puzzle export known words",
)

source = replace_once(
    source,
    '''        if (Key === GlobalWordHistoryStorageKey) {
            return MergeGlobalWordHistoryValues(LocalValue, IncomingValue);
        }

        if (Key.startsWith("LetterBoxedCubed_FoundTwofers_")) {
''',
    '''        if (Key === GlobalWordHistoryStorageKey) {
            return MergeGlobalWordHistoryValues(LocalValue, IncomingValue);
        }

        if (Key === HistoricalWordProjectionStorageKey) {
            return MergeHistoricalWordProjectionValues(
                LocalValue,
                IncomingValue
            );
        }

        if (Key.startsWith("LetterBoxedCubed_FoundTwofers_")) {
''',
    "projection merge dispatch",
)

historical_helpers = r'''
    // -------------------------------------------------------------------------
    // Historical known-word projection
    // -------------------------------------------------------------------------

    function CreateEmptyHistoricalWordProjection() {
        return {
            Version: HistoricalWordProjectionVersion,
            Puzzles: {}
        };
    }

    function NormalizeHistoricalWordProjection(RawProjection) {
        const Result = CreateEmptyHistoricalWordProjection();

        if (
            !RawProjection ||
            typeof RawProjection !== "object" ||
            Array.isArray(RawProjection)
        ) {
            return Result;
        }

        const RawPuzzles =
            RawProjection.Puzzles &&
            typeof RawProjection.Puzzles === "object" &&
            !Array.isArray(RawProjection.Puzzles)
                ? RawProjection.Puzzles
                : {};

        for (const [RawPuzzleId, RawEntry] of Object.entries(RawPuzzles)) {
            const PuzzleId = String(RawPuzzleId || "").trim();
            if (!PuzzleId) {
                continue;
            }

            const PreviousWords = [...new Set(
                (Array.isArray(RawEntry?.PreviouslyFoundWords)
                    ? RawEntry.PreviouslyFoundWords
                    : [])
                    .map(NormalizeWord)
                    .filter(Boolean)
            )].sort(Alphabetically);

            const RawOrigins =
                RawEntry?.Origins &&
                typeof RawEntry.Origins === "object" &&
                !Array.isArray(RawEntry.Origins)
                    ? RawEntry.Origins
                    : {};
            const Origins = {};

            for (const Word of PreviousWords) {
                const RawOrigin = RawOrigins[Word];
                Origins[Word] = {
                    PuzzleId:
                        String(RawOrigin?.PuzzleId || "").trim() || null,
                    PrintDate: RawOrigin?.PrintDate || null,
                    Date: RawOrigin?.Date || null
                };
            }

            Result.Puzzles[PuzzleId] = {
                PreviouslyFoundWords: PreviousWords,
                Origins
            };
        }

        return Result;
    }

    function CanonicalizeHistoricalWordProjection(Projection) {
        const Normalized = NormalizeHistoricalWordProjection(Projection);
        const Puzzles = {};

        for (const PuzzleId of Object.keys(Normalized.Puzzles).sort(Alphabetically)) {
            const Entry = Normalized.Puzzles[PuzzleId];
            const Origins = {};

            for (const Word of Entry.PreviouslyFoundWords) {
                Origins[Word] = Entry.Origins[Word] || {
                    PuzzleId: null,
                    PrintDate: null,
                    Date: null
                };
            }

            Puzzles[PuzzleId] = {
                PreviouslyFoundWords: [...Entry.PreviouslyFoundWords],
                Origins
            };
        }

        return {
            Version: HistoricalWordProjectionVersion,
            Puzzles
        };
    }

    function CompareHistoricalOrigins(A, B) {
        const PuzzleA = {
            PuzzleId: A?.PuzzleId || "",
            PrintDate: A?.PrintDate || null
        };
        const PuzzleB = {
            PuzzleId: B?.PuzzleId || "",
            PrintDate: B?.PrintDate || null
        };
        return CompareHistoryPuzzles(PuzzleA, PuzzleB);
    }

    function MergeHistoricalWordProjectionValues(LocalValue, IncomingValue) {
        const Local = NormalizeHistoricalWordProjection(LocalValue);
        const Incoming = NormalizeHistoricalWordProjection(IncomingValue);
        const Result = CreateEmptyHistoricalWordProjection();
        const PuzzleIds = new Set([
            ...Object.keys(Local.Puzzles),
            ...Object.keys(Incoming.Puzzles)
        ]);

        for (const PuzzleId of PuzzleIds) {
            const LocalEntry = Local.Puzzles[PuzzleId];
            const IncomingEntry = Incoming.Puzzles[PuzzleId];
            const PreviousWords = [...new Set([
                ...(LocalEntry?.PreviouslyFoundWords || []),
                ...(IncomingEntry?.PreviouslyFoundWords || [])
            ])].sort(Alphabetically);
            const Origins = {};

            for (const Word of PreviousWords) {
                const LocalOrigin = LocalEntry?.Origins?.[Word] || null;
                const IncomingOrigin = IncomingEntry?.Origins?.[Word] || null;

                if (!LocalOrigin) {
                    Origins[Word] = IncomingOrigin || {
                        PuzzleId: null,
                        PrintDate: null,
                        Date: null
                    };
                } else if (!IncomingOrigin) {
                    Origins[Word] = LocalOrigin;
                } else {
                    Origins[Word] =
                        CompareHistoricalOrigins(LocalOrigin, IncomingOrigin) <= 0
                            ? LocalOrigin
                            : IncomingOrigin;
                }
            }

            Result.Puzzles[PuzzleId] = {
                PreviouslyFoundWords: PreviousWords,
                Origins
            };
        }

        return CanonicalizeHistoricalWordProjection(Result);
    }

    function BuildSideMapFromSides(Sides) {
        const SideByLetter = new Map();

        for (let SideIndex = 0; SideIndex < (Array.isArray(Sides) ? Sides.length : 0); SideIndex++) {
            for (const Letter of String(Sides[SideIndex] || "").toUpperCase()) {
                SideByLetter.set(Letter, SideIndex);
            }
        }

        return SideByLetter;
    }

    function BuildLetterMaskFromSideMap(SideByLetter) {
        let Mask = 0;

        for (const Letter of SideByLetter.keys()) {
            const Bit = Letter.charCodeAt(0) - 65;
            if (Bit >= 0 && Bit < 26) {
                Mask |= (1 << Bit);
            }
        }

        return Mask >>> 0;
    }

    function IsGlobalWordRecordValidForSideMap(
        Record,
        PuzzleMask,
        SideByLetter
    ) {
        if (!Record || (Record.LetterMask & PuzzleMask) !== Record.LetterMask) {
            return false;
        }

        for (const Pair of Record.AdjacentPairs || []) {
            const LeftSide = SideByLetter.get(Pair[0]);
            const RightSide = SideByLetter.get(Pair[1]);

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

    function BuildHistoricalWordProjection(Puzzles) {
        const Result = CreateEmptyHistoricalWordProjection();
        const PriorRecordsByMask = new Map();
        const SeenWords = new Set();
        const SortedPuzzles = (
            Array.isArray(Puzzles) ? Puzzles : []
        )
            .filter(
                Puzzle =>
                    Puzzle &&
                    typeof Puzzle === "object" &&
                    !Array.isArray(Puzzle)
            )
            .map(Puzzle => structuredClone(Puzzle))
            .sort(CompareHistoryPuzzles);

        for (const Puzzle of SortedPuzzles) {
            const PuzzleId = String(Puzzle?.PuzzleId || "").trim();
            if (!PuzzleId) {
                continue;
            }

            const SideByLetter = BuildSideMapFromSides(Puzzle?.Sides);
            const PuzzleMask = BuildLetterMaskFromSideMap(SideByLetter);
            const PreviousWords = new Set();
            const Origins = {};

            if (SideByLetter.size > 0) {
                let Subset = PuzzleMask;

                while (true) {
                    for (const Item of PriorRecordsByMask.get(Subset) || []) {
                        if (
                            IsGlobalWordRecordValidForSideMap(
                                Item.Record,
                                PuzzleMask,
                                SideByLetter
                            )
                        ) {
                            PreviousWords.add(Item.Record.Word);
                            Origins[Item.Record.Word] = structuredClone(Item.Origin);
                        }
                    }

                    if (Subset === 0) {
                        break;
                    }
                    Subset = ((Subset - 1) & PuzzleMask) >>> 0;
                }
            }

            Result.Puzzles[PuzzleId] = {
                PreviouslyFoundWords: [...PreviousWords].sort(Alphabetically),
                Origins
            };

            const ActualFoundWords = [...new Set(
                (Array.isArray(Puzzle?.FoundWords) ? Puzzle.FoundWords : [])
                    .map(NormalizeWord)
                    .filter(Word => Word.length >= 3)
            )];

            for (const Word of ActualFoundWords) {
                if (SeenWords.has(Word)) {
                    continue;
                }

                const Record = BuildGlobalWordRecord(Word, [PuzzleId]);
                if (!Record) {
                    continue;
                }

                const Mask = Number(Record.LetterMask) >>> 0;
                if (!PriorRecordsByMask.has(Mask)) {
                    PriorRecordsByMask.set(Mask, []);
                }

                PriorRecordsByMask.get(Mask).push({
                    Record,
                    Origin: {
                        PuzzleId,
                        PrintDate: Puzzle?.PrintDate || null,
                        Date: Puzzle?.Date || null
                    }
                });
                SeenWords.add(Word);
            }
        }

        return CanonicalizeHistoricalWordProjection(Result);
    }

    function SaveHistoricalWordProjection(Projection, QueueSync = false) {
        const Canonical = CanonicalizeHistoricalWordProjection(Projection);
        const Existing = NormalizeHistoricalWordProjection(
            GM_getValue(HistoricalWordProjectionStorageKey, null)
        );

        HistoricalWordProjection = Canonical;

        if (ValuesEqual(Canonical, CanonicalizeHistoricalWordProjection(Existing))) {
            return false;
        }

        GM_setValue(HistoricalWordProjectionStorageKey, Canonical);

        if (QueueSync) {
            ScheduleCloudSync();
        }

        return true;
    }

    function RefreshHistoricalWordProjectionFromStorage() {
        const Snapshot = BuildExportData();
        SaveHistoricalWordProjection(
            BuildHistoricalWordProjection(Snapshot.Puzzles),
            false
        );
    }

    function PrepareHistoryPuzzles(Puzzles, QueueProjectionSync = true) {
        let Prepared = (Array.isArray(Puzzles) ? Puzzles : [])
            .filter(
                Puzzle =>
                    Puzzle &&
                    typeof Puzzle === "object" &&
                    !Array.isArray(Puzzle)
            )
            .map(Puzzle => structuredClone(Puzzle));

        /*
            Browse History is cloud-backed, but today's local runtime can be a
            few seconds ahead of the last Drive write. Overlay the live local
            export for the current puzzle before deriving the retroactive view.
        */
        const LocalCurrent = BuildExportData().Puzzles.find(
            Puzzle =>
                String(Puzzle?.PuzzleId || "") ===
                String(PuzzleStorageId || "")
        );

        if (LocalCurrent) {
            const RemoteCurrentIndex = Prepared.findIndex(
                Puzzle =>
                    String(Puzzle?.PuzzleId || "") ===
                    String(PuzzleStorageId || "")
            );

            if (RemoteCurrentIndex >= 0) {
                Prepared[RemoteCurrentIndex] = structuredClone(LocalCurrent);
            } else {
                Prepared.push(structuredClone(LocalCurrent));
            }
        }

        Prepared.sort(CompareHistoryPuzzles);

        /*
            Reprocess the complete retained history chronologically. A day's
            inherited words are calculated BEFORE that day's newly found words
            are added to the running vocabulary, so future discoveries can
            never leak backward into older puzzles.
        */
        const Projection = BuildHistoricalWordProjection(Prepared);
        SaveHistoricalWordProjection(Projection, QueueProjectionSync);

        for (const Puzzle of Prepared) {
            const PuzzleId = String(Puzzle?.PuzzleId || "");
            const Entry = Projection.Puzzles[PuzzleId] || {
                PreviouslyFoundWords: [],
                Origins: {}
            };
            const ActualFoundWords = [...new Set(
                (Array.isArray(Puzzle?.FoundWords) ? Puzzle.FoundWords : [])
                    .map(NormalizeWord)
                    .filter(Boolean)
            )].sort(Alphabetically);

            Puzzle.PreviouslyFoundWords = [...Entry.PreviouslyFoundWords];
            Puzzle.KnownWords = [...new Set([
                ...ActualFoundWords,
                ...Entry.PreviouslyFoundWords
            ])].sort(Alphabetically);
            Puzzle.PreviousWordOrigins = structuredClone(Entry.Origins);
        }

        const CurrentPuzzle = Prepared.find(
            Puzzle =>
                String(Puzzle?.PuzzleId || "") ===
                String(PuzzleStorageId || "")
        );

        if (CurrentPuzzle) {
            const DerivedKnown = [...new Set(
                CurrentPuzzle.KnownWords || []
            )].sort(Alphabetically);
            const LiveKnown = [...KnownWordsForPuzzle].sort(Alphabetically);
            const DerivedPrevious = [...new Set(
                CurrentPuzzle.PreviouslyFoundWords || []
            )].sort(Alphabetically);
            const LivePrevious = [...PreviouslyFoundWordsForPuzzle]
                .sort(Alphabetically);

            if (
                !ValuesEqual(DerivedKnown, LiveKnown) ||
                !ValuesEqual(DerivedPrevious, LivePrevious)
            ) {
                console.warn(
                    "[Letter Boxed Cubed] Browse History current-day sanity check differed from the live panel; using live values.",
                    {
                        DerivedKnown,
                        LiveKnown,
                        DerivedPrevious,
                        LivePrevious
                    }
                );
            }

            /*
                This is the final parity guarantee: today's Browse History card
                uses the exact same known/previous sets as the live LBC panel.
            */
            CurrentPuzzle.KnownWords = LiveKnown;
            CurrentPuzzle.PreviouslyFoundWords = LivePrevious;
        }

        return Prepared;
    }

    function ShouldHighlightWordDiscovery(
        Word,
        PreviousWords = PreviouslyFoundWordsForPuzzle
    ) {
        return !PreviousWords.has(NormalizeWord(Word));
    }
'''

source = replace_once(
    source,
    '''    // -------------------------------------------------------------------------
    // Found words
    // -------------------------------------------------------------------------
''',
    historical_helpers + '''

    // -------------------------------------------------------------------------
    // Found words
    // -------------------------------------------------------------------------
''',
    "historical projection helper insertion",
)

# OpenCloudHistoryBrowser: let us rewrite/overlay/enrich the cloud puzzle list.
source = replace_once(
    source,
    '''            const Puzzles = (
                Array.isArray(Backup.Puzzles)
                    ? Backup.Puzzles
                    : []
            )
                .filter(
                    Puzzle =>
                        Puzzle &&
                        typeof Puzzle === "object" &&
                        !Array.isArray(Puzzle)
                )
                .map(Puzzle => structuredClone(Puzzle))
                .sort(CompareHistoryPuzzles);
''',
    '''            let Puzzles = (
                Array.isArray(Backup.Puzzles)
                    ? Backup.Puzzles
                    : []
            )
                .filter(
                    Puzzle =>
                        Puzzle &&
                        typeof Puzzle === "object" &&
                        !Array.isArray(Puzzle)
                )
                .map(Puzzle => structuredClone(Puzzle))
                .sort(CompareHistoryPuzzles);

            Puzzles = PrepareHistoryPuzzles(Puzzles, true);
''',
    "prepare cloud history puzzles",
)

# Render history from the same Known/Previous model as the live panel.
source = replace_once(
    source,
    '''        const FoundWordsForPuzzle =
            [...new Set(
                Array.isArray(Puzzle?.FoundWords)
                    ? Puzzle.FoundWords
                        .map(NormalizeWord)
                        .filter(Boolean)
                    : []
            )].sort(Alphabetically);
''',
    '''        const ActualFoundWordsForPuzzle =
            [...new Set(
                Array.isArray(Puzzle?.FoundWords)
                    ? Puzzle.FoundWords
                        .map(NormalizeWord)
                        .filter(Boolean)
                    : []
            )].sort(Alphabetically);

        const PreviouslyFoundWordsForHistory =
            new Set(
                Array.isArray(Puzzle?.PreviouslyFoundWords)
                    ? Puzzle.PreviouslyFoundWords
                        .map(NormalizeWord)
                        .filter(Boolean)
                    : []
            );

        const FoundWordsForPuzzle =
            [...new Set(
                Array.isArray(Puzzle?.KnownWords)
                    ? Puzzle.KnownWords
                        .map(NormalizeWord)
                        .filter(Boolean)
                    : [
                        ...ActualFoundWordsForPuzzle,
                        ...PreviouslyFoundWordsForHistory
                    ]
            )].sort(Alphabetically);

        const PreviousWordOrigins =
            Puzzle?.PreviousWordOrigins &&
            typeof Puzzle.PreviousWordOrigins === "object" &&
            !Array.isArray(Puzzle.PreviousWordOrigins)
                ? Puzzle.PreviousWordOrigins
                : {};
''',
    "history known-word render model",
)

source = replace_once(
    source,
    '''            CreateHistoryWordSection(
                `Found Words (${FoundWordsForPuzzle.length.toLocaleString()})`,
                FoundWordsForPuzzle
            ),
            CreateHistoryTwoferSection(
                `Solved Twofers (${FoundTwofersForPuzzle.length.toLocaleString()})`,
                FoundTwofersForPuzzle
            )
''',
    '''            CreateHistoryWordSection(
                `Found Words (${FoundWordsForPuzzle.length.toLocaleString()})`,
                FoundWordsForPuzzle,
                "",
                PreviouslyFoundWordsForHistory,
                PreviousWordOrigins
            ),
            CreateHistoryTwoferSection(
                `Solved Twofers (${FoundTwofersForPuzzle.length.toLocaleString()})`,
                FoundTwofersForPuzzle,
                PreviouslyFoundWordsForHistory,
                PreviousWordOrigins
            )
''',
    "history sections previous styling args",
)

history_style_helpers = r'''
    function GetHistoricalPreviousWordTitle(Word, Origins) {
        const Origin = Origins?.[Word];
        const Label =
            Origin?.Date ||
            Origin?.PrintDate ||
            (Origin?.PuzzleId ? `Puzzle ${Origin.PuzzleId}` : null);

        return Label
            ? `Previously found on ${Label}`
            : "Previously found on an earlier Letter Boxed puzzle";
    }

    function ApplyHistoricalPreviousWordStyling(
        Element,
        Word,
        PreviousWords,
        Origins,
        PreviousClass
    ) {
        if (!PreviousWords?.has(Word)) {
            return;
        }

        Element.classList.add(PreviousClass);
        Element.title = GetHistoricalPreviousWordTitle(Word, Origins);
    }

'''

source = replace_once(
    source,
    '    function CreateHistoryWordSection(\n',
    history_style_helpers + '    function CreateHistoryWordSection(\n',
    "history previous styling helpers",
)

source = replace_once(
    source,
    '''    function CreateHistoryWordSection(
        Title,
        Words,
        ExtraWordClass = ""
    ) {
''',
    '''    function CreateHistoryWordSection(
        Title,
        Words,
        ExtraWordClass = "",
        PreviousWords = new Set(),
        Origins = {}
    ) {
''',
    "history word section signature",
)

source = replace_once(
    source,
    '''                Item.className =
                    `lb-cubed-word lb-cubed-found-word ${ExtraWordClass}`.trim();
                Item.textContent = Word;
                Grid.appendChild(Item);
''',
    '''                Item.className =
                    `lb-cubed-word lb-cubed-found-word ${ExtraWordClass}`.trim();
                Item.textContent = Word;
                ApplyHistoricalPreviousWordStyling(
                    Item,
                    Word,
                    PreviousWords,
                    Origins,
                    "lb-cubed-word-previously-found"
                );
                Grid.appendChild(Item);
''',
    "history word previous styling",
)

source = replace_once(
    source,
    '''    function CreateHistoryTwoferSection(
        Title,
        TwofersForPuzzle
    ) {
''',
    '''    function CreateHistoryTwoferSection(
        Title,
        TwofersForPuzzle,
        PreviousWords = new Set(),
        Origins = {}
    ) {
''',
    "history twofer section signature",
)

source = replace_once(
    source,
    '''                First.className =
                    "lb-cubed-twofer-word lb-cubed-twofer-revealed";
                First.textContent = Pair[0];
''',
    '''                First.className =
                    "lb-cubed-twofer-word lb-cubed-twofer-revealed";
                First.textContent = Pair[0];
                ApplyHistoricalPreviousWordStyling(
                    First,
                    Pair[0],
                    PreviousWords,
                    Origins,
                    "lb-cubed-twofer-word-previously-found"
                );
''',
    "history first twofer word styling",
)

source = replace_once(
    source,
    '''                Second.className =
                    "lb-cubed-twofer-word lb-cubed-twofer-revealed";
                Second.textContent = Pair[1];
''',
    '''                Second.className =
                    "lb-cubed-twofer-word lb-cubed-twofer-revealed";
                Second.textContent = Pair[1];
                ApplyHistoricalPreviousWordStyling(
                    Second,
                    Pair[1],
                    PreviousWords,
                    Origins,
                    "lb-cubed-twofer-word-previously-found"
                );
''',
    "history second twofer word styling",
)

source = replace_once(
    source,
    '''        if (!FirstWasFound) {
            MarkWordForHighlight(NormalizedFirst);
        }

        if (!SecondWasFound) {
            MarkWordForHighlight(NormalizedSecond);
        }
''',
    '''        if (
            !FirstWasFound &&
            ShouldHighlightWordDiscovery(NormalizedFirst)
        ) {
            MarkWordForHighlight(NormalizedFirst);
        }

        if (
            !SecondWasFound &&
            ShouldHighlightWordDiscovery(NormalizedSecond)
        ) {
            MarkWordForHighlight(NormalizedSecond);
        }
''',
    "twofer historical highlight suppression",
)

source = replace_once(
    source,
    '''            if (!FoundWords.has(Word)) {
                FoundWords.add(Word);
                MarkWordForHighlight(Word);
                FoundWordsChanged = true;
''',
    '''            if (!FoundWords.has(Word)) {
                const ShouldHighlight = ShouldHighlightWordDiscovery(Word);
                FoundWords.add(Word);

                if (ShouldHighlight) {
                    MarkWordForHighlight(Word);
                }

                FoundWordsChanged = true;
''',
    "scan historical highlight suppression",
)

source_path.write_text(source, encoding="utf-8")

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

test_path = Path("tests/merge-tests.js")
tests = test_path.read_text(encoding="utf-8")

tests = replace_once(
    tests,
    '''      BuildGlobalWordRecord, MergeGlobalWordHistoryValues,
      RebuildGlobalWordHistoryFromTrackerStorage
''',
    '''      BuildGlobalWordRecord, MergeGlobalWordHistoryValues,
      RebuildGlobalWordHistoryFromTrackerStorage,
      HistoricalWordProjectionStorageKey, HistoricalWordProjectionVersion,
      BuildHistoricalWordProjection, MergeHistoricalWordProjectionValues,
      ShouldHighlightWordDiscovery
''',
    "test exports beta2 helpers",
)

new_tests = r'''

test('Historical projection only inherits words from earlier puzzles', () => {
  const puzzles = [
    {PuzzleId:'100',PrintDate:'2026-09-01',Date:'Sep 1',Sides:['AXD','BEF','CGH','IJK'],FoundWords:['ABC']},
    {PuzzleId:'101',PrintDate:'2026-09-02',Date:'Sep 2',Sides:['AXD','BEF','CGH','IJK'],FoundWords:['CBA']}
  ];
  const projection = T.BuildHistoricalWordProjection(puzzles);
  eq(projection.Puzzles['100'].PreviouslyFoundWords, [], 'future word leaked backward into first puzzle');
  eq(projection.Puzzles['101'].PreviouslyFoundWords, ['ABC'], 'earlier valid word was not inherited by later puzzle');
  assert(projection.Puzzles['101'].Origins.ABC.PuzzleId === '100', 'first-found provenance was not retained');
});

test('Historical projection excludes an earlier word when its adjacent letters share a side', () => {
  const puzzles = [
    {PuzzleId:'100',PrintDate:'2026-09-01',Sides:['AXD','BEF','CGH','IJK'],FoundWords:['ABC']},
    {PuzzleId:'101',PrintDate:'2026-09-02',Sides:['ABX','CDE','FGH','IJK'],FoundWords:[]}
  ];
  const projection = T.BuildHistoricalWordProjection(puzzles);
  eq(projection.Puzzles['101'].PreviouslyFoundWords, [], 'structurally invalid historical word was inherited');
});

test('Historical projection merge unions puzzle backfills and keeps earliest provenance', () => {
  const local = {
    Version:T.HistoricalWordProjectionVersion,
    Puzzles:{'200':{PreviouslyFoundWords:['ABC'],Origins:{ABC:{PuzzleId:'100',PrintDate:'2026-09-01',Date:'Sep 1'}}}}
  };
  const incoming = {
    Version:T.HistoricalWordProjectionVersion,
    Puzzles:{'200':{PreviouslyFoundWords:['ABC','CBA'],Origins:{ABC:{PuzzleId:'101',PrintDate:'2026-09-02',Date:'Sep 2'},CBA:{PuzzleId:'150',PrintDate:'2026-09-03',Date:'Sep 3'}}}}
  };
  const merged = T.MergeHistoricalWordProjectionValues(local,incoming);
  eq(merged.Puzzles['200'].PreviouslyFoundWords, ['ABC','CBA'], 'historical projection words did not union');
  assert(merged.Puzzles['200'].Origins.ABC.PuzzleId === '100', 'earliest historical provenance did not win');
});

test('Previously known word discovery suppresses new-word highlighting', () => {
  assert(T.ShouldHighlightWordDiscovery('ABC', new Set(['ABC'])) === false, 'historical word should not highlight');
  assert(T.ShouldHighlightWordDiscovery('CBA', new Set(['ABC'])) === true, 'genuinely new word should highlight');
});
'''

anchor = "\ntest('Cloud payload omits device-local panel width', () => {"
if tests.count(anchor) != 1:
    raise RuntimeError(f"beta2 test insertion anchor: expected one match, found {tests.count(anchor)}")
tests = tests.replace(anchor, new_tests + anchor, 1)

test_path.write_text(tests, encoding="utf-8")

# -----------------------------------------------------------------------------
# Changelog / preview docs
# -----------------------------------------------------------------------------

changelog_path = Path("CHANGELOG.md")
changelog = changelog_path.read_text(encoding="utf-8")
changelog = replace_once(
    changelog,
    "# Changelog\n\n## 1.13.0-beta.1",
    """# Changelog\n\n## 1.13.0-beta.2\n- Backfilled Browse History chronologically so each retained puzzle inherits only words actually found on earlier puzzles that are structurally valid on that day's sides; future discoveries are never allowed to leak backward.\n- Browse History now renders inherited words with the same darker previously-found styling used by the live panel, including solved-twofer constituents and first-found provenance tooltips when available. Completion/Longest/Found Words use the day's known-word projection.\n- Today's Browse History record is overlaid from the live local puzzle before rendering, then sanity-checked against the live Known/Previously Found sets; any mismatch is logged and the live values win so the two views remain identical.\n- Added a versioned, cloud-synced historical projection cache so the retroactive backfill persists instead of reparsing every retained day on every normal page load.\n- Suppressed new-word highlight animations when a word is first entered on the current day but was already known from an earlier puzzle; newly solved twofers still receive their own twofer highlight.\n\n## 1.13.0-beta.1""",
    "beta2 changelog",
)
changelog_path.write_text(changelog, encoding="utf-8")

docs_path = Path("docs/PREVIEW_TESTING.md")
docs = docs_path.read_text(encoding="utf-8")
docs = docs.replace("The current source is `1.12.0`.", "The current source is `1.13.0-beta.2`.", 1)
marker = "## v1.12 QoL bundle checks\n"
if marker not in docs:
    raise RuntimeError("preview docs v1.12 marker missing")
beta2_docs = '''## v1.13 global word memory checks\n\n- Browse History retroactively derives each puzzle's known words in chronological order. A word found on Sep 3 may appear as previously found on Sep 4 if it fits Sep 4's sides, but must never appear on Sep 1 or Sep 2 because that would leak future knowledge backward.\n- Previously found words in Browse History use the same darker styling as the live panel. When first-found provenance is available, hovering the word identifies the earlier date/puzzle. Solved Twofer constituents use the same previous-word styling independently.\n- The current day's Browse History record is overlaid from the live local puzzle and sanity-checked against the exact live KnownWordsForPuzzle / PreviouslyFoundWordsForPuzzle sets. A mismatch should emit a console warning and Browse History should use the live values.\n- Entering a historically known word for the first time today must not trigger any new-word fade/highlight. Entering a genuinely never-before-found word still highlights normally. Solving a new exact Twofer may still highlight the Twofer itself even when one or both constituent words were historical.\n- The versioned HistoricalWordProjection is included in backup/cloud sync and is rebuilt from chronological FoundWords + side metadata, never from already projected KnownWords.\n\n'''
docs = docs.replace(marker, beta2_docs + marker, 1)
docs_path.write_text(docs, encoding="utf-8")
