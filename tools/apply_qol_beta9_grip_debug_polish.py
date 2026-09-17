from pathlib import Path

source = Path("LetterBoxedCubed.user.js")
text = source.read_text(encoding="utf-8")


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {count}")
    text = text.replace(old, new, 1)


replace_once(
    "// @version      1.12.0-beta.8",
    "// @version      1.12.0-beta.9",
    "version",
)

replace_once(
    """    const ResizeHandleWidth = 16;
    const RightResizeHandleGap = 3;""",
    """    const ResizeHandleWidth = 16;
    const RightResizeHandleGap = 3;
    const ResizeGripLineOffset =
        (ResizeHandleWidth / 2) + RightResizeHandleGap;""",
    "shared grip offset",
)

replace_once(
    """            const Midpoint =
                ((WordRect.bottom + SquareRect.top) / 2) -
                GameRect.top;

            Handle.style.left = `${Math.round(Left)}px`;
            Handle.style.width = `${Math.max(24, Math.round(Right - Left))}px`;
            Handle.style.top = `${Math.round(Midpoint - 6)}px`;""",
    """            /*
                Keep the visible horizontal grip a fixed distance ABOVE the
                GB boundary. That distance matches the visual offset of LBC's
                vertical resize-grip lines from the panel edge.
            */
            const GripLineY =
                SquareRect.top -
                ResizeGripLineOffset -
                GameRect.top;

            Handle.style.left = `${Math.round(Left)}px`;
            Handle.style.width = `${Math.max(24, Math.round(Right - Left))}px`;
            Handle.style.top = `${Math.round(GripLineY - 6)}px`;""",
    "TI/GB grip placement",
)

replace_once(
    """            .lb-cubed-resize-handle-left {
                left: -${ResizeHandleWidth / 2}px;
            }

            .lb-cubed-resize-handle-right {
                right: -${ResizeHandleWidth + RightResizeHandleGap}px;
            }""",
    """            .lb-cubed-resize-handle-left {
                left: -${ResizeHandleWidth + RightResizeHandleGap}px;
            }

            .lb-cubed-resize-handle-right {
                right: -${ResizeHandleWidth + RightResizeHandleGap}px;
            }""",
    "symmetric LBC grips",
)

replace_once(
    """        const ToggleLeft = Clamp(
            (SettingsRect?.left ?? PanelRect.right) - ToggleWidth - 6,
            8,
            Math.max(8, window.innerWidth - ToggleWidth - 8)
        );""",
    """        const ToggleLeft = Clamp(
            (SettingsRect?.right ?? PanelRect.right) - ToggleWidth,
            8,
            Math.max(8, window.innerWidth - ToggleWidth - 8)
        );""",
    "debug toggle alignment",
)

replace_once(
    """        /* User-tested placement: debug pane belongs to the RIGHT of LBC. */
        const Left = Math.max(
            8,
            PanelRect.right + 8
        );""",
    """        /*
            The right LBC grip line sits ResizeGripLineOffset px outside LBC.
            Put the debugger another equal offset beyond that line, so the
            grip is visually centered in the gutter between the two panels.
        */
        const Left = Math.max(
            8,
            PanelRect.right + (ResizeGripLineOffset * 2)
        );""",
    "debug pane gutter",
)

replace_once(
    """        DebugPanel.hidden = !PreviewDebugPaneVisible;

        ToggleButton.addEventListener("click", () => {
            PreviewDebugPaneVisible = !PreviewDebugPaneVisible;
            DebugPanel.hidden = !PreviewDebugPaneVisible;""",
    """        DebugPanel.hidden = !PreviewDebugPaneVisible;
        DebugPanel.style.setProperty(
            "display",
            PreviewDebugPaneVisible ? "block" : "none",
            "important"
        );

        ToggleButton.addEventListener("click", () => {
            PreviewDebugPaneVisible = !PreviewDebugPaneVisible;
            DebugPanel.hidden = !PreviewDebugPaneVisible;
            DebugPanel.style.setProperty(
                "display",
                PreviewDebugPaneVisible ? "block" : "none",
                "important"
            );""",
    "debug pane show/hide",
)

source.write_text(text, encoding="utf-8")

changelog = Path("CHANGELOG.md")
ctext = changelog.read_text(encoding="utf-8")
marker = "# Changelog\n\n"
entry = """## 1.12.0-beta.9
- Raised the TI/GB horizontal resize-grip line above the GB top letters using the same visual offset as LBC's vertical grip lines.
- Made LBC's left and right vertical resize-grip lines symmetric outside the panel edges.
- Moved the Preview debugger farther right so LBC's right grip line is centered in an equal gutter between LBC and the debugger.
- Fixed the Preview debugger Show/Hide control with an explicit display override and right-aligned its external toggle with the Settings button.

"""
if entry not in ctext:
    if marker not in ctext:
        raise SystemExit("changelog heading not found")
    ctext = ctext.replace(marker, marker + entry, 1)
    changelog.write_text(ctext, encoding="utf-8")

docs = Path("docs/PREVIEW_TESTING.md")
dtext = docs.read_text(encoding="utf-8")
dtext = dtext.replace(
    "The current source is `1.12.0-beta.8`.",
    "The current source is `1.12.0-beta.9`.",
    1,
)
old = "- Preview includes a TI/GB DOM debugger. Its external **Show Debug Pane / Hide Debug Pane** control sits just outside LBC near Settings; the pane opens to the **right** of LBC and below that control. Mutation capture continues while the pane is hidden."
new = "- Preview includes a TI/GB DOM debugger. Its external **Show Debug Pane / Hide Debug Pane** control sits just outside LBC, right-aligned with Settings; the pane opens to the **right** of LBC and below that control. The pane is explicitly hidden/shown by the toggle, and mutation capture continues while hidden. The right LBC resize grip is centered in an equal gutter between LBC and the debugger."
if old not in dtext:
    raise SystemExit("preview debug docs bullet not found")
dtext = dtext.replace(old, new, 1)
gap_old = "- **Adjust layout gap between text input and letter box** now reserves a fixed-height history lane below the text input. Accepted words, the par, and feedback consume this already-reserved space instead of increasing TI height. Entering enough words to wrap onto additional rows must not move GB."
gap_new = gap_old + " The draggable horizontal grip line sits a fixed visual offset above the GB top letters rather than touching them."
if gap_old not in dtext:
    raise SystemExit("gap docs bullet not found")
dtext = dtext.replace(gap_old, gap_new, 1)
docs.write_text(dtext, encoding="utf-8")
