from pathlib import Path

path = Path("tools/preview_runtime.js")
text = path.read_text(encoding="utf-8")


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    text = text.replace(old, new, 1)


# Keep preview chrome below NYT's native modal layer instead of trying to win z-index wars.
replace_once("""                z-index: 99999;""", """                z-index: 20;""", "version z-index")
replace_once("""                z-index: 100001;""", """                z-index: 22;""", "button z-index")
replace_once("""                z-index: 100010;""", """                z-index: 40;""", "history overlay z-index")
replace_once("""                z-index: 100000;""", """                z-index: 21;""", "debug pane z-index")

replace_once(
'''            #${PreviewHistoryTestPanelId} button {
                padding: 4px 8px;
                cursor: pointer;
            }
''',
'''            #${PreviewHistoryTestPanelId} button {
                padding: 4px 8px;
                cursor: pointer;
            }

            #${PreviewHistoryTestPanelId} button:disabled,
            #${PreviewHistoryTestPanelId} select:disabled {
                opacity: 0.45;
                cursor: not-allowed;
            }
''',
"disabled sandbox styling",
)

replace_once(
'''    let PreviewDebugObserver = null;
    let PreviewDebugRenderTimer = null;
''',
'''    let PreviewDebugObserver = null;
    let PreviewChromeObserver = null;
    let PreviewDebugRenderTimer = null;
''',
"preview chrome observer state",
)

# Restrict the sandbox to already-solved current-day twofers, and neutralize the
# selected pair inside the in-memory sandbox so those real discoveries do not
# prevent us from testing historical/partial/independent states.
replace_once(
'''    function GetPreviewHistoricalSelectedTwofer() {
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
''',
'''    function GetPreviewHistoricalAvailableTwofers() {
        const SolvedKeys =
            PreviewHistoricalBaseline?.FoundTwofers ||
            FoundTwofers;

        return Twofers.filter(
            Twofer => SolvedKeys.has(Twofer.Key)
        );
    }

    function GetPreviewHistoricalSelectedTwofer() {
        if (!PreviewHistoricalSelectedTwoferKey) {
            return null;
        }

        return GetPreviewHistoricalAvailableTwofers().find(
            Twofer => Twofer.Key === PreviewHistoricalSelectedTwoferKey
        ) || null;
    }

    function ChoosePreviewHistoricalDefaultTwofer() {
        const AvailableTwofers =
            GetPreviewHistoricalAvailableTwofers();

        PreviewHistoricalSelectedTwoferKey =
            AvailableTwofers[0]?.Key || null;
    }
''',
"restrict testable twofers",
)

replace_once(
'''        PreviouslyFoundWordsForPuzzle = new Set([
            ...PreviewHistoricalBaseline.PreviouslyFoundWordsForPuzzle,
            ...PreviewHistoricalInjectedWords
        ]);

        KnownWordsForPuzzle = new Set([
''',
'''        const HistoricalBaseline = new Set(
            PreviewHistoricalBaseline.PreviouslyFoundWordsForPuzzle
        );
        const SelectedTwofer =
            GetPreviewHistoricalSelectedTwofer();

        /*
            A testable pair necessarily exists in today's real FoundTwofers.
            Remove its two words from the real historical baseline while the
            scenario is active so First/Second/Both/Neither are deterministic.
        */
        if (SelectedTwofer) {
            HistoricalBaseline.delete(SelectedTwofer.First);
            HistoricalBaseline.delete(SelectedTwofer.Second);
        }

        PreviouslyFoundWordsForPuzzle = new Set([
            ...HistoricalBaseline,
            ...PreviewHistoricalInjectedWords
        ]);

        KnownWordsForPuzzle = new Set([
''',
"neutralize real historical state for selected pair",
)

replace_once(
'''        PreviewHistoricalInjectedWords = new Set();

        if (!KeepActive) {
            PreviewHistoricalTestModeActive = false;
            PreviewHistoricalBaseline = null;
        }

        RenderPanel();
''',
'''        PreviewHistoricalInjectedWords = new Set();

        if (KeepActive) {
            const SelectedTwofer =
                GetPreviewHistoricalSelectedTwofer();

            if (SelectedTwofer) {
                FoundTwofers.delete(SelectedTwofer.Key);
                FoundWords.delete(SelectedTwofer.First);
                FoundWords.delete(SelectedTwofer.Second);
                RecentWordHighlights.delete(SelectedTwofer.First);
                RecentWordHighlights.delete(SelectedTwofer.Second);
                RecentTwoferHighlights.delete(SelectedTwofer.Key);
            }
        } else {
            PreviewHistoricalTestModeActive = false;
            PreviewHistoricalBaseline = null;
        }

        RenderPanel();
''',
"neutralize selected solved pair in active sandbox",
)

replace_once(
'''        ChoosePreviewHistoricalDefaultTwofer();
        RecomputePreviewHistoricalSandboxState();
        UpdatePreviewHistoricalTestButton();
''',
'''        ChoosePreviewHistoricalDefaultTwofer();
        RestorePreviewHistoricalBaseline({ KeepActive: true });
        RecomputePreviewHistoricalSandboxState();
        UpdatePreviewHistoricalTestButton();
''',
"prepare selected pair when sandbox enters",
)

replace_once(
'''        Button.title = PreviewHistoricalTestModeActive
            ? "Historical-word sandbox is active. Google Drive sync and LBC progress writes are paused."
            : "Open preview-only historical-word/twofer sandbox";
    }
''',
'''        Button.title = PreviewHistoricalTestModeActive
            ? "Historical-word sandbox is active. Google Drive sync and LBC progress writes are paused."
            : "Open preview-only historical-word/twofer sandbox";

        /* Keep the Debug button anchored; the longer ACTIVE label grows left. */
        PositionPreviewDebugPane();
    }
''',
"reposition active history button",
)

replace_once(
'''        const Select = Panel.querySelector("select[data-lbc-history-test-twofer]");
        if (Select) {
            const ExistingValue = PreviewHistoricalSelectedTwoferKey || "";
            Select.replaceChildren();

            for (const Twofer of Twofers) {
''',
'''        const AvailableTwofers =
            GetPreviewHistoricalAvailableTwofers();
        const HasTestableTwofer = AvailableTwofers.length > 0;
        const Select = Panel.querySelector("select[data-lbc-history-test-twofer]");
        if (Select) {
            const ExistingValue = PreviewHistoricalSelectedTwoferKey || "";
            Select.replaceChildren();

            for (const Twofer of AvailableTwofers) {
''',
"populate only found twofers",
)

replace_once(
'''            if (
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
''',
'''            if (
                ExistingValue &&
                [...Select.options].some(Option => Option.value === ExistingValue)
            ) {
                Select.value = ExistingValue;
            } else if (Select.options.length) {
                Select.selectedIndex = 0;
                PreviewHistoricalSelectedTwoferKey = Select.value;
            } else {
                PreviewHistoricalSelectedTwoferKey = null;
            }

            Select.disabled = !HasTestableTwofer;
        }

        for (const Button of Panel.querySelectorAll("button")) {
            if (Button.dataset.lbcHistoryTestExit === "true") {
                Button.disabled = false;
                continue;
            }

            Button.disabled = !HasTestableTwofer;
        }

        const Status = Panel.querySelector(".lbc-history-test-status");
''',
"disable sandbox controls without found twofers",
)

replace_once(
'''        if (!Twofer) {
            Status.textContent = "No valid twofers are available for this puzzle.";
            return;
        }
''',
'''        if (!Twofer) {
            Status.textContent =
                "No twofers found today are available for safe testing. " +
                "Solve a twofer normally, then reopen History Test.";
            return;
        }
''',
"no spoiler-safe twofer message",
)

replace_once(
'''        const Exit = document.createElement("button");
        Exit.type = "button";
        Exit.textContent = "EXIT TEST MODE + restore real state";
''',
'''        const Exit = document.createElement("button");
        Exit.type = "button";
        Exit.dataset.lbcHistoryTestExit = "true";
        Exit.textContent = "EXIT TEST MODE + restore real state";
''',
"mark exit control",
)

# Add native-dialog awareness as a second layer beyond lower z-index values.
insert_anchor = '''    function StartPreviewDebugObserver() {
'''
if text.count(insert_anchor) != 1:
    raise RuntimeError("native modal helper anchor mismatch")
modal_helpers = '''    function IsVisiblePreviewNativeDialog() {
        const Candidates = document.querySelectorAll(
            'dialog[open], [role="dialog"], [aria-modal="true"]'
        );

        for (const Candidate of Candidates) {
            if (!(Candidate instanceof Element)) {
                continue;
            }

            if (Candidate.closest(
                `#${PreviewDebugPanelId}, #${PreviewHistoryTestOverlayId}`
            )) {
                continue;
            }

            const Style = getComputedStyle(Candidate);
            const Rect = Candidate.getBoundingClientRect();

            if (
                Style.display !== "none" &&
                Style.visibility !== "hidden" &&
                Number(Style.opacity || 1) !== 0 &&
                Rect.width > 0 &&
                Rect.height > 0
            ) {
                return true;
            }
        }

        return false;
    }

    function UpdatePreviewChromeForNativeDialog() {
        const Hide = IsVisiblePreviewNativeDialog();

        for (const Id of [
            PreviewVersionLabelId,
            PreviewDebugToggleButtonId,
            PreviewHistoryTestButtonId,
            PreviewDebugPanelId
        ]) {
            const ElementNode = document.getElementById(Id);
            if (ElementNode) {
                ElementNode.style.visibility = Hide ? "hidden" : "";
            }
        }
    }

    function StartPreviewChromeObserver() {
        PreviewChromeObserver?.disconnect();

        PreviewChromeObserver = new MutationObserver(() => {
            UpdatePreviewChromeForNativeDialog();
        });

        PreviewChromeObserver.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: [
                "class",
                "style",
                "open",
                "aria-hidden",
                "aria-modal"
            ]
        });

        UpdatePreviewChromeForNativeDialog();
    }

'''
text = text.replace(insert_anchor, modal_helpers + insert_anchor, 1)

replace_once(
'''        CreatePreviewHistoricalTestControls();

        window.addEventListener(
''',
'''        CreatePreviewHistoricalTestControls();
        StartPreviewChromeObserver();

        window.addEventListener(
''',
"start native modal observer",
)

path.write_text(text, encoding="utf-8")
print("Applied preview sandbox spoiler/layout/modal polish.")
