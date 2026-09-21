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
    "// @version      1.12.0-beta.18",
    "// @version      1.12.0-beta.19",
    "version bump",
)

source = replace_once(
    source,
    """    let ScanTimer = null;\n    let LayoutTimer = null;""",
    """    let ScanTimer = null;\n    let LayoutTimer = null;\n    let LastParTrackHeight = null;""",
    "par track state",
)

source = replace_once(
    source,
    """        GameContainer.classList.toggle(\n            \"lb-cubed-hide-par\",\n            HidePar\n        );\n    }""",
    """        GameContainer.classList.toggle(\n            \"lb-cubed-hide-par\",\n            HidePar\n        );\n\n        // Showing/hiding the real par changes the vertical space reserved\n        // between TI/history and GB. Recalculate that fixed grid track now.\n        QueuePanelLayoutUpdate();\n    }""",
    "hide par layout refresh",
)

source = replace_once(
    source,
    """                /*\n                    Gameplay mutations update player data, but they must not\n                    reflow the TI/GB meta-column. GB's vertical position is\n                    intentionally stable until an actual viewport resize.\n                */\n                NormalizeWordAreaFeedbackLayout();""",
    """                /*\n                    Gameplay mutations update player data without generally\n                    reflowing the TI/GB meta-column. The one intentional\n                    exception is the actual par prompt: NormalizeWordAreaFeedbackLayout\n                    queues a layout update only when its visible direct-child\n                    footprint changes, so GB makes room for the par when needed.\n                */\n                NormalizeWordAreaFeedbackLayout();""",
    "game observer comment",
)

source = replace_once(
    source,
    """        QueueValidWordFeedbackPlacement();\n    }\n\n    function GetVisibleHistoryContentBottom(ListContainer) {""",
    """        const ParTrackHeight = GetVisibleParTrackHeight(WordContainer);\n        if (\n            LastParTrackHeight !== null &&\n            ParTrackHeight !== LastParTrackHeight\n        ) {\n            QueuePanelLayoutUpdate();\n        }\n        LastParTrackHeight = ParTrackHeight;\n\n        QueueValidWordFeedbackPlacement();\n    }\n\n    function GetVisibleHistoryContentBottom(ListContainer) {""",
    "par mutation reflow",
)

source = replace_once(
    source,
    """    function UpdateHistoryLaneGeometry(GameContainer, WordContainer) {\n        const TextFieldWrapper = WordContainer?.querySelector(\n            \":scope > .lb-text-field-wrapper\"\n        );""",
    """    function GetVisibleParTrackHeight(WordContainer) {\n        const Par = WordContainer?.querySelector(\n            \":scope > .lb-par\"\n        );\n\n        if (!Par) {\n            return 0;\n        }\n\n        const Style = getComputedStyle(Par);\n        if (\n            Style.display === \"none\" ||\n            Style.visibility === \"hidden\"\n        ) {\n            return 0;\n        }\n\n        const Height = Math.max(\n            0,\n            Par.getBoundingClientRect().height\n        );\n        const MarginTop = Math.max(\n            0,\n            Number.parseFloat(Style.marginTop) || 0\n        );\n        const MarginBottom = Math.max(\n            0,\n            Number.parseFloat(Style.marginBottom) || 0\n        );\n\n        return Math.ceil(\n            Height + MarginTop + MarginBottom\n        );\n    }\n\n    function UpdateHistoryLaneGeometry(GameContainer, WordContainer) {\n        const TextFieldWrapper = WordContainer?.querySelector(\n            \":scope > .lb-text-field-wrapper\"\n        );""",
    "visible par height helper",
)

source = replace_once(
    source,
    """        const WordAreaHeight = InputHeight + HistoryLaneHeight;\n\n        /*\n            NYT vertically offsets the TI with a native top margin. Because TI""",
    """        const WordAreaHeight = InputHeight + HistoryLaneHeight;\n        const ParTrackHeight = GetVisibleParTrackHeight(WordContainer);\n        LastParTrackHeight = ParTrackHeight;\n\n        /*\n            NYT vertically offsets the TI with a native top margin. Because TI""",
    "measure par track height",
)

source = replace_once(
    source,
    """        const WordGridTrackHeight = Math.ceil(\n            WordMarginTop + WordAreaHeight + WordMarginBottom\n        );""",
    """        /*\n            The accepted-word DOM variant places the real par as a direct flex\n            child after the history lane. Because Cubed uses an explicit grid\n            track, that child otherwise overflows the track and collides with\n            GB (and its normal-position success toast). Reserve only the actual\n            visible par's outer height; hiding the par collapses this space.\n        */\n        const WordGridTrackHeight = Math.ceil(\n            WordMarginTop +\n            WordAreaHeight +\n            ParTrackHeight +\n            WordMarginBottom\n        );""",
    "include par in grid track",
)

source_path.write_text(source, encoding="utf-8")

changelog_path = Path("CHANGELOG.md")
changelog = changelog_path.read_text(encoding="utf-8")
changelog = replace_once(
    changelog,
    "# Changelog\n\n## 1.12.0-beta.18",
    """# Changelog\n\n## 1.12.0-beta.19\n- Reserved the visible direct-child par prompt's full outer height in the fixed TI grid track, so an unhidden par pushes GB (and its normal-position success toast) downward instead of overlapping it.\n- Par visibility/DOM-shape changes now trigger a targeted layout recalculation; hiding the par immediately collapses the extra space again without reintroducing general gameplay-driven GB movement.\n\n## 1.12.0-beta.18""",
    "changelog beta.19",
)
changelog_path.write_text(changelog, encoding="utf-8")

docs_path = Path("docs/PREVIEW_TESTING.md")
docs = docs_path.read_text(encoding="utf-8")
docs = replace_once(
    docs,
    "The `feature/qol-4-10-12-13-14` preview bundles issues #4, #5, #10, #12, #13, #14, #16, #17, #18, and #19. The current source is `1.12.0-beta.18`.",
    "The `feature/qol-4-10-12-13-14` preview bundles issues #4, #5, #10, #12, #13, #14, #16, #17, #18, and #19. The current source is `1.12.0-beta.19`.",
    "preview docs source version",
)
docs = replace_once(
    docs,
    "- **Hide par** should hide only the actual `Try to solve in X words` prompt in both NYT DOM states. Invalid-submission feedback injected as `.lb-text-field-wrapper > .lb-message-box` (for example **Too short** and **Not in word list**) must remain visible.",
    "- **Hide par** should hide only the actual `Try to solve in X words` prompt in both NYT DOM states. When the accepted-word variant exposes the par as a direct child of the word container, its visible outer height is included in the fixed TI grid track so GB moves down far enough to clear both the par and a normal-position success toast; hiding the par collapses that reserved height again. Invalid-submission feedback injected as `.lb-text-field-wrapper > .lb-message-box` (for example **Too short** and **Not in word list**) must remain visible.",
    "preview docs par spacing",
)
docs_path.write_text(docs, encoding="utf-8")
