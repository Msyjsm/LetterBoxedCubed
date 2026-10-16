from pathlib import Path

source_path = Path('LetterBoxedCubed.user.js')
preview_path = Path('tools/preview_runtime.js')
tests_path = Path('tests/final-polish-tests.js')

source = source_path.read_text()
preview = preview_path.read_text()
tests = tests_path.read_text()

if '// @version      1.13.1-beta.34' in source:
    print('beta.34 already applied')
    raise SystemExit(0)


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 match, found {count}')
    return text.replace(old, new, 1)


source = replace_once(
    source,
    '// @version      1.13.1-beta.33',
    '// @version      1.13.1-beta.34',
    'version'
)

source = replace_once(
    source,
    '''    function ApplyRecentHighlight(Element, MapValue, Key) {\n''',
    '''    function QueueHighlightedElementScrollIntoView(Element) {\n        requestAnimationFrame(() => {\n            if (!(Element instanceof HTMLElement) || !Element.isConnected) {\n                return;\n            }\n\n            const ScrollHost = Element.closest(\n                ".lb-cubed-potential-word-list, " +\n                ".lb-cubed-twofer-body, " +\n                ".lb-cubed-length-grid, " +\n                ".lb-cubed-word-grid"\n            );\n\n            if (\n                !(ScrollHost instanceof HTMLElement) ||\n                ScrollHost.scrollHeight <= ScrollHost.clientHeight + 1\n            ) {\n                return;\n            }\n\n            const HostRect = ScrollHost.getBoundingClientRect();\n            const ElementRect = Element.getBoundingClientRect();\n            const Above = ElementRect.top - HostRect.top;\n            const Below = ElementRect.bottom - HostRect.bottom;\n\n            if (Above >= 0 && Below <= 0) {\n                return;\n            }\n\n            let TargetTop = ScrollHost.scrollTop;\n            if (Above < 0) {\n                TargetTop += Above;\n            } else if (Below > 0) {\n                TargetTop += Below;\n            }\n\n            const Maximum = Math.max(\n                0,\n                ScrollHost.scrollHeight - ScrollHost.clientHeight\n            );\n\n            ScrollHost.scrollTo({\n                top: Clamp(TargetTop, 0, Maximum),\n                behavior: "smooth"\n            });\n        });\n    }\n\n    function ApplyRecentHighlight(Element, MapValue, Key) {\n''',
    'highlight auto-scroll helper'
)

source = replace_once(
    source,
    '''        Element.style.setProperty(\n            "--lb-cubed-highlight-duration",\n            `${Math.max(1, Math.round(RemainingMs))}ms`\n        );\n\n        return true;\n''',
    '''        Element.style.setProperty(\n            "--lb-cubed-highlight-duration",\n            `${Math.max(1, Math.round(RemainingMs))}ms`\n        );\n        QueueHighlightedElementScrollIntoView(Element);\n\n        return true;\n''',
    'direct highlight auto-scroll'
)

source = replace_once(
    source,
    '''        Element.style.setProperty(\n            "--lb-cubed-highlight-duration",\n            `${Math.max(1, Math.round(LatestExpiry - Date.now()))}ms`\n        );\n\n        if (RecentWords.length) {\n''',
    '''        Element.style.setProperty(\n            "--lb-cubed-highlight-duration",\n            `${Math.max(1, Math.round(LatestExpiry - Date.now()))}ms`\n        );\n        QueueHighlightedElementScrollIntoView(Element);\n\n        if (RecentWords.length) {\n''',
    'length highlight auto-scroll'
)

source = replace_once(
    source,
    '''        Element.style.setProperty(\n            "--lb-cubed-highlight-duration",\n            `${Math.max(1, Math.round(LatestExpiry - Now))}ms`\n        );\n\n        return true;\n''',
    '''        Element.style.setProperty(\n            "--lb-cubed-highlight-duration",\n            `${Math.max(1, Math.round(LatestExpiry - Now))}ms`\n        );\n        QueueHighlightedElementScrollIntoView(Element);\n\n        return true;\n''',
    'group highlight auto-scroll'
)

preview = replace_once(
    preview,
    '''            #${PreviewHistoryTestPanelId} .lbc-longest-words-test-input {\n                width: 100%;\n                min-height: 30px;\n                padding: 4px 6px;\n                border: 1px solid #777;\n                border-radius: 3px;\n                background: #101014;\n                color: #fff;\n                font: 12px/1.3 Consolas, "Courier New", monospace;\n            }\n''',
    '''            #${PreviewHistoryTestPanelId} .lbc-longest-words-test-input {\n                width: 100%;\n                min-height: 30px;\n                padding: 4px 6px;\n                border: 1px solid #777;\n                border-radius: 3px;\n                background: #101014;\n                color: #fff;\n                font: 12px/1.3 Consolas, "Courier New", monospace;\n            }\n\n            #${PreviewHistoryTestPanelId} .lbc-longest-words-test-input::placeholder {\n                color: currentColor;\n                opacity: 0.55;\n                font-style: italic;\n            }\n''',
    'test bed placeholder styling'
)

preview = replace_once(
    preview,
    '        LongestInput.placeholder = "LONGESTWORD, ANOTHERTIEDWORD";',
    '        LongestInput.placeholder = "Enter a long string of text here";',
    'test bed placeholder text'
)

tests = replace_once(
    tests,
    "assert(source.includes('// @version      1.13.1-beta.33'), 'beta.33 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.34'), 'beta.34 version missing');",
    'test version'
)

marker = "console.log('PASS: beta.33 Help/ticker/Test Beds static checks');"
if marker not in tests:
    raise SystemExit('beta.33 test marker missing')

tests = tests.replace(
    marker,
    marker + '''\n\n// beta.34: Test Beds placeholder polish + reveal newly highlighted rows in their owned scrollports.\nassert(source.includes('function QueueHighlightedElementScrollIntoView(Element)'), 'highlight scroll helper missing');\nassert(source.includes('ScrollHost.scrollTo({'), 'highlight scroll action missing');\nassert(source.includes('behavior: "smooth"'), 'highlight scroll should be smooth');\nassert((source.match(/QueueHighlightedElementScrollIntoView\\(Element\\);/g) || []).length >= 3, 'not all recent highlight paths reveal their rows');\nassert(preview.includes('LongestInput.placeholder = "Enter a long string of text here";'), 'Longest Words placeholder text missing');\nassert(preview.includes('.lbc-longest-words-test-input::placeholder'), 'Longest Words placeholder styling missing');\nassert(preview.includes('font-style: italic;'), 'Longest Words placeholder italics missing');\nassert(preview.includes('opacity: 0.55;'), 'Longest Words placeholder dimming missing');\n\nconsole.log('PASS: beta.34 final scroll/placeholder static checks');''',
    1
)

source_path.write_text(source)
preview_path.write_text(preview)
tests_path.write_text(tests)
