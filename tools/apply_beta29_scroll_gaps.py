from pathlib import Path
import re

source_path = Path('LetterBoxedCubed.user.js')
text = source_path.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 match, found {count}')
    text = text.replace(old, new, 1)


def sub_once(pattern, repl, label):
    global text
    text2, count = re.subn(pattern, repl, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 match, found {count}')
    text = text2

replace_once('// @version      1.13.1-beta.28', '// @version      1.13.1-beta.29', 'version')

replace_once(
'''    const LayoutGapHandleId = "lb-cubed-layout-gap-handle";''',
'''    const LayoutGapHandleId = "lb-cubed-layout-gap-handle";
    const BottomLayoutGapHandleId = "lb-cubed-bottom-layout-gap-handle";''',
'bottom gap handle id'
)

replace_once(
'''    let NewItemHighlightSeconds = DefaultNewItemHighlightSeconds;
    let AdjustLayoutGap = false;
    let LayoutGapPx = LeftColumnGap;''',
'''    let NewItemHighlightSeconds = DefaultNewItemHighlightSeconds;
    let AdjustLayoutGap = false;
    let LayoutGapPx = LeftColumnGap;
    let BottomLayoutGapPx = 0;''',
'bottom gap state'
)

replace_once(
'''    let LayoutGapResizeState = null;
    let NytPageResizeState = null;''',
'''    let LayoutGapResizeState = null;
    let BottomLayoutGapResizeState = null;
    let NytPageResizeState = null;''',
'bottom gap resize state'
)

replace_once(
'''            AdjustLayoutGap,
            LayoutGapPx,
            HideNytHeader,''',
'''            AdjustLayoutGap,
            LayoutGapPx,
            BottomLayoutGapPx,
            HideNytHeader,''',
'debug bottom gap'
)

replace_once(
'''        LayoutGapPx = GetFiniteGuiNumber(
            "LayoutGapPx",
            MinimumHistoryLaneHeight,
            MinimumHistoryLaneHeight,
            MaximumHistoryLaneHeight
        );''',
'''        LayoutGapPx = GetFiniteGuiNumber(
            "LayoutGapPx",
            MinimumHistoryLaneHeight,
            MinimumHistoryLaneHeight,
            MaximumHistoryLaneHeight
        );
        BottomLayoutGapPx = GetFiniteGuiNumber(
            "BottomLayoutGapPx",
            0,
            MinimumLayoutGap,
            MaximumLayoutGap
        );''',
'load bottom gap'
)

replace_once(
'''    function SetDisplayedLayoutGapPx(Value) {
        const Numeric = Number(Value);
        const DisplayedGap = Number.isFinite(Numeric)
            ? Clamp(Numeric, MinimumLayoutGap, MaximumLayoutGap)
            : MinimumLayoutGap;

        LayoutGapPx =
            MinimumHistoryLaneHeight +
            DisplayedGap;
    }

    function RegisterRecentHighlight(MapValue, Key) {''',
'''    function SetDisplayedLayoutGapPx(Value) {
        const Numeric = Number(Value);
        const DisplayedGap = Number.isFinite(Numeric)
            ? Clamp(Numeric, MinimumLayoutGap, MaximumLayoutGap)
            : MinimumLayoutGap;

        LayoutGapPx =
            MinimumHistoryLaneHeight +
            DisplayedGap;
    }

    function GetDisplayedBottomLayoutGapPx() {
        return Math.max(
            0,
            Math.round(BottomLayoutGapPx)
        );
    }

    function SetDisplayedBottomLayoutGapPx(Value) {
        const Numeric = Number(Value);
        BottomLayoutGapPx = Number.isFinite(Numeric)
            ? Clamp(Numeric, MinimumLayoutGap, MaximumLayoutGap)
            : MinimumLayoutGap;
    }

    function RegisterRecentHighlight(MapValue, Key) {''',
'bottom gap getter setter'
)

replace_once(
'''        GapHeading.textContent = "Adjust layout gap between text input and letter box:";''',
'''        GapHeading.textContent = "Letter box layout gaps";''',
'gap heading label'
)

replace_once(
'''                "Enable draggable grip line",''',
'''                "Enable draggable grip lines",''',
'grip checkbox label'
)

replace_once(
'''                    UpdateLayoutGapHandleVisibility();
                    PositionLayoutGapResizeHandle();''',
'''                    UpdateLayoutGapHandleVisibility();
                    PositionLayoutGapResizeHandle();''',
'gap checkbox callback anchor'
)

replace_once(
'''                "Show a draggable horizontal grip that adjusts the same gap value as the manual input"''',
'''                "Show draggable horizontal grips for the gaps above and below the letter box"''',
'grip checkbox tooltip'
)

replace_once(
'''                "Manually set gap",
                GetDisplayedLayoutGapPx(),''',
'''                "Set top gap",
                GetDisplayedLayoutGapPx(),''',
'top gap label'
)

# Add the bottom-gap row immediately after the existing top-gap row.
needle = '''            CreateSettingsNumberWithReset(
                "Set top gap",
                GetDisplayedLayoutGapPx(),
                MinimumLayoutGap,
                MaximumLayoutGap,
                1,
                "px",
                0,
                "LayoutGapPx",
                Value => {
                    SetDisplayedLayoutGapPx(Value);
                    SetGuiSetting("LayoutGapPx", LayoutGapPx);
                    UpdatePanelLayout();
                }
            )'''
replacement = needle + ''',
            CreateSettingsNumberWithReset(
                "Set bottom gap",
                GetDisplayedBottomLayoutGapPx(),
                MinimumLayoutGap,
                MaximumLayoutGap,
                1,
                "px",
                0,
                "BottomLayoutGapPx",
                Value => {
                    SetDisplayedBottomLayoutGapPx(Value);
                    SetGuiSetting("BottomLayoutGapPx", BottomLayoutGapPx);
                    UpdatePanelLayout();
                }
            )'''
replace_once(needle, replacement, 'bottom gap settings row')

# Create both top and bottom draggable handles.
sub_once(
    r'''    function EnsureLayoutGapResizeHandle\(\) \{.*?\n    \}\n\n    function UpdateLayoutGapHandleVisibility''',
'''    function EnsureLayoutGapResizeHandle() {
        const GameContainer = document.querySelector(".lb-game-container");
        if (!GameContainer) {
            return;
        }

        const Definitions = [
            {
                Id: LayoutGapHandleId,
                Kind: "top",
                Label: "Adjust gap above the letter box",
                Title: "Drag to adjust the gap between the word-entry area and letter box"
            },
            {
                Id: BottomLayoutGapHandleId,
                Kind: "bottom",
                Label: "Adjust gap below the letter box",
                Title: "Drag to adjust the gap between the letter box and Restart/Delete/Enter buttons"
            }
        ];

        for (const Definition of Definitions) {
            if (document.getElementById(Definition.Id)) {
                continue;
            }

            const Handle = document.createElement("div");
            Handle.id = Definition.Id;
            Handle.className = "lb-cubed-layout-gap-handle";
            Handle.dataset.cubedGapKind = Definition.Kind;
            Handle.setAttribute("role", "separator");
            Handle.setAttribute("aria-orientation", "horizontal");
            Handle.setAttribute("aria-label", Definition.Label);
            Handle.title = Definition.Title;
            GameContainer.appendChild(Handle);
        }

        UpdateLayoutGapHandleVisibility();
    }

    function UpdateLayoutGapHandleVisibility''',
'ensure two gap handles'
)

# Replace positioning with explicit top and bottom handle geometry.
sub_once(
    r'''    function PositionLayoutGapResizeHandle\(\) \{.*?\n    \}\n\n    function StartLayoutGapResizeBehavior''',
'''    function GetLetterBoxControlsContainer(SquareContainer) {
        const RestartButton = SquareContainer?.querySelector(
            "[data-testid='restart']"
        );
        if (!RestartButton) {
            return null;
        }

        let Candidate = RestartButton.parentElement;
        while (
            Candidate?.parentElement &&
            Candidate.parentElement !== SquareContainer &&
            !Candidate.parentElement.querySelector("canvas")
        ) {
            Candidate = Candidate.parentElement;
        }
        return Candidate;
    }

    function ApplyBottomLayoutGap(SquareContainer) {
        const Controls = GetLetterBoxControlsContainer(SquareContainer);
        if (!Controls) {
            return;
        }

        if (!Object.prototype.hasOwnProperty.call(
            Controls.dataset,
            "cubedNativeMarginTop"
        )) {
            Controls.dataset.cubedNativeMarginTop = String(
                Number.parseFloat(getComputedStyle(Controls).marginTop) || 0
            );
        }

        const NativeMarginTop = Number.parseFloat(
            Controls.dataset.cubedNativeMarginTop
        ) || 0;
        Controls.style.setProperty(
            "margin-top",
            `${NativeMarginTop + BottomLayoutGapPx}px`,
            "important"
        );
    }

    function PositionLayoutGapResizeHandle() {
        const GameContainer = document.querySelector(".lb-game-container");
        const WordContainer = GameContainer?.querySelector(".lb-word-container");
        const SquareContainer = GameContainer?.querySelector(".lb-square-container");
        const TopHandle = document.getElementById(LayoutGapHandleId);
        const BottomHandle = document.getElementById(BottomLayoutGapHandleId);

        if (
            !GameContainer ||
            !WordContainer ||
            !SquareContainer ||
            !AdjustLayoutGap
        ) {
            return;
        }

        requestAnimationFrame(() => {
            const GameRect = GameContainer.getBoundingClientRect();
            const WordRect = WordContainer.getBoundingClientRect();
            const SquareRect = SquareContainer.getBoundingClientRect();
            const Left = Math.max(
                0,
                Math.min(WordRect.left, SquareRect.left) - GameRect.left
            );
            const Right = Math.min(
                GameRect.width,
                Math.max(WordRect.right, SquareRect.right) - GameRect.left
            );

            if (TopHandle) {
                const GripLineY =
                    SquareRect.top -
                    ResizeGripLineOffset -
                    GameRect.top;
                TopHandle.style.left = `${Math.round(Left)}px`;
                TopHandle.style.width = `${Math.max(24, Math.round(Right - Left))}px`;
                TopHandle.style.top = `${Math.round(GripLineY - 5)}px`;
            }

            if (BottomHandle) {
                const Board = SquareContainer.querySelector("canvas");
                const Controls = GetLetterBoxControlsContainer(SquareContainer);
                if (Board && Controls) {
                    const BoardRect = Board.getBoundingClientRect();
                    const ControlsRect = Controls.getBoundingClientRect();
                    const BottomGripY =
                        ((BoardRect.bottom + ControlsRect.top) / 2) -
                        GameRect.top;
                    BottomHandle.style.left = `${Math.round(SquareRect.left - GameRect.left)}px`;
                    BottomHandle.style.width = `${Math.max(24, Math.round(SquareRect.width))}px`;
                    BottomHandle.style.top = `${Math.round(BottomGripY - 5)}px`;
                }
            }
        });
    }

    function StartLayoutGapResizeBehavior''',
'position both gap handles'
)

sub_once(
    r'''    function StartLayoutGapResizeBehavior\(\) \{.*?\n    \}\n\n    function HandleLayoutGapPointerDown''',
'''    function StartLayoutGapResizeBehavior() {
        EnsureLayoutGapResizeHandle();

        const TopHandle = document.getElementById(LayoutGapHandleId);
        if (TopHandle) {
            TopHandle.addEventListener("pointerdown", HandleLayoutGapPointerDown, true);
            TopHandle.addEventListener("pointermove", HandleLayoutGapPointerMove, true);
            TopHandle.addEventListener("pointerup", EndLayoutGapResize, true);
            TopHandle.addEventListener("pointercancel", EndLayoutGapResize, true);
        }

        const BottomHandle = document.getElementById(BottomLayoutGapHandleId);
        if (BottomHandle) {
            BottomHandle.addEventListener("pointerdown", HandleBottomLayoutGapPointerDown, true);
            BottomHandle.addEventListener("pointermove", HandleBottomLayoutGapPointerMove, true);
            BottomHandle.addEventListener("pointerup", EndBottomLayoutGapResize, true);
            BottomHandle.addEventListener("pointercancel", EndBottomLayoutGapResize, true);
        }
    }

    function HandleLayoutGapPointerDown''',
'start both gap resize behaviors'
)

# Insert bottom-gap drag handlers before NYT page resize behavior.
replace_once(
'''    function StartNytPageResizeBehavior() {''',
'''    function HandleBottomLayoutGapPointerDown(Event) {
        if (Event.button !== 0 || !AdjustLayoutGap) {
            return;
        }

        const Handle = Event.currentTarget;
        BottomLayoutGapResizeState = {
            PointerId: Event.pointerId,
            StartY: Event.clientY,
            StartGap: BottomLayoutGapPx,
            Handle
        };
        Handle.classList.add("lb-cubed-layout-gap-handle-active");
        Handle.setPointerCapture(Event.pointerId);
        Event.preventDefault();
        Event.stopPropagation();
    }

    function HandleBottomLayoutGapPointerMove(Event) {
        if (
            !BottomLayoutGapResizeState ||
            Event.pointerId !== BottomLayoutGapResizeState.PointerId
        ) {
            return;
        }

        BottomLayoutGapPx = Clamp(
            BottomLayoutGapResizeState.StartGap +
            (Event.clientY - BottomLayoutGapResizeState.StartY),
            MinimumLayoutGap,
            MaximumLayoutGap
        );

        const Input = document.querySelector(
            '[data-cubed-setting-input="BottomLayoutGapPx"]'
        );
        if (Input) {
            Input.value = String(GetDisplayedBottomLayoutGapPx());
        }

        UpdatePanelLayout();
        Event.preventDefault();
    }

    function EndBottomLayoutGapResize(Event) {
        if (!BottomLayoutGapResizeState) {
            return;
        }

        const State = BottomLayoutGapResizeState;
        BottomLayoutGapResizeState = null;
        State.Handle.classList.remove("lb-cubed-layout-gap-handle-active");

        try {
            State.Handle.releasePointerCapture(State.PointerId);
        } catch {
            // Ignore browsers that already released pointer capture.
        }

        BottomLayoutGapPx = Math.round(BottomLayoutGapPx);
        SetGuiSetting("BottomLayoutGapPx", BottomLayoutGapPx);
        UpdatePanelLayout();

        if (Event) {
            Event.preventDefault();
        }
    }

    function StartNytPageResizeBehavior() {''',
'bottom gap drag handlers'
)

# Effective square height includes the user-controlled lower gap.
replace_once(
'''    function GetLeftColumnWidth() {''',
'''    function GetEffectiveSquareHeight() {
        return Math.max(
            0,
            NativeSquareHeight + BottomLayoutGapPx
        );
    }

    function GetLeftColumnWidth() {''',
'effective square height helper'
)
text = text.replace('`${NativeSquareHeight}px`', '`${GetEffectiveSquareHeight()}px`')

# Page scroll must belong to the document, not NYT's generated _moment wrapper.
replace_once(
'''    function ApplyGameContainerVerticalPaddingTrim(GameContainer) {''',
'''    function ApplyOuterPageScrollOwnership(GameContainer) {
        document.querySelectorAll(".lb-cubed-native-scroll-passthrough")
            .forEach(Element =>
                Element.classList.remove("lb-cubed-native-scroll-passthrough")
            );

        const GameModuleContainer = GameContainer?.closest(
            '[class*="Game-module_gameContainer__"]'
        );
        let Candidate = GameModuleContainer?.parentElement || null;
        while (Candidate && Candidate !== document.body) {
            const Style = getComputedStyle(Candidate);
            if (/^(auto|scroll)$/.test(Style.overflowY)) {
                Candidate.classList.add("lb-cubed-native-scroll-passthrough");
                break;
            }
            Candidate = Candidate.parentElement;
        }
    }

    function ApplyGameContainerVerticalPaddingTrim(GameContainer) {''',
'outer scroll ownership helper'
)

replace_once(
'''        GameContainer.style.setProperty(
            "padding-bottom",
            `${Math.max(0, NativeBottom - GameContainerVerticalPaddingTrimPx)}px`,
            "important"
        );''',
'''        const BottomPadding = HideNytFooter
            ? 0
            : Math.max(0, NativeBottom - GameContainerVerticalPaddingTrimPx);
        GameContainer.style.setProperty(
            "padding-bottom",
            `${BottomPadding}px`,
            "important"
        );''',
'conditional bottom padding'
)

replace_once(
'''        ApplyGameContainerVerticalPaddingTrim(GameContainer);

        const MaximumSidePanelWidth = GetMaximumSidePanelWidth(GameContainer);''',
'''        ApplyGameContainerVerticalPaddingTrim(GameContainer);
        ApplyOuterPageScrollOwnership(GameContainer);
        ApplyBottomLayoutGap(SquareContainer);

        const MaximumSidePanelWidth = GetMaximumSidePanelWidth(GameContainer);''',
'layout helper calls'
)

# Footer visibility changes must update the conditional bottom padding immediately.
replace_once(
'''        const Targets = GetNytPageTargets();
        const Visibility = [''',
'''        const Targets = GetNytPageTargets();
        ApplyGameContainerVerticalPaddingTrim(
            document.querySelector(".lb-game-container")
        );
        const Visibility = [''',
'footer padding refresh'
)

# Switch details from flex to an explicit two-row grid so the second row is a
# real bounded scrollport in Chromium.
replace_once(
'''            .lb-cubed-dashboard-grid > .lb-cubed-tree[open] {
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }''',
'''            .lb-cubed-dashboard-grid > .lb-cubed-tree[open] {
                display: grid;
                grid-template-rows: auto minmax(0, 1fr);
                overflow: hidden;
            }''',
'top-level details grid'
)

replace_once(
'''            .lb-cubed-hints-body {
                display: flex;
                flex: 1 1 auto;
                flex-direction: column;
                min-height: 0;
                overflow: hidden;
                padding: 5px;
            }''',
'''            .lb-cubed-hints-body {
                display: grid;
                grid-template-rows: auto minmax(0, 1fr);
                min-height: 0;
                overflow: hidden;
                padding: 5px;
            }''',
'hints bounded grid'
)

replace_once(
'''            .lb-cubed-potential-word-tree[open] {
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }''',
'''            .lb-cubed-potential-word-tree[open] {
                display: grid;
                grid-template-rows: auto minmax(0, 1fr);
                overflow: hidden;
            }''',
'nested hint details grid'
)

replace_once(
'''                scrollbar-gutter: stable;
                scrollbar-width: thin;
            }''',
'''                scrollbar-gutter: stable;
                scrollbar-width: thin;
                scrollbar-color:
                    var(--lb-cubed-lbc-text, #301818)
                    var(--lb-cubed-lbc-bg, #D88482);
                align-content: start;
            }''',
'explicit section scrollbar styling'
)

# Let the document own page scrolling instead of NYT's generated inner wrapper.
replace_once(
'''            .lb-game-container.${SideModeClass} {''',
'''            .lb-cubed-native-scroll-passthrough {
                height: auto !important;
                min-height: 0 !important;
                max-height: none !important;
                overflow: visible !important;
                overflow-x: visible !important;
                overflow-y: visible !important;
            }

            .lb-game-container.${SideModeClass} {''',
'outer scroll passthrough css'
)

# Both horizontal gap grips share the same styling and visibility toggle.
text = text.replace(
    '#${LayoutGapHandleId} {',
    '#${LayoutGapHandleId},\n            #${BottomLayoutGapHandleId} {'
)
text = text.replace(
    '.lb-game-container.lb-cubed-adjust-layout-gap > #${LayoutGapHandleId} {',
    '.lb-game-container.lb-cubed-adjust-layout-gap > #${LayoutGapHandleId},\n            .lb-game-container.lb-cubed-adjust-layout-gap > #${BottomLayoutGapHandleId} {'
)
text = text.replace(
    '#${LayoutGapHandleId}::after {',
    '#${LayoutGapHandleId}::after,\n            #${BottomLayoutGapHandleId}::after {'
)
text = text.replace(
    '#${LayoutGapHandleId}:hover::after,\n            #${LayoutGapHandleId}.lb-cubed-layout-gap-handle-active::after {',
    '#${LayoutGapHandleId}:hover::after,\n            #${LayoutGapHandleId}.lb-cubed-layout-gap-handle-active::after,\n            #${BottomLayoutGapHandleId}:hover::after,\n            #${BottomLayoutGapHandleId}.lb-cubed-layout-gap-handle-active::after {'
)
# Theme-aware handle selectors occur later too.
text = text.replace(
    '#${LayoutGapHandleId}::after,\n            .lb-cubed-page-resize-handle::after,',
    '#${LayoutGapHandleId}::after,\n            #${BottomLayoutGapHandleId}::after,\n            .lb-cubed-page-resize-handle::after,'
)
text = text.replace(
    '#${LayoutGapHandleId}:hover::after,\n            #${LayoutGapHandleId}.lb-cubed-layout-gap-handle-active::after,\n            .lb-cubed-page-resize-handle:hover::after,',
    '#${LayoutGapHandleId}:hover::after,\n            #${LayoutGapHandleId}.lb-cubed-layout-gap-handle-active::after,\n            #${BottomLayoutGapHandleId}:hover::after,\n            #${BottomLayoutGapHandleId}.lb-cubed-layout-gap-handle-active::after,\n            .lb-cubed-page-resize-handle:hover::after,'
)

source_path.write_text(text, encoding='utf-8')

# Update and extend regression coverage.
test_path = Path('tests/final-polish-tests.js')
tests = test_path.read_text(encoding='utf-8')
tests = tests.replace(
    "assert(source.includes('// @version      1.13.1-beta.28'), 'beta.28 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.29'), 'beta.29 version missing');",
    1
)
marker = "console.log('PASS: beta.28 section scrollers + full-height allocation static checks');"
if marker not in tests:
    raise SystemExit('test marker missing')
block = r'''

// beta.29: bounded subsection scrollports, document-owned page scrolling,
// conditional footer padding, and independently adjustable lower LB gap.
assert(source.includes('const BottomLayoutGapHandleId = "lb-cubed-bottom-layout-gap-handle";'), 'bottom gap handle id missing');
assert(source.includes('let BottomLayoutGapPx = 0;'), 'bottom gap state missing');
assert(source.includes('"Set top gap"'), 'top gap label missing');
assert(source.includes('"Set bottom gap"'), 'bottom gap label missing');
assert(source.includes('"Enable draggable grip lines"'), 'plural grip label missing');
assert(source.includes('GapHeading.textContent = "Letter box layout gaps";'), 'gap section label missing');
assert(source.includes('function ApplyBottomLayoutGap(SquareContainer)'), 'bottom gap application missing');
assert(source.includes('function HandleBottomLayoutGapPointerMove(Event)'), 'bottom gap drag behavior missing');
assert(source.includes('NativeSquareHeight + BottomLayoutGapPx'), 'lower gap does not expand square lane');
assert(source.includes('const BottomPadding = HideNytFooter'), 'footer-hidden zero bottom padding missing');
assert(source.includes('function ApplyOuterPageScrollOwnership(GameContainer)'), 'outer scroll ownership helper missing');
assert(source.includes('.lb-cubed-native-scroll-passthrough {'), 'native inner-scroll passthrough CSS missing');
assert(source.includes('display: grid;\n                grid-template-rows: auto minmax(0, 1fr);\n                overflow: hidden;'), 'top-level details are not bounded grid scroll hosts');
assert(source.includes('.lb-cubed-potential-word-tree[open] {\n                display: grid;'), 'hint subtrees are not bounded grid scroll hosts');
assert(source.includes('scrollbar-color:\n                    var(--lb-cubed-lbc-text, #301818)'), 'section scrollbar colors missing');
'''
tests = tests.replace(marker, block + '\n' + "console.log('PASS: beta.29 section scrollports + lower gap cleanup static checks');", 1)
test_path.write_text(tests, encoding='utf-8')
