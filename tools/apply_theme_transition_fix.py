from pathlib import Path

SOURCE = Path("LetterBoxedCubed.user.js")
TESTS = Path("tests/final-polish-tests.js")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


source = SOURCE.read_text(encoding="utf-8")
source = replace_once(
    source,
    "// @version      1.13.1-beta.9",
    "// @version      1.13.1-beta.10",
    "version",
)

source = replace_once(
    source,
    """    let DarkBoardCanvasHookInstalled = false;\n    let NativeBoardFillText = null;\n    let NativeBoardStrokeText = null;\n""",
    """    let DarkBoardCanvasHookInstalled = false;\n    let NativeBoardFillText = null;\n    let NativeBoardStrokeText = null;\n    let ThemeAppliedOnce = false;\n""",
    "theme transition state",
)

source = replace_once(
    source,
    """        const Theme = GetActiveThemeDefinition();\n        const Palette = NormalizeThemePalette(Theme.Palette);\n        const Root = document.documentElement;\n\n        if (!Root) {\n            return;\n        }\n\n        const Variables = {\n""",
    """        const Theme = GetActiveThemeDefinition();\n        const Palette = NormalizeThemePalette(Theme.Palette);\n        const Root = document.documentElement;\n\n        if (!Root) {\n            return;\n        }\n\n        const NextBoardInverted = Boolean(Theme.InvertBoard);\n\n        /*\n            NYT's Letter Boxed board is a canvas whose source colors are baked\n            into its bitmap. Switching between non-inverted and inverted board\n            modes in place proved inherently fragile: NYT can asynchronously\n            repaint after Cubed's repair, and Cubed's own pixel normalization\n            intentionally mutates the dark-mode bitmap. Treat crossing that\n            boundary as a clean page-lifecycle change instead. The selected\n            theme is already persisted before ApplyTheme() is called, so the\n            reload comes back directly into the requested mode. Same-mode\n            palette edits remain live and do not reload.\n        */\n        if (\n            ThemeAppliedOnce &&\n            Root.classList.contains("lb-cubed-board-inverted") !==\n                NextBoardInverted\n        ) {\n            location.reload();\n            return;\n        }\n\n        const Variables = {\n""",
    "runtime inversion reload guard",
)

source = replace_once(
    source,
    """        Root.classList.toggle(\n            "lb-cubed-board-inverted",\n            Boolean(Theme.InvertBoard)\n        );\n        Root.dataset.lbcTheme = Theme.Id || DefaultThemeId;\n\n        /*\n""",
    """        Root.classList.toggle(\n            "lb-cubed-board-inverted",\n            NextBoardInverted\n        );\n        Root.dataset.lbcTheme = Theme.Id || DefaultThemeId;\n        ThemeAppliedOnce = true;\n\n        /*\n""",
    "mark theme applied",
)

source = replace_once(
    source,
    """            html.lb-cubed-native-theme .lb-word-list,\n            html.lb-cubed-native-theme .lb-word-list-length,\n            html.lb-cubed-native-theme .lb-par,\n            html.lb-cubed-native-theme input {\n                color: var(--lb-cubed-lb-text) !important;\n            }\n\n            /*\n                The web board is one canvas. NYT's renderer resolves its neutral\n""",
    """            html.lb-cubed-native-theme .lb-word-list,\n            html.lb-cubed-native-theme .lb-word-list-length,\n            html.lb-cubed-native-theme .lb-par,\n            html.lb-cubed-native-theme input {\n                color: var(--lb-cubed-lb-text) !important;\n            }\n\n            /*\n                NYT uses its --text token for several game-native details that\n                are not ordinary text nodes, including the Letter Boxed entry\n                underline/cursor. Give the whole game the theme text token,\n                then override the square container back to black source colors\n                below when the board itself is inverted.\n            */\n            html.lb-cubed-native-theme .lb-game-container {\n                --text: var(--lb-cubed-lb-text);\n            }\n\n            html.lb-cubed-native-theme .lb-text-field,\n            html.lb-cubed-native-theme .lb-text-field * {\n                color: var(--lb-cubed-lb-text) !important;\n                caret-color: var(--lb-cubed-lb-text) !important;\n            }\n\n            html.lb-cubed-native-theme .lb-text-field {\n                border-color: var(--lb-cubed-lb-text) !important;\n                border-bottom-color: var(--lb-cubed-lb-text) !important;\n            }\n\n            html.lb-cubed-native-theme .lb-text-field::before,\n            html.lb-cubed-native-theme .lb-text-field::after,\n            html.lb-cubed-native-theme .lb-text-field-wrapper::before,\n            html.lb-cubed-native-theme .lb-text-field-wrapper::after {\n                border-color: var(--lb-cubed-lb-text) !important;\n            }\n\n            /*\n                The web board is one canvas. NYT's renderer resolves its neutral\n""",
    "dark text entry styling",
)

SOURCE.write_text(source, encoding="utf-8")

tests = TESTS.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    "assert(source.includes('// @version      1.13.1-beta.9'), 'beta.9 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.10'), 'beta.10 version missing');",
    "test version",
)

anchor = "assert(source.includes('ScheduleDarkBoardCanvasRepairs'), 'runtime theme-switch dark board repair scheduler missing');\n"
extra = (
    "assert(source.includes('ThemeAppliedOnce'), 'theme transition reload guard state missing');\n"
    "assert(source.includes('location.reload();'), 'light/dark board-mode transition reload missing');\n"
    "assert(source.includes('caret-color: var(--lb-cubed-lb-text)'), 'dark text-entry caret styling missing');\n"
    "assert(source.includes('html.lb-cubed-native-theme .lb-game-container'), 'game-native --text theme token missing');\n"
)
if "theme transition reload guard state missing" not in tests:
    tests = replace_once(tests, anchor, anchor + extra, "theme transition regression tests")

TESTS.write_text(tests, encoding="utf-8")
