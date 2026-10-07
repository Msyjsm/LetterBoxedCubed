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
    "// @version      1.13.1-beta.15",
    "// @version      1.13.1-beta.16",
    "version"
)

source = replace_once(
    source,
    '''            html.lb-cubed-native-theme .lb-game-container {
                --text: var(--lb-cubed-lb-fg);
            }
''',
    '''            /*
                Keep NYT's canvas SOURCE palette native even when the visible
                theme foreground is light. NYT resolves inactive GB letter
                paint from the game-level --text token, not reliably from the
                square container. Feeding the themed foreground here caused
                Dark mode to draw white source glyphs; the affine matrix then
                correctly mapped source white -> Board, making those letters
                disappear. DOM text/caret/rule colors are styled explicitly,
                so the renderer-facing source token can stay native black.
            */
            html.lb-cubed-board-themed .lb-game-container {
                --text: #000000 !important;
            }
''',
    "native canvas source text token"
)

source = replace_once(
    source,
    '''            /* Theme only the colors; leave native toast geometry/typography. */
            html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy,
            html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy * {
                color: var(--lb-cubed-lb-text) !important;
                fill: currentColor !important;
                text-shadow: none !important;
            }
''',
    '''            /*
                Theme transient validation/praise as one semantic LB surface:
                Foreground (active) is the toast body; Board is its readable
                foreground. Keep NYT's native toast geometry/typography.
                Invalid messages live in the text-field wrapper; valid praise
                uses Cubed's lifecycle proxy.
            */
            html.lb-cubed-native-theme .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-message-box,
            html.lb-cubed-native-theme .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-par:not(.no-words),
            html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy {
                background-color: var(--lb-cubed-lb-active) !important;
                color: var(--lb-cubed-lb-board) !important;
                border-color: var(--lb-cubed-lb-active) !important;
                text-shadow: none !important;
            }

            html.lb-cubed-native-theme .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-message-box *,
            html.lb-cubed-native-theme .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-par:not(.no-words) *,
            html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy * {
                color: var(--lb-cubed-lb-board) !important;
                fill: currentColor !important;
                text-shadow: none !important;
            }
''',
    "toast semantic colors"
)

SOURCE.write_text(source, encoding="utf-8")

tests = TESTS.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    "assert(source.includes('// @version      1.13.1-beta.15'), 'beta.15 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.16'), 'beta.16 version missing');",
    "test version"
)
anchor = "assert(source.includes('filter: url(#lb-cubed-board-theme-filter)'), 'semantic board filter CSS missing');\n"
additions = (
    "assert(source.includes('html.lb-cubed-board-themed .lb-game-container'), 'game-level native source color guard missing');\n"
    "assert(source.includes('--text: #000000 !important;'), 'inactive GB letter source normalization missing');\n"
    "assert(source.includes('background-color: var(--lb-cubed-lb-active) !important;'), 'active-color toast background missing');\n"
    "assert(source.includes('color: var(--lb-cubed-lb-board) !important;'), 'board-color toast foreground missing');\n"
    "assert(source.includes('> .lb-par:not(.no-words)'), 'validation-message semantic toast selector missing');\n"
)
if "inactive GB letter source normalization missing" not in tests:
    tests = replace_once(tests, anchor, anchor + additions, "theme follow-up tests")
TESTS.write_text(tests, encoding="utf-8")
