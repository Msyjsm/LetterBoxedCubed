from pathlib import Path
import re

source_path = Path('LetterBoxedCubed.user.js')
text = source_path.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 occurrence, found {count}')
    text = text.replace(old, new, 1)


replace_once('// @version      1.13.1-beta.26', '// @version      1.13.1-beta.27', 'version')

# -----------------------------------------------------------------------------
# Game-title hiding should also collapse NYT's otherwise orphaned section margin.
# Keep the compact-layout preference semantically disabled while the title is
# hidden, but separate that from whether the title section margin is collapsed.
# -----------------------------------------------------------------------------
replace_once(
'''        const CompactTitleActive =
            CompactTitleLayout &&
            !HideNytGameTitle;

        if (Host) {''',
'''        const CompactTitleActive =
            CompactTitleLayout &&
            !HideNytGameTitle;
        const CollapseTitleSectionMargin =
            CompactTitleActive ||
            HideNytGameTitle;

        if (Host) {''',
'compact title state split')

replace_once(
'''        if (TitleSection) {
            TitleSection.classList.toggle(
                "lb-cubed-compact-title-section",
                CompactTitleActive
            );
        }''',
'''        if (TitleSection) {
            TitleSection.classList.toggle(
                "lb-cubed-compact-title-section",
                CollapseTitleSectionMargin
            );
        }''',
'collapse title section margin when hidden')

# -----------------------------------------------------------------------------
# Replace the single outer LBC scroll position with independent subsection
# scroll state. RenderPanel rebuilds its dashboard frequently, so preserve each
# named scroller's position across those rebuilds.
# -----------------------------------------------------------------------------
replace_once(
'''        const PreviousScrollTop =
            PanelContent.scrollTop;''',
'''        const PreviousSectionScrollStates =
            ReadPanelSectionScrollStates(
                PanelContent
            );''',
'panel scroll snapshot')

replace_once(
'''        PanelContent.scrollTop =
            PreviousScrollTop;''',
'''        RestorePanelSectionScrollStates(
            PanelContent,
            PreviousSectionScrollStates
        );''',
'panel scroll restore')

# Hint First/Second lists each own a scroll lane.
replace_once(
'''        const List = document.createElement("div");
        List.className = "lb-cubed-potential-word-list";

        const Position = SectionName === "HintFirstWords"''',
'''        const List = document.createElement("div");
        List.className = "lb-cubed-potential-word-list";
        List.dataset.cubedScrollKey = SectionName;

        const Position = SectionName === "HintFirstWords"''',
'hint scroller key')

# Twofers use one scrollbar regardless of grouped/ungrouped presentation.
replace_once(
'''        const TwoferBody = document.createElement("div");
        TwoferBody.className = "lb-cubed-twofer-body";

        if (TwofersGrouped) {''',
'''        const TwoferBody = document.createElement("div");
        TwoferBody.className = "lb-cubed-twofer-body";
        TwoferBody.dataset.cubedScrollKey = "Twofers";

        if (TwofersGrouped) {''',
'twofer scroller key')

# Words by Length normally fits, but still gets its own overflow lane for very
# short panel heights.
replace_once(
'''        const LengthGrid = document.createElement("div");
        LengthGrid.className = "lb-cubed-length-grid";

        const Lengths = Object.keys(Stats.LengthStats)''',
'''        const LengthGrid = document.createElement("div");
        LengthGrid.className = "lb-cubed-length-grid";
        LengthGrid.dataset.cubedScrollKey = "WordsByLength";

        const Lengths = Object.keys(Stats.LengthStats)''',
'length scroller key')

# Found and Unfound each own a scroll lane.
replace_once(
'''        const List = document.createElement("div");
        List.className = "lb-cubed-word-grid";

        if (Words.length === 0) {''',
'''        const List = document.createElement("div");
        List.className = "lb-cubed-word-grid";
        List.dataset.cubedScrollKey = SectionName;

        if (Words.length === 0) {''',
'word tree scroller key')

# Preserve subsection scroll positions across RenderPanel() DOM replacement.
marker = '''    function ReadTreeOpenStates(Panel) {'''
if text.count(marker) != 1:
    raise SystemExit('scroll-state insertion marker missing')
scroll_helpers = '''    function ReadPanelSectionScrollStates(Panel) {
        const States = {};

        for (const Scroller of Panel.querySelectorAll(
            "[data-cubed-scroll-key]"
        )) {
            const Key = Scroller.dataset.cubedScrollKey;
            if (!Key) {
                continue;
            }

            States[Key] = {
                Top: Scroller.scrollTop,
                Left: Scroller.scrollLeft
            };
        }

        return States;
    }

    function RestorePanelSectionScrollStates(Panel, States) {
        if (!States || typeof States !== "object") {
            return;
        }

        for (const Scroller of Panel.querySelectorAll(
            "[data-cubed-scroll-key]"
        )) {
            const Key = Scroller.dataset.cubedScrollKey;
            const State = Key ? States[Key] : null;
            if (!State) {
                continue;
            }

            Scroller.scrollTop = Number(State.Top) || 0;
            Scroller.scrollLeft = Number(State.Left) || 0;
        }
    }

'''
text = text.replace(marker, scroll_helpers + marker, 1)

# -----------------------------------------------------------------------------
# Longest Found is always one line. If tied values overflow horizontally, glide
# gently between both ends. Hover pauses the glide; mousewheel up/down moves the
# ticker left/right respectively.
# -----------------------------------------------------------------------------
replace_once(
'''        const LongestCard = AddStat(
            StatGrid,
            "Longest Found",
            Stats.LongestFoundText
        );

        if (Stats.LongestLength > 0) {''',
'''        const LongestCard = AddStat(
            StatGrid,
            "Longest Found",
            Stats.LongestFoundText
        );
        ConfigureLongestFoundTicker(LongestCard);

        if (Stats.LongestLength > 0) {''',
'longest ticker hookup')

marker = '''    function RenderHints(Panel, PreviousOpenStates, HintStats) {'''
if text.count(marker) != 1:
    raise SystemExit('longest ticker insertion marker missing')
ticker_helper = '''    function ConfigureLongestFoundTicker(Card) {
        const Viewport = Card?.querySelector(
            ".lb-cubed-stat-value"
        );
        if (!Viewport) {
            return;
        }

        Viewport.classList.add("lb-cubed-longest-ticker");
        Viewport.title = Viewport.textContent || "";

        let Paused = false;
        let Direction = 1;
        let LastTimestamp = null;
        let HoldUntil = performance.now() + 900;
        const SpeedPixelsPerSecond = 16;
        const EndPauseMs = 900;

        Viewport.addEventListener("pointerenter", () => {
            Paused = true;
        });
        Viewport.addEventListener("pointerleave", () => {
            Paused = false;
            LastTimestamp = null;
        });
        Viewport.addEventListener(
            "wheel",
            Event => {
                const Maximum = Math.max(
                    0,
                    Viewport.scrollWidth - Viewport.clientWidth
                );
                if (Maximum <= 1) {
                    return;
                }

                const Delta = Event.deltaY !== 0
                    ? Event.deltaY
                    : Event.deltaX;
                Viewport.scrollLeft = Clamp(
                    Viewport.scrollLeft + Delta,
                    0,
                    Maximum
                );
                Event.preventDefault();
            },
            { passive: false }
        );

        const Tick = Timestamp => {
            if (!Viewport.isConnected) {
                return;
            }

            const Maximum = Math.max(
                0,
                Viewport.scrollWidth - Viewport.clientWidth
            );

            if (Maximum <= 1) {
                Viewport.scrollLeft = 0;
                LastTimestamp = Timestamp;
                requestAnimationFrame(Tick);
                return;
            }

            if (Paused || Timestamp < HoldUntil) {
                LastTimestamp = Timestamp;
                requestAnimationFrame(Tick);
                return;
            }

            const DeltaMs = LastTimestamp === null
                ? 0
                : Math.min(50, Math.max(0, Timestamp - LastTimestamp));
            LastTimestamp = Timestamp;

            let Next =
                Viewport.scrollLeft +
                Direction * SpeedPixelsPerSecond * (DeltaMs / 1000);

            if (Next >= Maximum) {
                Next = Maximum;
                Direction = -1;
                HoldUntil = Timestamp + EndPauseMs;
            } else if (Next <= 0) {
                Next = 0;
                Direction = 1;
                HoldUntil = Timestamp + EndPauseMs;
            }

            Viewport.scrollLeft = Next;
            requestAnimationFrame(Tick);
        };

        requestAnimationFrame(Tick);
    }

'''
text = text.replace(marker, ticker_helper + marker, 1)

# -----------------------------------------------------------------------------
# Panel shell: no outer LBC scrollbar. Header stays fixed, dashboard consumes the
# remaining height, and each data-heavy subsection owns its own scroll lane.
# -----------------------------------------------------------------------------
replace_once(
'''            #${PanelContentId} {
                width: 100%;
                height: 100%;
                min-height: 0;
                padding: 12px;
                overflow-x: hidden;
                overflow-y: auto;''',
'''            #${PanelContentId} {
                display: flex;
                flex-direction: column;
                width: 100%;
                height: 100%;
                min-height: 0;
                padding: 12px;
                overflow: hidden;''',
'panel content outer scroller removal')

# Header must never be squeezed by the new fixed-height dashboard viewport.
replace_once(
'''            .lb-cubed-header {
                display: flex;
                justify-content: space-between;''',
'''            .lb-cubed-header {
                display: flex;
                flex: 0 0 auto;
                justify-content: space-between;''',
'fixed panel header')

# Base dashboard: fixed stats row plus independently scrollable section rows.
replace_once(
'''            .lb-cubed-dashboard-grid {
                display: grid;
                grid-template-columns: minmax(0, 1fr);
                grid-template-areas:
                    "stats"
                    "hints"
                    "twofers"
                    "length"
                    "found"
                    "unfound";
                gap: 7px;
                align-items: start;
            }''',
'''            .lb-cubed-dashboard-grid {
                display: grid;
                flex: 1 1 auto;
                min-height: 0;
                height: 100%;
                overflow: hidden;
                grid-template-columns: minmax(0, 1fr);
                grid-template-rows:
                    auto
                    repeat(5, minmax(0, 1fr));
                grid-template-areas:
                    "stats"
                    "hints"
                    "twofers"
                    "length"
                    "found"
                    "unfound";
                gap: 7px;
                align-items: stretch;
            }''',
'base dashboard bounded height')

replace_once(
'''            .lb-cubed-stat-grid {
                grid-area: stats;
                display: grid;''',
'''            .lb-cubed-stat-grid {
                grid-area: stats;
                align-self: start;
                display: grid;''',
'stats pinned top')

# Top-level details fill their assigned grid cell only while open. Their summary
# remains pinned while the section's inner content scrolls.
needle = '''            .lb-cubed-dashboard-grid > .lb-cubed-tree,
            .lb-cubed-dashboard-grid > .lb-cubed-stat-grid {
                margin: 0;
            }
'''
if text.count(needle) != 1:
    raise SystemExit('top-level dashboard child style marker missing')
replacement = needle + '''
            .lb-cubed-dashboard-grid > .lb-cubed-tree {
                min-height: 0;
                max-height: 100%;
            }

            .lb-cubed-dashboard-grid > .lb-cubed-tree[open] {
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }

            .lb-cubed-dashboard-grid > .lb-cubed-tree:not([open]) {
                align-self: start;
            }

            .lb-cubed-dashboard-grid > .lb-cubed-tree > summary,
            .lb-cubed-potential-word-tree > summary {
                flex: 0 0 auto;
            }
'''
text = text.replace(needle, replacement, 1)

# Longest ticker visuals: one line, hidden native scrollbar, horizontal movement
# controlled by the small JS animator / hover wheel interaction above.
replace_once(
'''            .lb-cubed-stat-value {
                color: rgb(48, 24, 24);
                font-size: 16px;
                line-height: 1.15;
                font-weight: 700;
                overflow-wrap: anywhere;
            }''',
'''            .lb-cubed-stat-value {
                color: rgb(48, 24, 24);
                font-size: 16px;
                line-height: 1.15;
                font-weight: 700;
                overflow-wrap: anywhere;
            }

            .lb-cubed-longest-ticker {
                width: 100%;
                min-width: 0;
                overflow-x: auto;
                overflow-y: hidden;
                white-space: nowrap;
                overflow-wrap: normal;
                scrollbar-width: none !important;
                overscroll-behavior-x: contain;
            }

            .lb-cubed-longest-ticker::-webkit-scrollbar {
                display: none;
            }''',
'longest ticker CSS')

# Hints: the indicator stays fixed; First/Second Words each owns its own scroll.
replace_once(
'''            .lb-cubed-hints-body {
                padding: 5px;
            }''',
'''            .lb-cubed-hints-body {
                display: flex;
                flex: 1 1 auto;
                flex-direction: column;
                min-height: 0;
                overflow: hidden;
                padding: 5px;
            }''',
'hints body bounded')

replace_once(
'''            .lb-cubed-hint-counter-grid {
                display: grid;
                grid-template-columns:
                    repeat(auto-fit, minmax(125px, 1fr));
                gap: 5px;
                align-items: start;
            }

            .lb-cubed-potential-word-tree {
                min-width: 0;
            }

            .lb-cubed-potential-word-list {
                display: grid;
                grid-template-columns: 1fr;
                gap: 2px;
                padding: 4px;
            }''',
'''            .lb-cubed-hint-counter-grid {
                display: grid;
                flex: 1 1 auto;
                min-height: 0;
                grid-template-columns:
                    repeat(auto-fit, minmax(125px, 1fr));
                grid-auto-rows: minmax(0, 1fr);
                gap: 5px;
                align-items: stretch;
                overflow: hidden;
            }

            .lb-cubed-potential-word-tree {
                min-width: 0;
                min-height: 0;
                max-height: 100%;
            }

            .lb-cubed-potential-word-tree[open] {
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }

            .lb-cubed-potential-word-list {
                display: grid;
                flex: 1 1 auto;
                min-height: 0;
                grid-template-columns: 1fr;
                gap: 2px;
                padding: 4px;
                overflow-x: hidden;
                overflow-y: auto;
                overscroll-behavior: contain;
            }''',
'hint list independent scrollers')

# Twofers: one shared body scroller whether grouped or ungrouped.
needle = '''            .lb-cubed-twofer-summary {
                display: list-item;
            }
'''
if text.count(needle) != 1:
    raise SystemExit('twofer CSS marker missing')
text = text.replace(needle, needle + '''
            .lb-cubed-twofer-body {
                flex: 1 1 auto;
                min-height: 0;
                overflow-x: hidden;
                overflow-y: auto;
                overscroll-behavior: contain;
            }
''', 1)

# Words by Length can scroll in pathological short-height layouts.
replace_once(
'''            .lb-cubed-length-grid {
                display: grid;
                grid-template-columns: 1fr;
                gap: 2px;
                padding: 4px;
            }''',
'''            .lb-cubed-length-grid {
                display: grid;
                flex: 1 1 auto;
                min-height: 0;
                grid-template-columns: 1fr;
                gap: 2px;
                padding: 4px;
                overflow-x: hidden;
                overflow-y: auto;
                overscroll-behavior: contain;
            }''',
'length independent scroller')

# Found and Unfound each own their list scrollbar.
replace_once(
'''            .lb-cubed-word-grid {
                display: grid;
                grid-template-columns: 1fr;
                gap: 2px;
                padding: 4px;
                overflow: visible;
            }''',
'''            .lb-cubed-word-grid {
                display: grid;
                flex: 1 1 auto;
                min-height: 0;
                grid-template-columns: 1fr;
                gap: 2px;
                padding: 4px;
                overflow-x: hidden;
                overflow-y: auto;
                overscroll-behavior: contain;
            }''',
'found/unfound independent scrollers')

# Responsive row allocation: every non-stat row is a bounded viewport. At wide
# stages, rows shared by several sections divide the remaining height naturally.
replace_once(
'''            #${PanelId}.lb-cubed-layout-stage-0 .lb-cubed-dashboard-grid,
            #${PanelId}.lb-cubed-layout-stage-1 .lb-cubed-dashboard-grid {
                grid-template-columns: minmax(0, 1fr);
                grid-template-areas:''',
'''            #${PanelId}.lb-cubed-layout-stage-0 .lb-cubed-dashboard-grid,
            #${PanelId}.lb-cubed-layout-stage-1 .lb-cubed-dashboard-grid {
                grid-template-columns: minmax(0, 1fr);
                grid-template-rows: auto repeat(5, minmax(0, 1fr));
                grid-template-areas:''',
'stage 0/1 row sizing')

for stage, rows in [(2, 'auto repeat(4, minmax(0, 1fr))'), (3, 'auto repeat(3, minmax(0, 1fr))'), (4, 'auto repeat(2, minmax(0, 1fr))')]:
    old = f'''            #${{PanelId}}.lb-cubed-layout-stage-{stage} .lb-cubed-dashboard-grid {{\n                grid-template-columns:'''
    new = f'''            #${{PanelId}}.lb-cubed-layout-stage-{stage} .lb-cubed-dashboard-grid {{\n                grid-template-rows: {rows};\n                grid-template-columns:'''
    replace_once(old, new, f'stage {stage} row sizing')

replace_once(
'''            #${PanelId}.lb-cubed-layout-stage-5 .lb-cubed-dashboard-grid {
                grid-template-columns:''',
'''            #${PanelId}.lb-cubed-layout-stage-5 .lb-cubed-dashboard-grid {
                grid-template-rows: repeat(2, minmax(0, 1fr));
                grid-template-columns:''',
'stage 5 row sizing')

replace_once(
'''            #${PanelId}.lb-cubed-layout-stage-6 .lb-cubed-dashboard-grid {
                grid-template-columns:''',
'''            #${PanelId}.lb-cubed-layout-stage-6 .lb-cubed-dashboard-grid {
                grid-template-rows: minmax(0, 1fr);
                grid-template-columns:''',
'stage 6 row sizing')

replace_once(
'''            #${PanelId}.lb-cubed-layout-custom .lb-cubed-dashboard-grid {
                display: grid;
                grid-template-columns: repeat(12, minmax(0, 1fr));
                grid-template-areas: none;
            }''',
'''            #${PanelId}.lb-cubed-layout-custom .lb-cubed-dashboard-grid {
                display: grid;
                grid-template-columns: repeat(12, minmax(0, 1fr));
                grid-auto-rows: minmax(0, 1fr);
                grid-template-areas: none;
            }''',
'custom layout bounded rows')

source_path.write_text(text, encoding='utf-8')

# -----------------------------------------------------------------------------
# Static regression checks.
# -----------------------------------------------------------------------------
test_path = Path('tests/final-polish-tests.js')
tests = test_path.read_text(encoding='utf-8')
tests = tests.replace('// @version      1.13.1-beta.26', '// @version      1.13.1-beta.27')
tests = tests.replace("'beta.26 version missing'", "'beta.27 version missing'")
tests = tests.replace(
    "console.log('PASS: beta.26 settings/display cleanup + cross-mode/theme/toast static checks');",
    "console.log('PASS: beta.27 section scrollers + ticker + cleanup static checks');"
)
extra = r'''
assert(source.includes('const CollapseTitleSectionMargin ='), 'hidden-title margin collapse state missing');
assert(source.includes('CompactTitleActive ||\n            HideNytGameTitle'), 'hidden title does not collapse section margin');
assert(source.includes('ReadPanelSectionScrollStates'), 'subsection scroll snapshot missing');
assert(source.includes('RestorePanelSectionScrollStates'), 'subsection scroll restore missing');
assert(source.includes('data-cubed-scroll-key'), 'subsection scroll keys missing');
assert(source.includes('ConfigureLongestFoundTicker(LongestCard)'), 'Longest Found ticker hookup missing');
assert(source.includes('SpeedPixelsPerSecond = 16'), 'Longest Found gentle autoscroll missing');
assert(source.includes('Viewport.addEventListener(\n            "wheel"'), 'Longest Found wheel control missing');
assert(source.includes('.lb-cubed-longest-ticker {'), 'Longest Found one-line CSS missing');
assert(source.includes('white-space: nowrap;\n                overflow-wrap: normal;'), 'Longest Found can still wrap');
assert(source.includes('#${PanelContentId} {\n                display: flex;\n                flex-direction: column;'), 'panel shell is not fixed-header flex layout');
assert(source.includes('overflow: hidden;\n                background: rgb(216, 132, 130);'), 'outer LBC scroller still active');
assert(source.includes('.lb-cubed-potential-word-list {\n                display: grid;\n                flex: 1 1 auto;'), 'Hints do not own list scrollers');
assert(source.includes('.lb-cubed-twofer-body {\n                flex: 1 1 auto;'), 'Twofers body scroller missing');
assert(source.includes('.lb-cubed-length-grid {\n                display: grid;\n                flex: 1 1 auto;'), 'Words by Length fallback scroller missing');
assert(source.includes('.lb-cubed-word-grid {\n                display: grid;\n                flex: 1 1 auto;'), 'Found/Unfound scrollers missing');
assert(source.includes('grid-template-rows: auto repeat(5, minmax(0, 1fr));'), 'narrow responsive section rows are not bounded');
assert(source.includes('grid-template-rows: minmax(0, 1fr);'), 'wide responsive section row is not bounded');
'''
needle = "console.log('PASS: beta.27 section scrollers + ticker + cleanup static checks');"
if needle not in tests:
    raise SystemExit('beta.27 PASS marker missing')
tests = tests.replace(needle, extra + '\n' + needle, 1)
test_path.write_text(tests, encoding='utf-8')
