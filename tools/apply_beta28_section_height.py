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

# Update/extend static regression coverage.
test_path = Path('tests/final-polish-tests.js')
tests = test_path.read_text(encoding='utf-8')
tests = tests.replace(
    "assert(source.includes('// @version      1.13.1-beta.27'), 'beta.27 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.28'), 'beta.28 version missing');",
    1
)
tests = tests.replace(
    "assert(source.includes('grid-template-rows: minmax(0, 1fr);'), 'wide responsive section row is not bounded');",
    "assert(source.includes('\\\"stats stats stats stats stats\\\"') && source.includes('\\\"hints twofers length found unfound\\\"'), 'wide responsive section rows are not bounded');",
    1
)
marker = "console.log('PASS: beta.27 section scrollers + ticker + cleanup static checks');"
if marker not in tests:
    raise SystemExit('test marker missing')
block = r'''

// beta.28: section-owned scrolling + full-height allocation.
assert(source.includes('const GameContainerVerticalPaddingTrimPx = 30;'), '30px game-container padding trim missing');
assert(source.includes('ApplyGameContainerVerticalPaddingTrim(GameContainer);'), 'game-container padding trim is not applied');
assert(source.includes('flex: 1 1 0;\n                min-width: 0;\n                min-height: 0;\n                height: auto;\n                max-height: 100%;'), 'dashboard does not own remaining panel height');
assert(source.includes('.lb-cubed-dashboard-grid > .lb-cubed-tree {\n                height: 100%;'), 'dashboard sections do not stretch to their grid tracks');
assert(source.includes('flex: 1 1 0 !important;\n                min-height: 0 !important;\n                overflow-x: hidden !important;\n                overflow-y: auto !important;'), 'section scroll lanes are not explicit scrollports');
assert(source.includes('scrollbar-gutter: stable;'), 'section scrollbar gutter missing');
assert(source.includes('Entry.Definition.Selector === ".lb-cubed-stat-grid"'), 'Completion/Longest are not forced into the first row');
assert(source.includes('grid-template-rows: auto;\n                grid-auto-rows: minmax(0, 1fr);'), 'custom layout does not keep row 1 static and divide later rows evenly');
assert(source.includes('"stats stats stats stats stats"') && source.includes('"hints twofers length found unfound"'), 'wide automatic layout no longer pins stats above scrollable sections');
'''
if 'beta.28: section-owned scrolling' not in tests:
    tests = tests.replace(marker, block + '\n' + "console.log('PASS: beta.28 section scrollers + full-height allocation static checks');", 1)
test_path.write_text(tests, encoding='utf-8')
