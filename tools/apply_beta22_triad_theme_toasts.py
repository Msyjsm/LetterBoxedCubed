from pathlib import Path

PATH = Path("LetterBoxedCubed.user.js")
source = PATH.read_text(encoding="utf-8")


def require_replace(text, old, new, label, count=1):
    found = text.count(old)
    if found != count:
        raise RuntimeError(f"{label}: expected {count} match(es), found {found}")
    return text.replace(old, new, count)


def replace_function(text, start_name, next_name, replacement, label):
    start = text.find(f"    function {start_name}")
    if start < 0:
        raise RuntimeError(f"{label}: start function {start_name} not found")
    end = text.find(f"    function {next_name}", start + 1)
    if end < 0:
        raise RuntimeError(f"{label}: next function {next_name} not found")
    return text[:start] + replacement.rstrip() + "\n\n" + text[end:]


source = require_replace(
    source,
    "// @version      1.13.1-beta.21",
    "// @version      1.13.1-beta.22",
    "version",
)

source = require_replace(
    source,
    "    const ValidFeedbackProxyMinimumVisibleMs = 600;\n",
    "    const ValidFeedbackProxyMinimumVisibleMs = 600;\n    const ToastFadeMs = 160;\n",
    "toast fade constant",
)

source = require_replace(
    source,
    "    let ValidFeedbackProxyShownAt = 0;\n",
    "    let ValidFeedbackProxyShownAt = 0;\n    let ErrorFeedbackPlacementTimer = null;\n    let ErrorFeedbackRemovalTimer = null;\n    let RenderedErrorFeedbackText = \"\";\n",
    "error toast state",
)

source = require_replace(
    source,
    "        InstallBoardTextSourceHook();\n        ApplyTheme();",
    "        ApplyTheme();",
    "defer board hook until themed",
)

source = require_replace(
    source,
    '''            /* Use the same semantic compositor as every other theme. */
            ApplyNative: true,''',
    '''            /* Native NYT Light is the zero-override baseline. */
            ApplyNative: false,''',
    "NYT Light native opt-out",
)

source = require_replace(
    source,
    '''                LbBoard: "#FFFFFF",
                LbForeground: "#000000",
                LbActive: NativeBoardActiveSourceColor,''',
    '''                /* Core triad: Background / Foreground / Highlight. */
                LbBoard: "#FFFFFF",
                LbForeground: "#000000",
                LbActive: "#FFFFFF",''',
    "NYT Light triad",
)

new_semantics = r'''    function GetLbThemeSemantics(Palette) {
        const IsDark = GetThemeRelativeLuminance(Palette.LbBackground) < 0.38;
        const Background = Palette.LbBackground;
        const Foreground = Palette.LbForeground;
        const Highlight = Palette.LbActive;

        /*
            The user owns exactly three Letter Boxed colors. Background alone
            chooses the Light/Dark semantic column; no target color is invented
            here. Every native state is mapped back to Background, Foreground,
            or Highlight.
        */
        return {
            IsDark,
            Background,
            Foreground,
            Highlight,
            TextInput: Foreground,
            BoardBackground: IsDark ? Background : Highlight,
            BoardOutline: Foreground,
            UnusedLetter: IsDark ? Foreground : Highlight,
            UnusedNodeOutline: Foreground,
            UnusedNodeBackground: IsDark ? Background : Highlight,
            ActiveLetter: IsDark ? Highlight : Foreground,
            ActiveNodeOutline: IsDark ? Highlight : Background,
            ActiveNodeBackground: IsDark ? Background : Highlight,
            UsedLetter: IsDark ? Highlight : Foreground,
            UsedNodeOutline: IsDark ? Highlight : Foreground,
            UsedNodeBackground: IsDark ? Highlight : Background,
            Connector: IsDark ? Highlight : Background,
            CurrentNodeOutline: IsDark ? Highlight : Background,
            CurrentNodeBackground: Foreground,
            SuccessToastForeground: IsDark ? Background : Foreground,
            SuccessToastBackground: IsDark ? Foreground : Highlight,
            ErrorToastForeground: IsDark ? Background : Highlight,
            ErrorToastBackground: Foreground
        };
    }'''
source = replace_function(
    source,
    "GetLbThemeSemantics(Palette)",
    "GetDerivedLbcMutedText(Palette)",
    new_semantics,
    "triad LB semantics",
)

new_apply_matrix = r'''    function ApplyBoardThemeMatrix(Palette, LbSemantics) {
        const Matrix = EnsureBoardThemeFilter();
        if (!Matrix) {
            return;
        }

        /*
            Native Light's source palette is black / white / coral. In a Light
            semantic theme those become Foreground / Highlight / Background.
            In a Dark semantic theme they become Foreground / Background /
            Highlight. The Dark-only canvas shim disambiguates the source-paint
            collisions for letter glyphs and used-node outlines.
        */
        const Rows = BuildBoardThemeAffineMatrix(
            LbSemantics.BoardBackground,
            LbSemantics.Foreground,
            LbSemantics.Connector
        );
        Matrix.setAttribute(
            "values",
            Rows.flat().map(Value => {
                const Rounded = Math.abs(Value) < 0.0000001 ? 0 : Value;
                return Number(Rounded.toFixed(7)).toString();
            }).join(" ")
        );
    }'''
source = replace_function(
    source,
    "ApplyBoardThemeMatrix(Palette)",
    "IsLetterBoxedBoardCanvas(Canvas)",
    new_apply_matrix,
    "board matrix triad mapping",
)

# Add an uninstall path so the built-in NYT Light preset truly returns to native canvas behavior.
insert_after_hook = '''        BoardTextSourceHookInstalled = true;\n    }\n\n'''
uninstall_hook = r'''        BoardTextSourceHookInstalled = true;
    }

    function UninstallBoardTextSourceHook() {
        if (!BoardTextSourceHookInstalled) {
            return;
        }

        const Prototype = PageWindow.CanvasRenderingContext2D?.prototype;
        if (Prototype) {
            if (typeof NativeBoardFillText === "function") {
                Prototype.fillText = NativeBoardFillText;
            }
            if (typeof NativeBoardStrokeText === "function") {
                Prototype.strokeText = NativeBoardStrokeText;
            }
            if (typeof NativeBoardStroke === "function") {
                Prototype.stroke = NativeBoardStroke;
            }
        }

        BoardTextSourceHookInstalled = false;
        NativeBoardFillText = null;
        NativeBoardStrokeText = null;
        NativeBoardStroke = null;
    }

'''
source = require_replace(
    source,
    insert_after_hook,
    uninstall_hook,
    "board hook uninstall insertion",
)

new_queue_refresh = r'''    function QueueBoardThemeRendererRefresh(Force = false) {
        if (
            (!Force && !document.documentElement?.classList.contains(
                "lb-cubed-board-themed"
            )) ||
            !document.querySelector(
                ".lb-game-container .lb-square-container canvas"
            )
        ) {
            return;
        }

        /*
            NYT redraws the board on resize. The forced path is used only when
            leaving a themed board for native NYT Light so source paints altered
            by the Dark shim are repainted once with the restored native methods.
        */
        requestAnimationFrame(() => {
            window.dispatchEvent(new Event("resize"));
            setTimeout(
                () => window.dispatchEvent(new Event("resize")),
                80
            );
        });
    }'''
source = replace_function(
    source,
    "QueueBoardThemeRendererRefresh()",
    "ApplyTheme()",
    new_queue_refresh,
    "board refresh force path",
)

new_apply_theme = r'''    function ApplyTheme() {
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
            "--lb-cubed-lb-primary": LbSemantics.Background,
            "--lb-cubed-lb-secondary": LbSemantics.Foreground,
            "--lb-cubed-lb-tertiary": LbSemantics.Highlight,
            "--lb-cubed-lb-bg": LbSemantics.Background,
            "--lb-cubed-lb-board": LbSemantics.BoardBackground,
            "--lb-cubed-lb-fg": LbSemantics.Foreground,
            "--lb-cubed-lb-highlight": LbSemantics.Highlight,
            "--lb-cubed-lb-active": LbSemantics.Connector,
            "--lb-cubed-success-toast-bg": LbSemantics.SuccessToastBackground,
            "--lb-cubed-success-toast-fg": LbSemantics.SuccessToastForeground,
            "--lb-cubed-error-toast-bg": LbSemantics.ErrorToastBackground,
            "--lb-cubed-error-toast-fg": LbSemantics.ErrorToastForeground,
            "--lb-cubed-lb-page-bg": LbSemantics.Background,
            "--lb-cubed-lb-text": LbSemantics.Foreground,
            "--lb-cubed-lb-surface": LbSemantics.Background,
            "--lb-cubed-lb-border": LbSemantics.Foreground,
            "--lb-cubed-lb-accent": LbSemantics.Highlight,
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

        const WasBoardThemed = Root.classList.contains("lb-cubed-board-themed");
        const ApplyNative = Theme.ApplyNative !== false;

        Root.classList.toggle("lb-cubed-native-theme", ApplyNative);
        Root.classList.toggle("lb-cubed-board-themed", ApplyNative);
        Root.classList.toggle("lb-cubed-theme-dark", LbSemantics.IsDark);
        Root.dataset.lbcTheme = Theme.Id || DefaultThemeId;
        Root.dataset.lbcThemeMode = LbSemantics.IsDark ? "dark" : "light";

        if (ApplyNative) {
            InstallBoardTextSourceHook();
            ApplyBoardThemeMatrix(Palette, LbSemantics);
            QueueBoardThemeRendererRefresh();
        } else {
            UninstallBoardTextSourceHook();
            if (WasBoardThemed) {
                QueueBoardThemeRendererRefresh(true);
            }
        }
    }'''
source = replace_function(
    source,
    "ApplyTheme()",
    "SetActiveTheme(ThemeId)",
    new_apply_theme,
    "ApplyTheme triad + native Light opt-out",
)

new_create_custom = r'''    function CreateCustomThemeFromActive(Name = "Custom Theme") {
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
        const Palette = NormalizeThemePalette(Base.Palette, null, false);

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
    }'''
source = replace_function(
    source,
    "CreateCustomThemeFromActive(Name = \"Custom Theme\")",
    "RenameActiveCustomTheme(Name)",
    new_create_custom,
    "custom theme preserves triad",
)

new_update_palette = r'''    function UpdateActiveCustomThemePalette(Key, Value, Persist = true) {
        const Theme = GetActiveCustomThemeRecord();
        if (!Theme || !Object.prototype.hasOwnProperty.call(Theme.Palette, Key)) {
            return false;
        }

        Theme.Palette[Key] = NormalizeThemeColor(Value, Theme.Palette[Key]);

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

        if (Persist) {
            Theme.UpdatedAt = new Date().toISOString();
            SaveThemeState();
        }
        ApplyTheme();
        return true;
    }'''
source = replace_function(
    source,
    "UpdateActiveCustomThemePalette(Key, Value, Persist = true)",
    "UpdateActiveCustomThemeBoardMatch(Value)",
    new_update_palette,
    "custom triad updates",
)

new_lbc_text_match = r'''    function UpdateActiveCustomThemeLbcTextMatch(Value) {
        const Theme = GetActiveCustomThemeRecord();
        if (!Theme) {
            return false;
        }

        Theme.LbcTextMatchesLbForeground = Boolean(Value);
        if (Theme.LbcTextMatchesLbForeground) {
            Theme.Palette.LbcText = Theme.Palette.LbForeground;
        }
        Theme.UpdatedAt = new Date().toISOString();
        SaveThemeState();
        ApplyTheme();
        return true;
    }'''
source = replace_function(
    source,
    "UpdateActiveCustomThemeLbcTextMatch(Value)",
    "CreateEmptyGuiState()",
    new_lbc_text_match,
    "LBC text link preserves foreground",
)

source = require_replace(
    source,
    '''                CreateThemeColorRow("Primary (background)", "LbBackground"),
                CreateThemeColorRow("Secondary (board)", "LbBoard"),
                CreateThemeColorRow("Tertiary (active / used)", "LbActive")''',
    '''                CreateThemeColorRow("Background", "LbBackground"),
                CreateThemeColorRow("Foreground", "LbForeground"),
                CreateThemeColorRow("Highlight", "LbActive")''',
    "theme UI triad labels",
)

source = require_replace(
    source,
    '''            "Letter Boxed text, outlines, node states, connectors and toast colors " +
            "are derived from Primary / Secondary / Tertiary. LBC muted text and " +
            "secondary accents are derived automatically.";''',
    '''            "Background brightness selects the Light or Dark mapping column. " +
            "Every Letter Boxed board state and toast then uses only Background, " +
            "Foreground, or Highlight; no extra native colors are synthesized.";''',
    "theme UI mapping note",
)

source = require_replace(
    source,
    '''                ? "NYT mobile dark-mode colors adapted to the web game. Duplicate this theme to tune individual colors."
                : "Prebuilt themes are read-only. Use New from current to make an editable copy.";''',
    '''                ? "NYT mobile dark-mode colors adapted to the web game. Duplicate this theme to tune Background, Foreground, and Highlight."
                : "Native NYT Light is left unthemed. Duplicate it to create a custom theme with the same initial appearance.";''',
    "prebuilt theme note",
)

# Shared fade helper + native error proxy. Insert immediately before native-success discovery.
error_proxy_block = r'''    function FadeOutToastProxy(Element) {
        if (!Element) {
            return;
        }
        Element.classList.remove("lb-cubed-toast-visible");
        setTimeout(() => {
            if (!Element.classList.contains("lb-cubed-toast-visible")) {
                Element.remove();
            }
        }, ToastFadeMs);
    }

    function GetNativeErrorWordFeedbackSource() {
        const Wrapper = document.querySelector(
            ".lb-game-container .lb-word-container > .lb-text-field-wrapper"
        );
        if (!Wrapper) {
            return null;
        }

        const Candidates = [
            ...Wrapper.querySelectorAll(":scope > .lb-message-box"),
            ...Wrapper.querySelectorAll(":scope > .lb-par:not(.no-words)")
        ];

        return Candidates.find(Element =>
            !Element.classList.contains("lb-cubed-error-feedback-proxy") &&
            String(Element.textContent || "").trim()
        ) || null;
    }

    function ClearErrorWordFeedbackProxy() {
        clearTimeout(ErrorFeedbackRemovalTimer);
        ErrorFeedbackRemovalTimer = null;
        RenderedErrorFeedbackText = "";

        document.querySelectorAll(".lb-cubed-error-feedback-source")
            .forEach(Element => Element.classList.remove(
                "lb-cubed-error-feedback-source"
            ));

        const Proxy = document.querySelector(
            ".lb-cubed-error-feedback-proxy"
        );
        if (!Proxy) {
            return;
        }

        Proxy.classList.remove("lb-cubed-toast-visible");
        ErrorFeedbackRemovalTimer = setTimeout(() => {
            ErrorFeedbackRemovalTimer = null;
            if (!Proxy.classList.contains("lb-cubed-toast-visible")) {
                Proxy.remove();
            }
        }, ToastFadeMs);
    }

    function UpdateErrorWordFeedbackPlacement() {
        ErrorFeedbackPlacementTimer = null;

        const GameContainer = document.querySelector(".lb-game-container");
        const WordContainer = GameContainer?.querySelector(
            ":scope > .lb-word-container"
        );
        const TextFieldWrapper = WordContainer?.querySelector(
            ":scope > .lb-text-field-wrapper"
        );
        const ListContainer = WordContainer?.querySelector(
            ":scope > .lb-list-container"
        );
        const SquareContainer = GameContainer?.querySelector(
            ":scope > .lb-square-container"
        );
        const Source = GetNativeErrorWordFeedbackSource();
        const MessageText = String(Source?.textContent || "").trim();

        if (
            !GameContainer ||
            !WordContainer ||
            !TextFieldWrapper ||
            !ListContainer ||
            !SquareContainer ||
            !Source ||
            !MessageText
        ) {
            ClearErrorWordFeedbackProxy();
            return;
        }

        clearTimeout(ErrorFeedbackRemovalTimer);
        ErrorFeedbackRemovalTimer = null;
        Source.classList.add("lb-cubed-error-feedback-source");

        let Proxy = GameContainer.querySelector(
            ":scope > .lb-cubed-error-feedback-proxy"
        );
        if (!Proxy) {
            Proxy = document.createElement("div");
            Proxy.className =
                "lb-message-box error-message lb-cubed-toast-proxy lb-cubed-error-feedback-proxy";
            GameContainer.appendChild(Proxy);
        }

        if (RenderedErrorFeedbackText !== MessageText) {
            Proxy.textContent = MessageText;
            RenderedErrorFeedbackText = MessageText;
        }

        PositionValidWordFeedbackProxy(
            Proxy,
            GameContainer,
            WordContainer,
            TextFieldWrapper,
            ListContainer,
            SquareContainer
        );

        requestAnimationFrame(() => {
            if (Proxy.isConnected) {
                Proxy.classList.add("lb-cubed-toast-visible");
            }
        });
    }

    function QueueErrorWordFeedbackPlacement() {
        clearTimeout(ErrorFeedbackPlacementTimer);
        ErrorFeedbackPlacementTimer = setTimeout(
            UpdateErrorWordFeedbackPlacement,
            0
        );
    }

'''
marker = "    function GetNativeValidWordFeedbackSource() {"
if marker not in source:
    raise RuntimeError("error proxy insertion marker missing")
source = source.replace(marker, error_proxy_block + marker, 1)

source = require_replace(
    source,
    '''                NormalizeWordAreaFeedbackLayout();
                ScanGameState();''',
    '''                NormalizeWordAreaFeedbackLayout();
                QueueErrorWordFeedbackPlacement();
                ScanGameState();''',
    "game observer error toast sync",
)

source = require_replace(
    source,
    '''        QueueValidWordFeedbackPlacement();
    }

    function CountRenderedHistoryLines''',
    '''        QueueValidWordFeedbackPlacement();
        QueueErrorWordFeedbackPlacement();
    }

    function CountRenderedHistoryLines''',
    "normalize layout error toast sync",
)

# Normal success clear now fades the complete proxy rather than popping it out.
source = require_replace(
    source,
    '''        document.querySelectorAll(".lb-cubed-valid-feedback-proxy")
            .forEach(Element => Element.remove());''',
    '''        document.querySelectorAll(".lb-cubed-valid-feedback-proxy")
            .forEach(FadeOutToastProxy);''',
    "success clear fade",
    count=1,
)

source = require_replace(
    source,
    '''            Proxy.className =
                "lb-message-box success-message lb-cubed-valid-feedback-proxy";''',
    '''            Proxy.className =
                "lb-message-box success-message lb-cubed-toast-proxy lb-cubed-valid-feedback-proxy";''',
    "success proxy shared toast class",
)

source = require_replace(
    source,
    '''            GameContainer.appendChild(Proxy);
            RenderedValidFeedbackKey = FeedbackKey;
            ValidFeedbackProxyShownAt = performance.now();''',
    '''            GameContainer.appendChild(Proxy);
            requestAnimationFrame(() => {
                if (Proxy.isConnected) {
                    Proxy.classList.add("lb-cubed-toast-visible");
                }
            });
            RenderedValidFeedbackKey = FeedbackKey;
            ValidFeedbackProxyShownAt = performance.now();''',
    "success fade in",
)

# Leave immediate replacement removal for a brand-new success lifecycle; it prevents
# an old fading proxy from being mistaken for the new lifecycle's reusable node.

old_toast_css = r'''            .lb-cubed-valid-feedback-proxy {
                position: absolute !important;
                right: auto !important;
                bottom: auto !important;
                margin: 0 !important;
                transform: none !important;
                visibility: visible !important;
                display: block !important;
                opacity: 1 !important;
                clip-path: none !important;
                filter: none !important;
                z-index: 60 !important;
                pointer-events: none !important;
                animation: none !important;
                transition: none !important;
            }

            /* Success = black on white. Error = white on black in a light
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
new_toast_css = r'''            .lb-cubed-toast-proxy {
                position: absolute !important;
                right: auto !important;
                bottom: auto !important;
                margin: 0 !important;
                transform: none !important;
                visibility: visible !important;
                display: block !important;
                opacity: 0 !important;
                clip-path: none !important;
                filter: none !important;
                z-index: 60 !important;
                pointer-events: none !important;
                animation: none !important;
                transition: opacity ${ToastFadeMs}ms ease !important;
                text-shadow: none !important;
            }

            .lb-cubed-toast-proxy.lb-cubed-toast-visible {
                opacity: 1 !important;
            }

            .lb-cubed-valid-feedback-proxy {
                background: var(--lb-cubed-success-toast-bg) !important;
                background-color: var(--lb-cubed-success-toast-bg) !important;
                color: var(--lb-cubed-success-toast-fg) !important;
                border-color: var(--lb-cubed-success-toast-bg) !important;
            }

            .lb-cubed-error-feedback-proxy {
                background: var(--lb-cubed-error-toast-bg) !important;
                background-color: var(--lb-cubed-error-toast-bg) !important;
                color: var(--lb-cubed-error-toast-fg) !important;
                border-color: var(--lb-cubed-error-toast-bg) !important;
            }

            .lb-cubed-valid-feedback-proxy *,
            .lb-cubed-error-feedback-proxy * {
                opacity: 1 !important;
                animation: none !important;
                transition: none !important;
                text-shadow: none !important;
            }

            .lb-cubed-valid-feedback-proxy * {
                color: var(--lb-cubed-success-toast-fg) !important;
                -webkit-text-fill-color: var(--lb-cubed-success-toast-fg) !important;
                fill: currentColor !important;
            }

            .lb-cubed-error-feedback-proxy * {
                color: var(--lb-cubed-error-toast-fg) !important;
                -webkit-text-fill-color: var(--lb-cubed-error-toast-fg) !important;
                fill: currentColor !important;
            }

            .lb-cubed-valid-feedback-proxy::before,
            .lb-cubed-valid-feedback-proxy::after,
            .lb-cubed-error-feedback-proxy::before,
            .lb-cubed-error-feedback-proxy::after {
                background: transparent !important;
                box-shadow: none !important;
                animation: none !important;
            }
'''
source = require_replace(
    source,
    old_toast_css,
    new_toast_css,
    "toast proxy CSS",
)

source = require_replace(
    source,
    '''            .lb-cubed-valid-feedback-relocated-source {
                visibility: hidden !important;''',
    '''            .lb-cubed-valid-feedback-relocated-source,
            .lb-cubed-error-feedback-source {
                visibility: hidden !important;''',
    "hide native success + error sources",
)

# Do not let the broad native-surface rule recolor toast boxes after their own
# semantic rules have run.
source = require_replace(
    source,
    '''            html.lb-cubed-native-theme .lb-word-list-container,
            html.lb-cubed-native-theme .lb-message-box,
            html.lb-cubed-native-theme button:not([id^="lb-cubed"]),''',
    '''            html.lb-cubed-native-theme .lb-word-list-container,
            html.lb-cubed-native-theme button:not([id^="lb-cubed"]),''',
    "remove message box from broad native recolor",
)

# Keep the now-correct dark modal X semantic instead of hardcoded black.
source = source.replace(
    "color: #000000 !important;\n                -webkit-text-fill-color: #000000 !important;",
    "color: var(--lb-cubed-lb-bg) !important;\n                -webkit-text-fill-color: var(--lb-cubed-lb-bg) !important;",
    2,
)

# Static acceptance checks for this patch.
checks = [
    'ApplyNative: false',
    'CreateThemeColorRow("Foreground", "LbForeground")',
    'CreateThemeColorRow("Highlight", "LbActive")',
    'const ApplyNative = Theme.ApplyNative !== false;',
    'ApplyBoardThemeMatrix(Palette, LbSemantics);',
    'function UninstallBoardTextSourceHook()',
    'function GetNativeErrorWordFeedbackSource()',
    'lb-cubed-error-feedback-proxy',
    'transition: opacity ${ToastFadeMs}ms ease !important;',
]
for check in checks:
    if check not in source:
        raise RuntimeError(f"acceptance check missing: {check}")

if 'Palette.LbForeground = GetThemeContrastPole(Palette.LbBackground)' in source:
    raise RuntimeError("LB Foreground is still being derived from Background")

PATH.write_text(source, encoding="utf-8")
print("Applied beta.22 triad theme + unified toast proxy patch")
