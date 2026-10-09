from pathlib import Path
import re

SOURCE = Path("LetterBoxedCubed.user.js")
FINAL_TESTS = Path("tests/final-polish-tests.js")
CLOUD_TESTS = Path("tests/cloud-sync-tests.js")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


def replace_regex_once(text, pattern, repl, label, flags=0):
    new_text, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 regex match, found {count}")
    return new_text


def function_bounds(text, name):
    marker = f"    function {name}("
    start = text.find(marker)
    if start < 0:
        raise RuntimeError(f"function not found: {name}")
    brace = text.find("{", start)
    depth = 0
    quote = None
    escape = False
    i = brace
    while i < len(text):
        ch = text[i]
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
        else:
            if ch in ('"', "'", '`'):
                quote = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return start, i + 1
        i += 1
    raise RuntimeError(f"unterminated function: {name}")


def edit_function(text, name, editor):
    start, end = function_bounds(text, name)
    old = text[start:end]
    new = editor(old)
    if old == new:
        raise RuntimeError(f"function editor made no change: {name}")
    return text[:start] + new + text[end:]


source = SOURCE.read_text(encoding="utf-8")
source = replace_once(
    source,
    "// @version      1.13.1-beta.17",
    "// @version      1.13.1-beta.18",
    "version"
)

# Prebuilt semantic relationships: both presets keep LBC background/text tied
# to their corresponding Letter Boxed values. NYT Light deliberately keeps the
# board itself separate (white board on pink page).
source = replace_once(
    source,
    '''            ApplyNative: false,\n            BoardMatchesBackground: false,\n            Palette: {''',
    '''            ApplyNative: false,\n            BoardMatchesBackground: false,\n            LbcBackgroundMatchesLbBackground: true,\n            LbcTextMatchesLbForeground: true,\n            Palette: {''',
    "NYT Light semantic ties"
)
source = replace_once(
    source,
    '''            ApplyNative: true,\n            BoardMatchesBackground: true,\n            Palette: {''',
    '''            ApplyNative: true,\n            BoardMatchesBackground: true,\n            LbcBackgroundMatchesLbBackground: true,\n            LbcTextMatchesLbForeground: true,\n            Palette: {''',
    "NYT Dark semantic ties"
)
source = replace_once(
    source,
    '''                LbcBackground: "#D88482",\n                LbcHeadingBackground: "#E5A09E",\n                LbcText: "#301818",''',
    '''                LbcBackground: "#FAA6A4",\n                LbcHeadingBackground: "#E5A09E",\n                LbcText: "#000000",''',
    "NYT Light linked LBC colors"
)

# Existing custom themes gain explicit semantic-link flags. Absent flags are
# inferred from the stored colors so intentionally independent beta themes are
# not silently changed during migration.
def edit_normalize_custom(fn):
    fn = replace_once(
        fn,
        '''        if (BoardMatchesBackground) {\n            Palette.LbBoard = Palette.LbBackground;\n        }\n\n        return {''',
        '''        const LbcBackgroundMatchesLbBackground =\n            Object.prototype.hasOwnProperty.call(\n                RawTheme,\n                "LbcBackgroundMatchesLbBackground"\n            )\n                ? Boolean(RawTheme.LbcBackgroundMatchesLbBackground)\n                : Palette.LbcBackground === Palette.LbBackground;\n        const LbcTextMatchesLbForeground =\n            Object.prototype.hasOwnProperty.call(\n                RawTheme,\n                "LbcTextMatchesLbForeground"\n            )\n                ? Boolean(RawTheme.LbcTextMatchesLbForeground)\n                : Palette.LbcText === Palette.LbForeground;\n\n        if (BoardMatchesBackground) {\n            Palette.LbBoard = Palette.LbBackground;\n        }\n        if (LbcBackgroundMatchesLbBackground) {\n            Palette.LbcBackground = Palette.LbBackground;\n        }\n        if (LbcTextMatchesLbForeground) {\n            Palette.LbcText = Palette.LbForeground;\n        }\n\n        return {''',
        "custom theme link migration"
    )
    fn = replace_once(
        fn,
        '''            Palette,\n            BoardMatchesBackground,\n            Deleted:''',
        '''            Palette,\n            BoardMatchesBackground,\n            LbcBackgroundMatchesLbBackground,\n            LbcTextMatchesLbForeground,\n            Deleted:''',
        "normalized custom theme link fields"
    )
    return fn

source = edit_function(source, "NormalizeCustomThemeRecord", edit_normalize_custom)

# Apply linked semantic values before deriving secondary shades.
def edit_apply_theme(fn):
    fn = replace_once(
        fn,
        '''        if (Theme.BoardMatchesBackground) {\n            Palette.LbBoard = Palette.LbBackground;\n        }\n\n        const MutedText = GetDerivedLbcMutedText(Palette);''',
        '''        if (Theme.BoardMatchesBackground) {\n            Palette.LbBoard = Palette.LbBackground;\n        }\n        if (Theme.LbcBackgroundMatchesLbBackground) {\n            Palette.LbcBackground = Palette.LbBackground;\n        }\n        if (Theme.LbcTextMatchesLbForeground) {\n            Palette.LbcText = Palette.LbForeground;\n        }\n\n        const MutedText = GetDerivedLbcMutedText(Palette);''',
        "ApplyTheme semantic ties"
    )
    fn = replace_once(
        fn,
        '''        const NytSolutionText = GetDerivedNytSolutionText(Palette);\n        const ApplyNative = Boolean(Theme.ApplyNative);''',
        '''        const NytSolutionText = GetDerivedNytSolutionText(Palette);\n        const ControlColorScheme =\n            GetThemeRelativeLuminance(Palette.LbcBackground) < 0.38\n                ? "dark"\n                : "light";\n        const ApplyNative = Boolean(Theme.ApplyNative);''',
        "control color scheme derivation"
    )
    fn = replace_once(
        fn,
        '''            "--lb-cubed-lbc-accent": LbcAccent,\n            "--lb-cubed-nyt-solution": Palette.NytSolution,''',
        '''            "--lb-cubed-lbc-accent": LbcAccent,\n            "--lb-cubed-control-color-scheme": ControlColorScheme,\n            "--lb-cubed-nyt-solution": Palette.NytSolution,''',
        "control color scheme variable"
    )
    return fn

source = edit_function(source, "ApplyTheme", edit_apply_theme)

# NYT-solution foreground remains a tint/shade of its chosen background rather
# than collapsing to plain black/white.
def edit_solution_text(fn):
    return replace_regex_once(
        fn,
        r'''    function GetDerivedNytSolutionText\(Palette\) \{.*?\n    \}''',
        '''    function GetDerivedNytSolutionText(Palette) {\n        const Pole = GetThemeRelativeLuminance(Palette.NytSolution) < 0.38\n            ? "#FFFFFF"\n            : "#000000";\n        return MixThemeColors(\n            Palette.NytSolution,\n            Pole,\n            0.65\n        );\n    }''',
        "NYT solution tint/shade",
        flags=re.S
    )

source = edit_function(source, "GetDerivedNytSolutionText", lambda fn: fn.replace(
    '''        return MixThemeColors(\n            Palette.NytSolution,\n            GetThemeContrastPole(Palette.NytSolution),\n            0.82\n        );''',
    '''        const Pole = GetThemeRelativeLuminance(Palette.NytSolution) < 0.38\n            ? "#FFFFFF"\n            : "#000000";\n        return MixThemeColors(\n            Palette.NytSolution,\n            Pole,\n            0.65\n        );'''
))

# New custom themes inherit all semantic relationships from their source.
def edit_create_custom(fn):
    fn = replace_once(
        fn,
        '''        const BoardMatchesBackground = Boolean(Base.BoardMatchesBackground);\n        const Palette = NormalizeThemePalette(''',
        '''        const BoardMatchesBackground = Boolean(Base.BoardMatchesBackground);\n        const LbcBackgroundMatchesLbBackground = Boolean(\n            Base.LbcBackgroundMatchesLbBackground\n        );\n        const LbcTextMatchesLbForeground = Boolean(\n            Base.LbcTextMatchesLbForeground\n        );\n        const Palette = NormalizeThemePalette(''',
        "custom theme inherited links"
    )
    fn = replace_once(
        fn,
        '''        if (BoardMatchesBackground) {\n            Palette.LbBoard = Palette.LbBackground;\n        }\n\n        ThemeState.CustomThemes[Id] = {''',
        '''        if (BoardMatchesBackground) {\n            Palette.LbBoard = Palette.LbBackground;\n        }\n        if (LbcBackgroundMatchesLbBackground) {\n            Palette.LbcBackground = Palette.LbBackground;\n        }\n        if (LbcTextMatchesLbForeground) {\n            Palette.LbcText = Palette.LbForeground;\n        }\n\n        ThemeState.CustomThemes[Id] = {''',
        "custom theme apply inherited links"
    )
    fn = replace_once(
        fn,
        '''            Palette,\n            BoardMatchesBackground,\n            Deleted: false,''',
        '''            Palette,\n            BoardMatchesBackground,\n            LbcBackgroundMatchesLbBackground,\n            LbcTextMatchesLbForeground,\n            Deleted: false,''',
        "custom theme persisted links"
    )
    return fn

source = edit_function(source, "CreateCustomThemeFromActive", edit_create_custom)

# Editing a linked source color propagates to all dependent semantic colors.
def edit_update_palette(fn):
    return replace_once(
        fn,
        '''        if (Key === "LbBackground" && Theme.BoardMatchesBackground) {\n            Theme.Palette.LbBoard = Theme.Palette.LbBackground;\n        }\n\n        if (Persist) {''',
        '''        if (Key === "LbBackground" && Theme.BoardMatchesBackground) {\n            Theme.Palette.LbBoard = Theme.Palette.LbBackground;\n        }\n        if (\n            Key === "LbBackground" &&\n            Theme.LbcBackgroundMatchesLbBackground\n        ) {\n            Theme.Palette.LbcBackground = Theme.Palette.LbBackground;\n        }\n        if (\n            Key === "LbForeground" &&\n            Theme.LbcTextMatchesLbForeground\n        ) {\n            Theme.Palette.LbcText = Theme.Palette.LbForeground;\n        }\n\n        if (Persist) {''',
        "linked source color propagation"
    )

source = edit_function(source, "UpdateActiveCustomThemePalette", edit_update_palette)

# Add toggles for the two new LBC semantic links.
_, board_match_end = function_bounds(source, "UpdateActiveCustomThemeBoardMatch")
link_functions = '''\n\n    function UpdateActiveCustomThemeLbcBackgroundMatch(Value) {\n        const Theme = GetActiveCustomThemeRecord();\n        if (!Theme) {\n            return false;\n        }\n\n        Theme.LbcBackgroundMatchesLbBackground = Boolean(Value);\n        if (Theme.LbcBackgroundMatchesLbBackground) {\n            Theme.Palette.LbcBackground = Theme.Palette.LbBackground;\n        }\n        Theme.UpdatedAt = new Date().toISOString();\n        SaveThemeState();\n        ApplyTheme();\n        return true;\n    }\n\n    function UpdateActiveCustomThemeLbcTextMatch(Value) {\n        const Theme = GetActiveCustomThemeRecord();\n        if (!Theme) {\n            return false;\n        }\n\n        Theme.LbcTextMatchesLbForeground = Boolean(Value);\n        if (Theme.LbcTextMatchesLbForeground) {\n            Theme.Palette.LbcText = Theme.Palette.LbForeground;\n        }\n        Theme.UpdatedAt = new Date().toISOString();\n        SaveThemeState();\n        ApplyTheme();\n        return true;\n    }'''
source = source[:board_match_end] + link_functions + source[board_match_end:]

# Capitalization and generic linked-color row for the two LBC relationships.
source = replace_once(
    source,
    '        MatchText.textContent = "Same as background";',
    '        MatchText.textContent = "Same as Background";',
    "Board checkbox capitalization"
)

append_marker = "    function AppendThemeColorGroup(Section, Title, Rows) {"
linked_row_function = '''    function CreateThemeLinkedColorRow(\n        Section,\n        LabelText,\n        PaletteKey,\n        MatchProperty,\n        MatchTextValue,\n        FallbackValue,\n        UpdateMatch\n    ) {\n        const Theme = GetActiveCustomThemeRecord();\n        const Row = document.createElement("div");\n        Row.className = "lb-cubed-theme-color-row lb-cubed-theme-board-row";\n\n        const Label = document.createElement("span");\n        Label.className = "lb-cubed-settings-label";\n        Label.textContent = LabelText;\n\n        const MatchLabel = document.createElement("label");\n        MatchLabel.className = "lb-cubed-theme-board-match";\n        const MatchInput = document.createElement("input");\n        MatchInput.type = "checkbox";\n        MatchInput.checked = Boolean(Theme?.[MatchProperty]);\n        const MatchText = document.createElement("span");\n        MatchText.textContent = MatchTextValue;\n        MatchLabel.append(MatchInput, MatchText);\n\n        const ColorInput = document.createElement("input");\n        ColorInput.type = "color";\n        ColorInput.value = Theme?.Palette?.[PaletteKey] || FallbackValue;\n        ColorInput.disabled = Boolean(Theme?.[MatchProperty]);\n        ColorInput.addEventListener("input", Event => {\n            UpdateActiveCustomThemePalette(\n                PaletteKey,\n                Event.currentTarget.value,\n                false\n            );\n        });\n        ColorInput.addEventListener("change", Event => {\n            UpdateActiveCustomThemePalette(\n                PaletteKey,\n                Event.currentTarget.value,\n                true\n            );\n        });\n\n        MatchInput.addEventListener("change", () => {\n            UpdateMatch(MatchInput.checked);\n            RefreshThemeSettingsSection(Section);\n        });\n\n        Row.append(Label, MatchLabel, ColorInput);\n        return Row;\n    }\n\n'''
source = replace_once(source, append_marker, linked_row_function + append_marker, "linked theme row helper")

# Replace independent LBC Background/Text rows with linked rows.
source = replace_once(
    source,
    '''                CreateThemeColorRow("Background", "LbcBackground"),\n                CreateThemeColorRow("Heading background", "LbcHeadingBackground"),\n                CreateThemeColorRow("Text", "LbcText"),\n                CreateThemeColorRow("Border", "LbcBorder")''',
    '''                CreateThemeLinkedColorRow(\n                    Section,\n                    "Background",\n                    "LbcBackground",\n                    "LbcBackgroundMatchesLbBackground",\n                    "Same as Letter Boxed Background",\n                    "#D88482",\n                    UpdateActiveCustomThemeLbcBackgroundMatch\n                ),\n                CreateThemeColorRow("Heading background", "LbcHeadingBackground"),\n                CreateThemeLinkedColorRow(\n                    Section,\n                    "Text",\n                    "LbcText",\n                    "LbcTextMatchesLbForeground",\n                    "Same as Letter Boxed Foreground",\n                    "#301818",\n                    UpdateActiveCustomThemeLbcTextMatch\n                ),\n                CreateThemeColorRow("Border", "LbcBorder")''',
    "LBC linked theme controls"
)

# Give the solution star its own element so it can be 2px larger without moving
# the baseline of the label text.
def edit_twofer_row(fn):
    return replace_once(
        fn,
        '''        const NytLabel = document.createElement("div");\n        NytLabel.className = "lb-cubed-nyt-solution-label";\n        NytLabel.textContent = "★ NYT Solution";\n\n        NytWrapper.append(NytLabel, Row);''',
        '''        const NytLabel = document.createElement("div");\n        NytLabel.className = "lb-cubed-nyt-solution-label";\n\n        const NytStar = document.createElement("span");\n        NytStar.className = "lb-cubed-nyt-solution-star";\n        NytStar.textContent = "★";\n\n        const NytLabelText = document.createElement("span");\n        NytLabelText.textContent = "NYT Solution";\n        NytLabel.append(NytStar, NytLabelText);\n\n        NytWrapper.append(NytLabel, Row);''',
        "NYT solution star element"
    )

source = edit_function(source, "CreateTwoferRow", edit_twofer_row)

# Compact number-input sizing based on each control's maximum digit count.
number_helper_marker = "    function CreateSettingsNumberWithReset("
number_helper = '''    function ApplyCompactNumberInputWidth(Input, Maximum) {\n        const NumericMaximum = Math.abs(Math.trunc(Number(Maximum) || 0));\n        const DigitCount = Math.max(2, String(NumericMaximum).length);\n        Input.style.width = `calc(${DigitCount}ch + 22px)`;\n    }\n\n'''
source = replace_once(source, number_helper_marker, number_helper + number_helper_marker, "compact number helper")

def edit_number_reset(fn):
    return replace_once(
        fn,
        '''        Input.dataset.cubedSettingInput = SettingName;\n\n        const SuffixText''',
        '''        Input.dataset.cubedSettingInput = SettingName;\n        ApplyCompactNumberInputWidth(Input, Maximum);\n\n        const SuffixText''',
        "settings number compact width"
    )

source = edit_function(source, "CreateSettingsNumberWithReset", edit_number_reset)
source = replace_once(
    source,
    '''            SpanInput.title = "Width in twelfths of the LBC dashboard";''',
    '''            SpanInput.title = "Width in twelfths of the LBC dashboard";\n            ApplyCompactNumberInputWidth(SpanInput, 12);''',
    "span input compact width"
)

# Friendly HTML response handling. A transient Apps Script HTML page is a
# response-side failure, never imported backup data. Retrying the exact payload
# is safe because Write requests already carry an idempotency WriteId.
def edit_bridge_request(fn):
    fn = replace_once(
        fn,
        "    function GoogleDriveBridgeRequest(Action, Payload = {}) {",
        "    function GoogleDriveBridgeRequest(Action, Payload = {}, RetryAttempt = 0) {",
        "bridge retry signature"
    )
    fn = replace_once(
        fn,
        '''                        const Parsed = JSON.parse(Response.responseText);\n\n                        if (!Parsed || typeof Parsed !== "object") {''',
        '''                        const ResponseText = String(\n                            Response.responseText || ""\n                        ).trim();\n                        const LooksLikeHtml = /^<(?:!doctype|html|head|body)\\b/i\n                            .test(ResponseText);\n\n                        if (LooksLikeHtml) {\n                            if (RetryAttempt < 1) {\n                                console.warn(\n                                    "[Letter Boxed Cubed] Google Drive bridge returned HTML instead of JSON; retrying the same request once.",\n                                    { Action, Status: Response.status }\n                                );\n                                setTimeout(() => {\n                                    GoogleDriveBridgeRequest(\n                                        Action,\n                                        Payload,\n                                        RetryAttempt + 1\n                                    ).then(Resolve, Reject);\n                                }, 500);\n                                return;\n                            }\n\n                            throw new Error(\n                                "Google Drive bridge returned an HTML page instead of JSON after retry. " +\n                                "This is usually a temporary Apps Script or authorization response; no HTML was imported into LBC data."\n                            );\n                        }\n\n                        let Parsed;\n                        try {\n                            Parsed = JSON.parse(ResponseText);\n                        } catch (ParseError) {\n                            throw new Error(\n                                "Google Drive bridge returned invalid JSON: " +\n                                ParseError.message\n                            );\n                        }\n\n                        if (!Parsed || typeof Parsed !== "object") {''',
        "bridge HTML/JSON response validation"
    )
    return fn

source = edit_function(source, "GoogleDriveBridgeRequest", edit_bridge_request)

# Theme-aware controls and native UI finishing pass. This is intentionally an
# override block with semantic variables, so legacy visual CSS remains a safe
# fallback when no theme has been applied.
css_marker = '''            /*\n                ================================================================\n                COLOR THEMES (ISSUE #30) - SEMANTIC THEME MODEL V2\n                ================================================================\n            */'''
control_css = '''            /*\n                ================================================================\n                THEME-AWARE NATIVE CONTROLS\n                ================================================================\n            */\n\n            #${PanelId},\n            #${HistoryOverlayId} {\n                color-scheme: var(--lb-cubed-control-color-scheme, light);\n                scrollbar-color:\n                    var(--lb-cubed-lbc-border, #4C2222)\n                    color-mix(\n                        in srgb,\n                        var(--lb-cubed-lbc-heading-bg, #E5A09E) 55%,\n                        var(--lb-cubed-lbc-bg, #D88482)\n                    );\n            }\n\n            html.lb-cubed-native-theme {\n                color-scheme: var(--lb-cubed-control-color-scheme, light);\n                scrollbar-color:\n                    var(--lb-cubed-lb-fg)\n                    var(--lb-cubed-lb-bg);\n            }\n\n            #${PanelId} input[type="checkbox"],\n            #${PanelId} input[type="range"],\n            #${HistoryOverlayId} input[type="checkbox"],\n            #${HistoryOverlayId} input[type="range"] {\n                accent-color: var(--lb-cubed-lbc-border, #4C2222) !important;\n            }\n\n            #${PanelId} input[type="number"],\n            #${HistoryOverlayId} input[type="number"] {\n                box-sizing: border-box;\n                min-width: 0 !important;\n                padding: 2px 2px 2px 4px !important;\n                border: 1px solid var(--lb-cubed-lbc-border, #4C2222) !important;\n                border-radius: 3px !important;\n                background: var(--lb-cubed-lbc-heading-bg, #E5A09E) !important;\n                color: var(--lb-cubed-lbc-text, #301818) !important;\n                font: inherit;\n                font-family: Consolas, "Courier New", monospace;\n                text-align: right !important;\n                color-scheme: var(--lb-cubed-control-color-scheme, light);\n            }\n\n            #${PanelId} input[type="number"]::-webkit-inner-spin-button,\n            #${PanelId} input[type="number"]::-webkit-outer-spin-button,\n            #${HistoryOverlayId} input[type="number"]::-webkit-inner-spin-button,\n            #${HistoryOverlayId} input[type="number"]::-webkit-outer-spin-button {\n                opacity: 1 !important;\n                margin: 0 0 0 0.6ch !important;\n                width: 12px !important;\n                height: 16px !important;\n            }\n\n            #${PanelContentId}::-webkit-scrollbar,\n            #${PanelId} *::-webkit-scrollbar,\n            #${HistoryOverlayId} *::-webkit-scrollbar {\n                width: 8px;\n                height: 8px;\n            }\n\n            #${PanelContentId}::-webkit-scrollbar-track,\n            #${PanelId} *::-webkit-scrollbar-track,\n            #${HistoryOverlayId} *::-webkit-scrollbar-track {\n                background: color-mix(\n                    in srgb,\n                    var(--lb-cubed-lbc-heading-bg, #E5A09E) 55%,\n                    var(--lb-cubed-lbc-bg, #D88482)\n                );\n            }\n\n            #${PanelContentId}::-webkit-scrollbar-thumb,\n            #${PanelId} *::-webkit-scrollbar-thumb,\n            #${HistoryOverlayId} *::-webkit-scrollbar-thumb {\n                background: var(--lb-cubed-lbc-border, #4C2222);\n                border-radius: 4px;\n            }\n\n            #${PanelContentId}::-webkit-scrollbar-button,\n            #${PanelId} *::-webkit-scrollbar-button,\n            #${HistoryOverlayId} *::-webkit-scrollbar-button {\n                color-scheme: var(--lb-cubed-control-color-scheme, light);\n                background-color: var(--lb-cubed-lbc-heading-bg, #E5A09E);\n            }\n\n            #${LayoutGapHandleId}::after,\n            .lb-cubed-page-resize-handle::after,\n            .lb-cubed-resize-handle::after {\n                background: color-mix(\n                    in srgb,\n                    var(--lb-cubed-lbc-border, #4C2222) 62%,\n                    transparent\n                ) !important;\n            }\n\n            #${LayoutGapHandleId}:hover::after,\n            #${LayoutGapHandleId}.lb-cubed-layout-gap-handle-active::after,\n            .lb-cubed-page-resize-handle:hover::after,\n            .lb-cubed-page-resize-handle-active::after {\n                background: var(--lb-cubed-lbc-border, #4C2222) !important;\n            }\n\n'''
source = replace_once(source, css_marker, control_css + css_marker, "theme-aware control CSS")

# Native Letter Boxed DOM text should use the exact foreground, without legacy
# text-fill/opacity tinting that can make it look lighter than the matrix-mapped
# GB foreground. Disabled buttons retain NYT's own disabled opacity.
semantic_anchor = '''            html.lb-cubed-native-theme .lb-word-list,\n            html.lb-cubed-native-theme .lb-word-list-length,\n            html.lb-cubed-native-theme .lb-par,\n            html.lb-cubed-native-theme input,\n            html.lb-cubed-native-theme .lb-text-field,\n            html.lb-cubed-native-theme .lb-text-field * {\n                color: var(--lb-cubed-lb-fg) !important;\n                caret-color: var(--lb-cubed-lb-fg) !important;\n            }'''
semantic_replacement = '''            html.lb-cubed-native-theme .lb-word-list,\n            html.lb-cubed-native-theme .lb-word-list *,\n            html.lb-cubed-native-theme .lb-word-list-length,\n            html.lb-cubed-native-theme .lb-par,\n            html.lb-cubed-native-theme input,\n            html.lb-cubed-native-theme .lb-text-field-label,\n            html.lb-cubed-native-theme .lb-text-field,\n            html.lb-cubed-native-theme .lb-text-field * {\n                color: var(--lb-cubed-lb-fg) !important;\n                -webkit-text-fill-color: var(--lb-cubed-lb-fg) !important;\n                caret-color: var(--lb-cubed-lb-fg) !important;\n            }\n\n            html.lb-cubed-native-theme .lb-word-list,\n            html.lb-cubed-native-theme .lb-word-list *,\n            html.lb-cubed-native-theme .lb-word-list-length,\n            html.lb-cubed-native-theme .lb-text-field-label,\n            html.lb-cubed-native-theme .lb-text-field {\n                opacity: 1 !important;\n            }'''
source = replace_once(source, semantic_anchor, semantic_replacement, "exact native foreground CSS")

# Cover the visible caret's own box and any NYT pseudo-element implementation.
source = replace_once(
    source,
    '''            html.lb-cubed-native-theme .lb-text-field__caret {\n                color: var(--lb-cubed-lb-fg) !important;\n                background: var(--lb-cubed-lb-fg) !important;\n                background-color: var(--lb-cubed-lb-fg) !important;\n                border-color: var(--lb-cubed-lb-fg) !important;\n            }''',
    '''            html.lb-cubed-native-theme .lb-text-field__caret,\n            html.lb-cubed-native-theme .lb-text-field__caret::before,\n            html.lb-cubed-native-theme .lb-text-field__caret::after {\n                color: var(--lb-cubed-lb-fg) !important;\n                background: var(--lb-cubed-lb-fg) !important;\n                background-color: var(--lb-cubed-lb-fg) !important;\n                border-color: var(--lb-cubed-lb-fg) !important;\n                border-left-color: var(--lb-cubed-lb-fg) !important;\n                border-right-color: var(--lb-cubed-lb-fg) !important;\n                outline-color: var(--lb-cubed-lb-fg) !important;\n            }''',
    "caret pseudo-element theming"
)

# Star size/alignment.
solution_css_anchor = '''            #${PanelId} .lb-cubed-nyt-solution .lb-cubed-twofer-row,\n            #${PanelId} .lb-cubed-nyt-solution .lb-cubed-twofer-arrow,\n            #${PanelId} .lb-cubed-nyt-solution .lb-cubed-twofer-revealed {\n                background-color: inherit !important;\n            }'''
solution_css_replacement = solution_css_anchor + '''\n\n            #${PanelId} .lb-cubed-nyt-solution-label {\n                display: inline-flex;\n                align-items: center;\n                gap: 3px;\n            }\n\n            #${PanelId} .lb-cubed-nyt-solution-star {\n                display: inline-flex;\n                align-items: center;\n                justify-content: center;\n                font-size: calc(1em + 2px);\n                line-height: 1;\n            }'''
source = replace_once(source, solution_css_anchor, solution_css_replacement, "NYT solution star CSS")

SOURCE.write_text(source, encoding="utf-8")

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
final_tests = FINAL_TESTS.read_text(encoding="utf-8")
final_tests = replace_once(
    final_tests,
    "assert(source.includes('// @version      1.13.1-beta.17'), 'beta.17 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.18'), 'beta.18 version missing');",
    "final test version"
)
final_tests = replace_once(
    final_tests,
    "assert(source.includes('Same as background'), 'board/background tie control missing');",
    "assert(source.includes('Same as Background'), 'board/background tie control missing');",
    "board label capitalization test"
)
final_tests = replace_once(
    final_tests,
    "assert(source.includes('NytLabel.textContent = \"★ NYT Solution\"'), 'themeable NYT solution star missing');",
    "assert(source.includes('lb-cubed-nyt-solution-star'), 'separately sized NYT solution star missing');",
    "solution star test"
)
extra_assert_anchor = "assert(source.includes('Heading background'), 'LBC heading background control missing');\n"
extra_asserts = '''assert(source.includes('LbcBackgroundMatchesLbBackground'), 'LBC/background semantic link missing');\nassert(source.includes('LbcTextMatchesLbForeground'), 'LBC/text semantic link missing');\nassert(source.includes('Same as Letter Boxed Background'), 'LBC background link checkbox missing');\nassert(source.includes('Same as Letter Boxed Foreground'), 'LBC text link checkbox missing');\nassert(source.includes('ApplyCompactNumberInputWidth'), 'compact number input sizing missing');\nassert(source.includes('--lb-cubed-control-color-scheme'), 'theme-aware native control color scheme missing');\nassert(source.includes('scrollbar-color:'), 'theme-aware scrollbar styling missing');\nassert(source.includes('::-webkit-inner-spin-button'), 'always-visible number steppers missing');\nassert(source.includes('0.6ch !important'), 'number input stepper spacing missing');\nassert(source.includes('font-size: calc(1em + 2px)'), 'NYT solution star +2px sizing missing');\nassert(source.includes('0.65'), 'NYT solution tint/shade derivation missing');\nassert(source.includes('Google Drive bridge returned HTML instead of JSON'), 'Drive HTML response retry guard missing');\nassert(source.includes('no HTML was imported into LBC data'), 'Drive HTML failure explanation missing');\nassert(source.includes('.lb-text-field__caret::before'), 'caret pseudo-element theming missing');\nassert(source.includes('-webkit-text-fill-color: var(--lb-cubed-lb-fg)'), 'exact native foreground fill missing');\n'''
if "LBC/background semantic link missing" not in final_tests:
    final_tests = replace_once(final_tests, extra_assert_anchor, extra_assert_anchor + extra_asserts, "new final assertions")
FINAL_TESTS.write_text(final_tests, encoding="utf-8")

cloud_tests = CLOUD_TESTS.read_text(encoding="utf-8")
cloud_tests = replace_once(
    cloud_tests,
    '''    Options.onload({\n      status: 200,\n      responseText: JSON.stringify(Response)\n    });''',
    '''    Options.onload({\n      status: Response?.__status ?? 200,\n      responseText: Object.prototype.hasOwnProperty.call(Response || {}, '__raw')\n        ? String(Response.__raw)\n        : JSON.stringify(Response)\n    });''',
    "cloud test raw response support"
)

# Add a regression after the clean-sync test: transient HTML must never be fed
# to JSON.parse/merge and a replayed Write must preserve the same WriteId.
cloud_test_anchor = "test('dirty automatic sync is push-only and increments expected revision', async () => {"
cloud_test = '''test('transient Apps Script HTML response retries once with the same idempotent WriteId', async () => {\n  const key = 'LetterBoxedTracker_3000';\n  put(key, ['ALPHA']);\n  T.SetSession({Ready: true, ExpectedRevision: 7, Dirty: false, Status: 'Synced'});\n  T.MarkCloudSyncDirty();\n\n  let count = 0;\n  BridgeHandler = Request => {\n    count++;\n    if (count === 1) {\n      return {__raw: '<!DOCTYPE html><html><body>temporary Apps Script page</body></html>'};\n    }\n    return {Status: 'ok', Revision: 8};\n  };\n\n  await T.SyncWithGoogleDrive();\n\n  eq(actions(), ['Write', 'Write'], 'HTML response should retry the same Write once');\n  assert(Requests[0].WriteId === Requests[1].WriteId, 'HTML retry changed the idempotency WriteId');\n  const State = T.GetState();\n  assert(State.ExpectedRevision === 8, 'HTML retry did not retain successful revision');\n  assert(State.Dirty === false, 'HTML retry left successful data dirty');\n  assert(State.Status === 'Synced', 'HTML retry did not finish Synced');\n});\n\n'''
if "transient Apps Script HTML response retries once" not in cloud_tests:
    cloud_tests = replace_once(cloud_tests, cloud_test_anchor, cloud_test + cloud_test_anchor, "cloud HTML retry test")
CLOUD_TESTS.write_text(cloud_tests, encoding="utf-8")
