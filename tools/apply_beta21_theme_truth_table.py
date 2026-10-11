from pathlib import Path

SOURCE = Path("LetterBoxedCubed.user.js")
TESTS = Path("tests/final-polish-tests.js")


def require_replace(text, old, new, label, count=1):
    found = text.count(old)
    if found != count:
        raise RuntimeError(f"{label}: expected {count} match(es), found {found}")
    return text.replace(old, new, count)


def replace_range(text, start_marker, end_marker, new_text, label):
    start = text.find(start_marker)
    if start < 0:
        raise RuntimeError(f"{label}: start marker missing")
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        raise RuntimeError(f"{label}: end marker missing")
    return text[:start] + new_text + text[end:]


def replace_function(text, function_name, next_function_name, new_text, label):
    start = f"    function {function_name}("
    end = f"    function {next_function_name}("
    return replace_range(text, start, end, new_text, label)


source = SOURCE.read_text(encoding="utf-8")

source = require_replace(
    source,
    "// @version      1.13.1-beta.20",
    "// @version      1.13.1-beta.21",
    "version",
)

# Built-ins: calibrate Light from the native screenshot, and run Light through
# the same semantic compositor as Dark/custom themes so mid-puzzle switching
# never depends on stale canvas state.
source = require_replace(
    source,
    '''            /* Native web Light already supplies this exact presentation. */
            ApplyNative: false,''',
    '''            /* Use the same semantic compositor as every other theme. */
            ApplyNative: true,''',
    "Light compositor",
)
source = source.replace('LbBackground: "#FAA6A4"', 'LbBackground: "#E3A5A3"')
source = source.replace('LbcBackground: "#FAA6A4"', 'LbcBackground: "#E3A5A3"')
source = require_replace(
    source,
    '''            Name: "NYT Dark",
            ApplyNative: true,
            BoardMatchesBackground: true,''',
    '''            Name: "NYT Dark",
            ApplyNative: true,
            BoardMatchesBackground: false,''',
    "Dark secondary independence",
)

# Three-color semantics. LbForeground remains as a compatibility storage key,
# but becomes derived from Primary every time a theme is applied.
contrast = '''    function GetThemeContrastPole(Value) {
        return GetThemeRelativeLuminance(Value) < 0.38
            ? "#FFFFFF"
            : "#000000";
    }
'''
source = require_replace(
    source,
    contrast,
    contrast + '''
    function GetLbThemeSemantics(Palette) {
        const IsDark = GetThemeRelativeLuminance(Palette.LbBackground) < 0.38;
        const TextInput = GetThemeContrastPole(Palette.LbBackground);

        return {
            IsDark,
            TextInput,
            BoardOutline: TextInput,
            SuccessToastBackground: "#FFFFFF",
            SuccessToastForeground: "#000000",
            ErrorToastBackground: IsDark ? TextInput : "#000000",
            ErrorToastForeground: IsDark ? Palette.LbBackground : "#FFFFFF"
        };
    }
''',
    "LB semantic derivation",
)

# The canvas needs two very narrow dark-mode disambiguation hooks. Native NYT
# source colors collide: white is both board fill and unused glyph; black is
# both outline and active/used glyph. We remap only single-letter text draws.
source = require_replace(
    source,
    '''    let NativeBoardFillText = null;
    let NativeBoardStrokeText = null;''',
    '''    let NativeBoardFillText = null;
    let NativeBoardStrokeText = null;
    let NativeBoardStroke = null;''',
    "board hook state",
)

old_is_white = '''    function IsNativeBoardWhite(Value) {
        const Text = String(Value || "")
            .trim()
            .toLowerCase()
            .replace(/\\s+/g, "");
        return (
            Text === "#fff" ||
            Text === "#ffffff" ||
            Text === "white" ||
            Text === "rgb(255,255,255)" ||
            Text === "rgba(255,255,255,1)"
        );
    }
'''
new_is_white = '''    function NormalizeNativeBoardPaint(Value) {
        return String(Value || "")
            .trim()
            .toLowerCase()
            .replace(/\\s+/g, "");
    }

    function IsNativeBoardWhite(Value) {
        const Text = NormalizeNativeBoardPaint(Value);
        return (
            Text === "#fff" ||
            Text === "#ffffff" ||
            Text === "white" ||
            Text === "rgb(255,255,255)" ||
            Text === "rgba(255,255,255,1)"
        );
    }

    function IsNativeBoardBlack(Value) {
        const Text = NormalizeNativeBoardPaint(Value);
        return (
            Text === "#000" ||
            Text === "#000000" ||
            Text === "black" ||
            Text === "rgb(0,0,0)" ||
            Text === "rgba(0,0,0,1)"
        );
    }

    function IsNativeBoardActive(Value) {
        const Text = NormalizeNativeBoardPaint(Value);
        return (
            Text === NativeBoardActiveSourceColor.toLowerCase() ||
            Text === "rgb(232,169,160)" ||
            Text === "rgba(232,169,160,1)"
        );
    }
'''
source = require_replace(source, old_is_white, new_is_white, "board paint helpers")

new_hook = '''    function InstallBoardTextSourceHook() {
        if (BoardTextSourceHookInstalled) {
            return;
        }

        const Prototype = PageWindow.CanvasRenderingContext2D?.prototype;
        if (!Prototype) {
            return;
        }

        NativeBoardFillText = Prototype.fillText;
        NativeBoardStrokeText = Prototype.strokeText;
        NativeBoardStroke = Prototype.stroke;

        const IsThemedBoardContext = Context =>
            document.documentElement?.classList.contains("lb-cubed-board-themed") &&
            IsLetterBoxedBoardCanvas(Context?.canvas);

        const IsDarkBoardContext = Context =>
            IsThemedBoardContext(Context) &&
            document.documentElement?.classList.contains("lb-cubed-theme-dark");

        const IsBoardLetter = (Context, Text) =>
            IsThemedBoardContext(Context) &&
            /^[A-Z]$/.test(String(Text || "").trim());

        const GetDarkLetterSource = Paint => {
            if (IsNativeBoardWhite(Paint)) {
                return "#000000";
            }
            if (IsNativeBoardBlack(Paint)) {
                return NativeBoardActiveSourceColor;
            }
            return null;
        };

        if (typeof NativeBoardFillText === "function") {
            Prototype.fillText = function (Text, ...Arguments) {
                const Replacement =
                    IsDarkBoardContext(this) && IsBoardLetter(this, Text)
                        ? GetDarkLetterSource(this.fillStyle)
                        : null;
                if (!Replacement) {
                    return NativeBoardFillText.call(this, Text, ...Arguments);
                }

                const Previous = this.fillStyle;
                this.fillStyle = Replacement;
                try {
                    return NativeBoardFillText.call(this, Text, ...Arguments);
                } finally {
                    this.fillStyle = Previous;
                }
            };
        }

        if (typeof NativeBoardStrokeText === "function") {
            Prototype.strokeText = function (Text, ...Arguments) {
                const Replacement =
                    IsDarkBoardContext(this) && IsBoardLetter(this, Text)
                        ? GetDarkLetterSource(this.strokeStyle)
                        : null;
                if (!Replacement) {
                    return NativeBoardStrokeText.call(this, Text, ...Arguments);
                }

                const Previous = this.strokeStyle;
                this.strokeStyle = Replacement;
                try {
                    return NativeBoardStrokeText.call(this, Text, ...Arguments);
                } finally {
                    this.strokeStyle = Previous;
                }
            };
        }

        /*
            Used nodes are native active-fill + native-black outline. Dark mode
            wants both surfaces Tertiary. Promote only that exact outline paint.
            The mobile current/last node is active-outline + black-fill already,
            so it naturally becomes Tertiary-outline + derived-white-fill.
        */
        if (typeof NativeBoardStroke === "function") {
            Prototype.stroke = function (...Arguments) {
                if (
                    IsDarkBoardContext(this) &&
                    IsNativeBoardBlack(this.strokeStyle) &&
                    IsNativeBoardActive(this.fillStyle)
                ) {
                    const Previous = this.strokeStyle;
                    this.strokeStyle = NativeBoardActiveSourceColor;
                    try {
                        return NativeBoardStroke.call(this, ...Arguments);
                    } finally {
                        this.strokeStyle = Previous;
                    }
                }
                return NativeBoardStroke.call(this, ...Arguments);
            };
        }

        BoardTextSourceHookInstalled = true;
    }

'''
source = replace_function(
    source,
    "InstallBoardTextSourceHook",
    "QueueBoardThemeRendererRefresh",
    new_hook,
    "board semantic hook",
)

# Apply Primary / Secondary / Tertiary consistently. Stored BoardMatchesBackground
# is ignored at runtime; the old flag survives only for backward-compatible data.
new_apply = '''    function ApplyTheme() {
        if (!ThemeState) {
            ThemeState = CreateDefaultThemeState();
        }

        const Theme = GetActiveThemeDefinition();
        const Palette = NormalizeThemePalette(
            Theme.Palette,
            PrebuiltThemes[DefaultThemeId].Palette,
            false
        );
        const Root = document.documentElement;
        if (!Root) {
            return;
        }

        const LbSemantics = GetLbThemeSemantics(Palette);
        Palette.LbForeground = LbSemantics.TextInput;

        if (Theme.LbcBackgroundMatchesLbBackground) {
            Palette.LbcBackground = Palette.LbBackground;
        }
        if (Theme.LbcTextMatchesLbForeground) {
            Palette.LbcText = Palette.LbForeground;
        }

        const MutedText = GetDerivedLbcMutedText(Palette);
        const LbcAccent = GetDerivedLbcAccent(Palette);
        const NytSolutionText = GetDerivedNytSolutionText(Palette);
        const ControlColorScheme =
            GetThemeRelativeLuminance(Palette.LbcBackground) < 0.38
                ? "dark"
                : "light";

        const Variables = {
            "--lb-cubed-lb-primary": Palette.LbBackground,
            "--lb-cubed-lb-secondary": Palette.LbBoard,
            "--lb-cubed-lb-tertiary": Palette.LbActive,
            "--lb-cubed-lb-bg": Palette.LbBackground,
            "--lb-cubed-lb-board": Palette.LbBoard,
            "--lb-cubed-lb-fg": Palette.LbForeground,
            "--lb-cubed-lb-active": Palette.LbActive,
            "--lb-cubed-success-toast-bg": LbSemantics.SuccessToastBackground,
            "--lb-cubed-success-toast-fg": LbSemantics.SuccessToastForeground,
            "--lb-cubed-error-toast-bg": LbSemantics.ErrorToastBackground,
            "--lb-cubed-error-toast-fg": LbSemantics.ErrorToastForeground,
            "--lb-cubed-lb-page-bg": Palette.LbBackground,
            "--lb-cubed-lb-text": Palette.LbForeground,
            "--lb-cubed-lb-surface": Palette.LbBackground,
            "--lb-cubed-lb-border": Palette.LbForeground,
            "--lb-cubed-lb-accent": Palette.LbActive,
            "--lb-cubed-lbc-bg": Palette.LbcBackground,
            "--lb-cubed-lbc-heading-bg": Palette.LbcHeadingBackground,
            "--lb-cubed-lbc-surface": Palette.LbcHeadingBackground,
            "--lb-cubed-lbc-text": Palette.LbcText,
            "--lb-cubed-lbc-muted": MutedText,
            "--lb-cubed-lbc-border": Palette.LbcBorder,
            "--lb-cubed-lbc-accent": LbcAccent,
            "--lb-cubed-control-color-scheme": ControlColorScheme,
            "--lb-cubed-nyt-solution": Palette.NytSolution,
            "--lb-cubed-nyt-solution-text": NytSolutionText,
            "--lb-cubed-new-highlight": Palette.NewHighlight,
            "--lb-cubed-redacted": Palette.Redacted,
            "--lb-cubed-success": FixedSuccessColor,
            "--lb-cubed-danger": FixedDangerColor
        };

        for (const [Name, Value] of Object.entries(Variables)) {
            Root.style.setProperty(Name, Value);
        }

        Root.classList.add("lb-cubed-native-theme", "lb-cubed-board-themed");
        Root.classList.toggle("lb-cubed-theme-dark", LbSemantics.IsDark);
        Root.dataset.lbcTheme = Theme.Id || DefaultThemeId;
        Root.dataset.lbcThemeMode = LbSemantics.IsDark ? "dark" : "light";

        ApplyBoardThemeMatrix(Palette);
        QueueBoardThemeRendererRefresh();
    }

'''
source = replace_function(source, "ApplyTheme", "SetActiveTheme", new_apply, "ApplyTheme")

# Custom themes no longer carry an active board/background tie into new copies.
source = require_replace(
    source,
    '''        const BoardMatchesBackground = Boolean(
            Base.BoardMatchesBackground
        );''',
    '''        const BoardMatchesBackground = false;''',
    "new custom secondary independence",
)
source = require_replace(
    source,
    '''        const Palette = NormalizeThemePalette(
            Base.Palette,
            null,
            BoardMatchesBackground
        );

        if (BoardMatchesBackground) {
            Palette.LbBoard = Palette.LbBackground;
        }''',
    '''        const Palette = NormalizeThemePalette(
            Base.Palette,
            null,
            false
        );
        Palette.LbForeground = GetThemeContrastPole(Palette.LbBackground);''',
    "custom palette normalization",
)

old_update_bg = '''        if (Key === "LbBackground" && Theme.BoardMatchesBackground) {
            Theme.Palette.LbBoard = Theme.Palette.LbBackground;
        }
        if (
            Key === "LbBackground" &&
            Theme.LbcBackgroundMatchesLbBackground
        ) {
            Theme.Palette.LbcBackground = Theme.Palette.LbBackground;
        }
        if (
            Key === "LbForeground" &&
            Theme.LbcTextMatchesLbForeground
        ) {
            Theme.Palette.LbcText = Theme.Palette.LbForeground;
        }
'''
new_update_bg = '''        if (Key === "LbBackground") {
            Theme.Palette.LbForeground = GetThemeContrastPole(
                Theme.Palette.LbBackground
            );
            if (Theme.LbcBackgroundMatchesLbBackground) {
                Theme.Palette.LbcBackground = Theme.Palette.LbBackground;
            }
            if (Theme.LbcTextMatchesLbForeground) {
                Theme.Palette.LbcText = Theme.Palette.LbForeground;
            }
        }
'''
source = require_replace(source, old_update_bg, new_update_bg, "custom Primary updates")

source = require_replace(
    source,
    '''        Theme.LbcTextMatchesLbForeground = Boolean(Value);
        if (Theme.LbcTextMatchesLbForeground) {
            Theme.Palette.LbcText = Theme.Palette.LbForeground;
        }''',
    '''        Theme.LbcTextMatchesLbForeground = Boolean(Value);
        Theme.Palette.LbForeground = GetThemeContrastPole(
            Theme.Palette.LbBackground
        );
        if (Theme.LbcTextMatchesLbForeground) {
            Theme.Palette.LbcText = Theme.Palette.LbForeground;
        }''',
    "LBC linked Text derivation",
)

# Simplify the Letter Boxed theme editor to the three user-controlled colors.
source = replace_function(
    source,
    "CreateThemeBoardColorRow",
    "CreateThemeLinkedColorRow",
    "",
    "remove board-link editor row",
)
source = require_replace(
    source,
    '''            [
                CreateThemeColorRow("Background", "LbBackground"),
                CreateThemeBoardColorRow(Section),
                CreateThemeColorRow("Foreground", "LbForeground"),
                CreateThemeColorRow("Foreground (active)", "LbActive")
            ]''',
    '''            [
                CreateThemeColorRow("Primary (background)", "LbBackground"),
                CreateThemeColorRow("Secondary (board)", "LbBoard"),
                CreateThemeColorRow("Tertiary (active / used)", "LbActive")
            ]''',
    "three-color menu",
)
source = source.replace("Same as Letter Boxed Foreground", "Same as Letter Boxed Text")

source = require_replace(
    source,
    '''        Note.textContent =
            "Muted text and secondary accents are derived automatically. " +
            "Success/error indicators remain fixed green/red.";''',
    '''        Note.textContent =
            "Letter Boxed text, outlines, node states, connectors and toast colors " +
            "are derived from Primary / Secondary / Tertiary. LBC muted text and " +
            "secondary accents are derived automatically.";''',
    "theme note",
)

# Revert beta.20's mistaken Text Input -> Tertiary mapping. The generic native
# rule immediately above already maps input text to derived LbForeground.
active_start = '''            /* Current word entry belongs to the same active semantic lane as the GB path. */'''
active_end = '''            html.lb-cubed-native-theme .lb-text-field-underline {'''
source = replace_range(source, active_start, active_end, "", "Text Input semantics")

# Split the success and error toast palettes according to the truth table.
toast_start = '''            /*
                Theme transient validation/praise as one semantic LB surface:'''
toast_end = '''            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-par.no-words {'''
toast_css = '''            /* Success = black on white. Error = white on black in a light
               theme; dark themes use Text Input as background and Primary as text. */
            html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy {
                background-color: var(--lb-cubed-success-toast-bg) !important;
                color: var(--lb-cubed-success-toast-fg) !important;
                border-color: var(--lb-cubed-success-toast-bg) !important;
                text-shadow: none !important;
            }

            html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy * {
                color: var(--lb-cubed-success-toast-fg) !important;
                -webkit-text-fill-color: var(--lb-cubed-success-toast-fg) !important;
                fill: currentColor !important;
                text-shadow: none !important;
            }

            html.lb-cubed-native-theme .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-message-box,
            html.lb-cubed-native-theme .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-par:not(.no-words) {
                background-color: var(--lb-cubed-error-toast-bg) !important;
                color: var(--lb-cubed-error-toast-fg) !important;
                border-color: var(--lb-cubed-error-toast-bg) !important;
                text-shadow: none !important;
            }

            html.lb-cubed-native-theme .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-message-box *,
            html.lb-cubed-native-theme .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-par:not(.no-words) * {
                color: var(--lb-cubed-error-toast-fg) !important;
                -webkit-text-fill-color: var(--lb-cubed-error-toast-fg) !important;
                fill: currentColor !important;
                text-shadow: none !important;
            }

'''
source = replace_range(source, toast_start, toast_end, toast_css, "toast truth table")

# Win modal stays white; keep its close X black even while the surrounding game
# uses a dark theme.
modal_anchor = '''            html.lb-cubed-native-theme .lb-word-list,
            html.lb-cubed-native-theme .lb-word-list *,'''
modal_css = '''            html.lb-cubed-theme-dark button[data-testid="modal-close"] {
                background: transparent !important;
                background-color: transparent !important;
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
                border-color: transparent !important;
            }

            html.lb-cubed-theme-dark button[data-testid="modal-close"] .pz-icon,
            html.lb-cubed-theme-dark button[data-testid="modal-close"] .pz-icon::before,
            html.lb-cubed-theme-dark button[data-testid="modal-close"] .pz-icon::after {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }

'''
modal_pos = source.find(modal_anchor)
if modal_pos < 0:
    raise RuntimeError("modal close anchor missing")
source = source[:modal_pos] + modal_css + source[modal_pos:]

# Hints empty message is foreground; Twofer arrows remain muted.
source = require_replace(
    source,
    '''            #${PanelId} .lb-cubed-twofer-solution-text,
            #${PanelId} .lb-cubed-length-value,''',
    '''            #${PanelId} .lb-cubed-twofer-solution-text,
            #${PanelId} .lb-cubed-potential-word-empty,
            #${PanelId} .lb-cubed-length-value,''',
    "Hints empty foreground",
)
source = require_replace(
    source,
    '''            #${PanelId} .lb-cubed-twofer-disclaimer,
            #${PanelId} .lb-cubed-twofer-group-title,''',
    '''            #${PanelId} .lb-cubed-twofer-disclaimer,
            #${PanelId} .lb-cubed-twofer-arrow,
            #${PanelId} .lb-cubed-twofer-group-title,''',
    "Twofer arrow muted style",
)

# NYT Solution special colors are strictly wrapper + heading; word cells use
# ordinary Twofer styling so redaction remains intact.
nyt_base_start = '''            /*
                NYT's published solution.'''
nyt_base_end = '''            /*
                ================================================================
                WORDS BY LENGTH'''
nyt_base_css = '''            /* NYT solution decoration: card + heading only. */
            .lb-cubed-nyt-solution {
                padding: 4px;
                background-color: rgb(218, 203, 119);
                border: 1px solid rgba(105, 88, 19, 0.45);
                border-radius: 4px;
            }

            .lb-cubed-nyt-solution-label {
                margin: 0 0 3px 1px;
                color: rgb(71, 57, 8);
                font-size: 10px;
                font-weight: 700;
                line-height: 1.2;
            }

'''
source = replace_range(source, nyt_base_start, nyt_base_end, nyt_base_css, "base solution scope")

nyt_theme_start = '''            #${PanelId} .lb-cubed-nyt-solution,
            #${HistoryOverlayId} .lb-cubed-history-custom-word {'''
nyt_theme_end = '''            #${PanelId} .lb-cubed-nyt-solution-label {
                display: inline-flex;'''
nyt_theme_css = '''            #${PanelId} .lb-cubed-nyt-solution {
                background-color: var(--lb-cubed-nyt-solution) !important;
                border-color: color-mix(
                    in srgb,
                    var(--lb-cubed-nyt-solution-text) 52%,
                    transparent
                ) !important;
            }

            #${PanelId} .lb-cubed-nyt-solution-label {
                color: var(--lb-cubed-nyt-solution-text) !important;
                -webkit-text-fill-color: var(--lb-cubed-nyt-solution-text) !important;
            }

            #${HistoryOverlayId} .lb-cubed-history-custom-word {
                background-color: var(--lb-cubed-nyt-solution) !important;
                color: var(--lb-cubed-nyt-solution-text) !important;
            }

'''
source = replace_range(source, nyt_theme_start, nyt_theme_end, nyt_theme_css, "themed solution scope")

source = require_replace(
    source,
    '''                color: var(--lb-cubed-redacted) !important;
                border-color: var(--lb-cubed-redacted) !important;
                text-shadow: none !important;''',
    '''                color: var(--lb-cubed-redacted) !important;
                -webkit-text-fill-color: var(--lb-cubed-redacted) !important;
                border-color: var(--lb-cubed-redacted) !important;
                text-shadow: none !important;''',
    "redacted text fill",
)

source = source.replace(
    '''                The SVG affine filter above the bitmap maps source black ->
                Foreground, source white -> Board, and source active coral ->
                Foreground (active). Because the bitmap itself is never mutated,''',
    '''                The SVG affine filter above the bitmap maps source black ->
                derived Text/Outline, source white -> Secondary, and source active
                coral -> Tertiary. Because the bitmap itself is never mutated,'''
)

SOURCE.write_text(source, encoding="utf-8")

TESTS.write_text(r'''const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'LetterBoxedCubed.user.js'), 'utf8');
const preview = fs.readFileSync(path.join(root, 'tools', 'preview_runtime.js'), 'utf8');
function assert(condition, message) { if (!condition) throw new Error(message); }

assert(source.includes('// @version      1.13.1-beta.21'), 'beta.21 version missing');
assert(source.includes('const ExportFormatVersion = 4;'), 'backup schema v4 missing');
assert(source.includes('const ThemeStateVersion = 2;'), 'ThemeState v2 compatibility missing');
assert(source.includes('MergeThemeStates'), 'theme merge missing');
assert(source.includes('Name: "NYT Light"'), 'Light preset missing');
assert(source.includes('Name: "NYT Dark"'), 'Dark preset missing');
assert(source.includes('LbBackground: "#E3A5A3"'), 'Light Primary calibration missing');
assert(source.includes('LbBoard: "#FFFFFF"'), 'Light Secondary missing');
assert(source.includes('LbBackground: "#121212"'), 'Dark Primary missing');
assert(source.includes('LbBoard: "#121212"'), 'Dark Secondary missing');
assert(source.includes('LbActive: "#DA5D57"'), 'Dark Tertiary missing');
assert(source.includes('GetLbThemeSemantics'), 'semantic derivation missing');
assert(source.includes('Primary (background)'), 'Primary editor missing');
assert(source.includes('Secondary (board)'), 'Secondary editor missing');
assert(source.includes('Tertiary (active / used)'), 'Tertiary editor missing');
assert(!source.includes('CreateThemeBoardColorRow('), 'obsolete board-link UI remains');
assert(source.includes('Same as Letter Boxed Background'), 'LBC background link missing');
assert(source.includes('Same as Letter Boxed Text'), 'LBC text link missing');
assert(source.includes('Root.classList.add("lb-cubed-native-theme", "lb-cubed-board-themed")'), 'unified compositor missing');
assert(source.includes('lb-cubed-theme-dark'), 'dark semantic class missing');
assert(source.includes('--lb-cubed-success-toast-bg'), 'success toast vars missing');
assert(source.includes('--lb-cubed-error-toast-bg'), 'error toast vars missing');
assert(source.includes('ErrorToastBackground: IsDark ? TextInput : "#000000"'), 'error toast background rule missing');
assert(source.includes('ErrorToastForeground: IsDark ? Palette.LbBackground : "#FFFFFF"'), 'error toast foreground rule missing');
assert(source.includes('BuildBoardThemeAffineMatrix'), 'board affine matrix missing');
assert(source.includes('NativeBoardStroke = Prototype.stroke'), 'used-node stroke hook missing');
assert(source.includes('GetDarkLetterSource'), 'dark letter source mapping missing');
assert(source.includes('IsNativeBoardBlack'), 'black source detector missing');
assert(source.includes('IsNativeBoardActive'), 'active source detector missing');
assert(source.includes('this.strokeStyle = NativeBoardActiveSourceColor'), 'used-node outline promotion missing');
assert(source.includes('QueueBoardThemeRendererRefresh();'), 'theme-switch board refresh missing');
assert(source.includes('.lb-cubed-potential-word-empty,'), 'Hints empty foreground missing');
assert(source.includes('font-size: calc(1em + 5px)'), 'NYT solution star size missing');
assert(!source.includes('#${PanelId} .lb-cubed-nyt-solution * {'), 'solution still recolors all descendants');
assert(source.includes('-webkit-text-fill-color: var(--lb-cubed-redacted)'), 'redaction fill guard missing');
assert(source.includes('button[data-testid="modal-close"]'), 'win modal close override missing');
assert(source.includes('ApplyCompactNumberInputWidth'), 'number sizing missing');
assert(source.includes('DigitCount + 1}ch + 22px'), 'number breathing room missing');
assert(source.includes('Google Drive bridge returned HTML instead of JSON'), 'Drive HTML guard missing');
assert(source.includes('lb-message-box success-message lb-cubed-valid-feedback-proxy'), 'valid feedback proxy missing');
assert(source.includes('ValidFeedbackProxyMinimumVisibleMs = 600'), 'valid toast lifetime missing');
assert(source.includes('InternalPanelLayoutBreakpoints = ['), 'responsive breakpoints missing');
for (const breakpoint of ['340', '390', '520', '650', '860', '1180']) assert(source.includes(breakpoint), `breakpoint missing ${breakpoint}`);
for (const label of ['Copy Board Source Snapshot','Start Board Canvas Trace','Stop + Copy Board Trace','Copy Full Debug Bundle']) assert(preview.includes(label), `preview diagnostic missing ${label}`);
console.log('PASS: beta.21 semantic theme static checks');
''', encoding="utf-8")
