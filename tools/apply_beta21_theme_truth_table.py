from pathlib import Path

SOURCE = Path("LetterBoxedCubed.user.js")
TESTS = Path("tests/final-polish-tests.js")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 match, found {count}")
    return text.replace(old, new, 1)


def replace_between(text, start, end, replacement, label):
    start_index = text.find(start)
    if start_index < 0:
        raise RuntimeError(f"{label}: start marker not found")
    end_index = text.find(end, start_index + len(start))
    if end_index < 0:
        raise RuntimeError(f"{label}: end marker not found")
    return text[:start_index] + replacement + text[end_index:]


source = SOURCE.read_text(encoding="utf-8")

source = replace_once(
    source,
    "// @version      1.13.1-beta.20",
    "// @version      1.13.1-beta.21",
    "userscript version",
)

# Run every theme, including NYT Light, through the same semantic compositor.
# This removes the old native-Light special case that made live theme switching
# dependent on whatever state NYT happened to have already painted.
source = replace_once(
    source,
    '''            /* Native web Light already supplies this exact presentation. */\n            ApplyNative: false,''',
    '''            /* Keep Light on the same semantic compositor as every other theme. */\n            ApplyNative: true,''',
    "NYT Light compositor",
)
source = source.replace('LbBackground: "#FAA6A4"', 'LbBackground: "#E3A5A3"')
source = source.replace('LbcBackground: "#FAA6A4"', 'LbcBackground: "#E3A5A3"')
source = replace_once(
    source,
    '''            Name: "NYT Dark",\n            ApplyNative: true,\n            BoardMatchesBackground: true,''',
    '''            Name: "NYT Dark",\n            ApplyNative: true,\n            BoardMatchesBackground: false,''',
    "NYT Dark independent secondary color",
)

# The persisted v2 shape stays compatible, but the editable LB model is now:
# Primary = page/background, Secondary = board, Tertiary = state/accent.
# LbForeground becomes a derived compatibility field (black/white from Primary).
normalize_custom_start = '''    function NormalizeCustomThemeRecord(RawTheme, Id) {'''
normalize_custom_end = '''    function NormalizeThemeState(RawState) {'''
normalize_custom_new = '''    function NormalizeCustomThemeRecord(RawTheme, Id) {
        if (!RawTheme || typeof RawTheme !== "object" || Array.isArray(RawTheme)) {
            return null;
        }

        const ThemeId = String(RawTheme.Id || Id || "").trim();
        if (!ThemeId) {
            return null;
        }

        /*
            BoardMatchesBackground is retained only as a migration hint for
            beta-era themes. If it was enabled, preserve that relationship once
            while reading the old record, then decouple Secondary from Primary
            in the normalized record so the new three-color model is stable.
        */
        const LegacyBoardMatchesBackground =
            Object.prototype.hasOwnProperty.call(
                RawTheme,
                "BoardMatchesBackground"
            )
                ? Boolean(RawTheme.BoardMatchesBackground)
                : Boolean(RawTheme.InvertBoard);

        const Palette = NormalizeThemePalette(
            RawTheme.Palette,
            null,
            LegacyBoardMatchesBackground
        );
        const LegacyForeground = Palette.LbForeground;

        const LbcBackgroundMatchesLbBackground =
            Object.prototype.hasOwnProperty.call(
                RawTheme,
                "LbcBackgroundMatchesLbBackground"
            )
                ? Boolean(RawTheme.LbcBackgroundMatchesLbBackground)
                : Palette.LbcBackground === Palette.LbBackground;
        const LbcTextMatchesLbForeground =
            Object.prototype.hasOwnProperty.call(
                RawTheme,
                "LbcTextMatchesLbForeground"
            )
                ? Boolean(RawTheme.LbcTextMatchesLbForeground)
                : Palette.LbcText === LegacyForeground;

        Palette.LbForeground = GetThemeContrastPole(Palette.LbBackground);
        if (LbcBackgroundMatchesLbBackground) {
            Palette.LbcBackground = Palette.LbBackground;
        }
        if (LbcTextMatchesLbForeground) {
            Palette.LbcText = Palette.LbForeground;
        }

        return {
            Id: ThemeId,
            Name: String(RawTheme.Name || "Custom Theme").trim() || "Custom Theme",
            Palette,
            BoardMatchesBackground: false,
            LbcBackgroundMatchesLbBackground,
            LbcTextMatchesLbForeground,
            Deleted: Boolean(RawTheme.Deleted),
            UpdatedAt: NormalizeTimestamp(RawTheme.UpdatedAt)
        };
    }

'''
source = replace_between(
    source,
    normalize_custom_start,
    normalize_custom_end,
    normalize_custom_new,
    "custom-theme normalization",
)

contrast_anchor = '''    function GetThemeContrastPole(Value) {
        return GetThemeRelativeLuminance(Value) < 0.38
            ? "#FFFFFF"
            : "#000000";
    }
'''
contrast_replacement = contrast_anchor + '''
    function GetLbThemeSemantics(Palette) {
        const IsDark =
            GetThemeRelativeLuminance(Palette.LbBackground) < 0.38;
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
'''
source = replace_once(
    source,
    contrast_anchor,
    contrast_replacement,
    "LB semantic derivation",
)

# Add the native path-stroke hook used only for dark used-letter nodes.
source = replace_once(
    source,
    '''    let NativeBoardFillText = null;\n    let NativeBoardStrokeText = null;''',
    '''    let NativeBoardFillText = null;\n    let NativeBoardStrokeText = null;\n    let NativeBoardStroke = null;''',
    "board stroke hook state",
)

board_hook_start = '''    function IsNativeBoardWhite(Value) {'''
board_hook_end = '''    function QueueBoardThemeRendererRefresh() {'''
board_hook_new = '''    function NormalizeNativeBoardPaint(Value) {
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

    function InstallBoardTextSourceHook() {
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
            document.documentElement?.classList.contains(
                "lb-cubed-board-themed"
            ) &&
            IsLetterBoxedBoardCanvas(Context?.canvas);

        const IsDarkThemedBoardContext = Context =>
            IsThemedBoardContext(Context) &&
            document.documentElement?.classList.contains(
                "lb-cubed-theme-dark"
            );

        const IsThemedBoardLetterDraw = (Context, Text) =>
            IsThemedBoardContext(Context) &&
            /^[A-Z]$/.test(String(Text || "").trim());

        /*
            NYT Light's source bitmap carries exactly the state distinctions we
            need, but two pairs collide at the RGB level:

              white = board/node fill AND unused letter glyph
              black = board/unused outline AND active/used letter glyph

            In a dark semantic theme, remap only single-letter glyph draws:
            source white -> source black -> derived Text/Outline (white), and
            source black -> native active -> Tertiary. Geometry/path paints are
            untouched, so the board square and unused node outlines still map
            from black to the derived Text/Outline color.
        */
        const GetDarkLetterReplacement = Paint => {
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
                    IsThemedBoardLetterDraw(this, Text) &&
                    IsDarkThemedBoardContext(this)
                        ? GetDarkLetterReplacement(this.fillStyle)
                        : null;

                if (Replacement) {
                    const Previous = this.fillStyle;
                    this.fillStyle = Replacement;
                    try {
                        return NativeBoardFillText.call(
                            this,
                            Text,
                            ...Arguments
                        );
                    } finally {
                        this.fillStyle = Previous;
                    }
                }

                return NativeBoardFillText.call(this, Text, ...Arguments);
            };
        }

        if (typeof NativeBoardStrokeText === "function") {
            Prototype.strokeText = function (Text, ...Arguments) {
                const Replacement =
                    IsThemedBoardLetterDraw(this, Text) &&
                    IsDarkThemedBoardContext(this)
                        ? GetDarkLetterReplacement(this.strokeStyle)
                        : null;

                if (Replacement) {
                    const Previous = this.strokeStyle;
                    this.strokeStyle = Replacement;
                    try {
                        return NativeBoardStrokeText.call(
                            this,
                            Text,
                            ...Arguments
                        );
                    } finally {
                        this.strokeStyle = Previous;
                    }
                }

                return NativeBoardStrokeText.call(this, Text, ...Arguments);
            };
        }

        /*
            A used node is the one remaining source collision in Dark mode:
            NYT paints its fill with native active salmon but keeps its outline
            native black. The truth table wants BOTH to be Tertiary. Detect
            precisely that paint pair at stroke time and promote only that
            outline to the active source anchor. This also leaves the mobile
            Current/Last node alone: it already uses active outline + black fill,
            which maps naturally to Tertiary outline + derived white fill.
        */
        if (typeof NativeBoardStroke === "function") {
            Prototype.stroke = function (...Arguments) {
                if (
                    IsDarkThemedBoardContext(this) &&
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
source = replace_between(
    source,
    board_hook_start,
    board_hook_end,
    board_hook_new,
    "board semantic source hooks",
)

# Apply Primary/Secondary/Tertiary semantics on every theme application.
apply_theme_start = '''    function ApplyTheme() {'''
apply_theme_end = '''    function SetActiveTheme(ThemeId) {'''
apply_theme_new = '''    function ApplyTheme() {
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
        const ApplyNative = true;

        const Variables = {
            "--lb-cubed-lb-primary": Palette.LbBackground,
            "--lb-cubed-lb-secondary": Palette.LbBoard,
            "--lb-cubed-lb-tertiary": Palette.LbActive,
            "--lb-cubed-lb-bg": Palette.LbBackground,
            "--lb-cubed-lb-board": Palette.LbBoard,
            "--lb-cubed-lb-fg": Palette.LbForeground,
            "--lb-cubed-lb-active": Palette.LbActive,
            "--lb-cubed-lb-board-outline": LbSemantics.BoardOutline,
            "--lb-cubed-success-toast-bg": LbSemantics.SuccessToastBackground,
            "--lb-cubed-success-toast-fg": LbSemantics.SuccessToastForeground,
            "--lb-cubed-error-toast-bg": LbSemantics.ErrorToastBackground,
            "--lb-cubed-error-toast-fg": LbSemantics.ErrorToastForeground,
            /* Compatibility aliases used by preview/toast code. */
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

        Root.classList.toggle("lb-cubed-native-theme", ApplyNative);
        Root.classList.toggle("lb-cubed-board-themed", ApplyNative);
        Root.classList.toggle("lb-cubed-theme-dark", LbSemantics.IsDark);
        Root.dataset.lbcTheme = Theme.Id || DefaultThemeId;
        Root.dataset.lbcThemeMode = LbSemantics.IsDark ? "dark" : "light";

        ApplyBoardThemeMatrix(Palette);
        QueueBoardThemeRendererRefresh();
    }

'''
source = replace_between(
    source,
    apply_theme_start,
    apply_theme_end,
    apply_theme_new,
    "ApplyTheme semantic model",
)

# New custom themes are always three independent LB colors. LBC linkage still
# inherits from the source theme.
custom_create_start = '''    function CreateCustomThemeFromActive(Name = "Custom Theme") {'''
custom_create_end = '''    function RenameActiveCustomTheme(Name) {'''
custom_create_new = '''    function CreateCustomThemeFromActive(Name = "Custom Theme") {
        const Base = GetActiveThemeDefinition();
        const Id = `custom-${CreateCloudOpaqueId("theme")}`;
        const Now = new Date().toISOString();
        const BoardMatchesBackground = false;
        const LbcBackgroundMatchesLbBackground = Boolean(
            Base.LbcBackgroundMatchesLbBackground
        );
        const LbcTextMatchesLbForeground = Boolean(
            Base.LbcTextMatchesLbForeground
        );
        const Palette = NormalizeThemePalette(
            Base.Palette,
            null,
            false
        );

        Palette.LbForeground = GetThemeContrastPole(Palette.LbBackground);
        if (LbcBackgroundMatchesLbBackground) {
            Palette.LbcBackground = Palette.LbBackground;
        }
        if (LbcTextMatchesLbForeground) {
            Palette.LbcText = Palette.LbForeground;
        }

        ThemeState.CustomThemes[Id] = {
            Id,
            Name: String(Name || "Custom Theme").trim() || "Custom Theme",
            Palette,
            BoardMatchesBackground,
            LbcBackgroundMatchesLbBackground,
            LbcTextMatchesLbForeground,
            Deleted: false,
            UpdatedAt: Now
        };
        ThemeState.ActiveTheme = { Id, UpdatedAt: Now };
        SaveThemeState();
        ApplyTheme();
        return Id;
    }

'''
source = replace_between(
    source,
    custom_create_start,
    custom_create_end,
    custom_create_new,
    "custom-theme creation",
)

update_palette_start = '''    function UpdateActiveCustomThemePalette(Key, Value, Persist = true) {'''
update_palette_end = '''    function UpdateActiveCustomThemeBoardMatch(Value) {'''
update_palette_new = '''    function UpdateActiveCustomThemePalette(Key, Value, Persist = true) {
        const Theme = GetActiveCustomThemeRecord();
        if (!Theme || !Object.prototype.hasOwnProperty.call(Theme.Palette, Key)) {
            return false;
        }

        Theme.Palette[Key] = NormalizeThemeColor(
            Value,
            Theme.Palette[Key]
        );

        if (Key === "LbBackground") {
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

        if (Persist) {
            Theme.UpdatedAt = new Date().toISOString();
            SaveThemeState();
        }

        ApplyTheme();
        return true;
    }

'''
source = replace_between(
    source,
    update_palette_start,
    update_palette_end,
    update_palette_new,
    "custom palette updates",
)

# LBC's linked Text now follows the derived Letter Boxed Text Input color.
old_lbc_text_match = '''        Theme.LbcTextMatchesLbForeground = Boolean(Value);
        if (Theme.LbcTextMatchesLbForeground) {
            Theme.Palette.LbcText = Theme.Palette.LbForeground;
        }
'''
new_lbc_text_match = '''        Theme.LbcTextMatchesLbForeground = Boolean(Value);
        Theme.Palette.LbForeground = GetThemeContrastPole(
            Theme.Palette.LbBackground
        );
        if (Theme.LbcTextMatchesLbForeground) {
            Theme.Palette.LbcText = Theme.Palette.LbForeground;
        }
'''
source = replace_once(
    source,
    old_lbc_text_match,
    new_lbc_text_match,
    "LBC linked text derivation",
)

# Remove the obsolete Board/Same-as-Background control from the editable UI.
board_row_start = '''    function CreateThemeBoardColorRow(Section) {'''
board_row_end = '''    function CreateThemeLinkedColorRow('''
source = replace_between(
    source,
    board_row_start,
    board_row_end,
    '''    function CreateThemeLinkedColorRow(''',
    "obsolete board-link control",
)

source = replace_once(
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
    "three-color LB theme controls",
)
source = source.replace(
    '"Same as Letter Boxed Foreground"',
    '"Same as Letter Boxed Text"'
)
source = replace_once(
    source,
    '''        Note.textContent =
            "Muted text and secondary accents are derived automatically. " +
            "Success/error indicators remain fixed green/red.";''',
    '''        Note.textContent =
            "Letter Boxed Text, outlines, state colors and toast colors are derived " +
            "from Primary / Secondary / Tertiary using light/dark semantics. " +
            "LBC muted text and secondary accents are also derived automatically.";''',
    "theme settings explanatory note",
)

# Restore the original Text Input semantics. beta.20 temporarily mapped it to
# the active color, but NYT's truth table uses black/white text derived from the
# page background; only board state elements use Tertiary.
active_entry_start = '''            /* Current word entry belongs to the same active semantic lane as the GB path. */'''
active_entry_end = '''            html.lb-cubed-native-theme .lb-text-field-underline {'''
source = replace_between(
    source,
    active_entry_start,
    active_entry_end,
    '''            html.lb-cubed-native-theme .lb-text-field-underline {''',
    "text-input active-color regression",
)

# Split success and error toast semantics instead of painting every transient
# message with Tertiary/Board.
toast_start = '''            /*
                Theme transient validation/praise as one semantic LB surface:'''
toast_end = '''            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-par.no-words {'''
toast_new = '''            /*
                Match NYT's two distinct toast surfaces. Success is invariant:
                black on white. Error is white on black in a light theme; in a
                dark theme it intentionally reverses to Text Input on Primary
                (white background / dark-page foreground in the stock preset).
            */
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
source = replace_between(
    source,
    toast_start,
    toast_end,
    toast_new,
    "toast truth table",
)

# The win modal is intentionally white even in NYT dark mode. Do not let the
# generic themed-button rule paint its close button black-on-black.
modal_anchor = '''            html.lb-cubed-native-theme .lb-word-list,
            html.lb-cubed-native-theme .lb-word-list *,'''
modal_override = '''            html.lb-cubed-theme-dark button[data-testid="modal-close"] {
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
source = replace_once(
    source,
    modal_anchor,
    modal_override + modal_anchor,
    "dark win-modal close button",
)

# The hint-empty sentence is normal LBC foreground, not muted text.
source = replace_once(
    source,
    '''            #${PanelId} .lb-cubed-twofer-solution-text,
            #${PanelId} .lb-cubed-length-value,''',
    '''            #${PanelId} .lb-cubed-twofer-solution-text,
            #${PanelId} .lb-cubed-potential-word-empty,
            #${PanelId} .lb-cubed-length-value,''',
    "hint empty foreground",
)
# Give normal Twofer arrows a semantic muted color so an NYT-solution wrapper
# never has to color them specially.
source = replace_once(
    source,
    '''            #${PanelId} .lb-cubed-twofer-disclaimer,
            #${PanelId} .lb-cubed-twofer-group-title,''',
    '''            #${PanelId} .lb-cubed-twofer-disclaimer,
            #${PanelId} .lb-cubed-twofer-arrow,
            #${PanelId} .lb-cubed-twofer-group-title,''',
    "twofer arrow semantic color",
)

# Base NYT-solution styling decorates only the wrapper and heading. The row and
# word cells remain ordinary Twofer UI so unrevealed words stay redacted.
nyt_base_start = '''            /*
                NYT's published solution.'''
nyt_base_end = '''            /*
                ================================================================
                WORDS BY LENGTH'''
nyt_base_new = '''            /*
                NYT's published solution. Only the outer card and its heading
                receive solution-specific coloring; the actual Twofer row keeps
                the exact same revealed/redacted styling as every other pair.
            */
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
source = replace_between(
    source,
    nyt_base_start,
    nyt_base_end,
    nyt_base_new,
    "base NYT solution scope",
)

nyt_theme_start = '''            #${PanelId} .lb-cubed-nyt-solution,
            #${HistoryOverlayId} .lb-cubed-history-custom-word {'''
nyt_theme_end = '''            #${PanelId} .lb-cubed-nyt-solution-label {
                display: inline-flex;'''
nyt_theme_new = '''            #${PanelId} .lb-cubed-nyt-solution {
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

            #${PanelId} .lb-cubed-nyt-solution-label {
                display: inline-flex;'''
source = replace_between(
    source,
    nyt_theme_start,
    nyt_theme_end,
    nyt_theme_new,
    "themed NYT solution scope",
)

# WebKit text fill can otherwise leak from an ancestor and visually reveal a
# redacted word even though its normal color is correctly redacted.
source = replace_once(
    source,
    '''                color: var(--lb-cubed-redacted) !important;
                border-color: var(--lb-cubed-redacted) !important;
                text-shadow: none !important;''',
    '''                color: var(--lb-cubed-redacted) !important;
                -webkit-text-fill-color: var(--lb-cubed-redacted) !important;
                border-color: var(--lb-cubed-redacted) !important;
                text-shadow: none !important;''',
    "redacted text-fill protection",
)

# Update board comments so future work does not regress back to the old
# Foreground/Board/Active mental model.
source = source.replace(
    '''                The SVG affine filter above the bitmap maps source black ->
                Foreground, source white -> Board, and source active coral ->
                Foreground (active). Because the bitmap itself is never mutated,''',
    '''                The SVG affine filter above the bitmap maps source black ->
                derived Text/Outline, source white -> Secondary, and source
                active coral -> Tertiary. Because the bitmap itself is never mutated,'''
)

SOURCE.write_text(source, encoding="utf-8")

# Keep the static acceptance test focused on durable semantics rather than the
# discarded beta.20 implementation details.
TESTS.write_text(r'''const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'LetterBoxedCubed.user.js'), 'utf8');
const preview = fs.readFileSync(path.join(root, 'tools', 'preview_runtime.js'), 'utf8');

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(source.includes('// @version      1.13.1-beta.21'), 'beta.21 version missing');
assert(source.includes('const ExportFormatVersion = 4;'), 'backup schema v4 missing');
assert(source.includes('const ThemeStateVersion = 2;'), 'ThemeState v2 compatibility missing');
assert(source.includes('MergeThemeStates'), 'theme merge missing');
assert(source.includes('Name: "NYT Light"'), 'NYT Light preset missing');
assert(source.includes('Name: "NYT Dark"'), 'NYT Dark preset missing');
assert(source.includes('LbBackground: "#E3A5A3"'), 'NYT Light primary calibration missing');
assert(source.includes('LbBoard: "#FFFFFF"'), 'NYT Light secondary calibration missing');
assert(source.includes('LbBackground: "#121212"'), 'NYT Dark primary calibration missing');
assert(source.includes('LbBoard: "#121212"'), 'NYT Dark secondary calibration missing');
assert(source.includes('LbActive: "#DA5D57"'), 'NYT Dark tertiary calibration missing');
assert(source.includes('GetLbThemeSemantics'), 'LB semantic derivation missing');
assert(source.includes('Primary (background)'), 'Primary theme control missing');
assert(source.includes('Secondary (board)'), 'Secondary theme control missing');
assert(source.includes('Tertiary (active / used)'), 'Tertiary theme control missing');
assert(!source.includes('CreateThemeBoardColorRow('), 'obsolete Board/Same-as-Background UI remains');
assert(source.includes('Same as Letter Boxed Background'), 'LBC background linkage missing');
assert(source.includes('Same as Letter Boxed Text'), 'LBC text linkage missing');
assert(source.includes('const ApplyNative = true;'), 'all themes do not share semantic compositor');
assert(source.includes('lb-cubed-theme-dark'), 'derived dark theme class missing');
assert(source.includes('--lb-cubed-success-toast-bg'), 'success toast semantic variable missing');
assert(source.includes('--lb-cubed-error-toast-bg'), 'error toast semantic variable missing');
assert(source.includes('ErrorToastBackground: IsDark ? TextInput : "#000000"'), 'dark/light error toast rule missing');
assert(source.includes('ErrorToastForeground: IsDark ? Palette.LbBackground : "#FFFFFF"'), 'dark error foreground rule missing');

assert(source.includes('BuildBoardThemeAffineMatrix'), 'semantic affine board transform missing');
assert(source.includes('feColorMatrix'), 'SVG board color matrix missing');
assert(source.includes('NativeBoardActiveSourceColor = "#E8A9A0"'), 'native tertiary source anchor missing');
assert(source.includes('filter: url(#lb-cubed-board-theme-filter)'), 'board filter CSS missing');
assert(source.includes('IsNativeBoardWhite'), 'unused-letter source detector missing');
assert(source.includes('IsNativeBoardBlack'), 'active/used-letter source detector missing');
assert(source.includes('IsNativeBoardActive'), 'used-node source detector missing');
assert(source.includes('NativeBoardStroke = Prototype.stroke'), 'used-node outline hook missing');
assert(source.includes('GetDarkLetterReplacement'), 'dark board-letter state mapping missing');
assert(source.includes('this.strokeStyle = NativeBoardActiveSourceColor'), 'dark used-node outline promotion missing');
assert(source.includes('QueueBoardThemeRendererRefresh'), 'mid-puzzle board refresh missing');
assert(!source.includes('invert(1) hue-rotate(180deg)'), 'legacy inversion filter remains');
assert(!source.includes('RepairDarkBoardCanvas'), 'legacy bitmap repair remains');

assert(source.includes('.lb-cubed-potential-word-empty,'), 'Hints empty text is not semantic foreground');
assert(source.includes('font-size: calc(1em + 5px)'), 'NYT solution star +5px sizing missing');
assert(source.includes('Lightness * 0.55'), 'NYT solution hue-preserving shade missing');
assert(!source.includes('#${PanelId} .lb-cubed-nyt-solution * {'), 'NYT solution still recolors/spoils word descendants');
assert(source.includes('-webkit-text-fill-color: var(--lb-cubed-redacted)'), 'redaction text-fill protection missing');
assert(source.includes('button[data-testid="modal-close"]'), 'dark win-modal close-button special case missing');

assert(source.includes('ApplyCompactNumberInputWidth'), 'compact number input sizing missing');
assert(source.includes('DigitCount + 1}ch + 22px'), 'number input breathing room missing');
assert(source.includes('.lb-cubed-settings-panel,'), 'settings scrollbar root styling missing');
assert(source.includes('var(--lb-cubed-lbc-text, #301818)'), 'semantic LBC scrollbar thumb missing');
assert(source.includes('Google Drive bridge returned HTML instead of JSON'), 'Drive HTML response guard missing');
assert(source.includes('no HTML was imported into LBC data'), 'Drive HTML failure explanation missing');
assert(source.includes('lb-message-box success-message lb-cubed-valid-feedback-proxy'), 'valid-word proxy missing');
assert(source.includes('ValidFeedbackProxyMinimumVisibleMs = 600'), 'valid toast minimum lifetime missing');
assert(source.includes('Source?.textContent || ActiveValidFeedbackText'), 'toast capture lifecycle missing');
assert(source.includes('Proxy.textContent = MessageText'), 'toast captured text missing');

assert(source.includes('InternalPanelLayoutBreakpoints = ['), 'responsive breakpoints missing');
for (const breakpoint of ['340', '390', '520', '650', '860', '1180']) {
  assert(source.includes(breakpoint), `responsive breakpoint missing: ${breakpoint}`);
}
assert(source.includes('DefaultInternalPanelLayoutHysteresisPx = 30'), 'layout hysteresis default missing');
for (let stage = 0; stage <= 6; stage++) {
  assert(source.includes(`lb-cubed-layout-stage-${stage}`), `responsive stage missing: ${stage}`);
}
assert(source.includes('Custom 12-column'), 'custom layout option missing');
assert(source.includes('Start from current automatic layout'), 'automatic-to-custom snapshot missing');
assert(!source.includes('@container lbc'), 'state-less container-query cascade should not return');

for (const label of [
  'Copy Geometry Snapshot',
  'Start Transient Element Trace',
  'Stop + Copy Trace',
  'Copy Board Source Snapshot',
  'Start Board Canvas Trace',
  'Stop + Copy Board Trace',
  'Copy Bootstrap Trace',
  'Copy Full Debug Bundle'
]) {
  assert(preview.includes(label), `preview diagnostic missing: ${label}`);
}
assert(preview.includes('GetPreviewDebugBundle'), 'full debug bundle function missing');
assert(preview.includes('SourcePixelHistogram'), 'board source pixel histogram missing');
assert(preview.includes('TextDraws: structuredClone(PreviewBoardCanvasTrace)'), 'board trace missing from debug bundle');

console.log('PASS: beta.21 theme truth-table static checks');
''', encoding="utf-8")
