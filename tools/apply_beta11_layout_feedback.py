from pathlib import Path

SOURCE = Path("LetterBoxedCubed.user.js")
CHANGELOG = Path("CHANGELOG.md")
DOCS = Path("docs/PREVIEW_TESTING.md")

text = SOURCE.read_text(encoding="utf-8")


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {count}")
    text = text.replace(old, new, 1)


replace_once(
    "// @version      1.12.0-beta.10",
    "// @version      1.12.0-beta.11",
    "version",
)

replace_once(
    '''    const MaximumHistoryLaneHeight =
        MinimumHistoryLaneHeight + MaximumLayoutGap;
    const MinimumNytPageScale = 0;''',
    '''    const MaximumHistoryLaneHeight =
        MinimumHistoryLaneHeight + MaximumLayoutGap;
    const ValidFeedbackHistoryClearance = 10;
    const MinimumNytPageScale = 0;''',
    "feedback clearance constant",
)

replace_once(
    '''    let GameObserver = null;
    let LayoutObserver = null;
    let ScanTimer = null;
    let LayoutTimer = null;''',
    '''    let GameObserver = null;
    let LayoutObserver = null;
    let SquareFeedbackObserver = null;
    let ValidFeedbackPlacementFrame = null;
    let ScanTimer = null;
    let LayoutTimer = null;''',
    "feedback observer globals",
)

replace_once(
    '''        ScanGameState(true);
        StartGameObserver();
        StartSubmissionHooks();''',
    '''        ScanGameState(true);
        StartGameObserver();
        StartSquareFeedbackObserver();
        StartSubmissionHooks();''',
    "feedback observer startup",
)

replace_once(
    '''            const SquareRect = SquareContainer.getBoundingClientRect();

            const Left = Math.max(
                0,
                Math.min(WordRect.left, SquareRect.left) - GameRect.left
            );
            const Right = Math.min(
                GameRect.width,
                Math.max(WordRect.right, SquareRect.right) - GameRect.left
            );
            /*
                Keep the visible horizontal grip a fixed distance ABOVE the
                GB boundary. That distance matches the visual offset of LBC's
                vertical resize-grip lines from the panel edge.
            */
            const GripLineY =
                SquareRect.top -
                ResizeGripLineOffset -
                GameRect.top;''',
    '''            const SquareRect = SquareContainer.getBoundingClientRect();

            const Left = Math.max(
                0,
                Math.min(WordRect.left, SquareRect.left) - GameRect.left
            );
            const Right = Math.min(
                GameRect.width,
                Math.max(WordRect.right, SquareRect.right) - GameRect.left
            );
            /*
                Position the grip in the gutter BELOW the history lane rather
                than relative to the square container's native box. NYT gives
                the square container its own vertical offset, which previously
                pulled the handle up across accepted-word history.
            */
            const GripLineY =
                WordRect.bottom +
                ResizeGripLineOffset -
                GameRect.top;''',
    "gap grip placement",
)

replace_once(
    '''        for (const Child of WordContainer.children) {
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

    function StartSubmissionHooks() {''',
    '''        for (const Child of WordContainer.children) {
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

        QueueValidWordFeedbackPlacement();
    }

    function GetVisibleHistoryContentBottom(ListContainer) {
        if (!ListContainer) {
            return null;
        }

        const ListRect = ListContainer.getBoundingClientRect();
        let Bottom = ListRect.top;
        let SawVisibleContent = false;

        for (const Selector of [
            ":scope > .lb-word-list-length",
            ":scope > .lb-word-list-container .lb-word-list"
        ]) {
            const Element = ListContainer.querySelector(Selector);
            if (!Element) {
                continue;
            }

            const Rect = Element.getBoundingClientRect();
            if (
                Rect.height <= 0 ||
                Rect.bottom <= ListRect.top ||
                Rect.top >= ListRect.bottom
            ) {
                continue;
            }

            SawVisibleContent = true;
            Bottom = Math.max(
                Bottom,
                Math.min(Rect.bottom, ListRect.bottom)
            );
        }

        return SawVisibleContent
            ? Bottom
            : null;
    }

    function ClearValidWordFeedbackProxy(Source = null) {
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

    function UpdateValidWordFeedbackPlacement() {
        ValidFeedbackPlacementFrame = null;

        const WordContainer = document.querySelector(
            ".lb-game-container .lb-word-container"
        );
        const TextFieldWrapper = WordContainer?.querySelector(
            ":scope > .lb-text-field-wrapper"
        );
        const ListContainer = WordContainer?.querySelector(
            ":scope > .lb-list-container"
        );
        const SquareContainer = document.querySelector(
            ".lb-game-container .lb-square-container"
        );
        const Source = SquareContainer?.querySelector(
            ":scope > .lb-message-box"
        );

        if (!TextFieldWrapper || !ListContainer || !Source) {
            ClearValidWordFeedbackProxy();
            return;
        }

        const MessageText = String(Source.textContent || "").trim();
        if (!MessageText) {
            ClearValidWordFeedbackProxy(Source);
            return;
        }

        const HistoryBottom = GetVisibleHistoryContentBottom(ListContainer);
        if (!Number.isFinite(HistoryBottom)) {
            ClearValidWordFeedbackProxy(Source);
            return;
        }

        const SourceRect = Source.getBoundingClientRect();
        const ShouldRelocate =
            SourceRect.width > 0 &&
            SourceRect.height > 0 &&
            SourceRect.top <
                HistoryBottom + ValidFeedbackHistoryClearance;

        if (!ShouldRelocate) {
            ClearValidWordFeedbackProxy(Source);
            return;
        }

        let Proxy = TextFieldWrapper.querySelector(
            ":scope > .lb-cubed-valid-feedback-proxy"
        );

        if (!Proxy) {
            Proxy = document.createElement("div");
            Proxy.className =
                "lb-message-box lb-cubed-valid-feedback-proxy";
            TextFieldWrapper.appendChild(Proxy);
        }

        Proxy.replaceChildren(
            ...[...Source.childNodes].map(Node => Node.cloneNode(true))
        );
        Source.classList.add(
            "lb-cubed-valid-feedback-relocated-source"
        );
    }

    function QueueValidWordFeedbackPlacement() {
        if (ValidFeedbackPlacementFrame !== null) {
            cancelAnimationFrame(ValidFeedbackPlacementFrame);
        }

        ValidFeedbackPlacementFrame = requestAnimationFrame(
            UpdateValidWordFeedbackPlacement
        );
    }

    function StartSquareFeedbackObserver() {
        const SquareContainer = document.querySelector(
            ".lb-game-container .lb-square-container"
        );

        if (!SquareContainer) {
            return;
        }

        SquareFeedbackObserver?.disconnect();
        SquareFeedbackObserver = new MutationObserver(
            QueueValidWordFeedbackPlacement
        );
        SquareFeedbackObserver.observe(SquareContainer, {
            childList: true,
            subtree: true,
            characterData: true
        });

        QueueValidWordFeedbackPlacement();
    }

    function StartSubmissionHooks() {''',
    "valid feedback relocation functions",
)

replace_once(
    '''        UpdateLayoutGapHandleVisibility();
        PositionLayoutGapResizeHandle();
        UpdateLogoPlaceholderSize();
        PositionPreviewDebugPane();''',
    '''        UpdateLayoutGapHandleVisibility();
        PositionLayoutGapResizeHandle();
        UpdateLogoPlaceholderSize();
        PositionPreviewDebugPane();
        QueueValidWordFeedbackPlacement();''',
    "feedback placement after layout",
)

replace_once(
    '''            .lb-game-container.${LayoutClass} {
                box-sizing: border-box !important;
                position: relative !important;
            }

            /*
                Issue #4: optional, explicit vertical-gap grip.''',
    '''            .lb-game-container.${LayoutClass} {
                box-sizing: border-box !important;
                position: relative !important;
            }

            /*
                Once Cubed owns TI/GB positioning as grid rows, NYT's native
                vertical square-container margins must not pull GB back upward
                into the reserved history lane. Horizontal margins are left
                untouched so NYT can keep its own board centering behavior.
            */
            .lb-game-container.${LayoutClass} > .lb-square-container {
                margin-top: 0 !important;
                margin-bottom: 0 !important;
            }

            /*
                Issue #4: optional, explicit vertical-gap grip.''',
    "square vertical margin normalization",
)

replace_once(
    '''            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-message-box {
                z-index: 4 !important;
            }

            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-par.no-words {''',
    '''            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-message-box {
                z-index: 4 !important;
            }

            /*
                NYT renders success praise in the square container, unlike its
                invalid-submission messages in the text-field wrapper. When the
                native praise position would crowd accepted-word history, Cubed
                mirrors it into the wrapper so NYT's own message-box positioning
                puts it in the same safe feedback area as validation errors.
            */
            .lb-cubed-valid-feedback-relocated-source {
                visibility: hidden !important;
                pointer-events: none !important;
            }

            .lb-cubed-valid-feedback-proxy {
                z-index: 5 !important;
                pointer-events: none !important;
            }

            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-par.no-words {''',
    "valid feedback proxy css",
)

SOURCE.write_text(text, encoding="utf-8")

changelog = CHANGELOG.read_text(encoding="utf-8")
entry = '''## 1.12.0-beta.11
- Removed NYT's native vertical margins from the square container while Cubed owns the TI/GB grid, preventing GB/canvas content from being pulled upward into the reserved history lane and blocking its scrollbar.
- Repositioned the draggable TI/GB grip into the gutter immediately below the history lane instead of anchoring it above the square container's native box.
- Added collision-aware valid-word feedback placement: if NYT's success message would crowd visible accepted-word history, Cubed mirrors it into the text-field wrapper where NYT already displays invalid-submission messages, with a small clearance buffer.

'''
marker = "# Changelog\n\n"
if entry not in changelog:
    if marker not in changelog:
        raise SystemExit("changelog heading not found")
    changelog = changelog.replace(marker, marker + entry, 1)
    CHANGELOG.write_text(changelog, encoding="utf-8")

docs = DOCS.read_text(encoding="utf-8")
docs = docs.replace(
    "The current source is `1.12.0-beta.10`.",
    "The current source is `1.12.0-beta.11`.",
    1,
)
old_gap = "- `.lb-list-container` is now an exact-height scroll viewport matching the reserved history lane rather than a flex-inferred remainder. Accepted-word history must scroll inside that lane before it can visually enter GB territory; GB remains fixed."
new_gap = old_gap + " Cubed also neutralizes NYT's native top/bottom margin on `.lb-square-container`, so the GB canvas can no longer be pulled upward across that lane or intercept its scrollbar; the draggable grip is positioned just below the lane."
if old_gap not in docs:
    raise SystemExit("preview gap bullet not found")
docs = docs.replace(old_gap, new_gap, 1)
hide_par_bullet = "- **Hide par** should hide only the actual `Try to solve in X words` prompt in both NYT DOM states. Invalid-submission feedback injected as `.lb-text-field-wrapper > .lb-message-box` (for example **Too short** and **Not in word list**) must remain visible and must not be clipped by the fixed TI/history lane."
replacement = hide_par_bullet + " Valid-word praise remains native when it has room; if its square-container position would crowd visible history, Cubed temporarily mirrors it into the text-field wrapper so it occupies the same safe feedback region as invalid messages."
if hide_par_bullet not in docs:
    raise SystemExit("preview feedback bullet not found")
docs = docs.replace(hide_par_bullet, replacement, 1)
DOCS.write_text(docs, encoding="utf-8")

required = [
    "// @version      1.12.0-beta.11",
    "let SquareFeedbackObserver = null;",
    "function UpdateValidWordFeedbackPlacement()",
    "margin-top: 0 !important;",
    "WordRect.bottom +",
    "lb-cubed-valid-feedback-proxy",
]
for needle in required:
    if needle not in text:
        raise SystemExit(f"missing validation marker: {needle}")
