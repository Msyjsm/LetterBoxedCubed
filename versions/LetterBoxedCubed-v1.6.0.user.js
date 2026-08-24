// ==UserScript==
// @name         NYT Letter Boxed Cubed
// @namespace    https://www.nytimes.com/puzzles/letter-boxed
// @version      1.6.0
// @description  Tracks Letter Boxed discoveries, twofers, hints, statistics, found words, and spoiler-redacted unfound words.
// @author       Nathan Burgdorff + Ari (ChatGPT)
// @match        https://www.nytimes.com/puzzles/letter-boxed*
// @grant        unsafeWindow
// @grant        GM_getValue
// @grant        GM_setValue
// @run-at       document-idle
// ==/UserScript==

(function () {
    "use strict";

    const PageWindow = typeof unsafeWindow !== "undefined" ? unsafeWindow : window;

    const PanelId = "lb-cubed-panel";
    const StyleId = "lb-cubed-styles";
    const LayoutClass = "lb-cubed-layout-active";
    const SideModeClass = "lb-cubed-side-mode";
    const StackedModeClass = "lb-cubed-stacked-mode";

    const GameGap = 24;
    const EdgePadding = 18;
    const MinimumPanelWidth = 340;

    const TwoferCacheVersion = 1;
    const TwoferSeparator = "\u001F";

    let GameData = null;
    let Dictionary = [];
    let FoundWords = new Set();

    let PuzzleStorageId = null;
    let WordStorageKey = null;
    let TwoferCacheKey = null;
    let FoundTwoferStorageKey = null;

    let Twofers = [];
    let TwoferKeySet = new Set();
    let TwoferFirstWords = new Set();
    let TwoferSecondWords = new Set();
    let FoundTwofers = new Set();
    let TwofersGrouped = true;

    let NativeWordWidth = 0;
    let NativeSquareWidth = 0;

    let GameObserver = null;
    let LayoutObserver = null;
    let ScanTimer = null;
    let LayoutTimer = null;

    // -------------------------------------------------------------------------
    // Initialization
    // -------------------------------------------------------------------------

    async function Initialize() {
        AddStyles();

        const Ready = await WaitForGame();
        if (!Ready) {
            console.warn("[Letter Boxed Cubed] Could not find Letter Boxed game data.");
            return;
        }

        LoadPuzzleData();
        LoadFoundWords();
        LoadOrCalculateTwofers();
        LoadFoundTwofers();
        CaptureNativeDimensions();
        CreatePanel();
        ScanGameState(true);
        StartGameObserver();
        StartSubmissionHooks();
        StartLayoutObserver();
        UpdatePanelLayout();

        window.addEventListener("resize", QueuePanelLayoutUpdate);

        console.log("[Letter Boxed Cubed] Initialized.", {
            PuzzleId: GameData.id,
            Date: GameData.printDate,
            DictionaryWords: Dictionary.length,
            Twofers: Twofers.length,
            UniqueTwoferFirstWords: TwoferFirstWords.size,
            UniqueTwoferSecondWords: TwoferSecondWords.size,
            FoundWords: FoundWords.size,
            FoundTwofers: FoundTwofers.size,
            NativeWordWidth,
            NativeSquareWidth
        });
    }

    function WaitForGame() {
        return new Promise((Resolve) => {
            const StartTime = Date.now();
            const TimeoutMs = 20000;

            const Timer = setInterval(() => {
                const HasGameData =
                    PageWindow.gameData &&
                    Array.isArray(PageWindow.gameData.dictionary);

                const HasWordContainer = document.querySelector(
                    ".lb-game-container .lb-word-container"
                );

                const HasSquareContainer = document.querySelector(
                    ".lb-game-container .lb-square-container"
                );

                if (HasGameData && HasWordContainer && HasSquareContainer) {
                    clearInterval(Timer);
                    Resolve(true);
                    return;
                }

                if (Date.now() - StartTime >= TimeoutMs) {
                    clearInterval(Timer);
                    Resolve(false);
                }
            }, 250);
        });
    }

    function LoadPuzzleData() {
        GameData = PageWindow.gameData;

        Dictionary = [...new Set(
            GameData.dictionary
                .map(NormalizeWord)
                .filter(Boolean)
        )].sort(Alphabetically);

        PuzzleStorageId = String(
            GameData.id ||
            GameData.printDate ||
            "UnknownPuzzle"
        );

        // Preserve the original v1 key so existing tracked words survive.
        WordStorageKey = "LetterBoxedTracker_" + PuzzleStorageId;
        TwoferCacheKey = "LetterBoxedCubed_TwoferCache_" + PuzzleStorageId;
        FoundTwoferStorageKey = "LetterBoxedCubed_FoundTwofers_" + PuzzleStorageId;
    }

    // -------------------------------------------------------------------------
    // Found words
    // -------------------------------------------------------------------------

    function LoadFoundWords() {
        const SavedWords = GM_getValue(WordStorageKey, []);

        FoundWords = new Set(
            Array.isArray(SavedWords)
                ? SavedWords.map(NormalizeWord).filter(Boolean)
                : []
        );
    }

    function SaveFoundWords() {
        GM_setValue(
            WordStorageKey,
            [...FoundWords].sort(Alphabetically)
        );
    }

    // -------------------------------------------------------------------------
    // Twofer calculation and cache
    // -------------------------------------------------------------------------

    function LoadOrCalculateTwofers() {
        const SidesSignature = (GameData.sides || []).join("|");
        const DictionaryHash = HashString(Dictionary.join("\u001E"));
        const Cached = GM_getValue(TwoferCacheKey, null);

        const CacheIsValid =
            Cached &&
            Cached.Version === TwoferCacheVersion &&
            Cached.PuzzleId === PuzzleStorageId &&
            Cached.SidesSignature === SidesSignature &&
            Cached.DictionaryHash === DictionaryHash &&
            Array.isArray(Cached.Solutions);

        if (CacheIsValid) {
            Twofers = Cached.Solutions
                .filter(Solution => Array.isArray(Solution) && Solution.length === 2)
                .map(Solution => CreateTwoferRecord(Solution[0], Solution[1]));

            console.log(
                `[Letter Boxed Cubed] Loaded ${Twofers.length.toLocaleString()} cached twofers.`
            );
        } else {
            const StartTime = performance.now();
            Twofers = CalculateTwofers();
            const Elapsed = performance.now() - StartTime;

            GM_setValue(TwoferCacheKey, {
                Version: TwoferCacheVersion,
                PuzzleId: PuzzleStorageId,
                PrintDate: GameData.printDate || null,
                Sides: Array.isArray(GameData.sides) ? [...GameData.sides] : [],
                SidesSignature,
                DictionaryCount: Dictionary.length,
                DictionaryHash,
                CalculatedAt: new Date().toISOString(),
                Solutions: Twofers.map(Twofer => [Twofer.First, Twofer.Second])
            });

            console.log(
                `[Letter Boxed Cubed] Calculated ${Twofers.length.toLocaleString()} twofers in ${Elapsed.toFixed(1)} ms.`
            );
        }

        TwoferKeySet = new Set(Twofers.map(Twofer => Twofer.Key));
        RebuildTwoferWordCategories();
    }

    function RebuildTwoferWordCategories() {
        TwoferFirstWords = new Set(Twofers.map(Twofer => Twofer.First));
        TwoferSecondWords = new Set(Twofers.map(Twofer => Twofer.Second));
    }

    function CalculateTwofers() {
        const PuzzleLetters = [...new Set(
            (GameData.sides || [])
                .join("")
                .toUpperCase()
                .split("")
        )];

        const LetterBits = new Map();
        let FullMask = 0;

        for (let Index = 0; Index < PuzzleLetters.length; Index++) {
            const Bit = 1 << Index;
            LetterBits.set(PuzzleLetters[Index], Bit);
            FullMask |= Bit;
        }

        const WordRecords = Dictionary.map(Word => {
            let Mask = 0;

            for (const Letter of Word) {
                const Bit = LetterBits.get(Letter);
                if (Bit !== undefined) {
                    Mask |= Bit;
                }
            }

            return {
                Word,
                First: Word[0],
                Last: Word[Word.length - 1],
                Mask
            };
        });

        const WordsByFirstLetter = new Map();

        for (const Record of WordRecords) {
            if (!WordsByFirstLetter.has(Record.First)) {
                WordsByFirstLetter.set(Record.First, []);
            }

            WordsByFirstLetter.get(Record.First).push(Record);
        }

        const Solutions = [];

        for (const FirstRecord of WordRecords) {
            const PossibleSeconds = WordsByFirstLetter.get(FirstRecord.Last) || [];

            for (const SecondRecord of PossibleSeconds) {
                if ((FirstRecord.Mask | SecondRecord.Mask) !== FullMask) {
                    continue;
                }

                Solutions.push(
                    CreateTwoferRecord(FirstRecord.Word, SecondRecord.Word)
                );
            }
        }

        Solutions.sort(CompareTwofers);
        return Solutions;
    }

    function CreateTwoferRecord(First, Second) {
        const NormalizedFirst = NormalizeWord(First);
        const NormalizedSecond = NormalizeWord(Second);

        return {
            First: NormalizedFirst,
            Second: NormalizedSecond,
            Key: MakeTwoferKey(NormalizedFirst, NormalizedSecond)
        };
    }

    function MakeTwoferKey(First, Second) {
        return NormalizeWord(First) + TwoferSeparator + NormalizeWord(Second);
    }

    function SplitTwoferKey(Key) {
        return String(Key).split(TwoferSeparator);
    }

    function CompareTwofers(A, B) {
        const FirstComparison = Alphabetically(A.First, B.First);
        return FirstComparison !== 0
            ? FirstComparison
            : Alphabetically(A.Second, B.Second);
    }

    function HashString(Value) {
        let Hash = 2166136261;

        for (let Index = 0; Index < Value.length; Index++) {
            Hash ^= Value.charCodeAt(Index);
            Hash = Math.imul(Hash, 16777619);
        }

        return (Hash >>> 0).toString(16).padStart(8, "0");
    }

    // -------------------------------------------------------------------------
    // Found twofers
    // -------------------------------------------------------------------------

    function LoadFoundTwofers() {
        const Saved = GM_getValue(FoundTwoferStorageKey, []);
        const SavedKeys = Array.isArray(Saved) ? Saved : [];

        FoundTwofers = new Set(
            SavedKeys.filter(Key => TwoferKeySet.has(Key))
        );

        if (FoundTwofers.size !== SavedKeys.length) {
            SaveFoundTwofers();
        }

        // Every word in a completed twofer was necessarily found.
        let FoundWordsChanged = false;

        for (const Key of FoundTwofers) {
            const Parts = SplitTwoferKey(Key);
            if (Parts.length !== 2) {
                continue;
            }

            for (const Word of Parts) {
                if (!FoundWords.has(Word)) {
                    FoundWords.add(Word);
                    FoundWordsChanged = true;
                }
            }
        }

        if (FoundWordsChanged) {
            SaveFoundWords();
        }
    }

    function SaveFoundTwofers() {
        GM_setValue(
            FoundTwoferStorageKey,
            [...FoundTwofers].sort(Alphabetically)
        );
    }

    function MarkTwoferFound(First, Second) {
        const NormalizedFirst = NormalizeWord(First);
        const NormalizedSecond = NormalizeWord(Second);
        const Key = MakeTwoferKey(NormalizedFirst, NormalizedSecond);

        if (!TwoferKeySet.has(Key) || FoundTwofers.has(Key)) {
            return false;
        }

        FoundTwofers.add(Key);
        FoundWords.add(NormalizedFirst);
        FoundWords.add(NormalizedSecond);

        SaveFoundTwofers();
        SaveFoundWords();

        console.log(
            "[Letter Boxed Cubed] Twofer found:",
            `${NormalizedFirst} -> ${NormalizedSecond}`
        );

        return true;
    }

    // -------------------------------------------------------------------------
    // Hints and twofer categories
    // -------------------------------------------------------------------------

    function CalculateTwoferHintStats() {
        let FoundFirstWords = 0;
        let FoundSecondWords = 0;

        for (const Word of TwoferFirstWords) {
            if (FoundWords.has(Word)) {
                FoundFirstWords++;
            }
        }

        for (const Word of TwoferSecondWords) {
            if (FoundWords.has(Word)) {
                FoundSecondWords++;
            }
        }

        return {
            FoundFirstWords,
            TotalFirstWords: TwoferFirstWords.size,
            FoundSecondWords,
            TotalSecondWords: TwoferSecondWords.size,
            HasUnconnectedFoundSolution: Twofers.some(
                Twofer => GetTwoferCategory(Twofer) === "IndividuallyFound"
            )
        };
    }

    function GetTwoferCategory(Twofer) {
        if (FoundTwofers.has(Twofer.Key)) {
            return "Found";
        }

        const FirstFound = FoundWords.has(Twofer.First);
        const SecondFound = FoundWords.has(Twofer.Second);

        if (FirstFound && SecondFound) {
            return "IndividuallyFound";
        }

        if (FirstFound || SecondFound) {
            return "PartiallyFound";
        }

        return "Unfound";
    }

    function GetTwoferWordVisibility(Twofer, Category) {
        switch (Category) {
            case "Found":
                return {
                    FirstVisible: true,
                    SecondVisible: true
                };

            case "PartiallyFound":
                return {
                    FirstVisible: FoundWords.has(Twofer.First),
                    SecondVisible: FoundWords.has(Twofer.Second)
                };

            case "IndividuallyFound":
            case "Unfound":
            default:
                return {
                    FirstVisible: false,
                    SecondVisible: false
                };
        }
    }

    function GetGroupedTwofers() {
        const Groups = {
            Found: [],
            PartiallyFound: [],
            IndividuallyFound: [],
            Unfound: []
        };

        for (const Twofer of Twofers) {
            Groups[GetTwoferCategory(Twofer)].push(Twofer);
        }

        for (const Group of Object.values(Groups)) {
            Group.sort(CompareTwofers);
        }

        return Groups;
    }

    // -------------------------------------------------------------------------
    // Game state tracking
    // -------------------------------------------------------------------------

    function StartGameObserver() {
        const WordContainer = document.querySelector(
            ".lb-game-container .lb-word-container"
        );

        if (!WordContainer) {
            console.warn("[Letter Boxed Cubed] Could not find word container.");
            return;
        }

        GameObserver = new MutationObserver(() => {
            clearTimeout(ScanTimer);
            ScanTimer = setTimeout(() => {
                ScanGameState();
                QueuePanelLayoutUpdate();
            }, 30);
        });

        GameObserver.observe(WordContainer, {
            childList: true,
            subtree: true,
            characterData: true
        });
    }

    function StartSubmissionHooks() {
        document.addEventListener("click", Event => {
            if (!(Event.target instanceof Element)) {
                return;
            }

            const EnterButton = Event.target.closest('[data-testid="enter"]');
            if (!EnterButton) {
                return;
            }

            CheckProspectiveTwofer();
            QueuePostSubmissionScans();
        }, true);

        document.addEventListener("keydown", Event => {
            if (Event.key !== "Enter") {
                return;
            }

            CheckProspectiveTwofer();
            QueuePostSubmissionScans();
        }, true);
    }

    function QueuePostSubmissionScans() {
        for (const Delay of [0, 40, 100, 250, 500]) {
            setTimeout(ScanGameState, Delay);
        }
    }

    function CheckProspectiveTwofer() {
        const CurrentChain = ReadCurrentChain();
        if (CurrentChain.length !== 1) {
            return;
        }

        const InputWord = ReadCurrentInputWord();
        if (!InputWord) {
            return;
        }

        if (MarkTwoferFound(CurrentChain[0], InputWord)) {
            RenderPanel();
        }
    }

    function ScanGameState(ForceRender = false) {
        const CurrentChain = ReadCurrentChain();
        let FoundWordsChanged = false;

        for (const Word of CurrentChain) {
            if (!FoundWords.has(Word)) {
                FoundWords.add(Word);
                FoundWordsChanged = true;

                console.log("[Letter Boxed Cubed] Found:", Word);
            }
        }

        if (FoundWordsChanged) {
            SaveFoundWords();
        }

        let TwoferChanged = false;

        if (CurrentChain.length === 2) {
            TwoferChanged = MarkTwoferFound(
                CurrentChain[0],
                CurrentChain[1]
            );
        }

        if (FoundWordsChanged || TwoferChanged || ForceRender) {
            RenderPanel();
        }
    }

    function ReadCurrentChain() {
        return [...document.querySelectorAll(
            "#pz-game-root .lb-word-list__word"
        )]
            .map(Element => NormalizeWord(Element.textContent))
            .filter(Boolean);
    }

    function ReadCurrentInputWord() {
        const InputElement = document.querySelector(
            "#pz-game-root .lb-text-field"
        );

        return InputElement
            ? NormalizeWord(InputElement.textContent)
            : "";
    }

    function NormalizeWord(Value) {
        return String(Value || "")
            .replace(/\s+/g, "")
            .trim()
            .toUpperCase();
    }

    function Alphabetically(A, B) {
        return String(A).localeCompare(String(B));
    }

    // -------------------------------------------------------------------------
    // Layout
    // -------------------------------------------------------------------------

    function CaptureNativeDimensions() {
        const WordContainer = document.querySelector(
            ".lb-game-container .lb-word-container"
        );

        const SquareContainer = document.querySelector(
            ".lb-game-container .lb-square-container"
        );

        if (!WordContainer || !SquareContainer) {
            return;
        }

        NativeWordWidth = Math.ceil(
            WordContainer.getBoundingClientRect().width
        );

        NativeSquareWidth = Math.ceil(
            SquareContainer.getBoundingClientRect().width
        );
    }

    function StartLayoutObserver() {
        if (typeof ResizeObserver === "undefined") {
            return;
        }

        const WordContainer = document.querySelector(
            ".lb-game-container .lb-word-container"
        );

        const SquareContainer = document.querySelector(
            ".lb-game-container .lb-square-container"
        );

        if (!WordContainer || !SquareContainer) {
            return;
        }

        LayoutObserver = new ResizeObserver(QueuePanelLayoutUpdate);
        LayoutObserver.observe(WordContainer);
        LayoutObserver.observe(SquareContainer);
    }

    function QueuePanelLayoutUpdate() {
        clearTimeout(LayoutTimer);
        LayoutTimer = setTimeout(UpdatePanelLayout, 40);
    }

    function UpdatePanelLayout() {
        const GameContainer = document.querySelector(".lb-game-container");
        const WordContainer = GameContainer?.querySelector(".lb-word-container");
        const SquareContainer = GameContainer?.querySelector(".lb-square-container");
        const Panel = document.getElementById(PanelId);

        if (!GameContainer || !WordContainer || !SquareContainer || !Panel) {
            return;
        }

        const AvailableWidth = GameContainer.clientWidth;
        const RequiredWidth =
            EdgePadding +
            NativeWordWidth +
            GameGap +
            NativeSquareWidth +
            GameGap +
            MinimumPanelWidth +
            EdgePadding;

        if (AvailableWidth >= RequiredWidth) {
            ApplySideLayout(
                GameContainer,
                WordContainer,
                SquareContainer,
                Panel
            );
        } else {
            ApplyStackedLayout(
                GameContainer,
                WordContainer,
                SquareContainer,
                Panel
            );
        }
    }

    function ApplySideLayout(
        GameContainer,
        WordContainer,
        SquareContainer,
        Panel
    ) {
        GameContainer.classList.add(SideModeClass);
        GameContainer.classList.remove(StackedModeClass);

        GameContainer.style.setProperty(
            "--lb-cubed-word-width",
            `${NativeWordWidth}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-square-width",
            `${NativeSquareWidth}px`
        );

        GameContainer.style.setProperty("--lb-cubed-gap", `${GameGap}px`);
        GameContainer.style.setProperty(
            "--lb-cubed-edge-padding",
            `${EdgePadding}px`
        );

        Panel.style.removeProperty("left");
        Panel.style.removeProperty("top");
        Panel.style.removeProperty("width");

        const WordRect = WordContainer.getBoundingClientRect();
        const SquareRect = SquareContainer.getBoundingClientRect();
        const PlayTop = Math.min(WordRect.top, SquareRect.top);
        const PlayBottom = Math.max(WordRect.bottom, SquareRect.bottom);
        const PlayHeight = Math.ceil(PlayBottom - PlayTop);

        Panel.style.height = `${PlayHeight}px`;
        Panel.style.maxHeight = `${PlayHeight}px`;
    }

    function ApplyStackedLayout(
        GameContainer,
        WordContainer,
        SquareContainer,
        Panel
    ) {
        GameContainer.classList.remove(SideModeClass);
        GameContainer.classList.add(StackedModeClass);

        const GameRect = GameContainer.getBoundingClientRect();
        const WordRect = WordContainer.getBoundingClientRect();
        const SquareRect = SquareContainer.getBoundingClientRect();
        const PlayTop = Math.min(WordRect.top, SquareRect.top);
        const PlayBottom = Math.max(WordRect.bottom, SquareRect.bottom);
        const PlayHeight = Math.ceil(PlayBottom - PlayTop);
        const PanelTop = Math.round(PlayBottom - GameRect.top + 16);

        Panel.style.left = `${EdgePadding}px`;
        Panel.style.top = `${PanelTop}px`;
        Panel.style.width = `${Math.max(
            280,
            GameRect.width - (EdgePadding * 2)
        )}px`;
        Panel.style.height = `${PlayHeight}px`;
        Panel.style.maxHeight = `${PlayHeight}px`;
    }

    // -------------------------------------------------------------------------
    // Panel rendering
    // -------------------------------------------------------------------------

    function CreatePanel() {
        if (document.getElementById(PanelId)) {
            return;
        }

        const GameContainer = document.querySelector(".lb-game-container");
        if (!GameContainer) {
            console.warn("[Letter Boxed Cubed] Could not find .lb-game-container.");
            return;
        }

        GameContainer.classList.add(LayoutClass);

        const Panel = document.createElement("section");
        Panel.id = PanelId;
        GameContainer.appendChild(Panel);
    }

    function RenderPanel() {
        const Panel = document.getElementById(PanelId);
        if (!Panel) {
            return;
        }

        const PreviousOpenStates = ReadTreeOpenStates(Panel);
        const PreviousScrollTop = Panel.scrollTop;

        const FoundDictionaryWords = Dictionary
            .filter(Word => FoundWords.has(Word))
            .sort(Alphabetically);

        const UnfoundWords = Dictionary
            .filter(Word => !FoundWords.has(Word))
            .sort(Alphabetically);

        const Stats = CalculateStats(FoundDictionaryWords);
        const TwoferHintStats = CalculateTwoferHintStats();

        Panel.replaceChildren();

        RenderHeader(Panel);
        RenderMainStats(Panel, Stats);
        RenderHints(Panel, PreviousOpenStates, TwoferHintStats);
        RenderTwofers(Panel, PreviousOpenStates);
        RenderWordsByLength(Panel, PreviousOpenStates, Stats);
        RenderFoundAndUnfoundWords(
            Panel,
            PreviousOpenStates,
            FoundDictionaryWords,
            UnfoundWords
        );

        Panel.scrollTop = PreviousScrollTop;
        QueuePanelLayoutUpdate();
    }

    function RenderHeader(Panel) {
        const Header = document.createElement("div");
        Header.className = "lb-cubed-header";

        const Title = document.createElement("h2");
        Title.className = "lb-cubed-title";
        Title.textContent = "Word Log";

        const Subtitle = document.createElement("div");
        Subtitle.className = "lb-cubed-subtitle";
        Subtitle.textContent =
            GameData.date ||
            GameData.printDate ||
            "Today's Letter Boxed";

        const HeaderText = document.createElement("div");
        HeaderText.append(Title, Subtitle);
        Header.appendChild(HeaderText);
        Panel.appendChild(Header);
    }

    function RenderMainStats(Panel, Stats) {
        const StatGrid = document.createElement("div");
        StatGrid.className = "lb-cubed-stat-grid";

        AddStat(
            StatGrid,
            "Completion",
            `${Stats.FoundCount.toLocaleString()} / ${Stats.TotalCount.toLocaleString()} (${Stats.PercentFound.toFixed(1)}%)`
        );

        AddStat(
            StatGrid,
            "Longest Found",
            Stats.LongestFoundText
        );

        Panel.appendChild(StatGrid);
    }

    function RenderHints(Panel, PreviousOpenStates, HintStats) {
        const HintsDetails = document.createElement("details");
        HintsDetails.className = "lb-cubed-tree lb-cubed-hints-tree";
        ConfigureTree(
            HintsDetails,
            "Hints",
            PreviousOpenStates,
            false
        );

        const HintsSummary = document.createElement("summary");
        HintsSummary.textContent = "Hints";
        HintsDetails.appendChild(HintsSummary);

        const HintsBody = document.createElement("div");
        HintsBody.className = "lb-cubed-hints-body";

        const SolutionIndicator = document.createElement("div");
        SolutionIndicator.className = "lb-cubed-twofer-solution-indicator";

        const SolutionIcon = document.createElement("span");
        SolutionIcon.className = HintStats.HasUnconnectedFoundSolution
            ? "lb-cubed-twofer-status-icon lb-cubed-twofer-status-yes"
            : "lb-cubed-twofer-status-icon lb-cubed-twofer-status-no";
        SolutionIcon.textContent = HintStats.HasUnconnectedFoundSolution ? "✓" : "✕";

        const SolutionText = document.createElement("span");
        SolutionText.className = "lb-cubed-twofer-solution-text";
        SolutionText.textContent = "Valid solution independently found?";

        SolutionIndicator.append(SolutionIcon, SolutionText);
        HintsBody.appendChild(SolutionIndicator);

        const CounterGrid = document.createElement("div");
        CounterGrid.className = "lb-cubed-hint-counter-grid";

        CounterGrid.append(
            CreatePotentialWordHintTree(
                "First Words",
                "HintFirstWords",
                TwoferFirstWords,
                HintStats.FoundFirstWords,
                HintStats.TotalFirstWords,
                PreviousOpenStates
            ),
            CreatePotentialWordHintTree(
                "Second Words",
                "HintSecondWords",
                TwoferSecondWords,
                HintStats.FoundSecondWords,
                HintStats.TotalSecondWords,
                PreviousOpenStates
            )
        );

        HintsBody.appendChild(CounterGrid);
        HintsDetails.appendChild(HintsBody);
        Panel.appendChild(HintsDetails);
    }

    function CreatePotentialWordHintTree(
        Label,
        SectionName,
        Words,
        FoundCount,
        TotalCount,
        PreviousOpenStates
    ) {
        const Details = document.createElement("details");
        Details.className = "lb-cubed-nested-tree lb-cubed-potential-word-tree";

        ConfigureTree(
            Details,
            SectionName,
            PreviousOpenStates,
            false
        );

        const Summary = document.createElement("summary");
        Summary.textContent = `${Label} (${FoundCount.toLocaleString()} / ${TotalCount.toLocaleString()})`;
        Details.appendChild(Summary);

        const List = document.createElement("div");
        List.className = "lb-cubed-potential-word-list";

        const SortedWords = [...Words].sort(Alphabetically);
        const Fragment = document.createDocumentFragment();

        for (const Word of SortedWords) {
            const Item = document.createElement("div");
            Item.className = FoundWords.has(Word)
                ? "lb-cubed-potential-word lb-cubed-potential-word-found"
                : "lb-cubed-potential-word";
            Item.textContent = Word;
            Fragment.appendChild(Item);
        }

        List.appendChild(Fragment);
        Details.appendChild(List);
        return Details;
    }

    function RenderTwofers(Panel, PreviousOpenStates) {
        const TwoferDetails = document.createElement("details");
        TwoferDetails.className = "lb-cubed-tree lb-cubed-twofer-tree";

        ConfigureTree(
            TwoferDetails,
            "Twofers",
            PreviousOpenStates,
            false
        );

        const TwoferSummary = document.createElement("summary");
        TwoferSummary.className = "lb-cubed-twofer-summary";

        const SummaryTitle = document.createElement("span");
        SummaryTitle.className = "lb-cubed-twofer-summary-title";
        SummaryTitle.textContent =
            `Twofers (${FoundTwofers.size.toLocaleString()} / ${Twofers.length.toLocaleString()})`;

        const SummaryActions = document.createElement("span");
        SummaryActions.className = "lb-cubed-twofer-summary-actions";

        const Disclaimer = document.createElement("span");
        Disclaimer.className = "lb-cubed-twofer-disclaimer";
        Disclaimer.textContent = "Ungrouping may spoil solutions due to alphabetization.";

        const GroupButton = document.createElement("button");
        GroupButton.type = "button";
        GroupButton.className = "lb-cubed-twofer-group-button";
        GroupButton.textContent = TwofersGrouped ? "Ungroup" : "Group";
        GroupButton.title = TwofersGrouped
            ? "Combine all twofer categories into one alphabetical list"
            : "Restore grouped twofer categories";

        const StopSummaryToggle = Event => {
            Event.preventDefault();
            Event.stopPropagation();
        };

        GroupButton.addEventListener("mousedown", StopSummaryToggle);
        GroupButton.addEventListener("click", Event => {
            StopSummaryToggle(Event);
            TwofersGrouped = !TwofersGrouped;
            RenderPanel();
        });

        SummaryActions.append(Disclaimer, GroupButton);
        TwoferSummary.append(SummaryTitle, SummaryActions);
        TwoferDetails.appendChild(TwoferSummary);

        const TwoferBody = document.createElement("div");
        TwoferBody.className = "lb-cubed-twofer-body";

        if (TwofersGrouped) {
            RenderGroupedTwofers(TwoferBody);
        } else {
            RenderUngroupedTwofers(TwoferBody);
        }

        TwoferDetails.appendChild(TwoferBody);
        Panel.appendChild(TwoferDetails);
    }

    function RenderGroupedTwofers(Container) {
        const Groups = GetGroupedTwofers();
        const GroupDefinitions = [
            ["Found", "Found"],
            ["PartiallyFound", "Partially Found"],
            ["IndividuallyFound", "Individually Found"],
            ["Unfound", "Unfound"]
        ];

        for (const [GroupKey, Label] of GroupDefinitions) {
            const Section = document.createElement("section");
            Section.className = "lb-cubed-twofer-group";

            const Heading = document.createElement("div");
            Heading.className = "lb-cubed-twofer-group-title";
            Heading.textContent = `${Label} (${Groups[GroupKey].length.toLocaleString()})`;
            Section.appendChild(Heading);

            const List = document.createElement("div");
            List.className = "lb-cubed-twofer-list";

            if (Groups[GroupKey].length === 0) {
                const Empty = document.createElement("div");
                Empty.className = "lb-cubed-twofer-group-empty";
                Empty.textContent = "None";
                List.appendChild(Empty);
            } else {
                const Fragment = document.createDocumentFragment();

                for (const Twofer of Groups[GroupKey]) {
                    Fragment.appendChild(
                        CreateTwoferRow(Twofer, GroupKey)
                    );
                }

                List.appendChild(Fragment);
            }

            Section.appendChild(List);
            Container.appendChild(Section);
        }
    }

    function RenderUngroupedTwofers(Container) {
        const List = document.createElement("div");
        List.className = "lb-cubed-twofer-list lb-cubed-twofer-list-ungrouped";

        const SortedTwofers = [...Twofers].sort(CompareTwofers);
        const Fragment = document.createDocumentFragment();

        for (const Twofer of SortedTwofers) {
            Fragment.appendChild(
                CreateTwoferRow(
                    Twofer,
                    GetTwoferCategory(Twofer)
                )
            );
        }

        List.appendChild(Fragment);
        Container.appendChild(List);
    }

    function CreateTwoferRow(Twofer, Category) {
        const Visibility = GetTwoferWordVisibility(Twofer, Category);

        const Row = document.createElement("div");
        Row.className = `lb-cubed-twofer-row lb-cubed-twofer-category-${Category}`;

        const FirstWord = CreateTwoferWordElement(
            Twofer.First,
            Visibility.FirstVisible
        );

        const Arrow = document.createElement("span");
        Arrow.className = "lb-cubed-twofer-arrow";
        Arrow.textContent = "→";

        const SecondWord = CreateTwoferWordElement(
            Twofer.Second,
            Visibility.SecondVisible
        );

        Row.append(FirstWord, Arrow, SecondWord);
        return Row;
    }

    function CreateTwoferWordElement(Word, Visible) {
        const Item = document.createElement("span");
        Item.className = Visible
            ? "lb-cubed-twofer-word lb-cubed-twofer-revealed"
            : "lb-cubed-twofer-word lb-cubed-twofer-redacted";
        Item.textContent = Word;

        if (!Visible) {
            Item.setAttribute("aria-label", "Redacted twofer word");
        }

        return Item;
    }

    function RenderWordsByLength(Panel, PreviousOpenStates, Stats) {
        const LengthDetails = document.createElement("details");
        LengthDetails.className = "lb-cubed-tree lb-cubed-length-tree";

        ConfigureTree(
            LengthDetails,
            "WordsByLength",
            PreviousOpenStates,
            false
        );

        const LengthSummary = document.createElement("summary");
        LengthSummary.textContent = "Words by Length";
        LengthDetails.appendChild(LengthSummary);

        const LengthGrid = document.createElement("div");
        LengthGrid.className = "lb-cubed-length-grid";

        AddLengthStat(LengthGrid, "3 letters", Stats.LengthStats["3"]);
        AddLengthStat(LengthGrid, "4 letters", Stats.LengthStats["4"]);
        AddLengthStat(LengthGrid, "5 letters", Stats.LengthStats["5"]);
        AddLengthStat(LengthGrid, "6 letters", Stats.LengthStats["6"]);
        AddLengthStat(LengthGrid, "7+ letters", Stats.LengthStats["7+"]);

        LengthDetails.appendChild(LengthGrid);
        Panel.appendChild(LengthDetails);
    }

    function RenderFoundAndUnfoundWords(
        Panel,
        PreviousOpenStates,
        FoundDictionaryWords,
        UnfoundWords
    ) {
        const WordColumns = document.createElement("div");
        WordColumns.className = "lb-cubed-word-columns";

        WordColumns.append(
            CreateWordTree(
                "FoundWords",
                `Found Words (${FoundDictionaryWords.length.toLocaleString()})`,
                FoundDictionaryWords,
                true,
                PreviousOpenStates,
                false
            ),
            CreateWordTree(
                "UnfoundWords",
                `Unfound Words (${UnfoundWords.length.toLocaleString()})`,
                UnfoundWords,
                true,
                PreviousOpenStates,
                true
            )
        );

        Panel.appendChild(WordColumns);
    }

    function CreateWordTree(
        SectionName,
        SummaryText,
        Words,
        DefaultOpen,
        PreviousOpenStates,
        Redacted
    ) {
        const Details = document.createElement("details");
        Details.className = "lb-cubed-tree lb-cubed-word-tree";

        ConfigureTree(
            Details,
            SectionName,
            PreviousOpenStates,
            DefaultOpen
        );

        const Summary = document.createElement("summary");
        Summary.textContent = SummaryText;
        Details.appendChild(Summary);

        const List = document.createElement("div");
        List.className = "lb-cubed-word-grid";

        if (Words.length === 0) {
            const Empty = document.createElement("div");
            Empty.className = "lb-cubed-empty";
            Empty.textContent = Redacted
                ? "You found everything. What in God's name."
                : "No words tracked yet.";
            List.appendChild(Empty);
        } else {
            const Fragment = document.createDocumentFragment();

            for (const Word of Words) {
                const Item = document.createElement("div");
                Item.className = Redacted
                    ? "lb-cubed-word lb-cubed-redacted"
                    : "lb-cubed-word lb-cubed-found-word";
                Item.textContent = Word;

                if (Redacted) {
                    Item.setAttribute("aria-label", "Unfound word, redacted");
                }

                Fragment.appendChild(Item);
            }

            List.appendChild(Fragment);
        }

        Details.appendChild(List);
        return Details;
    }

    function ReadTreeOpenStates(Panel) {
        const States = {};

        for (const Details of Panel.querySelectorAll(
            "details[data-cubed-section]"
        )) {
            States[Details.dataset.cubedSection] = Details.open;
        }

        return States;
    }

    function ConfigureTree(
        Details,
        Name,
        PreviousOpenStates,
        DefaultOpen
    ) {
        Details.dataset.cubedSection = Name;

        if (Object.prototype.hasOwnProperty.call(PreviousOpenStates, Name)) {
            Details.open = PreviousOpenStates[Name];
        } else {
            Details.open = DefaultOpen;
        }
    }

    function AddStat(Container, Label, Value) {
        const Card = document.createElement("div");
        Card.className = "lb-cubed-stat";

        const ValueElement = document.createElement("div");
        ValueElement.className = "lb-cubed-stat-value";
        ValueElement.textContent = Value;

        const LabelElement = document.createElement("div");
        LabelElement.className = "lb-cubed-stat-label";
        LabelElement.textContent = Label;

        Card.append(ValueElement, LabelElement);
        Container.appendChild(Card);
    }

    function AddLengthStat(Container, Label, Values) {
        const Row = document.createElement("div");
        Row.className = "lb-cubed-length-stat";

        const LabelElement = document.createElement("span");
        LabelElement.className = "lb-cubed-length-label";
        LabelElement.textContent = Label;

        const ValueElement = document.createElement("span");
        ValueElement.className = "lb-cubed-length-value";
        ValueElement.textContent =
            `${Values.Found.toLocaleString()} / ${Values.Total.toLocaleString()}`;

        Row.append(LabelElement, ValueElement);
        Container.appendChild(Row);
    }

    // -------------------------------------------------------------------------
    // Statistics
    // -------------------------------------------------------------------------

    function CalculateStats(FoundDictionaryWords) {
        const FoundCount = FoundDictionaryWords.length;
        const TotalCount = Dictionary.length;
        const PercentFound = TotalCount === 0
            ? 0
            : (FoundCount / TotalCount) * 100;

        const LengthStats = {
            "3": { Found: 0, Total: 0 },
            "4": { Found: 0, Total: 0 },
            "5": { Found: 0, Total: 0 },
            "6": { Found: 0, Total: 0 },
            "7+": { Found: 0, Total: 0 }
        };

        for (const Word of Dictionary) {
            const Bucket = GetLengthBucket(Word.length);
            if (Bucket) {
                LengthStats[Bucket].Total++;
            }
        }

        for (const Word of FoundDictionaryWords) {
            const Bucket = GetLengthBucket(Word.length);
            if (Bucket) {
                LengthStats[Bucket].Found++;
            }
        }

        let LongestFoundText = "-";

        if (FoundDictionaryWords.length > 0) {
            const LongestLength = Math.max(
                ...FoundDictionaryWords.map(Word => Word.length)
            );

            LongestFoundText = FoundDictionaryWords
                .filter(Word => Word.length === LongestLength)
                .sort(Alphabetically)
                .join(", ");
        }

        return {
            FoundCount,
            TotalCount,
            PercentFound,
            LengthStats,
            LongestFoundText
        };
    }

    function GetLengthBucket(Length) {
        if (Length === 3) return "3";
        if (Length === 4) return "4";
        if (Length === 5) return "5";
        if (Length === 6) return "6";
        if (Length >= 7) return "7+";
        return null;
    }

    // -------------------------------------------------------------------------
    // Styles
    // -------------------------------------------------------------------------

    function AddStyles() {
        if (document.getElementById(StyleId)) {
            return;
        }

        const Style = document.createElement("style");
        Style.id = StyleId;

        Style.textContent = `
            .lb-game-container.${LayoutClass} {
                box-sizing: border-box !important;
            }

            .lb-game-container.${SideModeClass} {
                display: flex !important;
                flex-direction: row !important;
                justify-content: flex-start !important;
                align-items: flex-start !important;
                gap: var(--lb-cubed-gap, 24px) !important;
                width: 100% !important;
                max-width: none !important;
                padding-left: var(--lb-cubed-edge-padding, 18px) !important;
                padding-right: var(--lb-cubed-edge-padding, 18px) !important;
                overflow: visible !important;
            }

            .lb-game-container.${SideModeClass} > .lb-word-container {
                flex: 0 0 var(--lb-cubed-word-width) !important;
                width: var(--lb-cubed-word-width) !important;
                min-width: var(--lb-cubed-word-width) !important;
                max-width: var(--lb-cubed-word-width) !important;
            }

            .lb-game-container.${SideModeClass} > .lb-square-container {
                flex: 0 0 var(--lb-cubed-square-width) !important;
                width: var(--lb-cubed-square-width) !important;
                min-width: var(--lb-cubed-square-width) !important;
                max-width: var(--lb-cubed-square-width) !important;
            }

            .lb-game-container.${SideModeClass} > #${PanelId} {
                position: static;
                flex: 1 1 0;
                width: auto;
                min-width: 0;
                align-self: flex-start;
            }

            .lb-game-container.${StackedModeClass} {
                position: relative !important;
                overflow: visible !important;
            }

            .lb-game-container.${StackedModeClass} > #${PanelId} {
                position: absolute;
            }

            #${PanelId} {
                z-index: 10;
                box-sizing: border-box;
                margin: 0;
                padding: 16px;
                overflow-x: hidden;
                overflow-y: auto;
                background: rgb(216, 132, 130);
                color: rgb(48, 24, 24);
                border: 1px solid rgba(76, 34, 34, 0.58);
                border-radius: 4px;
                font-family: Arial, Helvetica, sans-serif;
                scrollbar-width: thin;
                scrollbar-color: rgba(76, 32, 32, 0.58) rgba(255, 255, 255, 0.13);
            }

            #${PanelId} * {
                box-sizing: border-box;
            }

            #${PanelId}::-webkit-scrollbar {
                width: 8px;
            }

            #${PanelId}::-webkit-scrollbar-track {
                background: rgba(255, 255, 255, 0.13);
            }

            #${PanelId}::-webkit-scrollbar-thumb {
                background: rgba(76, 32, 32, 0.58);
                border-radius: 4px;
            }

            .lb-cubed-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 14px;
            }

            .lb-cubed-title {
                margin: 0;
                padding: 0;
                color: rgb(48, 24, 24);
                font-size: 24px;
                line-height: 1.1;
                font-weight: 700;
            }

            .lb-cubed-subtitle {
                margin-top: 4px;
                color: rgba(48, 24, 24, 0.70);
                font-size: 12px;
            }

            .lb-cubed-stat-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 8px;
                margin-bottom: 12px;
            }

            .lb-cubed-stat {
                min-width: 0;
                padding: 10px 8px;
                background: rgba(255, 255, 255, 0.18);
                border: 1px solid rgba(78, 34, 34, 0.32);
                border-radius: 3px;
                text-align: center;
            }

            .lb-cubed-stat-value {
                color: rgb(48, 24, 24);
                font-size: 18px;
                line-height: 1.15;
                font-weight: 700;
                overflow-wrap: anywhere;
            }

            .lb-cubed-stat-label {
                margin-top: 4px;
                color: rgba(48, 24, 24, 0.67);
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            .lb-cubed-tree,
            .lb-cubed-nested-tree {
                margin-top: 8px;
                border: 1px solid rgba(78, 34, 34, 0.38);
                border-radius: 3px;
                overflow: hidden;
            }

            .lb-cubed-tree > summary,
            .lb-cubed-nested-tree > summary {
                padding: 9px 10px;
                cursor: pointer;
                user-select: none;
                color: rgb(48, 24, 24);
                background: rgba(92, 37, 37, 0.11);
                font-size: 13px;
                font-weight: 700;
            }

            .lb-cubed-tree > summary:hover,
            .lb-cubed-nested-tree > summary:hover {
                background: rgba(92, 37, 37, 0.18);
            }

            /* Hints */

            .lb-cubed-hints-tree {
                margin-bottom: 8px;
            }

            .lb-cubed-hints-body {
                padding: 8px;
            }

            .lb-cubed-twofer-solution-indicator {
                display: flex;
                align-items: center;
                gap: 7px;
                padding: 7px 8px;
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(78, 34, 34, 0.25);
                border-radius: 3px;
                font-size: 12px;
            }

            .lb-cubed-twofer-status-icon {
                display: inline-flex;
                flex: 0 0 18px;
                align-items: center;
                justify-content: center;
                width: 18px;
                height: 18px;
                border-radius: 50%;
                color: #fff;
                font-size: 12px;
                font-weight: 900;
                line-height: 1;
            }

            .lb-cubed-twofer-status-yes {
                background: rgb(45, 125, 62);
            }

            .lb-cubed-twofer-status-no {
                background: rgb(175, 54, 54);
            }

            .lb-cubed-twofer-solution-text {
                color: rgb(48, 24, 24);
                font-style: italic;
            }

            .lb-cubed-hint-counter-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 8px;
                align-items: start;
            }

            .lb-cubed-potential-word-tree {
                min-width: 0;
            }

            .lb-cubed-potential-word-list {
                display: grid;
                grid-template-columns: 1fr;
                gap: 4px;
                padding: 8px;
            }

            .lb-cubed-potential-word {
                min-width: 0;
                padding: 5px 7px;
                background: rgba(255, 255, 255, 0.11);
                border-radius: 2px;
                color: rgba(48, 24, 24, 0.75);
                font-family: Consolas, "Courier New", monospace;
                font-size: 11px;
                overflow-wrap: anywhere;
            }

            .lb-cubed-potential-word-found {
                background: rgba(255, 255, 255, 0.28);
                color: rgb(42, 20, 20);
                font-weight: 700;
            }

            /* Twofers */

            .lb-cubed-twofer-tree {
                margin-bottom: 8px;
            }

            .lb-cubed-twofer-summary {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
            }

            .lb-cubed-twofer-summary-title {
                flex: 0 0 auto;
            }

            .lb-cubed-twofer-summary-actions {
                display: inline-flex;
                flex: 1 1 auto;
                align-items: center;
                justify-content: flex-end;
                gap: 8px;
                min-width: 0;
            }

            .lb-cubed-twofer-tree:not([open]) .lb-cubed-twofer-summary-actions {
                display: none;
            }

            .lb-cubed-twofer-disclaimer {
                min-width: 0;
                color: rgba(48, 24, 24, 0.66);
                font-size: 10px;
                font-style: italic;
                font-weight: 400;
                text-align: right;
            }

            .lb-cubed-twofer-group-button {
                flex: 0 0 auto;
                padding: 4px 8px;
                color: rgb(48, 24, 24);
                background: rgba(255, 255, 255, 0.24);
                border: 1px solid rgba(78, 34, 34, 0.35);
                border-radius: 3px;
                font: inherit;
                font-size: 11px;
                font-weight: 700;
                cursor: pointer;
            }

            .lb-cubed-twofer-group-button:hover {
                background: rgba(255, 255, 255, 0.36);
            }

            .lb-cubed-twofer-body {
                padding: 8px;
            }

            .lb-cubed-twofer-group + .lb-cubed-twofer-group {
                margin-top: 10px;
            }

            .lb-cubed-twofer-group-title {
                margin-bottom: 5px;
                padding: 5px 7px;
                color: rgba(48, 24, 24, 0.78);
                background: rgba(92, 37, 37, 0.08);
                border-radius: 2px;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }

            .lb-cubed-twofer-list {
                display: grid;
                grid-template-columns: 1fr;
                gap: 5px;
            }

            .lb-cubed-twofer-list-ungrouped {
                padding: 0;
            }

            .lb-cubed-twofer-group-empty {
                padding: 6px 8px;
                color: rgba(48, 24, 24, 0.55);
                font-size: 11px;
                font-style: italic;
            }

            .lb-cubed-twofer-row {
                display: grid;
                grid-template-columns: minmax(0, 1fr) 20px minmax(0, 1fr);
                gap: 6px;
                align-items: center;
                min-width: 0;
                padding: 3px;
                border-radius: 3px;
            }

            .lb-cubed-twofer-category-Found {
                background: rgba(255, 255, 255, 0.10);
            }

            .lb-cubed-twofer-word {
                display: block;
                min-width: 0;
                width: 100%;
                padding: 5px 7px;
                border-radius: 2px;
                font-family: Consolas, "Courier New", monospace;
                font-size: 11px;
                font-weight: 600;
                text-align: center;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .lb-cubed-twofer-arrow {
                color: rgba(48, 24, 24, 0.72);
                text-align: center;
                font-size: 14px;
                font-weight: 700;
            }

            .lb-cubed-twofer-redacted {
                background: #000 !important;
                color: #000 !important;
                border: 1px solid #000;
                user-select: none;
                cursor: default;
                text-shadow: none !important;
                text-overflow: clip;
            }

            .lb-cubed-twofer-redacted::selection {
                background: #000;
                color: #000;
            }

            .lb-cubed-twofer-revealed {
                background: rgba(255, 255, 255, 0.25);
                color: rgb(42, 20, 20);
                border: 1px solid rgba(78, 34, 34, 0.18);
            }

            /* Words by length */

            .lb-cubed-length-tree {
                margin-bottom: 10px;
            }

            .lb-cubed-length-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
                gap: 6px;
                padding: 8px;
            }

            .lb-cubed-length-stat {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-width: 0;
                padding: 7px 6px;
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(78, 34, 34, 0.27);
                border-radius: 3px;
                text-align: center;
                font-size: 11px;
            }

            .lb-cubed-length-label {
                color: rgba(48, 24, 24, 0.77);
                white-space: nowrap;
            }

            .lb-cubed-length-value {
                margin-top: 3px;
                color: rgb(48, 24, 24);
                font-weight: 700;
            }

            /* Found / unfound words */

            .lb-cubed-word-columns {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 10px;
                align-items: start;
            }

            .lb-cubed-word-tree {
                min-width: 0;
            }

            .lb-cubed-word-grid {
                display: grid;
                grid-template-columns: 1fr;
                gap: 4px;
                padding: 8px;
                overflow: visible;
            }

            .lb-cubed-word {
                display: block;
                width: 100%;
                min-width: 0;
                padding: 5px 7px;
                border-radius: 2px;
                font-family: Consolas, "Courier New", monospace;
                font-size: 11px;
                font-weight: 600;
                overflow-wrap: anywhere;
            }

            .lb-cubed-found-word {
                background: rgba(255, 255, 255, 0.25);
                color: rgb(42, 20, 20);
            }

            .lb-cubed-redacted {
                background: #000 !important;
                color: #000 !important;
                user-select: none;
                border: 1px solid #000;
                cursor: default;
                text-shadow: none !important;
            }

            .lb-cubed-redacted::selection {
                background: #000;
                color: #000;
            }

            .lb-cubed-empty {
                width: 100%;
                padding: 10px;
                color: rgba(48, 24, 24, 0.70);
                text-align: center;
                font-style: italic;
            }

            @media (max-width: 900px) {
                .lb-cubed-twofer-summary {
                    align-items: flex-start;
                }

                .lb-cubed-twofer-summary-actions {
                    flex-direction: column-reverse;
                    align-items: flex-end;
                }
            }

            @media (max-width: 700px) {
                .lb-cubed-word-columns,
                .lb-cubed-stat-grid,
                .lb-cubed-hint-counter-grid {
                    grid-template-columns: 1fr;
                }
            }
        `;

        document.head.appendChild(Style);
    }

    Initialize();
})();
