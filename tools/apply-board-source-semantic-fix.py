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
    "// @version      1.13.1-beta.16",
    "// @version      1.13.1-beta.17",
    "version"
)

source = replace_once(
    source,
    """    let NativeRequestAnimationFrame = null;\n    let LineAnimationAcceleration = null;\n""",
    """    let NativeRequestAnimationFrame = null;\n    let LineAnimationAcceleration = null;\n    let BoardTextSourceHookInstalled = false;\n    let NativeBoardFillText = null;\n    let NativeBoardStrokeText = null;\n""",
    "board text hook state"
)

source = replace_once(
    source,
    """        LoadThemeState();\n        AddStyles();\n        ApplyTheme();\n""",
    """        LoadThemeState();\n        AddStyles();\n        InstallBoardTextSourceHook();\n        ApplyTheme();\n""",
    "install semantic board text hook"
)

source = replace_once(
    source,
    """        const Ready = await WaitForGame();\n        if (!Ready) {\n            console.warn(\"[Letter Boxed Cubed] Could not find Letter Boxed game data.\");\n            return;\n        }\n\n        LoadPuzzleData();\n""",
    """        const Ready = await WaitForGame();\n        if (!Ready) {\n            console.warn(\"[Letter Boxed Cubed] Could not find Letter Boxed game data.\");\n            return;\n        }\n\n        /*\n            The first theme application can precede NYT's board canvas. Apply\n            it once more after readiness so an already-painted board gets one\n            harmless renderer refresh through the semantic text hook.\n        */\n        ApplyTheme();\n\n        LoadPuzzleData();\n""",
    "post-readiness theme refresh"
)

anchor = """    function ApplyBoardThemeMatrix(Palette) {\n        const Matrix = EnsureBoardThemeFilter();\n        if (!Matrix) {\n            return;\n        }\n\n        const Rows = BuildBoardThemeAffineMatrix(\n            Palette.LbBoard,\n            Palette.LbForeground,\n            Palette.LbActive\n        );\n        Matrix.setAttribute(\n            \"values\",\n            Rows.flat().map(Value => {\n                const Rounded = Math.abs(Value) < 0.0000001 ? 0 : Value;\n                return Number(Rounded.toFixed(7)).toString();\n            }).join(\" \")\n        );\n    }\n\n"""
addition = anchor + """    function IsLetterBoxedBoardCanvas(Canvas) {\n        return Boolean(\n            Canvas &&\n            typeof Canvas.closest === \"function\" &&\n            Canvas.closest(\".lb-game-container .lb-square-container\")\n        );\n    }\n\n    function IsNativeBoardWhite(Value) {\n        const Text = String(Value || \"\")\n            .trim()\n            .toLowerCase()\n            .replace(/\\s+/g, \"\");\n\n        return (\n            Text === \"#fff\" ||\n            Text === \"#ffffff\" ||\n            Text === \"white\" ||\n            Text === \"rgb(255,255,255)\" ||\n            Text === \"rgba(255,255,255,1)\"\n        );\n    }\n\n    function InstallBoardTextSourceHook() {\n        if (BoardTextSourceHookInstalled) {\n            return;\n        }\n\n        const Prototype = PageWindow.CanvasRenderingContext2D?.prototype;\n        if (!Prototype) {\n            return;\n        }\n\n        NativeBoardFillText = Prototype.fillText;\n        NativeBoardStrokeText = Prototype.strokeText;\n\n        const IsThemedBoardLetterDraw = (Context, Text) =>\n            document.documentElement?.classList.contains(\n                \"lb-cubed-board-themed\"\n            ) &&\n            IsLetterBoxedBoardCanvas(Context?.canvas) &&\n            /^[A-Z]$/.test(String(Text || \"\").trim());\n\n        /*\n            Board diagnostics proved that NYT uses the SAME native white for\n            two different semantic jobs: the board fill and inactive letter\n            glyphs. An RGB matrix cannot map one source color to both Board and\n            Foreground. Keep the affine transform for the bitmap as a whole,\n            but normalize only white single-letter text draws to native black.\n            The matrix then maps those glyphs to Foreground while leaving the\n            white board fill available to map to Board. This is intentionally\n            tiny and draw-semantic: no getImageData(), pixel walks, inversion,\n            repaint polling, or mutation of path/node rendering.\n        */\n        if (typeof NativeBoardFillText === \"function\") {\n            Prototype.fillText = function (Text, ...Arguments) {\n                if (\n                    IsThemedBoardLetterDraw(this, Text) &&\n                    IsNativeBoardWhite(this.fillStyle)\n                ) {\n                    const Previous = this.fillStyle;\n                    this.fillStyle = \"#000000\";\n                    try {\n                        return NativeBoardFillText.call(\n                            this,\n                            Text,\n                            ...Arguments\n                        );\n                    } finally {\n                        this.fillStyle = Previous;\n                    }\n                }\n\n                return NativeBoardFillText.call(\n                    this,\n                    Text,\n                    ...Arguments\n                );\n            };\n        }\n\n        if (typeof NativeBoardStrokeText === \"function\") {\n            Prototype.strokeText = function (Text, ...Arguments) {\n                if (\n                    IsThemedBoardLetterDraw(this, Text) &&\n                    IsNativeBoardWhite(this.strokeStyle)\n                ) {\n                    const Previous = this.strokeStyle;\n                    this.strokeStyle = \"#000000\";\n                    try {\n                        return NativeBoardStrokeText.call(\n                            this,\n                            Text,\n                            ...Arguments\n                        );\n                    } finally {\n                        this.strokeStyle = Previous;\n                    }\n                }\n\n                return NativeBoardStrokeText.call(\n                    this,\n                    Text,\n                    ...Arguments\n                );\n            };\n        }\n\n        BoardTextSourceHookInstalled = true;\n    }\n\n    function QueueBoardThemeRendererRefresh() {\n        if (\n            !document.documentElement?.classList.contains(\n                \"lb-cubed-board-themed\"\n            ) ||\n            !document.querySelector(\n                \".lb-game-container .lb-square-container canvas\"\n            )\n        ) {\n            return;\n        }\n\n        /*\n            NYT redraws the board on resize. One short two-frame nudge is enough\n            to route an already-painted canvas through the semantic text hook;\n            unlike the old bitmap repair this does no synchronous pixel work.\n        */\n        requestAnimationFrame(() => {\n            window.dispatchEvent(new Event(\"resize\"));\n            setTimeout(\n                () => window.dispatchEvent(new Event(\"resize\")),\n                80\n            );\n        });\n    }\n\n"""
source = replace_once(
    source,
    anchor,
    addition,
    "semantic board text functions"
)

source = replace_once(
    source,
    """        if (ApplyNative) {\n            ApplyBoardThemeMatrix(Palette);\n        }\n    }\n""",
    """        if (ApplyNative) {\n            ApplyBoardThemeMatrix(Palette);\n            QueueBoardThemeRendererRefresh();\n        }\n    }\n""",
    "queue board redraw after theme"
)

source = replace_once(
    source,
    """            html.lb-cubed-native-theme .lb-text-field::before,\n            html.lb-cubed-native-theme .lb-text-field::after,\n            html.lb-cubed-native-theme .lb-text-field-wrapper::before,\n            html.lb-cubed-native-theme .lb-text-field-wrapper::after {\n                border-color: var(--lb-cubed-lb-fg) !important;\n            }\n""",
    """            html.lb-cubed-native-theme .lb-text-field::before,\n            html.lb-cubed-native-theme .lb-text-field::after,\n            html.lb-cubed-native-theme .lb-text-field-wrapper::before,\n            html.lb-cubed-native-theme .lb-text-field-wrapper::after {\n                border-color: var(--lb-cubed-lb-fg) !important;\n            }\n\n            /* NYT's visible caret is a span, not the browser-native caret. */\n            html.lb-cubed-native-theme .lb-text-field__caret {\n                color: var(--lb-cubed-lb-fg) !important;\n                background: var(--lb-cubed-lb-fg) !important;\n                background-color: var(--lb-cubed-lb-fg) !important;\n                border-color: var(--lb-cubed-lb-fg) !important;\n            }\n""",
    "visible cursor theme"
)

source = replace_once(
    source,
    """            #${PanelId} .lb-cubed-stat,\n            #${PanelId} .lb-cubed-tree > summary,\n            #${PanelId} .lb-cubed-nested-tree > summary,\n            #${HistoryOverlayId} .lb-cubed-history-section-title,\n            #${HistoryOverlayId} .lb-cubed-history-navigation {\n""",
    """            #${PanelId} .lb-cubed-stat,\n            #${HistoryOverlayId} .lb-cubed-stat,\n            #${PanelId} .lb-cubed-tree > summary,\n            #${PanelId} .lb-cubed-nested-tree > summary,\n            #${HistoryOverlayId} .lb-cubed-history-section-title,\n            #${HistoryOverlayId} .lb-cubed-history-navigation {\n""",
    "history stat heading background"
)

source = replace_once(
    source,
    """            #${PanelId} .lb-cubed-stat-value,\n            #${PanelId} .lb-cubed-twofer-solution-text,\n""",
    """            #${PanelId} .lb-cubed-stat-value,\n            #${HistoryOverlayId} .lb-cubed-stat-value,\n            #${PanelId} .lb-cubed-twofer-solution-text,\n""",
    "history stat value text"
)

source = replace_once(
    source,
    """            #${PanelId} .lb-cubed-stat-label,\n            #${PanelId} .lb-cubed-potential-word,\n""",
    """            #${PanelId} .lb-cubed-stat-label,\n            #${HistoryOverlayId} .lb-cubed-stat-label,\n            #${PanelId} .lb-cubed-potential-word,\n""",
    "history stat label text"
)

SOURCE.write_text(source, encoding="utf-8")

tests = TESTS.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    "assert(source.includes('// @version      1.13.1-beta.16'), 'beta.16 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.17'), 'beta.17 version missing');",
    "test version"
)

anchor_test = "assert(source.includes('--text: #000000 !important;'), 'inactive GB letter source normalization missing');\n"
add_tests = """assert(source.includes('InstallBoardTextSourceHook'), 'semantic board text source hook missing');\nassert(source.includes('IsThemedBoardLetterDraw'), 'board text hook is not restricted to letter draws');\nassert(source.includes('IsNativeBoardWhite(this.fillStyle)'), 'white inactive board letters are not normalized before affine mapping');\nassert(source.includes('QueueBoardThemeRendererRefresh'), 'already-painted board renderer refresh missing');\nassert(source.includes('.lb-text-field__caret'), 'visible NYT caret theme selector missing');\nassert(source.includes('#${HistoryOverlayId} .lb-cubed-stat-value'), 'Browse History stat value theming missing');\nassert(source.includes('#${HistoryOverlayId} .lb-cubed-stat-label'), 'Browse History stat label theming missing');\n"""
if "semantic board text source hook missing" not in tests:
    tests = replace_once(
        tests,
        anchor_test,
        anchor_test + add_tests,
        "beta17 regression tests"
    )

TESTS.write_text(tests, encoding="utf-8")
