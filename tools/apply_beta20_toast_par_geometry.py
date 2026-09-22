from pathlib import Path


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


source_path = Path("LetterBoxedCubed.user.js")
source = source_path.read_text(encoding="utf-8")

source = replace_once(
    source,
    "// @version      1.12.0-beta.19",
    "// @version      1.12.0-beta.20",
    "version bump",
)

source = replace_once(
    source,
    """    const ValidFeedbackHistoryClearance = 10;\n    const MinimumNytPageScale = 0;""",
    """    const ValidFeedbackHistoryLineThreshold = 2;\n    const ValidFeedbackNormalSlotInset = 1;\n    const ValidFeedbackParMarginFallback = 10;\n    const MinimumNytPageScale = 0;""",
    "toast geometry constants",
)

old_history_helper = r'''    function GetVisibleHistoryContentBottom(ListContainer) {
        if (!ListContainer) {
            return null;
        }

        /*
            The count label is intentionally outside the scrolling viewport.
            Collision detection therefore measures only the actually visible
            accepted-word content inside .lb-word-list-container.
        */
        const HistoryViewport = ListContainer.querySelector(
            ":scope > .lb-word-list-container"
        );
        const HistoryList = HistoryViewport?.querySelector(
            ":scope > .lb-word-list"
        );

        if (!HistoryViewport || !HistoryList) {
            return null;
        }

        const ViewportRect = HistoryViewport.getBoundingClientRect();
        const ListRect = HistoryList.getBoundingClientRect();

        if (
            ViewportRect.height <= 0 ||
            ListRect.height <= 0 ||
            ListRect.bottom <= ViewportRect.top ||
            ListRect.top >= ViewportRect.bottom
        ) {
            return null;
        }

        return Math.min(
            ListRect.bottom,
            ViewportRect.bottom
        );
    }
'''

new_history_helper = r'''    function CountRenderedHistoryLines(ListContainer) {
        const HistoryViewport = ListContainer?.querySelector(
            ":scope > .lb-word-list-container"
        );
        const HistoryList = HistoryViewport?.querySelector(
            ":scope > .lb-word-list"
        );

        if (!HistoryViewport || !HistoryList) {
            return 0;
        }

        /*
            The toast's jump rule is semantic now: the lower slot is available
            for exactly one rendered history line. Do not infer that from NYT's
            toast rectangle, because moving GB for a visible par also moves that
            native rectangle and changes the answer for the wrong reason.

            Range fragments let us count wrapped visual lines even when the
            history is made of several inline/span fragments. Group fragments
            that share the same vertical center into one rendered line.
        */
        const Range = document.createRange();
        Range.selectNodeContents(HistoryList);

        const LineCenters = [];
        for (const Rect of Range.getClientRects()) {
            if (Rect.width <= 0 || Rect.height <= 0) {
                continue;
            }

            const CenterY = (Rect.top + Rect.bottom) / 2;
            const ExistingLine = LineCenters.some(
                Existing => Math.abs(Existing - CenterY) <= 2
            );

            if (!ExistingLine) {
                LineCenters.push(CenterY);
            }
        }

        if (LineCenters.length) {
            return LineCenters.length;
        }

        /* Fallback for browsers that return no Range fragments. */
        const Rect = HistoryList.getBoundingClientRect();
        if (Rect.height <= 0) {
            return 0;
        }

        const Style = getComputedStyle(HistoryList);
        let LineHeight = Number.parseFloat(Style.lineHeight);
        if (!Number.isFinite(LineHeight) || LineHeight <= 0) {
            const FontSize = Number.parseFloat(Style.fontSize) || 16;
            LineHeight = FontSize * 1.2;
        }

        return Math.max(
            1,
            Math.round(Rect.height / LineHeight)
        );
    }

    function GetNormalFeedbackParMarginTop(WordContainer) {
        const Par = WordContainer?.querySelector(
            ":scope > .lb-par"
        );

        if (!Par) {
            return ValidFeedbackParMarginFallback;
        }

        const MarginTop = Number.parseFloat(
            getComputedStyle(Par).marginTop
        );

        return Number.isFinite(MarginTop)
            ? Math.max(0, MarginTop)
            : ValidFeedbackParMarginFallback;
    }
'''

source = replace_once(
    source,
    old_history_helper,
    new_history_helper,
    "history-line helper",
)

old_position = r'''    function PositionValidWordFeedbackProxy(
        Proxy,
        Source,
        GameContainer,
        TextFieldWrapper,
        ListContainer
    ) {
        const GameRect = GameContainer.getBoundingClientRect();
        const InputRect = TextFieldWrapper.getBoundingClientRect();
        const SourceRect = Source.getBoundingClientRect();
        const ProxyRect = Proxy.getBoundingClientRect();
        const HistoryBottom = GetVisibleHistoryContentBottom(ListContainer);

        const ShouldRelocate =
            Number.isFinite(HistoryBottom) &&
            SourceRect.width > 0 &&
            SourceRect.height > 0 &&
            SourceRect.top <
                HistoryBottom + ValidFeedbackHistoryClearance;

        let Left;
        let Top;

        if (ShouldRelocate) {
            Left =
                ((InputRect.left + InputRect.right) / 2) -
                GameRect.left -
                (ProxyRect.width / 2);
            Top = Math.max(
                0,
                InputRect.top -
                GameRect.top -
                ProxyRect.height -
                8
            );
        } else {
            /*
                Native praise is always suppressed while Cubed controls TI/GB.
                When there is no collision, reproduce NYT's final rendered
                position exactly rather than briefly showing NYT's own box.
            */
            Left = SourceRect.left - GameRect.left;
            Top = SourceRect.top - GameRect.top;
        }

        Proxy.style.setProperty(
            "left",
            `${Math.round(Left)}px`,
            "important"
        );
        Proxy.style.setProperty(
            "top",
            `${Math.round(Top)}px`,
            "important"
        );
    }
'''

new_position = r'''    function PositionValidWordFeedbackProxy(
        Proxy,
        GameContainer,
        WordContainer,
        TextFieldWrapper,
        ListContainer,
        SquareContainer
    ) {
        const GameRect = GameContainer.getBoundingClientRect();
        const InputRect = TextFieldWrapper.getBoundingClientRect();
        const HistoryRect = ListContainer.getBoundingClientRect();
        const SquareRect = SquareContainer.getBoundingClientRect();
        const ProxyRect = Proxy.getBoundingClientRect();
        const HistoryLineCount = CountRenderedHistoryLines(ListContainer);

        /*
            One history line leaves the calibrated second-line slot available
            for praise. As soon as the history actually wraps to line two, that
            slot belongs to history and praise jumps above TI. This decision is
            deliberately independent of par visibility and of NYT's native
            toast rectangle.
        */
        const ShouldRelocate =
            HistoryLineCount >= ValidFeedbackHistoryLineThreshold;

        let Left;
        let Top;

        if (ShouldRelocate) {
            Left =
                ((InputRect.left + InputRect.right) / 2) -
                GameRect.left -
                (ProxyRect.width / 2);
            Top = Math.max(
                0,
                InputRect.top -
                GameRect.top -
                ProxyRect.height -
                8
            );
        } else {
            /*
                The 90px baseline history lane is calibrated for the pinned word
                count plus two rendered history lines. With only one line, the
                unused second-line slot is exactly where lower-position praise
                belongs. Anchor its bottom just inside the par's normal 10px top
                margin: the toast therefore fits between line one and the par,
                while Hide par does not move the toast at all. GB may move for
                the visible par, but the toast's rule and lower position do not.
            */
            const ParMarginTop = GetNormalFeedbackParMarginTop(WordContainer);
            const SlotBottom =
                HistoryRect.bottom +
                ParMarginTop -
                ValidFeedbackNormalSlotInset;

            Left =
                ((SquareRect.left + SquareRect.right) / 2) -
                GameRect.left -
                (ProxyRect.width / 2);
            Top =
                SlotBottom -
                GameRect.top -
                ProxyRect.height;
        }

        Proxy.style.setProperty(
            "left",
            `${Math.round(Left)}px`,
            "important"
        );
        Proxy.style.setProperty(
            "top",
            `${Math.round(Top)}px`,
            "important"
        );
    }
'''

source = replace_once(
    source,
    old_position,
    new_position,
    "toast positioning",
)

source = replace_once(
    source,
    r'''        const ListContainer = WordContainer?.querySelector(
            ":scope > .lb-list-container"
        );
        const Source = GetNativeValidWordFeedbackSource();

        if (
            !GameContainer ||
            !TextFieldWrapper ||
            !ListContainer ||
            !Source
        ) {''',
    r'''        const ListContainer = WordContainer?.querySelector(
            ":scope > .lb-list-container"
        );
        const SquareContainer = GameContainer?.querySelector(
            ":scope > .lb-square-container"
        );
        const Source = GetNativeValidWordFeedbackSource();

        if (
            !GameContainer ||
            !WordContainer ||
            !TextFieldWrapper ||
            !ListContainer ||
            !SquareContainer ||
            !Source
        ) {''',
    "square-container lookup",
)

source = replace_once(
    source,
    r'''        PositionValidWordFeedbackProxy(
            Proxy,
            Source,
            GameContainer,
            TextFieldWrapper,
            ListContainer
        );''',
    r'''        PositionValidWordFeedbackProxy(
            Proxy,
            GameContainer,
            WordContainer,
            TextFieldWrapper,
            ListContainer,
            SquareContainer
        );''',
    "toast positioning call",
)

source_path.write_text(source, encoding="utf-8")

changelog_path = Path("CHANGELOG.md")
changelog = changelog_path.read_text(encoding="utf-8")
changelog = replace_once(
    changelog,
    "# Changelog\n\n## 1.12.0-beta.19",
    """# Changelog\n\n## 1.12.0-beta.20\n- Decoupled success-toast relocation from NYT's native toast rectangle: praise now remains in the lower slot for exactly one rendered history line and relocates above TI as soon as history wraps to line two.\n- Anchored normal lower praise in the calibrated spare second-history-line slot, ending just inside the par's normal top margin. A visible par still pushes GB down, but showing/hiding the par no longer changes the toast's lower position or relocation threshold.\n- Kept the 90px baseline history geometry and 22px structural TI/GB gutter unchanged; no additional toast-only whitespace is added.\n\n## 1.12.0-beta.19""",
    "changelog beta.20",
)
changelog_path.write_text(changelog, encoding="utf-8")

docs_path = Path("docs/PREVIEW_TESTING.md")
docs = docs_path.read_text(encoding="utf-8")
docs = replace_once(
    docs,
    "The `feature/qol-4-10-12-13-14` preview bundles issues #4, #5, #10, #12, #13, #14, #16, #17, #18, and #19. The current source is `1.12.0-beta.19`.",
    "The `feature/qol-4-10-12-13-14` preview bundles issues #4, #5, #10, #12, #13, #14, #16, #17, #18, and #19. The current source is `1.12.0-beta.20`.",
    "preview docs source version",
)

old_docs = "- **Hide par** should hide only the actual `Try to solve in X words` prompt in both NYT DOM states. When the accepted-word variant exposes the par as a direct child of the word container, its visible outer height is included in the fixed TI grid track so GB moves down far enough to clear both the par and a normal-position success toast; hiding the par collapses that reserved height again. Invalid-submission feedback injected as `.lb-text-field-wrapper > .lb-message-box` (for example **Too short** and **Not in word list**) must remain visible. Valid-word praise is now always rendered through Cubed's game-container-level proxy while the custom TI/GB layout is active. NYT's native praise box is suppressed immediately by DOM location even before NYT adds its later `success-message` class. Cubed records one native-toast lifecycle as one submission generation, waits until NYT's accepted-word history count actually advances (up to a 400ms safety ceiling), then either mirrors the hidden native box's final rendered position or moves the proxy above TI if history would collide. The proxy is not recreated merely because the live chain count changes during that same submission."
new_docs = "- **Hide par** should hide only the actual `Try to solve in X words` prompt in both NYT DOM states. When the accepted-word variant exposes the par as a direct child of the word container, its visible outer height remains part of the fixed TI grid track, so GB moves down for the par and hiding it collapses only that par space. Invalid-submission feedback injected as `.lb-text-field-wrapper > .lb-message-box` (for example **Too short** and **Not in word list**) must remain visible. Valid-word praise is always rendered through Cubed's game-container-level proxy while the custom TI/GB layout is active. NYT's native praise box is suppressed immediately by DOM location even before NYT adds its later `success-message` class. Cubed records one native-toast lifecycle as one submission generation and waits until NYT's accepted-word history count advances (up to a 400ms safety ceiling). With exactly one rendered history line, lower praise occupies the calibrated spare second-line slot immediately above the par; at two or more rendered history lines it relocates above TI. That decision and the lower toast position are independent of whether par is shown or hidden, and the proxy is not recreated merely because the live chain count changes during the same submission."
docs = replace_once(docs, old_docs, new_docs, "preview docs toast/par behavior")

docs_path.write_text(docs, encoding="utf-8")
