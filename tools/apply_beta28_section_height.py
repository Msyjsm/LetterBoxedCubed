from pathlib import Path

source_path = Path('LetterBoxedCubed.user.js')
text = source_path.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 match, found {count}')
    text = text.replace(old, new, 1)

replace_once('// @version      1.13.1-beta.27', '// @version      1.13.1-beta.28', 'version')

replace_once(
'''    const EdgePadding = 18;
    const MinimumPanelWidth = 300;''',
'''    const EdgePadding = 18;
    const GameContainerVerticalPaddingTrimPx = 30;
    const MinimumPanelWidth = 300;''',
'padding trim constant'
)

replace_once(
'''    function UpdatePanelLayout() {
        const GameContainer = document.querySelector(".lb-game-container");''',
'''    function ApplyGameContainerVerticalPaddingTrim(GameContainer) {
        if (!GameContainer) {
            return;
        }

        const Dataset = GameContainer.dataset;
        if (!Object.prototype.hasOwnProperty.call(
            Dataset,
            "cubedNativePaddingTop"
        )) {
            const Style = getComputedStyle(GameContainer);
            Dataset.cubedNativePaddingTop = String(
                Math.max(0, Number.parseFloat(Style.paddingTop) || 0)
            );
            Dataset.cubedNativePaddingBottom = String(
                Math.max(0, Number.parseFloat(Style.paddingBottom) || 0)
            );
        }

        const NativeTop = Number.parseFloat(
            Dataset.cubedNativePaddingTop
        ) || 0;
        const NativeBottom = Number.parseFloat(
            Dataset.cubedNativePaddingBottom
        ) || 0;

        GameContainer.style.setProperty(
            "padding-top",
            `${Math.max(0, NativeTop - GameContainerVerticalPaddingTrimPx)}px`,
            "important"
        );
        GameContainer.style.setProperty(
            "padding-bottom",
            `${Math.max(0, NativeBottom - GameContainerVerticalPaddingTrimPx)}px`,
            "important"
        );
    }

    function UpdatePanelLayout() {
        const GameContainer = document.querySelector(".lb-game-container");''',
'padding trim function'
)

replace_once(
'''        if (!GameContainer || !WordContainer || !SquareContainer || !Panel) {
            return;
        }

        const MaximumSidePanelWidth = GetMaximumSidePanelWidth(GameContainer);''',
'''        if (!GameContainer || !WordContainer || !SquareContainer || !Panel) {
            return;
        }

        ApplyGameContainerVerticalPaddingTrim(GameContainer);

        const MaximumSidePanelWidth = GetMaximumSidePanelWidth(GameContainer);''',
'padding trim call'
)

replace_once(
'''                height: auto !important;
                min-height: 0;
                max-height: none !important;''',
'''                height: 100% !important;
                min-height: 0;
                max-height: 100% !important;''',
'side panel height'
)

replace_once(
'''            .lb-cubed-dashboard-grid {
                display: grid;
                flex: 1 1 auto;
                min-height: 0;
                height: 100%;
                overflow: hidden;''',
'''            .lb-cubed-dashboard-grid {
                display: grid;
                flex: 1 1 0;
                min-width: 0;
                min-height: 0;
                height: auto;
                max-height: 100%;
                overflow: hidden;''',
'dashboard flex height'
)

replace_once(
'''            .lb-cubed-dashboard-grid > .lb-cubed-tree {
                min-height: 0;
                max-height: 100%;
            }''',
'''            .lb-cubed-dashboard-grid > .lb-cubed-tree {
                height: 100%;
                min-height: 0;
                max-height: 100%;
            }''',
'grid item definite height'
)

replace_once(
'''            .lb-cubed-dashboard-grid > .lb-cubed-tree > summary,
            .lb-cubed-potential-word-tree > summary {
                flex: 0 0 auto;
            }

            .lb-cubed-stat {''',
'''            .lb-cubed-dashboard-grid > .lb-cubed-tree > summary,
            .lb-cubed-potential-word-tree > summary {
                flex: 0 0 auto;
            }

            /*
                Every scrollable subsection gets an explicit zero-basis flex
                lane. The surrounding details/grid item owns the row height;
                the list/body owns overflow. This prevents content from simply
                being clipped by the row without ever becoming a scrollport.
            */
            .lb-cubed-potential-word-list,
            .lb-cubed-twofer-body,
            .lb-cubed-length-grid,
            .lb-cubed-word-grid {
                flex: 1 1 0 !important;
                min-height: 0 !important;
                overflow-x: hidden !important;
                overflow-y: auto !important;
                overscroll-behavior: contain;
                scrollbar-gutter: stable;
                scrollbar-width: thin;
            }

            .lb-cubed-stat {''',
'section scroll lane rule'
)

replace_once(
'''        const Pinned = Entries.filter(Entry => Entry.Layout.PinFirstRow);
        const Flowing = Entries.filter(Entry => !Entry.Layout.PinFirstRow);''',
'''        const IsStatsEntry = Entry =>
            Entry.Definition.Selector === ".lb-cubed-stat-grid";
        const Pinned = Entries.filter(
            Entry => IsStatsEntry(Entry) || Entry.Layout.PinFirstRow
        );
        const Flowing = Entries.filter(
            Entry => !IsStatsEntry(Entry) && !Entry.Layout.PinFirstRow
        );''',
'force stats first row'
)

replace_once(
'''            #${PanelId}.lb-cubed-layout-stage-5 .lb-cubed-dashboard-grid {
                grid-template-rows: repeat(2, minmax(0, 1fr));
                grid-template-columns:
                    minmax(250px, 2fr)
                    minmax(135px, 1fr)
                    minmax(220px, 1.6fr)
                    minmax(135px, 1fr);
                grid-template-areas:
                    "stats hints twofers length"
                    "found unfound . .";
            }

            #${PanelId}.lb-cubed-layout-stage-6 .lb-cubed-dashboard-grid {
                grid-template-rows: minmax(0, 1fr);
                grid-template-columns:
                    minmax(260px, 2fr)
                    minmax(130px, 1fr)
                    minmax(220px, 1.6fr)
                    minmax(125px, 1fr)
                    minmax(155px, 1fr)
                    minmax(155px, 1fr);
                grid-template-areas:
                    "stats hints twofers length found unfound";
            }''',
'''            #${PanelId}.lb-cubed-layout-stage-5 .lb-cubed-dashboard-grid {
                grid-template-rows:
                    auto
                    repeat(2, minmax(0, 1fr));
                grid-template-columns:
                    minmax(135px, 1fr)
                    minmax(220px, 1.6fr)
                    minmax(135px, 1fr);
                grid-template-areas:
                    "stats stats stats"
                    "hints twofers length"
                    "found unfound .";
            }

            #${PanelId}.lb-cubed-layout-stage-6 .lb-cubed-dashboard-grid {
                grid-template-rows:
                    auto
                    minmax(0, 1fr);
                grid-template-columns:
                    minmax(130px, 1fr)
                    minmax(220px, 1.6fr)
                    minmax(125px, 1fr)
                    minmax(155px, 1fr)
                    minmax(155px, 1fr);
                grid-template-areas:
                    "stats stats stats stats stats"
                    "hints twofers length found unfound";
            }''',
'wide automatic rows'
)

replace_once(
'''            #${PanelId}.lb-cubed-layout-custom .lb-cubed-dashboard-grid {
                display: grid;
                grid-template-columns: repeat(12, minmax(0, 1fr));
                grid-auto-rows: minmax(0, 1fr);
                grid-template-areas: none;
            }''',
'''            #${PanelId}.lb-cubed-layout-custom .lb-cubed-dashboard-grid {
                display: grid;
                grid-template-columns: repeat(12, minmax(0, 1fr));
                grid-template-rows: auto;
                grid-auto-rows: minmax(0, 1fr);
                grid-template-areas: none;
            }''',
'custom first row auto'
)

source_path.write_text(text, encoding='utf-8')

# Extend static regression coverage.
test_path = Path('tests/final-polish-tests.js')
tests = test_path.read_text(encoding='utf-8')
marker = 'console.log("final-polish-tests: all assertions passed");'
if marker not in tests:
    raise SystemExit('test marker missing')
block = r'''

// beta.28: section-owned scrolling + full-height allocation.
assert.match(Source, /@version\s+1\.13\.1-beta\.28/);
assert.match(Source, /const GameContainerVerticalPaddingTrimPx = 30;/);
assert.match(Source, /ApplyGameContainerVerticalPaddingTrim\(GameContainer\);/);
assert.match(Source, /\.lb-cubed-dashboard-grid \{[\s\S]*?flex: 1 1 0;[\s\S]*?height: auto;[\s\S]*?max-height: 100%;/);
assert.match(Source, /\.lb-cubed-dashboard-grid > \.lb-cubed-tree \{[\s\S]*?height: 100%;/);
assert.match(Source, /\.lb-cubed-potential-word-list,[\s\S]*?\.lb-cubed-twofer-body,[\s\S]*?\.lb-cubed-length-grid,[\s\S]*?\.lb-cubed-word-grid \{[\s\S]*?overflow-y: auto !important;[\s\S]*?scrollbar-gutter: stable;/);
assert.match(Source, /Entry\.Definition\.Selector === "\.lb-cubed-stat-grid"/);
assert.match(Source, /lb-cubed-layout-custom \.lb-cubed-dashboard-grid \{[\s\S]*?grid-template-rows: auto;[\s\S]*?grid-auto-rows: minmax\(0, 1fr\);/);
assert.match(Source, /lb-cubed-layout-stage-6 \.lb-cubed-dashboard-grid \{[\s\S]*?"stats stats stats stats stats"[\s\S]*?"hints twofers length found unfound"/);
'''
if 'beta.28: section-owned scrolling' not in tests:
    tests = tests.replace(marker, block + '\n' + marker, 1)
test_path.write_text(tests, encoding='utf-8')
