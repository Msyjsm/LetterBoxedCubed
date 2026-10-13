from pathlib import Path

SOURCE_PATH = Path("LetterBoxedCubed.user.js")
TEST_PATH = Path("tests/final-polish-tests.js")

source = SOURCE_PATH.read_text(encoding="utf-8")
tests = TEST_PATH.read_text(encoding="utf-8")


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"{label}: expected fragment not found")
    return text.replace(old, new, 1)


def replace_function(text, start_name, next_name, replacement, label):
    start = text.find(f"    function {start_name}(")
    end = text.find(f"    function {next_name}(", start + 1)
    if start < 0 or end < 0:
        raise RuntimeError(f"{label}: function boundary not found")
    return text[:start] + replacement.rstrip() + "\n\n" + text[end:]


source = replace_once(
    source,
    "// @version      1.13.1-beta.22",
    "// @version      1.13.1-beta.23",
    "version",
)

source = replace_once(
    source,
    '''    let ErrorFeedbackPlacementTimer = null;
    let ErrorFeedbackRemovalTimer = null;
    let RenderedErrorFeedbackText = "";
    const ValidFeedbackSettlePollMs = 30;''',
    '''    let ErrorFeedbackPlacementTimer = null;
    let ErrorFeedbackRemovalTimer = null;
    let RenderedErrorFeedbackText = "";
    let ActiveErrorFeedbackSource = null;
    let ActiveErrorFeedbackText = "";
    let ActiveToastType = null;
    const ValidFeedbackSettlePollMs = 30;''',
    "toast lifecycle state",
)

source = replace_once(
    source,
    '''            ErrorToastForeground: IsDark ? Background : Highlight,
            ErrorToastBackground: Foreground''',
    '''            ErrorToastForeground: IsDark ? Background : Highlight,
            ErrorToastBackground: IsDark ? Highlight : Foreground''',
    "dark error toast triad mapping",
)

capture_helper = r'''    function ParseComputedThemeColor(Value) {
        const Text = String(Value || "").trim();
        if (!Text || Text === "transparent") {
            return null;
        }

        if (/^#[0-9a-f]{6}$/i.test(Text)) {
            return NormalizeThemeColor(Text, null);
        }

        const Match = Text.match(
            /^rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)(?:\s*,\s*([0-9.]+))?\s*\)$/i
        );
        if (!Match) {
            return null;
        }

        const Alpha = Match[4] === undefined ? 1 : Number(Match[4]);
        if (!Number.isFinite(Alpha) || Alpha <= 0.01) {
            return null;
        }

        return ThemeRgbToHex([
            Number(Match[1]),
            Number(Match[2]),
            Number(Match[3])
        ]);
    }

    function CaptureNativeLightTriad(Palette) {
        const Captured = { ...Palette };

        /*
            NYT Light intentionally bypasses Cubed's native theming. When it is
            used as the source for a custom theme, sample NYT's live computed
            Background / Foreground instead of relying on a stale calibration.
            This makes "duplicate NYT Light" a visual no-op even if NYT tweaks
            its native salmon later.
        */
        let BackgroundNode = document.querySelector(
            ".lb-game-container"
        );
        while (BackgroundNode && BackgroundNode instanceof Element) {
            const Background = ParseComputedThemeColor(
                getComputedStyle(BackgroundNode).backgroundColor
            );
            if (Background) {
                Captured.LbBackground = Background;
                break;
            }
            BackgroundNode = BackgroundNode.parentElement;
        }

        const TextNode =
            document.querySelector(".lb-text-field") ||
            document.querySelector(".lb-text-field-label");
        if (TextNode) {
            const Foreground = ParseComputedThemeColor(
                getComputedStyle(TextNode).color
            );
            if (Foreground) {
                Captured.LbForeground = Foreground;
            }
        }

        return Captured;
    }

'''
marker = "    function GetLbThemeSemantics(Palette) {"
if marker not in source:
    raise RuntimeError("native Light capture insertion point missing")
source = source.replace(marker, capture_helper + marker, 1)

new_refresh = r'''    function QueueBoardThemeRendererRefresh(Force = false) {
        const Root = document.documentElement;
        const SquareContainer = document.querySelector(
            ".lb-game-container .lb-square-container"
        );
        if (
            (!Force && !Root?.classList.contains("lb-cubed-board-themed")) ||
            !SquareContainer
        ) {
            return;
        }

        const DispatchResize = () =>
            window.dispatchEvent(new Event("resize"));
        const Rect = SquareContainer.getBoundingClientRect();

        /*
            A synthetic window resize alone does not currently make NYT repaint
            the canvas when its measured box is unchanged. That left source
            pixels produced under the previous Light/Dark paint shim in place
            until the next keystroke. Give the square a one-frame 1px width
            nudge so NYT's ResizeObserver sees a real geometry change, then
            restore every inline width property exactly as it was.
        */
        if (!Number.isFinite(Rect.width) || Rect.width <= 0) {
            DispatchResize();
            setTimeout(DispatchResize, 80);
            return;
        }

        const Properties = ["width", "min-width", "max-width"];
        const Saved = Properties.map(Property => ({
            Property,
            Value: SquareContainer.style.getPropertyValue(Property),
            Priority: SquareContainer.style.getPropertyPriority(Property)
        }));
        const NudgedWidth = `${Rect.width + 1}px`;

        requestAnimationFrame(() => {
            for (const { Property } of Saved) {
                SquareContainer.style.setProperty(
                    Property,
                    NudgedWidth,
                    "important"
                );
            }
            void SquareContainer.offsetWidth;
            DispatchResize();

            requestAnimationFrame(() => {
                for (const { Property, Value, Priority } of Saved) {
                    if (Value) {
                        SquareContainer.style.setProperty(
                            Property,
                            Value,
                            Priority
                        );
                    } else {
                        SquareContainer.style.removeProperty(Property);
                    }
                }
                void SquareContainer.offsetWidth;
                DispatchResize();
                setTimeout(DispatchResize, 80);
            });
        });
    }
'''
source = replace_function(
    source,
    "QueueBoardThemeRendererRefresh",
    "ApplyTheme",
    new_refresh,
    "board refresh",
)

source = replace_once(
    source,
    '''        const Theme = GetActiveThemeDefinition();
        const Palette = NormalizeThemePalette(
            Theme.Palette,
            PrebuiltThemes[DefaultThemeId].Palette,
            false
        );
        const Root = document.documentElement;
        if (!Root) {
            return;
        }

        const LbSemantics = GetLbThemeSemantics(Palette);''',
    '''        const Theme = GetActiveThemeDefinition();
        let Palette = NormalizeThemePalette(
            Theme.Palette,
            PrebuiltThemes[DefaultThemeId].Palette,
            false
        );
        const Root = document.documentElement;
        if (!Root) {
            return;
        }

        const ApplyNative = Theme.ApplyNative !== false;
        const WasBoardThemed = Root.classList.contains("lb-cubed-board-themed");
        const WasDarkTheme = Root.classList.contains("lb-cubed-theme-dark");

        /* Measure NYT Light only after removing any previous custom overrides. */
        if (!ApplyNative) {
            Root.classList.remove(
                "lb-cubed-native-theme",
                "lb-cubed-board-themed",
                "lb-cubed-theme-dark"
            );
            if (Theme.Id === DefaultThemeId) {
                Palette = CaptureNativeLightTriad(Palette);
            }
        }

        const LbSemantics = GetLbThemeSemantics(Palette);''',
    "ApplyTheme prelude",
)

source = replace_once(
    source,
    '''        const WasBoardThemed = Root.classList.contains("lb-cubed-board-themed");
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
        }''',
    '''        const ThemeModeChanged =
            WasBoardThemed &&
            WasDarkTheme !== LbSemantics.IsDark;

        Root.classList.toggle("lb-cubed-native-theme", ApplyNative);
        Root.classList.toggle("lb-cubed-board-themed", ApplyNative);
        Root.classList.toggle("lb-cubed-theme-dark", LbSemantics.IsDark);
        Root.dataset.lbcTheme = Theme.Id || DefaultThemeId;
        Root.dataset.lbcThemeMode = LbSemantics.IsDark ? "dark" : "light";

        if (ApplyNative) {
            InstallBoardTextSourceHook();
            ApplyBoardThemeMatrix(Palette, LbSemantics);

            const NeedsSourceRepaint =
                (LbSemantics.IsDark && !WasBoardThemed) ||
                ThemeModeChanged;
            if (NeedsSourceRepaint) {
                QueueBoardThemeRendererRefresh(true);
            }
        } else {
            UninstallBoardTextSourceHook();
            if (WasBoardThemed && WasDarkTheme) {
                QueueBoardThemeRendererRefresh(true);
            }
        }''',
    "ApplyTheme repaint routing",
)

source = replace_once(
    source,
    '''        const Palette = NormalizeThemePalette(Base.Palette, null, false);

        if (LbcBackgroundMatchesLbBackground) {''',
    '''        let Palette = NormalizeThemePalette(Base.Palette, null, false);
        if (Base.Id === DefaultThemeId && Base.ApplyNative === false) {
            Palette = CaptureNativeLightTriad(Palette);
        }

        if (LbcBackgroundMatchesLbBackground) {''',
    "custom native-Light capture",
)

toast_helpers = r'''    function RemoveToastProxyImmediately(Kind) {
        if (Kind === "success") {
            clearTimeout(ValidFeedbackPlacementTimer);
            ValidFeedbackPlacementTimer = null;
            clearTimeout(ValidFeedbackClearTimer);
            ValidFeedbackClearTimer = null;
            document.querySelectorAll(".lb-cubed-valid-feedback-proxy")
                .forEach(Element => Element.remove());
            RenderedValidFeedbackKey = null;
            PendingValidFeedbackBaselineChainLength = null;
            PendingValidFeedbackStartedAt = 0;
            ValidFeedbackProxyShownAt = 0;
            return;
        }

        if (Kind === "error") {
            clearTimeout(ErrorFeedbackPlacementTimer);
            ErrorFeedbackPlacementTimer = null;
            clearTimeout(ErrorFeedbackRemovalTimer);
            ErrorFeedbackRemovalTimer = null;
            document.querySelectorAll(".lb-cubed-error-feedback-proxy")
                .forEach(Element => Element.remove());
            RenderedErrorFeedbackText = "";
        }
    }

    function ActivateToastType(Kind) {
        if (ActiveToastType === Kind) {
            return;
        }

        const Previous = ActiveToastType;
        ActiveToastType = Kind;
        if (Previous && Previous !== Kind) {
            /* A newer toast wins immediately; do not cross-fade two messages. */
            RemoveToastProxyImmediately(Previous);
        }
    }

'''
marker = "    function GetNativeErrorWordFeedbackSource() {"
if marker not in source:
    raise RuntimeError("toast helper insertion point missing")
source = source.replace(marker, toast_helpers + marker, 1)

source = replace_once(
    source,
    '''        RenderedErrorFeedbackText = "";

        document.querySelectorAll(".lb-cubed-error-feedback-source")''',
    '''        RenderedErrorFeedbackText = "";
        ActiveErrorFeedbackSource = null;
        ActiveErrorFeedbackText = "";
        if (ActiveToastType === "error") {
            ActiveToastType = null;
        }

        document.querySelectorAll(".lb-cubed-error-feedback-source")''',
    "error toast clear state",
)

source = replace_once(
    source,
    '''        clearTimeout(ErrorFeedbackRemovalTimer);
        ErrorFeedbackRemovalTimer = null;
        Source.classList.add("lb-cubed-error-feedback-source");

        let Proxy = GameContainer.querySelector(''',
    '''        const StartsNewLifecycle =
            ActiveErrorFeedbackSource !== Source ||
            ActiveErrorFeedbackText !== MessageText;
        if (StartsNewLifecycle) {
            ActiveErrorFeedbackSource = Source;
            ActiveErrorFeedbackText = MessageText;
            ActivateToastType("error");
        }

        Source.classList.add("lb-cubed-error-feedback-source");
        if (ActiveToastType !== "error") {
            return;
        }

        clearTimeout(ErrorFeedbackRemovalTimer);
        ErrorFeedbackRemovalTimer = null;

        let Proxy = GameContainer.querySelector(''',
    "error toast lifecycle arbitration",
)

source = replace_once(
    source,
    '''        ValidFeedbackProxyShownAt = 0;

        document.querySelectorAll(".lb-cubed-valid-feedback-proxy")''',
    '''        ValidFeedbackProxyShownAt = 0;
        if (ActiveToastType === "success") {
            ActiveToastType = null;
        }

        document.querySelectorAll(".lb-cubed-valid-feedback-proxy")''',
    "success toast clear state",
)

source = replace_once(
    source,
    '''        if (Source) {
            ActiveValidFeedbackSource = Source;
            ActiveValidFeedbackText = MessageText;
        }

        /*
            Wait until NYT has committed''',
    '''        if (Source) {
            ActiveValidFeedbackSource = Source;
            ActiveValidFeedbackText = MessageText;
        }

        if (ActiveToastType !== "success") {
            return;
        }

        /*
            Wait until NYT has committed''',
    "success active-type guard",
)

source = replace_once(
    source,
    '''            if (StartsNewLifecycle) {
                clearTimeout(ValidFeedbackClearTimer);''',
    '''            if (StartsNewLifecycle) {
                ActivateToastType("success");
                clearTimeout(ValidFeedbackClearTimer);''',
    "success toast lifecycle arbitration",
)

source = replace_once(
    source,
    '''                display: block !important;
                opacity: 0 !important;
                clip-path: none !important;''',
    '''                display: block !important;
                box-sizing: border-box !important;
                padding: 6px 10px !important;
                border-radius: 3px !important;
                line-height: 1.2 !important;
                white-space: nowrap !important;
                opacity: 0 !important;
                clip-path: none !important;''',
    "toast padding",
)

# Update static regression checks for beta.23.
tests = tests.replace(
    "assert(source.includes('// @version      1.13.1-beta.22'), 'beta.22 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.23'), 'beta.23 version missing');",
    1,
)
tests = tests.replace(
    "assert(source.includes('ErrorToastBackground: Foreground'), 'error background triad mapping missing');",
    "assert(source.includes('ErrorToastBackground: IsDark ? Highlight : Foreground'), 'error background triad mapping missing');",
    1,
)
tests = tests.replace(
    "console.log('PASS: beta.22 triad theme + toast static checks');",
    """assert(source.includes('function CaptureNativeLightTriad(Palette)'), 'native Light live calibration missing');
assert(source.includes('Palette = CaptureNativeLightTriad(Palette);'), 'custom Light capture missing');
assert(source.includes('const ThemeModeChanged ='), 'theme mode transition detection missing');
assert(source.includes('const NudgedWidth = `${Rect.width + 1}px`;'), 'real board resize nudge missing');
assert(source.includes('function ActivateToastType(Kind)'), 'cross-type toast arbitration missing');
assert(source.includes('RemoveToastProxyImmediately(Previous)'), 'older toast immediate kill missing');
assert(source.includes('padding: 6px 10px !important;'), 'toast padding missing');
console.log('PASS: beta.23 theme refresh + toast static checks');""",
    1,
)

SOURCE_PATH.write_text(source, encoding="utf-8")
TEST_PATH.write_text(tests, encoding="utf-8")
print("Applied beta.23 theme switch + toast polish patch")
