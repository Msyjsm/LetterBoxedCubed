from pathlib import Path

path = Path("LetterBoxedCubed.user.js")
source = path.read_text(encoding="utf-8")

def replace_once(old, new, label):
    global source
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly 1 match, found {count}")
    source = source.replace(old, new, 1)

# Version bump.
replace_once(
    "// @version      1.11.0-beta.1",
    "// @version      1.11.0-beta.2",
    "version"
)

# History UI constants.
replace_once(
    '    const GoogleDriveButtonId = "lb-cubed-google-drive-button";\n',
    '    const GoogleDriveButtonId = "lb-cubed-google-drive-button";\n'
    '    const BrowseHistoryButtonId = "lb-cubed-browse-history-button";\n'
    '    const HistoryOverlayId = "lb-cubed-history-overlay";\n',
    "history constants"
)

# Fix UI strings that accidentally double-escaped newline characters.
replace_once(
    '"Google Drive sync uses a small Google Apps Script bridge that you own.\\\\n\\\\n" +',
    '"Google Drive sync uses a small Google Apps Script bridge that you own.\\n\\n" +',
    "Drive setup prompt newlines"
)
replace_once(
    'Button.title = StatusParts.join("\\\\n");',
    'Button.title = StatusParts.join("\\n");',
    "Drive status tooltip newlines"
)

history_functions = r'''
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

'''

anchor = '''    // -------------------------------------------------------------------------
    // Google Drive cloud sync (via user-owned Apps Script bridge)
    // -------------------------------------------------------------------------
'''
replace_once(
    anchor,
    history_functions + anchor,
    "history functions insertion"
)

browse_button_block = r'''
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

'''

replace_once(
    '        const GoogleDriveButton = document.createElement("button");\n',
    browse_button_block +
    '        const GoogleDriveButton = document.createElement("button");\n',
    "browse history button"
)

replace_once(
    '''            LineSpeedControl,
            GoogleDriveButton,
            ExportButton,
''',
    '''            LineSpeedControl,
            BrowseHistoryButton,
            GoogleDriveButton,
            ExportButton,
''',
    "header action order"
)

history_css = r'''
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

'''

css_anchor = '''            /*
                ================================================================
                RESPONSIVE TOP-LEVEL LBC GRID
'''
replace_once(
    css_anchor,
    history_css + css_anchor,
    "history CSS insertion"
)

path.write_text(source, encoding="utf-8")
print("Patched LetterBoxedCubed.user.js to v1.11.0-beta.2")
