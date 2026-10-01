from pathlib import Path
import re

SOURCE = Path("LetterBoxedCubed.user.js")
TESTS = Path("tests/final-polish-tests.js")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


source = SOURCE.read_text(encoding="utf-8")

source = replace_once(
    source,
    "// @version      1.13.1-beta.3",
    "// @version      1.13.1-beta.4",
    "version"
)

source = replace_once(
    source,
'''    const InternalPanelLayoutModeClasses = [
        "lb-cubed-layout-narrow",
        "lb-cubed-layout-medium",
        "lb-cubed-layout-wide"
    ];
    const InternalPanelLayoutThresholds = {
        NarrowToMedium: 500,
        MediumToNarrow: 440,
        MediumToWide: 820,
        WideToMedium: 740
    };
''',
'''    const InternalPanelLayoutStageClasses = Array.from(
        { length: 7 },
        (_, Index) => `lb-cubed-layout-stage-${Index}`
    );
    const InternalPanelLayoutBreakpoints = [
        340,
        390,
        520,
        650,
        860,
        1180
    ];
    const DefaultInternalPanelLayoutHysteresisPx = 30;
    const CustomPanelLayoutSections = [
        {
            Id: "Stats",
            Label: "Completion + Longest",
            Selector: ".lb-cubed-stat-grid"
        },
        {
            Id: "Hints",
            Label: "Hints",
            Selector: ".lb-cubed-hints-tree"
        },
        {
            Id: "Twofers",
            Label: "Twofers",
            Selector: ".lb-cubed-twofer-tree"
        },
        {
            Id: "Length",
            Label: "Words by Length",
            Selector: ".lb-cubed-length-tree"
        },
        {
            Id: "Found",
            Label: "Found Words",
            Selector: '.lb-cubed-word-tree[data-cubed-section="FoundWords"]'
        },
        {
            Id: "Unfound",
            Label: "Unfound Words",
            Selector: '.lb-cubed-word-tree[data-cubed-section="UnfoundWords"]'
        }
    ];
''',
    "layout constants"
)

source = replace_once(
    source,
    "    let InternalPanelLayoutMode = null;\n",
'''    let InternalPanelLayoutStage = null;
    let PanelLayoutStyle = "automatic";
    let PanelLayoutHysteresisPx = DefaultInternalPanelLayoutHysteresisPx;
    let CustomPanelLayout = null;
    let CustomPanelLayoutInitialized = false;
''',
    "layout state"
)

finite_helper = '''    function GetFiniteGuiNumber(Name, DefaultValue, Minimum, Maximum) {
        const Value = Number(GetGuiSetting(Name, DefaultValue));

        return Number.isFinite(Value)
            ? Clamp(Value, Minimum, Maximum)
            : DefaultValue;
    }
'''

layout_helpers = finite_helper + '''
    function CreateDefaultCustomPanelLayout() {
        return GetAutomaticLayoutSnapshot(3);
    }

    function NormalizeCustomPanelLayout(RawLayout) {
        const Defaults = {
            StatsSideBySide: true,
            Items: {
                Stats: { Span: 12, PinFirstRow: true },
                Hints: { Span: 6, PinFirstRow: false },
                Twofers: { Span: 6, PinFirstRow: false },
                Length: { Span: 12, PinFirstRow: false },
                Found: { Span: 6, PinFirstRow: false },
                Unfound: { Span: 6, PinFirstRow: false }
            }
        };

        const Raw = RawLayout && typeof RawLayout === "object" && !Array.isArray(RawLayout)
            ? RawLayout
            : {};
        const Result = {
            StatsSideBySide: Object.prototype.hasOwnProperty.call(Raw, "StatsSideBySide")
                ? Boolean(Raw.StatsSideBySide)
                : Defaults.StatsSideBySide,
            Items: {}
        };
        const RawItems = Raw.Items && typeof Raw.Items === "object" && !Array.isArray(Raw.Items)
            ? Raw.Items
            : {};

        for (const Definition of CustomPanelLayoutSections) {
            const DefaultItem = Defaults.Items[Definition.Id];
            const RawItem = RawItems[Definition.Id];
            const Span = Number(RawItem?.Span);

            Result.Items[Definition.Id] = {
                Span: Number.isFinite(Span)
                    ? Math.round(Clamp(Span, 1, 12))
                    : DefaultItem.Span,
                PinFirstRow: RawItem && Object.prototype.hasOwnProperty.call(RawItem, "PinFirstRow")
                    ? Boolean(RawItem.PinFirstRow)
                    : DefaultItem.PinFirstRow
            };
        }

        return Result;
    }

    function GetAutomaticLayoutSnapshot(Stage) {
        const NormalizedStage = Math.round(Clamp(Number(Stage) || 0, 0, 6));
        const Snapshots = [
            {
                StatsSideBySide: false,
                Spans: [12, 12, 12, 12, 12, 12],
                Pinned: ["Stats"]
            },
            {
                StatsSideBySide: true,
                Spans: [12, 12, 12, 12, 12, 12],
                Pinned: ["Stats"]
            },
            {
                StatsSideBySide: true,
                Spans: [12, 12, 12, 12, 6, 6],
                Pinned: ["Stats"]
            },
            {
                StatsSideBySide: true,
                Spans: [12, 6, 6, 12, 6, 6],
                Pinned: ["Stats"]
            },
            {
                StatsSideBySide: true,
                Spans: [12, 4, 4, 4, 4, 4],
                Pinned: ["Stats"]
            },
            {
                StatsSideBySide: true,
                Spans: [4, 2, 4, 2, 6, 6],
                Pinned: ["Stats", "Hints", "Twofers", "Length"]
            },
            {
                StatsSideBySide: true,
                Spans: [3, 1, 3, 1, 2, 2],
                Pinned: ["Stats", "Hints", "Twofers", "Length", "Found", "Unfound"]
            }
        ];
        const Snapshot = Snapshots[NormalizedStage];
        const Result = {
            StatsSideBySide: Snapshot.StatsSideBySide,
            Items: {}
        };

        CustomPanelLayoutSections.forEach((Definition, Index) => {
            Result.Items[Definition.Id] = {
                Span: Snapshot.Spans[Index],
                PinFirstRow: Snapshot.Pinned.includes(Definition.Id)
            };
        });

        return Result;
    }

    function SaveCustomPanelLayoutPreference() {
        CustomPanelLayout = NormalizeCustomPanelLayout(CustomPanelLayout);
        CustomPanelLayoutInitialized = true;
        SetGuiSetting("CustomPanelLayout", CustomPanelLayout);
        UpdatePanelLayout();
    }
'''
source = replace_once(
    source,
    finite_helper,
    layout_helpers,
    "layout preference helpers"
)

source = replace_once(
    source,
'''        HideYesterdayHelpRow = Boolean(
            GetGuiSetting("HideYesterdayHelpRow", false)
        );
    }
''',
'''        HideYesterdayHelpRow = Boolean(
            GetGuiSetting("HideYesterdayHelpRow", false)
        );

        PanelLayoutStyle = GetGuiSetting("PanelLayoutStyle", "automatic") === "custom"
            ? "custom"
            : "automatic";

        PanelLayoutHysteresisPx = GetFiniteGuiNumber(
            "PanelLayoutHysteresisPx",
            DefaultInternalPanelLayoutHysteresisPx,
            0,
            120
        );

        const SavedCustomPanelLayout = GetGuiSetting("CustomPanelLayout", null);
        CustomPanelLayoutInitialized = Boolean(
            SavedCustomPanelLayout &&
            typeof SavedCustomPanelLayout === "object" &&
            !Array.isArray(SavedCustomPanelLayout)
        );
        CustomPanelLayout = NormalizeCustomPanelLayout(
            SavedCustomPanelLayout || CreateDefaultCustomPanelLayout()
        );
    }
''',
    "load layout preferences"
)

settings_anchor = '''    function CreateSettingsMenu() {
'''
settings_helpers = '''    function RefreshPanelLayoutSettingsGroup(Group) {
        Group.replaceChildren();

        const Heading = document.createElement("div");
        Heading.className = "lb-cubed-settings-subgroup-title";
        Heading.textContent = "Panel layout";

        const ModeRow = document.createElement("label");
        ModeRow.className = "lb-cubed-layout-select-row";
        const ModeLabel = document.createElement("span");
        ModeLabel.className = "lb-cubed-settings-label";
        ModeLabel.textContent = "Layout";
        const ModeSelect = document.createElement("select");
        ModeSelect.className = "lb-cubed-theme-select";

        for (const [Value, Label] of [
            ["automatic", "Automatic (original responsive)"],
            ["custom", "Custom 12-column"]
        ]) {
            const Option = document.createElement("option");
            Option.value = Value;
            Option.textContent = Label;
            ModeSelect.appendChild(Option);
        }

        ModeSelect.value = PanelLayoutStyle;
        ModeSelect.addEventListener("change", () => {
            const NextStyle = ModeSelect.value === "custom"
                ? "custom"
                : "automatic";

            if (NextStyle === "custom" && !CustomPanelLayoutInitialized) {
                const Panel = document.getElementById(PanelId);
                const Width = Panel?.getBoundingClientRect().width || 0;
                CustomPanelLayout = GetAutomaticLayoutSnapshot(
                    GetInitialInternalPanelLayoutStage(Width)
                );
                CustomPanelLayoutInitialized = true;
                SetGuiSetting("CustomPanelLayout", CustomPanelLayout);
            }

            PanelLayoutStyle = NextStyle;
            InternalPanelLayoutStage = null;
            SetGuiSetting("PanelLayoutStyle", PanelLayoutStyle);
            UpdatePanelLayout();
            RefreshPanelLayoutSettingsGroup(Group);
        });
        ModeRow.append(ModeLabel, ModeSelect);

        Group.append(Heading, ModeRow);

        if (PanelLayoutStyle === "automatic") {
            Group.appendChild(
                CreateSettingsNumberWithReset(
                    "Breakpoint hysteresis",
                    Math.round(PanelLayoutHysteresisPx),
                    0,
                    120,
                    1,
                    "px",
                    DefaultInternalPanelLayoutHysteresisPx,
                    "PanelLayoutHysteresisPx",
                    Value => {
                        PanelLayoutHysteresisPx = Clamp(Value, 0, 120);
                        InternalPanelLayoutStage = null;
                        SetGuiSetting(
                            "PanelLayoutHysteresisPx",
                            PanelLayoutHysteresisPx
                        );
                        UpdatePanelLayout();
                    }
                )
            );

            const Note = document.createElement("div");
            Note.className = "lb-cubed-theme-note";
            Note.textContent =
                "Uses the original 340/390/520/650/860/1180px layouts. " +
                "Hysteresis only delays the reverse transition so resizing does not flap at a boundary.";
            Group.appendChild(Note);
            return;
        }

        const ButtonRow = document.createElement("div");
        ButtonRow.className = "lb-cubed-settings-button-row";
        const CopyAutomatic = document.createElement("button");
        CopyAutomatic.type = "button";
        CopyAutomatic.className = "lb-cubed-header-button";
        CopyAutomatic.textContent = "Start from current automatic layout";
        CopyAutomatic.addEventListener("click", Event => {
            Event.preventDefault();
            const Panel = document.getElementById(PanelId);
            const Width = Panel?.getBoundingClientRect().width || 0;
            CustomPanelLayout = GetAutomaticLayoutSnapshot(
                GetInitialInternalPanelLayoutStage(Width)
            );
            SaveCustomPanelLayoutPreference();
            RefreshPanelLayoutSettingsGroup(Group);
        });
        ButtonRow.appendChild(CopyAutomatic);
        Group.appendChild(ButtonRow);

        Group.appendChild(
            CreateSettingsCheckbox(
                "Keep Completion + Longest side-by-side",
                CustomPanelLayout.StatsSideBySide,
                Checked => {
                    CustomPanelLayout.StatsSideBySide = Checked;
                    SaveCustomPanelLayoutPreference();
                }
            )
        );

        const HeaderRow = document.createElement("div");
        HeaderRow.className = "lb-cubed-layout-item-row lb-cubed-layout-item-header";
        HeaderRow.innerHTML =
            '<span>Section</span><span>Span /12</span><span>First row</span>';
        Group.appendChild(HeaderRow);

        for (const Definition of CustomPanelLayoutSections) {
            const Item = CustomPanelLayout.Items[Definition.Id];
            const Row = document.createElement("div");
            Row.className = "lb-cubed-layout-item-row";

            const Label = document.createElement("span");
            Label.className = "lb-cubed-settings-label";
            Label.textContent = Definition.Label;

            const SpanInput = document.createElement("input");
            SpanInput.type = "number";
            SpanInput.min = "1";
            SpanInput.max = "12";
            SpanInput.step = "1";
            SpanInput.value = String(Item.Span);
            SpanInput.title = "Width in twelfths of the LBC dashboard";
            SpanInput.addEventListener("change", () => {
                const Value = Number(SpanInput.value);
                Item.Span = Number.isFinite(Value)
                    ? Math.round(Clamp(Value, 1, 12))
                    : Item.Span;
                SpanInput.value = String(Item.Span);
                SaveCustomPanelLayoutPreference();
                RefreshPanelLayoutSettingsGroup(Group);
            });

            const PinLabel = document.createElement("label");
            PinLabel.className = "lb-cubed-layout-pin";
            const PinInput = document.createElement("input");
            PinInput.type = "checkbox";
            PinInput.checked = Item.PinFirstRow;
            PinInput.addEventListener("change", () => {
                Item.PinFirstRow = PinInput.checked;
                SaveCustomPanelLayoutPreference();
                RefreshPanelLayoutSettingsGroup(Group);
            });
            const PinText = document.createElement("span");
            PinText.textContent = "Pin";
            PinLabel.append(PinInput, PinText);

            Row.append(Label, SpanInput, PinLabel);
            Group.appendChild(Row);
        }

        const PinnedTotal = CustomPanelLayoutSections
            .filter(Definition => CustomPanelLayout.Items[Definition.Id].PinFirstRow)
            .reduce(
                (Total, Definition) =>
                    Total + CustomPanelLayout.Items[Definition.Id].Span,
                0
            );

        const Note = document.createElement("div");
        Note.className = PinnedTotal > 12
            ? "lb-cubed-layout-warning"
            : "lb-cubed-theme-note";
        Note.textContent = PinnedTotal > 12
            ? `Pinned spans total ${PinnedTotal}/12. The first row will compress later pinned sections to fit safely.`
            : "Pinned sections always occupy row 1 in the order shown. Unpinned sections flow below them using their chosen 1-12 column spans.";
        Group.appendChild(Note);
    }

    function CreatePanelLayoutSettingsGroup() {
        const Group = document.createElement("div");
        Group.className = "lb-cubed-settings-subgroup lb-cubed-layout-settings";
        RefreshPanelLayoutSettingsGroup(Group);
        return Group;
    }

''' + settings_anchor
source = replace_once(
    source,
    settings_anchor,
    settings_helpers,
    "panel layout settings helpers"
)

source = replace_once(
    source,
'''        const GapGroup = document.createElement("div");
''',
'''        DisplaySection.appendChild(
            CreatePanelLayoutSettingsGroup()
        );

        const GapGroup = document.createElement("div");
''',
    "insert panel layout settings"
)

layout_pattern = re.compile(
    r'''    function GetNextInternalPanelLayoutMode\(PanelWidth\) \{.*?\n    function UpdateInternalPanelLayout\(Panel, PanelWidth\) \{.*?\n    \}\n\n(?=    function UpdatePanelLayout\(\))''',
    re.S
)

layout_replacement = '''    function GetInitialInternalPanelLayoutStage(PanelWidth) {
        const Width = Math.max(0, Number(PanelWidth) || 0);
        let Stage = 0;

        for (const Breakpoint of InternalPanelLayoutBreakpoints) {
            if (Width < Breakpoint) {
                break;
            }
            Stage++;
        }

        return Stage;
    }

    function GetNextInternalPanelLayoutStage(PanelWidth) {
        const Width = Math.max(0, Number(PanelWidth) || 0);

        if (InternalPanelLayoutStage === null) {
            return GetInitialInternalPanelLayoutStage(Width);
        }

        let Stage = InternalPanelLayoutStage;

        while (
            Stage < InternalPanelLayoutBreakpoints.length &&
            Width >= InternalPanelLayoutBreakpoints[Stage]
        ) {
            Stage++;
        }

        while (Stage > 0) {
            const ExitThreshold = Math.max(
                0,
                InternalPanelLayoutBreakpoints[Stage - 1] -
                PanelLayoutHysteresisPx
            );

            if (Width >= ExitThreshold) {
                break;
            }
            Stage--;
        }

        return Stage;
    }

    function ClearCustomPanelLayoutInlineStyles(Panel) {
        const Dashboard = Panel.querySelector(".lb-cubed-dashboard-grid");
        if (!Dashboard) {
            return;
        }

        Dashboard.style.removeProperty("grid-template-columns");
        Dashboard.style.removeProperty("grid-template-areas");

        for (const Definition of CustomPanelLayoutSections) {
            const Element = Dashboard.querySelector(Definition.Selector);
            if (!Element) {
                continue;
            }
            Element.style.removeProperty("grid-column");
            Element.style.removeProperty("grid-row");
        }

        const StatGrid = Dashboard.querySelector(".lb-cubed-stat-grid");
        StatGrid?.style.removeProperty("grid-template-columns");
    }

    function ApplyCustomPanelLayout(Panel) {
        const Dashboard = Panel.querySelector(".lb-cubed-dashboard-grid");
        if (!Dashboard) {
            return;
        }

        CustomPanelLayout = NormalizeCustomPanelLayout(CustomPanelLayout);
        Dashboard.style.setProperty(
            "grid-template-columns",
            "repeat(12, minmax(0, 1fr))"
        );
        Dashboard.style.setProperty("grid-template-areas", "none");

        const Entries = CustomPanelLayoutSections
            .map(Definition => ({
                Definition,
                Element: Dashboard.querySelector(Definition.Selector),
                Layout: CustomPanelLayout.Items[Definition.Id]
            }))
            .filter(Entry => Entry.Element);
        const Pinned = Entries.filter(Entry => Entry.Layout.PinFirstRow);
        const Flowing = Entries.filter(Entry => !Entry.Layout.PinFirstRow);
        const Placements = [];

        let Column = 1;
        for (let Index = 0; Index < Pinned.length; Index++) {
            const Entry = Pinned[Index];
            const RemainingItems = Pinned.length - Index - 1;
            const MaximumSpan = Math.max(
                1,
                13 - Column - RemainingItems
            );
            const Span = Math.min(Entry.Layout.Span, MaximumSpan);

            Placements.push({ Entry, Row: 1, Column, Span });
            Column += Span;
        }

        let Row = Pinned.length ? 2 : 1;
        Column = 1;

        for (const Entry of Flowing) {
            const Span = Entry.Layout.Span;
            if (Column + Span - 1 > 12) {
                Row++;
                Column = 1;
            }

            Placements.push({ Entry, Row, Column, Span });
            Column += Span;

            if (Column > 12) {
                Row++;
                Column = 1;
            }
        }

        for (const Placement of Placements) {
            Placement.Entry.Element.style.setProperty(
                "grid-column",
                `${Placement.Column} / span ${Placement.Span}`
            );
            Placement.Entry.Element.style.setProperty(
                "grid-row",
                String(Placement.Row)
            );
        }

        const StatGrid = Dashboard.querySelector(".lb-cubed-stat-grid");
        if (StatGrid) {
            StatGrid.style.setProperty(
                "grid-template-columns",
                CustomPanelLayout.StatsSideBySide
                    ? "repeat(2, minmax(0, 1fr))"
                    : "minmax(0, 1fr)"
            );
        }
    }

    function UpdateInternalPanelLayout(Panel, PanelWidth) {
        for (const ClassName of InternalPanelLayoutStageClasses) {
            Panel.classList.remove(ClassName);
        }
        Panel.classList.remove("lb-cubed-layout-custom");

        if (PanelLayoutStyle === "custom") {
            InternalPanelLayoutStage = GetInitialInternalPanelLayoutStage(
                PanelWidth
            );
            Panel.classList.add("lb-cubed-layout-custom");
            Panel.dataset.cubedLayoutMode = "custom";
            Panel.dataset.cubedLayoutStage = String(InternalPanelLayoutStage);
            ApplyCustomPanelLayout(Panel);
            return;
        }

        ClearCustomPanelLayoutInlineStyles(Panel);
        InternalPanelLayoutStage = GetNextInternalPanelLayoutStage(PanelWidth);
        Panel.classList.add(
            `lb-cubed-layout-stage-${InternalPanelLayoutStage}`
        );
        Panel.dataset.cubedLayoutMode = "automatic";
        Panel.dataset.cubedLayoutStage = String(InternalPanelLayoutStage);
    }

'''
source, count = layout_pattern.subn(layout_replacement, source, count=1)
if count != 1:
    raise RuntimeError(f"layout functions: expected one replacement, found {count}")

css_start_marker = '''            /*
                ================================================================
                COHERENT INTERNAL LBC LAYOUT MODES (ISSUE #15)
'''
css_end_marker = '''            /*
                ================================================================
                COLOR THEMES (ISSUE #30)
'''
css_start = source.find(css_start_marker)
css_end = source.find(css_end_marker, css_start)
if css_start < 0 or css_end < 0:
    raise RuntimeError("responsive CSS markers not found")

new_css = r'''            /*
                ================================================================
                ORIGINAL RESPONSIVE LAYOUT + HYSTERESIS (ISSUE #15)
                ================================================================

                The visual arrangements below intentionally reproduce the old
                340/390/520/650/860/1180px container-query cascade. JavaScript
                applies the stage classes so reverse transitions can use a
                configurable dead band instead of flapping on one exact pixel.
            */

            #${PanelId}.lb-cubed-layout-stage-0 .lb-cubed-dashboard-grid,
            #${PanelId}.lb-cubed-layout-stage-1 .lb-cubed-dashboard-grid {
                grid-template-columns: minmax(0, 1fr);
                grid-template-areas:
                    "stats"
                    "hints"
                    "twofers"
                    "length"
                    "found"
                    "unfound";
            }

            #${PanelId}.lb-cubed-layout-stage-1 .lb-cubed-stat-grid,
            #${PanelId}.lb-cubed-layout-stage-2 .lb-cubed-stat-grid,
            #${PanelId}.lb-cubed-layout-stage-3 .lb-cubed-stat-grid,
            #${PanelId}.lb-cubed-layout-stage-4 .lb-cubed-stat-grid,
            #${PanelId}.lb-cubed-layout-stage-5 .lb-cubed-stat-grid,
            #${PanelId}.lb-cubed-layout-stage-6 .lb-cubed-stat-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            #${PanelId}.lb-cubed-layout-stage-0 .lb-cubed-word-tree,
            #${PanelId}.lb-cubed-layout-stage-1 .lb-cubed-word-tree,
            #${PanelId}.lb-cubed-layout-custom .lb-cubed-word-tree {
                max-width: none;
            }

            #${PanelId}.lb-cubed-layout-stage-0 .lb-cubed-header,
            #${PanelId}.lb-cubed-layout-stage-1 .lb-cubed-header {
                flex-direction: column;
            }

            #${PanelId}.lb-cubed-layout-stage-0 .lb-cubed-header-actions,
            #${PanelId}.lb-cubed-layout-stage-1 .lb-cubed-header-actions {
                width: 100%;
                justify-content: flex-start;
                flex-wrap: wrap;
            }

            #${PanelId}.lb-cubed-layout-stage-0 .lb-cubed-title-row,
            #${PanelId}.lb-cubed-layout-stage-1 .lb-cubed-title-row {
                flex-wrap: wrap;
            }

            #${PanelId}.lb-cubed-layout-stage-0 .lb-cubed-settings-panel,
            #${PanelId}.lb-cubed-layout-stage-1 .lb-cubed-settings-panel {
                left: 0;
                right: auto;
                width: min(340px, calc(100vw - 36px));
            }

            #${PanelId}.lb-cubed-layout-stage-2 .lb-cubed-dashboard-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
                grid-template-areas:
                    "stats stats"
                    "hints hints"
                    "twofers twofers"
                    "length length"
                    "found unfound";
            }

            #${PanelId}.lb-cubed-layout-stage-3 .lb-cubed-dashboard-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
                grid-template-areas:
                    "stats stats"
                    "hints twofers"
                    "length length"
                    "found unfound";
            }

            #${PanelId}.lb-cubed-layout-stage-4 .lb-cubed-dashboard-grid {
                grid-template-columns: repeat(6, minmax(0, 1fr));
                grid-template-areas:
                    "stats stats stats stats stats stats"
                    "hints hints twofers twofers length length"
                    "found found unfound unfound . .";
            }

            #${PanelId}.lb-cubed-layout-stage-5 .lb-cubed-dashboard-grid {
                grid-template-columns:
                    minmax(250px, 2fr)
                    minmax(135px, 1fr)
                    minmax(220px, 1.6fr)
                    minmax(135px, 1fr);
                grid-template-areas:
                    "stats hints twofers length"
                    "found unfound . .";
            }

            #${PanelId}.lb-cubed-layout-stage-6 .lb-cubed-dashboard-grid {
                grid-template-columns:
                    minmax(260px, 2fr)
                    minmax(130px, 1fr)
                    minmax(220px, 1.6fr)
                    minmax(125px, 1fr)
                    minmax(155px, 1fr)
                    minmax(155px, 1fr);
                grid-template-areas:
                    "stats hints twofers length found unfound";
            }

            #${PanelId}.lb-cubed-layout-stage-2 .lb-cubed-word-tree,
            #${PanelId}.lb-cubed-layout-stage-3 .lb-cubed-word-tree,
            #${PanelId}.lb-cubed-layout-stage-4 .lb-cubed-word-tree,
            #${PanelId}.lb-cubed-layout-stage-5 .lb-cubed-word-tree,
            #${PanelId}.lb-cubed-layout-stage-6 .lb-cubed-word-tree {
                max-width: 220px;
            }

            /*
                Optional advanced layout. Each top-level dashboard section is
                placed by JavaScript on a deterministic 12-column grid. Pinned
                sections occupy row 1; everything else flows below it.
            */
            #${PanelId}.lb-cubed-layout-custom .lb-cubed-dashboard-grid {
                display: grid;
                grid-template-columns: repeat(12, minmax(0, 1fr));
                grid-template-areas: none;
            }

            .lb-cubed-layout-select-row,
            .lb-cubed-layout-item-row {
                display: grid;
                grid-template-columns: minmax(120px, 1fr) 64px 76px;
                align-items: center;
                gap: 6px;
                min-height: 28px;
                font-size: 12px;
            }

            .lb-cubed-layout-select-row {
                grid-template-columns: minmax(120px, 1fr) minmax(150px, 1.4fr);
            }

            .lb-cubed-layout-item-row input[type="number"] {
                width: 58px;
                min-width: 0;
                padding: 2px 4px;
                border: 1px solid var(--lb-cubed-lbc-border, #4C2222);
                border-radius: 3px;
                background: var(--lb-cubed-lbc-surface, #E5A09E);
                color: var(--lb-cubed-lbc-text, #301818);
            }

            .lb-cubed-layout-item-header {
                min-height: 20px;
                color: var(--lb-cubed-lbc-muted, #684949);
                font-size: 10px;
                font-weight: 700;
            }

            .lb-cubed-layout-pin {
                display: flex;
                align-items: center;
                gap: 4px;
                white-space: nowrap;
            }

            .lb-cubed-layout-warning {
                margin-top: 5px;
                color: var(--lb-cubed-danger, #AF3636);
                font-size: 10px;
                line-height: 1.35;
            }

'''
source = source[:css_start] + new_css + source[css_end:]

SOURCE.write_text(source, encoding="utf-8")

# Update static regression coverage for the revised layout implementation.
tests = TESTS.read_text(encoding="utf-8")
tests = tests.replace("1.13.1-beta.3", "1.13.1-beta.4")
old_checks = '''assert(source.includes('lb-cubed-layout-narrow'), 'narrow layout mode missing');
assert(source.includes('lb-cubed-layout-medium'), 'medium layout mode missing');
assert(source.includes('lb-cubed-layout-wide'), 'wide layout mode missing');
assert(source.includes('NarrowToMedium: 500'), 'layout hysteresis enter threshold missing');
assert(source.includes('MediumToNarrow: 440'), 'layout hysteresis exit threshold missing');
assert(source.includes('MediumToWide: 820'), 'wide enter threshold missing');
assert(source.includes('WideToMedium: 740'), 'wide exit threshold missing');
assert(!source.includes('@container lbc'), 'old independent container-query cascade remains');
'''
new_checks = '''assert(source.includes('InternalPanelLayoutBreakpoints = ['), 'original breakpoint list missing');
for (const breakpoint of ['340', '390', '520', '650', '860', '1180']) {
  assert(source.includes(breakpoint), `original breakpoint missing: ${breakpoint}`);
}
assert(source.includes('DefaultInternalPanelLayoutHysteresisPx = 30'), 'layout hysteresis default missing');
for (let stage = 0; stage <= 6; stage++) {
  assert(source.includes(`lb-cubed-layout-stage-${stage}`), `responsive stage missing: ${stage}`);
}
assert(source.includes('Custom 12-column'), 'custom 12-column layout option missing');
assert(source.includes('PinFirstRow'), 'first-row pinning missing');
assert(source.includes('Span: 12'), 'custom column span model missing');
assert(source.includes('Start from current automatic layout'), 'automatic-to-custom snapshot action missing');
assert(!source.includes('lb-cubed-layout-narrow'), 'rejected narrow/medium/wide layout implementation remains');
assert(!source.includes('@container lbc'), 'state-less container-query cascade should not return');
'''
if old_checks not in tests:
    raise RuntimeError("final polish layout checks anchor not found")
tests = tests.replace(old_checks, new_checks, 1)
TESTS.write_text(tests, encoding="utf-8")
