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
    "// @version      1.13.1-beta.13",
    "// @version      1.13.1-beta.14",
    "version"
)

source = replace_once(
    source,
    '            Proxy.className = "lb-cubed-valid-feedback-proxy";',
    '            Proxy.className =\n                "lb-message-box success-message lb-cubed-valid-feedback-proxy";',
    "native toast classes"
)

old_css = '''            /*
                Cubed owns the relocated valid-word toast completely. Keeping
                NYT's transient success-message classes on the clone proved
                fragile because their animation lifecycle can leave the clone
                clipped/transparent even after the native source becomes
                visible. Use a small theme-aware Cubed surface instead while
                retaining the hidden NYT node only as the lifecycle source.
            */
            .lb-cubed-valid-feedback-proxy {
                position: absolute !important;
                right: auto !important;
                bottom: auto !important;
                min-width: 72px;
                max-width: min(260px, calc(100vw - 24px));
                margin: 0 !important;
                padding: 5px 10px;
                transform: none !important;
                visibility: visible !important;
                display: block !important;
                opacity: 1 !important;
                clip-path: none !important;
                filter: none !important;
                z-index: 60 !important;
                pointer-events: none !important;
                animation: none !important;
                transition: none !important;
                background:
                    color-mix(
                        in srgb,
                        var(--lb-cubed-lb-text, #111111) 10%,
                        var(--lb-cubed-lb-surface, #FFFFFF)
                    ) !important;
                color: var(--lb-cubed-lb-text, #111111) !important;
                border: 1px solid
                    color-mix(
                        in srgb,
                        var(--lb-cubed-lb-border, #000000) 75%,
                        transparent
                    ) !important;
                border-radius: 4px;
                box-shadow: 0 2px 7px rgba(0, 0, 0, 0.16);
                font: 700 12px/1.25 Arial, Helvetica, sans-serif;
                text-align: center;
                text-shadow: none !important;
                white-space: nowrap;
            }
'''
new_css = '''            /*
                Cubed owns praise timing and placement, but NYT still owns its
                presentation. Reuse the native lb-message-box/success-message
                classes so padding, type, sizing and shape remain indistinguish-
                able from Letter Boxed. Only the transient animation state is
                neutralized, because Cubed's captured lifecycle outlives NYT's
                native node in dark mode.
            */
            .lb-cubed-valid-feedback-proxy {
                position: absolute !important;
                right: auto !important;
                bottom: auto !important;
                margin: 0 !important;
                transform: none !important;
                visibility: visible !important;
                display: block !important;
                opacity: 1 !important;
                clip-path: none !important;
                filter: none !important;
                z-index: 60 !important;
                pointer-events: none !important;
                animation: none !important;
                transition: none !important;
            }

            /* Theme only the colors; leave native toast geometry/typography. */
            html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy,
            html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy * {
                color: var(--lb-cubed-lb-text) !important;
                fill: currentColor !important;
                text-shadow: none !important;
            }
'''
source = replace_once(source, old_css, new_css, "native toast presentation")

old_schedule = '''    function ScheduleDarkBoardCanvasRepairs() {
        if (
            !document.documentElement?.classList.contains(
                "lb-cubed-board-inverted"
            )
        ) {
            return;
        }

        requestAnimationFrame(RepairDarkBoardCanvas);

        for (const Delay of [0, 40, 100, 250, 500, 1000]) {
            setTimeout(RepairDarkBoardCanvas, Delay);
        }
    }
'''
new_schedule = '''    function ScheduleDarkBoardCanvasRepairs() {
        if (
            !document.documentElement?.classList.contains(
                "lb-cubed-board-inverted"
            )
        ) {
            return;
        }

        /*
            One immediate repair is enough for an already-painted board. Theme
            transitions that change inversion mode reload the page, and the
            canvas text hook handles all later NYT redraws. Repeated full-bitmap
            scans are deliberately avoided because getImageData + a pixel walk
            can monopolize the main thread on older hardware.
        */
        requestAnimationFrame(RepairDarkBoardCanvas);
    }
'''
source = replace_once(source, old_schedule, new_schedule, "dark board repair schedule")

old_scans = '''    function QueuePostSubmissionScans() {
        for (const Delay of [0, 40, 100, 250, 500]) {
            setTimeout(() => {
                ScanGameState();
                RepairDarkBoardCanvas();
            }, Delay);
        }
    }
'''
new_scans = '''    function QueuePostSubmissionScans() {
        for (const Delay of [0, 40, 100, 250, 500]) {
            setTimeout(ScanGameState, Delay);
        }
    }
'''
source = replace_once(source, old_scans, new_scans, "post-submission bitmap rescans")
SOURCE.write_text(source, encoding="utf-8")


tests = TESTS.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    "assert(source.includes('// @version      1.13.1-beta.13'), 'beta.13 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.14'), 'beta.14 version missing');",
    "test version"
)
tests = replace_once(
    tests,
    "assert(source.includes('Proxy.className = \"lb-cubed-valid-feedback-proxy\"'), 'self-owned valid-word toast proxy missing');",
    "assert(source.includes('lb-message-box success-message lb-cubed-valid-feedback-proxy'), 'valid-word toast no longer reuses native NYT styling classes');",
    "toast class test"
)
anchor = "assert(source.includes('Proxy.textContent = MessageText'), 'valid-word toast does not preserve captured praise text');\n"
if "post-submission path still performs expensive canvas bitmap repair" not in tests:
    tests = replace_once(
        tests,
        anchor,
        anchor +
        "assert(!source.includes('ScanGameState();\\n                RepairDarkBoardCanvas();'), 'post-submission path still performs expensive canvas bitmap repair');\n" +
        "assert(source.includes('Repeated full-bitmap'), 'dark board repair performance rationale missing');\n",
        "dark board performance tests"
    )
TESTS.write_text(tests, encoding="utf-8")
