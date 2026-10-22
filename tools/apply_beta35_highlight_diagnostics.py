from pathlib import Path

PreviewPath = Path("tools/preview_runtime.js")
SourcePath = Path("LetterBoxedCubed.user.js")
TestsPath = Path("tests/final-polish-tests.js")

Preview = PreviewPath.read_text()
Source = SourcePath.read_text()
Tests = TestsPath.read_text()

if "// @version      1.13.1-beta.35" in Source:
    print("beta.35 already installed")
    raise SystemExit(0)

def ReplaceOnce(Text, Old, New, Description):
    Count = Text.count(Old)
    if Count != 1:
        raise SystemExit(f"{Description}: wanted 1 occurrence, saw {Count}")
    return Text.replace(Old, New, 1)

Source = ReplaceOnce(Source, "// @version      1.13.1-beta.34", "// @version      1.13.1-beta.35", "version")

Preview = ReplaceOnce(Preview,
    '    const PreviewTransientTrace = [];\n',
    '    const PreviewTransientTrace = [];\n'
    '    const PreviewHighlightTrace = [];\n'
    '    let PreviewHighlightTraceStart = performance.now();\n',
    "trace state"
)

DiagnosticMethods = r'''
    // ---------------------------------------------------------
    // Preview-only highlight continuity diagnostics (bug #39).
    // Passive, bounded logging: intentionally does not change
    // core highlight timing or the stored found-word data.
    // ---------------------------------------------------------

    function RecordPreviewHighlightTrace(Type, Details = {}) {
        const Entry = {
            At: new Date().toISOString(),
            ElapsedMs: Math.round((performance.now() - PreviewHighlightTraceStart) * 10) / 10,
            Type,
            ...Details
        };
        PreviewHighlightTrace.push(Entry);
        if (PreviewHighlightTrace.length > 1200) {
            PreviewHighlightTrace.splice(0, PreviewHighlightTrace.length - 1200);
        }
        return Entry;
    }

    function DescribePreviewHighlightNode(Node) {
        if (!(Node instanceof Element)) {
            return null;
        }

        const Animation = typeof Node.getAnimations === "function"
            ? Node.getAnimations().find(Item =>
                String(Item.animationName || "").includes("lb-cubed-new-highlight")
            )
            : null;

        const Timing = Animation?.effect?.getTiming?.() || null;
        return {
            Word: Node.dataset.cubedWord || null,
            Twofer: Node.dataset.cubedTwofer || null,
            Text: (Node.textContent || "").trim().slice(0, 90),
            ClassName: String(Node.className || "").slice(0, 180),
            DurationCss: Node.style.getPropertyValue("--lb-cubed-highlight-duration") || null,
            AnimationName: Animation?.animationName || null,
            AnimationCurrentMs: typeof Animation?.currentTime === "number"
                ? Math.round(Animation.currentTime) : null,
            AnimationStartMs: typeof Animation?.startTime === "number"
                ? Math.round(Animation.startTime) : null,
            AnimationDurationMs: Timing?.duration ?? null,
            AnimationDelayMs: Timing?.delay ?? null,
            AnimationState: Animation?.playState || null
        };
    }

    function SnapshotPreviewHighlights() {
        const Nodes = [...document.querySelectorAll(
            "#" + PanelId + " .lb-cubed-new-highlight"
        )];
        return {
            ActiveNodeCount: Nodes.length,
            Sample: Nodes.slice(0, 16).map(DescribePreviewHighlightNode)
        };
    }

    function GetPreviewHighlightTraceJson() {
        return JSON.stringify({
            Version: "1.13.1-beta.35",
            CapturedAt: new Date().toISOString(),
            Bug: "https://github.com/Msyjsm/LetterBoxedCubed/issues/39",
            RecentWords: [...RecentWordHighlights].map(([Key, Expiry]) => ({
                Word: Key,
                RemainingMs: Math.max(0, Expiry - Date.now())
            })),
            RecentTwofers: [...RecentTwoferHighlights].map(([Key, Expiry]) => ({
                Twofer: Key,
                RemainingMs: Math.max(0, Expiry - Date.now())
            })),
            Trace: PreviewHighlightTrace
        }, null, 2);
    }

    function ResetPreviewNewWordHighlights() {
        const ClearedWords = [...RecentWordHighlights.keys()];
        const ClearedTwofers = [...RecentTwoferHighlights.keys()];
        PreviewHighlightTrace.length = 0;
        PreviewHighlightTraceStart = performance.now();
        RecentWordHighlights.clear();
        RecentTwoferHighlights.clear();
        RecordPreviewHighlightTrace("reset-active-highlights", {
            ClearedWords, ClearedTwofers,
            Note: "Only live highlight animations were reset. No stored words or NYT data were cleared."
        });
        RenderPanel();
        QueuePanelLayoutUpdate();
        const Status = document.querySelector(".lbc-highlight-test-status");
        if (Status) {
            Status.textContent = "Highlight animations reset; trace recording (0s). Now submit words normally, then copy the trace.";
        }
    }

    async function CopyPreviewHighlightTrace() {
        const Json = GetPreviewHighlightTraceJson();
        const Status = document.querySelector(".lbc-highlight-test-status");
        try {
            await navigator.clipboard.writeText(Json);
            if (Status) {
                Status.textContent = "Copied " + PreviewHighlightTrace.length + " trace entries to clipboard.";
            }
        } catch (ErrorValue) {
            console.info("[Letter Boxed Cubed][highlight trace] Clipboard unavailable; use DevTools:", Json);
            if (Status) {
                Status.textContent = "Clipboard unavailable. In DevTools Console run: copy(window.__LetterBoxedCubedGetHighlightTrace())";
            }
        }
    }

    function InstallPreviewHighlightDiagnostics() {
        try {
            PageWindow.__LetterBoxedCubedGetHighlightTrace = GetPreviewHighlightTraceJson;
        } catch {}

        document.addEventListener("animationstart", Event => {
            if (!String(Event.animationName).includes("lb-cubed-new-highlight") ||
                !Event.target?.closest?.("#" + PanelId)) {
                return;
            }
            RecordPreviewHighlightTrace("animation-start", {
                ElapsedAnimationSeconds: Event.elapsedTime,
                Node: DescribePreviewHighlightNode(Event.target)
            });
        }, true);

        for (const [EventType, Label] of [
            ["animationcancel", "animation-cancel"],
            ["animationend", "animation-end"]
        ]) {
            document.addEventListener(EventType, Event => {
                if (!String(Event.animationName).includes("lb-cubed-new-highlight") ||
                    !Event.target?.closest?.("#" + PanelId)) {
                    return;
                }
                RecordPreviewHighlightTrace(Label, {
                    ElapsedAnimationSeconds: Event.elapsedTime,
                    Node: DescribePreviewHighlightNode(Event.target)
                });
            }, true);
        }

        const OriginalRegisterHighlight = RegisterRecentHighlight;
        RegisterRecentHighlight = function (MapValue, Key, ...Args) {
            const PreviousExpiry = MapValue.get(Key) ?? null;
            const Result = OriginalRegisterHighlight(MapValue, Key, ...Args);
            RecordPreviewHighlightTrace("highlight-registered", {
                Kind: MapValue === RecentWordHighlights ? "word" :
                    MapValue === RecentTwoferHighlights ? "twofer" : "other",
                Key,
                PreviousExpiry,
                ExpiresAt: MapValue.get(Key) ?? null,
                DurationMs: (MapValue.get(Key) ?? Date.now()) - Date.now()
            });
            return Result;
        };

        const OriginalRender = RenderPanel;
        let RenderSequence = 0;
        RenderPanel = function (...Args) {
            RenderSequence++;
            RecordPreviewHighlightTrace("render-start", {
                RenderSequence,
                Before: SnapshotPreviewHighlights()
            });
            const Result = OriginalRender(...Args);
            RecordPreviewHighlightTrace("render-end", {
                RenderSequence,
                After: SnapshotPreviewHighlights()
            });
            return Result;
        };

        const OriginalSubmissionAttempt = HandleSubmissionAttempt;
        HandleSubmissionAttempt = function (...Args) {
            const Word = ReadCurrentInputWord();
            const Chain = ReadCurrentChain();
            RecordPreviewHighlightTrace("submission-attempt", {
                Word,
                Chain,
                AlreadyFound: FoundWords.has(Word),
                PotentialTwofer: Chain.length === 1
                    ? MakeTwoferKey(Chain[0], Word)
                    : null,
                PotentialTwoferAlreadyFound: Chain.length === 1
                    ? FoundTwofers.has(MakeTwoferKey(Chain[0], Word))
                    : null
            });
            return OriginalSubmissionAttempt(...Args);
        };

        const OriginalMarkTwofer = MarkTwoferFound;
        MarkTwoferFound = function (First, Second, ...Args) {
            const Key = MakeTwoferKey(NormalizeWord(First), NormalizeWord(Second));
            const PreviouslyFound = FoundTwofers.has(Key);
            const FirstAlreadyFound = FoundWords.has(NormalizeWord(First));
            const SecondAlreadyFound = FoundWords.has(NormalizeWord(Second));
            const Result = OriginalMarkTwofer(First, Second, ...Args);
            RecordPreviewHighlightTrace("twofer-check", {
                Key, PreviouslyFound, FirstAlreadyFound, SecondAlreadyFound,
                NewlyRegistered: Boolean(Result)
            });
            return Result;
        };

        RecordPreviewHighlightTrace("diagnostics-installed");
    }

'''

Preview = ReplaceOnce(Preview,
    '    // -------------------------------------------------------------------------\n    // Preview-only DOM inspector\n',
    DiagnosticMethods +
    '    // -------------------------------------------------------------------------\n    // Preview-only DOM inspector\n',
    "diagnostics injection"
)

Preview = ReplaceOnce(Preview,
    '''            if (Button.dataset.lbcHistoryTestExit === "true") {
                Button.disabled = false;
                continue;
            }
''',
    '''            if (
                Button.dataset.lbcHistoryTestExit === "true" ||
                Button.dataset.lbcHighlightTestAction === "true"
            ) {
                Button.disabled = false;
                continue;
            }
''',
    "keep highlight trace buttons usable without a twofer"
)

Preview = ReplaceOnce(Preview,
    '''        LongestSection.append(LongestHeading, LongestInput);

        Panel.append(Heading, HistoricalSection, LongestSection, Footer);
''',
    '''        LongestSection.append(LongestHeading, LongestInput);

        const HighlightSection = document.createElement("section");
        HighlightSection.className = "lbc-test-bed-section";
        const HighlightHeading = document.createElement("h3");
        HighlightHeading.textContent = "New Word Highlights";
        const HighlightNote = document.createElement("p");
        HighlightNote.textContent =
            "Reset active fades and clear the trace, then enter words normally. " +
            "This does not erase found words or NYT progress. " +
            "The trace records registrations, submissions, twofer checks, " +
            "dashboard redraws, and CSS animation start/cancel/end.";
        const HighlightActions = document.createElement("div");
        HighlightActions.className = "lbc-history-test-actions";

        const HighlightReset = document.createElement("button");
        HighlightReset.type = "button";
        HighlightReset.dataset.lbcHighlightTestAction = "true";
        HighlightReset.textContent = "Reset new-word highlights + trace";
        HighlightReset.addEventListener("click", ResetPreviewNewWordHighlights);

        const HighlightCopy = document.createElement("button");
        HighlightCopy.type = "button";
        HighlightCopy.dataset.lbcHighlightTestAction = "true";
        HighlightCopy.textContent = "Copy highlight trace";
        HighlightCopy.addEventListener("click", CopyPreviewHighlightTrace);

        const HighlightStatus = document.createElement("div");
        HighlightStatus.className = "lbc-highlight-test-status";
        HighlightStatus.textContent =
            "Ready. Reset first, then hide Test Beds and submit words. " +
            "Reopen Test Beds to copy the trace.";

        HighlightActions.append(HighlightReset, HighlightCopy);
        HighlightSection.append(
            HighlightHeading, HighlightNote, HighlightActions, HighlightStatus
        );

        Panel.append(
            Heading, HistoricalSection, LongestSection, HighlightSection, Footer
        );
''',
    "new test bed UI"
)

Preview = ReplaceOnce(Preview,
    '''    InstallPreviewHistoricalSandboxGuards();
''',
    '''    InstallPreviewHistoricalSandboxGuards();
    InstallPreviewHighlightDiagnostics();
''',
    "install diagnostics"
)

Tests = ReplaceOnce(Tests,
    "assert(source.includes('// @version      1.13.1-beta.34'), 'beta.34 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.35'), 'beta.35 version missing');",
    "test version"
)

TestAppend = r'''

// beta.35: Preview-only, non-destructive highlight-continuity Test Bed and trace.
assert(preview.includes('HighlightHeading.textContent = "New Word Highlights"'), 'new highlights Test Bed missing');
assert(preview.includes('function ResetPreviewNewWordHighlights()'), 'highlight reset missing');
assert(preview.includes('RecentWordHighlights.clear();'), 'word highlight reset missing');
assert(preview.includes('RecentTwoferHighlights.clear();'), 'twofer highlight reset missing');
assert(preview.includes('function CopyPreviewHighlightTrace()'), 'highlight trace copy missing');
assert(preview.includes('["animationcancel", "animation-cancel"]'), 'CSS cancel trace missing');
assert(preview.includes('"animation-start"'), 'CSS animation start trace missing');
assert(preview.includes('"render-start"'), 'redraw trace missing');
assert(preview.includes('"submission-attempt"'), 'submission trace missing');
assert(preview.includes('"twofer-check"'), 'twofer trace missing');
assert(preview.includes('InstallPreviewHighlightDiagnostics();'), 'diagnostics not installed');
console.log('PASS: beta.35 highlight-continuity diagnostic checks');
'''
Tests += TestAppend

SourcePath.write_text(Source)
PreviewPath.write_text(Preview)
TestsPath.write_text(Tests)
print("Applied beta.35 preview highlight diagnostics and Test Bed")
