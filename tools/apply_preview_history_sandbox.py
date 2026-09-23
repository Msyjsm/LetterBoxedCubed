from pathlib import Path


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


path = Path("tools/preview_runtime.js")
text = path.read_text(encoding="utf-8")

text = replace_once(
    text,
    '''    const PreviewDebugToggleButtonId = "lb-cubed-preview-debug-toggle";\n    const PreviewVersionLabelId = "lb-cubed-preview-version";\n''',
    '''    const PreviewDebugToggleButtonId = "lb-cubed-preview-debug-toggle";\n    const PreviewHistoryTestButtonId = "lb-cubed-preview-history-test-toggle";\n    const PreviewHistoryTestOverlayId = "lb-cubed-preview-history-test-overlay";\n    const PreviewHistoryTestPanelId = "lb-cubed-preview-history-test-panel";\n    const PreviewVersionLabelId = "lb-cubed-preview-version";\n''',
    "preview sandbox ids",
)

text = replace_once(
    text,
    '''    let PreviewDebugPaneVisible = false;\n    const PreviewDebugElementIds = new WeakMap();\n''',
    '''    let PreviewDebugPaneVisible = false;\n    let PreviewHistoricalTestModeActive = false;\n    let PreviewHistoricalInjectedWords = new Set();\n    let PreviewHistoricalBaseline = null;\n    let PreviewHistoricalSelectedTwoferKey = null;\n    const PreviewDebugElementIds = new WeakMap();\n''',
    "preview sandbox state",
)

text = replace_once(
    text,
    '''    function IsPreviewDebugTypingContext(Target) {\n        return Boolean(\n            Target instanceof Element &&\n            Target.closest(`#${PreviewDebugPanelId}`)\n        );\n    }\n''',
    '''    function IsPreviewDebugTypingContext(Target) {\n        return Boolean(\n            Target instanceof Element &&\n            Target.closest(\n                `#${PreviewDebugPanelId}, #${PreviewHistoryTestOverlayId}`\n            )\n        );\n    }\n''',
    "sandbox typing context",
)

text = replace_once(
    text,
    '''            #${PreviewDebugToggleButtonId} {\n                position: absolute;\n                z-index: 100001;\n                padding: 4px 7px;\n                border: 1px solid rgba(255, 255, 255, 0.45);\n                border-radius: 3px;\n                background: rgba(20, 20, 24, 0.96);\n                color: #f2f2f2;\n                box-shadow: 0 3px 12px rgba(0, 0, 0, 0.32);\n                font: 700 11px/1.25 Arial, sans-serif;\n                white-space: nowrap;\n                cursor: pointer;\n            }\n\n            #${PreviewDebugToggleButtonId}:hover {\n                background: #303038;\n            }\n''',
    '''            #${PreviewDebugToggleButtonId},\n            #${PreviewHistoryTestButtonId} {\n                position: absolute;\n                z-index: 100001;\n                padding: 4px 7px;\n                border: 1px solid rgba(255, 255, 255, 0.45);\n                border-radius: 3px;\n                background: rgba(20, 20, 24, 0.96);\n                color: #f2f2f2;\n                box-shadow: 0 3px 12px rgba(0, 0, 0, 0.32);\n                font: 700 11px/1.25 Arial, sans-serif;\n                white-space: nowrap;\n                cursor: pointer;\n            }\n\n            #${PreviewDebugToggleButtonId}:hover,\n            #${PreviewHistoryTestButtonId}:hover {\n                background: #303038;\n            }\n\n            #${PreviewHistoryTestButtonId}.lbc-history-test-active {\n                border-color: #ffd166;\n                background: #4a3510;\n                color: #fff3c4;\n            }\n\n            #${PreviewHistoryTestOverlayId} {\n                position: fixed;\n                inset: 0;\n                z-index: 100010;\n                display: flex;\n                align-items: center;\n                justify-content: center;\n                padding: 18px;\n                background: rgba(0, 0, 0, 0.42);\n            }\n\n            #${PreviewHistoryTestPanelId} {\n                width: min(620px, calc(100vw - 36px));\n                max-height: calc(100vh - 36px);\n                overflow: auto;\n                padding: 14px;\n                border: 1px solid #777;\n                border-radius: 6px;\n                background: #18181d;\n                color: #f4f4f4;\n                box-shadow: 0 8px 36px rgba(0, 0, 0, 0.52);\n                font: 12px/1.4 Arial, sans-serif;\n            }\n\n            #${PreviewHistoryTestPanelId} * {\n                box-sizing: border-box;\n            }\n\n            #${PreviewHistoryTestPanelId} h2 {\n                margin: 0 0 8px;\n                font-size: 16px;\n            }\n\n            #${PreviewHistoryTestPanelId} .lbc-history-test-warning {\n                margin: 0 0 10px;\n                padding: 8px;\n                border: 1px solid #8b6b1f;\n                border-radius: 4px;\n                background: #34290f;\n                color: #ffe7a3;\n            }\n\n            #${PreviewHistoryTestPanelId} .lbc-history-test-grid {\n                display: grid;\n                grid-template-columns: 1fr 1fr;\n                gap: 8px;\n                margin: 8px 0;\n            }\n\n            #${PreviewHistoryTestPanelId} .lbc-history-test-block {\n                padding: 8px;\n                border: 1px solid #555;\n                border-radius: 4px;\n                background: #222229;\n            }\n\n            #${PreviewHistoryTestPanelId} .lbc-history-test-actions {\n                display: flex;\n                flex-wrap: wrap;\n                gap: 5px;\n                margin-top: 6px;\n            }\n\n            #${PreviewHistoryTestPanelId} button,\n            #${PreviewHistoryTestPanelId} select {\n                min-height: 28px;\n                border: 1px solid #777;\n                border-radius: 3px;\n                background: #303038;\n                color: #fff;\n                font: 12px/1.3 Arial, sans-serif;\n            }\n\n            #${PreviewHistoryTestPanelId} button {\n                padding: 4px 8px;\n                cursor: pointer;\n            }\n\n            #${PreviewHistoryTestPanelId} select {\n                width: 100%;\n                padding: 3px 5px;\n            }\n\n            #${PreviewHistoryTestPanelId} .lbc-history-test-status {\n                margin-top: 10px;\n                padding: 8px;\n                border: 1px solid #555;\n                border-radius: 4px;\n                background: #101014;\n                font: 11px/1.45 Consolas, "Courier New", monospace;\n                white-space: pre-wrap;\n            }\n\n            @media (max-width: 680px) {\n                #${PreviewHistoryTestPanelId} .lbc-history-test-grid {\n                    grid-template-columns: 1fr;\n                }\n            }\n''',
    "sandbox styles",
)

text = replace_once(
    text,
    '''        const DebugPanel = document.getElementById(PreviewDebugPanelId);\n        const ToggleButton = document.getElementById(PreviewDebugToggleButtonId);\n        const Panel = document.getElementById(PanelId);\n\n        if (!DebugPanel || !ToggleButton || !Panel) {\n''',
    '''        const DebugPanel = document.getElementById(PreviewDebugPanelId);\n        const ToggleButton = document.getElementById(PreviewDebugToggleButtonId);\n        const HistoryTestButton = document.getElementById(PreviewHistoryTestButtonId);\n        const Panel = document.getElementById(PanelId);\n\n        if (!DebugPanel || !ToggleButton || !Panel) {\n''',
    "sandbox position lookup",
)

text = replace_once(
    text,
    '''        ToggleButton.style.left = `${ToggleLeft}px`;\n        ToggleButton.style.top = `${ToggleTop}px`;\n\n        const ToggleRect = ToggleButton.getBoundingClientRect();\n''',
    '''        ToggleButton.style.left = `${ToggleLeft}px`;\n        ToggleButton.style.top = `${ToggleTop}px`;\n\n        if (HistoryTestButton) {\n            const HistoryWidth = Math.max(1, HistoryTestButton.offsetWidth);\n            const HistoryLeft = Clamp(\n                ToggleLeft - HistoryWidth - 4,\n                ScrollX + 8,\n                Math.max(\n                    ScrollX + 8,\n                    ScrollX + window.innerWidth - HistoryWidth - 8\n                )\n            );\n            HistoryTestButton.style.left = `${HistoryLeft}px`;\n            HistoryTestButton.style.top = `${ToggleTop}px`;\n        }\n\n        const ToggleRect = ToggleButton.getBoundingClientRect();\n''',
    "sandbox button positioning",
)

sandbox_code = r'''

    // -------------------------------------------------------------------------
    // Preview-only historical-word sandbox
    // -------------------------------------------------------------------------

    function GetPreviewHistoricalSelectedTwofer() {
        if (!PreviewHistoricalSelectedTwoferKey) {
            return null;
        }

        return Twofers.find(
            Twofer => Twofer.Key === PreviewHistoricalSelectedTwoferKey
        ) || null;
    }

    function ChoosePreviewHistoricalDefaultTwofer() {
        if (!Twofers.length) {
            PreviewHistoricalSelectedTwoferKey = null;
            return;
        }

        const Candidate =
            Twofers.find(Twofer =>
                !FoundTwofers.has(Twofer.Key) &&
                (!KnownWordsForPuzzle.has(Twofer.First) ||
                    !KnownWordsForPuzzle.has(Twofer.Second))
            ) ||
            Twofers.find(Twofer => !FoundTwofers.has(Twofer.Key)) ||
            Twofers[0];

        PreviewHistoricalSelectedTwoferKey = Candidate?.Key || null;
    }

    function RecomputePreviewHistoricalSandboxState() {
        if (!PreviewHistoricalTestModeActive || !PreviewHistoricalBaseline) {
            return;
        }

        PreviouslyFoundWordsForPuzzle = new Set([
            ...PreviewHistoricalBaseline.PreviouslyFoundWordsForPuzzle,
            ...PreviewHistoricalInjectedWords
        ]);

        KnownWordsForPuzzle = new Set([
            ...PreviouslyFoundWordsForPuzzle,
            ...FoundWords
        ]);
    }

    function SnapshotPreviewHistoricalBaseline() {
        PreviewHistoricalBaseline = {
            FoundWords: new Set(FoundWords),
            FoundTwofers: new Set(FoundTwofers),
            PreviouslyFoundWordsForPuzzle:
                new Set(PreviouslyFoundWordsForPuzzle),
            KnownWordsForPuzzle: new Set(KnownWordsForPuzzle),
            RecentWordHighlights: new Map(RecentWordHighlights),
            RecentTwoferHighlights: new Map(RecentTwoferHighlights)
        };
    }

    function RestorePreviewHistoricalBaseline({ KeepActive = false } = {}) {
        if (!PreviewHistoricalBaseline) {
            return;
        }

        FoundWords = new Set(PreviewHistoricalBaseline.FoundWords);
        FoundTwofers = new Set(PreviewHistoricalBaseline.FoundTwofers);
        PreviouslyFoundWordsForPuzzle = new Set(
            PreviewHistoricalBaseline.PreviouslyFoundWordsForPuzzle
        );
        KnownWordsForPuzzle = new Set(
            PreviewHistoricalBaseline.KnownWordsForPuzzle
        );

        RecentWordHighlights.clear();
        for (const [Key, Value] of PreviewHistoricalBaseline.RecentWordHighlights) {
            RecentWordHighlights.set(Key, Value);
        }

        RecentTwoferHighlights.clear();
        for (const [Key, Value] of PreviewHistoricalBaseline.RecentTwoferHighlights) {
            RecentTwoferHighlights.set(Key, Value);
        }

        PreviewHistoricalInjectedWords = new Set();

        if (!KeepActive) {
            PreviewHistoricalTestModeActive = false;
            PreviewHistoricalBaseline = null;
        }

        RenderPanel();
        QueuePanelLayoutUpdate();
        UpdatePreviewHistoricalTestButton();
        RenderPreviewHistoricalTestPanel();
    }

    function EnterPreviewHistoricalTestMode() {
        if (PreviewHistoricalTestModeActive) {
            return true;
        }

        if (CloudSyncInFlight) {
            alert(
                "LBC is currently syncing with Google Drive. Wait for that sync to finish, then start History Test mode again."
            );
            return false;
        }

        if (CloudSyncTimer) {
            clearTimeout(CloudSyncTimer);
            CloudSyncTimer = null;
        }
        CloudSyncPending = false;

        SnapshotPreviewHistoricalBaseline();
        PreviewHistoricalTestModeActive = true;
        PreviewHistoricalInjectedWords = new Set();
        ChoosePreviewHistoricalDefaultTwofer();
        RecomputePreviewHistoricalSandboxState();
        UpdatePreviewHistoricalTestButton();

        console.info(
            "[Letter Boxed Cubed][preview] Historical test mode enabled. " +
            "LBC progress persistence and Google Drive sync are paused."
        );
        return true;
    }

    function ExitPreviewHistoricalTestMode() {
        if (!PreviewHistoricalTestModeActive) {
            return;
        }

        RestorePreviewHistoricalBaseline();

        console.info(
            "[Letter Boxed Cubed][preview] Historical test mode disabled; " +
            "real LBC state restored."
        );
    }

    function SetPreviewHistoricalInjection(Mode) {
        if (!EnterPreviewHistoricalTestMode()) {
            return;
        }

        const Twofer = GetPreviewHistoricalSelectedTwofer();
        if (!Twofer) {
            return;
        }

        PreviewHistoricalInjectedWords = new Set();

        if (Mode === "First" || Mode === "Both") {
            PreviewHistoricalInjectedWords.add(Twofer.First);
        }
        if (Mode === "Second" || Mode === "Both") {
            PreviewHistoricalInjectedWords.add(Twofer.Second);
        }

        RecomputePreviewHistoricalSandboxState();
        RenderPanel();
        QueuePanelLayoutUpdate();
        RenderPreviewHistoricalTestPanel();
    }

    function SimulatePreviewHistoricalWordDiscovery(Position) {
        if (!EnterPreviewHistoricalTestMode()) {
            return;
        }

        const Twofer = GetPreviewHistoricalSelectedTwofer();
        const Word = Position === "Second"
            ? Twofer?.Second
            : Twofer?.First;

        if (!Word || FoundWords.has(Word)) {
            RenderPreviewHistoricalTestPanel();
            return;
        }

        const ShouldHighlight = ShouldHighlightWordDiscovery(Word);
        FoundWords.add(Word);

        if (ShouldHighlight) {
            MarkWordForHighlight(Word);
        }

        RecomputePreviewHistoricalSandboxState();
        RenderPanel();
        QueuePanelLayoutUpdate();
        RenderPreviewHistoricalTestPanel();
    }

    function SimulatePreviewHistoricalTwoferSolve() {
        if (!EnterPreviewHistoricalTestMode()) {
            return;
        }

        const Twofer = GetPreviewHistoricalSelectedTwofer();
        if (!Twofer) {
            return;
        }

        MarkTwoferFound(Twofer.First, Twofer.Second);
        RecomputePreviewHistoricalSandboxState();
        RenderPanel();
        QueuePanelLayoutUpdate();
        RenderPreviewHistoricalTestPanel();
    }

    function UpdatePreviewHistoricalTestButton() {
        const Button = document.getElementById(PreviewHistoryTestButtonId);
        if (!Button) {
            return;
        }

        Button.textContent = PreviewHistoricalTestModeActive
            ? "History Test (ACTIVE)"
            : "History Test";
        Button.classList.toggle(
            "lbc-history-test-active",
            PreviewHistoricalTestModeActive
        );
        Button.title = PreviewHistoricalTestModeActive
            ? "Historical-word sandbox is active. Google Drive sync and LBC progress writes are paused."
            : "Open preview-only historical-word/twofer sandbox";
    }

    function RenderPreviewHistoricalTestPanel() {
        const Panel = document.getElementById(PreviewHistoryTestPanelId);
        if (!Panel) {
            return;
        }

        const Select = Panel.querySelector("select[data-lbc-history-test-twofer]");
        if (Select) {
            const ExistingValue = PreviewHistoricalSelectedTwoferKey || "";
            Select.replaceChildren();

            for (const Twofer of Twofers) {
                const Option = document.createElement("option");
                Option.value = Twofer.Key;
                const Category = GetTwoferCategory(Twofer);
                Option.textContent = `${Twofer.First} -> ${Twofer.Second}  [${Category}]`;
                Select.appendChild(Option);
            }

            if (
                ExistingValue &&
                [...Select.options].some(Option => Option.value === ExistingValue)
            ) {
                Select.value = ExistingValue;
            } else if (Select.options.length) {
                Select.selectedIndex = 0;
                PreviewHistoricalSelectedTwoferKey = Select.value;
            }
        }

        const Status = Panel.querySelector(".lbc-history-test-status");
        const Twofer = GetPreviewHistoricalSelectedTwofer();

        if (!Status) {
            return;
        }

        if (!Twofer) {
            Status.textContent = "No valid twofers are available for this puzzle.";
            return;
        }

        const Category = GetTwoferCategory(Twofer);
        const Visibility = GetTwoferWordVisibility(Twofer, Category);
        const HintStats = CalculateTwoferHintStats();
        const DescribeWord = Word => {
            const Flags = [];
            if (PreviewHistoricalInjectedWords.has(Word)) {
                Flags.push("TEST historical");
            } else if (PreviewHistoricalBaseline?.PreviouslyFoundWordsForPuzzle.has(Word)) {
                Flags.push("real historical");
            }
            if (FoundWords.has(Word)) {
                Flags.push("found today/in sandbox");
            }
            if (!Flags.length) {
                Flags.push("unknown");
            }
            return `${Word}: ${Flags.join(", ")}`;
        };

        Status.textContent = [
            `Mode: ${PreviewHistoricalTestModeActive ? "ACTIVE - persistence/sync paused" : "inactive"}`,
            DescribeWord(Twofer.First),
            DescribeWord(Twofer.Second),
            `Twofer category: ${Category}`,
            `Visible words: first=${Visibility.FirstVisible}, second=${Visibility.SecondVisible}`,
            `Independent-solution indicator: ${HintStats.HasUnconnectedFoundSolution}`,
            `Exact pair solved in sandbox: ${FoundTwofers.has(Twofer.Key)}`,
            `Word highlights active: first=${RecentWordHighlights.has(Twofer.First)}, second=${RecentWordHighlights.has(Twofer.Second)}`
        ].join("\n");
    }

    function OpenPreviewHistoricalTestPanel() {
        if (!EnterPreviewHistoricalTestMode()) {
            return;
        }

        let Overlay = document.getElementById(PreviewHistoryTestOverlayId);
        if (Overlay) {
            RenderPreviewHistoricalTestPanel();
            return;
        }

        Overlay = document.createElement("div");
        Overlay.id = PreviewHistoryTestOverlayId;

        const Panel = document.createElement("section");
        Panel.id = PreviewHistoryTestPanelId;

        const Heading = document.createElement("h2");
        Heading.textContent = "PREVIEW Historical Word Sandbox";

        const Warning = document.createElement("div");
        Warning.className = "lbc-history-test-warning";
        Warning.textContent =
            "Safe LBC sandbox: progress writes and Google Drive sync are paused. " +
            "This does NOT replace NYT's own internal game state, so use these simulation buttons rather than typing into NYT if you want zero effect on today's real NYT progress.";

        const SelectLabel = document.createElement("label");
        SelectLabel.textContent = "Current-board twofer to test:";
        const Select = document.createElement("select");
        Select.dataset.lbcHistoryTestTwofer = "true";
        Select.addEventListener("change", () => {
            PreviewHistoricalSelectedTwoferKey = Select.value;
            RestorePreviewHistoricalBaseline({ KeepActive: true });
            RecomputePreviewHistoricalSandboxState();
            RenderPanel();
            RenderPreviewHistoricalTestPanel();
        });
        SelectLabel.appendChild(Select);

        const Grid = document.createElement("div");
        Grid.className = "lbc-history-test-grid";

        const HistoricalBlock = document.createElement("div");
        HistoricalBlock.className = "lbc-history-test-block";
        HistoricalBlock.innerHTML = "<strong>Pretend these were found on an earlier day</strong>";
        const HistoricalActions = document.createElement("div");
        HistoricalActions.className = "lbc-history-test-actions";

        for (const [Label, Mode] of [
            ["First only", "First"],
            ["Second only", "Second"],
            ["Both", "Both"],
            ["Neither", "Neither"]
        ]) {
            const Button = document.createElement("button");
            Button.type = "button";
            Button.textContent = Label;
            Button.addEventListener("click", () => SetPreviewHistoricalInjection(Mode));
            HistoricalActions.appendChild(Button);
        }
        HistoricalBlock.appendChild(HistoricalActions);

        const DiscoveryBlock = document.createElement("div");
        DiscoveryBlock.className = "lbc-history-test-block";
        DiscoveryBlock.innerHTML = "<strong>Simulate today's discoveries</strong>";
        const DiscoveryActions = document.createElement("div");
        DiscoveryActions.className = "lbc-history-test-actions";

        const FindFirst = document.createElement("button");
        FindFirst.type = "button";
        FindFirst.textContent = "Find first today";
        FindFirst.addEventListener(
            "click",
            () => SimulatePreviewHistoricalWordDiscovery("First")
        );

        const FindSecond = document.createElement("button");
        FindSecond.type = "button";
        FindSecond.textContent = "Find second today";
        FindSecond.addEventListener(
            "click",
            () => SimulatePreviewHistoricalWordDiscovery("Second")
        );

        const SolvePair = document.createElement("button");
        SolvePair.type = "button";
        SolvePair.textContent = "Solve exact pair";
        SolvePair.addEventListener("click", SimulatePreviewHistoricalTwoferSolve);

        DiscoveryActions.append(
            FindFirst,
            FindSecond,
            SolvePair
        );
        DiscoveryBlock.appendChild(DiscoveryActions);

        Grid.append(
            HistoricalBlock,
            DiscoveryBlock
        );

        const Status = document.createElement("pre");
        Status.className = "lbc-history-test-status";

        const Footer = document.createElement("div");
        Footer.className = "lbc-history-test-actions";

        const Reset = document.createElement("button");
        Reset.type = "button";
        Reset.textContent = "Reset sandbox";
        Reset.addEventListener("click", () => {
            RestorePreviewHistoricalBaseline({ KeepActive: true });
            RecomputePreviewHistoricalSandboxState();
            RenderPanel();
            RenderPreviewHistoricalTestPanel();
        });

        const Close = document.createElement("button");
        Close.type = "button";
        Close.textContent = "Hide panel (keep sandbox active)";
        Close.addEventListener("click", () => Overlay.remove());

        const Exit = document.createElement("button");
        Exit.type = "button";
        Exit.textContent = "EXIT TEST MODE + restore real state";
        Exit.addEventListener("click", () => {
            Overlay.remove();
            ExitPreviewHistoricalTestMode();
        });

        Footer.append(
            Reset,
            Close,
            Exit
        );

        Panel.append(
            Heading,
            Warning,
            SelectLabel,
            Grid,
            Status,
            Footer
        );
        Overlay.appendChild(Panel);
        document.body.appendChild(Overlay);

        Overlay.addEventListener("click", Event => {
            if (Event.target === Overlay) {
                Overlay.remove();
            }
        });

        RenderPreviewHistoricalTestPanel();
    }

    function CreatePreviewHistoricalTestControls() {
        if (
            UserscriptBuildChannel !== "preview" ||
            document.getElementById(PreviewHistoryTestButtonId)
        ) {
            return;
        }

        const Button = document.createElement("button");
        Button.id = PreviewHistoryTestButtonId;
        Button.type = "button";
        Button.addEventListener("click", OpenPreviewHistoricalTestPanel);
        document.body.appendChild(Button);
        UpdatePreviewHistoricalTestButton();
        PositionPreviewDebugPane();
    }

    function InstallPreviewHistoricalSandboxGuards() {
        const OriginalScheduleCloudSync = ScheduleCloudSync;
        ScheduleCloudSync = function (...Args) {
            if (PreviewHistoricalTestModeActive) {
                return;
            }
            return OriginalScheduleCloudSync(...Args);
        };

        const OriginalSyncWithGoogleDrive = SyncWithGoogleDrive;
        SyncWithGoogleDrive = async function (...Args) {
            if (PreviewHistoricalTestModeActive) {
                console.info(
                    "[Letter Boxed Cubed][preview] Google Drive sync suppressed by History Test mode."
                );
                return;
            }
            return OriginalSyncWithGoogleDrive(...Args);
        };

        const OriginalSaveFoundWords = SaveFoundWords;
        SaveFoundWords = function (...Args) {
            if (PreviewHistoricalTestModeActive) {
                RecomputePreviewHistoricalSandboxState();
                return;
            }
            return OriginalSaveFoundWords(...Args);
        };

        const OriginalSaveFoundTwofers = SaveFoundTwofers;
        SaveFoundTwofers = function (...Args) {
            if (PreviewHistoricalTestModeActive) {
                return;
            }
            return OriginalSaveFoundTwofers(...Args);
        };

        const OriginalSaveGlobalWordHistory = SaveGlobalWordHistory;
        SaveGlobalWordHistory = function (...Args) {
            if (PreviewHistoricalTestModeActive) {
                return;
            }
            return OriginalSaveGlobalWordHistory(...Args);
        };
    }
'''

text = replace_once(
    text,
    '''    function CreatePreviewDebugPane() {\n''',
    sandbox_code + '''\n    function CreatePreviewDebugPane() {\n''',
    "sandbox implementation insertion",
)

text = replace_once(
    text,
    '''        window.addEventListener(\n            "resize",\n            PositionPreviewDebugPane\n        );\n    }\n''',
    '''        CreatePreviewHistoricalTestControls();\n\n        window.addEventListener(\n            "resize",\n            PositionPreviewDebugPane\n        );\n    }\n\n    InstallPreviewHistoricalSandboxGuards();\n''',
    "sandbox activation",
)

path.write_text(text, encoding="utf-8")

# Keep the preview-testing doc explicit about this being a preview-only test harness.
docs_path = Path("docs/PREVIEW_TESTING.md")
docs = docs_path.read_text(encoding="utf-8")
marker = "## Preview-only debugging\n"
if marker in docs and "Historical Word Sandbox" not in docs:
    docs = docs.replace(
        marker,
        marker + "\n- **Historical Word Sandbox:** use the `History Test` button next to `Show Debug Pane` to inject either half (or both halves) of any current-board Twofer as previously found, simulate finding those words today, or simulate solving the exact pair. While active, LBC Found Words / Found Twofers / global-history persistence and Google Drive sync are suppressed; exiting restores the exact pre-test in-memory state. The sandbox deliberately does not rewrite NYT's own game engine, so use its simulation buttons rather than typing into NYT when testing.\n",
        1,
    )
docs_path.write_text(docs, encoding="utf-8")
