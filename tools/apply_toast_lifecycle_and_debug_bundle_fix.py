from pathlib import Path

SOURCE = Path("LetterBoxedCubed.user.js")
PREVIEW = Path("tools/preview_runtime.js")
TESTS = Path("tests/final-polish-tests.js")
DOC = Path("docs/THEMES.md")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


source = SOURCE.read_text(encoding="utf-8")
source = replace_once(
    source,
    "// @version      1.13.1-beta.12",
    "// @version      1.13.1-beta.13",
    "version"
)

source = replace_once(
    source,
    '''    let ValidFeedbackGeneration = 0;
    let ActiveValidFeedbackSource = null;
    let ActiveValidFeedbackText = "";
    let PendingValidFeedbackBaselineChainLength = null;
    let PendingValidFeedbackStartedAt = 0;
    const ValidFeedbackSettlePollMs = 30;
    const ValidFeedbackSettleMaximumMs = 400;''',
    '''    let ValidFeedbackGeneration = 0;
    let ActiveValidFeedbackSource = null;
    let ActiveValidFeedbackText = "";
    let PendingValidFeedbackBaselineChainLength = null;
    let PendingValidFeedbackStartedAt = 0;
    let ValidFeedbackClearTimer = null;
    let ValidFeedbackProxyShownAt = 0;
    const ValidFeedbackSettlePollMs = 30;
    const ValidFeedbackSettleMaximumMs = 400;
    const ValidFeedbackProxyMinimumVisibleMs = 600;''',
    "valid feedback lifecycle state"
)

source = replace_once(
    source,
    '''    function ClearValidWordFeedbackProxy(Source = null) {
        clearTimeout(ValidFeedbackPlacementTimer);
        ValidFeedbackPlacementTimer = null;
        RenderedValidFeedbackKey = null;
        ActiveValidFeedbackSource = null;
        ActiveValidFeedbackText = "";
        PendingValidFeedbackBaselineChainLength = null;
        PendingValidFeedbackStartedAt = 0;

        document.querySelectorAll(".lb-cubed-valid-feedback-proxy")
            .forEach(Element => Element.remove());

        if (Source) {
            Source.classList.remove(
                "lb-cubed-valid-feedback-relocated-source"
            );
        } else {
            document.querySelectorAll(
                ".lb-cubed-valid-feedback-relocated-source"
            ).forEach(Element => Element.classList.remove(
                "lb-cubed-valid-feedback-relocated-source"
            ));
        }
    }

    function PositionValidWordFeedbackProxy(''',
    '''    function ClearValidWordFeedbackProxy(Source = null) {
        clearTimeout(ValidFeedbackPlacementTimer);
        ValidFeedbackPlacementTimer = null;
        clearTimeout(ValidFeedbackClearTimer);
        ValidFeedbackClearTimer = null;
        RenderedValidFeedbackKey = null;
        ActiveValidFeedbackSource = null;
        ActiveValidFeedbackText = "";
        PendingValidFeedbackBaselineChainLength = null;
        PendingValidFeedbackStartedAt = 0;
        ValidFeedbackProxyShownAt = 0;

        document.querySelectorAll(".lb-cubed-valid-feedback-proxy")
            .forEach(Element => Element.remove());

        if (Source) {
            Source.classList.remove(
                "lb-cubed-valid-feedback-relocated-source"
            );
        } else {
            document.querySelectorAll(
                ".lb-cubed-valid-feedback-relocated-source"
            ).forEach(Element => Element.classList.remove(
                "lb-cubed-valid-feedback-relocated-source"
            ));
        }
    }

    function ScheduleValidWordFeedbackProxyClear() {
        clearTimeout(ValidFeedbackClearTimer);

        const VisibleFor = ValidFeedbackProxyShownAt
            ? performance.now() - ValidFeedbackProxyShownAt
            : 0;
        const Delay = Math.max(
            0,
            ValidFeedbackProxyMinimumVisibleMs - VisibleFor
        );

        ValidFeedbackClearTimer = setTimeout(() => {
            ValidFeedbackClearTimer = null;
            ClearValidWordFeedbackProxy();
        }, Delay);
    }

    function PositionValidWordFeedbackProxy(''',
    "valid feedback clear lifecycle"
)

source = replace_once(
    source,
    '''            !TextFieldWrapper ||
            !ListContainer ||
            !SquareContainer ||
            !Source
        ) {
            ClearValidWordFeedbackProxy();
            return;
        }

        const MessageText = String(Source.textContent || "").trim();
        if (!MessageText) {
            ClearValidWordFeedbackProxy(Source);
            return;
        }

        /*
            Wait until NYT has committed the accepted word to history before
            making Cubed's proxy visible. The native box appears first; the
            history DOM can lag it by a couple hundred milliseconds. Showing
            the proxy before that commit made it appear in the old normal
            position and then jump above TI when wrapping finally settled.

            The 400ms ceiling is only a safety fallback for an unexpected NYT
            state where the history count does not advance.
        */''',
    '''            !TextFieldWrapper ||
            !ListContainer ||
            !SquareContainer
        ) {
            ClearValidWordFeedbackProxy();
            return;
        }

        /*
            Snapshot praise text at lifecycle start and keep using it even if
            NYT clears its native toast before the delayed history DOM commit.
            Dark mode can shorten the native success-message lifecycle to less
            than our settling window; tying proxy creation to Source existence
            therefore made the toast disappear only in dark mode.
        */
        const MessageText = String(
            Source?.textContent || ActiveValidFeedbackText || ""
        ).trim();
        if (!MessageText) {
            ClearValidWordFeedbackProxy(Source);
            return;
        }

        if (Source) {
            ActiveValidFeedbackSource = Source;
            ActiveValidFeedbackText = MessageText;
        }

        /*
            Wait until NYT has committed the accepted word to history before
            making Cubed's proxy visible. The native box appears first; the
            history DOM can lag it by a couple hundred milliseconds. Showing
            the proxy before that commit made it appear in the old normal
            position and then jump above TI when wrapping finally settled.

            Crucially, this settling wait is now owned by Cubed's captured
            lifecycle, not by the continued existence of NYT's native node.
            The 400ms ceiling remains the fallback when history does not move.
        */''',
    "source-independent feedback settling"
)

source = replace_once(
    source,
    '''            Proxy.textContent = String(Source.textContent || "").trim();
            GameContainer.appendChild(Proxy);
            RenderedValidFeedbackKey = FeedbackKey;
        }

        PositionValidWordFeedbackProxy(''',
    '''            Proxy.textContent = MessageText;
            GameContainer.appendChild(Proxy);
            RenderedValidFeedbackKey = FeedbackKey;
            ValidFeedbackProxyShownAt = performance.now();
        } else if (!ValidFeedbackProxyShownAt) {
            ValidFeedbackProxyShownAt = performance.now();
        }

        PositionValidWordFeedbackProxy(''',
    "captured feedback text"
)

source = replace_once(
    source,
    '''        Source.classList.add(
            "lb-cubed-valid-feedback-relocated-source"
        );
    }

    function QueueValidWordFeedbackPlacement() {''',
    '''        if (Source) {
            clearTimeout(ValidFeedbackClearTimer);
            ValidFeedbackClearTimer = null;
            Source.classList.add(
                "lb-cubed-valid-feedback-relocated-source"
            );
        } else {
            /*
                NYT has already retired its native success node. Keep Cubed's
                independently-owned praise visible for at least the same rough
                perceptual lifetime as the normal light-mode toast.
            */
            ScheduleValidWordFeedbackProxyClear();
        }
    }

    function QueueValidWordFeedbackPlacement() {''',
    "source-independent feedback cleanup"
)

source = replace_once(
    source,
    '''            if (StartsNewLifecycle) {
                ActiveValidFeedbackSource = Source;
                ActiveValidFeedbackText = MessageText;
                ValidFeedbackGeneration++;
                PendingValidFeedbackBaselineChainLength =
                    ReadCurrentChain().length;
                PendingValidFeedbackStartedAt = performance.now();
            } else {''',
    '''            if (StartsNewLifecycle) {
                clearTimeout(ValidFeedbackClearTimer);
                ValidFeedbackClearTimer = null;
                document.querySelectorAll(".lb-cubed-valid-feedback-proxy")
                    .forEach(Element => Element.remove());
                RenderedValidFeedbackKey = null;
                ValidFeedbackProxyShownAt = 0;

                ActiveValidFeedbackSource = Source;
                ActiveValidFeedbackText = MessageText;
                ValidFeedbackGeneration++;
                PendingValidFeedbackBaselineChainLength =
                    ReadCurrentChain().length;
                PendingValidFeedbackStartedAt = performance.now();
            } else {''',
    "new feedback lifecycle reset"
)

SOURCE.write_text(source, encoding="utf-8")

preview = PREVIEW.read_text(encoding="utf-8")
preview = replace_once(
    preview,
    "                InternalPanelLayoutMode,",
    "                InternalPanelLayoutStage,",
    "debug bundle stale layout variable"
)

preview = replace_once(
    preview,
    '''        AddButton(
            "Copy Full Debug Bundle",
            () => CopyPreviewDiagnostic(
                GetPreviewDebugBundle(),
                "Full debug bundle"
            )
        );''',
    '''        AddButton(
            "Copy Full Debug Bundle",
            () => {
                try {
                    return CopyPreviewDiagnostic(
                        GetPreviewDebugBundle(),
                        "Full debug bundle"
                    );
                } catch (ErrorValue) {
                    console.error(
                        "[Letter Boxed Cubed][preview] Could not build full debug bundle.",
                        ErrorValue
                    );
                    return CopyPreviewDiagnostic(
                        {
                            GeneratedAt: new Date().toISOString(),
                            PreviewVersion: GetRunningUserscriptVersion(),
                            DebugBundleError: {
                                Name: ErrorValue?.name || "Error",
                                Message: String(ErrorValue?.message || ErrorValue),
                                Stack: String(ErrorValue?.stack || "")
                            },
                            Geometry: GetPreviewGeometrySnapshot(),
                            TransientTrace: structuredClone(PreviewTransientTrace)
                        },
                        "Full debug bundle fallback"
                    );
                }
            }
        );''',
    "debug bundle fallback"
)
PREVIEW.write_text(preview, encoding="utf-8")

tests = TESTS.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    "assert(source.includes('// @version      1.13.1-beta.12'), 'beta.12 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.13'), 'beta.13 version missing');",
    "test version"
)
anchor = "assert(source.includes('Proxy.textContent = MessageText'), 'valid-word toast does not preserve captured praise text');\n"
if anchor not in tests:
    insert_after = "assert(source.includes('Proxy.className = \"lb-cubed-valid-feedback-proxy\"'), 'self-owned valid-word toast proxy missing');\n"
    tests = replace_once(
        tests,
        insert_after,
        insert_after +
        "assert(source.includes('ValidFeedbackProxyMinimumVisibleMs = 600'), 'source-independent toast minimum lifetime missing');\n" +
        "assert(source.includes('Source?.textContent || ActiveValidFeedbackText'), 'toast settling still requires live NYT source');\n" +
        anchor,
        "toast lifecycle tests"
    )

preview_anchor = "assert(preview.includes('GetPreviewDebugBundle'), 'full debug bundle function missing');\n"
if "stale InternalPanelLayoutMode" not in tests:
    tests = replace_once(
        tests,
        preview_anchor,
        preview_anchor +
        "assert(preview.includes('InternalPanelLayoutStage'), 'debug bundle does not use current layout stage');\n" +
        "assert(!preview.includes('                InternalPanelLayoutMode,'), 'debug bundle still references stale InternalPanelLayoutMode');\n" +
        "assert(preview.includes('Full debug bundle fallback'), 'debug bundle copy lacks failure fallback');\n",
        "debug bundle tests"
    )
TESTS.write_text(tests, encoding="utf-8")

doc = DOC.read_text(encoding="utf-8")
doc += '''\nDark-mode toast timing note: NYT can retire its native success node before Cubed's 400ms history-settling window completes. Cubed therefore snapshots the praise text/lifecycle immediately, finishes history settling independently of the native node, and guarantees its own proxy at least 600ms of visible time once shown. This preserves stable placement without depending on NYT's shorter dark-mode toast lifetime.\n'''
DOC.write_text(doc, encoding="utf-8")
