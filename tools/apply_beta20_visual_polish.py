from pathlib import Path

SOURCE = Path("LetterBoxedCubed.user.js")
TESTS = Path("tests/final-polish-tests.js")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 match, found {count}")
    return text.replace(old, new, 1)


source = SOURCE.read_text(encoding="utf-8")
tests = TESTS.read_text(encoding="utf-8")

source = replace_once(
    source,
    "// @version      1.13.1-beta.19",
    "// @version      1.13.1-beta.20",
    "userscript version",
)

# The beta.19 tint/shade kept hue and saturation, but moved lightness too
# aggressively toward the pole. Keep the hue-preserving model while using a
# visibly related shade/tint rather than near-black/near-white text.
source = replace_once(
    source,
    '''        const TargetLightness = IsDark\n            ? 1 - (1 - Lightness) * 0.24\n            : Lightness * 0.24;''',
    '''        const TargetLightness = IsDark\n            ? Lightness + (1 - Lightness) * 0.55\n            : Lightness * 0.55;''',
    "NYT solution shade strength",
)

# A standards scrollbar-color declaration on the actual scrolling node wins
# over inherited/theme WebKit pseudo-element styling in current Chromium. Give
# the LBC scrollers the same semantic treatment as the page scrollbar:
# background track + foreground/text thumb/buttons.
scroll_anchor = '''            html.lb-cubed-native-theme::-webkit-scrollbar-thumb,\n            html.lb-cubed-native-theme *::-webkit-scrollbar-thumb,\n            html.lb-cubed-native-theme::-webkit-scrollbar-button,\n            html.lb-cubed-native-theme *::-webkit-scrollbar-button {\n                background: var(--lb-cubed-lb-fg);\n            }\n'''
scroll_block = scroll_anchor + '''\n            /* Mirror the page scrollbar inside LBC and its popovers/modals. */\n            #${PanelId},\n            #${PanelContentId},\n            .lb-cubed-settings-panel,\n            #${HistoryOverlayId},\n            .lb-cubed-history-modal {\n                scrollbar-width: thin;\n                scrollbar-color:\n                    var(--lb-cubed-lbc-text, #301818)\n                    var(--lb-cubed-lbc-bg, #D88482);\n            }\n\n            #${PanelId}::-webkit-scrollbar,\n            #${PanelContentId}::-webkit-scrollbar,\n            #${PanelId} *::-webkit-scrollbar,\n            .lb-cubed-settings-panel::-webkit-scrollbar,\n            .lb-cubed-settings-panel *::-webkit-scrollbar,\n            #${HistoryOverlayId}::-webkit-scrollbar,\n            #${HistoryOverlayId} *::-webkit-scrollbar,\n            .lb-cubed-history-modal::-webkit-scrollbar,\n            .lb-cubed-history-modal *::-webkit-scrollbar {\n                width: 8px;\n                height: 8px;\n            }\n\n            #${PanelId}::-webkit-scrollbar-track,\n            #${PanelContentId}::-webkit-scrollbar-track,\n            #${PanelId} *::-webkit-scrollbar-track,\n            .lb-cubed-settings-panel::-webkit-scrollbar-track,\n            .lb-cubed-settings-panel *::-webkit-scrollbar-track,\n            #${HistoryOverlayId}::-webkit-scrollbar-track,\n            #${HistoryOverlayId} *::-webkit-scrollbar-track,\n            .lb-cubed-history-modal::-webkit-scrollbar-track,\n            .lb-cubed-history-modal *::-webkit-scrollbar-track {\n                background: var(--lb-cubed-lbc-bg, #D88482);\n            }\n\n            #${PanelId}::-webkit-scrollbar-thumb,\n            #${PanelContentId}::-webkit-scrollbar-thumb,\n            #${PanelId} *::-webkit-scrollbar-thumb,\n            .lb-cubed-settings-panel::-webkit-scrollbar-thumb,\n            .lb-cubed-settings-panel *::-webkit-scrollbar-thumb,\n            #${HistoryOverlayId}::-webkit-scrollbar-thumb,\n            #${HistoryOverlayId} *::-webkit-scrollbar-thumb,\n            .lb-cubed-history-modal::-webkit-scrollbar-thumb,\n            .lb-cubed-history-modal *::-webkit-scrollbar-thumb,\n            #${PanelId}::-webkit-scrollbar-button,\n            #${PanelContentId}::-webkit-scrollbar-button,\n            #${PanelId} *::-webkit-scrollbar-button,\n            .lb-cubed-settings-panel::-webkit-scrollbar-button,\n            .lb-cubed-settings-panel *::-webkit-scrollbar-button,\n            #${HistoryOverlayId}::-webkit-scrollbar-button,\n            #${HistoryOverlayId} *::-webkit-scrollbar-button,\n            .lb-cubed-history-modal::-webkit-scrollbar-button,\n            .lb-cubed-history-modal *::-webkit-scrollbar-button {\n                background: var(--lb-cubed-lbc-text, #301818);\n            }\n'''
source = replace_once(source, scroll_anchor, scroll_block, "LBC scrollbar override insertion")

# The screenshot made the remaining GB mismatch concrete: the canvas path is
# using Foreground (active), while the current word-entry UI was still forced
# to neutral Foreground. Treat the current-entry UI as active interaction too.
entry_anchor = '''            html.lb-cubed-native-theme .lb-text-field-wrapper {\n                background-image: none !important;\n                box-shadow: none !important;\n            }\n'''
entry_block = entry_anchor + '''\n            /* Current word entry belongs to the same active semantic lane as the GB path. */\n            html.lb-cubed-native-theme .lb-text-field-label,\n            html.lb-cubed-native-theme .lb-text-field,\n            html.lb-cubed-native-theme .lb-text-field *,\n            html.lb-cubed-native-theme .lb-text-field-underline,\n            html.lb-cubed-native-theme .lb-text-field__caret,\n            html.lb-cubed-native-theme .lb-text-field__caret::before,\n            html.lb-cubed-native-theme .lb-text-field__caret::after {\n                color: var(--lb-cubed-lb-active) !important;\n                -webkit-text-fill-color: var(--lb-cubed-lb-active) !important;\n                caret-color: var(--lb-cubed-lb-active) !important;\n            }\n\n            html.lb-cubed-native-theme .lb-text-field-underline,\n            html.lb-cubed-native-theme .lb-text-field__caret,\n            html.lb-cubed-native-theme .lb-text-field__caret::before,\n            html.lb-cubed-native-theme .lb-text-field__caret::after {\n                background: var(--lb-cubed-lb-active) !important;\n                background-color: var(--lb-cubed-lb-active) !important;\n                border-color: var(--lb-cubed-lb-active) !important;\n                border-left-color: var(--lb-cubed-lb-active) !important;\n                border-right-color: var(--lb-cubed-lb-active) !important;\n                outline-color: var(--lb-cubed-lb-active) !important;\n            }\n'''
source = replace_once(source, entry_anchor, entry_block, "active word-entry semantic override")

# Force every visible NYT-solution descendant onto the derived solution shade.
# This removes generic twofer/LBC text rules from the computed cascade. The
# later redaction rule still wins for intentionally hidden words.
solution_anchor = '''            #${PanelId} .lb-cubed-nyt-solution-label {\n                display: inline-flex;\n                align-items: center;\n                gap: 3px;\n            }\n'''
solution_block = '''            #${PanelId} .lb-cubed-nyt-solution,\n            #${PanelId} .lb-cubed-nyt-solution * {\n                color: var(--lb-cubed-nyt-solution-text) !important;\n                -webkit-text-fill-color: var(--lb-cubed-nyt-solution-text) !important;\n            }\n\n            #${PanelId} .lb-cubed-nyt-solution {\n                border-color: color-mix(\n                    in srgb,\n                    var(--lb-cubed-nyt-solution-text) 52%,\n                    transparent\n                ) !important;\n            }\n\n            #${PanelId} .lb-cubed-nyt-solution .lb-cubed-twofer-revealed {\n                border-color: color-mix(\n                    in srgb,\n                    var(--lb-cubed-nyt-solution-text) 38%,\n                    transparent\n                ) !important;\n            }\n\n''' + solution_anchor
source = replace_once(source, solution_anchor, solution_block, "NYT solution descendant color override")

# Tests.
tests = replace_once(
    tests,
    "assert(source.includes('// @version      1.13.1-beta.19'), 'beta.19 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.20'), 'beta.20 version missing');",
    "test version",
)

insert_after = "assert(source.includes('scrollbar-color:'), 'theme-aware scrollbar styling missing');\n"
addition = "assert(source.includes('.lb-cubed-settings-panel,'), 'settings scrollbar root styling missing');\nassert(source.includes('var(--lb-cubed-lbc-bg, #D88482);'), 'LBC scrollbar track is not semantic background');\n"
if addition not in tests:
    if insert_after not in tests:
        raise RuntimeError("scrollbar test insertion point missing")
    tests = tests.replace(insert_after, insert_after + addition, 1)

insert_after = "assert(source.includes('const TargetLightness = IsDark'), 'NYT solution hue-preserving tint/shade derivation missing');\n"
addition = "assert(source.includes('Lightness * 0.55'), 'NYT solution shade is still too close to black/white');\nassert(source.includes('.lb-cubed-nyt-solution * {'), 'NYT solution descendants are not forced to the derived shade');\nassert(source.includes('-webkit-text-fill-color: var(--lb-cubed-nyt-solution-text)'), 'NYT solution text-fill override missing');\n"
if addition not in tests:
    if insert_after not in tests:
        raise RuntimeError("solution test insertion point missing")
    tests = tests.replace(insert_after, insert_after + addition, 1)

insert_after = "assert(source.includes('.lb-text-field__caret::before'), 'caret pseudo-element theming missing');\n"
addition = "assert(source.includes('color: var(--lb-cubed-lb-active) !important;'), 'current word-entry UI is not mapped to active foreground');\n"
if addition not in tests:
    if insert_after not in tests:
        raise RuntimeError("active-entry test insertion point missing")
    tests = tests.replace(insert_after, insert_after + addition, 1)

SOURCE.write_text(source, encoding="utf-8")
TESTS.write_text(tests, encoding="utf-8")
