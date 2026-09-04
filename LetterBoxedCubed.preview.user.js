// ==UserScript==
// @name         Letter Boxed Cubed [PREVIEW]
// @namespace    https://nathanburgdorff.com/userscripts/preview/
// @version      1.11.0-beta.2.12
// @description  Tracks Letter Boxed discoveries, twofers, hints, statistics, found words, and spoiler-redacted unfound words.
// @author       Nathan Burgdorff + Ari (ChatGPT)
// @match        https://www.nytimes.com/puzzles/letter-boxed*
// @license      GPL-3.0-or-later
// @grant        unsafeWindow
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_listValues
// @grant        GM_xmlhttpRequest
// @connect      script.google.com
// @connect      script.googleusercontent.com
// @run-at       document-idle
// @updateURL    https://raw.githubusercontent.com/Msyjsm/LetterBoxedCubed/preview/LetterBoxedCubed.preview.user.js
// @downloadURL  https://raw.githubusercontent.com/Msyjsm/LetterBoxedCubed/preview/LetterBoxedCubed.preview.user.js
// @tag          preview
// ==/UserScript==

(function () {
    "use strict";


    // PREVIEW_CHANNEL_ROUTING
    // Tampermonkey's URL matcher ignores hash fragments, so both installed
    // copies match the page. This runtime gate makes exactly one copy active
    // and reloads when the preview hash is toggled.
    const UserscriptBuildChannel = "preview"; // PREVIEW_CHANNEL_MARKER
    const UserscriptPreviewHash = "#lbc-preview";
    const UserscriptPreviewRequested =
        location.hash.toLowerCase() === UserscriptPreviewHash;

    window.addEventListener("hashchange", () => {
        const PreviewRequestedNow =
            location.hash.toLowerCase() === UserscriptPreviewHash;

        if (PreviewRequestedNow !== UserscriptPreviewRequested) {
            location.reload();
        }
    });

    if (
        (UserscriptBuildChannel === "preview") !==
        UserscriptPreviewRequested
    ) {
        return;
    }

    const PageWindow = typeof unsafeWindow !== "undefined" ? unsafeWindow : window;

    const PanelId = "lb-cubed-panel";
    const StyleId = "lb-cubed-styles";
    const LayoutClass = "lb-cubed-layout-active";
    const SideModeClass = "lb-cubed-side-mode";
    const StackedModeClass = "lb-cubed-stacked-mode";

    const GameGap = 24;
    const LeftColumnGap = 16;
    const EdgePadding = 18;
    const MinimumPanelWidth = 300;

    /*
        TI and GB are stacked in Cubed's left meta-column. Give TI a stable
        vertical slot so accepting words cannot move GB up or down. The slot
        is intentionally roomy enough for the active chain while keeping GB
        close to the entry area; the page can still scroll if a very long
        chain eventually outgrows it.
    */
    const StableWordAreaHeight = 250;

    /*
        v1.7's automatic width was 75% of the horizontal space left after
        placing TI and GB side-by-side. In v1.8 TI and GB are stacked, which
        creates substantially more available width. To honor the request that
        LBC start at about 75% of its previous visual width, we calculate the
        old v1.7 default and then shrink that result to 75%.
    */
    const LegacyDefaultPanelWidthRatio = 0.75;
    const DefaultPanelShrinkRatio = 0.75;

    const ResizeHandleWidth = 16;
    const RightResizeHandleGap = 3;

    const LegacyPanelWidthStorageKey = "LetterBoxedCubed_PanelWidth";
    const PanelWidthStorageKey = "LetterBoxedCubed_PanelWidth_v2";

    const ExportFormatName = "LetterBoxedCubedBackup";
    const ExportFormatVersion = 3;
    const PuzzleMetadataVersion = 1;
    const PuzzleMetadataPrefix = "LetterBoxedCubed_PuzzleMetadata_";

    const CustomDictionaryStorageKey = "LetterBoxedCubed_CustomDictionary";
    const CustomWordsPrefix = "LetterBoxedCubed_CustomWords_";
    const HideParStorageKey = "LetterBoxedCubed_HidePar";
    const LineDrawingSpeedStorageKey = "LetterBoxedCubed_LineDrawingSpeed";
    const GuiStateStorageKey = "LetterBoxedCubed_GuiState";
    const GuiStateVersion = 1;

    /*
        Cloud connection credentials are deliberately local-only. They are not
        included in exports or cloud payloads, so a backup can never leak the
        Google Apps Script endpoint's shared secret.
    */
    const GoogleDriveConfigStorageKey = "LetterBoxedCubed_GoogleDriveConfig";
    const GoogleDriveConfigVersion = 1;
    const GoogleDriveButtonId = "lb-cubed-google-drive-button";
    const BrowseHistoryButtonId = "lb-cubed-browse-history-button";
    const HistoryOverlayId = "lb-cubed-history-overlay";
    const CloudSyncDebounceMs = 2500;
    const CloudSyncProtocolVersion = 1;

    const ExportStoragePrefixes = [
        "LetterBoxedTracker_",
        "LetterBoxedCubed_FoundTwofers_",
        "LetterBoxedCubed_TwoferCache_",
        PuzzleMetadataPrefix,
        CustomWordsPrefix
    ];

    const ExportExactStorageKeys = [
        LegacyPanelWidthStorageKey,
        PanelWidthStorageKey,
        CustomDictionaryStorageKey,
        HideParStorageKey,
        LineDrawingSpeedStorageKey,
        GuiStateStorageKey
    ];

    const DeviceLocalStorageKeys = [
        LegacyPanelWidthStorageKey,
        PanelWidthStorageKey
    ];

    const PanelContentId = "lb-cubed-panel-content";
    const LeftResizeHandleId = "lb-cubed-resize-handle-left";
    const RightResizeHandleId = "lb-cubed-resize-handle-right";

    const TwoferCacheVersion = 1;
    const TwoferSeparator = "\u001F";

    let GameData = null;
    let Dictionary = [];
    let DictionarySet = new Set();
    let FoundWords = new Set();
    let PuzzleSideByLetter = new Map();

    let PuzzleStorageId = null;
    let WordStorageKey = null;
    let TwoferCacheKey = null;
    let FoundTwoferStorageKey = null;
    let PuzzleMetadataStorageKey = null;
    let CustomWordsStorageKey = null;

    let Twofers = [];
    let TwoferKeySet = new Set();
    let TwoferFirstWords = new Set();
    let TwoferSecondWords = new Set();
    let FoundTwofers = new Set();
    let TwofersGrouped = true;

    let NytSolutionWords = null;
    let NytSolutionKey = null;

    let NativeWordWidth = 0;
    let NativeSquareWidth = 0;
    let NativeSquareHeight = 0;
    let PanelWidthPreference = null;
    let PanelResizeState = null;

    let CustomDictionary = new Map();
    let CustomWordsForCurrentPuzzle = new Set();
    let LastInvalidWord = null;

    let HidePar = false;
    let LineDrawingSpeed = 1.0;
    let GuiState = null;

    let GoogleDriveConfig = null;
    let CloudSyncTimer = null;
    let CloudSyncInFlight = false;
    let CloudSyncPending = false;
    let CloudSyncStatus = "Off";
    let LastCloudSyncAt = null;
    let LastCloudSyncError = null;

    let NativeRequestAnimationFrame = null;
    let LineAnimationAcceleration = null;

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
        UpdateCurrentPuzzleMetadata();
        LoadFoundWords();
        LoadCustomDictionary();
        LoadGoogleDriveConfig();
        LoadGuiState();
        LoadHideParPreference();
        ApplyHideParPreference();
        LoadLineDrawingSpeed();
        InstallLineDrawingSpeedHook();
        LoadPanelWidthPreference();
        LoadOrCalculateTwofers();
        LoadFoundTwofers();
        CaptureNativeDimensions();
        NormalizeWordAreaFeedbackLayout();
        CreatePanel();
        StartPanelResizeBehavior();
        ScanGameState(true);
        StartGameObserver();
        StartSubmissionHooks();
        StartLayoutObserver();
        UpdatePanelLayout();

        window.addEventListener("resize", QueuePanelLayoutUpdate);

        if (GoogleDriveConfig?.Enabled) {
            ScheduleCloudSync(750);
        }

        console.log("[Letter Boxed Cubed] Initialized.", {
            PuzzleId: GameData.id,
            Date: GameData.printDate,
            DictionaryWords: Dictionary.length,
            Twofers: Twofers.length,
            UniqueTwoferFirstWords: TwoferFirstWords.size,
            UniqueTwoferSecondWords: TwoferSecondWords.size,
            FoundWords: FoundWords.size,
            FoundTwofers: FoundTwofers.size,
            NytSolution: NytSolutionWords,
            CustomDictionaryWords: CustomDictionary.size,
            CustomWordsForCurrentPuzzle: CustomWordsForCurrentPuzzle.size,
            HidePar,
            LineDrawingSpeed,
            TwofersGrouped,
            GuiState,
            GoogleDriveConfigured: Boolean(GoogleDriveConfig?.Enabled),
            PanelWidthPreference,
            NativeWordWidth,
            NativeSquareWidth,
            NativeSquareHeight
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

        DictionarySet = new Set(Dictionary);

        PuzzleSideByLetter = new Map();
        for (let SideIndex = 0; SideIndex < (GameData.sides || []).length; SideIndex++) {
            for (const Letter of String(GameData.sides[SideIndex]).toUpperCase()) {
                PuzzleSideByLetter.set(Letter, SideIndex);
            }
        }

        PuzzleStorageId = String(
            GameData.id ||
            GameData.printDate ||
            "UnknownPuzzle"
        );

        // Preserve the original v1 key so existing tracked words survive.
        WordStorageKey = "LetterBoxedTracker_" + PuzzleStorageId;
        TwoferCacheKey = "LetterBoxedCubed_TwoferCache_" + PuzzleStorageId;
        FoundTwoferStorageKey = "LetterBoxedCubed_FoundTwofers_" + PuzzleStorageId;
        PuzzleMetadataStorageKey = PuzzleMetadataPrefix + PuzzleStorageId;
        CustomWordsStorageKey = CustomWordsPrefix + PuzzleStorageId;

        /*
            NYT exposes its intended answer as gameData.ourSolution.

            Cubed only marks it in the Twofers list when it is itself a
            two-word solution; longer official solutions have no corresponding
            Twofer row to annotate.
        */
        const RawNytSolution = Array.isArray(GameData.ourSolution)
            ? GameData.ourSolution.map(NormalizeWord).filter(Boolean)
            : [];

        if (RawNytSolution.length === 2) {
            NytSolutionWords = RawNytSolution;
            NytSolutionKey = MakeTwoferKey(
                RawNytSolution[0],
                RawNytSolution[1]
            );
        } else {
            NytSolutionWords = null;
            NytSolutionKey = null;
        }
    }

    // -------------------------------------------------------------------------
    // Panel width preference
    // -------------------------------------------------------------------------

    function LoadPanelWidthPreference() {
        const SavedWidth = Number(
            GM_getValue(PanelWidthStorageKey, NaN)
        );

        if (Number.isFinite(SavedWidth) && SavedWidth > 0) {
            PanelWidthPreference = SavedWidth;
            return;
        }

        /*
            v1.8 changes the outer layout substantially, so it uses a new
            preference key. If a v1.7 width exists, migrate it once at 75% so
            existing users get the intentionally smaller new default rather
            than inheriting the old, wider panel unchanged.
        */
        const LegacySavedWidth = Number(
            GM_getValue(LegacyPanelWidthStorageKey, NaN)
        );

        if (Number.isFinite(LegacySavedWidth) && LegacySavedWidth > 0) {
            PanelWidthPreference = Math.max(
                MinimumPanelWidth,
                Math.round(LegacySavedWidth * DefaultPanelShrinkRatio)
            );
            SavePanelWidthPreference();
            return;
        }

        PanelWidthPreference = null;
    }

    function SavePanelWidthPreference() {
        if (Number.isFinite(PanelWidthPreference)) {
            GM_setValue(
                PanelWidthStorageKey,
                Math.round(PanelWidthPreference)
            );
        }
    }

    // -------------------------------------------------------------------------
    // Durable puzzle metadata + backup / restore
    // -------------------------------------------------------------------------

    function UpdateCurrentPuzzleMetadata() {
        /*
            Migration and enrichment are deliberately separate concepts:

            - A future migration will change an older stored object's SHAPE.
            - This enrichment pass refreshes canonical facts we can authoritatively
              recover from today's gameData, even when the instance already exists.

            That means a metadata record created before NytSolution was tracked can
            self-heal the next time that same puzzle is loaded. Player-history data
            is intentionally not reconstructed here.
        */
        const Existing = GM_getValue(
            PuzzleMetadataStorageKey,
            {}
        );

        const Updated = {
            ...(Existing && typeof Existing === "object" && !Array.isArray(Existing)
                ? Existing
                : {}),
            Version: PuzzleMetadataVersion,
            PuzzleId: PuzzleStorageId,
            PrintDate: GameData.printDate || null,
            Date: GameData.date || null,
            Sides: Array.isArray(GameData.sides)
                ? [...GameData.sides]
                : [],
            NytSolution: Array.isArray(GameData.ourSolution)
                ? GameData.ourSolution
                    .map(NormalizeWord)
                    .filter(Boolean)
                : [],
            DictionaryCount: Dictionary.length,
            DictionaryHash: HashString(Dictionary.join("\u001E")),
            LastSeenAt: new Date().toISOString()
        };

        GM_setValue(
            PuzzleMetadataStorageKey,
            Updated
        );
    }

    // -------------------------------------------------------------------------
    // Custom dictionary
    // -------------------------------------------------------------------------

    function LoadCustomDictionary() {
        const SavedDictionary = GM_getValue(
            CustomDictionaryStorageKey,
            []
        );

        CustomDictionary = new Map();

        if (Array.isArray(SavedDictionary)) {
            for (const RawEntry of SavedDictionary) {
                const Entry = NormalizeCustomDictionaryEntry(RawEntry);

                if (Entry) {
                    CustomDictionary.set(Entry.Word, Entry);
                }
            }
        }

        const SavedPuzzleWords = GM_getValue(
            CustomWordsStorageKey,
            []
        );

        CustomWordsForCurrentPuzzle = new Set(
            Array.isArray(SavedPuzzleWords)
                ? SavedPuzzleWords
                    .map(NormalizeWord)
                    .filter(Boolean)
                : []
        );
    }

    function NormalizeCustomDictionaryEntry(RawEntry) {
        if (typeof RawEntry === "string") {
            const Word = NormalizeWord(RawEntry);

            return Word
                ? {
                    Word,
                    Provenance: "User",
                    AddedAt: null,
                    FirstAddedPuzzleId: null,
                    FirstAddedPrintDate: null
                }
                : null;
        }

        if (!RawEntry || typeof RawEntry !== "object" || Array.isArray(RawEntry)) {
            return null;
        }

        const Word = NormalizeWord(RawEntry.Word);

        if (!Word) {
            return null;
        }

        return {
            ...RawEntry,
            Word,
            Provenance: RawEntry.Provenance || "User",
            AddedAt: RawEntry.AddedAt || null,
            FirstAddedPuzzleId: RawEntry.FirstAddedPuzzleId || null,
            FirstAddedPrintDate: RawEntry.FirstAddedPrintDate || null
        };
    }

    function SaveCustomDictionary() {
        const Entries = [...CustomDictionary.values()]
            .sort((A, B) => Alphabetically(A.Word, B.Word));

        GM_setValue(
            CustomDictionaryStorageKey,
            Entries
        );

        ScheduleCloudSync();
    }

    function SaveCustomWordsForCurrentPuzzle() {
        GM_setValue(
            CustomWordsStorageKey,
            [...CustomWordsForCurrentPuzzle].sort(Alphabetically)
        );

        ScheduleCloudSync();
    }

    function AddLastInvalidWordToCustomDictionary() {
        const Word = NormalizeWord(LastInvalidWord);

        if (!Word) {
            return;
        }

        if (!CustomDictionary.has(Word)) {
            CustomDictionary.set(
                Word,
                {
                    Word,
                    Provenance: "User",
                    AddedAt: new Date().toISOString(),
                    FirstAddedPuzzleId: PuzzleStorageId,
                    FirstAddedPrintDate: GameData.printDate || null
                }
            );

            SaveCustomDictionary();
        }

        CustomWordsForCurrentPuzzle.add(Word);
        SaveCustomWordsForCurrentPuzzle();

        console.log(
            "[Letter Boxed Cubed] Added custom dictionary word:",
            Word
        );

        RenderPanel();
    }

    function IsStructurallyValidLetterBoxedWord(Word) {
        const Normalized = NormalizeWord(Word);

        if (Normalized.length < 3) {
            return false;
        }

        let PreviousSide = null;

        for (const Letter of Normalized) {
            const Side = PuzzleSideByLetter.get(Letter);

            if (Side === undefined || Side === PreviousSide) {
                return false;
            }

            PreviousSide = Side;
        }

        return true;
    }

    function TrackPotentialCustomDictionaryWord(Word) {
        const Normalized = NormalizeWord(Word);

        if (
            !Normalized ||
            DictionarySet.has(Normalized) ||
            !IsStructurallyValidLetterBoxedWord(Normalized)
        ) {
            return;
        }

        LastInvalidWord = Normalized;

        /*
            If the user has already declared this word valid globally, merely
            attempting it on today's board is enough to retain the puzzle-level
            provenance as well.
        */
        if (CustomDictionary.has(Normalized)) {
            CustomWordsForCurrentPuzzle.add(Normalized);
            SaveCustomWordsForCurrentPuzzle();
        }

        RenderPanel();
    }

    // -------------------------------------------------------------------------
    // Portable GUI state
    // -------------------------------------------------------------------------

    function CreateEmptyGuiState() {
        return {
            Version: GuiStateVersion,
            Settings: {},
            Sections: {}
        };
    }

    function NormalizeTimestamp(Value) {
        if (!Value) {
            return null;
        }

        const Parsed = Date.parse(Value);

        return Number.isFinite(Parsed)
            ? new Date(Parsed).toISOString()
            : null;
    }

    function NormalizeGuiState(RawState) {
        const Result = CreateEmptyGuiState();

        if (!RawState || typeof RawState !== "object" || Array.isArray(RawState)) {
            return Result;
        }

        const RawSettings =
            RawState.Settings &&
            typeof RawState.Settings === "object" &&
            !Array.isArray(RawState.Settings)
                ? RawState.Settings
                : {};

        for (const [Name, RawEntry] of Object.entries(RawSettings)) {
            if (
                !RawEntry ||
                typeof RawEntry !== "object" ||
                Array.isArray(RawEntry) ||
                !Object.prototype.hasOwnProperty.call(RawEntry, "Value")
            ) {
                continue;
            }

            Result.Settings[Name] = {
                Value: structuredClone(RawEntry.Value),
                UpdatedAt: NormalizeTimestamp(RawEntry.UpdatedAt)
            };
        }

        const RawSections =
            RawState.Sections &&
            typeof RawState.Sections === "object" &&
            !Array.isArray(RawState.Sections)
                ? RawState.Sections
                : {};

        for (const [Name, RawEntry] of Object.entries(RawSections)) {
            if (
                !RawEntry ||
                typeof RawEntry !== "object" ||
                Array.isArray(RawEntry) ||
                !Object.prototype.hasOwnProperty.call(RawEntry, "Open")
            ) {
                continue;
            }

            Result.Sections[Name] = {
                Open: Boolean(RawEntry.Open),
                UpdatedAt: NormalizeTimestamp(RawEntry.UpdatedAt)
            };
        }

        return Result;
    }

    function LoadGuiState() {
        const Existing = GM_getValue(
            GuiStateStorageKey,
            null
        );

        GuiState = NormalizeGuiState(Existing);

        /*
            v1.11 consolidates portable GUI preferences into one versioned
            object. Existing values are migrated without inventing timestamps:
            we know their values, but not when the user chose them.
        */
        if (!Existing || typeof Existing !== "object" || Array.isArray(Existing)) {
            const ExistingKeys = typeof GM_listValues === "function"
                ? new Set(GM_listValues())
                : new Set();

            if (ExistingKeys.has(HideParStorageKey)) {
                GuiState.Settings.HidePar = {
                    Value: Boolean(GM_getValue(HideParStorageKey, false)),
                    UpdatedAt: null
                };
            }

            if (ExistingKeys.has(LineDrawingSpeedStorageKey)) {
                const SavedSpeed = Number(
                    GM_getValue(LineDrawingSpeedStorageKey, 1.0)
                );

                if (Number.isFinite(SavedSpeed)) {
                    GuiState.Settings.AnimationSpeed = {
                        Value: Clamp(SavedSpeed, 0, 1),
                        UpdatedAt: null
                    };
                }
            }

            SaveGuiState(false);
        }

        TwofersGrouped = Boolean(
            GetGuiSetting(
                "TwofersGrouped",
                true
            )
        );
    }

    function SaveGuiState(QueueSync = true) {
        if (!GuiState) {
            GuiState = CreateEmptyGuiState();
        }

        GM_setValue(
            GuiStateStorageKey,
            GuiState
        );

        if (QueueSync) {
            ScheduleCloudSync();
        }
    }

    function GetGuiSetting(Name, DefaultValue) {
        const Entry = GuiState?.Settings?.[Name];

        return Entry && Object.prototype.hasOwnProperty.call(Entry, "Value")
            ? Entry.Value
            : DefaultValue;
    }

    function SetGuiSetting(Name, Value) {
        if (!GuiState) {
            GuiState = CreateEmptyGuiState();
        }

        GuiState.Settings[Name] = {
            Value: structuredClone(Value),
            UpdatedAt: new Date().toISOString()
        };

        SaveGuiState();
    }

    function GetGuiSectionOpen(Name) {
        const Entry = GuiState?.Sections?.[Name];

        return Entry && Object.prototype.hasOwnProperty.call(Entry, "Open")
            ? Boolean(Entry.Open)
            : null;
    }

    function SetGuiSectionOpen(Name, Open) {
        if (!GuiState) {
            GuiState = CreateEmptyGuiState();
        }

        const Existing = GuiState.Sections[Name];
        const NormalizedOpen = Boolean(Open);

        if (Existing && Boolean(Existing.Open) === NormalizedOpen) {
            return;
        }

        GuiState.Sections[Name] = {
            Open: NormalizedOpen,
            UpdatedAt: new Date().toISOString()
        };

        SaveGuiState();
    }

    function SaveTwofersGroupedPreference() {
        SetGuiSetting(
            "TwofersGrouped",
            TwofersGrouped
        );
    }

    // -------------------------------------------------------------------------
    // Display preferences
    // -------------------------------------------------------------------------

    function LoadHideParPreference() {
        HidePar = Boolean(
            GetGuiSetting(
                "HidePar",
                GM_getValue(
                    HideParStorageKey,
                    false
                )
            )
        );
    }

    function SaveHideParPreference() {
        /* Legacy write-through keeps rollback compatibility. */
        GM_setValue(
            HideParStorageKey,
            HidePar
        );

        SetGuiSetting(
            "HidePar",
            HidePar
        );
    }

    function ApplyHideParPreference() {
        const GameContainer = document.querySelector(
            ".lb-game-container"
        );

        if (!GameContainer) {
            return;
        }

        GameContainer.classList.toggle(
            "lb-cubed-hide-par",
            HidePar
        );
    }

    // -------------------------------------------------------------------------
    // Animation speed (NYT line drawing)
    // -------------------------------------------------------------------------

    function LoadLineDrawingSpeed() {
        const Saved = Number(
            GetGuiSetting(
                "AnimationSpeed",
                GM_getValue(
                    LineDrawingSpeedStorageKey,
                    1.0
                )
            )
        );

        LineDrawingSpeed = Number.isFinite(Saved)
            ? Clamp(Saved, 0, 1)
            : 1.0;
    }

    function SaveLineDrawingSpeed() {
        const SavedValue = Number(
            LineDrawingSpeed.toFixed(2)
        );

        /* Legacy write-through keeps rollback compatibility. */
        GM_setValue(
            LineDrawingSpeedStorageKey,
            SavedValue
        );

        SetGuiSetting(
            "AnimationSpeed",
            SavedValue
        );
    }

    function InstallLineDrawingSpeedHook() {
        if (NativeRequestAnimationFrame) {
            return;
        }

        /*
            The Letter Boxed board is a canvas, so its line drawing is not a
            CSS transition we can simply shorten. This hook accelerates the
            timestamp supplied to requestAnimationFrame during the short window
            immediately after a likely-valid word submission.

            1.0 = NYT's normal timing.
            0.5 = approximately half-duration.
            0.0 = advance the animation clock far enough to collapse to its end.

            This is intentionally scoped to submission animations rather than
            globally speeding every animation on the NYT page.
        */
        try {
            NativeRequestAnimationFrame =
                PageWindow.requestAnimationFrame.bind(PageWindow);

            PageWindow.requestAnimationFrame = Callback =>
                NativeRequestAnimationFrame(RealTimestamp => {
                    const Active =
                        LineAnimationAcceleration &&
                        RealTimestamp <= LineAnimationAcceleration.RealEnd;

                    if (!Active || LineDrawingSpeed >= 0.999) {
                        return Callback(RealTimestamp);
                    }

                    const SpeedScale = LineDrawingSpeed <= 0.001
                        ? 0.0001
                        : LineDrawingSpeed;

                    const VirtualTimestamp =
                        LineAnimationAcceleration.RealStart +
                        (
                            (RealTimestamp - LineAnimationAcceleration.RealStart) /
                            SpeedScale
                        );

                    return Callback(VirtualTimestamp);
                });
        } catch (Error) {
            NativeRequestAnimationFrame = null;

            console.warn(
                "[Letter Boxed Cubed] Could not install line-drawing animation hook.",
                Error
            );
        }
    }

    function BeginLineDrawingAcceleration() {
        if (LineDrawingSpeed >= 0.999) {
            LineAnimationAcceleration = null;
            return;
        }

        const Now = PageWindow.performance.now();

        LineAnimationAcceleration = {
            RealStart: Now,
            RealEnd: Now + 2500
        };
    }

    function IsLikelyAcceptedSubmission(CurrentChain, InputWord) {
        const Word = NormalizeWord(InputWord);

        if (!DictionarySet.has(Word)) {
            return false;
        }

        if (!CurrentChain.length) {
            return true;
        }

        const PreviousWord = CurrentChain[CurrentChain.length - 1];

        return PreviousWord.slice(-1) === Word[0];
    }

    function GetExportStorageKeys() {
        const AllKeys = typeof GM_listValues === "function"
            ? GM_listValues()
            : [];

        return AllKeys
            .filter(Key =>
                ExportExactStorageKeys.includes(Key) ||
                ExportStoragePrefixes.some(Prefix => Key.startsWith(Prefix))
            )
            .sort(Alphabetically);
    }

    function GetPuzzleIdFromStorageKey(Key) {
        for (const Prefix of ExportStoragePrefixes) {
            if (Key.startsWith(Prefix)) {
                return Key.substring(Prefix.length);
            }
        }

        return null;
    }

    function ParseStoredTwoferKeys(Value) {
        if (!Array.isArray(Value)) {
            return [];
        }

        return Value
            .map(Key => SplitTwoferKey(Key))
            .filter(Parts => Parts.length === 2)
            .map(Parts => [Parts[0], Parts[1]]);
    }

    function BuildNormalizedPuzzleExport(
        PuzzleId,
        StorageSnapshot
    ) {
        const WordKey =
            "LetterBoxedTracker_" + PuzzleId;

        const FoundTwoferKey =
            "LetterBoxedCubed_FoundTwofers_" + PuzzleId;

        const TwoferCacheKeyForPuzzle =
            "LetterBoxedCubed_TwoferCache_" + PuzzleId;

        const MetadataKey =
            PuzzleMetadataPrefix + PuzzleId;

        const CustomWordsKey =
            CustomWordsPrefix + PuzzleId;

        const Metadata =
            StorageSnapshot[MetadataKey] || null;

        const Cache =
            StorageSnapshot[TwoferCacheKeyForPuzzle] || null;

        const IsCurrentPuzzle =
            PuzzleId === PuzzleStorageId;

        const FoundWordsForPuzzle = Array.isArray(
            StorageSnapshot[WordKey]
        )
            ? [...StorageSnapshot[WordKey]]
                .map(NormalizeWord)
                .filter(Boolean)
                .sort(Alphabetically)
            : [];

        const FoundTwofersForPuzzle =
            ParseStoredTwoferKeys(
                StorageSnapshot[FoundTwoferKey]
            );

        const AllTwofersForPuzzle =
            Cache && Array.isArray(Cache.Solutions)
                ? Cache.Solutions
                    .filter(
                        Solution =>
                            Array.isArray(Solution) &&
                            Solution.length === 2
                    )
                    .map(Solution => [
                        NormalizeWord(Solution[0]),
                        NormalizeWord(Solution[1])
                    ])
                : [];

        const CustomWordsForPuzzle = Array.isArray(
            StorageSnapshot[CustomWordsKey]
        )
            ? [...StorageSnapshot[CustomWordsKey]]
                .map(NormalizeWord)
                .filter(Boolean)
                .sort(Alphabetically)
            : [];

        const NytSolution =
            Metadata && Array.isArray(Metadata.NytSolution)
                ? Metadata.NytSolution
                : IsCurrentPuzzle && Array.isArray(GameData.ourSolution)
                    ? GameData.ourSolution
                        .map(NormalizeWord)
                        .filter(Boolean)
                    : [];

        return {
            PuzzleId,
            PrintDate:
                Metadata?.PrintDate ||
                Cache?.PrintDate ||
                (IsCurrentPuzzle ? GameData.printDate || null : null),
            Date:
                Metadata?.Date ||
                (IsCurrentPuzzle ? GameData.date || null : null),
            Sides:
                Array.isArray(Metadata?.Sides)
                    ? Metadata.Sides
                    : Array.isArray(Cache?.Sides)
                        ? Cache.Sides
                        : IsCurrentPuzzle && Array.isArray(GameData.sides)
                            ? [...GameData.sides]
                            : [],
            NytSolution,
            DictionaryCount:
                Metadata?.DictionaryCount ??
                Cache?.DictionaryCount ??
                (IsCurrentPuzzle ? Dictionary.length : null),
            DictionaryHash:
                Metadata?.DictionaryHash ||
                Cache?.DictionaryHash ||
                null,
            FoundWords: FoundWordsForPuzzle,
            FoundTwofers: FoundTwofersForPuzzle,
            AllTwofers: AllTwofersForPuzzle,
            CustomWords: CustomWordsForPuzzle
        };
    }

    function BuildExportData() {
        const Keys = GetExportStorageKeys();
        const StorageSnapshot = {};

        for (const Key of Keys) {
            StorageSnapshot[Key] = GM_getValue(Key, null);
        }

        const PuzzleIds = new Set();

        for (const Key of Keys) {
            const PuzzleId = GetPuzzleIdFromStorageKey(Key);

            if (PuzzleId) {
                PuzzleIds.add(PuzzleId);
            }
        }

        const Puzzles = [...PuzzleIds]
            .map(PuzzleId =>
                BuildNormalizedPuzzleExport(
                    PuzzleId,
                    StorageSnapshot
                )
            )
            .sort((A, B) => {
                if (A.PrintDate && B.PrintDate) {
                    return A.PrintDate.localeCompare(B.PrintDate);
                }

                const NumericA = Number(A.PuzzleId);
                const NumericB = Number(B.PuzzleId);

                if (
                    Number.isFinite(NumericA) &&
                    Number.isFinite(NumericB)
                ) {
                    return NumericA - NumericB;
                }

                return Alphabetically(A.PuzzleId, B.PuzzleId);
            });

        return {
            Format: ExportFormatName,
            FormatVersion: ExportFormatVersion,
            ExportedAt: new Date().toISOString(),
            CurrentPuzzleId: PuzzleStorageId,
            PuzzleCount: Puzzles.length,
            Puzzles,
            GuiState: NormalizeGuiState(
                StorageSnapshot[GuiStateStorageKey]
            ),
            CustomDictionary: Array.isArray(
                StorageSnapshot[CustomDictionaryStorageKey]
            )
                ? StorageSnapshot[CustomDictionaryStorageKey]
                : [],

            /*
                The normalized Puzzles collection is intended for analysis,
                database imports, and public-data workflows.

                StorageSnapshot is intentionally included as well so the same
                file is also a lossless disaster-recovery backup for Cubed's
                Tampermonkey data.
            */
            StorageSnapshot
        };
    }

    function ExportAllData() {
        try {
            /*
                Ensure today's lightweight metadata is current immediately
                before taking the snapshot.
            */
            UpdateCurrentPuzzleMetadata();

            const ExportData = BuildExportData();
            const Json = JSON.stringify(ExportData, null, 2);
            const BlobData = new Blob(
                [Json],
                { type: "text/plain;charset=utf-8" }
            );

            const Url = URL.createObjectURL(BlobData);
            const Link = document.createElement("a");

            const Timestamp = new Date()
                .toISOString()
                .replace(/[:.]/g, "-");

            Link.href = Url;
            Link.download =
                `Letter Boxed Cubed Backup ${Timestamp}.txt`;

            document.body.appendChild(Link);
            Link.click();
            Link.remove();

            setTimeout(
                () => URL.revokeObjectURL(Url),
                1000
            );

            console.log(
                "[Letter Boxed Cubed] Exported backup.",
                {
                    PuzzleCount: ExportData.PuzzleCount,
                    StorageKeys: Object.keys(
                        ExportData.StorageSnapshot
                    ).length
                }
            );
        } catch (Error) {
            console.error(
                "[Letter Boxed Cubed] Export failed.",
                Error
            );

            alert(
                "Letter Boxed Cubed could not export its data. " +
                "Check the developer console for details."
            );
        }
    }

    function MigrateBackupToCurrent(RawBackup) {
        if (
            !RawBackup ||
            RawBackup.Format !== ExportFormatName
        ) {
            throw new Error(
                "This is not a Letter Boxed Cubed backup file."
            );
        }

        let Backup = structuredClone(RawBackup);

        while (Backup.FormatVersion < ExportFormatVersion) {
            const Migration = BackupMigrations[Backup.FormatVersion];

            if (!Migration) {
                throw new Error(
                    `No migration exists from backup schema v${Backup.FormatVersion}.`
                );
            }

            Backup = Migration(Backup);
        }

        if (Backup.FormatVersion > ExportFormatVersion) {
            throw new Error(
                `This backup uses newer schema v${Backup.FormatVersion}; this script supports v${ExportFormatVersion}.`
            );
        }

        return Backup;
    }

    const BackupMigrations = {
        1: MigrateBackupV1ToV2,
        2: MigrateBackupV2ToV3
    };

    function MigrateBackupV1ToV2(V1) {
        /*
            Backup schema v2 adds user-defined custom dictionary data.

            v1 had no such concept, so the honest migration is an empty custom
            dictionary and an empty CustomWords collection on every historical
            puzzle. No custom words are inferred from ordinary FoundWords.
        */
        return {
            ...V1,
            FormatVersion: 2,
            Puzzles: Array.isArray(V1.Puzzles)
                ? V1.Puzzles.map(Puzzle => ({
                    ...Puzzle,
                    CustomWords: Array.isArray(Puzzle.CustomWords)
                        ? Puzzle.CustomWords
                        : []
                }))
                : [],
            CustomDictionary: Array.isArray(V1.CustomDictionary)
                ? V1.CustomDictionary
                : []
        };
    }


    function MigrateBackupV2ToV3(V2) {
        /*
            Backup schema v3 introduces portable GUI state.

            Older backups may contain legacy Hide Par / Animation Speed values
            in StorageSnapshot, but they contain no trustworthy timestamps and
            no persisted tree/group state. Preserve only what was actually
            known and leave UpdatedAt null rather than manufacturing history.
        */
        const Snapshot =
            V2.StorageSnapshot &&
            typeof V2.StorageSnapshot === "object" &&
            !Array.isArray(V2.StorageSnapshot)
                ? structuredClone(V2.StorageSnapshot)
                : {};

        const MigratedGuiState = CreateEmptyGuiState();

        if (Object.prototype.hasOwnProperty.call(Snapshot, HideParStorageKey)) {
            MigratedGuiState.Settings.HidePar = {
                Value: Boolean(Snapshot[HideParStorageKey]),
                UpdatedAt: null
            };
        }

        if (Object.prototype.hasOwnProperty.call(Snapshot, LineDrawingSpeedStorageKey)) {
            const SavedSpeed = Number(
                Snapshot[LineDrawingSpeedStorageKey]
            );

            if (Number.isFinite(SavedSpeed)) {
                MigratedGuiState.Settings.AnimationSpeed = {
                    Value: Clamp(SavedSpeed, 0, 1),
                    UpdatedAt: null
                };
            }
        }

        Snapshot[GuiStateStorageKey] = MigratedGuiState;

        return {
            ...V2,
            FormatVersion: 3,
            GuiState: MigratedGuiState,
            StorageSnapshot: Snapshot
        };
    }

    function IsAllowedExportStorageKey(Key) {
        return (
            ExportExactStorageKeys.includes(Key) ||
            ExportStoragePrefixes.some(
                Prefix => Key.startsWith(Prefix)
            )
        );
    }

    function CloneValue(Value) {
        return Value === undefined
            ? undefined
            : structuredClone(Value);
    }

    function ValuesEqual(A, B) {
        return JSON.stringify(A) === JSON.stringify(B);
    }

    function MergeUniqueWords(LocalValue, IncomingValue) {
        return [...new Set([
            ...(Array.isArray(LocalValue) ? LocalValue : []),
            ...(Array.isArray(IncomingValue) ? IncomingValue : [])
        ]
            .map(NormalizeWord)
            .filter(Boolean))]
            .sort(Alphabetically);
    }

    function MergeUniqueStrings(LocalValue, IncomingValue) {
        return [...new Set([
            ...(Array.isArray(LocalValue) ? LocalValue : []),
            ...(Array.isArray(IncomingValue) ? IncomingValue : [])
        ]
            .map(Value => String(Value || ""))
            .filter(Boolean))]
            .sort(Alphabetically);
    }

    function GetTimestampMilliseconds(Value) {
        if (!Value) {
            return null;
        }

        const Parsed = Date.parse(Value);
        return Number.isFinite(Parsed) ? Parsed : null;
    }

    function MergeStampedEntry(LocalEntry, IncomingEntry, ValueProperty) {
        if (!LocalEntry) {
            return CloneValue(IncomingEntry);
        }

        if (!IncomingEntry) {
            return CloneValue(LocalEntry);
        }

        const LocalTime = GetTimestampMilliseconds(LocalEntry.UpdatedAt);
        const IncomingTime = GetTimestampMilliseconds(IncomingEntry.UpdatedAt);

        if (
            IncomingTime !== null &&
            (LocalTime === null || IncomingTime > LocalTime)
        ) {
            return CloneValue(IncomingEntry);
        }

        if (
            LocalTime !== null &&
            (IncomingTime === null || LocalTime >= IncomingTime)
        ) {
            return CloneValue(LocalEntry);
        }

        /*
            Both timestamps are unknown. Prefer the local value so importing an
            old backup cannot silently change an equally old local preference.
        */
        return Object.prototype.hasOwnProperty.call(LocalEntry, ValueProperty)
            ? CloneValue(LocalEntry)
            : CloneValue(IncomingEntry);
    }

    function MergeGuiStates(LocalValue, IncomingValue) {
        const Local = NormalizeGuiState(LocalValue);
        const Incoming = NormalizeGuiState(IncomingValue);
        const Result = CreateEmptyGuiState();

        const SettingNames = new Set([
            ...Object.keys(Local.Settings),
            ...Object.keys(Incoming.Settings)
        ]);

        for (const Name of SettingNames) {
            const Merged = MergeStampedEntry(
                Local.Settings[Name],
                Incoming.Settings[Name],
                "Value"
            );

            if (Merged) {
                Result.Settings[Name] = Merged;
            }
        }

        const SectionNames = new Set([
            ...Object.keys(Local.Sections),
            ...Object.keys(Incoming.Sections)
        ]);

        for (const Name of SectionNames) {
            const Merged = MergeStampedEntry(
                Local.Sections[Name],
                Incoming.Sections[Name],
                "Open"
            );

            if (Merged) {
                Result.Sections[Name] = Merged;
            }
        }

        return Result;
    }

    function MergeCustomDictionaryValues(LocalValue, IncomingValue) {
        const Entries = new Map();

        const MergeEntry = Entry => {
            const Existing = Entries.get(Entry.Word);

            if (!Existing) {
                Entries.set(Entry.Word, Entry);
                return;
            }

            const ExistingTime = GetTimestampMilliseconds(Existing.AddedAt);
            const EntryTime = GetTimestampMilliseconds(Entry.AddedAt);

            let AddedAt = null;
            let FirstAddedPuzzleId = null;
            let FirstAddedPrintDate = null;

            if (ExistingTime !== null && EntryTime !== null) {
                const Earlier = EntryTime < ExistingTime
                    ? Entry
                    : Existing;

                AddedAt = Earlier.AddedAt;
                FirstAddedPuzzleId = Earlier.FirstAddedPuzzleId || null;
                FirstAddedPrintDate = Earlier.FirstAddedPrintDate || null;
            } else if (ExistingTime === null && EntryTime === null) {
                /*
                    Both timestamps are historically unknown. Preserve any
                    explicit first-puzzle provenance we do have, but do not
                    fabricate a timestamp.
                */
                FirstAddedPuzzleId =
                    Existing.FirstAddedPuzzleId ||
                    Entry.FirstAddedPuzzleId ||
                    null;

                FirstAddedPrintDate =
                    Existing.FirstAddedPrintDate ||
                    Entry.FirstAddedPrintDate ||
                    null;
            } else {
                /*
                    One record predates timestamp tracking. We cannot prove the
                    timestamped record was the first addition, so the merged
                    first-addition timestamp/provenance remains unknown unless
                    the older unknown-time record itself carries provenance.
                */
                const UnknownTimeEntry = ExistingTime === null
                    ? Existing
                    : Entry;

                FirstAddedPuzzleId =
                    UnknownTimeEntry.FirstAddedPuzzleId ||
                    null;

                FirstAddedPrintDate =
                    UnknownTimeEntry.FirstAddedPrintDate ||
                    null;
            }

            Entries.set(
                Entry.Word,
                {
                    ...Existing,
                    ...Entry,
                    Word: Entry.Word,
                    Provenance:
                        Existing.Provenance ||
                        Entry.Provenance ||
                        "User",
                    AddedAt,
                    FirstAddedPuzzleId,
                    FirstAddedPrintDate
                }
            );
        };

        const AddEntries = Value => {
            if (!Array.isArray(Value)) {
                return;
            }

            for (const RawEntry of Value) {
                const Entry = NormalizeCustomDictionaryEntry(RawEntry);

                if (Entry) {
                    MergeEntry(Entry);
                }
            }
        };

        AddEntries(LocalValue);
        AddEntries(IncomingValue);

        return [...Entries.values()]
            .sort((A, B) => Alphabetically(A.Word, B.Word));
    }

    function HasUsefulValue(Value) {
        if (Value === null || Value === undefined || Value === "") {
            return false;
        }

        if (Array.isArray(Value)) {
            return Value.length > 0;
        }

        return true;
    }

    function MergePuzzleMetadataValues(LocalValue, IncomingValue) {
        if (!LocalValue || typeof LocalValue !== "object" || Array.isArray(LocalValue)) {
            return CloneValue(IncomingValue);
        }

        if (!IncomingValue || typeof IncomingValue !== "object" || Array.isArray(IncomingValue)) {
            return CloneValue(LocalValue);
        }

        const LocalTime = GetTimestampMilliseconds(LocalValue.LastSeenAt) ?? -1;
        const IncomingTime = GetTimestampMilliseconds(IncomingValue.LastSeenAt) ?? -1;
        const Newer = IncomingTime > LocalTime ? IncomingValue : LocalValue;
        const Older = Newer === IncomingValue ? LocalValue : IncomingValue;

        const Result = {
            ...Older,
            ...Newer,
            Version: Math.max(
                Number(LocalValue.Version) || 0,
                Number(IncomingValue.Version) || 0
            )
        };

        for (const Key of [
            "PuzzleId",
            "PrintDate",
            "Date",
            "Sides",
            "NytSolution",
            "DictionaryCount",
            "DictionaryHash"
        ]) {
            if (!HasUsefulValue(Result[Key]) && HasUsefulValue(Older[Key])) {
                Result[Key] = CloneValue(Older[Key]);
            }
        }

        const LastSeenTimes = [
            LocalValue.LastSeenAt,
            IncomingValue.LastSeenAt
        ]
            .map(Value => ({
                Value,
                Time: GetTimestampMilliseconds(Value)
            }))
            .filter(Item => Item.Time !== null)
            .sort((A, B) => B.Time - A.Time);

        Result.LastSeenAt = LastSeenTimes[0]?.Value || null;

        return Result;
    }

    function MergeTwoferCacheValues(LocalValue, IncomingValue) {
        if (!LocalValue || typeof LocalValue !== "object" || Array.isArray(LocalValue)) {
            return CloneValue(IncomingValue);
        }

        if (!IncomingValue || typeof IncomingValue !== "object" || Array.isArray(IncomingValue)) {
            return CloneValue(LocalValue);
        }

        const LocalSolutions = Array.isArray(LocalValue.Solutions)
            ? LocalValue.Solutions.length
            : 0;

        const IncomingSolutions = Array.isArray(IncomingValue.Solutions)
            ? IncomingValue.Solutions.length
            : 0;

        const LocalVersion = Number(LocalValue.Version) || 0;
        const IncomingVersion = Number(IncomingValue.Version) || 0;

        if (IncomingVersion > LocalVersion) {
            return CloneValue(IncomingValue);
        }

        if (LocalVersion > IncomingVersion) {
            return CloneValue(LocalValue);
        }

        return IncomingSolutions > LocalSolutions
            ? CloneValue(IncomingValue)
            : CloneValue(LocalValue);
    }

    function MergeStorageValue(Key, LocalValue, IncomingValue) {
        if (LocalValue === null || LocalValue === undefined) {
            return CloneValue(IncomingValue);
        }

        if (IncomingValue === null || IncomingValue === undefined) {
            return CloneValue(LocalValue);
        }

        if (
            Key.startsWith("LetterBoxedTracker_") ||
            Key.startsWith(CustomWordsPrefix)
        ) {
            return MergeUniqueWords(LocalValue, IncomingValue);
        }

        if (Key.startsWith("LetterBoxedCubed_FoundTwofers_")) {
            return MergeUniqueStrings(LocalValue, IncomingValue);
        }

        if (Key === CustomDictionaryStorageKey) {
            return MergeCustomDictionaryValues(LocalValue, IncomingValue);
        }

        if (Key === GuiStateStorageKey) {
            return MergeGuiStates(LocalValue, IncomingValue);
        }

        if (Key.startsWith(PuzzleMetadataPrefix)) {
            return MergePuzzleMetadataValues(LocalValue, IncomingValue);
        }

        if (Key.startsWith("LetterBoxedCubed_TwoferCache_")) {
            return MergeTwoferCacheValues(LocalValue, IncomingValue);
        }

        if (DeviceLocalStorageKeys.includes(Key)) {
            /*
                Physical layout preferences are local to a device/window. Keep
                an existing local value; only restore one if this device has no
                preference yet.
            */
            return CloneValue(LocalValue);
        }

        /*
            Legacy portable settings are superseded by GuiState in v3. Keep a
            local copy when both exist; GuiState determines the effective value.
        */
        if (
            Key === HideParStorageKey ||
            Key === LineDrawingSpeedStorageKey
        ) {
            return CloneValue(LocalValue);
        }

        return CloneValue(LocalValue);
    }

    function MergeBackupIntoStorage(
        RawBackup,
        { IncludeDeviceState = true } = {}
    ) {
        const Backup = MigrateBackupToCurrent(RawBackup);
        const Snapshot = Backup.StorageSnapshot;

        if (!Snapshot || typeof Snapshot !== "object" || Array.isArray(Snapshot)) {
            throw new Error(
                "This is not a Letter Boxed Cubed backup file."
            );
        }

        let ChangedKeys = 0;
        let ConsideredKeys = 0;

        for (const Key of Object.keys(Snapshot)) {
            if (!IsAllowedExportStorageKey(Key)) {
                continue;
            }

            if (!IncludeDeviceState && DeviceLocalStorageKeys.includes(Key)) {
                continue;
            }

            ConsideredKeys++;

            const LocalValue = GM_getValue(Key, null);
            const MergedValue = MergeStorageValue(
                Key,
                LocalValue,
                Snapshot[Key]
            );

            if (!ValuesEqual(LocalValue, MergedValue)) {
                GM_setValue(
                    Key,
                    MergedValue
                );
                ChangedKeys++;
            }
        }

        return {
            ConsideredKeys,
            ChangedKeys
        };
    }

    function PromptForImport() {
        const Input = document.createElement("input");
        Input.type = "file";
        Input.accept = ".txt,.json,text/plain,application/json";
        Input.style.display = "none";

        Input.addEventListener(
            "change",
            async () => {
                const File = Input.files?.[0];

                Input.remove();

                if (!File) {
                    return;
                }

                try {
                    const Text = await File.text();
                    const RawBackup = JSON.parse(Text);
                    const Backup = MigrateBackupToCurrent(RawBackup);

                    if (
                        !Backup.StorageSnapshot ||
                        typeof Backup.StorageSnapshot !== "object" ||
                        Array.isArray(Backup.StorageSnapshot)
                    ) {
                        throw new Error(
                            "This is not a Letter Boxed Cubed backup file."
                        );
                    }

                    const Keys = Object.keys(
                        Backup.StorageSnapshot
                    );

                    const Confirmed = confirm(
                        `Merge ${Keys.length.toLocaleString()} stored Letter Boxed Cubed records` +
                        `${Backup.ExportedAt ? ` from ${Backup.ExportedAt}` : ""}?\n\n` +
                        "Discovery data is combined rather than overwritten: found words, " +
                        "solved twofers, custom words, and custom dictionary entries are unioned. " +
                        "Portable GUI settings use their per-setting timestamps."
                    );

                    if (!Confirmed) {
                        return;
                    }

                    const MergeStats = MergeBackupIntoStorage(
                        Backup,
                        { IncludeDeviceState: true }
                    );

                    alert(
                        "Letter Boxed Cubed backup merged successfully. " +
                        `${MergeStats.ChangedKeys.toLocaleString()} stored record(s) changed. ` +
                        "The page will now reload."
                    );

                    location.reload();
                } catch (Error) {
                    console.error(
                        "[Letter Boxed Cubed] Import failed.",
                        Error
                    );

                    alert(
                        "Letter Boxed Cubed could not import that file. " +
                        "Make sure it is an unmodified Cubed backup."
                    );
                }
            },
            { once: true }
        );

        document.body.appendChild(Input);
        Input.click();
    }


    // -------------------------------------------------------------------------
    // Cloud history browser
    // -------------------------------------------------------------------------

    function CompareHistoryPuzzles(A, B) {
        const DateA = String(A?.PrintDate || "");
        const DateB = String(B?.PrintDate || "");

        if (DateA && DateB && DateA !== DateB) {
            return DateA.localeCompare(DateB);
        }

        if (DateA && !DateB) {
            return -1;
        }

        if (!DateA && DateB) {
            return 1;
        }

        const NumericA = Number(A?.PuzzleId);
        const NumericB = Number(B?.PuzzleId);

        if (Number.isFinite(NumericA) && Number.isFinite(NumericB)) {
            return NumericA - NumericB;
        }

        return Alphabetically(
            A?.PuzzleId || "",
            B?.PuzzleId || ""
        );
    }

    function GetInitialHistoryPuzzleIndex(Puzzles) {
        if (!Puzzles.length) {
            return -1;
        }

        const CurrentPrintDate = String(
            GameData?.printDate || ""
        );

        if (CurrentPrintDate) {
            let PreviousDateIndex = -1;

            for (let Index = 0; Index < Puzzles.length; Index++) {
                const PrintDate = String(
                    Puzzles[Index]?.PrintDate || ""
                );

                if (PrintDate && PrintDate < CurrentPrintDate) {
                    PreviousDateIndex = Index;
                }
            }

            if (PreviousDateIndex >= 0) {
                return PreviousDateIndex;
            }
        }

        const CurrentNumericId = Number(PuzzleStorageId);

        if (Number.isFinite(CurrentNumericId)) {
            let PreviousIdIndex = -1;

            for (let Index = 0; Index < Puzzles.length; Index++) {
                const NumericId = Number(
                    Puzzles[Index]?.PuzzleId
                );

                if (
                    Number.isFinite(NumericId) &&
                    NumericId < CurrentNumericId
                ) {
                    PreviousIdIndex = Index;
                }
            }

            if (PreviousIdIndex >= 0) {
                return PreviousIdIndex;
            }
        }

        const CurrentIndex = Puzzles.findIndex(
            Puzzle =>
                String(Puzzle?.PuzzleId || "") ===
                String(PuzzleStorageId || "")
        );

        if (CurrentIndex > 0) {
            return CurrentIndex - 1;
        }

        return Puzzles.length - 1;
    }

    function SetBrowseHistoryButtonLoading(IsLoading) {
        const Button = document.getElementById(
            BrowseHistoryButtonId
        );

        if (!Button) {
            return;
        }

        Button.disabled = Boolean(IsLoading);
        Button.textContent = IsLoading
            ? "Loading..."
            : "Browse History";
    }

    async function OpenCloudHistoryBrowser() {
        if (!GoogleDriveConfig?.Enabled) {
            alert(
                "Google Drive sync is not configured.\n\n" +
                "Use Drive: Setup first, then Browse History can read the synced cloud backup."
            );
            return;
        }

        if (document.getElementById(HistoryOverlayId)) {
            return;
        }

        SetBrowseHistoryButtonLoading(true);

        try {
            const Remote = await GoogleDriveBridgeRequest("Read");

            if (!Remote.Data) {
                alert(
                    "The Google Drive backup is currently empty.\n\n" +
                    "Run a Drive sync first, then try Browse History again."
                );
                return;
            }

            const Backup = MigrateBackupToCurrent(
                Remote.Data
            );

            const Puzzles = (
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

            if (!Puzzles.length) {
                alert(
                    "The synced Google Drive backup does not contain any puzzle history yet."
                );
                return;
            }

            const InitialIndex =
                GetInitialHistoryPuzzleIndex(Puzzles);

            CreateHistoryBrowser(
                Puzzles,
                InitialIndex,
                Number(Remote.Revision) || 0
            );
        } catch (Error) {
            console.error(
                "[Letter Boxed Cubed] Could not browse Google Drive history.",
                Error
            );

            alert(
                "Letter Boxed Cubed could not load the Google Drive history.\n\n" +
                (Error?.message || String(Error))
            );
        } finally {
            SetBrowseHistoryButtonLoading(false);
        }
    }

    function CreateHistoryBrowser(
        Puzzles,
        InitialIndex,
        CloudRevision
    ) {
        const Existing = document.getElementById(
            HistoryOverlayId
        );

        if (Existing) {
            Existing.remove();
        }

        const Overlay = document.createElement("div");
        Overlay.id = HistoryOverlayId;

        const Modal = document.createElement("section");
        Modal.className = "lb-cubed-history-modal";

        const Header = document.createElement("div");
        Header.className = "lb-cubed-history-header";

        const HeadingBlock = document.createElement("div");
        HeadingBlock.className = "lb-cubed-history-heading-block";

        const Heading = document.createElement("h2");
        Heading.className = "lb-cubed-history-title";
        Heading.textContent = "Letter Boxed Cubed History";

        const CloudLabel = document.createElement("div");
        CloudLabel.className = "lb-cubed-history-cloud-label";
        CloudLabel.textContent =
            `Google Drive revision ${CloudRevision.toLocaleString()}`;

        HeadingBlock.append(
            Heading,
            CloudLabel
        );

        const CloseButton = document.createElement("button");
        CloseButton.type = "button";
        CloseButton.className =
            "lb-cubed-header-button lb-cubed-history-close";
        CloseButton.textContent = "Close";
        CloseButton.title = "Close history browser";

        Header.append(
            HeadingBlock,
            CloseButton
        );

        const Navigation = document.createElement("div");
        Navigation.className = "lb-cubed-history-navigation";

        const FirstButton = document.createElement("button");
        const PreviousButton = document.createElement("button");
        const NextButton = document.createElement("button");
        const LastButton = document.createElement("button");

        for (const Button of [
            FirstButton,
            PreviousButton,
            NextButton,
            LastButton
        ]) {
            Button.type = "button";
            Button.className =
                "lb-cubed-header-button lb-cubed-history-nav-button";
        }

        FirstButton.textContent = "<<";
        FirstButton.title = "First retained puzzle";
        PreviousButton.textContent = "<";
        PreviousButton.title = "Previous puzzle";
        NextButton.textContent = ">";
        NextButton.title = "Next puzzle";
        LastButton.textContent = ">>";
        LastButton.title = "Last retained puzzle";

        const PositionLabel = document.createElement("div");
        PositionLabel.className =
            "lb-cubed-history-position";

        Navigation.append(
            FirstButton,
            PreviousButton,
            PositionLabel,
            NextButton,
            LastButton
        );

        const Content = document.createElement("div");
        Content.className = "lb-cubed-history-content";

        Modal.append(
            Header,
            Navigation,
            Content
        );

        Overlay.appendChild(Modal);
        document.body.appendChild(Overlay);

        let CurrentIndex = Clamp(
            Number(InitialIndex) || 0,
            0,
            Puzzles.length - 1
        );

        const RenderCurrent = () => {
            const Puzzle = Puzzles[CurrentIndex];

            RenderHistoryPuzzle(
                Content,
                Puzzle
            );

            const DateText =
                Puzzle?.Date ||
                Puzzle?.PrintDate ||
                `Puzzle ${Puzzle?.PuzzleId || "?"}`;

            PositionLabel.textContent =
                `${DateText}  (${(CurrentIndex + 1).toLocaleString()} / ${Puzzles.length.toLocaleString()})`;

            FirstButton.disabled =
                CurrentIndex === 0;
            PreviousButton.disabled =
                CurrentIndex === 0;
            NextButton.disabled =
                CurrentIndex === Puzzles.length - 1;
            LastButton.disabled =
                CurrentIndex === Puzzles.length - 1;

            Content.scrollTop = 0;
        };

        const HandleKeyDown = Event => {
            if (Event.key === "Escape") {
                Event.preventDefault();
                Close();
            }
        };

        const Close = () => {
            document.removeEventListener(
                "keydown",
                HandleKeyDown,
                true
            );
            Overlay.remove();
        };

        FirstButton.addEventListener(
            "click",
            () => {
                CurrentIndex = 0;
                RenderCurrent();
            }
        );

        PreviousButton.addEventListener(
            "click",
            () => {
                if (CurrentIndex > 0) {
                    CurrentIndex--;
                    RenderCurrent();
                }
            }
        );

        NextButton.addEventListener(
            "click",
            () => {
                if (CurrentIndex < Puzzles.length - 1) {
                    CurrentIndex++;
                    RenderCurrent();
                }
            }
        );

        LastButton.addEventListener(
            "click",
            () => {
                CurrentIndex = Puzzles.length - 1;
                RenderCurrent();
            }
        );

        CloseButton.addEventListener(
            "click",
            Close
        );

        Overlay.addEventListener(
            "click",
            Event => {
                if (Event.target === Overlay) {
                    Close();
                }
            }
        );

        document.addEventListener(
            "keydown",
            HandleKeyDown,
            true
        );

        RenderCurrent();
    }

    function RenderHistoryPuzzle(
        Container,
        Puzzle
    ) {
        Container.replaceChildren();

        const FoundWordsForPuzzle =
            [...new Set(
                Array.isArray(Puzzle?.FoundWords)
                    ? Puzzle.FoundWords
                        .map(NormalizeWord)
                        .filter(Boolean)
                    : []
            )].sort(Alphabetically);

        const CustomWordsForPuzzle =
            [...new Set(
                Array.isArray(Puzzle?.CustomWords)
                    ? Puzzle.CustomWords
                        .map(NormalizeWord)
                        .filter(Boolean)
                    : []
            )].sort(Alphabetically);

        const FoundTwofersForPuzzle =
            Array.isArray(Puzzle?.FoundTwofers)
                ? Puzzle.FoundTwofers
                    .filter(
                        Pair =>
                            Array.isArray(Pair) &&
                            Pair.length === 2
                    )
                    .map(Pair => [
                        NormalizeWord(Pair[0]),
                        NormalizeWord(Pair[1])
                    ])
                    .filter(
                        Pair =>
                            Pair[0] &&
                            Pair[1]
                    )
                    .sort(
                        (A, B) =>
                            Alphabetically(A[0], B[0]) ||
                            Alphabetically(A[1], B[1])
                    )
                : [];

        const PuzzleHeader = document.createElement("div");
        PuzzleHeader.className =
            "lb-cubed-history-puzzle-header";

        const PuzzleTitle = document.createElement("h3");
        PuzzleTitle.className =
            "lb-cubed-history-puzzle-title";
        PuzzleTitle.textContent =
            Puzzle?.Date ||
            Puzzle?.PrintDate ||
            `Puzzle ${Puzzle?.PuzzleId || "?"}`;

        const PuzzleMeta = document.createElement("div");
        PuzzleMeta.className =
            "lb-cubed-history-puzzle-meta";

        const MetaParts = [];

        if (Puzzle?.PuzzleId) {
            MetaParts.push(
                `Puzzle ${Puzzle.PuzzleId}`
            );
        }

        if (
            Array.isArray(Puzzle?.Sides) &&
            Puzzle.Sides.length
        ) {
            MetaParts.push(
                Puzzle.Sides.join(" | ")
            );
        }

        PuzzleMeta.textContent =
            MetaParts.join(" · ");

        PuzzleHeader.append(
            PuzzleTitle,
            PuzzleMeta
        );

        const Stats = document.createElement("div");
        Stats.className =
            "lb-cubed-history-stat-grid";

        const TotalCount = Number(
            Puzzle?.DictionaryCount
        );

        const CompletionText =
            Number.isFinite(TotalCount) &&
            TotalCount > 0
                ? `${FoundWordsForPuzzle.length.toLocaleString()} / ${TotalCount.toLocaleString()} (${((FoundWordsForPuzzle.length / TotalCount) * 100).toFixed(1)}%)`
                : `${FoundWordsForPuzzle.length.toLocaleString()} found`;

        let LongestFound = "-";

        if (FoundWordsForPuzzle.length) {
            const LongestLength = Math.max(
                ...FoundWordsForPuzzle.map(
                    Word => Word.length
                )
            );

            LongestFound = FoundWordsForPuzzle
                .filter(
                    Word =>
                        Word.length === LongestLength
                )
                .join(", ");
        }

        AddHistoryStat(
            Stats,
            "Completion",
            CompletionText
        );

        AddHistoryStat(
            Stats,
            "Longest Found",
            LongestFound
        );

        const Sections = document.createElement("div");
        Sections.className =
            "lb-cubed-history-sections";

        Sections.append(
            CreateHistoryWordSection(
                `Found Words (${FoundWordsForPuzzle.length.toLocaleString()})`,
                FoundWordsForPuzzle
            ),
            CreateHistoryTwoferSection(
                `Solved Twofers (${FoundTwofersForPuzzle.length.toLocaleString()})`,
                FoundTwofersForPuzzle
            )
        );

        if (CustomWordsForPuzzle.length) {
            Sections.appendChild(
                CreateHistoryWordSection(
                    `Custom Words (${CustomWordsForPuzzle.length.toLocaleString()})`,
                    CustomWordsForPuzzle,
                    "lb-cubed-history-custom-word"
                )
            );
        }

        Container.append(
            PuzzleHeader,
            Stats,
            Sections
        );
    }

    function AddHistoryStat(
        Container,
        Label,
        Value
    ) {
        const Card = document.createElement("div");
        Card.className =
            "lb-cubed-stat lb-cubed-history-stat";

        const ValueElement = document.createElement("div");
        ValueElement.className =
            "lb-cubed-stat-value";
        ValueElement.textContent = Value;

        const LabelElement = document.createElement("div");
        LabelElement.className =
            "lb-cubed-stat-label";
        LabelElement.textContent = Label;

        Card.append(
            ValueElement,
            LabelElement
        );

        Container.appendChild(Card);
    }

    function CreateHistoryWordSection(
        Title,
        Words,
        ExtraWordClass = ""
    ) {
        const Section = document.createElement("section");
        Section.className =
            "lb-cubed-history-section";

        const Heading = document.createElement("h4");
        Heading.className =
            "lb-cubed-history-section-title";
        Heading.textContent = Title;

        const Grid = document.createElement("div");
        Grid.className =
            "lb-cubed-history-word-grid";

        if (!Words.length) {
            const Empty = document.createElement("div");
            Empty.className =
                "lb-cubed-history-empty";
            Empty.textContent = "None.";
            Grid.appendChild(Empty);
        } else {
            for (const Word of Words) {
                const Item = document.createElement("div");
                Item.className =
                    `lb-cubed-word lb-cubed-found-word ${ExtraWordClass}`.trim();
                Item.textContent = Word;
                Grid.appendChild(Item);
            }
        }

        Section.append(
            Heading,
            Grid
        );

        return Section;
    }

    function CreateHistoryTwoferSection(
        Title,
        TwofersForPuzzle
    ) {
        const Section = document.createElement("section");
        Section.className =
            "lb-cubed-history-section";

        const Heading = document.createElement("h4");
        Heading.className =
            "lb-cubed-history-section-title";
        Heading.textContent = Title;

        const Grid = document.createElement("div");
        Grid.className =
            "lb-cubed-history-twofer-grid";

        if (!TwofersForPuzzle.length) {
            const Empty = document.createElement("div");
            Empty.className =
                "lb-cubed-history-empty";
            Empty.textContent = "None.";
            Grid.appendChild(Empty);
        } else {
            for (const Pair of TwofersForPuzzle) {
                const Row = document.createElement("div");
                Row.className =
                    "lb-cubed-history-twofer-row";

                const First = document.createElement("span");
                First.className =
                    "lb-cubed-twofer-word lb-cubed-twofer-revealed";
                First.textContent = Pair[0];

                const Arrow = document.createElement("span");
                Arrow.className =
                    "lb-cubed-twofer-arrow";
                Arrow.textContent = "→";

                const Second = document.createElement("span");
                Second.className =
                    "lb-cubed-twofer-word lb-cubed-twofer-revealed";
                Second.textContent = Pair[1];

                Row.append(
                    First,
                    Arrow,
                    Second
                );

                Grid.appendChild(Row);
            }
        }

        Section.append(
            Heading,
            Grid
        );

        return Section;
    }

    // -------------------------------------------------------------------------
    // Google Drive cloud sync (via user-owned Apps Script bridge)
    // -------------------------------------------------------------------------

    function LoadGoogleDriveConfig() {
        const Saved = GM_getValue(
            GoogleDriveConfigStorageKey,
            null
        );

        GoogleDriveConfig = NormalizeGoogleDriveConfig(Saved);
        CloudSyncStatus = GoogleDriveConfig?.Enabled
            ? "Ready"
            : "Off";
    }

    function NormalizeGoogleDriveConfig(RawConfig) {
        if (!RawConfig || typeof RawConfig !== "object" || Array.isArray(RawConfig)) {
            return null;
        }

        const Endpoint = String(RawConfig.Endpoint || "").trim();
        const Secret = String(RawConfig.Secret || "").trim();

        if (!Endpoint || !Secret) {
            return null;
        }

        return {
            Version: GoogleDriveConfigVersion,
            Endpoint,
            Secret,
            Enabled: RawConfig.Enabled !== false
        };
    }

    function SaveGoogleDriveConfig() {
        GM_setValue(
            GoogleDriveConfigStorageKey,
            GoogleDriveConfig
        );
    }

    function ConfigureGoogleDriveSync() {
        const ExistingEndpoint = GoogleDriveConfig?.Endpoint || "";
        const EndpointInput = prompt(
            "Google Drive sync uses a small Google Apps Script bridge that you own.\n\n" +
            "Paste its deployed Web App URL (/exec) here. Leave this blank to disconnect Drive sync.",
            ExistingEndpoint
        );

        if (EndpointInput === null) {
            return;
        }

        const Endpoint = EndpointInput.trim();

        if (!Endpoint) {
            if (
                GoogleDriveConfig &&
                confirm("Disconnect Google Drive sync on this browser?")
            ) {
                GoogleDriveConfig = null;
                SaveGoogleDriveConfig();
                CloudSyncStatus = "Off";
                LastCloudSyncError = null;
                UpdateGoogleDriveButton();
            }
            return;
        }

        if (!/^https:\/\/script\.google\.com\/macros\/s\/.+\/exec(?:\?.*)?$/i.test(Endpoint)) {
            alert(
                "That does not look like a deployed Google Apps Script Web App URL. " +
                "It should begin with https://script.google.com/macros/s/ and end with /exec."
            );
            return;
        }

        const SecretInput = prompt(
            "Paste the LBC sync secret printed by the bridge's Setup() function.",
            GoogleDriveConfig?.Secret || ""
        );

        if (SecretInput === null) {
            return;
        }

        const Secret = SecretInput.trim();

        if (!Secret) {
            alert("A non-empty sync secret is required.");
            return;
        }

        GoogleDriveConfig = {
            Version: GoogleDriveConfigVersion,
            Endpoint,
            Secret,
            Enabled: true
        };

        SaveGoogleDriveConfig();
        CloudSyncStatus = "Ready";
        LastCloudSyncError = null;
        UpdateGoogleDriveButton();

        SyncWithGoogleDrive({ Manual: true });
    }

    function ScheduleCloudSync(DelayMs = CloudSyncDebounceMs) {
        if (!GoogleDriveConfig?.Enabled) {
            return;
        }

        if (CloudSyncTimer) {
            clearTimeout(CloudSyncTimer);
        }

        CloudSyncTimer = setTimeout(
            () => {
                CloudSyncTimer = null;
                SyncWithGoogleDrive();
            },
            Math.max(0, DelayMs)
        );
    }

    function BuildCloudSyncData() {
        UpdateCurrentPuzzleMetadata();

        const Data = BuildExportData();

        /*
            Manual backups retain device-local layout preferences. Cloud sync
            deliberately omits them so a laptop cannot rewrite a desktop's
            preferred physical panel width (and vice versa).
        */
        for (const Key of DeviceLocalStorageKeys) {
            delete Data.StorageSnapshot[Key];
        }

        return Data;
    }

    function GoogleDriveBridgeRequest(Action, Payload = {}) {
        if (
            !GoogleDriveConfig?.Enabled ||
            typeof GM_xmlhttpRequest !== "function"
        ) {
            return Promise.reject(
                new Error("Google Drive sync is not configured.")
            );
        }

        return new Promise((Resolve, Reject) => {
            GM_xmlhttpRequest({
                method: "POST",
                url: GoogleDriveConfig.Endpoint,
                headers: {
                    "Content-Type": "text/plain;charset=UTF-8"
                },
                data: JSON.stringify({
                    ProtocolVersion: CloudSyncProtocolVersion,
                    Secret: GoogleDriveConfig.Secret,
                    Action,
                    ...Payload
                }),
                timeout: 30000,
                onload: Response => {
                    try {
                        if (Response.status < 200 || Response.status >= 300) {
                            throw new Error(
                                `Google Drive bridge returned HTTP ${Response.status}.`
                            );
                        }

                        const Parsed = JSON.parse(Response.responseText);

                        if (!Parsed || typeof Parsed !== "object") {
                            throw new Error(
                                "Google Drive bridge returned an invalid response."
                            );
                        }

                        if (Parsed.Status === "error") {
                            throw new Error(
                                Parsed.Message || "Google Drive bridge reported an error."
                            );
                        }

                        Resolve(Parsed);
                    } catch (Error) {
                        Reject(Error);
                    }
                },
                onerror: () => Reject(
                    new Error("Could not reach the Google Drive sync bridge.")
                ),
                ontimeout: () => Reject(
                    new Error("Google Drive sync timed out.")
                )
            });
        });
    }

    async function SyncWithGoogleDrive({ Manual = false } = {}) {
        if (!GoogleDriveConfig?.Enabled) {
            if (Manual) {
                ConfigureGoogleDriveSync();
            }
            return;
        }

        if (CloudSyncInFlight) {
            CloudSyncPending = true;
            return;
        }

        CloudSyncInFlight = true;
        CloudSyncPending = false;
        CloudSyncStatus = "Syncing";
        LastCloudSyncError = null;
        UpdateGoogleDriveButton();

        try {
            let Completed = false;

            for (let Attempt = 0; Attempt < 3 && !Completed; Attempt++) {
                const Remote = await GoogleDriveBridgeRequest("Read");
                const RemoteRevision = Number(Remote.Revision) || 0;
                let RemoteChangedLocal = false;

                if (Remote.Data) {
                    const RemoteBackup = MigrateBackupToCurrent(Remote.Data);
                    const MergeStats = MergeBackupIntoStorage(
                        RemoteBackup,
                        { IncludeDeviceState: false }
                    );

                    RemoteChangedLocal = MergeStats.ChangedKeys > 0;
                }

                if (RemoteChangedLocal) {
                    ReloadRuntimeStateFromStorage();
                }

                const LocalData = BuildCloudSyncData();
                const Write = await GoogleDriveBridgeRequest(
                    "Write",
                    {
                        ExpectedRevision: RemoteRevision,
                        Data: LocalData
                    }
                );

                if (Write.Status === "conflict") {
                    continue;
                }

                if (Write.Status !== "ok") {
                    throw new Error(
                        Write.Message || "Google Drive sync write failed."
                    );
                }

                Completed = true;
                LastCloudSyncAt = new Date().toISOString();
            }

            if (!Completed) {
                throw new Error(
                    "Google Drive changed repeatedly during sync. Please try again."
                );
            }

            CloudSyncStatus = "Synced";
        } catch (Error) {
            CloudSyncStatus = "Error";
            LastCloudSyncError = Error;

            console.error(
                "[Letter Boxed Cubed] Google Drive sync failed.",
                Error
            );

            if (Manual) {
                alert(
                    "Google Drive sync failed: " +
                    (Error?.message || String(Error))
                );
            }
        } finally {
            CloudSyncInFlight = false;
            UpdateGoogleDriveButton();

            if (CloudSyncPending) {
                CloudSyncPending = false;
                ScheduleCloudSync(250);
            }
        }
    }

    function ReloadRuntimeStateFromStorage() {
        LoadGuiState();
        LoadFoundWords();
        LoadCustomDictionary();
        LoadHideParPreference();
        ApplyHideParPreference();
        LoadLineDrawingSpeed();
        LoadFoundTwofers();
        RenderPanel();
        QueuePanelLayoutUpdate();
    }

    function UpdateGoogleDriveButton() {
        const Button = document.getElementById(
            GoogleDriveButtonId
        );

        if (!Button) {
            return;
        }

        if (!GoogleDriveConfig?.Enabled) {
            Button.textContent = "Drive: Setup";
            Button.title =
                "Configure automatic Google Drive sync";
            return;
        }

        const TextByStatus = {
            Ready: "Drive: Sync",
            Syncing: "Drive: Syncing…",
            Synced: "Drive: ✓",
            Error: "Drive: Error"
        };

        Button.textContent =
            TextByStatus[CloudSyncStatus] ||
            "Drive: Sync";

        const StatusParts = [
            "Click to sync now. Shift-click to reconfigure or disconnect."
        ];

        if (LastCloudSyncAt) {
            StatusParts.push(
                `Last synced: ${new Date(LastCloudSyncAt).toLocaleString()}`
            );
        }

        if (LastCloudSyncError) {
            StatusParts.push(
                `Last error: ${LastCloudSyncError.message || LastCloudSyncError}`
            );
        }

        Button.title = StatusParts.join("\n");
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

        ScheduleCloudSync();
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

        if (NytSolutionKey && !TwoferKeySet.has(NytSolutionKey)) {
            console.warn(
                "[Letter Boxed Cubed] NYT's two-word ourSolution was not found in the calculated Twofer set.",
                NytSolutionWords
            );
        }
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

        ScheduleCloudSync();
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
                /*
                    Gameplay mutations update player data, but they must not
                    reflow the TI/GB meta-column. GB's vertical position is
                    intentionally stable until an actual viewport resize.
                */
                NormalizeWordAreaFeedbackLayout();
                ScanGameState();
            }, 30);
        });

        GameObserver.observe(WordContainer, {
            childList: true,
            subtree: true,
            characterData: true
        });
    }

    function NormalizeWordAreaFeedbackLayout() {
        const WordContainer = document.querySelector(
            ".lb-game-container .lb-word-container"
        );

        if (!WordContainer) {
            return;
        }

        /*
            NYT's normal TI has three direct children: the active text field,
            accepted-word list, and par text. Praise/error popups are injected
            as additional transient children. Mark those extras so Cubed can
            place them AFTER the par text instead of allowing NYT's responsive
            positioning to overlap the two.

            Keeping this structural rather than matching words such as
            "Genius!" also handles NYT's other feedback messages.
        */
        for (const Child of WordContainer.children) {
            const IsKnownTiChild =
                Child.classList.contains("lb-text-field-wrapper") ||
                Child.classList.contains("lb-list-container") ||
                Child.classList.contains("lb-par");

            if (IsKnownTiChild) {
                continue;
            }

            const Text = String(Child.textContent || "").trim();

            if (Text) {
                Child.classList.add(
                    "lb-cubed-nyt-feedback"
                );
            }
        }
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

            HandleSubmissionAttempt();
            CheckProspectiveTwofer();
            QueuePostSubmissionScans();
        }, true);

        document.addEventListener("keydown", Event => {
            if (Event.key !== "Enter") {
                return;
            }

            HandleSubmissionAttempt();
            CheckProspectiveTwofer();
            QueuePostSubmissionScans();
        }, true);
    }

    function HandleSubmissionAttempt() {
        const CurrentChain = ReadCurrentChain();
        const InputWord = ReadCurrentInputWord();

        if (!InputWord) {
            return;
        }

        TrackPotentialCustomDictionaryWord(InputWord);

        if (IsLikelyAcceptedSubmission(CurrentChain, InputWord)) {
            BeginLineDrawingAcceleration();
        }
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

        const SquareRect =
            SquareContainer.getBoundingClientRect();

        NativeSquareWidth = Math.ceil(
            SquareRect.width
        );

        NativeSquareHeight = Math.ceil(
            SquareRect.height
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

        const MaximumSidePanelWidth = GetMaximumSidePanelWidth(GameContainer);

        if (MaximumSidePanelWidth >= MinimumPanelWidth) {
            ApplySideLayout(
                GameContainer,
                WordContainer,
                SquareContainer,
                Panel,
                MaximumSidePanelWidth
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

    function GetLeftColumnWidth() {
        return Math.max(
            NativeWordWidth,
            NativeSquareWidth
        );
    }

    function GetMaximumSidePanelWidth(GameContainer) {
        /*
            TI and GB now share a single stacked left column, so LBC only has
            to compete horizontally with the WIDER of those two NYT elements.
        */
        return Math.floor(
            GameContainer.clientWidth -
            (EdgePadding * 2) -
            GetLeftColumnWidth() -
            GameGap
        );
    }

    function GetLegacyMaximumPanelWidth(GameContainer) {
        /*
            This reproduces the amount of horizontal space v1.7 had available
            when TI, GB, and LBC were three side-by-side columns. It is used
            only to derive the new smaller default width.
        */
        return Math.max(
            MinimumPanelWidth,
            Math.floor(
                GameContainer.clientWidth -
                (EdgePadding * 2) -
                NativeWordWidth -
                NativeSquareWidth -
                (GameGap * 2)
            )
        );
    }

    function GetDefaultSidePanelWidth(
        GameContainer,
        MaximumSidePanelWidth
    ) {
        const LegacyMaximumPanelWidth =
            GetLegacyMaximumPanelWidth(GameContainer);

        const LegacyDefaultWidth =
            LegacyMaximumPanelWidth *
            LegacyDefaultPanelWidthRatio;

        const NewDefaultWidth =
            Math.round(
                LegacyDefaultWidth *
                DefaultPanelShrinkRatio
            );

        return Clamp(
            NewDefaultWidth,
            MinimumPanelWidth,
            MaximumSidePanelWidth
        );
    }

    function GetSidePanelWidth(
        GameContainer,
        MaximumSidePanelWidth
    ) {
        const RequestedWidth = Number.isFinite(PanelWidthPreference)
            ? PanelWidthPreference
            : GetDefaultSidePanelWidth(
                GameContainer,
                MaximumSidePanelWidth
            );

        /*
            This render-time clamp is intentionally separate from the clamp
            applied during a manual drag. The preference represents what the
            user chose; rendering must still adapt if the browser later becomes
            too narrow to honor that preference temporarily.
        */
        return Clamp(
            RequestedWidth,
            MinimumPanelWidth,
            MaximumSidePanelWidth
        );
    }

    function Clamp(Value, Minimum, Maximum) {
        return Math.min(
            Math.max(Value, Minimum),
            Maximum
        );
    }

    function ApplySideLayout(
        GameContainer,
        WordContainer,
        SquareContainer,
        Panel,
        MaximumSidePanelWidth
    ) {
        GameContainer.classList.add(SideModeClass);
        GameContainer.classList.remove(StackedModeClass);

        const PanelWidth = GetSidePanelWidth(
            GameContainer,
            MaximumSidePanelWidth
        );

        GameContainer.style.setProperty(
            "--lb-cubed-word-width",
            `${NativeWordWidth}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-square-width",
            `${NativeSquareWidth}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-square-height",
            `${NativeSquareHeight}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-word-area-height",
            `${StableWordAreaHeight}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-left-column-width",
            `${GetLeftColumnWidth()}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-panel-width",
            `${PanelWidth}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-gap",
            `${GameGap}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-left-column-gap",
            `${LeftColumnGap}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-edge-padding",
            `${EdgePadding}px`
        );

        Panel.style.removeProperty("left");
        Panel.style.removeProperty("top");
        Panel.style.removeProperty("width");
        Panel.style.removeProperty("height");
        Panel.style.removeProperty("max-height");
    }

    function ApplyStackedLayout(
        GameContainer,
        WordContainer,
        SquareContainer,
        Panel
    ) {
        GameContainer.classList.remove(SideModeClass);
        GameContainer.classList.add(StackedModeClass);

        const MaximumStackedWidth = Math.max(
            280,
            GameContainer.clientWidth -
            (EdgePadding * 2)
        );

        /*
            In stacked mode the saved side-by-side preference is still useful
            as a target width, but the panel may temporarily be clamped to the
            narrower available space. Automatic clamping never overwrites the
            preference.
        */
        const DefaultStackedWidth = Math.round(
            MaximumStackedWidth * 0.9
        );

        const RequestedWidth = Number.isFinite(PanelWidthPreference)
            ? PanelWidthPreference
            : DefaultStackedWidth;

        const StackedWidth = Clamp(
            RequestedWidth,
            Math.min(MinimumPanelWidth, MaximumStackedWidth),
            MaximumStackedWidth
        );

        GameContainer.style.setProperty(
            "--lb-cubed-word-width",
            `${NativeWordWidth}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-square-width",
            `${NativeSquareWidth}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-square-height",
            `${NativeSquareHeight}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-word-area-height",
            `${StableWordAreaHeight}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-left-column-width",
            `${GetLeftColumnWidth()}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-stacked-panel-width",
            `${StackedWidth}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-left-column-gap",
            `${LeftColumnGap}px`
        );

        GameContainer.style.setProperty(
            "--lb-cubed-edge-padding",
            `${EdgePadding}px`
        );

        /*
            Cap LBC's height to the total height of the stacked TI + GB column.
            The panel content owns its scrollbar.
        */
        requestAnimationFrame(() => {
            const WordRect = WordContainer.getBoundingClientRect();
            const SquareRect = SquareContainer.getBoundingClientRect();

            const PlayTop = Math.min(
                WordRect.top,
                SquareRect.top
            );

            const PlayBottom = Math.max(
                WordRect.bottom,
                SquareRect.bottom
            );

            const PlayHeight = Math.ceil(
                PlayBottom - PlayTop
            );

            Panel.style.height = `${PlayHeight}px`;
            Panel.style.maxHeight = `${PlayHeight}px`;
        });
    }

    // -------------------------------------------------------------------------
    // Panel edge resizing
    // -------------------------------------------------------------------------

    function StartPanelResizeBehavior() {
        const Handles = [
            document.getElementById(LeftResizeHandleId),
            document.getElementById(RightResizeHandleId)
        ].filter(Boolean);

        for (const Handle of Handles) {
            Handle.addEventListener(
                "pointerdown",
                HandlePanelPointerDown,
                true
            );

            Handle.addEventListener(
                "pointermove",
                HandlePanelPointerMove,
                true
            );

            Handle.addEventListener(
                "pointerup",
                EndPanelResize,
                true
            );

            Handle.addEventListener(
                "pointercancel",
                EndPanelResize,
                true
            );

            Handle.addEventListener(
                "dblclick",
                HandlePanelResizeDoubleClick,
                true
            );
        }
    }

    function HandlePanelPointerMove(Event) {
        if (!PanelResizeState) {
            return;
        }

        const GameContainer =
            document.querySelector(".lb-game-container");

        if (
            !GameContainer ||
            !GameContainer.classList.contains(SideModeClass)
        ) {
            return;
        }

        const Direction =
            PanelResizeState.Edge === "Right"
                ? 1
                : -1;

        const PointerDelta =
            Event.clientX -
            PanelResizeState.StartX;

        /*
            The complete two-column game group stays centered. Growing LBC by
            2px moves its dragged outer edge about 1px, so the pointer delta is
            doubled to keep the resize handle perceptually attached to the
            cursor.
        */
        const RequestedWidth =
            PanelResizeState.StartWidth +
            (PointerDelta * Direction * 2);

        const MaximumSidePanelWidth =
            GetMaximumSidePanelWidth(
                GameContainer
            );

        /*
            Store only a size the user could actually see. If the pointer is
            flung far past the min/max boundary, the preference stays clamped
            at that visible boundary. We deliberately do NOT rebase StartX or
            StartWidth, so reversing direction has the normal "catch back up
            to the edge" behavior of a native resize boundary.
        */
        PanelWidthPreference =
            Clamp(
                RequestedWidth,
                MinimumPanelWidth,
                MaximumSidePanelWidth
            );

        UpdatePanelLayout();

        Event.preventDefault();
    }

    function HandlePanelPointerDown(Event) {
        if (Event.button !== 0) {
            return;
        }

        const GameContainer =
            document.querySelector(".lb-game-container");

        const Panel =
            document.getElementById(PanelId);

        const Handle =
            Event.currentTarget;

        if (
            !GameContainer?.classList.contains(SideModeClass) ||
            !Panel ||
            !(Handle instanceof HTMLElement)
        ) {
            return;
        }

        const Edge =
            Handle.dataset.resizeEdge;

        if (
            Edge !== "Left" &&
            Edge !== "Right"
        ) {
            return;
        }

        const Rect =
            Panel.getBoundingClientRect();

        PanelResizeState = {
            Edge,
            StartX:
                Event.clientX,
            StartWidth:
                Rect.width,
            PointerId:
                Event.pointerId,
            Handle
        };

        Panel.classList.add(
            "lb-cubed-resizing"
        );

        if (
            typeof Handle.setPointerCapture ===
            "function"
        ) {
            try {
                Handle.setPointerCapture(
                    Event.pointerId
                );
            } catch {
                // Pointer capture is convenient but not required.
            }
        }

        Event.preventDefault();
        Event.stopPropagation();
    }

    function EndPanelResize(Event) {
        if (!PanelResizeState) {
            return;
        }

        const Panel =
            document.getElementById(
                PanelId
            );

        const Handle =
            PanelResizeState.Handle;

        if (
            Handle &&
            typeof Handle.releasePointerCapture ===
            "function" &&
            PanelResizeState.PointerId !== undefined
        ) {
            try {
                Handle.releasePointerCapture(
                    PanelResizeState.PointerId
                );
            } catch {
                // Ignore browsers that already released pointer capture.
            }
        }

        PanelResizeState = null;
        SavePanelWidthPreference();

        if (Panel) {
            Panel.classList.remove(
                "lb-cubed-resizing"
            );
        }

        QueuePanelLayoutUpdate();

        if (Event) {
            Event.preventDefault();
        }
    }

    function HandlePanelResizeDoubleClick(Event) {
        const GameContainer =
            document.querySelector(
                ".lb-game-container"
            );

        if (
            !GameContainer?.classList.contains(
                SideModeClass
            )
        ) {
            return;
        }

        /*
            A double-click is an explicit preference: maximize LBC to every
            currently available horizontal pixel and persist that width.
        */
        PanelWidthPreference =
            GetMaximumSidePanelWidth(
                GameContainer
            );

        SavePanelWidthPreference();
        UpdatePanelLayout();

        Event.preventDefault();
        Event.stopPropagation();
    }

    // -------------------------------------------------------------------------
    // Panel rendering
    // -------------------------------------------------------------------------

    function CreatePanel() {
        if (document.getElementById(PanelId)) {
            return;
        }

        const GameContainer =
            document.querySelector(
                ".lb-game-container"
            );

        if (!GameContainer) {
            console.warn(
                "[Letter Boxed Cubed] Could not find .lb-game-container."
            );
            return;
        }

        GameContainer.classList.add(
            LayoutClass
        );

        const Panel =
            document.createElement(
                "section"
            );

        Panel.id =
            PanelId;

        const PanelContent =
            document.createElement(
                "div"
            );

        PanelContent.id =
            PanelContentId;

        const LeftHandle =
            document.createElement(
                "div"
            );

        LeftHandle.id =
            LeftResizeHandleId;

        LeftHandle.className =
            "lb-cubed-resize-handle lb-cubed-resize-handle-left";

        LeftHandle.dataset.resizeEdge =
            "Left";

        LeftHandle.setAttribute(
            "aria-label",
            "Resize Letter Boxed Cubed from the left edge"
        );

        const RightHandle =
            document.createElement(
                "div"
            );

        RightHandle.id =
            RightResizeHandleId;

        RightHandle.className =
            "lb-cubed-resize-handle lb-cubed-resize-handle-right";

        RightHandle.dataset.resizeEdge =
            "Right";

        RightHandle.setAttribute(
            "aria-label",
            "Resize Letter Boxed Cubed from the right edge"
        );

        Panel.append(
            PanelContent,
            LeftHandle,
            RightHandle
        );

        GameContainer.appendChild(
            Panel
        );
    }

    function RenderPanel() {
        const Panel =
            document.getElementById(
                PanelId
            );

        const PanelContent =
            document.getElementById(
                PanelContentId
            );

        if (
            !Panel ||
            !PanelContent
        ) {
            return;
        }

        const PreviousOpenStates =
            ReadTreeOpenStates(
                PanelContent
            );

        const PreviousScrollTop =
            PanelContent.scrollTop;

        const FoundDictionaryWords =
            Dictionary
                .filter(
                    Word =>
                        FoundWords.has(
                            Word
                        )
                )
                .sort(
                    Alphabetically
                );

        const UnfoundWords =
            Dictionary
                .filter(
                    Word =>
                        !FoundWords.has(
                            Word
                        )
                )
                .sort(
                    Alphabetically
                );

        const Stats =
            CalculateStats(
                FoundDictionaryWords
            );

        const TwoferHintStats =
            CalculateTwoferHintStats();

        PanelContent.replaceChildren();

        RenderHeader(
            PanelContent
        );

        /*
            These are the six responsive top-level LBC elements:

                1. Completion + Longest Found ("big 2")
                2. Hints
                3. Twofers
                4. Words by Length
                5. Found Words
                6. Unfound Words

            CSS container queries rearrange these based on LBC's own width,
            not the browser viewport, so manual panel resizing participates in
            the responsive layout naturally.
        */
        const DashboardGrid =
            document.createElement(
                "div"
            );

        DashboardGrid.className =
            "lb-cubed-dashboard-grid";

        PanelContent.appendChild(
            DashboardGrid
        );

        RenderMainStats(
            DashboardGrid,
            Stats
        );

        RenderHints(
            DashboardGrid,
            PreviousOpenStates,
            TwoferHintStats
        );

        RenderTwofers(
            DashboardGrid,
            PreviousOpenStates
        );

        RenderWordsByLength(
            DashboardGrid,
            PreviousOpenStates,
            Stats
        );

        RenderFoundAndUnfoundWords(
            DashboardGrid,
            PreviousOpenStates,
            FoundDictionaryWords,
            UnfoundWords
        );

        PanelContent.scrollTop =
            PreviousScrollTop;
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
        HeaderText.className = "lb-cubed-header-text";
        HeaderText.append(Title, Subtitle);

        const HeaderActions = document.createElement("div");
        HeaderActions.className = "lb-cubed-header-actions";

        // Global display preference for NYT's par text.
        const HideParControl = document.createElement("label");
        HideParControl.className = "lb-cubed-display-option";
        HideParControl.title =
            "Hide NYT's 'Try to solve in X words' par text";

        const HideParCheckbox = document.createElement("input");
        HideParCheckbox.type = "checkbox";
        HideParCheckbox.checked = HidePar;

        const HideParLabel = document.createElement("span");
        HideParLabel.textContent = "Hide Par";

        HideParCheckbox.addEventListener(
            "change",
            Event => {
                HidePar = Boolean(Event.currentTarget.checked);
                SaveHideParPreference();
                ApplyHideParPreference();
            }
        );

        HideParControl.append(
            HideParCheckbox,
            HideParLabel
        );

        // Last NYT-invalid, structurally valid submission.
        const InvalidControl = document.createElement("div");
        InvalidControl.className = "lb-cubed-invalid-control";

        const InvalidWord = document.createElement("span");
        InvalidWord.className = "lb-cubed-invalid-word";
        InvalidWord.textContent = LastInvalidWord || "No invalid word";
        InvalidWord.title = LastInvalidWord
            ? "Last submitted word that obeys the board rules but is absent from NYT's dictionary"
            : "No structurally valid NYT-dictionary rejection has been captured yet";

        const AddDictionaryButton = document.createElement("button");
        AddDictionaryButton.type = "button";
        AddDictionaryButton.className = "lb-cubed-header-button";

        const InvalidAlreadyAdded =
            LastInvalidWord &&
            CustomDictionary.has(LastInvalidWord);

        AddDictionaryButton.textContent = InvalidAlreadyAdded
            ? "Added"
            : "Add to dictionary";

        AddDictionaryButton.disabled = !LastInvalidWord || InvalidAlreadyAdded;
        AddDictionaryButton.title = LastInvalidWord
            ? InvalidAlreadyAdded
                ? `${LastInvalidWord} is already in your custom dictionary`
                : `Record ${LastInvalidWord} as a user-approved custom dictionary word`
            : "Submit a structurally valid word that NYT does not recognize first";

        AddDictionaryButton.addEventListener(
            "click",
            Event => {
                Event.preventDefault();
                Event.stopPropagation();
                AddLastInvalidWordToCustomDictionary();
            }
        );

        InvalidControl.append(
            InvalidWord,
            AddDictionaryButton
        );

        // Experimental canvas-animation speed control.
        const LineSpeedControl = document.createElement("label");
        LineSpeedControl.className = "lb-cubed-line-speed-control";
        LineSpeedControl.title =
            "Scale the Letter Boxed canvas line-drawing duration: 1.0 = NYT normal, 0.0 = effectively instant";

        const LineSpeedLabel = document.createElement("span");
        LineSpeedLabel.className = "lb-cubed-line-speed-label";
        LineSpeedLabel.textContent = "Animation Speed";

        const LineSpeedSlider = document.createElement("input");
        LineSpeedSlider.className = "lb-cubed-line-speed-slider";
        LineSpeedSlider.type = "range";
        LineSpeedSlider.min = "0";
        LineSpeedSlider.max = "1";
        LineSpeedSlider.step = "0.1";
        LineSpeedSlider.value = String(LineDrawingSpeed);

        const LineSpeedValue = document.createElement("span");
        LineSpeedValue.className = "lb-cubed-line-speed-value";
        LineSpeedValue.textContent = LineDrawingSpeed.toFixed(1);

        LineSpeedSlider.addEventListener(
            "input",
            Event => {
                LineDrawingSpeed = Clamp(
                    Number(Event.currentTarget.value),
                    0,
                    1
                );

                LineSpeedValue.textContent = LineDrawingSpeed.toFixed(1);
            }
        );

        LineSpeedSlider.addEventListener(
            "change",
            () => SaveLineDrawingSpeed()
        );

        LineSpeedControl.append(
            LineSpeedLabel,
            LineSpeedSlider,
            LineSpeedValue
        );


        const BrowseHistoryButton = document.createElement("button");
        BrowseHistoryButton.id = BrowseHistoryButtonId;
        BrowseHistoryButton.type = "button";
        BrowseHistoryButton.className = "lb-cubed-header-button";
        BrowseHistoryButton.textContent = "Browse History";
        BrowseHistoryButton.title =
            "Browse found-word and solved-Twofer history from the synced Google Drive backup";
        BrowseHistoryButton.addEventListener(
            "click",
            Event => {
                Event.preventDefault();
                Event.stopPropagation();
                OpenCloudHistoryBrowser();
            }
        );

        const GoogleDriveButton = document.createElement("button");
        GoogleDriveButton.id = GoogleDriveButtonId;
        GoogleDriveButton.type = "button";
        GoogleDriveButton.className = "lb-cubed-header-button";
        GoogleDriveButton.addEventListener(
            "click",
            Event => {
                Event.preventDefault();
                Event.stopPropagation();

                if (!GoogleDriveConfig?.Enabled || Event.shiftKey) {
                    ConfigureGoogleDriveSync();
                    return;
                }

                SyncWithGoogleDrive({ Manual: true });
            }
        );

        const ExportButton = document.createElement("button");
        ExportButton.type = "button";
        ExportButton.className = "lb-cubed-header-button";
        ExportButton.textContent = "Export";
        ExportButton.title =
            "Export all retained Letter Boxed Cubed puzzle/player data as a text backup";
        ExportButton.addEventListener(
            "click",
            Event => {
                Event.preventDefault();
                Event.stopPropagation();
                ExportAllData();
            }
        );

        const ImportButton = document.createElement("button");
        ImportButton.type = "button";
        ImportButton.className = "lb-cubed-header-button";
        ImportButton.textContent = "Import";
        ImportButton.title =
            "Restore or merge data from a Letter Boxed Cubed backup";
        ImportButton.addEventListener(
            "click",
            Event => {
                Event.preventDefault();
                Event.stopPropagation();
                PromptForImport();
            }
        );

        HeaderActions.append(
            HideParControl,
            InvalidControl,
            LineSpeedControl,
            BrowseHistoryButton,
            GoogleDriveButton,
            ExportButton,
            ImportButton
        );

        Header.append(
            HeaderText,
            HeaderActions
        );

        Panel.appendChild(Header);
        UpdateGoogleDriveButton();
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

        /*
            Only reveal potential first/second words that the player has
            already found somewhere during today's play. The x / y counter
            still uses the total number of valid positional words, but the
            expanded list itself must never expose unfound candidates.
        */
        const SortedWords = [...Words]
            .filter(Word => FoundWords.has(Word))
            .sort(Alphabetically);

        if (SortedWords.length === 0) {
            const Empty = document.createElement("div");
            Empty.className = "lb-cubed-potential-word-empty";
            Empty.textContent = "None found yet.";
            List.appendChild(Empty);
        } else {
            const Fragment = document.createDocumentFragment();

            for (const Word of SortedWords) {
                const Item = document.createElement("div");
                Item.className =
                    "lb-cubed-potential-word lb-cubed-potential-word-found";
                Item.textContent = Word;
                Fragment.appendChild(Item);
            }

            List.appendChild(Fragment);
        }
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
            SaveTwofersGroupedPreference();
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

        if (!NytSolutionKey || Twofer.Key !== NytSolutionKey) {
            return Row;
        }

        const NytWrapper = document.createElement("div");
        NytWrapper.className = "lb-cubed-nyt-solution";

        const NytLabel = document.createElement("div");
        NytLabel.className = "lb-cubed-nyt-solution-label";
        NytLabel.textContent = "⭐ NYT Solution";

        NytWrapper.append(NytLabel, Row);
        return NytWrapper;
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
        Container,
        PreviousOpenStates,
        FoundDictionaryWords,
        UnfoundWords
    ) {
        /*
            Found and Unfound are intentionally separate top-level responsive
            grid items. At generous widths they can sit alongside other LBC
            sections; as the panel narrows they move to their own row and
            eventually stack individually.
        */
        Container.append(
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

        const SavedOpen = GetGuiSectionOpen(Name);

        if (Object.prototype.hasOwnProperty.call(PreviousOpenStates, Name)) {
            Details.open = PreviousOpenStates[Name];
        } else if (SavedOpen !== null) {
            Details.open = SavedOpen;
        } else {
            Details.open = DefaultOpen;
        }

        Details.addEventListener(
            "toggle",
            () => SetGuiSectionOpen(Name, Details.open)
        );
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
            /*
                ================================================================
                OUTER LETTER BOXED LAYOUT
                ================================================================

                TI = NYT text-input / word column
                GB = NYT game-board column
                LBC = Letter Boxed Cubed

                Side mode is now a TWO-column meta-layout:

                    [ TI ] [     ]
                    [ GB ] [ LBC ]

                TI and GB retain their native measured widths and form the
                centered left column. LBC forms the independently resizable
                right column. When those two meta-columns no longer fit, the
                entire left column stacks above LBC.
            */

            .lb-game-container.${LayoutClass} {
                box-sizing: border-box !important;
            }

            .lb-game-container.${SideModeClass} {
                display: grid !important;
                grid-template-columns:
                    var(--lb-cubed-left-column-width)
                    var(--lb-cubed-panel-width) !important;
                /*
                    Explicit track heights are the key to keeping GB static.
                    Because LBC spans both rows, auto-sized rows allowed its
                    height to participate in grid sizing; accepting a word
                    could therefore redistribute vertical space and make GB
                    jump upward. Fixed TI + GB tracks decouple the game from
                    LBC's height completely.
                */
                grid-template-rows:
                    var(--lb-cubed-word-area-height, 250px)
                    var(--lb-cubed-square-height, auto) !important;
                column-gap: var(--lb-cubed-gap, 24px) !important;
                row-gap: var(--lb-cubed-left-column-gap, 16px) !important;
                justify-content: center !important;
                align-items: start !important;
                width: 100% !important;
                max-width: none !important;
                padding-left: var(--lb-cubed-edge-padding, 18px) !important;
                padding-right: var(--lb-cubed-edge-padding, 18px) !important;
                overflow: visible !important;
            }

            .lb-game-container.${SideModeClass} > .lb-word-container {
                grid-column: 1 !important;
                grid-row: 1 !important;
                justify-self: center !important;
                align-self: start !important;
                width: var(--lb-cubed-word-width) !important;
                min-width: var(--lb-cubed-word-width) !important;
                max-width: var(--lb-cubed-word-width) !important;
                height: var(--lb-cubed-word-area-height, 250px) !important;
                min-height: var(--lb-cubed-word-area-height, 250px) !important;
                max-height: var(--lb-cubed-word-area-height, 250px) !important;
            }

            .lb-game-container.${SideModeClass} > .lb-square-container {
                grid-column: 1 !important;
                grid-row: 2 !important;
                justify-self: center !important;
                align-self: start !important;
                width: var(--lb-cubed-square-width) !important;
                min-width: var(--lb-cubed-square-width) !important;
                max-width: var(--lb-cubed-square-width) !important;
                height: var(--lb-cubed-square-height) !important;
                min-height: var(--lb-cubed-square-height) !important;
                max-height: var(--lb-cubed-square-height) !important;
            }

            .lb-game-container.${SideModeClass} > #${PanelId} {
                grid-column: 2 !important;
                grid-row: 1 / span 2 !important;
                position: relative;
                align-self: stretch;
                width: var(--lb-cubed-panel-width) !important;
                min-width: var(--lb-cubed-panel-width) !important;
                max-width: var(--lb-cubed-panel-width) !important;
                min-height: 0;
            }

            .lb-game-container.${StackedModeClass} {
                display: grid !important;
                grid-template-columns: minmax(0, 1fr) !important;
                grid-template-rows:
                    var(--lb-cubed-word-area-height, 250px)
                    var(--lb-cubed-square-height, auto)
                    auto !important;
                row-gap: var(--lb-cubed-left-column-gap, 16px) !important;
                justify-items: center !important;
                align-items: start !important;
                width: 100% !important;
                max-width: none !important;
                padding-left: var(--lb-cubed-edge-padding, 18px) !important;
                padding-right: var(--lb-cubed-edge-padding, 18px) !important;
                overflow: visible !important;
            }

            .lb-game-container.${StackedModeClass} > .lb-word-container {
                grid-column: 1 !important;
                grid-row: 1 !important;
                justify-self: center !important;
                width: min(var(--lb-cubed-word-width), 100%) !important;
                max-width: 100% !important;
                height: var(--lb-cubed-word-area-height, 250px) !important;
                min-height: var(--lb-cubed-word-area-height, 250px) !important;
                max-height: var(--lb-cubed-word-area-height, 250px) !important;
            }

            .lb-game-container.${StackedModeClass} > .lb-square-container {
                grid-column: 1 !important;
                grid-row: 2 !important;
                justify-self: center !important;
                width: min(var(--lb-cubed-square-width), 100%) !important;
                max-width: 100% !important;
                height: var(--lb-cubed-square-height) !important;
                min-height: var(--lb-cubed-square-height) !important;
                max-height: var(--lb-cubed-square-height) !important;
            }

            .lb-game-container.${StackedModeClass} > #${PanelId} {
                grid-column: 1 !important;
                grid-row: 3 !important;
                position: relative;
                justify-self: center;
                width: var(--lb-cubed-stacked-panel-width) !important;
                min-width: 0 !important;
                max-width: 100% !important;
            }

            /*
                ================================================================
                TI INTERNAL FLOW
                ================================================================

                NYT's own responsive rules spread the par text and transient
                praise popup through the available TI height. Cubed instead
                keeps the normal TI contents packed toward the top, leaving GB
                in its fixed row and ensuring feedback appears below the par.
            */

            .lb-game-container.${LayoutClass} > .lb-word-container {
                display: flex !important;
                flex-direction: column !important;
                justify-content: flex-start !important;
                overflow: visible !important;
            }

            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper {
                order: 1;
                flex: 0 0 auto;
            }

            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-list-container {
                order: 2;
                flex: 0 0 auto;
            }

            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-par {
                order: 3;
                position: static !important;
                flex: 0 0 auto;
                margin-top: 10px !important;
                margin-bottom: 0 !important;
                transform: none !important;
            }

            .lb-game-container.${LayoutClass}.lb-cubed-hide-par
            > .lb-word-container
            > .lb-par {
                display: none !important;
            }

            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-cubed-nyt-feedback {
                order: 4;
                position: static !important;
                flex: 0 0 auto;
                align-self: center !important;
                margin: 8px auto 0 !important;
                inset: auto !important;
                transform: none !important;
            }

            /*
                ================================================================
                PANEL SHELL / SCROLLER / RESIZE HANDLES
                ================================================================
            */

            #${PanelId} {
                z-index: 10;
                box-sizing: border-box;
                margin: 0;
                padding: 0;
                overflow: visible;
                color: rgb(48, 24, 24);
                font-family: Arial, Helvetica, sans-serif;
            }

            #${PanelId},
            #${PanelId} * {
                box-sizing: border-box;
            }

            #${PanelContentId} {
                width: 100%;
                height: 100%;
                min-height: 0;
                padding: 12px;
                overflow-x: hidden;
                overflow-y: auto;
                background: rgb(216, 132, 130);
                color: rgb(48, 24, 24);
                border: 1px solid rgba(76, 34, 34, 0.58);
                border-radius: 4px;
                scrollbar-width: thin;
                scrollbar-color:
                    rgba(76, 32, 32, 0.58)
                    rgba(255, 255, 255, 0.13);

                /*
                    All inner responsiveness is based on LBC's actual manually
                    resizable width rather than the browser viewport.
                */
                container-type: inline-size;
                container-name: lbc;
            }

            #${PanelContentId}::-webkit-scrollbar {
                width: 8px;
            }

            #${PanelContentId}::-webkit-scrollbar-track {
                background: rgba(255, 255, 255, 0.13);
            }

            #${PanelContentId}::-webkit-scrollbar-thumb {
                background: rgba(76, 32, 32, 0.58);
                border-radius: 4px;
            }

            .lb-cubed-resize-handle {
                display: none;
                position: absolute;
                top: 0;
                bottom: 0;
                width: ${ResizeHandleWidth}px;
                z-index: 30;
                cursor: ew-resize;
                touch-action: none;
                user-select: none;
                background: transparent;
            }

            /*
                Both grips have exactly the same hit width. The right grip is
                deliberately moved fully OUTSIDE the panel, plus a small gap,
                so it never fights with LBC's vertical scrollbar.
            */
            .lb-game-container.${SideModeClass}
            > #${PanelId}
            > .lb-cubed-resize-handle {
                display: block;
            }

            .lb-cubed-resize-handle-left {
                left: -${ResizeHandleWidth / 2}px;
            }

            .lb-cubed-resize-handle-right {
                right: -${ResizeHandleWidth + RightResizeHandleGap}px;
            }

            .lb-cubed-resize-handle::after {
                content: "";
                position: absolute;
                top: 0;
                bottom: 0;
                width: 2px;
                opacity: 0;
                background: rgba(76, 34, 34, 0.5);
                transition: opacity 100ms ease;
            }

            .lb-cubed-resize-handle-left::after {
                left: calc(50% - 1px);
            }

            .lb-cubed-resize-handle-right::after {
                right: calc(50% - 1px);
            }

            .lb-cubed-resize-handle:hover::after,
            #${PanelId}.lb-cubed-resizing
            .lb-cubed-resize-handle::after {
                opacity: 1;
            }

            #${PanelId}.lb-cubed-resizing {
                user-select: none;
            }

            /*
                ================================================================
                HEADER
                ================================================================
            */

            .lb-cubed-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 8px;
                margin-bottom: 10px;
            }

            .lb-cubed-header-text {
                min-width: 0;
            }

            .lb-cubed-header-actions {
                display: flex;
                flex: 0 1 auto;
                flex-wrap: wrap;
                gap: 5px;
                justify-content: flex-end;
                align-items: center;
            }

            .lb-cubed-display-option,
            .lb-cubed-invalid-control,
            .lb-cubed-line-speed-control {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                min-height: 24px;
                padding: 2px 4px;
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(78, 34, 34, 0.20);
                border-radius: 3px;
            }

            .lb-cubed-display-option {
                color: rgba(48, 24, 24, 0.78);
                font-size: 9px;
                font-weight: 700;
                white-space: nowrap;
                cursor: pointer;
            }

            .lb-cubed-display-option input {
                margin: 0;
                accent-color: rgb(92, 37, 37);
                cursor: pointer;
            }

            .lb-cubed-invalid-word {
                display: inline-block;
                max-width: 115px;
                overflow: hidden;
                color: rgb(48, 24, 24);
                font-family: Consolas, "Courier New", monospace;
                font-size: 10px;
                font-weight: 700;
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            .lb-cubed-line-speed-label {
                color: rgba(48, 24, 24, 0.78);
                font-size: 9px;
                font-weight: 700;
                white-space: nowrap;
            }

            .lb-cubed-line-speed-slider {
                width: 74px;
                min-width: 55px;
                accent-color: rgb(92, 37, 37);
                cursor: pointer;
            }

            .lb-cubed-line-speed-value {
                min-width: 22px;
                color: rgb(48, 24, 24);
                font-family: Consolas, "Courier New", monospace;
                font-size: 9px;
                font-weight: 700;
                text-align: right;
            }

            .lb-cubed-header-button {
                appearance: none;
                padding: 4px 7px;
                color: rgb(48, 24, 24);
                background: rgba(255, 255, 255, 0.18);
                border: 1px solid rgba(78, 34, 34, 0.36);
                border-radius: 3px;
                font: inherit;
                font-size: 10px;
                font-weight: 700;
                line-height: 1.2;
                cursor: pointer;
            }

            .lb-cubed-header-button:hover:not(:disabled) {
                background: rgba(255, 255, 255, 0.30);
            }

            .lb-cubed-header-button:disabled {
                opacity: 0.48;
                cursor: default;
            }

            .lb-cubed-header-button:active:not(:disabled) {
                transform: translateY(1px);
            }

            .lb-cubed-title {
                margin: 0;
                padding: 0;
                color: rgb(48, 24, 24);
                font-size: 22px;
                line-height: 1.1;
                font-weight: 700;
            }

            .lb-cubed-subtitle {
                margin-top: 3px;
                color: rgba(48, 24, 24, 0.70);
                font-size: 11px;
            }


            /*
                ================================================================
                CLOUD HISTORY BROWSER
                ================================================================
            */

            #${HistoryOverlayId} {
                position: fixed;
                inset: 0;
                z-index: 100000;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 24px;
                background: rgba(0, 0, 0, 0.55);
                color: rgb(48, 24, 24);
                font-family: Arial, Helvetica, sans-serif;
            }

            #${HistoryOverlayId},
            #${HistoryOverlayId} * {
                box-sizing: border-box;
            }

            .lb-cubed-history-modal {
                display: flex;
                flex-direction: column;
                width: min(920px, 100%);
                max-height: min(820px, 90vh);
                overflow: hidden;
                background: rgb(216, 132, 130);
                border: 1px solid rgba(76, 34, 34, 0.78);
                border-radius: 6px;
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.35);
            }

            .lb-cubed-history-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                padding: 12px 14px 8px;
                border-bottom: 1px solid rgba(78, 34, 34, 0.26);
            }

            .lb-cubed-history-heading-block {
                min-width: 0;
            }

            .lb-cubed-history-title {
                margin: 0;
                color: rgb(48, 24, 24);
                font-size: 20px;
                line-height: 1.1;
            }

            .lb-cubed-history-cloud-label {
                margin-top: 3px;
                color: rgba(48, 24, 24, 0.65);
                font-size: 10px;
            }

            .lb-cubed-history-navigation {
                display: grid;
                grid-template-columns:
                    auto
                    auto
                    minmax(180px, 1fr)
                    auto
                    auto;
                gap: 5px;
                align-items: center;
                padding: 8px 14px;
                background: rgba(255, 255, 255, 0.08);
                border-bottom: 1px solid rgba(78, 34, 34, 0.24);
            }

            .lb-cubed-history-nav-button {
                min-width: 32px;
                padding-left: 6px;
                padding-right: 6px;
            }

            .lb-cubed-history-position {
                min-width: 0;
                padding: 0 8px;
                color: rgb(48, 24, 24);
                font-size: 12px;
                font-weight: 700;
                text-align: center;
                overflow-wrap: anywhere;
            }

            .lb-cubed-history-content {
                min-height: 0;
                overflow: auto;
                padding: 12px 14px 14px;
            }

            .lb-cubed-history-puzzle-header {
                margin-bottom: 9px;
            }

            .lb-cubed-history-puzzle-title {
                margin: 0;
                color: rgb(48, 24, 24);
                font-size: 18px;
                line-height: 1.15;
            }

            .lb-cubed-history-puzzle-meta {
                margin-top: 3px;
                color: rgba(48, 24, 24, 0.65);
                font-family: Consolas, "Courier New", monospace;
                font-size: 10px;
            }

            .lb-cubed-history-stat-grid {
                display: grid;
                grid-template-columns:
                    repeat(2, minmax(0, 1fr));
                gap: 7px;
                margin-bottom: 9px;
            }

            .lb-cubed-history-stat {
                min-width: 0;
            }

            .lb-cubed-history-sections {
                display: grid;
                grid-template-columns:
                    repeat(auto-fit, minmax(230px, 1fr));
                gap: 8px;
                align-items: start;
            }

            .lb-cubed-history-section {
                min-width: 0;
                overflow: hidden;
                border: 1px solid rgba(78, 34, 34, 0.38);
                border-radius: 3px;
                background: rgba(255, 255, 255, 0.05);
            }

            .lb-cubed-history-section-title {
                margin: 0;
                padding: 7px 8px;
                color: rgb(48, 24, 24);
                background: rgba(92, 37, 37, 0.11);
                font-size: 12px;
                font-weight: 700;
            }

            .lb-cubed-history-word-grid {
                display: grid;
                grid-template-columns:
                    repeat(auto-fill, minmax(105px, 1fr));
                gap: 3px;
                padding: 5px;
            }

            .lb-cubed-history-twofer-grid {
                display: grid;
                grid-template-columns:
                    repeat(auto-fill, minmax(220px, 1fr));
                gap: 3px;
                padding: 5px;
            }

            .lb-cubed-history-twofer-row {
                display: grid;
                grid-template-columns:
                    minmax(0, 1fr)
                    16px
                    minmax(0, 1fr);
                gap: 3px;
                align-items: center;
                min-width: 0;
                padding: 1px;
                border-radius: 3px;
                background: rgba(255, 255, 255, 0.10);
            }

            .lb-cubed-history-custom-word {
                background: rgba(218, 203, 119, 0.58);
            }

            .lb-cubed-history-empty {
                grid-column: 1 / -1;
                padding: 7px;
                color: rgba(48, 24, 24, 0.62);
                font-size: 10px;
                font-style: italic;
                text-align: center;
            }

            @media (max-width: 600px) {
                #${HistoryOverlayId} {
                    padding: 8px;
                }

                .lb-cubed-history-modal {
                    max-height: 94vh;
                }

                .lb-cubed-history-navigation {
                    grid-template-columns:
                        auto
                        auto
                        minmax(0, 1fr)
                        auto
                        auto;
                    padding-left: 8px;
                    padding-right: 8px;
                }

                .lb-cubed-history-position {
                    padding-left: 2px;
                    padding-right: 2px;
                    font-size: 10px;
                }

                .lb-cubed-history-stat-grid {
                    grid-template-columns: 1fr;
                }

                .lb-cubed-history-sections {
                    grid-template-columns: 1fr;
                }
            }

            /*
                ================================================================
                RESPONSIVE TOP-LEVEL LBC GRID
                ================================================================

                Narrow -> wide cascade:

                - All sections stacked.
                - Completion/Longest stay together; Found/Unfound share a row.
                - Hints + Twofers share a row.
                - Hints + Twofers + Words by Length share a row.
                - Big 2 + Hints + Twofers + Length share row 1, words row 2.
                - All six top-level elements share one row when LBC is huge.
            */

            .lb-cubed-dashboard-grid {
                display: grid;
                grid-template-columns: minmax(0, 1fr);
                grid-template-areas:
                    "stats"
                    "hints"
                    "twofers"
                    "length"
                    "found"
                    "unfound";
                gap: 7px;
                align-items: start;
            }

            .lb-cubed-stat-grid {
                grid-area: stats;
                display: grid;
                grid-template-columns: 1fr;
                gap: 6px;
                margin: 0;
                min-width: 0;
            }

            .lb-cubed-hints-tree {
                grid-area: hints;
            }

            .lb-cubed-twofer-tree {
                grid-area: twofers;
            }

            .lb-cubed-length-tree {
                grid-area: length;
            }

            .lb-cubed-word-tree[data-cubed-section="FoundWords"] {
                grid-area: found;
            }

            .lb-cubed-word-tree[data-cubed-section="UnfoundWords"] {
                grid-area: unfound;
            }

            .lb-cubed-dashboard-grid > .lb-cubed-tree,
            .lb-cubed-dashboard-grid > .lb-cubed-stat-grid {
                margin: 0;
            }

            .lb-cubed-stat {
                min-width: 0;
                padding: 8px 6px;
                background: rgba(255, 255, 255, 0.18);
                border: 1px solid rgba(78, 34, 34, 0.32);
                border-radius: 3px;
                text-align: center;
            }

            .lb-cubed-stat-value {
                color: rgb(48, 24, 24);
                font-size: 16px;
                line-height: 1.15;
                font-weight: 700;
                overflow-wrap: anywhere;
            }

            .lb-cubed-stat-label {
                margin-top: 3px;
                color: rgba(48, 24, 24, 0.67);
                font-size: 9px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            .lb-cubed-tree,
            .lb-cubed-nested-tree {
                margin-top: 0;
                border: 1px solid rgba(78, 34, 34, 0.38);
                border-radius: 3px;
                overflow: hidden;
                min-width: 0;
            }

            .lb-cubed-tree > summary,
            .lb-cubed-nested-tree > summary {
                padding: 7px 8px;
                cursor: pointer;
                user-select: none;
                color: rgb(48, 24, 24);
                background: rgba(92, 37, 37, 0.11);
                font-size: 12px;
                font-weight: 700;
            }

            .lb-cubed-tree > summary:hover,
            .lb-cubed-nested-tree > summary:hover {
                background: rgba(92, 37, 37, 0.18);
            }

            /*
                Found and Unfound should not greedily stretch across wide rows.
                They remain compact and left-justified until LBC gets narrow.
            */
            .lb-cubed-word-tree {
                width: 100%;
                max-width: 220px;
                justify-self: start;
            }

            /*
                ================================================================
                HINTS
                ================================================================
            */

            .lb-cubed-hints-body {
                padding: 5px;
            }

            .lb-cubed-twofer-solution-indicator {
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 5px 6px;
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(78, 34, 34, 0.25);
                border-radius: 3px;
                font-size: 11px;
            }

            .lb-cubed-twofer-status-icon {
                display: inline-flex;
                flex: 0 0 17px;
                align-items: center;
                justify-content: center;
                width: 17px;
                height: 17px;
                border-radius: 50%;
                color: #fff;
                font-size: 11px;
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
                grid-template-columns:
                    repeat(auto-fit, minmax(125px, 1fr));
                gap: 5px;
                align-items: start;
            }

            .lb-cubed-potential-word-tree {
                min-width: 0;
            }

            .lb-cubed-potential-word-list {
                display: grid;
                grid-template-columns: 1fr;
                gap: 2px;
                padding: 4px;
            }

            .lb-cubed-potential-word {
                min-width: 0;
                padding: 3px 5px;
                background: rgba(255, 255, 255, 0.11);
                border-radius: 2px;
                color: rgba(48, 24, 24, 0.75);
                font-family: Consolas, "Courier New", monospace;
                font-size: 10px;
                overflow-wrap: anywhere;
            }

            .lb-cubed-potential-word-found {
                background: rgba(255, 255, 255, 0.28);
                color: rgb(42, 20, 20);
                font-weight: 700;
            }

            .lb-cubed-potential-word-empty {
                padding: 5px;
                color: rgba(48, 24, 24, 0.65);
                font-size: 10px;
                font-style: italic;
                text-align: center;
            }

            /*
                ================================================================
                TWOFERS
                ================================================================
            */

            /*
                Keep Twofers as a normal <summary> so Chrome supplies exactly
                the same native disclosure marker as every other details node.
            */
            .lb-cubed-twofer-summary {
                display: list-item;
            }

            .lb-cubed-twofer-summary-title {
                display: inline;
            }

            /*
                Controls live on their own line when expanded. This avoids
                fighting the native disclosure marker and works much better
                when Twofers occupies a narrow responsive column.
            */
            .lb-cubed-twofer-summary-actions {
                float: none;
                display: flex;
                align-items: center;
                justify-content: flex-start;
                gap: 6px;
                max-width: 100%;
                margin: 5px 0 0 0;
            }

            .lb-cubed-twofer-tree:not([open])
            .lb-cubed-twofer-summary-actions {
                display: none;
            }

            .lb-cubed-twofer-disclaimer {
                min-width: 0;
                color: rgba(48, 24, 24, 0.66);
                font-size: 9px;
                font-style: italic;
                font-weight: 400;
                text-align: left;
            }

            .lb-cubed-twofer-group-button {
                flex: 0 0 auto;
                padding: 3px 6px;
                color: rgb(48, 24, 24);
                background: rgba(255, 255, 255, 0.24);
                border: 1px solid rgba(78, 34, 34, 0.35);
                border-radius: 3px;
                font: inherit;
                font-size: 10px;
                font-weight: 700;
                cursor: pointer;
            }

            .lb-cubed-twofer-group-button:hover {
                background: rgba(255, 255, 255, 0.36);
            }

            .lb-cubed-twofer-body {
                padding: 4px;
            }

            .lb-cubed-twofer-group + .lb-cubed-twofer-group {
                margin-top: 6px;
            }

            .lb-cubed-twofer-group-title {
                margin-bottom: 3px;
                padding: 3px 5px;
                color: rgba(48, 24, 24, 0.78);
                background: rgba(92, 37, 37, 0.08);
                border-radius: 2px;
                font-size: 10px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }

            .lb-cubed-twofer-list {
                display: grid;
                grid-template-columns: 1fr;
                gap: 2px;
            }

            .lb-cubed-twofer-list-ungrouped {
                padding: 0;
            }

            .lb-cubed-twofer-group-empty {
                padding: 4px 5px;
                color: rgba(48, 24, 24, 0.55);
                font-size: 10px;
                font-style: italic;
            }

            .lb-cubed-twofer-row {
                display: grid;
                grid-template-columns:
                    minmax(0, 1fr)
                    16px
                    minmax(0, 1fr);
                gap: 3px;
                align-items: center;
                min-width: 0;
                padding: 1px;
                border-radius: 3px;
            }

            .lb-cubed-twofer-category-Found {
                background: rgba(255, 255, 255, 0.10);
            }

            .lb-cubed-twofer-word {
                display: block;
                min-width: 0;
                width: 100%;
                padding: 3px 4px;
                border-radius: 2px;
                font-family: Consolas, "Courier New", monospace;
                font-size: 10px;
                font-weight: 600;
                text-align: center;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .lb-cubed-twofer-arrow {
                color: rgba(48, 24, 24, 0.72);
                text-align: center;
                font-size: 12px;
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

            /*
                NYT's published solution.

                Every visible descendant inherits the same requested yellow
                background. A still-redacted solution word remains black,
                because spoiler protection outranks decoration.
            */
            .lb-cubed-nyt-solution {
                padding: 4px;
                background-color: rgb(218, 203, 119);
                border: 1px solid rgba(105, 88, 19, 0.45);
                border-radius: 4px;
            }

            .lb-cubed-nyt-solution-label {
                margin: 0 0 3px 1px;
                color: rgb(71, 57, 8);
                background-color: inherit !important;
                font-size: 10px;
                font-weight: 700;
                line-height: 1.2;
            }

            .lb-cubed-nyt-solution .lb-cubed-twofer-row,
            .lb-cubed-nyt-solution .lb-cubed-twofer-arrow,
            .lb-cubed-nyt-solution .lb-cubed-twofer-revealed {
                background-color: inherit !important;
            }

            .lb-cubed-nyt-solution .lb-cubed-twofer-redacted {
                background: #000 !important;
            }

            /*
                ================================================================
                WORDS BY LENGTH
                ================================================================
            */

            /*
                Always vertical. This keeps the section useful even when it is
                sitting beside Hints/Twofers in a narrow responsive row.
            */
            .lb-cubed-length-grid {
                display: grid;
                grid-template-columns: 1fr;
                gap: 2px;
                padding: 4px;
            }

            .lb-cubed-length-stat {
                display: flex;
                flex-direction: row;
                align-items: center;
                justify-content: space-between;
                min-width: 0;
                padding: 3px 5px;
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(78, 34, 34, 0.27);
                border-radius: 3px;
                text-align: left;
                font-size: 10px;
            }

            .lb-cubed-length-label {
                color: rgba(48, 24, 24, 0.77);
                white-space: nowrap;
            }

            .lb-cubed-length-value {
                margin: 0 0 0 6px;
                color: rgb(48, 24, 24);
                font-weight: 700;
                white-space: nowrap;
            }

            /*
                ================================================================
                FOUND / UNFOUND WORDS
                ================================================================
            */

            .lb-cubed-word-grid {
                display: grid;
                grid-template-columns: 1fr;
                gap: 2px;
                padding: 4px;
                overflow: visible;
            }

            .lb-cubed-word {
                display: block;
                width: 100%;
                min-width: 0;
                padding: 3px 5px;
                border-radius: 2px;
                font-family: Consolas, "Courier New", monospace;
                font-size: 10px;
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
                padding: 6px;
                color: rgba(48, 24, 24, 0.70);
                text-align: center;
                font-size: 10px;
                font-style: italic;
            }

            /*
                ================================================================
                LBC CONTAINER-QUERY CASCADE
                ================================================================
            */

            /*
                Completion + Longest Found stop stacking once LBC has enough
                room for two modest stat cards.
            */
            @container lbc (min-width: 340px) {
                .lb-cubed-stat-grid {
                    grid-template-columns:
                        repeat(2, minmax(0, 1fr));
                }
            }

            /*
                Found and Unfound are the first sections to share a row.
            */
            @container lbc (min-width: 390px) {
                .lb-cubed-dashboard-grid {
                    grid-template-columns:
                        repeat(2, minmax(0, 1fr));

                    grid-template-areas:
                        "stats stats"
                        "hints hints"
                        "twofers twofers"
                        "length length"
                        "found unfound";
                }

                .lb-cubed-word-tree {
                    max-width: 220px;
                }
            }

            /*
                Next, Hints and Twofers can sit beside one another. Words by
                Length remains below them.
            */
            @container lbc (min-width: 520px) {
                .lb-cubed-dashboard-grid {
                    grid-template-columns:
                        repeat(2, minmax(0, 1fr));

                    grid-template-areas:
                        "stats stats"
                        "hints twofers"
                        "length length"
                        "found unfound";
                }
            }

            /*
                Next stage: Hints, Twofers, and Words by Length share row 2;
                the Big 2 own row 1 and Found/Unfound own row 3.
            */
            @container lbc (min-width: 650px) {
                .lb-cubed-dashboard-grid {
                    grid-template-columns:
                        repeat(6, minmax(0, 1fr));

                    grid-template-areas:
                        "stats stats stats stats stats stats"
                        "hints hints twofers twofers length length"
                        "found found unfound unfound . .";
                }
            }

            /*
                At a generous width, Big 2 + Hints + Twofers + Length share the
                first row, while the word logs move to their own second row.
            */
            @container lbc (min-width: 860px) {
                .lb-cubed-dashboard-grid {
                    grid-template-columns:
                        minmax(250px, 2fr)
                        minmax(135px, 1fr)
                        minmax(220px, 1.6fr)
                        minmax(135px, 1fr);

                    grid-template-areas:
                        "stats hints twofers length"
                        "found unfound . .";
                }
            }

            /*
                Finally, when LBC itself is enormous, all six top-level
                elements can coexist on one row.
            */
            @container lbc (min-width: 1180px) {
                .lb-cubed-dashboard-grid {
                    grid-template-columns:
                        minmax(260px, 2fr)
                        minmax(130px, 1fr)
                        minmax(220px, 1.6fr)
                        minmax(125px, 1fr)
                        minmax(155px, 1fr)
                        minmax(155px, 1fr);

                    grid-template-areas:
                        "stats hints twofers length found unfound";
                }
            }

            /*
                Below 390px the word sections have each moved to their own row,
                so allow them to use the full available width. Below 340px the
                stat cards also stack, completing the requested cascade.
            */
            @container lbc (max-width: 389px) {
                .lb-cubed-word-tree {
                    max-width: none;
                }

                .lb-cubed-header {
                    flex-direction: column;
                }

                .lb-cubed-header-actions {
                    width: 100%;
                    justify-content: flex-start;
                }

                .lb-cubed-line-speed-control {
                    flex: 1 1 180px;
                }

                .lb-cubed-line-speed-slider {
                    flex: 1 1 auto;
                    width: auto;
                }
            }
        `;

        document.head.appendChild(Style);
    }

    Initialize();
})();
