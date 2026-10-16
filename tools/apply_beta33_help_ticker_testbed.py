from pathlib import Path

source_path = Path('LetterBoxedCubed.user.js')
preview_path = Path('tools/preview_runtime.js')
tests_path = Path('tests/final-polish-tests.js')

source = source_path.read_text()
preview = preview_path.read_text()
tests = tests_path.read_text()

if '// @version      1.13.1-beta.33' in source:
    print('beta.33 already applied')
    raise SystemExit(0)

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 match, found {count}')
    return text.replace(old, new, 1)

source = replace_once(
    source,
    '// @version      1.13.1-beta.32',
    '// @version      1.13.1-beta.33',
    'version'
)

source = replace_once(
    source,
    '''            #help-dialog {
                z-index: 100050 !important;
            }
''',
    '''            /* The Help menu's own huge z-index is trapped inside NYT's
             * toolbar stacking context (native z-index: 3). Lift that context
             * above LBC only while the menu is actually open. */
            [class*="Game-module_toolbarContainer__"]:has(#help-dialog) {
                z-index: 100 !important;
            }

            #help-dialog {
                z-index: 100050 !important;
            }
''',
    'help stacking context'
)

source = replace_once(
    source,
    '''            .lb-cubed-longest-ticker {
                width: 100%;
                min-width: 0;
                overflow-x: auto;
''',
    '''            .lb-cubed-longest-ticker {
                width: 100%;
                min-width: 0;
                overflow-x: auto;
                cursor: ew-resize;
''',
    'ticker cursor'
)

source = replace_once(
    source,
    '''        let HoldUntil = performance.now() + 900;
        const SpeedPixelsPerSecond = 16;
''',
    '''        let HoldUntil = performance.now() + 900;
        let Position = Viewport.scrollLeft;
        const SpeedPixelsPerSecond = 16;
''',
    'ticker position accumulator'
)

source = replace_once(
    source,
    '''        Viewport.addEventListener("pointerleave", () => {
            Paused = false;
            LastTimestamp = null;
        });
''',
    '''        Viewport.addEventListener("pointerleave", () => {
            Paused = false;
            Position = Viewport.scrollLeft;
            LastTimestamp = null;
        });
''',
    'ticker pointerleave sync'
)

source = replace_once(
    source,
    '''            if (Maximum <= 1) {
                Viewport.scrollLeft = 0;
                LastTimestamp = Timestamp;
''',
    '''            if (Maximum <= 1) {
                Position = 0;
                Viewport.scrollLeft = 0;
                LastTimestamp = Timestamp;
''',
    'ticker zero overflow reset'
)

source = replace_once(
    source,
    '''            let Next =
                Viewport.scrollLeft +
                Direction * SpeedPixelsPerSecond * (DeltaMs / 1000);
''',
    '''            let Next =
                Position +
                Direction * SpeedPixelsPerSecond * (DeltaMs / 1000);
''',
    'ticker accumulated position'
)

source = replace_once(
    source,
    '''            Viewport.scrollLeft = Next;
            requestAnimationFrame(Tick);
''',
    '''            Position = Next;
            Viewport.scrollLeft = Position;
            requestAnimationFrame(Tick);
''',
    'ticker apply accumulated position'
)

old_input = '''        LongestInput.addEventListener("input", () => {
            const Sanitized = SanitizePreviewLongestWordsTestValue(LongestInput.value);
            if (LongestInput.value !== Sanitized) {
                LongestInput.value = Sanitized;
            }
            PreviewLongestWordsTestValue = Sanitized;
            EnsurePreviewTestBedsObserver();
            ApplyPreviewLongestWordsTest();
        });
'''
new_input = '''        ["keydown", "keyup", "keypress", "beforeinput"].forEach(Type => {
            LongestInput.addEventListener(Type, Event => {
                Event.stopPropagation();
            });
        });
        LongestInput.addEventListener("input", Event => {
            Event.stopPropagation();

            const Raw = LongestInput.value;
            const SelectionStart = LongestInput.selectionStart ?? Raw.length;
            const SelectionEnd = LongestInput.selectionEnd ?? SelectionStart;
            const Sanitized = SanitizePreviewLongestWordsTestValue(Raw);

            if (Raw !== Sanitized) {
                const SanitizedStart = SanitizePreviewLongestWordsTestValue(
                    Raw.slice(0, SelectionStart)
                ).length;
                const SanitizedEnd = SanitizePreviewLongestWordsTestValue(
                    Raw.slice(0, SelectionEnd)
                ).length;

                LongestInput.value = Sanitized;
                LongestInput.setSelectionRange(SanitizedStart, SanitizedEnd);
            }

            PreviewLongestWordsTestValue = Sanitized;
            EnsurePreviewTestBedsObserver();
            ApplyPreviewLongestWordsTest();
        });
'''
preview = replace_once(preview, old_input, new_input, 'normal editable Test Beds input')

tests = replace_once(
    tests,
    "assert(source.includes('// @version      1.13.1-beta.32'), 'beta.32 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.33'), 'beta.33 version missing');",
    'test version'
)

marker = "console.log('PASS: beta.31 Hints full-height fill static checks');"
if marker not in tests:
    raise SystemExit('beta.31 test marker missing')

tests = tests.replace(
    marker,
    marker + '''\n\n// beta.33: Help stacking-context lift + robust ticker motion/test input.\nassert(source.includes('[class*="Game-module_toolbarContainer__"]:has(#help-dialog)'), 'Help toolbar stacking-context lift missing');\nassert(source.includes('cursor: ew-resize;'), 'Longest Found horizontal cursor missing');\nassert(source.includes('let Position = Viewport.scrollLeft;'), 'ticker floating position accumulator missing');\nassert(source.includes('Position = Next;'), 'ticker does not persist fractional progress');\nassert(preview.includes('LongestInput.setSelectionRange(SanitizedStart, SanitizedEnd);'), 'Test Beds input caret preservation missing');\nassert(preview.includes('["keydown", "keyup", "keypress", "beforeinput"]'), 'Test Beds input key propagation guard missing');\n\nconsole.log('PASS: beta.33 Help/ticker/Test Beds static checks');''',
    1
)

source_path.write_text(source)
preview_path.write_text(preview)
tests_path.write_text(tests)
