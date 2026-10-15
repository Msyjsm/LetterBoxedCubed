from pathlib import Path
import re

source_path = Path('LetterBoxedCubed.user.js')
text = source_path.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 occurrence, found {count}')
    text = text.replace(old, new, 1)


replace_once('// @version      1.13.1-beta.25', '// @version      1.13.1-beta.26', 'version')

# Preserve each independent LBC color while its Letter Boxed binding is enabled.
replace_once(
'''        const LbcHighlightMatchesLbHighlight =
            Object.prototype.hasOwnProperty.call(
                RawTheme,
                "LbcHighlightMatchesLbHighlight"
            )
                ? Boolean(RawTheme.LbcHighlightMatchesLbHighlight)
                : Palette.LbcBorder === Palette.LbActive;

        if (BoardMatchesBackground) {''',
'''        const LbcHighlightMatchesLbHighlight =
            Object.prototype.hasOwnProperty.call(
                RawTheme,
                "LbcHighlightMatchesLbHighlight"
            )
                ? Boolean(RawTheme.LbcHighlightMatchesLbHighlight)
                : Palette.LbcBorder === Palette.LbActive;

        const LbcBackgroundUnlinkedColor = NormalizeThemeColor(
            RawTheme.LbcBackgroundUnlinkedColor,
            Palette.LbcBackground
        );
        const LbcTextUnlinkedColor = NormalizeThemeColor(
            RawTheme.LbcTextUnlinkedColor,
            Palette.LbcText
        );
        const LbcHighlightUnlinkedColor = NormalizeThemeColor(
            RawTheme.LbcHighlightUnlinkedColor,
            Palette.LbcBorder
        );

        if (BoardMatchesBackground) {''',
'normalize unlinked colors')

replace_once(
'''            LbcBackgroundMatchesLbBackground,
            LbcTextMatchesLbForeground,
            LbcHighlightMatchesLbHighlight,
            Deleted: Boolean(RawTheme.Deleted),''',
'''            LbcBackgroundMatchesLbBackground,
            LbcTextMatchesLbForeground,
            LbcHighlightMatchesLbHighlight,
            LbcBackgroundUnlinkedColor,
            LbcTextUnlinkedColor,
            LbcHighlightUnlinkedColor,
            Deleted: Boolean(RawTheme.Deleted),''',
'return unlinked colors')

replace_once(
'''        let Palette = NormalizeThemePalette(Base.Palette, null, false);
        if (Base.Id === DefaultThemeId && Base.ApplyNative === false) {
            Palette = CaptureNativeLightTriad(Palette);
        }

        if (LbcBackgroundMatchesLbBackground) {''',
'''        let Palette = NormalizeThemePalette(Base.Palette, null, false);
        if (Base.Id === DefaultThemeId && Base.ApplyNative === false) {
            Palette = CaptureNativeLightTriad(Palette);
        }

        const LbcBackgroundUnlinkedColor = NormalizeThemeColor(
            Base.LbcBackgroundUnlinkedColor,
            Palette.LbcBackground
        );
        const LbcTextUnlinkedColor = NormalizeThemeColor(
            Base.LbcTextUnlinkedColor,
            Palette.LbcText
        );
        const LbcHighlightUnlinkedColor = NormalizeThemeColor(
            Base.LbcHighlightUnlinkedColor,
            Palette.LbcBorder
        );

        if (LbcBackgroundMatchesLbBackground) {''',
'duplicate unlinked colors')

replace_once(
'''            LbcBackgroundMatchesLbBackground,
            LbcTextMatchesLbForeground,
            LbcHighlightMatchesLbHighlight,
            Deleted: false,''',
'''            LbcBackgroundMatchesLbBackground,
            LbcTextMatchesLbForeground,
            LbcHighlightMatchesLbHighlight,
            LbcBackgroundUnlinkedColor,
            LbcTextUnlinkedColor,
            LbcHighlightUnlinkedColor,
            Deleted: false,''',
'store duplicate unlinked colors')

replace_once(
'''        Theme.Palette[Key] = NormalizeThemeColor(Value, Theme.Palette[Key]);

        if (
            Key === "LbBackground" &&''',
'''        Theme.Palette[Key] = NormalizeThemeColor(Value, Theme.Palette[Key]);

        if (Key === "LbcBackground" && !Theme.LbcBackgroundMatchesLbBackground) {
            Theme.LbcBackgroundUnlinkedColor = Theme.Palette.LbcBackground;
        }
        if (Key === "LbcText" && !Theme.LbcTextMatchesLbForeground) {
            Theme.LbcTextUnlinkedColor = Theme.Palette.LbcText;
        }
        if (Key === "LbcBorder" && !Theme.LbcHighlightMatchesLbHighlight) {
            Theme.LbcHighlightUnlinkedColor = Theme.Palette.LbcBorder;
        }

        if (
            Key === "LbBackground" &&''',
'track edits while unlinked')

pattern = re.compile(r'''    function UpdateActiveCustomThemeLbcBackgroundMatch\(Value\) \{.*?\n    \}\n\n    function UpdateActiveCustomThemeLbcTextMatch''', re.S)
replacement = '''    function UpdateActiveCustomThemeLbcBackgroundMatch(Value) {
        const Theme = GetActiveCustomThemeRecord();
        if (!Theme) {
            return false;
        }

        const Next = Boolean(Value);
        if (Next && !Theme.LbcBackgroundMatchesLbBackground) {
            Theme.LbcBackgroundUnlinkedColor = Theme.Palette.LbcBackground;
        }
        Theme.LbcBackgroundMatchesLbBackground = Next;
        Theme.Palette.LbcBackground = Next
            ? Theme.Palette.LbBackground
            : NormalizeThemeColor(
                Theme.LbcBackgroundUnlinkedColor,
                Theme.Palette.LbcBackground
            );
        Theme.UpdatedAt = new Date().toISOString();
        SaveThemeState();
        ApplyTheme();
        return true;
    }

    function UpdateActiveCustomThemeLbcTextMatch'''
text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit('background link function patch failed')

pattern = re.compile(r'''    function UpdateActiveCustomThemeLbcTextMatch\(Value\) \{.*?\n    \}\n\n    function UpdateActiveCustomThemeLbcHighlightMatch''', re.S)
replacement = '''    function UpdateActiveCustomThemeLbcTextMatch(Value) {
        const Theme = GetActiveCustomThemeRecord();
        if (!Theme) {
            return false;
        }

        const Next = Boolean(Value);
        if (Next && !Theme.LbcTextMatchesLbForeground) {
            Theme.LbcTextUnlinkedColor = Theme.Palette.LbcText;
        }
        Theme.LbcTextMatchesLbForeground = Next;
        Theme.Palette.LbcText = Next
            ? Theme.Palette.LbForeground
            : NormalizeThemeColor(
                Theme.LbcTextUnlinkedColor,
                Theme.Palette.LbcText
            );
        Theme.UpdatedAt = new Date().toISOString();
        SaveThemeState();
        ApplyTheme();
        return true;
    }

    function UpdateActiveCustomThemeLbcHighlightMatch'''
text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit('foreground link function patch failed')

pattern = re.compile(r'''    function UpdateActiveCustomThemeLbcHighlightMatch\(Value\) \{.*?\n    \}\n\n    function CreateEmptyGuiState''', re.S)
replacement = '''    function UpdateActiveCustomThemeLbcHighlightMatch(Value) {
        const Theme = GetActiveCustomThemeRecord();
        if (!Theme) {
            return false;
        }

        const Next = Boolean(Value);
        if (Next && !Theme.LbcHighlightMatchesLbHighlight) {
            Theme.LbcHighlightUnlinkedColor = Theme.Palette.LbcBorder;
        }
        Theme.LbcHighlightMatchesLbHighlight = Next;
        Theme.Palette.LbcBorder = Next
            ? Theme.Palette.LbActive
            : NormalizeThemeColor(
                Theme.LbcHighlightUnlinkedColor,
                Theme.Palette.LbcBorder
            );
        Theme.UpdatedAt = new Date().toISOString();
        SaveThemeState();
        ApplyTheme();
        return true;
    }

    function CreateEmptyGuiState'''
text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit('highlight link function patch failed')

# Theme menu: prior "Headings last" applies before appended former Highlights children.
replace_once(
'''    function AppendThemeColorGroup(Section, Title, Rows) {
        const Group = document.createElement("div");
        Group.className = "lb-cubed-settings-subgroup lb-cubed-theme-color-group";
        const GroupTitle = document.createElement("div");
        GroupTitle.className = "lb-cubed-settings-subgroup-title";
        GroupTitle.textContent = Title;
        Group.appendChild(GroupTitle);''',
'''    function AppendThemeColorGroup(Section, Title, Rows, TitleAttribute = "") {
        const Group = document.createElement("div");
        Group.className = "lb-cubed-settings-subgroup lb-cubed-theme-color-group";
        const GroupTitle = document.createElement("div");
        GroupTitle.className = "lb-cubed-settings-subgroup-title";
        GroupTitle.textContent = Title;
        if (TitleAttribute) {
            GroupTitle.title = TitleAttribute;
        }
        Group.appendChild(GroupTitle);''',
'theme group title attribute')

replace_once(
'''                CreateThemeLinkedColorRow(
                    Section,
                    "Highlight",
                    "LbcBorder",
                    "LbcHighlightMatchesLbHighlight",
                    "Use Letter Boxed color",
                    "#4C2222",
                    UpdateActiveCustomThemeLbcHighlightMatch
                ),
                CreateThemeColorRow("NYT solution", "NytSolution"),
                CreateThemeColorRow("New word highlight", "NewHighlight"),
                CreateThemeColorRow("Redacted", "Redacted"),
                CreateThemeColorRow("Headings", "LbcHeadingBackground")
            ]
        );

        const Note = document.createElement("div");
        Note.className = "lb-cubed-theme-note";
        Note.textContent =
            "Background brightness selects the Light or Dark mapping column. " +
            "Every Letter Boxed board state and toast then uses only Background, " +
            "Foreground, or Highlight; no extra native colors are synthesized.";
        Section.appendChild(Note);''',
'''                CreateThemeLinkedColorRow(
                    Section,
                    "Highlight",
                    "LbcBorder",
                    "LbcHighlightMatchesLbHighlight",
                    "Use Letter Boxed color",
                    "#4C2222",
                    UpdateActiveCustomThemeLbcHighlightMatch
                ),
                CreateThemeColorRow("Headings", "LbcHeadingBackground"),
                CreateThemeColorRow("NYT solution", "NytSolution"),
                CreateThemeColorRow("New word highlight", "NewHighlight"),
                CreateThemeColorRow("Redacted", "Redacted")
            ],
            "Background brightness selects the Light or Dark styling context."
        );''',
'theme group ordering/note cleanup')

# Hide controls replace scale controls. Legacy scale values remain only as migration hints.
replace_once(
'''    let NytHeaderScale = 1.0;
    let NytTitleScale = 1.0;
    let NytFooterScale = 1.0;
    let CompactTitleLayout = false;''',
'''    let NytHeaderScale = 1.0;
    let NytTitleScale = 1.0;
    let NytFooterScale = 1.0;
    let HideNytHeader = false;
    let HideNytGameTitle = false;
    let HideNytFooter = false;
    let CompactTitleLayout = false;''',
'hide globals')

replace_once(
'''        NytFooterScale = GetFiniteGuiNumber(
            "NytFooterScale",
            1.0,
            MinimumNytPageScale,
            MaximumNytPageScale
        );

        CompactTitleLayout = Boolean(''',
'''        NytFooterScale = GetFiniteGuiNumber(
            "NytFooterScale",
            1.0,
            MinimumNytPageScale,
            MaximumNytPageScale
        );

        HideNytHeader = Boolean(
            GetGuiSetting("HideNytHeader", NytHeaderScale <= 0.001)
        );
        HideNytGameTitle = Boolean(
            GetGuiSetting("HideNytGameTitle", NytTitleScale <= 0.001)
        );
        HideNytFooter = Boolean(
            GetGuiSetting("HideNytFooter", NytFooterScale <= 0.001)
        );

        CompactTitleLayout = Boolean(''',
'load hide preferences')

replace_once(
'''    function CreateSettingsCheckbox(LabelText, Checked, OnChange, TitleText = "") {
        const Label = document.createElement("label");
        Label.className = "lb-cubed-settings-checkbox";
        if (TitleText) {
            Label.title = TitleText;
        }

        const Input = document.createElement("input");
        Input.type = "checkbox";
        Input.checked = Boolean(Checked);''',
'''    function CreateSettingsCheckbox(
        LabelText,
        Checked,
        OnChange,
        TitleText = "",
        Disabled = false
    ) {
        const Label = document.createElement("label");
        Label.className = "lb-cubed-settings-checkbox";
        if (TitleText) {
            Label.title = TitleText;
        }

        const Input = document.createElement("input");
        Input.type = "checkbox";
        Input.checked = Boolean(Checked);
        Input.disabled = Boolean(Disabled);
        Label.classList.toggle(
            "lb-cubed-settings-checkbox-disabled",
            Input.disabled
        );''',
'checkbox disabled support')

pattern = re.compile(r'''        const DisplaySection = CreateSettingsSection\("Display"\);.*?\n        const SyncSection = CreateSettingsSection\("Sync"\);''', re.S)
replacement = '''        const DisplaySection = CreateSettingsSection("Display");

        const CompactTitleControl = CreateSettingsCheckbox(
            "Compact game title layout",
            CompactTitleLayout,
            Checked => {
                CompactTitleLayout = Checked;
                SetGuiSetting("CompactTitleLayout", CompactTitleLayout);
                ApplyNytPagePreferences();
            },
            "",
            HideNytGameTitle
        );
        const CompactTitleInput = CompactTitleControl.querySelector('input[type="checkbox"]');
        DisplaySection.appendChild(CompactTitleControl);

        const HideGroup = document.createElement("div");
        HideGroup.className = "lb-cubed-settings-subgroup lb-cubed-hide-settings";
        const HideHeading = document.createElement("div");
        HideHeading.className = "lb-cubed-settings-subgroup-title";
        HideHeading.textContent = "Hide:";

        HideGroup.append(
            HideHeading,
            CreateSettingsCheckbox(
                "Header",
                HideNytHeader,
                Checked => {
                    HideNytHeader = Checked;
                    SetGuiSetting("HideNytHeader", HideNytHeader);
                    ApplyNytPagePreferences();
                }
            ),
            CreateSettingsCheckbox(
                "Game title",
                HideNytGameTitle,
                Checked => {
                    HideNytGameTitle = Checked;
                    SetGuiSetting("HideNytGameTitle", HideNytGameTitle);
                    if (CompactTitleInput) {
                        CompactTitleInput.disabled = HideNytGameTitle;
                    }
                    CompactTitleControl.classList.toggle(
                        "lb-cubed-settings-checkbox-disabled",
                        HideNytGameTitle
                    );
                    ApplyNytPagePreferences();
                }
            ),
            CreateSettingsCheckbox(
                "Yesterday/Help row",
                HideYesterdayHelpRow,
                Checked => {
                    HideYesterdayHelpRow = Checked;
                    SetGuiSetting("HideYesterdayHelpRow", HideYesterdayHelpRow);
                    ApplyNytPagePreferences();
                }
            ),
            CreateSettingsCheckbox(
                "Par",
                HidePar,
                Checked => {
                    HidePar = Checked;
                    SaveHideParPreference();
                    ApplyHideParPreference();
                },
                "Hide NYT's 'Try to solve in X words' par text"
            ),
            CreateSettingsCheckbox(
                "Footer",
                HideNytFooter,
                Checked => {
                    HideNytFooter = Checked;
                    SetGuiSetting("HideNytFooter", HideNytFooter);
                    ApplyNytPagePreferences();
                }
            )
        );
        DisplaySection.appendChild(HideGroup);

        const GapGroup = document.createElement("div");
        GapGroup.className = "lb-cubed-settings-subgroup";

        const GapHeading = document.createElement("div");
        GapHeading.className = "lb-cubed-settings-subgroup-title";
        GapHeading.textContent = "Adjust layout gap between text input and letter box:";

        GapGroup.append(
            GapHeading,
            CreateSettingsCheckbox(
                "Enable draggable grip line",
                AdjustLayoutGap,
                Checked => {
                    AdjustLayoutGap = Checked;
                    SetGuiSetting("AdjustLayoutGap", AdjustLayoutGap);
                    UpdateLayoutGapHandleVisibility();
                    PositionLayoutGapResizeHandle();
                },
                "Show a draggable horizontal grip that adjusts the same gap value as the manual input"
            ),
            CreateSettingsNumberWithReset(
                "Manually set gap",
                GetDisplayedLayoutGapPx(),
                MinimumLayoutGap,
                MaximumLayoutGap,
                1,
                "px",
                0,
                "LayoutGapPx",
                Value => {
                    SetDisplayedLayoutGapPx(Value);
                    SetGuiSetting("LayoutGapPx", LayoutGapPx);
                    UpdatePanelLayout();
                }
            )
        );

        DisplaySection.appendChild(GapGroup);

        const SyncSection = CreateSettingsSection("Sync");'''
text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit(f'Display section replacement failed: {count}')

replace_once(
'''        if (Host) {
            Host.classList.toggle(
                "lb-cubed-compact-title-layout",
                CompactTitleLayout
            );
        }

        if (TitleSection) {
            TitleSection.classList.toggle(
                "lb-cubed-compact-title-section",
                CompactTitleLayout
            );
        }''',
'''        const CompactTitleActive =
            CompactTitleLayout &&
            !HideNytGameTitle;

        if (Host) {
            Host.classList.toggle(
                "lb-cubed-compact-title-layout",
                CompactTitleActive
            );
        }

        if (TitleSection) {
            TitleSection.classList.toggle(
                "lb-cubed-compact-title-section",
                CompactTitleActive
            );
        }''',
'compact hidden-title behavior')

pattern = re.compile(r'''    function EnsureNytPageResizeHandles\(\) \{.*?\n    \}\n\n    function GetNytScaleBySettingName''', re.S)
replacement = '''    function EnsureNytPageResizeHandles() {
        document.getElementById(NytHeaderResizeHandleId)?.remove();
        document.getElementById(NytTitleResizeHandleId)?.remove();
    }

    function GetNytScaleBySettingName'''
text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit('resize-handle removal patch failed')

pattern = re.compile(r'''    function ApplyNytPagePreferences\(\) \{.*?\n    \}\n\n    function EnsureLayoutGapResizeHandle''', re.S)
replacement = '''    function ApplyNytPagePreferences() {
        EnsureNytPageResizeHandles();

        const Targets = GetNytPageTargets();
        const Visibility = [
            [Targets.Header, HideNytHeader],
            [Targets.Title, HideNytGameTitle],
            [Targets.Footer, HideNytFooter]
        ];

        for (const [Element, Hidden] of Visibility) {
            if (!Element) {
                continue;
            }
            Element.classList.toggle(
                "lb-cubed-page-fluff-hidden",
                Boolean(Hidden)
            );
            Element.style.removeProperty("zoom");
        }

        if (Targets.Title) {
            Targets.Title.style.removeProperty("margin-left");
            Targets.Title.style.removeProperty("margin-right");
        }

        ApplyNytTitleArrangement();

        requestAnimationFrame(() => {
            PositionPreviewDebugPane();
            PositionPreviewVersionLabel();
        });
    }

    function EnsureLayoutGapResizeHandle'''
text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit('ApplyNytPagePreferences replacement failed')

replace_once(
'''            NytHeaderScale,
            NytTitleScale,
            NytFooterScale,
            CompactTitleLayout,''',
'''            HideNytHeader,
            HideNytGameTitle,
            HideNytFooter,
            CompactTitleLayout,''',
'init log hide state')

replace_once(
'''            .lb-cubed-settings-checkbox {
                cursor: pointer;
            }
''',
'''            .lb-cubed-settings-checkbox {
                cursor: pointer;
            }

            .lb-cubed-settings-checkbox-disabled {
                opacity: 0.55;
                cursor: not-allowed;
            }

            .lb-cubed-hide-settings .lb-cubed-settings-checkbox {
                padding-left: 12px;
            }
''',
'display settings styling')

source_path.write_text(text, encoding='utf-8')

# Static regression checks for the cleanup.
test_path = Path('tests/final-polish-tests.js')
tests = test_path.read_text(encoding='utf-8')
tests = tests.replace("// @version      1.13.1-beta.25", "// @version      1.13.1-beta.26")
tests = tests.replace("'beta.25 version missing'", "'beta.26 version missing'")
tests = tests.replace(
    "console.log('PASS: beta.25 settings cleanup + cross-mode/theme/toast static checks');",
    "console.log('PASS: beta.26 settings/display cleanup + cross-mode/theme/toast static checks');"
)
extra = '''
assert(source.includes('LbcBackgroundUnlinkedColor'), 'LBC Background unsynced color memory missing');
assert(source.includes('LbcTextUnlinkedColor'), 'LBC Foreground unsynced color memory missing');
assert(source.includes('LbcHighlightUnlinkedColor'), 'LBC Highlight unsynced color memory missing');
assert(source.includes('Background brightness selects the Light or Dark styling context.'), 'LBC section tooltip missing');
assert(!source.includes('Background brightness selects the Light or Dark mapping column.'), 'obsolete theme explainer remains');
assert(source.indexOf('CreateThemeColorRow("Headings", "LbcHeadingBackground")') < source.indexOf('CreateThemeColorRow("NYT solution", "NytSolution")'), 'sequential LBC theme row order is wrong');
assert(source.includes('"Compact game title layout"'), 'compact title label missing');
for (const label of ['"Header"', '"Game title"', '"Yesterday/Help row"', '"Par"', '"Footer"']) assert(source.includes(label), `Hide subgroup item missing ${label}`);
assert(source.includes('HideNytHeader'), 'Hide Header preference missing');
assert(source.includes('HideNytGameTitle'), 'Hide Game title preference missing');
assert(source.includes('HideNytFooter'), 'Hide Footer preference missing');
assert(source.includes('CompactTitleLayout &&\n            !HideNytGameTitle'), 'compact title hidden-state guard missing');
assert(source.includes('document.getElementById(NytHeaderResizeHandleId)?.remove();'), 'header grip removal missing');
assert(source.includes('document.getElementById(NytTitleResizeHandleId)?.remove();'), 'title grip removal missing');
assert(!source.includes('CreateSettingsNumberWithReset(\n                "Header size"'), 'Header size control still present');
assert(!source.includes('CreateSettingsNumberWithReset(\n                "Game title size"'), 'Game title size control still present');
assert(!source.includes('CreateSettingsNumberWithReset(\n                "Footer size"'), 'Footer size control still present');
'''
needle = "console.log('PASS: beta.26 settings/display cleanup + cross-mode/theme/toast static checks');"
if needle not in tests:
    raise SystemExit('test PASS marker missing')
tests = tests.replace(needle, extra + '\n' + needle, 1)
test_path.write_text(tests, encoding='utf-8')
