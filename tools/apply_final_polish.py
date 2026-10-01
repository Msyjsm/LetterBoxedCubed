from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "LetterBoxedCubed.user.js"
PREVIEW = ROOT / "tools" / "preview_runtime.js"
MERGE_TESTS = ROOT / "tests" / "merge-tests.js"
CLOUD_TESTS = ROOT / "tests" / "cloud-sync-tests.js"
FINAL_TESTS = ROOT / "tests" / "final-polish-tests.js"


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


source = SOURCE.read_text(encoding="utf-8")
source = replace_once(
    source,
    "// @version      1.13.1-beta.2",
    "// @version      1.13.1-beta.3",
    "version",
)

source = replace_once(
    source,
    '''    const StackedModeClass = "lb-cubed-stacked-mode";

    const GameGap = 24;
    const LeftColumnGap = 16;
    const EdgePadding = 18;
    const MinimumPanelWidth = 300;
''',
    '''    const StackedModeClass = "lb-cubed-stacked-mode";
    const InternalPanelLayoutModeClasses = [
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

    const GameGap = 24;
    const LeftColumnGap = 16;
    const EdgePadding = 18;
    const MinimumPanelWidth = 300;
''',
    "layout constants",
)

source = replace_once(
    source,
    '''    const ExportFormatName = "LetterBoxedCubedBackup";
    const ExportFormatVersion = 3;
''',
    '''    const ExportFormatName = "LetterBoxedCubedBackup";
    const ExportFormatVersion = 4;
''',
    "backup version",
)

source = replace_once(
    source,
    '''    const GuiStateStorageKey = "LetterBoxedCubed_GuiState";
    const GuiStateVersion = 1;
''',
    '''    const GuiStateStorageKey = "LetterBoxedCubed_GuiState";
    const GuiStateVersion = 1;
    const ThemeStateStorageKey = "LetterBoxedCubed_ThemeState";
    const ThemeStateVersion = 1;
    const DefaultThemeId = "nyt-light";
    const NytDarkThemeId = "nyt-dark-app";

    const PrebuiltThemes = {
        [DefaultThemeId]: {
            Id: DefaultThemeId,
            Name: "NYT Light",
            ApplyNative: false,
            InvertBoard: false,
            Palette: {
                LbPageBackground: "#FFFFFF",
                LbText: "#000000",
                LbSurface: "#FFFFFF",
                LbBorder: "#000000",
                LbcBackground: "#D88482",
                LbcSurface: "#E5A09E",
                LbcText: "#301818",
                LbcMuted: "#684949",
                LbcBorder: "#4C2222",
                LbcAccent: "#5C2525",
                NytSolution: "#DACB77",
                NewHighlight: "#7FFF00",
                Success: "#2D7D3E",
                Danger: "#AF3636"
            }
        },
        [NytDarkThemeId]: {
            Id: NytDarkThemeId,
            Name: "NYT Dark (app)",
            ApplyNative: true,
            InvertBoard: true,
            Palette: {
                LbPageBackground: "#121212",
                LbText: "#F4F4F4",
                LbSurface: "#1C1C1C",
                LbBorder: "#CFCFCF",
                LbcBackground: "#202020",
                LbcSurface: "#2B2B2B",
                LbcText: "#F2F2F2",
                LbcMuted: "#B8B8B8",
                LbcBorder: "#686868",
                LbcAccent: "#D7D7D7",
                NytSolution: "#8E8246",
                NewHighlight: "#8DDA3B",
                Success: "#56A86A",
                Danger: "#D86A6A"
            }
        }
    };
''',
    "theme constants",
)

source = replace_once(
    source,
    '''        LineDrawingSpeedStorageKey,
        GuiStateStorageKey
    ];
''',
    '''        LineDrawingSpeedStorageKey,
        GuiStateStorageKey,
        ThemeStateStorageKey
    ];
''',
    "export theme key",
)

source = replace_once(
    source,
    '''    let PanelWidthPreference = null;
    let PanelResizeState = null;
''',
    '''    let PanelWidthPreference = null;
    let PanelResizeState = null;
    let InternalPanelLayoutMode = null;
''',
    "layout global",
)

source = replace_once(
    source,
    '''    let HidePar = false;
    let LineDrawingSpeed = 1.0;
    let GuiState = null;
''',
    '''    let HidePar = false;
    let LineDrawingSpeed = 1.0;
    let GuiState = null;
    let ThemeState = null;
''',
    "theme global",
)

source = replace_once(
    source,
    '''        RecordBootstrapDiagnostic("initialize-start");
        AddStyles();

        const Ready = await WaitForGame();
''',
    '''        RecordBootstrapDiagnostic("initialize-start");
        LoadThemeState();
        AddStyles();
        ApplyTheme();

        const Ready = await WaitForGame();
''',
    "initialize theme",
)

# Insert theme state implementation before portable GUI state.
theme_code = r'''
    // -------------------------------------------------------------------------
    // Portable color themes
    // -------------------------------------------------------------------------

    function CreateDefaultThemeState() {
        return {
            Version: ThemeStateVersion,
            ActiveTheme: {
                Id: DefaultThemeId,
                UpdatedAt: null
            },
            CustomThemes: {}
        };
    }

    function NormalizeThemeColor(Value, Fallback) {
        const Candidate = String(Value || "").trim().toUpperCase();
        return /^#[0-9A-F]{6}$/.test(Candidate)
            ? Candidate
            : Fallback;
    }

    function NormalizeThemePalette(RawPalette, FallbackPalette = null) {
        const Defaults = FallbackPalette || PrebuiltThemes[DefaultThemeId].Palette;
        const Raw = RawPalette && typeof RawPalette === "object" && !Array.isArray(RawPalette)
            ? RawPalette
            : {};
        const Result = {};

        for (const [Key, DefaultValue] of Object.entries(Defaults)) {
            Result[Key] = NormalizeThemeColor(Raw[Key], DefaultValue);
        }

        return Result;
    }

    function NormalizeCustomThemeRecord(RawTheme, Id) {
        if (!RawTheme || typeof RawTheme !== "object" || Array.isArray(RawTheme)) {
            return null;
        }

        const ThemeId = String(RawTheme.Id || Id || "").trim();
        if (!ThemeId) {
            return null;
        }

        return {
            Id: ThemeId,
            Name: String(RawTheme.Name || "Custom Theme").trim() || "Custom Theme",
            Palette: NormalizeThemePalette(RawTheme.Palette),
            InvertBoard: Boolean(RawTheme.InvertBoard),
            Deleted: Boolean(RawTheme.Deleted),
            UpdatedAt: NormalizeTimestamp(RawTheme.UpdatedAt)
        };
    }

    function NormalizeThemeState(RawState) {
        const Result = CreateDefaultThemeState();

        if (!RawState || typeof RawState !== "object" || Array.isArray(RawState)) {
            return Result;
        }

        const RawActive = RawState.ActiveTheme;
        if (
            RawActive &&
            typeof RawActive === "object" &&
            !Array.isArray(RawActive)
        ) {
            Result.ActiveTheme = {
                Id: String(RawActive.Id || DefaultThemeId).trim() || DefaultThemeId,
                UpdatedAt: NormalizeTimestamp(RawActive.UpdatedAt)
            };
        }

        const RawCustomThemes =
            RawState.CustomThemes &&
            typeof RawState.CustomThemes === "object" &&
            !Array.isArray(RawState.CustomThemes)
                ? RawState.CustomThemes
                : {};

        for (const [Id, RawTheme] of Object.entries(RawCustomThemes)) {
            const Theme = NormalizeCustomThemeRecord(RawTheme, Id);
            if (Theme) {
                Result.CustomThemes[Theme.Id] = Theme;
            }
        }

        return Result;
    }

    function LoadThemeState() {
        const Raw = GM_getValue(ThemeStateStorageKey, null);
        ThemeState = NormalizeThemeState(Raw);

        if (!Raw || Raw.Version !== ThemeStateVersion) {
            SaveThemeState(false);
        }
    }

    function SaveThemeState(QueueSync = true) {
        ThemeState = NormalizeThemeState(ThemeState);
        GM_setValue(ThemeStateStorageKey, ThemeState);

        if (QueueSync) {
            ScheduleCloudSync();
        }
    }

    function GetThemeUpdatedTime(Entry) {
        return GetTimestampMilliseconds(Entry?.UpdatedAt);
    }

    function ChooseNewestThemeEntry(LocalEntry, IncomingEntry) {
        if (!LocalEntry) {
            return CloneValue(IncomingEntry);
        }
        if (!IncomingEntry) {
            return CloneValue(LocalEntry);
        }

        const LocalTime = GetThemeUpdatedTime(LocalEntry);
        const IncomingTime = GetThemeUpdatedTime(IncomingEntry);

        if (IncomingTime !== null && (LocalTime === null || IncomingTime > LocalTime)) {
            return CloneValue(IncomingEntry);
        }
        return CloneValue(LocalEntry);
    }

    function MergeThemeStates(LocalValue, IncomingValue) {
        const Local = NormalizeThemeState(LocalValue);
        const Incoming = NormalizeThemeState(IncomingValue);
        const Result = CreateDefaultThemeState();

        Result.ActiveTheme = ChooseNewestThemeEntry(
            Local.ActiveTheme,
            Incoming.ActiveTheme
        ) || Result.ActiveTheme;

        const ThemeIds = new Set([
            ...Object.keys(Local.CustomThemes),
            ...Object.keys(Incoming.CustomThemes)
        ]);

        for (const Id of ThemeIds) {
            const Chosen = ChooseNewestThemeEntry(
                Local.CustomThemes[Id],
                Incoming.CustomThemes[Id]
            );
            if (Chosen) {
                Result.CustomThemes[Id] = Chosen;
            }
        }

        return Result;
    }

    function GetActiveThemeDefinition() {
        const ActiveId = ThemeState?.ActiveTheme?.Id || DefaultThemeId;

        if (PrebuiltThemes[ActiveId]) {
            return PrebuiltThemes[ActiveId];
        }

        const Custom = ThemeState?.CustomThemes?.[ActiveId];
        if (Custom && !Custom.Deleted) {
            return {
                ...Custom,
                ApplyNative: true
            };
        }

        return PrebuiltThemes[DefaultThemeId];
    }

    function GetActiveCustomThemeRecord() {
        const ActiveId = ThemeState?.ActiveTheme?.Id;
        const Record = ActiveId ? ThemeState?.CustomThemes?.[ActiveId] : null;
        return Record && !Record.Deleted ? Record : null;
    }

    function ApplyTheme() {
        if (!ThemeState) {
            ThemeState = CreateDefaultThemeState();
        }

        const Theme = GetActiveThemeDefinition();
        const Palette = NormalizeThemePalette(Theme.Palette);
        const Root = document.documentElement;

        if (!Root) {
            return;
        }

        const Variables = {
            "--lb-cubed-lb-page-bg": Palette.LbPageBackground,
            "--lb-cubed-lb-text": Palette.LbText,
            "--lb-cubed-lb-surface": Palette.LbSurface,
            "--lb-cubed-lb-border": Palette.LbBorder,
            "--lb-cubed-lbc-bg": Palette.LbcBackground,
            "--lb-cubed-lbc-surface": Palette.LbcSurface,
            "--lb-cubed-lbc-text": Palette.LbcText,
            "--lb-cubed-lbc-muted": Palette.LbcMuted,
            "--lb-cubed-lbc-border": Palette.LbcBorder,
            "--lb-cubed-lbc-accent": Palette.LbcAccent,
            "--lb-cubed-nyt-solution": Palette.NytSolution,
            "--lb-cubed-new-highlight": Palette.NewHighlight,
            "--lb-cubed-success": Palette.Success,
            "--lb-cubed-danger": Palette.Danger,
            "--lb-cubed-board-filter": Theme.InvertBoard
                ? "invert(1) hue-rotate(180deg)"
                : "none"
        };

        for (const [Name, Value] of Object.entries(Variables)) {
            Root.style.setProperty(Name, Value);
        }

        Root.classList.toggle(
            "lb-cubed-native-theme",
            Boolean(Theme.ApplyNative)
        );
        Root.dataset.lbcTheme = Theme.Id || DefaultThemeId;
    }

    function SetActiveTheme(ThemeId) {
        const Id = String(ThemeId || "").trim();
        const IsPrebuilt = Boolean(PrebuiltThemes[Id]);
        const IsCustom = Boolean(ThemeState?.CustomThemes?.[Id] && !ThemeState.CustomThemes[Id].Deleted);

        if (!IsPrebuilt && !IsCustom) {
            return false;
        }

        ThemeState.ActiveTheme = {
            Id,
            UpdatedAt: new Date().toISOString()
        };
        SaveThemeState();
        ApplyTheme();
        return true;
    }

    function CreateCustomThemeFromActive(Name = "Custom Theme") {
        const Base = GetActiveThemeDefinition();
        const Id = `custom-${CreateCloudOpaqueId("theme")}`;
        const Now = new Date().toISOString();

        ThemeState.CustomThemes[Id] = {
            Id,
            Name: String(Name || "Custom Theme").trim() || "Custom Theme",
            Palette: NormalizeThemePalette(Base.Palette),
            InvertBoard: Boolean(Base.InvertBoard),
            Deleted: false,
            UpdatedAt: Now
        };
        ThemeState.ActiveTheme = { Id, UpdatedAt: Now };
        SaveThemeState();
        ApplyTheme();
        return Id;
    }

    function RenameActiveCustomTheme(Name) {
        const Theme = GetActiveCustomThemeRecord();
        if (!Theme) {
            return false;
        }

        Theme.Name = String(Name || "").trim() || Theme.Name;
        Theme.UpdatedAt = new Date().toISOString();
        SaveThemeState();
        return true;
    }

    function DeleteActiveCustomTheme() {
        const Theme = GetActiveCustomThemeRecord();
        if (!Theme) {
            return false;
        }

        const Now = new Date().toISOString();
        Theme.Deleted = true;
        Theme.UpdatedAt = Now;
        ThemeState.ActiveTheme = {
            Id: DefaultThemeId,
            UpdatedAt: Now
        };
        SaveThemeState();
        ApplyTheme();
        return true;
    }

    function UpdateActiveCustomThemePalette(Key, Value, Persist = true) {
        const Theme = GetActiveCustomThemeRecord();
        if (!Theme || !Object.prototype.hasOwnProperty.call(Theme.Palette, Key)) {
            return false;
        }

        Theme.Palette[Key] = NormalizeThemeColor(
            Value,
            Theme.Palette[Key]
        );

        if (Persist) {
            Theme.UpdatedAt = new Date().toISOString();
            SaveThemeState();
        }

        ApplyTheme();
        return true;
    }

    function UpdateActiveCustomThemeBoardInversion(Value) {
        const Theme = GetActiveCustomThemeRecord();
        if (!Theme) {
            return false;
        }

        Theme.InvertBoard = Boolean(Value);
        Theme.UpdatedAt = new Date().toISOString();
        SaveThemeState();
        ApplyTheme();
        return true;
    }

'''
source = replace_once(
    source,
    '''    // -------------------------------------------------------------------------
    // Portable GUI state
    // -------------------------------------------------------------------------
''',
    theme_code + '''    // -------------------------------------------------------------------------
    // Portable GUI state
    // -------------------------------------------------------------------------
''',
    "theme implementation",
)

# Insert theme settings controls before CreateSettingsMenu.
theme_settings_code = r'''
    function CreateThemeColorRow(LabelText, PaletteKey) {
        const Row = document.createElement("label");
        Row.className = "lb-cubed-theme-color-row";

        const Label = document.createElement("span");
        Label.className = "lb-cubed-settings-label";
        Label.textContent = LabelText;

        const Input = document.createElement("input");
        Input.type = "color";
        Input.value = GetActiveCustomThemeRecord()?.Palette?.[PaletteKey] || "#000000";
        Input.addEventListener("input", Event => {
            UpdateActiveCustomThemePalette(PaletteKey, Event.currentTarget.value, false);
        });
        Input.addEventListener("change", Event => {
            UpdateActiveCustomThemePalette(PaletteKey, Event.currentTarget.value, true);
        });

        Row.append(Label, Input);
        return Row;
    }

    function RefreshThemeSettingsSection(Section) {
        Section.replaceChildren();

        const Heading = document.createElement("div");
        Heading.className = "lb-cubed-settings-section-title";
        Heading.textContent = "Theme & colors";

        const ThemeRow = document.createElement("label");
        ThemeRow.className = "lb-cubed-theme-select-row";
        const ThemeLabel = document.createElement("span");
        ThemeLabel.className = "lb-cubed-settings-label";
        ThemeLabel.textContent = "Theme";
        const Select = document.createElement("select");
        Select.className = "lb-cubed-theme-select";

        for (const Theme of Object.values(PrebuiltThemes)) {
            const Option = document.createElement("option");
            Option.value = Theme.Id;
            Option.textContent = Theme.Name;
            Select.appendChild(Option);
        }

        const CustomThemes = Object.values(ThemeState?.CustomThemes || {})
            .filter(Theme => !Theme.Deleted)
            .sort((A, B) => Alphabetically(A.Name, B.Name));

        if (CustomThemes.length) {
            const Group = document.createElement("optgroup");
            Group.label = "Custom";
            for (const Theme of CustomThemes) {
                const Option = document.createElement("option");
                Option.value = Theme.Id;
                Option.textContent = Theme.Name;
                Group.appendChild(Option);
            }
            Select.appendChild(Group);
        }

        const ActiveId = GetActiveThemeDefinition().Id;
        Select.value = ActiveId;
        Select.addEventListener("change", () => {
            SetActiveTheme(Select.value);
            RefreshThemeSettingsSection(Section);
        });
        ThemeRow.append(ThemeLabel, Select);

        const Buttons = document.createElement("div");
        Buttons.className = "lb-cubed-settings-button-row lb-cubed-theme-actions";

        const Duplicate = document.createElement("button");
        Duplicate.type = "button";
        Duplicate.className = "lb-cubed-header-button";
        Duplicate.textContent = "New from current";
        Duplicate.title = "Create a custom theme from the colors currently in use";
        Duplicate.addEventListener("click", Event => {
            Event.preventDefault();
            const Suggested = `${GetActiveThemeDefinition().Name || "Theme"} Custom`;
            const Name = prompt("Name the new custom color theme:", Suggested);
            if (Name === null) {
                return;
            }
            CreateCustomThemeFromActive(Name);
            RefreshThemeSettingsSection(Section);
        });
        Buttons.appendChild(Duplicate);

        const ActiveCustom = GetActiveCustomThemeRecord();
        if (ActiveCustom) {
            const Rename = document.createElement("button");
            Rename.type = "button";
            Rename.className = "lb-cubed-header-button";
            Rename.textContent = "Rename";
            Rename.addEventListener("click", Event => {
                Event.preventDefault();
                const Name = prompt("Rename this custom theme:", ActiveCustom.Name);
                if (Name !== null && RenameActiveCustomTheme(Name)) {
                    RefreshThemeSettingsSection(Section);
                }
            });

            const Delete = document.createElement("button");
            Delete.type = "button";
            Delete.className = "lb-cubed-header-button";
            Delete.textContent = "Delete";
            Delete.addEventListener("click", Event => {
                Event.preventDefault();
                if (confirm(`Delete custom theme "${ActiveCustom.Name}"?`)) {
                    DeleteActiveCustomTheme();
                    RefreshThemeSettingsSection(Section);
                }
            });
            Buttons.append(Rename, Delete);
        }

        Section.append(Heading, ThemeRow, Buttons);

        if (!ActiveCustom) {
            const Note = document.createElement("div");
            Note.className = "lb-cubed-theme-note";
            Note.textContent = GetActiveThemeDefinition().Id === NytDarkThemeId
                ? "App-inspired NYT dark colors on web. Duplicate this theme to tune individual colors."
                : "Prebuilt themes are read-only. Use New from current to make an editable copy.";
            Section.appendChild(Note);
            return;
        }

        const Groups = [
            ["Letter Boxed", [
                ["Page background", "LbPageBackground"],
                ["Text", "LbText"],
                ["Surface", "LbSurface"],
                ["Border", "LbBorder"]
            ]],
            ["Letter Boxed Cubed", [
                ["Background", "LbcBackground"],
                ["Surface", "LbcSurface"],
                ["Text", "LbcText"],
                ["Muted text", "LbcMuted"],
                ["Border", "LbcBorder"],
                ["Accent", "LbcAccent"]
            ]],
            ["Highlights", [
                ["NYT solution", "NytSolution"],
                ["New item", "NewHighlight"],
                ["Success", "Success"],
                ["Error", "Danger"]
            ]]
        ];

        for (const [Title, Fields] of Groups) {
            const Group = document.createElement("div");
            Group.className = "lb-cubed-settings-subgroup lb-cubed-theme-color-group";
            const GroupTitle = document.createElement("div");
            GroupTitle.className = "lb-cubed-settings-subgroup-title";
            GroupTitle.textContent = Title;
            Group.appendChild(GroupTitle);
            for (const [Label, Key] of Fields) {
                Group.appendChild(CreateThemeColorRow(Label, Key));
            }
            Section.appendChild(Group);
        }

        Section.appendChild(
            CreateSettingsCheckbox(
                "Invert Letter Boxed board/canvas",
                ActiveCustom.InvertBoard,
                Checked => UpdateActiveCustomThemeBoardInversion(Checked),
                "Useful for dark palettes; intentionally optional for delightfully terrible custom schemes"
            )
        );
    }

    function CreateThemeSettingsSection() {
        const Section = document.createElement("section");
        Section.className = "lb-cubed-settings-section";
        RefreshThemeSettingsSection(Section);
        return Section;
    }

'''
source = replace_once(
    source,
    '''    function CreateSettingsMenu() {
''',
    theme_settings_code + '''    function CreateSettingsMenu() {
''',
    "theme settings helpers",
)

source = replace_once(
    source,
    '''        const DisplaySection = CreateSettingsSection("Display");
''',
    '''        const ThemeSection = CreateThemeSettingsSection();

        const DisplaySection = CreateSettingsSection("Display");
''',
    "theme section create",
)

source = replace_once(
    source,
    '''        Menu.append(
            AnimationSection,
            DisplaySection,
            SyncSection
        );
''',
    '''        Menu.append(
            AnimationSection,
            ThemeSection,
            DisplaySection,
            SyncSection
        );
''',
    "theme section append",
)

# Backup payload + migration/merge integration.
source = replace_once(
    source,
    '''            GuiState: StorageSnapshot[GuiStateStorageKey] ||
                CreateEmptyGuiState(),
            CustomDictionary: Array.isArray(
''',
    '''            GuiState: StorageSnapshot[GuiStateStorageKey] ||
                CreateEmptyGuiState(),
            ThemeState: StorageSnapshot[ThemeStateStorageKey] ||
                CreateDefaultThemeState(),
            CustomDictionary: Array.isArray(
''',
    "cloud top-level theme",
)

source = replace_once(
    source,
    '''            GuiState: NormalizeGuiState(
                StorageSnapshot[GuiStateStorageKey]
            ),
            CustomDictionary: Array.isArray(
''',
    '''            GuiState: NormalizeGuiState(
                StorageSnapshot[GuiStateStorageKey]
            ),
            ThemeState: NormalizeThemeState(
                StorageSnapshot[ThemeStateStorageKey]
            ),
            CustomDictionary: Array.isArray(
''',
    "export top-level theme",
)

source = replace_once(
    source,
    '''    const BackupMigrations = {
        1: MigrateBackupV1ToV2,
        2: MigrateBackupV2ToV3
    };
''',
    '''    const BackupMigrations = {
        1: MigrateBackupV1ToV2,
        2: MigrateBackupV2ToV3,
        3: MigrateBackupV3ToV4
    };
''',
    "migration table",
)

migration_v4 = r'''

    function MigrateBackupV3ToV4(V3) {
        const Snapshot =
            V3.StorageSnapshot &&
            typeof V3.StorageSnapshot === "object" &&
            !Array.isArray(V3.StorageSnapshot)
                ? structuredClone(V3.StorageSnapshot)
                : {};
        const MigratedThemeState = NormalizeThemeState(
            Snapshot[ThemeStateStorageKey] || V3.ThemeState
        );

        Snapshot[ThemeStateStorageKey] = MigratedThemeState;

        return {
            ...V3,
            FormatVersion: 4,
            ThemeState: MigratedThemeState,
            StorageSnapshot: Snapshot
        };
    }
'''
source = replace_once(
    source,
    '''    function IsAllowedExportStorageKey(Key) {
''',
    migration_v4 + '''
    function IsAllowedExportStorageKey(Key) {
''',
    "v4 migration",
)

source = replace_once(
    source,
    '''        if (Key === GuiStateStorageKey) {
            return MergeGuiStates(LocalValue, IncomingValue);
        }

        if (Key.startsWith(PuzzleMetadataPrefix)) {
''',
    '''        if (Key === GuiStateStorageKey) {
            return MergeGuiStates(LocalValue, IncomingValue);
        }

        if (Key === ThemeStateStorageKey) {
            return MergeThemeStates(LocalValue, IncomingValue);
        }

        if (Key.startsWith(PuzzleMetadataPrefix)) {
''',
    "theme merge dispatch",
)

source = replace_once(
    source,
    '''    function ReloadRuntimeStateFromStorage() {
        LoadGuiState();
        LoadQolPreferences();
''',
    '''    function ReloadRuntimeStateFromStorage() {
        LoadThemeState();
        ApplyTheme();
        LoadGuiState();
        LoadQolPreferences();
''',
    "reload theme",
)

source = replace_once(
    source,
    '''                `Remote revision ${CloudSyncConflictRevision} changed in another LBC session; automatic uploads are paused until manual Sync reconciles it.`
''',
    '''                `Drive revision ${CloudSyncConflictRevision} differs from this session's expected revision; automatic uploads are paused until manual Sync reconciles it.`
''',
    "conflict tooltip wording",
)

# Issue 15: coherent internal layout modes + hysteresis.
source = replace_once(
    source,
    '''    function UpdatePanelLayout() {
        const GameContainer = document.querySelector(".lb-game-container");
        const WordContainer = GameContainer?.querySelector(".lb-word-container");
        const SquareContainer = GameContainer?.querySelector(".lb-square-container");
        const Panel = document.getElementById(PanelId);

        if (!GameContainer || !WordContainer || !SquareContainer || !Panel) {
            return;
        }

        const MaximumSidePanelWidth = GetMaximumSidePanelWidth(GameContainer);

        if (MaximumSidePanelWidth >= MinimumPanelWidth) {
            ApplySideLayout(
                GameContainer,
                WordContainer,
                SquareContainer,
                Panel,
                MaximumSidePanelWidth
            );
        } else {
            ApplyStackedLayout(
                GameContainer,
                WordContainer,
                SquareContainer,
                Panel
            );
        }

        UpdateLayoutGapHandleVisibility();
''',
    '''    function GetNextInternalPanelLayoutMode(PanelWidth) {
        const Width = Math.max(0, Number(PanelWidth) || 0);
        const T = InternalPanelLayoutThresholds;

        if (!InternalPanelLayoutMode) {
            if (Width >= T.MediumToWide) {
                return "wide";
            }
            return Width >= T.NarrowToMedium
                ? "medium"
                : "narrow";
        }

        if (InternalPanelLayoutMode === "narrow") {
            if (Width >= T.MediumToWide) {
                return "wide";
            }
            return Width >= T.NarrowToMedium
                ? "medium"
                : "narrow";
        }

        if (InternalPanelLayoutMode === "wide") {
            if (Width < T.MediumToNarrow) {
                return "narrow";
            }
            return Width < T.WideToMedium
                ? "medium"
                : "wide";
        }

        if (Width >= T.MediumToWide) {
            return "wide";
        }
        if (Width < T.MediumToNarrow) {
            return "narrow";
        }
        return "medium";
    }

    function UpdateInternalPanelLayout(Panel, PanelWidth) {
        const NextMode = GetNextInternalPanelLayoutMode(PanelWidth);

        if (InternalPanelLayoutMode !== NextMode) {
            InternalPanelLayoutMode = NextMode;
        }

        for (const ClassName of InternalPanelLayoutModeClasses) {
            Panel.classList.remove(ClassName);
        }
        Panel.classList.add(`lb-cubed-layout-${InternalPanelLayoutMode}`);
        Panel.dataset.cubedLayoutMode = InternalPanelLayoutMode;
    }

    function UpdatePanelLayout() {
        const GameContainer = document.querySelector(".lb-game-container");
        const WordContainer = GameContainer?.querySelector(".lb-word-container");
        const SquareContainer = GameContainer?.querySelector(".lb-square-container");
        const Panel = document.getElementById(PanelId);

        if (!GameContainer || !WordContainer || !SquareContainer || !Panel) {
            return;
        }

        const MaximumSidePanelWidth = GetMaximumSidePanelWidth(GameContainer);
        let RenderedPanelWidth;

        if (MaximumSidePanelWidth >= MinimumPanelWidth) {
            RenderedPanelWidth = ApplySideLayout(
                GameContainer,
                WordContainer,
                SquareContainer,
                Panel,
                MaximumSidePanelWidth
            );
        } else {
            RenderedPanelWidth = ApplyStackedLayout(
                GameContainer,
                WordContainer,
                SquareContainer,
                Panel
            );
        }

        UpdateInternalPanelLayout(Panel, RenderedPanelWidth);
        UpdateLayoutGapHandleVisibility();
''',
    "layout updater",
)

source = replace_once(
    source,
    '''        Panel.style.removeProperty("max-height");
    }

    function ApplyStackedLayout(
''',
    '''        Panel.style.removeProperty("max-height");
        return PanelWidth;
    }

    function ApplyStackedLayout(
''',
    "side layout return",
)

source = replace_once(
    source,
    '''            Panel.style.height = `${PlayHeight}px`;
            Panel.style.maxHeight = `${PlayHeight}px`;
        });
    }

    // -------------------------------------------------------------------------
    // Panel edge resizing
''',
    '''            Panel.style.height = `${PlayHeight}px`;
            Panel.style.maxHeight = `${PlayHeight}px`;
        });

        return StackedWidth;
    }

    // -------------------------------------------------------------------------
    // Panel edge resizing
''',
    "stacked layout return",
)

# Replace the old many-breakpoint container-query cascade at the end of CSS.
css_start_marker = '''            /*
                ================================================================
                LBC CONTAINER-QUERY CASCADE
                ================================================================
'''
css_start = source.find(css_start_marker)
if css_start < 0:
    raise RuntimeError("responsive CSS start marker not found")
css_end = source.find("\n        `;", css_start)
if css_end < 0:
    raise RuntimeError("responsive CSS end marker not found")
new_tail_css = r'''            /*
                ================================================================
                COHERENT INTERNAL LBC LAYOUT MODES (ISSUE #15)
                ================================================================

                JavaScript chooses one of three modes with hysteresis. The
                panel width itself remains continuous while related sections
                move as a group only after crossing a mode boundary.
            */

            #${PanelId}.lb-cubed-layout-narrow .lb-cubed-dashboard-grid {
                grid-template-columns: minmax(0, 1fr);
                grid-template-areas:
                    "stats"
                    "hints"
                    "twofers"
                    "length"
                    "found"
                    "unfound";
            }

            #${PanelId}.lb-cubed-layout-narrow .lb-cubed-word-tree {
                max-width: none;
            }

            #${PanelId}.lb-cubed-layout-narrow .lb-cubed-header {
                flex-direction: column;
            }

            #${PanelId}.lb-cubed-layout-narrow .lb-cubed-header-actions {
                width: 100%;
                justify-content: flex-start;
                flex-wrap: wrap;
            }

            #${PanelId}.lb-cubed-layout-narrow .lb-cubed-title-row {
                flex-wrap: wrap;
            }

            #${PanelId}.lb-cubed-layout-narrow .lb-cubed-settings-panel {
                left: 0;
                right: auto;
                width: min(340px, calc(100vw - 36px));
            }

            #${PanelId}.lb-cubed-layout-medium .lb-cubed-stat-grid,
            #${PanelId}.lb-cubed-layout-wide .lb-cubed-stat-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            #${PanelId}.lb-cubed-layout-medium .lb-cubed-dashboard-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
                grid-template-areas:
                    "stats stats"
                    "hints twofers"
                    "length length"
                    "found unfound";
            }

            #${PanelId}.lb-cubed-layout-wide .lb-cubed-dashboard-grid {
                grid-template-columns:
                    minmax(250px, 2fr)
                    minmax(135px, 1fr)
                    minmax(220px, 1.6fr)
                    minmax(135px, 1fr);
                grid-template-areas:
                    "stats hints twofers length"
                    "found unfound . .";
            }

            #${PanelId}.lb-cubed-layout-medium .lb-cubed-word-tree,
            #${PanelId}.lb-cubed-layout-wide .lb-cubed-word-tree {
                max-width: 220px;
            }

            /*
                ================================================================
                COLOR THEMES (ISSUE #30)
                ================================================================
            */

            html.lb-cubed-native-theme,
            html.lb-cubed-native-theme body,
            html.lb-cubed-native-theme .pz-page,
            html.lb-cubed-native-theme .pz-content,
            html.lb-cubed-native-theme main {
                background: var(--lb-cubed-lb-page-bg) !important;
                color: var(--lb-cubed-lb-text) !important;
            }

            html.lb-cubed-native-theme header.pz-header,
            html.lb-cubed-native-theme #portal-game-header,
            html.lb-cubed-native-theme #letter-boxed-container,
            html.lb-cubed-native-theme footer.pz-footer,
            html.lb-cubed-native-theme .lb-game-container,
            html.lb-cubed-native-theme .lb-word-container,
            html.lb-cubed-native-theme .lb-list-container {
                background-color: var(--lb-cubed-lb-page-bg) !important;
                color: var(--lb-cubed-lb-text) !important;
                border-color: var(--lb-cubed-lb-border) !important;
            }

            html.lb-cubed-native-theme .lb-text-field,
            html.lb-cubed-native-theme .lb-text-field-wrapper,
            html.lb-cubed-native-theme .lb-word-list-container,
            html.lb-cubed-native-theme .lb-message-box,
            html.lb-cubed-native-theme button:not([id^="lb-cubed"]),
            html.lb-cubed-native-theme [role="button"]:not([class*="lb-cubed"]) {
                background-color: var(--lb-cubed-lb-surface) !important;
                color: var(--lb-cubed-lb-text) !important;
                border-color: var(--lb-cubed-lb-border) !important;
            }

            html.lb-cubed-native-theme .lb-word-list,
            html.lb-cubed-native-theme .lb-word-list-length,
            html.lb-cubed-native-theme .lb-par,
            html.lb-cubed-native-theme input {
                color: var(--lb-cubed-lb-text) !important;
            }

            html.lb-cubed-native-theme .lb-square-container canvas {
                filter: var(--lb-cubed-board-filter, none);
            }

            #${PanelId},
            #${HistoryOverlayId} {
                color: var(--lb-cubed-lbc-text, #301818);
            }

            #${PanelContentId},
            .lb-cubed-history-modal {
                background: var(--lb-cubed-lbc-bg, #D88482) !important;
                color: var(--lb-cubed-lbc-text, #301818) !important;
                border-color: var(--lb-cubed-lbc-border, #4C2222) !important;
            }

            .lb-cubed-settings-panel {
                background: var(--lb-cubed-lbc-surface, #E5A09E) !important;
                color: var(--lb-cubed-lbc-text, #301818) !important;
                border-color: var(--lb-cubed-lbc-border, #4C2222) !important;
            }

            #${PanelId} .lb-cubed-stat,
            #${PanelId} .lb-cubed-tree,
            #${PanelId} .lb-cubed-nested-tree,
            #${PanelId} .lb-cubed-twofer-solution-indicator,
            #${PanelId} .lb-cubed-length-stat,
            #${HistoryOverlayId} .lb-cubed-stat,
            #${HistoryOverlayId} .lb-cubed-history-section {
                border-color: color-mix(in srgb, var(--lb-cubed-lbc-border) 70%, transparent) !important;
            }

            #${PanelId} .lb-cubed-tree > summary,
            #${PanelId} .lb-cubed-nested-tree > summary,
            #${HistoryOverlayId} .lb-cubed-history-section-title,
            #${HistoryOverlayId} .lb-cubed-history-navigation {
                background: color-mix(in srgb, var(--lb-cubed-lbc-surface) 72%, var(--lb-cubed-lbc-bg)) !important;
                color: var(--lb-cubed-lbc-text) !important;
            }

            #${PanelId} .lb-cubed-header-button,
            #${PanelId} .lb-cubed-settings-mini-button,
            #${HistoryOverlayId} .lb-cubed-header-button,
            #${PanelId} .lb-cubed-twofer-group-button {
                background: color-mix(in srgb, var(--lb-cubed-lbc-surface) 78%, var(--lb-cubed-lbc-bg)) !important;
                color: var(--lb-cubed-lbc-text) !important;
                border-color: color-mix(in srgb, var(--lb-cubed-lbc-border) 70%, transparent) !important;
            }

            #${PanelId} .lb-cubed-settings-section-title,
            #${PanelId} .lb-cubed-settings-subgroup-title,
            #${PanelId} .lb-cubed-settings-checkbox,
            #${PanelId} .lb-cubed-settings-range,
            #${PanelId} .lb-cubed-settings-number-row,
            #${PanelId} .lb-cubed-settings-action-row,
            #${PanelId} .lb-cubed-stat-value,
            #${PanelId} .lb-cubed-twofer-solution-text,
            #${PanelId} .lb-cubed-length-value,
            #${PanelId} .lb-cubed-invalid-word,
            #${PanelId} .lb-cubed-line-speed-value,
            #${HistoryOverlayId} .lb-cubed-history-title,
            #${HistoryOverlayId} .lb-cubed-history-puzzle-title,
            #${HistoryOverlayId} .lb-cubed-history-position {
                color: var(--lb-cubed-lbc-text) !important;
            }

            #${PanelId} .lb-cubed-subtitle,
            #${PanelId} .lb-cubed-drive-status,
            #${PanelId} .lb-cubed-stat-label,
            #${PanelId} .lb-cubed-potential-word,
            #${PanelId} .lb-cubed-potential-word-progress,
            #${PanelId} .lb-cubed-twofer-disclaimer,
            #${PanelId} .lb-cubed-twofer-group-title,
            #${PanelId} .lb-cubed-length-label,
            #${PanelId} .lb-cubed-empty,
            #${PanelId} .lb-cubed-settings-suffix,
            #${PanelId} .lb-cubed-theme-note,
            #${HistoryOverlayId} .lb-cubed-history-cloud-label,
            #${HistoryOverlayId} .lb-cubed-history-puzzle-meta,
            #${HistoryOverlayId} .lb-cubed-history-empty {
                color: var(--lb-cubed-lbc-muted) !important;
            }

            #${PanelId} .lb-cubed-found-word,
            #${PanelId} .lb-cubed-twofer-revealed,
            #${PanelId} .lb-cubed-potential-word-found,
            #${HistoryOverlayId} .lb-cubed-found-word,
            #${HistoryOverlayId} .lb-cubed-twofer-revealed {
                background: color-mix(in srgb, var(--lb-cubed-lbc-surface) 80%, var(--lb-cubed-lbc-bg)) !important;
                color: var(--lb-cubed-lbc-text) !important;
            }

            #${PanelId} .lb-cubed-found-word.lb-cubed-word-previously-found,
            #${PanelId} .lb-cubed-potential-word.lb-cubed-potential-word-previously-found,
            #${PanelId} .lb-cubed-twofer-word.lb-cubed-twofer-word-previously-found,
            #${HistoryOverlayId} .lb-cubed-word-previously-found,
            #${HistoryOverlayId} .lb-cubed-twofer-word-previously-found {
                background: color-mix(in srgb, var(--lb-cubed-lbc-accent) 18%, var(--lb-cubed-lbc-bg)) !important;
            }

            #${PanelId} .lb-cubed-twofer-status-yes {
                background: var(--lb-cubed-success) !important;
            }

            #${PanelId} .lb-cubed-twofer-status-no {
                background: var(--lb-cubed-danger) !important;
            }

            #${PanelId} .lb-cubed-nyt-solution,
            #${HistoryOverlayId} .lb-cubed-history-custom-word {
                background-color: var(--lb-cubed-nyt-solution) !important;
            }

            #${PanelId} .lb-cubed-nyt-solution-label {
                color: color-mix(in srgb, var(--lb-cubed-lbc-text) 85%, #000000) !important;
            }

            @keyframes lb-cubed-new-highlight-fade-themed {
                from {
                    box-shadow: inset 0 0 0 9999px var(--lb-cubed-new-highlight);
                }
                to {
                    box-shadow: inset 0 0 0 9999px color-mix(in srgb, var(--lb-cubed-new-highlight) 0%, transparent);
                }
            }

            #${PanelId} .lb-cubed-new-highlight {
                animation-name: lb-cubed-new-highlight-fade-themed !important;
            }

            .lb-cubed-theme-select-row,
            .lb-cubed-theme-color-row {
                display: flex;
                align-items: center;
                gap: 6px;
                min-height: 30px;
                color: var(--lb-cubed-lbc-text, #301818);
                font-size: 12px;
            }

            .lb-cubed-theme-select {
                flex: 0 1 180px;
                min-width: 110px;
                padding: 3px 5px;
                border: 1px solid var(--lb-cubed-lbc-border, #4C2222);
                border-radius: 3px;
                background: var(--lb-cubed-lbc-surface, #E5A09E);
                color: var(--lb-cubed-lbc-text, #301818);
            }

            .lb-cubed-theme-color-row input[type="color"] {
                width: 42px;
                height: 26px;
                padding: 1px;
                border: 1px solid var(--lb-cubed-lbc-border, #4C2222);
                border-radius: 3px;
                background: transparent;
                cursor: pointer;
            }

            .lb-cubed-theme-note {
                margin-top: 5px;
                font-size: 10px;
                font-style: italic;
                line-height: 1.35;
            }
'''
source = source[:css_start] + new_tail_css + source[css_end:]

SOURCE.write_text(source, encoding="utf-8")

# ---------------------------------------------------------------------------
# Preview-only reusable diagnostics toolkit (issue #20)
# ---------------------------------------------------------------------------
preview = PREVIEW.read_text(encoding="utf-8")
preview = replace_once(
    preview,
    '''    const PreviewDebugMutationLog = [];

    const BootstrapDiagnostics = [];
''',
    '''    const PreviewDebugMutationLog = [];
    const PreviewTransientTrace = [];
    const PreviewTransientTraceSignatures = new Map();
    let PreviewTransientObserver = null;
    let PreviewTransientAnimationHandler = null;
    let PreviewTransientTraceActive = false;

    const BootstrapDiagnostics = [];
''',
    "preview transient globals",
)

preview = replace_once(
    preview,
    '''    function QueuePreviewDebugRender() {
        if (UserscriptBuildChannel !== "preview") {
            return;
        }

        clearTimeout(PreviewDebugRenderTimer);
''',
    '''    function QueuePreviewDebugRender() {
        if (
            UserscriptBuildChannel !== "preview" ||
            !PreviewDebugPaneVisible
        ) {
            return;
        }

        clearTimeout(PreviewDebugRenderTimer);
''',
    "hidden preview render optimization",
)

preview_diagnostics = r'''
    // -------------------------------------------------------------------------
    // Preview-only reusable diagnostics toolkit (issue #20)
    // -------------------------------------------------------------------------

    function RoundPreviewNumber(Value) {
        return Number.isFinite(Number(Value))
            ? Math.round(Number(Value) * 10) / 10
            : null;
    }

    function GetPreviewElementGeometry(ElementNode) {
        if (!ElementNode || typeof ElementNode.getBoundingClientRect !== "function") {
            return null;
        }

        const Rect = ElementNode.getBoundingClientRect();
        const Style = getComputedStyle(ElementNode);
        return {
            Tag: ElementNode.tagName?.toLowerCase() || null,
            Id: ElementNode.id || null,
            ClassName: String(ElementNode.className || "").slice(0, 300),
            Rect: {
                Left: RoundPreviewNumber(Rect.left),
                Top: RoundPreviewNumber(Rect.top),
                Right: RoundPreviewNumber(Rect.right),
                Bottom: RoundPreviewNumber(Rect.bottom),
                Width: RoundPreviewNumber(Rect.width),
                Height: RoundPreviewNumber(Rect.height)
            },
            Style: {
                Display: Style.display,
                Position: Style.position,
                Visibility: Style.visibility,
                OverflowX: Style.overflowX,
                OverflowY: Style.overflowY,
                MarginTop: Style.marginTop,
                MarginBottom: Style.marginBottom
            }
        };
    }

    function GetPreviewGeometrySnapshot() {
        const Selectors = {
            GameContainer: ".lb-game-container",
            WordContainer: ".lb-game-container .lb-word-container",
            TextFieldWrapper: ".lb-game-container .lb-text-field-wrapper",
            TextField: ".lb-game-container .lb-text-field",
            ListContainer: ".lb-game-container .lb-list-container",
            WordListContainer: ".lb-game-container .lb-word-list-container",
            WordList: ".lb-game-container .lb-word-list",
            SquareContainer: ".lb-game-container .lb-square-container",
            LayoutGapHandle: `#${LayoutGapHandleId}`,
            LbcPanel: `#${PanelId}`
        };
        const Elements = {};

        for (const [Name, Selector] of Object.entries(Selectors)) {
            Elements[Name] = GetPreviewElementGeometry(
                document.querySelector(Selector)
            );
        }

        const Feedback = [...document.querySelectorAll(
            ".lb-message-box, .lb-cubed-valid-feedback-proxy, [role='status'], [role='alert'], [aria-live]"
        )]
            .filter(ElementNode => {
                const Style = getComputedStyle(ElementNode);
                const Rect = ElementNode.getBoundingClientRect();
                return Style.display !== "none" &&
                    Style.visibility !== "hidden" &&
                    Rect.width > 0 && Rect.height > 0;
            })
            .slice(0, 20)
            .map(GetPreviewElementGeometry);

        const TiBottom = Elements.WordContainer?.Rect?.Bottom ?? null;
        const HistoryBottom = Elements.ListContainer?.Rect?.Bottom ?? null;
        const GbTop = Elements.SquareContainer?.Rect?.Top ?? null;
        const GripTop = Elements.LayoutGapHandle?.Rect?.Top ?? null;
        const GripY = GripTop === null ? null : GripTop + 5;

        return {
            CapturedAt: new Date().toISOString(),
            Elements,
            Feedback,
            Relationships: {
                TiBottom,
                HistoryBottom,
                GripY: RoundPreviewNumber(GripY),
                GbVisibleTop: GbTop,
                HistoryToGrip: HistoryBottom === null || GripY === null
                    ? null
                    : RoundPreviewNumber(GripY - HistoryBottom),
                GripToGb: GripY === null || GbTop === null
                    ? null
                    : RoundPreviewNumber(GbTop - GripY),
                HistoryToGb: HistoryBottom === null || GbTop === null
                    ? null
                    : RoundPreviewNumber(GbTop - HistoryBottom)
            }
        };
    }

    function IsPreviewElementLike(Node) {
        return Boolean(
            Node &&
            Node.nodeType === 1 &&
            typeof Node.matches === "function"
        );
    }

    const PreviewTransientSelector =
        ".lb-message-box, .lb-cubed-valid-feedback-proxy, [role='status'], [role='alert'], [aria-live]";

    function GetPreviewTransientLabel(ElementNode) {
        if (!IsPreviewElementLike(ElementNode)) {
            return "element";
        }
        if (ElementNode.matches(".lb-cubed-valid-feedback-proxy")) {
            return "Cubed proxy";
        }
        if (ElementNode.matches(".lb-message-box")) {
            return "native toast";
        }
        return "live region";
    }

    function GetPreviewTransientDescription(ElementNode) {
        if (!IsPreviewElementLike(ElementNode)) {
            return null;
        }

        const Text = String(ElementNode.textContent || "")
            .replace(/\s+/g, " ")
            .trim()
            .slice(0, 160);
        return {
            Kind: GetPreviewTransientLabel(ElementNode),
            Tag: ElementNode.tagName.toLowerCase(),
            Id: ElementNode.id || null,
            Classes: [...ElementNode.classList].slice(0, 8),
            Text
        };
    }

    function RecordPreviewTransientEvent(Action, ElementNode, Detail = null) {
        const Description = GetPreviewTransientDescription(ElementNode);
        if (!Description) {
            return;
        }

        const Signature = JSON.stringify([
            Action,
            Description.Kind,
            Description.Id,
            Description.Classes,
            Description.Text,
            Detail
        ]);
        const Now = Date.now();
        const LastAt = PreviewTransientTraceSignatures.get(Signature) || 0;

        if (Now - LastAt < 120) {
            return;
        }
        PreviewTransientTraceSignatures.set(Signature, Now);

        PreviewTransientTrace.push({
            Timestamp: new Date().toISOString(),
            Action,
            Detail,
            Element: Description
        });

        if (PreviewTransientTrace.length > 250) {
            PreviewTransientTrace.splice(0, PreviewTransientTrace.length - 250);
        }
        UpdatePreviewDiagnosticsStatus();
    }

    function VisitPreviewTransientElements(Node, Callback) {
        if (!IsPreviewElementLike(Node)) {
            return;
        }

        if (Node.matches(PreviewTransientSelector)) {
            Callback(Node);
        }

        for (const Child of Node.querySelectorAll(PreviewTransientSelector)) {
            Callback(Child);
        }
    }

    function StartPreviewTransientElementTrace() {
        PreviewTransientObserver?.disconnect();
        if (PreviewTransientAnimationHandler) {
            document.removeEventListener(
                "animationstart",
                PreviewTransientAnimationHandler,
                true
            );
        }

        PreviewTransientTrace.length = 0;
        PreviewTransientTraceSignatures.clear();
        PreviewTransientTraceActive = true;

        const Root = document.querySelector(".lb-game-container") || document.body;
        PreviewTransientObserver = new MutationObserver(Mutations => {
            for (const Mutation of Mutations) {
                if (Mutation.type === "childList") {
                    for (const Node of Mutation.addedNodes) {
                        VisitPreviewTransientElements(Node, ElementNode =>
                            RecordPreviewTransientEvent("created", ElementNode)
                        );
                    }
                    for (const Node of Mutation.removedNodes) {
                        VisitPreviewTransientElements(Node, ElementNode =>
                            RecordPreviewTransientEvent("removed", ElementNode)
                        );
                    }
                } else if (Mutation.type === "attributes") {
                    const Target = Mutation.target;
                    if (IsPreviewElementLike(Target) && Target.matches(PreviewTransientSelector)) {
                        const IsProxyMove =
                            Target.matches(".lb-cubed-valid-feedback-proxy") &&
                            Mutation.attributeName === "style";
                        RecordPreviewTransientEvent(
                            IsProxyMove ? "repositioned" : "changed",
                            Target,
                            `@${Mutation.attributeName}`
                        );
                    }
                } else if (Mutation.type === "characterData") {
                    const Parent = Mutation.target?.parentElement;
                    if (IsPreviewElementLike(Parent) && Parent.matches(PreviewTransientSelector)) {
                        RecordPreviewTransientEvent("text changed", Parent);
                    }
                }
            }
        });

        PreviewTransientObserver.observe(Root, {
            childList: true,
            subtree: true,
            characterData: true,
            attributes: true,
            attributeFilter: [
                "class",
                "style",
                "hidden",
                "aria-hidden",
                "role",
                "aria-live"
            ]
        });

        PreviewTransientAnimationHandler = Event => {
            const Target = Event.target;
            if (IsPreviewElementLike(Target) && Target.matches(PreviewTransientSelector)) {
                RecordPreviewTransientEvent(
                    "animationstart",
                    Target,
                    Event.animationName || null
                );
            }
        };
        document.addEventListener(
            "animationstart",
            PreviewTransientAnimationHandler,
            true
        );

        UpdatePreviewDiagnosticsStatus();
        console.info("[Letter Boxed Cubed][preview] Transient element trace started.");
    }

    function StopPreviewTransientElementTrace() {
        PreviewTransientObserver?.disconnect();
        PreviewTransientObserver = null;

        if (PreviewTransientAnimationHandler) {
            document.removeEventListener(
                "animationstart",
                PreviewTransientAnimationHandler,
                true
            );
            PreviewTransientAnimationHandler = null;
        }

        PreviewTransientTraceActive = false;
        UpdatePreviewDiagnosticsStatus();
        return structuredClone(PreviewTransientTrace);
    }

    function GetBoundedPreviewOuterHtml(Selector, MaximumLength = 6000) {
        const ElementNode = document.querySelector(Selector);
        if (!ElementNode) {
            return null;
        }

        const Html = ElementNode.outerHTML;
        return Html.length <= MaximumLength
            ? Html
            : Html.slice(0, MaximumLength) + "\n... [truncated] ...";
    }

    function GetPreviewDebugBundle() {
        return {
            GeneratedAt: new Date().toISOString(),
            PreviewVersion: GetRunningUserscriptVersion(),
            Puzzle: {
                Id: GameData?.id || null,
                PrintDate: GameData?.printDate || null
            },
            Viewport: {
                Width: window.innerWidth,
                Height: window.innerHeight,
                DevicePixelRatio: window.devicePixelRatio || 1,
                VisibilityState: document.visibilityState
            },
            LayoutAndSettings: {
                OuterMode: document.querySelector(".lb-game-container")?.classList.contains(SideModeClass)
                    ? "side"
                    : "stacked",
                InternalPanelLayoutMode,
                PanelWidthPreference,
                AdjustLayoutGap,
                DisplayedLayoutGapPx: GetDisplayedLayoutGapPx(),
                HidePar,
                LineDrawingSpeed,
                NytHeaderScale,
                NytTitleScale,
                NytFooterScale,
                CompactTitleLayout,
                HideYesterdayHelpRow,
                ActiveThemeId: ThemeState?.ActiveTheme?.Id || DefaultThemeId
            },
            Geometry: GetPreviewGeometrySnapshot(),
            DomSnippets: {
                TextInput: GetBoundedPreviewOuterHtml(
                    ".lb-game-container .lb-word-container"
                ),
                GameBoard: GetBoundedPreviewOuterHtml(
                    ".lb-game-container .lb-square-container"
                )
            },
            RecentMutationLog: PreviewDebugMutationLog.slice(-100),
            BootstrapTrace: BootstrapDiagnostics.slice(-100),
            TransientTrace: structuredClone(PreviewTransientTrace)
        };
    }

    async function CopyPreviewDiagnostic(Value, Label) {
        const Text = typeof Value === "string"
            ? Value
            : JSON.stringify(Value, null, 2);
        let Copied = false;

        try {
            await navigator.clipboard.writeText(Text);
            Copied = true;
        } catch {}

        if (!Copied) {
            try {
                const Textarea = document.createElement("textarea");
                Textarea.value = Text;
                Textarea.style.position = "fixed";
                Textarea.style.opacity = "0";
                document.body.appendChild(Textarea);
                Textarea.select();
                Copied = document.execCommand("copy");
                Textarea.remove();
            } catch {}
        }

        console.info(
            `[Letter Boxed Cubed][preview] ${Label}`,
            Value
        );

        if (!Copied) {
            alert(
                `${Label} was logged to DevTools, but the browser blocked automatic clipboard access.`
            );
        }
        return Copied;
    }

    function UpdatePreviewDiagnosticsStatus() {
        const Status = document.querySelector(
            `#${PreviewDebugPanelId} .lbc-debug-diagnostics-status`
        );
        if (!Status) {
            return;
        }

        Status.textContent = PreviewTransientTraceActive
            ? `Transient trace: RECORDING (${PreviewTransientTrace.length} events)`
            : `Transient trace: stopped (${PreviewTransientTrace.length} events retained)`;
    }

    function CreatePreviewDiagnosticsSection() {
        const Wrapper = document.createElement("section");
        Wrapper.className = "lbc-debug-diagnostics";

        const Title = document.createElement("div");
        Title.className = "lbc-debug-section-title";
        Title.textContent = "DIAGNOSTICS";

        const Tools = document.createElement("div");
        Tools.className = "lbc-debug-tools";

        const AddButton = (Text, Handler) => {
            const Button = document.createElement("button");
            Button.type = "button";
            Button.textContent = Text;
            Button.addEventListener("click", Handler);
            Tools.appendChild(Button);
        };

        AddButton(
            "Copy Geometry Snapshot",
            () => CopyPreviewDiagnostic(
                GetPreviewGeometrySnapshot(),
                "Geometry snapshot"
            )
        );
        AddButton(
            "Start Transient Element Trace",
            StartPreviewTransientElementTrace
        );
        AddButton(
            "Stop + Copy Trace",
            () => CopyPreviewDiagnostic(
                StopPreviewTransientElementTrace(),
                "Transient element trace"
            )
        );
        AddButton(
            "Copy Bootstrap Trace",
            () => CopyPreviewDiagnostic(
                BootstrapDiagnostics.slice(-100),
                "Bootstrap trace"
            )
        );
        AddButton(
            "Copy Full Debug Bundle",
            () => CopyPreviewDiagnostic(
                GetPreviewDebugBundle(),
                "Full debug bundle"
            )
        );

        const Status = document.createElement("div");
        Status.className = "lbc-debug-diagnostics-status";
        Wrapper.append(Title, Tools, Status);
        return Wrapper;
    }

'''
preview = replace_once(
    preview,
    '''    function CreatePreviewDebugPane() {
''',
    preview_diagnostics + '''    function CreatePreviewDebugPane() {
''',
    "preview diagnostics implementation",
)

preview = replace_once(
    preview,
    '''        const TiTitle = document.createElement("div");
''',
    '''        const Diagnostics = CreatePreviewDiagnosticsSection();

        const TiTitle = document.createElement("div");
''',
    "preview diagnostics create",
)

preview = replace_once(
    preview,
    '''        DebugPanel.append(
            Header,
            Tools,
            TiTitle,
''',
    '''        DebugPanel.append(
            Header,
            Tools,
            Diagnostics,
            TiTitle,
''',
    "preview diagnostics append",
)

preview = replace_once(
    preview,
    '''            #${PreviewDebugPanelId} .lbc-debug-log,
            #${PreviewDebugPanelId} .lbc-debug-html {
''',
    '''            #${PreviewDebugPanelId} .lbc-debug-diagnostics-status {
                margin: 3px 0 7px;
                color: #b9d9b9;
                font-size: 10px;
            }

            #${PreviewDebugPanelId} .lbc-debug-log,
            #${PreviewDebugPanelId} .lbc-debug-html {
''',
    "preview diagnostics style",
)

preview = replace_once(
    preview,
    '''        StartPreviewDebugObserver();
        RenderPreviewDebugPane();

        CreatePreviewHistoricalTestControls();
''',
    '''        StartPreviewDebugObserver();
        RenderPreviewDebugPane();
        UpdatePreviewDiagnosticsStatus();

        CreatePreviewHistoricalTestControls();
''',
    "preview diagnostics initial status",
)

PREVIEW.write_text(preview, encoding="utf-8")

# ---------------------------------------------------------------------------
# Regression tests: backup v4 + theme merge.
# ---------------------------------------------------------------------------
merge_tests = MERGE_TESTS.read_text(encoding="utf-8")
merge_tests = replace_once(
    merge_tests,
    '''      MigrateBackupToCurrent, MigrateBackupV2ToV3,\n      CreateEmptyGuiState, NormalizeGuiState, BuildCloudSyncData,\n''',
    '''      MigrateBackupToCurrent, MigrateBackupV2ToV3, MigrateBackupV3ToV4,\n      CreateEmptyGuiState, NormalizeGuiState, BuildCloudSyncData,\n      CreateDefaultThemeState, NormalizeThemeState, MergeThemeStates,\n''',
    "merge test exports functions",
)
merge_tests = replace_once(
    merge_tests,
    '''      HideParStorageKey, LineDrawingSpeedStorageKey,\n      CustomDictionaryStorageKey, CustomWordsPrefix, PuzzleMetadataPrefix,\n''',
    '''      HideParStorageKey, LineDrawingSpeedStorageKey,\n      ThemeStateStorageKey, ThemeStateVersion,\n      CustomDictionaryStorageKey, CustomWordsPrefix, PuzzleMetadataPrefix,\n''',
    "merge test exports constants",
)
merge_tests = merge_tests.replace("FormatVersion: 3,", "FormatVersion: 4,")
merge_tests = replace_once(
    merge_tests,
    "assert(migrated.FormatVersion === 3, 'migration did not reach v3');",
    "assert(migrated.FormatVersion === 4, 'migration did not reach current schema');",
    "migration assertion",
)

theme_test = r'''

test('Theme state merges active selection and custom theme tombstones by timestamp', () => {
  const local = T.CreateDefaultThemeState();
  local.ActiveTheme = {Id:'custom-a',UpdatedAt:'2026-09-02T10:00:00Z'};
  local.CustomThemes['custom-a'] = {
    Id:'custom-a',Name:'Sunset',Palette:{},InvertBoard:false,Deleted:false,
    UpdatedAt:'2026-09-02T10:00:00Z'
  };
  const incoming = T.CreateDefaultThemeState();
  incoming.ActiveTheme = {Id:'nyt-dark-app',UpdatedAt:'2026-09-02T12:00:00Z'};
  incoming.CustomThemes['custom-a'] = {
    Id:'custom-a',Name:'Sunset',Palette:{},InvertBoard:false,Deleted:true,
    UpdatedAt:'2026-09-02T11:00:00Z'
  };
  const merged = T.MergeThemeStates(local,incoming);
  assert(merged.ActiveTheme.Id === 'nyt-dark-app', 'newer active theme did not win');
  assert(merged.CustomThemes['custom-a'].Deleted === true, 'newer deletion tombstone did not win');
});

test('Cloud payload includes separate portable theme state', () => {
  const theme = T.CreateDefaultThemeState();
  put(T.ThemeStateStorageKey, theme);
  const data = T.BuildCloudSyncData();
  assert(T.ThemeStateStorageKey in data.StorageSnapshot, 'theme state omitted from cloud payload');
  assert(data.ThemeState.Version === T.ThemeStateVersion, 'top-level theme state missing from cloud payload');
});
'''
merge_tests = replace_once(
    merge_tests,
    '''for (const [name,status,detail] of results) {
''',
    theme_test + '''
for (const [name,status,detail] of results) {
''',
    "theme regression tests",
)
MERGE_TESTS.write_text(merge_tests, encoding="utf-8")

cloud_tests = CLOUD_TESTS.read_text(encoding="utf-8")
cloud_tests = cloud_tests.replace("FormatVersion: 3,", "FormatVersion: 4,")
CLOUD_TESTS.write_text(cloud_tests, encoding="utf-8")

FINAL_TESTS.write_text(r'''const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'LetterBoxedCubed.user.js'), 'utf8');
const preview = fs.readFileSync(path.join(root, 'tools', 'preview_runtime.js'), 'utf8');

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(source.includes('// @version      1.13.1-beta.3'), 'beta.3 version missing');
assert(source.includes('const ExportFormatVersion = 4;'), 'backup schema v4 missing');
assert(source.includes('LetterBoxedCubed_ThemeState'), 'theme state storage missing');
assert(source.includes('NYT Dark (app)'), 'NYT Dark prebuilt theme missing');
assert(source.includes('MergeThemeStates'), 'theme merge missing');
assert(source.includes('lb-cubed-layout-narrow'), 'narrow layout mode missing');
assert(source.includes('lb-cubed-layout-medium'), 'medium layout mode missing');
assert(source.includes('lb-cubed-layout-wide'), 'wide layout mode missing');
assert(source.includes('NarrowToMedium: 500'), 'layout hysteresis enter threshold missing');
assert(source.includes('MediumToNarrow: 440'), 'layout hysteresis exit threshold missing');
assert(source.includes('MediumToWide: 820'), 'wide enter threshold missing');
assert(source.includes('WideToMedium: 740'), 'wide exit threshold missing');
assert(!source.includes('@container lbc'), 'old independent container-query cascade remains');

for (const label of [
  'Copy Geometry Snapshot',
  'Start Transient Element Trace',
  'Stop + Copy Trace',
  'Copy Bootstrap Trace',
  'Copy Full Debug Bundle'
]) {
  assert(preview.includes(label), `preview diagnostic missing: ${label}`);
}
assert(preview.includes('GetPreviewDebugBundle'), 'full debug bundle function missing');
assert(preview.includes('PreviewTransientTrace'), 'transient trace state missing');
assert(preview.includes('!PreviewDebugPaneVisible'), 'hidden debug pane render guard missing');

console.log('PASS: final polish static checks');
''', encoding="utf-8")

print("Applied final LBC polish: issues #15, #20, #30.")
