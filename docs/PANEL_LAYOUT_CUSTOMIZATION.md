# LBC panel layout customization

v1.13.1-beta.5 restores the original responsive LBC dashboard arrangements and adds stateful hysteresis plus an optional advanced 12-column layout.

## Automatic layout

Automatic mode uses the original visual breakpoints at 340, 390, 520, 650, 860, and 1180 pixels. On initial layout, the stage is selected exactly as before. While resizing back across a breakpoint, LBC keeps the current stage until the panel has crossed the breakpoint by the configured hysteresis amount (30px by default). This preserves the old arrangements while preventing rapid back-and-forth layout changes near a boundary.

The hysteresis value is portable GUI state and can be changed in Settings -> Display -> Panel layout.

## Custom 12-column layout

Custom mode replaces the automatic dashboard arrangement with a deterministic 12-column grid. Each top-level section has two controls:

- Span /12: requested width from 1 to 12 grid units.
- First row: pins the section to row 1 regardless of panel width.

Pinned sections are placed left-to-right in their normal dashboard order. Unpinned sections flow below the pinned row, wrapping whenever the next requested span would exceed 12 units.

If pinned spans total more than 12, LBC safely compresses later pinned sections enough to keep the first row within the 12-column grid and displays a warning in Settings.

Completion + Longest Found remain a nested summary group. Custom mode separately exposes whether those two stat cards stay side-by-side.

Use "Start from current automatic layout" to seed the custom spans and first-row pins from whichever original responsive stage matches the panel's current width.

Panel layout mode, hysteresis, custom spans, first-row pins, and the stat-card arrangement are stored in portable GUI state and therefore participate in the existing Google Drive GUI-state merge/sync behavior.


## Rerender stability

Custom layout placement is reapplied synchronously whenever RenderPanel() rebuilds the dashboard children. This is required because the 12-column placement lives on those child elements as inline grid-row/grid-column styles. Without this refresh, any ordinary panel rerender - notably the rerender caused by a newly found word/highlight - temporarily discarded the custom placement until a resize happened to run UpdatePanelLayout().
