from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "LetterBoxedCubed.user.js"
TEST_PATH = ROOT / "tests" / "final-polish-tests.js"
DOC_PATH = ROOT / "docs" / "THEMES.md"

source = SOURCE_PATH.read_text(encoding="utf-8")
tests = TEST_PATH.read_text(encoding="utf-8")
docs = DOC_PATH.read_text(encoding="utf-8")


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"{label}: anchor not found")
    return text.replace(old, new, 1)


source = replace_once(
    source,
    "// @version      1.13.1-beta.23",
    "// @version      1.13.1-beta.24",
    "version",
)

repair_function = r'''    function RepairBoardLetterSourceForThemeModeSwitch(WasDark, IsDark) {
        if (WasDark === IsDark) {
            return false;
        }

        const Canvas = document.querySelector(
            ".lb-game-container .lb-square-container canvas"
        );
        if (!Canvas || !Canvas.width || !Canvas.height) {
            return false;
        }

        const Context = Canvas.getContext("2d");
        if (!Context) {
            return false;
        }

        /*
            The trace in beta.23 proved that NYT does not redraw the canvas at
            all for our synthetic resize invalidation. Its next genuine game
            update redraws correctly, but until then the bitmap still contains
            the previous semantic mode's source glyph colors.

            Repair only the four outer letter-label bands. They contain the 12
            side letters but stop before the board square, so node/connector
            paints remain untouched. This is a one-time O(canvas pixels) pass
            only when crossing the Light/Dark semantic threshold; same-mode
            theme switches still stay filter-only.
        */
        const Width = Canvas.width;
        const Height = Canvas.height;
        const EdgeX = Math.floor(Width * 0.15);
        const EdgeY = Math.floor(Height * 0.15);
        let Image;
        try {
            Image = Context.getImageData(0, 0, Width, Height);
        } catch (Error) {
            console.debug(
                "[Letter Boxed Cubed] Could not repair board letter source pixels.",
                Error
            );
            return false;
        }

        const Pixels = Image.data;
        const Active = ThemeHexToRgb(NativeBoardActiveSourceColor);
        let ChangedPixels = 0;

        const IsNearBlack = (Red, Green, Blue) =>
            Math.max(Red, Green, Blue) <= 20;
        const IsNearWhite = (Red, Green, Blue) =>
            Math.min(Red, Green, Blue) >= 235;
        const IsNearActive = (Red, Green, Blue) =>
            Math.abs(Red - Active[0]) <= 24 &&
            Math.abs(Green - Active[1]) <= 24 &&
            Math.abs(Blue - Active[2]) <= 24;

        for (let Y = 0; Y < Height; Y++) {
            const InOuterY = Y < EdgeY || Y >= Height - EdgeY;
            for (let X = 0; X < Width; X++) {
                if (!InOuterY && X >= EdgeX && X < Width - EdgeX) {
                    continue;
                }

                const Offset = (Y * Width + X) * 4;
                if (Pixels[Offset + 3] <= 4) {
                    continue;
                }

                const Red = Pixels[Offset];
                const Green = Pixels[Offset + 1];
                const Blue = Pixels[Offset + 2];

                if (!WasDark && IsDark) {
                    if (IsNearWhite(Red, Green, Blue)) {
                        Pixels[Offset] = 0;
                        Pixels[Offset + 1] = 0;
                        Pixels[Offset + 2] = 0;
                        ChangedPixels++;
                    } else if (IsNearBlack(Red, Green, Blue)) {
                        Pixels[Offset] = Active[0];
                        Pixels[Offset + 1] = Active[1];
                        Pixels[Offset + 2] = Active[2];
                        ChangedPixels++;
                    }
                } else if (WasDark && !IsDark) {
                    if (IsNearActive(Red, Green, Blue)) {
                        Pixels[Offset] = 0;
                        Pixels[Offset + 1] = 0;
                        Pixels[Offset + 2] = 0;
                        ChangedPixels++;
                    } else if (IsNearBlack(Red, Green, Blue)) {
                        Pixels[Offset] = 255;
                        Pixels[Offset + 1] = 255;
                        Pixels[Offset + 2] = 255;
                        ChangedPixels++;
                    }
                }
            }
        }

        if (!ChangedPixels) {
            return false;
        }

        Context.putImageData(Image, 0, 0);
        return true;
    }

'''

source = replace_once(
    source,
    "    function QueueBoardThemeRendererRefresh(Force = false) {",
    repair_function + "    function QueueBoardThemeRendererRefresh(Force = false) {",
    "letter source repair insertion",
)

old_transition = '''        const ThemeModeChanged =
            WasBoardThemed &&
            WasDarkTheme !== LbSemantics.IsDark;

        Root.classList.toggle("lb-cubed-native-theme", ApplyNative);'''
new_transition = '''        const ThemeModeChanged =
            WasDarkTheme !== LbSemantics.IsDark &&
            (WasBoardThemed || ApplyNative);

        if (ThemeModeChanged) {
            RepairBoardLetterSourceForThemeModeSwitch(
                WasDarkTheme,
                LbSemantics.IsDark
            );
        }

        Root.classList.toggle("lb-cubed-native-theme", ApplyNative);'''
source = replace_once(
    source,
    old_transition,
    new_transition,
    "theme transition repair call",
)

# Tests: bump beta and pin the trace-backed repair behavior.
tests = replace_once(
    tests,
    "assert(source.includes('// @version      1.13.1-beta.23'), 'beta.23 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.24'), 'beta.24 version missing');",
    "test version",
)
tests = replace_once(
    tests,
    "assert(source.includes('const ThemeModeChanged ='), 'theme mode transition detection missing');",
    "assert(source.includes('const ThemeModeChanged ='), 'theme mode transition detection missing');\n"
    "assert(source.includes('function RepairBoardLetterSourceForThemeModeSwitch(WasDark, IsDark)'), 'cross-mode letter source repair missing');\n"
    "assert(source.includes('const EdgeX = Math.floor(Width * 0.15);'), 'letter-only perimeter guard missing');\n"
    "assert(source.includes('Context.getImageData(0, 0, Width, Height)'), 'letter source pixel read missing');\n"
    "assert(source.includes('Context.putImageData(Image, 0, 0);'), 'letter source pixel write missing');\n"
    "assert(source.includes('RepairBoardLetterSourceForThemeModeSwitch(\\n                WasDarkTheme,'), 'theme transition does not invoke letter repair');",
    "repair tests",
)
tests = replace_once(
    tests,
    "console.log('PASS: beta.23 theme refresh + toast static checks');",
    "console.log('PASS: beta.24 cross-mode letter repair + theme/toast static checks');",
    "test banner",
)

# Docs: make the deliberate, tiny bitmap exception explicit and update the
# acceptance sequence so cross-mode switching is tested without gameplay input.
docs = replace_once(
    docs,
    "Antialiased and blended pixels transform continuously between those anchors. LBC never walks or rewrites the completed bitmap.",
    "Antialiased and blended pixels transform continuously between those anchors. Normal rendering remains filter-only. The one deliberate exception is a Light/Dark semantic-mode switch: NYT does not repaint the canvas for synthetic resize events, so LBC performs a single bounded source-pixel repair in the four outer letter-label bands before swapping modes. The board square, nodes, and connectors are never touched by that repair, and same-mode theme switches do no bitmap work.",
    "docs bitmap semantics",
)
docs = replace_once(
    docs,
    "3. Switch native Light -> custom Light -> NYT Dark -> custom Dark -> native Light mid-puzzle.",
    "3. Switch native Light -> custom Light -> NYT Dark -> custom Dark -> native Light mid-puzzle without typing or submitting anything between switches; all 12 side letters must remain visible immediately.",
    "docs acceptance sequence",
)

SOURCE_PATH.write_text(source, encoding="utf-8")
TEST_PATH.write_text(tests, encoding="utf-8")
DOC_PATH.write_text(docs, encoding="utf-8")
