from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "LetterBoxedCubed.user.js"
CHANGELOG = ROOT / "CHANGELOG.md"
DOCS = ROOT / "docs" / "PREVIEW_TESTING.md"


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


def replace_count(text, old, new, expected, label):
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} occurrences, found {count}")
    return text.replace(old, new)


def replace_regex_once(text, pattern, replacement, label):
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 regex match, found {count}")
    return updated


source = SOURCE.read_text(encoding="utf-8")
changelog = CHANGELOG.read_text(encoding="utf-8")
docs = DOCS.read_text(encoding="utf-8")

source = replace_once(
    source,
    "// @version      1.12.0-beta.11",
    "// @version      1.12.0-beta.12",
    "version",
)

source = replace_once(
    source,
    "// @grant        GM_setValue\n// @grant        GM_listValues",
    "// @grant        GM_setValue\n// @grant        GM_info\n// @grant        GM_listValues",
    "GM_info grant",
)

source = replace_once(
    source,
    '    const PreviewDebugToggleButtonId = "lb-cubed-preview-debug-toggle";\n',
    '    const PreviewDebugToggleButtonId = "lb-cubed-preview-debug-toggle";\n'
    '    const PreviewVersionLabelId = "lb-cubed-preview-version";\n',
    "preview version label id",
)

source = replace_once(
    source,
    "    const ResizeGripLineOffset =\n"
    "        (ResizeHandleWidth / 2) + RightResizeHandleGap;\n",
    "    const ResizeGripLineOffset =\n"
    "        (ResizeHandleWidth / 2) + RightResizeHandleGap;\n"
    "    const TiGbGripGutter = ResizeGripLineOffset * 2;\n",
    "TI/GB grip gutter constant",
)

source = replace_once(
    source,
    "        CreatePanel();\n"
    "        CreatePreviewDebugPane();\n",
    "        CreatePanel();\n"
    "        CreatePreviewDebugPane();\n"
    "        CreatePreviewVersionLabel();\n",
    "preview version label initialization",
)

source = replace_once(
    source,
    "        PositionPreviewDebugPane();\n"
    "        QueueValidWordFeedbackPlacement();\n",
    "        PositionPreviewDebugPane();\n"
    "        PositionPreviewVersionLabel();\n"
    "        QueueValidWordFeedbackPlacement();\n",
    "preview version layout positioning",
)

source = replace_once(
    source,
    "        requestAnimationFrame(PositionPreviewDebugPane);\n",
    "        requestAnimationFrame(() => {\n"
    "            PositionPreviewDebugPane();\n"
    "            PositionPreviewVersionLabel();\n"
    "        });\n",
    "post-render preview overlays",
)

source = replace_regex_once(
    source,
    r"    function UpdateHistoryLaneGeometry\(GameContainer, WordContainer\) \{.*?\n    \}\n\n    function StartLayoutObserver\(\)",
    '''    function UpdateHistoryLaneGeometry(GameContainer, WordContainer) {
        const TextFieldWrapper = WordContainer?.querySelector(
            ":scope > .lb-text-field-wrapper"
        );

        if (!GameContainer || !WordContainer || !TextFieldWrapper) {
            return;
        }

        const InputHeight = Math.max(
            1,
            Math.ceil(TextFieldWrapper.getBoundingClientRect().height)
        );
        const HistoryLaneHeight = Math.round(
            Clamp(
                LayoutGapPx,
                MinimumHistoryLaneHeight,
                MaximumHistoryLaneHeight
            )
        );
        const WordStyle = getComputedStyle(WordContainer);
        const WordMarginTop = Math.max(
            0,
            Number.parseFloat(WordStyle.marginTop) || 0
        );
        const WordMarginBottom = Math.max(
            0,
            Number.parseFloat(WordStyle.marginBottom) || 0
        );
        const WordAreaHeight = InputHeight + HistoryLaneHeight;

        /*
            NYT vertically offsets the TI with a native top margin. Because TI
            and GB are now separate rows in Cubed's grid, that margin has to be
            part of the ROW TRACK height as well as the rendered TI position.
            Otherwise the TI overflows its own row and the following GB row
            begins underneath the visible word history. The geometry dumps made
            this measurable: the missing amount was exactly the TI margin.
        */
        const WordGridTrackHeight = Math.ceil(
            WordMarginTop + WordAreaHeight + WordMarginBottom
        );

        GameContainer.style.setProperty(
            "--lb-cubed-history-lane-height",
            `${HistoryLaneHeight}px`
        );
        GameContainer.style.setProperty(
            "--lb-cubed-word-area-height",
            `${WordAreaHeight}px`
        );
        GameContainer.style.setProperty(
            "--lb-cubed-word-grid-track-height",
            `${WordGridTrackHeight}px`
        );
    }

    function StartLayoutObserver()''',
    "history lane/grid track geometry",
)

source = replace_count(
    source,
    '        GameContainer.style.setProperty(\n'
    '            "--lb-cubed-left-column-gap",\n'
    '            "0px"\n'
    '        );',
    '        GameContainer.style.setProperty(\n'
    '            "--lb-cubed-left-column-gap",\n'
    '            `${TiGbGripGutter}px`\n'
    '        );',
    2,
    "fixed TI/GB grip gutter",
)

source = replace_count(
    source,
    "                grid-template-rows:\n"
    "                    var(--lb-cubed-word-area-height, auto)",
    "                grid-template-rows:\n"
    "                    var(--lb-cubed-word-grid-track-height, auto)",
    2,
    "grid row uses margin-aware track height",
)

source = replace_once(
    source,
    "                overflow-x: hidden !important;\n"
    "                overflow-y: auto !important;\n"
    "                scrollbar-width: thin;\n",
    "                overflow-x: hidden !important;\n"
    "                overflow-y: auto !important;\n"
    "                pointer-events: auto !important;\n"
    "                scrollbar-width: thin;\n",
    "history scrollbar pointer events",
)

source = replace_regex_once(
    source,
    r"    function PositionLayoutGapResizeHandle\(\) \{.*?\n    \}\n\n    function StartLayoutGapResizeBehavior\(\)",
    '''    function PositionLayoutGapResizeHandle() {
        const GameContainer = document.querySelector(".lb-game-container");
        const WordContainer = GameContainer?.querySelector(".lb-word-container");
        const SquareContainer = GameContainer?.querySelector(".lb-square-container");
        const Handle = document.getElementById(LayoutGapHandleId);

        if (!GameContainer || !WordContainer || !SquareContainer || !Handle || !AdjustLayoutGap) {
            return;
        }

        requestAnimationFrame(() => {
            if (!AdjustLayoutGap || !Handle.isConnected) {
                return;
            }

            const GameRect = GameContainer.getBoundingClientRect();
            const WordRect = WordContainer.getBoundingClientRect();
            const SquareRect = SquareContainer.getBoundingClientRect();

            const Left = Math.max(
                0,
                Math.min(WordRect.left, SquareRect.left) - GameRect.left
            );
            const Right = Math.min(
                GameRect.width,
                Math.max(WordRect.right, SquareRect.right) - GameRect.left
            );

            /*
                The grid reserves a gutter exactly twice the normal external
                grip offset. Put the visible line one offset ABOVE GB, which
                centers it between the history lane and the first GB pixels.
            */
            const GripLineY =
                SquareRect.top -
                ResizeGripLineOffset -
                GameRect.top;

            Handle.style.left = `${Math.round(Left)}px`;
            Handle.style.width = `${Math.max(24, Math.round(Right - Left))}px`;
            Handle.style.top = `${Math.round(GripLineY - 5)}px`;
        });
    }

    function StartLayoutGapResizeBehavior()''',
    "grip placement",
)

source = replace_once(
    source,
    '            Proxy.className =\n'
    '                "lb-message-box lb-cubed-valid-feedback-proxy";\n',
    '            Proxy.className =\n'
    '                "lb-message-box success-message lb-cubed-valid-feedback-proxy";\n',
    "success proxy classes",
)

source = replace_once(
    source,
    '''            .lb-cubed-valid-feedback-proxy {
                z-index: 5 !important;
                pointer-events: none !important;
            }
''',
    '''            .lb-cubed-valid-feedback-proxy {
                position: absolute !important;
                left: 50% !important;
                right: auto !important;
                top: auto !important;
                bottom: calc(100% + 8px) !important;
                margin: 0 !important;
                transform: translateX(-50%) !important;
                z-index: 5 !important;
                pointer-events: none !important;
            }
''',
    "success proxy placement",
)

source = replace_once(
    source,
    '''            #${PreviewDebugToggleButtonId} {
''',
    '''            #${PreviewVersionLabelId} {
                position: fixed;
                z-index: 99999;
                color: rgba(92, 92, 92, 0.78);
                font: 10px/1.2 Consolas, "Courier New", monospace;
                white-space: nowrap;
                pointer-events: none;
                user-select: none;
            }

            #${PreviewDebugToggleButtonId} {
''',
    "preview version label style",
)

source = replace_once(
    source,
    "    function CreatePreviewDebugPane() {\n",
    '''    function GetRunningUserscriptVersion() {
        try {
            if (typeof GM_info !== "undefined") {
                const Version = String(GM_info?.script?.version || "").trim();
                if (Version) {
                    return Version;
                }
            }
        } catch {}

        return "preview";
    }

    function CreatePreviewVersionLabel() {
        if (
            UserscriptBuildChannel !== "preview" ||
            document.getElementById(PreviewVersionLabelId)
        ) {
            return;
        }

        EnsurePreviewDebugStyles();

        const Label = document.createElement("div");
        Label.id = PreviewVersionLabelId;
        Label.textContent = GetRunningUserscriptVersion();
        document.body.appendChild(Label);
        PositionPreviewVersionLabel();
    }

    function PositionPreviewVersionLabel() {
        if (UserscriptBuildChannel !== "preview") {
            return;
        }

        const Label = document.getElementById(PreviewVersionLabelId);
        const Panel = document.getElementById(PanelId);
        const Logo = document.querySelector(".lb-cubed-logo-placeholder");

        if (!Label || !Panel) {
            return;
        }

        const PanelRect = Panel.getBoundingClientRect();
        const LogoRect = Logo?.getBoundingClientRect();
        const LabelHeight = Math.max(1, Label.offsetHeight);
        const Left = Clamp(
            LogoRect?.left ?? (PanelRect.left + 12),
            4,
            Math.max(4, window.innerWidth - Label.offsetWidth - 4)
        );
        const Top = Math.max(
            2,
            PanelRect.top - LabelHeight - 4
        );

        Label.style.left = `${Math.round(Left)}px`;
        Label.style.top = `${Math.round(Top)}px`;
    }

    function CreatePreviewDebugPane() {
''',
    "preview version label functions",
)

source = replace_once(
    source,
    '''        const DriveStatus = document.createElement("span");
        DriveStatus.id = GoogleDriveStatusId;
        DriveStatus.className = "lb-cubed-drive-status";

        const TitleRow = document.createElement("div");
        TitleRow.className = "lb-cubed-title-row";
        TitleRow.append(LogoPlaceholder, DriveStatus);

        const Subtitle = document.createElement("div");
        Subtitle.className = "lb-cubed-subtitle";
        Subtitle.textContent =
            GameData.date ||
            GameData.printDate ||
            "Today's Letter Boxed";

        const HeaderText = document.createElement("div");
        HeaderText.className = "lb-cubed-header-text";
        HeaderText.append(TitleRow, Subtitle);
''',
    '''        const DriveStatus = document.createElement("span");
        DriveStatus.id = GoogleDriveStatusId;
        DriveStatus.className = "lb-cubed-drive-status";

        const Subtitle = document.createElement("div");
        Subtitle.className = "lb-cubed-subtitle";
        Subtitle.textContent =
            GameData.date ||
            GameData.printDate ||
            "Today's Letter Boxed";

        const TitleMeta = document.createElement("div");
        TitleMeta.className = "lb-cubed-title-meta";
        TitleMeta.append(DriveStatus, Subtitle);

        const TitleRow = document.createElement("div");
        TitleRow.className = "lb-cubed-title-row";
        TitleRow.append(LogoPlaceholder, TitleMeta);

        const HeaderText = document.createElement("div");
        HeaderText.className = "lb-cubed-header-text";
        HeaderText.append(TitleRow);
''',
    "header date/status structure",
)

source = replace_once(
    source,
    '''            .lb-cubed-title-row {
                display: flex;
                align-items: baseline;
                gap: 8px;
                min-width: 0;
            }

            .lb-cubed-drive-status {
''',
    '''            .lb-cubed-title-row {
                display: flex;
                align-items: flex-start;
                gap: 8px;
                min-width: 0;
            }

            .lb-cubed-title-meta {
                display: flex;
                flex-direction: column;
                align-items: flex-start;
                min-width: 0;
            }

            .lb-cubed-drive-status {
''',
    "header meta style",
)

source = replace_once(
    source,
    '''            .lb-cubed-subtitle {
                margin-top: 3px;
''',
    '''            .lb-cubed-subtitle {
                margin-top: 2px;
''',
    "date spacing",
)

# Documentation.
changelog = replace_once(
    changelog,
    "# Changelog\n\n",
    '''# Changelog

## 1.12.0-beta.12
- Corrected the TI/GB grid track to include NYT's native TI top/bottom margins. The four geometry dumps showed that the board/history overlap was exactly the uncounted TI margin, so GB now begins after the visible TI rather than after its smaller nominal grid row.
- Added a fixed 22px TI/GB grip gutter derived from the existing 11px grip-line offset, centering the horizontal grip between the history lane and GB instead of placing it inside either region.
- Restored direct pointer interaction on the accepted-word history scroller, whose computed `pointer-events: none` was preventing scrollbar dragging/wheel targeting.
- Preserved the `success-message` class on relocated valid-word feedback and gave its proxy an explicit above-input position instead of relying on NYT's parent-dependent absolute positioning.
- Preview builds now show their exact runtime version in gray just above LBC, left-aligned with the logo placeholder. The header date now sits directly below Drive sync status beside the logo.

''',
    "beta.12 changelog",
)

docs = replace_once(
    docs,
    "The current source is `1.12.0-beta.11`.",
    "The current source is `1.12.0-beta.12`.",
    "preview docs version",
)

docs = replace_once(
    docs,
    '''- `.lb-list-container` is now an exact-height scroll viewport matching the reserved history lane rather than a flex-inferred remainder. Accepted-word history must scroll inside that lane before it can visually enter GB territory; GB remains fixed. Cubed also neutralizes NYT's native top/bottom margin on `.lb-square-container`, so the GB canvas can no longer be pulled upward across that lane or intercept its scrollbar; the draggable grip is positioned just below the lane.
''',
    '''- `.lb-list-container` is an exact-height scroll viewport matching the reserved history lane. Cubed explicitly re-enables pointer events on that scroller, and the TI grid track includes NYT's native TI top/bottom margins so the following GB row starts after the *rendered* TI rather than underneath it. A fixed 22px structural gutter sits between history and GB; the draggable grip line is centered in that gutter.
''',
    "preview docs geometry bullet",
)

docs = replace_once(
    docs,
    '''- **Hide par** should hide only the actual `Try to solve in X words` prompt in both NYT DOM states. Invalid-submission feedback injected as `.lb-text-field-wrapper > .lb-message-box` (for example **Too short** and **Not in word list**) must remain visible and must not be clipped by the fixed TI/history lane. Valid-word praise remains native when it has room; if its square-container position would crowd visible history, Cubed temporarily mirrors it into the text-field wrapper so it occupies the same safe feedback region as invalid messages.
''',
    '''- **Hide par** should hide only the actual `Try to solve in X words` prompt in both NYT DOM states. Invalid-submission feedback injected as `.lb-text-field-wrapper > .lb-message-box` (for example **Too short** and **Not in word list**) must remain visible. Valid-word praise remains native when it has room; if it would crowd visible history, Cubed mirrors it as a `success-message` proxy explicitly positioned above the text-entry wrapper rather than inheriting NYT's square-container-relative coordinates.
''',
    "preview docs feedback bullet",
)

docs = replace_once(
    docs,
    '''- The temporary square logo placeholder must no longer collapse to 0x0 for one animation frame when a word is accepted. Its size measurement is synchronous and should not cause the visible LBC blink seen in beta.4.
''',
    '''- The temporary square logo placeholder must no longer collapse to 0x0 for one animation frame when a word is accepted. Its size measurement is synchronous and should not cause the visible LBC blink seen in beta.4. Preview builds show the exact `GM_info.script.version` in gray just above LBC, left-aligned with the logo; Drive status and the puzzle date form two lines beside the logo.
''',
    "preview docs header bullet",
)

# Guards for the intended architecture.
for needle, label in [
    ("// @version      1.12.0-beta.12", "version"),
    ("// @grant        GM_info", "GM_info"),
    ("const TiGbGripGutter = ResizeGripLineOffset * 2;", "grip gutter"),
    ("--lb-cubed-word-grid-track-height", "margin-aware grid track"),
    ("pointer-events: auto !important;", "history pointer events"),
    ("success-message lb-cubed-valid-feedback-proxy", "success proxy class"),
    ("bottom: calc(100% + 8px) !important;", "success proxy placement"),
    ("function CreatePreviewVersionLabel()", "preview version label"),
    ("TitleMeta.append(DriveStatus, Subtitle);", "header meta stack"),
]:
    if needle not in source:
        raise RuntimeError(f"missing guard: {label}")

SOURCE.write_text(source, encoding="utf-8")
CHANGELOG.write_text(changelog, encoding="utf-8")
DOCS.write_text(docs, encoding="utf-8")
print("beta.12 patch applied")
