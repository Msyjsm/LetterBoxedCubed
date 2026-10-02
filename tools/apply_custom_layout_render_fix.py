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
    "// @version      1.13.1-beta.4",
    "// @version      1.13.1-beta.5",
    "version"
)

anchor = '''        RenderFoundAndUnfoundWords(
            DashboardGrid,
            PreviousOpenStates,
            KnownWordsForDisplay,
            UnfoundWords
        );

        PanelContent.scrollTop =
            PreviousScrollTop;
'''
replacement = '''        RenderFoundAndUnfoundWords(
            DashboardGrid,
            PreviousOpenStates,
            KnownWordsForDisplay,
            UnfoundWords
        );

        /*
            Custom 12-column placement is stored as inline grid-column/grid-row
            styles on the dashboard children. RenderPanel() replaces those
            children whenever game state changes (including a new-word
            highlight), so reapply the custom placement before the browser gets
            a chance to paint the freshly rendered grid. Automatic layouts are
            class/CSS-driven and need no equivalent refresh.
        */
        if (PanelLayoutStyle === "custom") {
            ApplyCustomPanelLayout(Panel);
        }

        PanelContent.scrollTop =
            PreviousScrollTop;
'''
source = replace_once(source, anchor, replacement, "RenderPanel custom-layout refresh")
SOURCE.write_text(source, encoding="utf-8")

tests = TESTS.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    "assert(source.includes('// @version      1.13.1-beta.4'), 'beta.3 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.5'), 'beta.5 version missing');",
    "test version"
)
insert_after = "assert(source.includes('Start from current automatic layout'), 'automatic-to-custom snapshot action missing');\n"
test_line = "assert(source.includes('Custom 12-column placement is stored as inline grid-column/grid-row'), 'custom layout is not reapplied after RenderPanel rebuilds dashboard children');\n"
if test_line not in tests:
    tests = replace_once(tests, insert_after, insert_after + test_line, "custom render regression test")
TESTS.write_text(tests, encoding="utf-8")
