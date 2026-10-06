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
    "// @version      1.13.1-beta.10",
    "// @version      1.13.1-beta.11",
    "version",
)

old_entry = '''            html.lb-cubed-native-theme .lb-text-field {
                border-color: var(--lb-cubed-lb-text) !important;
                border-bottom-color: var(--lb-cubed-lb-text) !important;
            }

            html.lb-cubed-native-theme .lb-text-field::before,
'''
new_entry = '''            html.lb-cubed-native-theme .lb-text-field {
                border-color: var(--lb-cubed-lb-text) !important;
                border-bottom-color: var(--lb-cubed-lb-text) !important;
            }

            /*
                NYT's visible entry rule is not reliably the text field's own
                border. Guarantee the themed underline without changing layout
                by painting it as an inset edge on the existing wrapper. This
                also survives the dark-mode page reload used for board themes.
            */
            html.lb-cubed-native-theme .lb-text-field-wrapper {
                box-shadow:
                    inset 0 -2px 0 var(--lb-cubed-lb-text) !important;
            }

            html.lb-cubed-native-theme .lb-text-field::before,
'''
source = replace_once(source, old_entry, new_entry, "word-entry underline")

old_proxy = '''            .lb-cubed-valid-feedback-proxy {
                position: absolute !important;
                right: auto !important;
                bottom: auto !important;
                margin: 0 !important;
                transform: none !important;
                visibility: visible !important;
                display: block !important;
                z-index: 60 !important;
                pointer-events: none !important;
            }
'''
new_proxy = '''            .lb-cubed-valid-feedback-proxy {
                position: absolute !important;
                right: auto !important;
                bottom: auto !important;
                margin: 0 !important;
                transform: none !important;
                visibility: visible !important;
                display: block !important;
                z-index: 60 !important;
                pointer-events: none !important;
            }

            /*
                Cubed mirrors NYT's valid-word toast into an independently
                positioned proxy. In dark mode that proxy must not inherit the
                native success-message animation's transient opacity/clip state
                or child colors. The native source still owns the lifecycle;
                the proxy only needs to remain visibly styled while that source
                exists.
            */
            html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy {
                opacity: 1 !important;
                visibility: visible !important;
                clip-path: none !important;
                filter: none !important;
                animation: none !important;
                transition: none !important;
                background:
                    color-mix(
                        in srgb,
                        var(--lb-cubed-lb-text) 10%,
                        var(--lb-cubed-lb-surface)
                    ) !important;
                color: var(--lb-cubed-lb-text) !important;
                border: 1px solid
                    color-mix(
                        in srgb,
                        var(--lb-cubed-lb-border) 75%,
                        transparent
                    ) !important;
            }

            html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy,
            html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy * {
                color: var(--lb-cubed-lb-text) !important;
                fill: currentColor !important;
                text-shadow: none !important;
            }
'''
source = replace_once(source, old_proxy, new_proxy, "dark valid-word proxy")
SOURCE.write_text(source, encoding="utf-8")

tests = TESTS.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    "assert(source.includes('// @version      1.13.1-beta.10'), 'beta.10 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.11'), 'beta.11 version missing');",
    "test version",
)
anchor = "assert(source.includes('caret-color: var(--lb-cubed-lb-text)'), 'dark text-entry caret styling missing');\n"
checks = (
    "assert(source.includes('inset 0 -2px 0 var(--lb-cubed-lb-text)'), 'dark text-entry underline guarantee missing');\n"
    "assert(source.includes('html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy'), 'dark valid-word toast theme override missing');\n"
    "assert(source.includes('clip-path: none !important;'), 'dark valid-word toast clipping reset missing');\n"
)
if "dark text-entry underline guarantee missing" not in tests:
    tests = replace_once(tests, anchor, anchor + checks, "dark UI regression checks")
TESTS.write_text(tests, encoding="utf-8")
