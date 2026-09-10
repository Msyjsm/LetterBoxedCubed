from pathlib import Path

SOURCE = Path("LetterBoxedCubed.user.js")
CHANGELOG = Path("CHANGELOG.md")
text = SOURCE.read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f"Could not find patch target: {label}")
    text = text.replace(old, new, 1)


def replace_between(start: str, end: str, replacement: str, label: str) -> None:
    global text
    start_index = text.find(start)
    if start_index < 0:
        raise SystemExit(f"Could not find start marker: {label}")
    end_index = text.find(end, start_index)
    if end_index < 0:
        raise SystemExit(f"Could not find end marker: {label}")
    text = text[:start_index] + replacement.rstrip() + "\n\n" + text[end_index:]


replace_once(
    "// @version      1.11.0",
    "// @version      1.12.0-beta.1",
    "version header",
)

replace_once(
    '''    const GoogleDriveButtonId = "lb-cubed-google-drive-button";
    const BrowseHistoryButtonId = "lb-cubed-browse-history-button";
    const HistoryOverlayId = "lb-cubed-history-overlay";
    const CloudSyncDebounceMs = 2500;
    const CloudSyncProtocolVersion = 1;''',
    '''    const GoogleDriveButtonId = "lb-cubed-google-drive-button";
    const GoogleDriveStatusId = "lb-cubed-google-drive-status";
    const BrowseHistoryButtonId = "lb-cubed-browse-history-button";
    const SettingsMenuId = "lb-cubed-settings-menu";
    const HistoryOverlayId = "lb-cubed-history-overlay";
    const LayoutGapHandleId = "lb-cubed-layout-gap-handle";
    const NytHeaderResizeHandleId = "lb-cubed-nyt-header-resize-handle";
    const NytTitleResizeHandleId = "lb-cubed-nyt-title-resize-handle";
    const CloudSyncDebounceMs = 2500;
    const CloudSyncProtocolVersion = 1;

    const DefaultNewItemHighlightSeconds = 1.0;
    const MinimumNewItemHighlightSeconds = 0.1;
    const MaximumNewItemHighlightSeconds = 10.0;
    const MinimumLayoutGap = 0;
    const MaximumLayoutGap = 200;
    const MinimumNytPageScale = 0;
    const MaximumNytPageScale = 2;''',
    "QoL constants",
)

replace_once(
    '''    let HidePar = false;
    let LineDrawingSpeed = 1.0;
    let GuiState = null;''',
    '''    let HidePar = false;
    let LineDrawingSpeed = 1.0;
    let GuiState = null;

    let NewItemHighlightSeconds = DefaultNewItemHighlightSeconds;
    let AdjustLayoutGap = false;
    let LayoutGapPx = LeftColumnGap;
    let NytHeaderScale = 1.0;
    let NytTitleScale = 1.0;
    let BylineNextToDate = false;
    let YesterdayNextToDate = false;

    const RecentWordHighlights = new Map();
    const RecentTwoferHighlights = new Map();
    const NytOriginalHeights = {
        Header: null,
        Title: null
    };

    let LayoutGapResizeState = null;
    let NytPageResizeState = null;''',
    "QoL runtime state",
)

replace_once(
    '''        LoadGoogleDriveConfig();
        LoadGuiState();
        LoadHideParPreference();''',
    '''        LoadGoogleDriveConfig();
        LoadGuiState();
        LoadQolPreferences();
        LoadHideParPreference();''',
    "Initialize QoL preferences",
)

replace_once(
    '''        NormalizeWordAreaFeedbackLayout();
        CreatePanel();
        StartPanelResizeBehavior();
        ScanGameState(true);''',
    '''        NormalizeWordAreaFeedbackLayout();
        CreatePanel();
        EnsureLayoutGapResizeHandle();
        EnsureNytPageResizeHandles();
        ApplyNytPagePreferences();
        StartPanelResizeBehavior();
        StartLayoutGapResizeBehavior();
        StartNytPageResizeBehavior();
        ScanGameState(true);''',
    "Initialize QoL handles",
)

replace_once(
    '''            HidePar,
            LineDrawingSpeed,
            TwofersGrouped,''',
    '''            HidePar,
            LineDrawingSpeed,
            NewItemHighlightSeconds,
            AdjustLayoutGap,
            LayoutGapPx,
            NytHeaderScale,
            NytTitleScale,
            BylineNextToDate,
            YesterdayNextToDate,
            TwofersGrouped,''',
    "Initialize console details",
)

qol_block = r'''    // -------------------------------------------------------------------------
    // QoL display/layout preferences
    // -------------------------------------------------------------------------

    function GetFiniteGuiNumber(Name, DefaultValue, Minimum, Maximum) {
        const Value = Number(GetGuiSetting(Name, DefaultValue));

        return Number.isFinite(Value)
            ? Clamp(Value, Minimum, Maximum)
            : DefaultValue;
    }

    function LoadQolPreferences() {
        NewItemHighlightSeconds = GetFiniteGuiNumber(
            "NewItemHighlightSeconds",
            DefaultNewItemHighlightSeconds,
            MinimumNewItemHighlightSeconds,
            MaximumNewItemHighlightSeconds
        );

        AdjustLayoutGap = Boolean(
            GetGuiSetting("AdjustLayoutGap", false)
        );

        LayoutGapPx = GetFiniteGuiNumber(
            "LayoutGapPx",
            LeftColumnGap,
            MinimumLayoutGap,
            MaximumLayoutGap
        );

        NytHeaderScale = GetFiniteGuiNumber(
            "NytHeaderScale",
            1.0,
            MinimumNytPageScale,
            MaximumNytPageScale
        );

        NytTitleScale = GetFiniteGuiNumber(
            "NytTitleScale",
            1.0,
            MinimumNytPageScale,
            MaximumNytPageScale
        );

        BylineNextToDate = Boolean(
            GetGuiSetting("BylineNextToDate", false)
        );

        YesterdayNextToDate = Boolean(
            GetGuiSetting("YesterdayNextToDate", false)
        );
    }

    function RegisterRecentHighlight(MapValue, Key) {
        if (!Key) {
            return;
        }

        const DurationMs = Math.max(
            1,
            Math.round(NewItemHighlightSeconds * 1000)
        );

        const ExpiresAt = Date.now() + DurationMs;
        MapValue.set(Key, ExpiresAt);

        setTimeout(() => {
            if (MapValue.get(Key) === ExpiresAt) {
                MapValue.delete(Key);
            }
        }, DurationMs + 75);
    }

    function MarkWordForHighlight(Word) {
        RegisterRecentHighlight(
            RecentWordHighlights,
            NormalizeWord(Word)
        );
    }

    function MarkTwoferForHighlight(Key) {
        RegisterRecentHighlight(
            RecentTwoferHighlights,
            String(Key || "")
        );
    }

    function ApplyRecentHighlight(Element, MapValue, Key) {
        const ExpiresAt = MapValue.get(Key);
        const RemainingMs = Number(ExpiresAt) - Date.now();

        if (!Number.isFinite(RemainingMs) || RemainingMs <= 0) {
            MapValue.delete(Key);
            return false;
        }

        Element.classList.add("lb-cubed-new-highlight");
        Element.style.setProperty(
            "--lb-cubed-highlight-duration",
            `${Math.max(1, Math.round(RemainingMs))}ms`
        );

        return true;
    }

    function ApplyRecentWordHighlight(Element, Word) {
        const Normalized = NormalizeWord(Word);
        Element.dataset.cubedWord = Normalized;
        return ApplyRecentHighlight(
            Element,
            RecentWordHighlights,
            Normalized
        );
    }

    function ApplyRecentTwoferHighlight(Element, Key) {
        Element.dataset.cubedTwofer = String(Key || "");
        return ApplyRecentHighlight(
            Element,
            RecentTwoferHighlights,
            String(Key || "")
        );
    }

    function ApplyRecentLengthHighlight(Element, Bucket) {
        let LatestExpiry = 0;
        const RecentWords = [];

        for (const [Word, ExpiresAt] of RecentWordHighlights) {
            if (ExpiresAt <= Date.now()) {
                RecentWordHighlights.delete(Word);
                continue;
            }

            if (GetLengthBucket(Word.length) === Bucket) {
                LatestExpiry = Math.max(LatestExpiry, ExpiresAt);
                RecentWords.push(Word);
            }
        }

        if (!LatestExpiry) {
            return;
        }

        Element.classList.add("lb-cubed-new-highlight");
        Element.style.setProperty(
            "--lb-cubed-highlight-duration",
            `${Math.max(1, Math.round(LatestExpiry - Date.now()))}ms`
        );

        if (RecentWords.length) {
            Element.title = `Recently found: ${RecentWords.sort(Alphabetically).join(", ")}`;
        }
    }

    function CreateSettingsSection(TitleText) {
        const Section = document.createElement("section");
        Section.className = "lb-cubed-settings-section";

        const Heading = document.createElement("div");
        Heading.className = "lb-cubed-settings-section-title";
        Heading.textContent = TitleText;
        Section.appendChild(Heading);

        return Section;
    }

    function CreateSettingsCheckbox(LabelText, Checked, OnChange, TitleText = "") {
        const Label = document.createElement("label");
        Label.className = "lb-cubed-settings-checkbox";
        if (TitleText) {
            Label.title = TitleText;
        }

        const Input = document.createElement("input");
        Input.type = "checkbox";
        Input.checked = Boolean(Checked);
        Input.addEventListener("change", Event => {
            OnChange(Boolean(Event.currentTarget.checked));
        });

        const Text = document.createElement("span");
        Text.textContent = LabelText;

        Label.append(Input, Text);
        return Label;
    }

    function CreateSettingsRange(
        LabelText,
        Value,
        Minimum,
        Maximum,
        Step,
        FormatValue,
        OnInput,
        OnCommit
    ) {
        const Row = document.createElement("label");
        Row.className = "lb-cubed-settings-range";

        const Label = document.createElement("span");
        Label.className = "lb-cubed-settings-label";
        Label.textContent = LabelText;

        const Input = document.createElement("input");
        Input.type = "range";
        Input.min = String(Minimum);
        Input.max = String(Maximum);
        Input.step = String(Step);
        Input.value = String(Value);

        const ValueText = document.createElement("span");
        ValueText.className = "lb-cubed-settings-range-value";
        ValueText.textContent = FormatValue(Value);

        Input.addEventListener("input", Event => {
            const Next = Number(Event.currentTarget.value);
            ValueText.textContent = FormatValue(Next);
            OnInput(Next);
        });

        Input.addEventListener("change", Event => {
            const Next = Number(Event.currentTarget.value);
            ValueText.textContent = FormatValue(Next);
            OnCommit(Next);
        });

        Row.append(Label, Input, ValueText);
        return Row;
    }

    function CreateSettingsNumberWithReset(
        LabelText,
        Value,
        Minimum,
        Maximum,
        Step,
        Suffix,
        DefaultValue,
        SettingName,
        OnCommit
    ) {
        const Row = document.createElement("div");
        Row.className = "lb-cubed-settings-number-row";

        const Label = document.createElement("label");
        Label.className = "lb-cubed-settings-label";
        Label.textContent = LabelText;

        const InputWrap = document.createElement("span");
        InputWrap.className = "lb-cubed-settings-number-wrap";

        const Input = document.createElement("input");
        Input.type = "number";
        Input.min = String(Minimum);
        Input.max = String(Maximum);
        Input.step = String(Step);
        Input.value = String(Value);
        Input.dataset.cubedSettingInput = SettingName;

        const SuffixText = document.createElement("span");
        SuffixText.className = "lb-cubed-settings-suffix";
        SuffixText.textContent = Suffix;

        const Commit = RawValue => {
            const Numeric = Number(RawValue);
            const Next = Number.isFinite(Numeric)
                ? Clamp(Numeric, Minimum, Maximum)
                : DefaultValue;

            Input.value = String(Next);
            OnCommit(Next);
        };

        Input.addEventListener("change", Event => {
            Commit(Event.currentTarget.value);
        });

        const Reset = document.createElement("button");
        Reset.type = "button";
        Reset.className = "lb-cubed-settings-mini-button";
        Reset.textContent = "Reset";
        Reset.addEventListener("click", Event => {
            Event.preventDefault();
            Event.stopPropagation();
            Commit(DefaultValue);
        });

        Label.htmlFor = "";
        InputWrap.append(Input, SuffixText);
        Row.append(Label, InputWrap, Reset);
        return Row;
    }

    function CreateSettingsMenu() {
        const Details = document.createElement("details");
        Details.id = SettingsMenuId;
        Details.className = "lb-cubed-settings-menu";

        const Summary = document.createElement("summary");
        Summary.className = "lb-cubed-header-button lb-cubed-settings-summary";
        Summary.textContent = "⚙ Settings";
        Details.appendChild(Summary);

        const Menu = document.createElement("div");
        Menu.className = "lb-cubed-settings-panel";

        const DisplaySection = CreateSettingsSection("Display");
        DisplaySection.append(
            CreateSettingsCheckbox(
                "Hide Par",
                HidePar,
                Checked => {
                    HidePar = Checked;
                    SaveHideParPreference();
                    ApplyHideParPreference();
                },
                "Hide NYT's 'Try to solve in X words' par text"
            ),
            CreateSettingsCheckbox(
                "Adjust layout gap",
                AdjustLayoutGap,
                Checked => {
                    AdjustLayoutGap = Checked;
                    SetGuiSetting("AdjustLayoutGap", AdjustLayoutGap);
                    UpdateLayoutGapHandleVisibility();
                    PositionLayoutGapResizeHandle();
                },
                "Show a draggable bar between the word-entry area and puzzle box"
            ),
            CreateSettingsNumberWithReset(
                "Layout gap",
                Math.round(LayoutGapPx),
                MinimumLayoutGap,
                MaximumLayoutGap,
                1,
                "px",
                LeftColumnGap,
                "LayoutGapPx",
                Value => {
                    LayoutGapPx = Value;
                    SetGuiSetting("LayoutGapPx", LayoutGapPx);
                    UpdatePanelLayout();
                }
            )
        );

        const AnimationSection = CreateSettingsSection("Feedback & animation");
        AnimationSection.append(
            CreateSettingsRange(
                "Animation Speed",
                LineDrawingSpeed,
                0,
                1,
                0.1,
                Value => Value.toFixed(1),
                Value => {
                    LineDrawingSpeed = Clamp(Value, 0, 1);
                },
                Value => {
                    LineDrawingSpeed = Clamp(Value, 0, 1);
                    SaveLineDrawingSpeed();
                }
            ),
            CreateSettingsRange(
                "New-item highlight",
                NewItemHighlightSeconds,
                MinimumNewItemHighlightSeconds,
                MaximumNewItemHighlightSeconds,
                0.1,
                Value => `${Value.toFixed(1)}s`,
                Value => {
                    NewItemHighlightSeconds = Clamp(
                        Value,
                        MinimumNewItemHighlightSeconds,
                        MaximumNewItemHighlightSeconds
                    );
                },
                Value => {
                    NewItemHighlightSeconds = Clamp(
                        Value,
                        MinimumNewItemHighlightSeconds,
                        MaximumNewItemHighlightSeconds
                    );
                    SetGuiSetting(
                        "NewItemHighlightSeconds",
                        Number(NewItemHighlightSeconds.toFixed(1))
                    );
                }
            )
        );

        const NytSection = CreateSettingsSection("NYT page layout");
        NytSection.append(
            CreateSettingsNumberWithReset(
                "Header size",
                Math.round(NytHeaderScale * 100),
                0,
                200,
                1,
                "%",
                100,
                "NytHeaderScale",
                Value => {
                    NytHeaderScale = Clamp(Value / 100, MinimumNytPageScale, MaximumNytPageScale);
                    SetGuiSetting("NytHeaderScale", NytHeaderScale);
                    ApplyNytPagePreferences();
                }
            ),
            CreateSettingsNumberWithReset(
                "Game title size",
                Math.round(NytTitleScale * 100),
                0,
                200,
                1,
                "%",
                100,
                "NytTitleScale",
                Value => {
                    NytTitleScale = Clamp(Value / 100, MinimumNytPageScale, MaximumNytPageScale);
                    SetGuiSetting("NytTitleScale", NytTitleScale);
                    ApplyNytPagePreferences();
                }
            ),
            CreateSettingsCheckbox(
                "Put byline next to date",
                BylineNextToDate,
                Checked => {
                    BylineNextToDate = Checked;
                    SetGuiSetting("BylineNextToDate", BylineNextToDate);
                    ApplyNytPagePreferences();
                }
            ),
            CreateSettingsCheckbox(
                "Put Yesterday next to date",
                YesterdayNextToDate,
                Checked => {
                    YesterdayNextToDate = Checked;
                    SetGuiSetting("YesterdayNextToDate", YesterdayNextToDate);
                    ApplyNytPagePreferences();
                }
            )
        );

        const DataSection = CreateSettingsSection("Data");
        const DriveRow = document.createElement("div");
        DriveRow.className = "lb-cubed-settings-action-row";

        const DriveLabel = document.createElement("span");
        DriveLabel.className = "lb-cubed-settings-label";
        DriveLabel.textContent = "Google Drive";

        const GoogleDriveButton = document.createElement("button");
        GoogleDriveButton.id = GoogleDriveButtonId;
        GoogleDriveButton.type = "button";
        GoogleDriveButton.className = "lb-cubed-header-button";
        GoogleDriveButton.addEventListener("click", Event => {
            Event.preventDefault();
            Event.stopPropagation();

            if (!GoogleDriveConfig?.Enabled || Event.shiftKey) {
                ConfigureGoogleDriveSync();
                return;
            }

            SyncWithGoogleDrive({ Manual: true });
        });

        DriveRow.append(DriveLabel, GoogleDriveButton);

        const DataButtons = document.createElement("div");
        DataButtons.className = "lb-cubed-settings-button-row";

        const ExportButton = document.createElement("button");
        ExportButton.type = "button";
        ExportButton.className = "lb-cubed-header-button";
        ExportButton.textContent = "Export";
        ExportButton.title = "Export all retained Letter Boxed Cubed puzzle/player data as a text backup";
        ExportButton.addEventListener("click", Event => {
            Event.preventDefault();
            Event.stopPropagation();
            ExportAllData();
        });

        const ImportButton = document.createElement("button");
        ImportButton.type = "button";
        ImportButton.className = "lb-cubed-header-button";
        ImportButton.textContent = "Import";
        ImportButton.title = "Restore or merge data from a Letter Boxed Cubed backup";
        ImportButton.addEventListener("click", Event => {
            Event.preventDefault();
            Event.stopPropagation();
            PromptForImport();
        });

        DataButtons.append(ExportButton, ImportButton);
        DataSection.append(DriveRow, DataButtons);

        Menu.append(
            DisplaySection,
            AnimationSection,
            NytSection,
            DataSection
        );
        Details.appendChild(Menu);

        return Details;
    }

    function GetNytPageTargets() {
        return {
            Header: document.querySelector("header.pz-header.pz-game-header"),
            Title: document.querySelector("#letter-boxed-container .pz-game-title-bar")
        };
    }

    function CaptureNytOriginalHeight(Kind, Element) {
        if (!Element || NytOriginalHeights[Kind]) {
            return;
        }

        const Height = Element.getBoundingClientRect().height;
        if (Number.isFinite(Height) && Height > 0) {
            NytOriginalHeights[Kind] = Height;
        }
    }

    function ApplyNytElementScale(Element, Scale) {
        if (!Element) {
            return;
        }

        const Normalized = Clamp(
            Number(Scale) || 0,
            MinimumNytPageScale,
            MaximumNytPageScale
        );

        Element.classList.toggle(
            "lb-cubed-page-fluff-hidden",
            Normalized <= 0.001
        );

        if (Normalized > 0.001 && Math.abs(Normalized - 1) > 0.001) {
            Element.style.setProperty("zoom", String(Normalized));
        } else {
            Element.style.removeProperty("zoom");
        }
    }

    function EnsureNytPageResizeHandles() {
        const Targets = GetNytPageTargets();
        const Definitions = [
            {
                Kind: "Header",
                Element: Targets.Header,
                HandleId: NytHeaderResizeHandleId,
                SettingName: "NytHeaderScale",
                Label: "Resize NYT header"
            },
            {
                Kind: "Title",
                Element: Targets.Title,
                HandleId: NytTitleResizeHandleId,
                SettingName: "NytTitleScale",
                Label: "Resize Letter Boxed title area"
            }
        ];

        for (const Definition of Definitions) {
            if (!Definition.Element) {
                continue;
            }

            CaptureNytOriginalHeight(
                Definition.Kind,
                Definition.Element
            );

            if (document.getElementById(Definition.HandleId)) {
                continue;
            }

            const Handle = document.createElement("div");
            Handle.id = Definition.HandleId;
            Handle.className = "lb-cubed-page-resize-handle";
            Handle.dataset.cubedTargetKind = Definition.Kind;
            Handle.dataset.cubedScaleSetting = Definition.SettingName;
            Handle.setAttribute("role", "separator");
            Handle.setAttribute("aria-orientation", "horizontal");
            Handle.setAttribute("aria-label", Definition.Label);
            Handle.title = `${Definition.Label}; drag vertically, or use Settings for a precise percentage/reset`;

            Definition.Element.insertAdjacentElement("afterend", Handle);
        }
    }

    function GetNytScaleBySettingName(SettingName) {
        return SettingName === "NytHeaderScale"
            ? NytHeaderScale
            : NytTitleScale;
    }

    function SetNytScaleBySettingName(SettingName, Scale, Persist = false) {
        const Normalized = Clamp(
            Scale,
            MinimumNytPageScale,
            MaximumNytPageScale
        );

        if (SettingName === "NytHeaderScale") {
            NytHeaderScale = Normalized;
        } else if (SettingName === "NytTitleScale") {
            NytTitleScale = Normalized;
        } else {
            return;
        }

        const Input = document.querySelector(
            `[data-cubed-setting-input="${SettingName}"]`
        );
        if (Input) {
            Input.value = String(Math.round(Normalized * 100));
        }

        if (Persist) {
            SetGuiSetting(SettingName, Normalized);
        }

        ApplyNytPagePreferences();
    }

    function StartNytPageResizeBehavior() {
        EnsureNytPageResizeHandles();

        for (const Handle of [
            document.getElementById(NytHeaderResizeHandleId),
            document.getElementById(NytTitleResizeHandleId)
        ].filter(Boolean)) {
            Handle.addEventListener("pointerdown", HandleNytPageResizePointerDown, true);
            Handle.addEventListener("pointermove", HandleNytPageResizePointerMove, true);
            Handle.addEventListener("pointerup", EndNytPageResize, true);
            Handle.addEventListener("pointercancel", EndNytPageResize, true);
        }
    }

    function HandleNytPageResizePointerDown(Event) {
        if (Event.button !== 0) {
            return;
        }

        const Handle = Event.currentTarget;
        const Kind = Handle.dataset.cubedTargetKind;
        const SettingName = Handle.dataset.cubedScaleSetting;
        const OriginalHeight = Number(NytOriginalHeights[Kind]) || 60;

        NytPageResizeState = {
            PointerId: Event.pointerId,
            StartY: Event.clientY,
            StartScale: GetNytScaleBySettingName(SettingName),
            OriginalHeight: Math.max(20, OriginalHeight),
            SettingName,
            Handle
        };

        Handle.classList.add("lb-cubed-page-resize-handle-active");

        try {
            Handle.setPointerCapture(Event.pointerId);
        } catch {
            // Pointer capture is helpful but not required.
        }

        Event.preventDefault();
        Event.stopPropagation();
    }

    function HandleNytPageResizePointerMove(Event) {
        if (!NytPageResizeState || Event.pointerId !== NytPageResizeState.PointerId) {
            return;
        }

        const DeltaY = Event.clientY - NytPageResizeState.StartY;
        const NextScale =
            NytPageResizeState.StartScale +
            (DeltaY / NytPageResizeState.OriginalHeight);

        SetNytScaleBySettingName(
            NytPageResizeState.SettingName,
            NextScale,
            false
        );

        Event.preventDefault();
    }

    function EndNytPageResize(Event) {
        if (!NytPageResizeState) {
            return;
        }

        const State = NytPageResizeState;
        NytPageResizeState = null;

        State.Handle.classList.remove("lb-cubed-page-resize-handle-active");

        try {
            State.Handle.releasePointerCapture(State.PointerId);
        } catch {
            // Ignore browsers that already released pointer capture.
        }

        SetNytScaleBySettingName(
            State.SettingName,
            GetNytScaleBySettingName(State.SettingName),
            true
        );

        if (Event) {
            Event.preventDefault();
        }
    }

    function ApplyNytTitleArrangement() {
        const Host = document.querySelector("#portal-game-header");
        if (!Host) {
            return;
        }

        const OriginalYesterday = document.querySelector(
            '#yesterday-button, [data-testid="yesterday-button"]'
        );

        Host.classList.toggle(
            "lb-cubed-title-meta-layout",
            BylineNextToDate || YesterdayNextToDate
        );
        Host.classList.toggle(
            "lb-cubed-byline-next-to-date",
            BylineNextToDate
        );

        let Proxy = Host.querySelector(".lb-cubed-yesterday-proxy");

        if (YesterdayNextToDate && OriginalYesterday) {
            OriginalYesterday.classList.add("lb-cubed-original-yesterday-hidden");

            if (!Proxy) {
                Proxy = OriginalYesterday.cloneNode(true);
                Proxy.removeAttribute("id");
                Proxy.removeAttribute("data-testid");
                Proxy.removeAttribute("aria-controls");
                Proxy.removeAttribute("aria-expanded");
                Proxy.classList.add("lb-cubed-yesterday-proxy");
                Proxy.title = "Yesterday";

                Proxy.addEventListener("click", Event => {
                    Event.preventDefault();
                    Event.stopPropagation();

                    const CurrentOriginal = document.querySelector(
                        '#yesterday-button, [data-testid="yesterday-button"]'
                    );
                    CurrentOriginal?.click();
                });

                Host.appendChild(Proxy);
            }
        } else {
            Proxy?.remove();
            document.querySelectorAll(".lb-cubed-original-yesterday-hidden")
                .forEach(Element => Element.classList.remove("lb-cubed-original-yesterday-hidden"));
        }
    }

    function ApplyNytPagePreferences() {
        EnsureNytPageResizeHandles();

        const Targets = GetNytPageTargets();
        CaptureNytOriginalHeight("Header", Targets.Header);
        CaptureNytOriginalHeight("Title", Targets.Title);

        ApplyNytElementScale(Targets.Header, NytHeaderScale);
        ApplyNytElementScale(Targets.Title, NytTitleScale);
        ApplyNytTitleArrangement();
    }

    function EnsureLayoutGapResizeHandle() {
        const GameContainer = document.querySelector(".lb-game-container");
        if (!GameContainer || document.getElementById(LayoutGapHandleId)) {
            return;
        }

        const Handle = document.createElement("div");
        Handle.id = LayoutGapHandleId;
        Handle.className = "lb-cubed-layout-gap-handle";
        Handle.setAttribute("role", "separator");
        Handle.setAttribute("aria-orientation", "horizontal");
        Handle.setAttribute("aria-label", "Adjust gap between word entry and puzzle box");
        Handle.title = "Drag to adjust the gap between the word-entry area and puzzle box";

        GameContainer.appendChild(Handle);
        UpdateLayoutGapHandleVisibility();
    }

    function UpdateLayoutGapHandleVisibility() {
        const GameContainer = document.querySelector(".lb-game-container");
        GameContainer?.classList.toggle(
            "lb-cubed-adjust-layout-gap",
            AdjustLayoutGap
        );
    }

    function PositionLayoutGapResizeHandle() {
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
            const Midpoint =
                ((WordRect.bottom + SquareRect.top) / 2) -
                GameRect.top;

            Handle.style.left = `${Math.round(Left)}px`;
            Handle.style.width = `${Math.max(24, Math.round(Right - Left))}px`;
            Handle.style.top = `${Math.round(Midpoint - 6)}px`;
        });
    }

    function StartLayoutGapResizeBehavior() {
        EnsureLayoutGapResizeHandle();
        const Handle = document.getElementById(LayoutGapHandleId);
        if (!Handle) {
            return;
        }

        Handle.addEventListener("pointerdown", HandleLayoutGapPointerDown, true);
        Handle.addEventListener("pointermove", HandleLayoutGapPointerMove, true);
        Handle.addEventListener("pointerup", EndLayoutGapResize, true);
        Handle.addEventListener("pointercancel", EndLayoutGapResize, true);
    }

    function HandleLayoutGapPointerDown(Event) {
        if (Event.button !== 0 || !AdjustLayoutGap) {
            return;
        }

        const Handle = Event.currentTarget;
        LayoutGapResizeState = {
            PointerId: Event.pointerId,
            StartY: Event.clientY,
            StartGap: LayoutGapPx,
            Handle
        };

        Handle.classList.add("lb-cubed-layout-gap-handle-active");

        try {
            Handle.setPointerCapture(Event.pointerId);
        } catch {
            // Pointer capture is helpful but not required.
        }

        Event.preventDefault();
        Event.stopPropagation();
    }

    function HandleLayoutGapPointerMove(Event) {
        if (!LayoutGapResizeState || Event.pointerId !== LayoutGapResizeState.PointerId) {
            return;
        }

        LayoutGapPx = Clamp(
            LayoutGapResizeState.StartGap +
            (Event.clientY - LayoutGapResizeState.StartY),
            MinimumLayoutGap,
            MaximumLayoutGap
        );

        const Input = document.querySelector(
            '[data-cubed-setting-input="LayoutGapPx"]'
        );
        if (Input) {
            Input.value = String(Math.round(LayoutGapPx));
        }

        UpdatePanelLayout();
        Event.preventDefault();
    }

    function EndLayoutGapResize(Event) {
        if (!LayoutGapResizeState) {
            return;
        }

        const State = LayoutGapResizeState;
        LayoutGapResizeState = null;

        State.Handle.classList.remove("lb-cubed-layout-gap-handle-active");

        try {
            State.Handle.releasePointerCapture(State.PointerId);
        } catch {
            // Ignore browsers that already released pointer capture.
        }

        LayoutGapPx = Math.round(LayoutGapPx);
        SetGuiSetting("LayoutGapPx", LayoutGapPx);
        UpdatePanelLayout();

        if (Event) {
            Event.preventDefault();
        }
    }

'''

replace_once(
    "    function InstallLineDrawingSpeedHook() {",
    qol_block + "    function InstallLineDrawingSpeedHook() {",
    "QoL helper block insertion",
)

replace_between(
    "    function UpdateGoogleDriveButton() {",
    "    // -------------------------------------------------------------------------\n    // Found words",
    r'''    function UpdateGoogleDriveButton() {
        const Button = document.getElementById(GoogleDriveButtonId);
        const Status = document.getElementById(GoogleDriveStatusId);

        const StatusParts = [];

        if (!GoogleDriveConfig?.Enabled) {
            if (Button) {
                Button.textContent = "Drive: Setup";
                Button.title = "Configure automatic Google Drive sync";
            }

            if (Status) {
                Status.textContent = "Drive: Off";
                Status.title = "Google Drive sync is not configured on this browser.";
            }
            return;
        }

        const ButtonTextByStatus = {
            Ready: "Drive: Sync",
            Syncing: "Drive: Syncing…",
            Synced: "Drive: ✓",
            Error: "Drive: Error"
        };

        const StatusTextByStatus = {
            Ready: "Drive: Ready",
            Syncing: "Drive: Syncing…",
            Synced: "Drive: Synced",
            Error: "Drive: Error"
        };

        StatusParts.push(
            "Use Settings to sync now; Shift-click the Drive button there to reconfigure or disconnect."
        );

        if (LastCloudSyncAt) {
            StatusParts.push(
                `Last synced: ${new Date(LastCloudSyncAt).toLocaleString()}`
            );
        }

        if (LastCloudSyncError) {
            StatusParts.push(
                `Last error: ${LastCloudSyncError.message || LastCloudSyncError}`
            );
        }

        const Title = StatusParts.join("\n");

        if (Button) {
            Button.textContent = ButtonTextByStatus[CloudSyncStatus] || "Drive: Sync";
            Button.title = Title;
        }

        if (Status) {
            Status.textContent = StatusTextByStatus[CloudSyncStatus] || "Drive: Ready";
            Status.title = Title;
        }
    }

''',
    "Drive button/status renderer",
)

replace_once(
    '''        LoadGuiState();
        LoadFoundWords();''',
    '''        LoadGuiState();
        LoadQolPreferences();
        LoadFoundWords();''',
    "Reload QoL preferences",
)

replace_once(
    '''        LoadLineDrawingSpeed();
        LoadFoundTwofers();
        RenderPanel();''',
    '''        LoadLineDrawingSpeed();
        LoadFoundTwofers();
        ApplyNytPagePreferences();
        UpdateLayoutGapHandleVisibility();
        RenderPanel();''',
    "Reload QoL application",
)

replace_between(
    "    function MarkTwoferFound(First, Second) {",
    "    // -------------------------------------------------------------------------\n    // Hints and twofer categories",
    r'''    function MarkTwoferFound(First, Second) {
        const NormalizedFirst = NormalizeWord(First);
        const NormalizedSecond = NormalizeWord(Second);
        const Key = MakeTwoferKey(NormalizedFirst, NormalizedSecond);

        if (!TwoferKeySet.has(Key) || FoundTwofers.has(Key)) {
            return false;
        }

        const FirstWasFound = FoundWords.has(NormalizedFirst);
        const SecondWasFound = FoundWords.has(NormalizedSecond);

        FoundTwofers.add(Key);
        FoundWords.add(NormalizedFirst);
        FoundWords.add(NormalizedSecond);

        if (!FirstWasFound) {
            MarkWordForHighlight(NormalizedFirst);
        }

        if (!SecondWasFound) {
            MarkWordForHighlight(NormalizedSecond);
        }

        MarkTwoferForHighlight(Key);

        SaveFoundTwofers();
        SaveFoundWords();

        console.log(
            "[Letter Boxed Cubed] Twofer found:",
            `${NormalizedFirst} -> ${NormalizedSecond}`
        );

        return true;
    }

''',
    "Found twofer highlighting",
)

replace_between(
    "    function ScanGameState(ForceRender = false) {",
    "    function ReadCurrentChain() {",
    r'''    function ScanGameState(ForceRender = false) {
        const CurrentChain = ReadCurrentChain();
        let FoundWordsChanged = false;

        for (const Word of CurrentChain) {
            if (!FoundWords.has(Word)) {
                FoundWords.add(Word);
                MarkWordForHighlight(Word);
                FoundWordsChanged = true;

                console.log("[Letter Boxed Cubed] Found:", Word);
            }
        }

        if (FoundWordsChanged) {
            SaveFoundWords();
        }

        let TwoferChanged = false;

        if (CurrentChain.length === 2) {
            TwoferChanged = MarkTwoferFound(
                CurrentChain[0],
                CurrentChain[1]
            );
        }

        if (FoundWordsChanged || TwoferChanged || ForceRender) {
            RenderPanel();
        }
    }

''',
    "Found word highlighting",
)

replace_between(
    "    function UpdatePanelLayout() {",
    "    function GetLeftColumnWidth() {",
    r'''    function UpdatePanelLayout() {
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
        PositionLayoutGapResizeHandle();
    }

''',
    "Layout update with gap handle",
)

if text.count('`${LeftColumnGap}px`') < 2:
    raise SystemExit("Expected at least two LeftColumnGap runtime assignments")
text = text.replace('`${LeftColumnGap}px`', '`${LayoutGapPx}px`', 2)

replace_between(
    "    function RenderHeader(Panel) {",
    "    function RenderMainStats(Panel, Stats) {",
    r'''    function RenderHeader(Panel) {
        const Header = document.createElement("div");
        Header.className = "lb-cubed-header";

        const Title = document.createElement("h2");
        Title.className = "lb-cubed-title";
        Title.textContent = "Word Log";

        const DriveStatus = document.createElement("span");
        DriveStatus.id = GoogleDriveStatusId;
        DriveStatus.className = "lb-cubed-drive-status";

        const TitleRow = document.createElement("div");
        TitleRow.className = "lb-cubed-title-row";
        TitleRow.append(Title, DriveStatus);

        const Subtitle = document.createElement("div");
        Subtitle.className = "lb-cubed-subtitle";
        Subtitle.textContent =
            GameData.date ||
            GameData.printDate ||
            "Today's Letter Boxed";

        const HeaderText = document.createElement("div");
        HeaderText.className = "lb-cubed-header-text";
        HeaderText.append(TitleRow, Subtitle);

        const HeaderActions = document.createElement("div");
        HeaderActions.className = "lb-cubed-header-actions";

        // Last NYT-invalid, structurally valid submission.
        const InvalidControl = document.createElement("div");
        InvalidControl.className = "lb-cubed-invalid-control";

        const InvalidWord = document.createElement("span");
        InvalidWord.className = "lb-cubed-invalid-word";
        InvalidWord.textContent = LastInvalidWord || "No invalid word";
        InvalidWord.title = LastInvalidWord
            ? "Last submitted word that obeys the board rules but is absent from NYT's dictionary"
            : "No structurally valid NYT-dictionary rejection has been captured yet";

        const AddDictionaryButton = document.createElement("button");
        AddDictionaryButton.type = "button";
        AddDictionaryButton.className = "lb-cubed-header-button";

        const InvalidAlreadyAdded =
            LastInvalidWord &&
            CustomDictionary.has(LastInvalidWord);

        AddDictionaryButton.textContent = InvalidAlreadyAdded
            ? "Added"
            : "Add to dictionary";

        AddDictionaryButton.disabled = !LastInvalidWord || InvalidAlreadyAdded;
        AddDictionaryButton.title = LastInvalidWord
            ? InvalidAlreadyAdded
                ? `${LastInvalidWord} is already in your custom dictionary`
                : `Record ${LastInvalidWord} as a user-approved custom dictionary word`
            : "Submit a structurally valid word that NYT does not recognize first";

        AddDictionaryButton.addEventListener("click", Event => {
            Event.preventDefault();
            Event.stopPropagation();
            AddLastInvalidWordToCustomDictionary();
        });

        InvalidControl.append(
            InvalidWord,
            AddDictionaryButton
        );

        const BrowseHistoryButton = document.createElement("button");
        BrowseHistoryButton.id = BrowseHistoryButtonId;
        BrowseHistoryButton.type = "button";
        BrowseHistoryButton.className = "lb-cubed-header-button";
        BrowseHistoryButton.textContent = "Browse History";
        BrowseHistoryButton.title =
            "Browse found-word and solved-Twofer history from the synced Google Drive backup";
        BrowseHistoryButton.addEventListener("click", Event => {
            Event.preventDefault();
            Event.stopPropagation();
            OpenCloudHistoryBrowser();
        });

        const SettingsMenu = CreateSettingsMenu();

        HeaderActions.append(
            InvalidControl,
            BrowseHistoryButton,
            SettingsMenu
        );

        Header.append(
            HeaderText,
            HeaderActions
        );

        Panel.appendChild(Header);
        UpdateGoogleDriveButton();
    }

''',
    "Settings-based header",
)

replace_between(
    "    function CreatePotentialWordHintTree(",
    "    function RenderTwofers(Panel, PreviousOpenStates) {",
    r'''    function CreatePotentialWordHintTree(
        Label,
        SectionName,
        Words,
        FoundCount,
        TotalCount,
        PreviousOpenStates
    ) {
        const Details = document.createElement("details");
        Details.className = "lb-cubed-nested-tree lb-cubed-potential-word-tree";

        ConfigureTree(
            Details,
            SectionName,
            PreviousOpenStates,
            false
        );

        const Summary = document.createElement("summary");
        Summary.textContent = `${Label} (${FoundCount.toLocaleString()} / ${TotalCount.toLocaleString()})`;
        Details.appendChild(Summary);

        const List = document.createElement("div");
        List.className = "lb-cubed-potential-word-list";

        const Position = SectionName === "HintFirstWords"
            ? "First"
            : "Second";

        /*
            Only reveal potential first/second words that the player has
            already found. Each revealed candidate also shows how many exact
            twofers using it in that position have actually been solved.
        */
        const SortedWords = [...Words]
            .filter(Word => FoundWords.has(Word))
            .sort(Alphabetically);

        if (SortedWords.length === 0) {
            const Empty = document.createElement("div");
            Empty.className = "lb-cubed-potential-word-empty";
            Empty.textContent = "None found yet.";
            List.appendChild(Empty);
        } else {
            const Fragment = document.createDocumentFragment();

            for (const Word of SortedWords) {
                const RelevantTwofers = Twofers.filter(Twofer =>
                    Position === "First"
                        ? Twofer.First === Word
                        : Twofer.Second === Word
                );

                const SolvedCount = RelevantTwofers.reduce(
                    (Count, Twofer) => Count + (FoundTwofers.has(Twofer.Key) ? 1 : 0),
                    0
                );

                const Item = document.createElement("div");
                Item.className =
                    "lb-cubed-potential-word lb-cubed-potential-word-found";

                if (RelevantTwofers.length > 0 && SolvedCount === RelevantTwofers.length) {
                    Item.classList.add("lb-cubed-potential-word-complete");
                }

                const WordText = document.createElement("span");
                WordText.className = "lb-cubed-potential-word-label";
                WordText.textContent = Word;

                const Progress = document.createElement("span");
                Progress.className = "lb-cubed-potential-word-progress";
                Progress.textContent =
                    `${SolvedCount.toLocaleString()} / ${RelevantTwofers.length.toLocaleString()}`;

                Item.append(WordText, Progress);
                ApplyRecentWordHighlight(Item, Word);
                Fragment.appendChild(Item);
            }

            List.appendChild(Fragment);
        }

        Details.appendChild(List);
        return Details;
    }

''',
    "Hint per-word twofer progress",
)

replace_between(
    "    function CreateTwoferRow(Twofer, Category) {",
    "    function CreateTwoferWordElement(Word, Visible) {",
    r'''    function CreateTwoferRow(Twofer, Category) {
        const Visibility = GetTwoferWordVisibility(Twofer, Category);

        const Row = document.createElement("div");
        Row.className = `lb-cubed-twofer-row lb-cubed-twofer-category-${Category}`;

        const FirstWord = CreateTwoferWordElement(
            Twofer.First,
            Visibility.FirstVisible
        );

        const Arrow = document.createElement("span");
        Arrow.className = "lb-cubed-twofer-arrow";
        Arrow.textContent = "→";

        const SecondWord = CreateTwoferWordElement(
            Twofer.Second,
            Visibility.SecondVisible
        );

        Row.append(FirstWord, Arrow, SecondWord);

        if (Category === "Found") {
            ApplyRecentTwoferHighlight(Row, Twofer.Key);
        }

        if (!NytSolutionKey || Twofer.Key !== NytSolutionKey) {
            return Row;
        }

        const NytWrapper = document.createElement("div");
        NytWrapper.className = "lb-cubed-nyt-solution";

        const NytLabel = document.createElement("div");
        NytLabel.className = "lb-cubed-nyt-solution-label";
        NytLabel.textContent = "⭐ NYT Solution";

        NytWrapper.append(NytLabel, Row);
        return NytWrapper;
    }

''',
    "Twofer highlight renderer",
)

replace_once(
    '''        AddLengthStat(LengthGrid, "3 letters", Stats.LengthStats["3"]);
        AddLengthStat(LengthGrid, "4 letters", Stats.LengthStats["4"]);
        AddLengthStat(LengthGrid, "5 letters", Stats.LengthStats["5"]);
        AddLengthStat(LengthGrid, "6 letters", Stats.LengthStats["6"]);
        AddLengthStat(LengthGrid, "7+ letters", Stats.LengthStats["7+"]);''',
    '''        AddLengthStat(LengthGrid, "3 letters", Stats.LengthStats["3"], "3");
        AddLengthStat(LengthGrid, "4 letters", Stats.LengthStats["4"], "4");
        AddLengthStat(LengthGrid, "5 letters", Stats.LengthStats["5"], "5");
        AddLengthStat(LengthGrid, "6 letters", Stats.LengthStats["6"], "6");
        AddLengthStat(LengthGrid, "7+ letters", Stats.LengthStats["7+"], "7+");''',
    "Length bucket highlight calls",
)

replace_between(
    "    function CreateWordTree(",
    "    function ReadTreeOpenStates(Panel) {",
    r'''    function CreateWordTree(
        SectionName,
        SummaryText,
        Words,
        DefaultOpen,
        PreviousOpenStates,
        Redacted
    ) {
        const Details = document.createElement("details");
        Details.className = "lb-cubed-tree lb-cubed-word-tree";

        ConfigureTree(
            Details,
            SectionName,
            PreviousOpenStates,
            DefaultOpen
        );

        const Summary = document.createElement("summary");
        Summary.textContent = SummaryText;
        Details.appendChild(Summary);

        const List = document.createElement("div");
        List.className = "lb-cubed-word-grid";

        if (Words.length === 0) {
            const Empty = document.createElement("div");
            Empty.className = "lb-cubed-empty";
            Empty.textContent = Redacted
                ? "You found everything. What in God's name."
                : "No words tracked yet.";
            List.appendChild(Empty);
        } else {
            const Fragment = document.createDocumentFragment();

            for (const Word of Words) {
                const Item = document.createElement("div");
                Item.className = Redacted
                    ? "lb-cubed-word lb-cubed-redacted"
                    : "lb-cubed-word lb-cubed-found-word";
                Item.textContent = Word;

                if (Redacted) {
                    Item.setAttribute("aria-label", "Unfound word, redacted");
                } else {
                    ApplyRecentWordHighlight(Item, Word);
                }

                Fragment.appendChild(Item);
            }

            List.appendChild(Fragment);
        }

        Details.appendChild(List);
        return Details;
    }

''',
    "Found word highlight renderer",
)

replace_between(
    "    function AddLengthStat(Container, Label, Values) {",
    "    // -------------------------------------------------------------------------\n    // Statistics",
    r'''    function AddLengthStat(Container, Label, Values, Bucket) {
        const Row = document.createElement("div");
        Row.className = "lb-cubed-length-stat";

        const LabelElement = document.createElement("span");
        LabelElement.className = "lb-cubed-length-label";
        LabelElement.textContent = Label;

        const ValueElement = document.createElement("span");
        ValueElement.className = "lb-cubed-length-value";
        ValueElement.textContent =
            `${Values.Found.toLocaleString()} / ${Values.Total.toLocaleString()}`;

        Row.append(LabelElement, ValueElement);
        ApplyRecentLengthHighlight(Row, Bucket);
        Container.appendChild(Row);
    }

''',
    "Length row highlighting",
)

style_insert_marker = '''            .lb-game-container.${LayoutClass} {
                box-sizing: border-box !important;
            }'''
style_insert_replacement = '''            .lb-game-container.${LayoutClass} {
                box-sizing: border-box !important;
                position: relative !important;
            }

            /*
                Issue #4: optional, explicit vertical-gap grip. It is physically
                positioned between TI and GB by JavaScript so it follows either
                side-by-side or stacked outer layout without becoming a grid item.
            */
            #${LayoutGapHandleId} {
                display: none;
                position: absolute;
                z-index: 45;
                height: 12px;
                cursor: ns-resize;
                touch-action: none;
                user-select: none;
            }

            .lb-game-container.lb-cubed-adjust-layout-gap > #${LayoutGapHandleId} {
                display: block;
            }

            #${LayoutGapHandleId}::after {
                content: "";
                position: absolute;
                left: 0;
                right: 0;
                top: 5px;
                height: 2px;
                border-radius: 2px;
                background: rgba(76, 34, 34, 0.58);
                opacity: 0.62;
                transition: opacity 100ms ease, height 100ms ease;
            }

            #${LayoutGapHandleId}:hover::after,
            #${LayoutGapHandleId}.lb-cubed-layout-gap-handle-active::after {
                opacity: 1;
                height: 3px;
            }

            /*
                Issue #14: small horizontal resize grips immediately below the
                two NYT page-fluff regions. CSS zoom gives Chrome a proportional
                layout resize, including the text inside each region.
            */
            .lb-cubed-page-resize-handle {
                position: relative;
                z-index: 9000;
                width: 100%;
                height: 9px;
                margin: 0;
                cursor: ns-resize;
                touch-action: none;
                user-select: none;
            }

            .lb-cubed-page-resize-handle::after {
                content: "";
                position: absolute;
                left: 12px;
                right: 12px;
                top: 4px;
                height: 1px;
                background: rgba(128, 128, 128, 0.24);
                transition: background 100ms ease, height 100ms ease;
            }

            .lb-cubed-page-resize-handle:hover::after,
            .lb-cubed-page-resize-handle-active::after {
                height: 2px;
                background: rgba(92, 37, 37, 0.62);
            }

            .lb-cubed-page-fluff-hidden {
                display: none !important;
            }

            #portal-game-header.lb-cubed-title-meta-layout {
                display: grid !important;
                grid-template-columns: auto auto minmax(0, 1fr) auto;
                grid-template-rows: auto auto auto;
                column-gap: 10px;
                row-gap: 3px;
                align-items: center;
            }

            #portal-game-header.lb-cubed-title-meta-layout > h2 {
                display: contents !important;
            }

            #portal-game-header.lb-cubed-title-meta-layout .pz-game-title {
                grid-column: 1 / -1;
                grid-row: 1;
            }

            #portal-game-header.lb-cubed-title-meta-layout .pz-game-date {
                grid-column: 1;
                grid-row: 2;
                margin: 0 !important;
            }

            #portal-game-header.lb-cubed-title-meta-layout .pz-byline {
                grid-column: 1 / -1;
                grid-row: 3;
                margin-top: 0 !important;
            }

            #portal-game-header.lb-cubed-title-meta-layout.lb-cubed-byline-next-to-date .pz-byline {
                grid-column: 2;
                grid-row: 2;
                align-self: center;
                margin: 0 !important;
            }

            #portal-game-header .lb-cubed-yesterday-proxy {
                grid-column: 4;
                grid-row: 2;
                justify-self: end;
                align-self: center;
            }

            .lb-cubed-original-yesterday-hidden {
                display: none !important;
            }'''
replace_once(style_insert_marker, style_insert_replacement, "outer layout styles")

replace_once(
    '''            .lb-cubed-header-text {
                min-width: 0;
            }

            .lb-cubed-header-actions {
                display: flex;
                flex: 0 1 auto;
                flex-wrap: wrap;
                gap: 5px;
                justify-content: flex-end;
                align-items: center;
            }''',
    '''            .lb-cubed-header-text {
                min-width: 0;
            }

            .lb-cubed-title-row {
                display: flex;
                align-items: baseline;
                gap: 8px;
                min-width: 0;
            }

            .lb-cubed-drive-status {
                flex: 0 0 auto;
                color: rgba(92, 92, 92, 0.72);
                font-size: 10px;
                font-weight: 400;
                white-space: nowrap;
            }

            .lb-cubed-header-actions {
                display: flex;
                flex: 0 1 auto;
                flex-wrap: nowrap;
                gap: 5px;
                justify-content: flex-end;
                align-items: center;
            }

            .lb-cubed-settings-menu {
                position: relative;
                flex: 0 0 auto;
            }

            .lb-cubed-settings-menu > summary {
                list-style: none;
                white-space: nowrap;
            }

            .lb-cubed-settings-menu > summary::-webkit-details-marker {
                display: none;
            }

            .lb-cubed-settings-panel {
                position: absolute;
                top: calc(100% + 5px);
                right: 0;
                z-index: 1000;
                width: min(350px, 80vw);
                max-height: min(72vh, 620px);
                overflow: auto;
                padding: 8px;
                background: rgb(229, 160, 158);
                border: 1px solid rgba(76, 34, 34, 0.70);
                border-radius: 4px;
                box-shadow: 0 8px 26px rgba(0, 0, 0, 0.28);
            }

            .lb-cubed-settings-section + .lb-cubed-settings-section {
                margin-top: 9px;
                padding-top: 8px;
                border-top: 1px solid rgba(78, 34, 34, 0.20);
            }

            .lb-cubed-settings-section-title {
                margin-bottom: 5px;
                color: rgb(48, 24, 24);
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 0.04em;
                text-transform: uppercase;
            }

            .lb-cubed-settings-checkbox,
            .lb-cubed-settings-range,
            .lb-cubed-settings-number-row,
            .lb-cubed-settings-action-row {
                display: flex;
                align-items: center;
                gap: 6px;
                min-height: 28px;
                color: rgb(48, 24, 24);
                font-size: 10px;
            }

            .lb-cubed-settings-checkbox {
                cursor: pointer;
            }

            .lb-cubed-settings-checkbox input {
                margin: 0;
                accent-color: rgb(92, 37, 37);
            }

            .lb-cubed-settings-label {
                flex: 1 1 auto;
                min-width: 0;
            }

            .lb-cubed-settings-range input[type="range"] {
                flex: 0 1 120px;
                min-width: 70px;
                accent-color: rgb(92, 37, 37);
            }

            .lb-cubed-settings-range-value {
                flex: 0 0 34px;
                font-family: Consolas, "Courier New", monospace;
                font-weight: 700;
                text-align: right;
            }

            .lb-cubed-settings-number-wrap {
                display: inline-flex;
                align-items: center;
                gap: 2px;
                flex: 0 0 auto;
            }

            .lb-cubed-settings-number-wrap input {
                width: 62px;
                padding: 2px 3px;
                border: 1px solid rgba(78, 34, 34, 0.35);
                border-radius: 3px;
                background: rgba(255, 255, 255, 0.35);
                color: rgb(48, 24, 24);
                font: inherit;
                font-family: Consolas, "Courier New", monospace;
                text-align: right;
            }

            .lb-cubed-settings-suffix {
                min-width: 14px;
                color: rgba(48, 24, 24, 0.68);
                font-size: 9px;
            }

            .lb-cubed-settings-mini-button {
                padding: 2px 5px;
                border: 1px solid rgba(78, 34, 34, 0.32);
                border-radius: 3px;
                background: rgba(255, 255, 255, 0.20);
                color: rgb(48, 24, 24);
                font: inherit;
                font-size: 9px;
                cursor: pointer;
            }

            .lb-cubed-settings-button-row {
                display: flex;
                justify-content: flex-end;
                gap: 5px;
                margin-top: 4px;
            }''',
    "header/settings styles",
)

replace_once(
    '''            .lb-cubed-potential-word {
                min-width: 0;
                padding: 3px 5px;
                background: rgba(255, 255, 255, 0.11);
                border-radius: 2px;
                color: rgba(48, 24, 24, 0.75);
                font-family: Consolas, "Courier New", monospace;
                font-size: 10px;
                overflow-wrap: anywhere;
            }''',
    '''            .lb-cubed-potential-word {
                display: flex;
                align-items: baseline;
                justify-content: space-between;
                gap: 8px;
                min-width: 0;
                padding: 3px 5px;
                background: rgba(255, 255, 255, 0.11);
                border-radius: 2px;
                color: rgba(48, 24, 24, 0.75);
                font-family: Consolas, "Courier New", monospace;
                font-size: 10px;
                overflow-wrap: anywhere;
            }

            .lb-cubed-potential-word-label {
                min-width: 0;
                overflow-wrap: anywhere;
            }

            .lb-cubed-potential-word-progress {
                flex: 0 0 auto;
                margin-left: auto;
                color: rgba(48, 24, 24, 0.68);
                font-size: 9px;
                font-weight: 700;
                white-space: nowrap;
            }

            .lb-cubed-potential-word-complete {
                text-decoration: line-through;
                opacity: 0.70;
            }''',
    "hint progress styles",
)

replace_once(
    '''            .lb-cubed-found-word {
                background: rgba(255, 255, 255, 0.25);
                color: rgb(42, 20, 20);
            }''',
    '''            .lb-cubed-found-word {
                background: rgba(255, 255, 255, 0.25);
                color: rgb(42, 20, 20);
            }

            @keyframes lb-cubed-new-highlight-fade {
                from {
                    box-shadow: inset 0 0 0 9999px chartreuse;
                }
                to {
                    box-shadow: inset 0 0 0 9999px rgba(127, 255, 0, 0);
                }
            }

            .lb-cubed-new-highlight {
                animation:
                    lb-cubed-new-highlight-fade
                    var(--lb-cubed-highlight-duration, 1000ms)
                    ease-out
                    1;
            }''',
    "new-item highlight styles",
)

replace_once(
    '''                .lb-cubed-header-actions {
                    width: 100%;
                    justify-content: flex-start;
                }

                .lb-cubed-line-speed-control {
                    flex: 1 1 180px;
                }

                .lb-cubed-line-speed-slider {
                    flex: 1 1 auto;
                    width: auto;
                }''',
    '''                .lb-cubed-header-actions {
                    width: 100%;
                    justify-content: flex-start;
                    flex-wrap: wrap;
                }

                .lb-cubed-title-row {
                    flex-wrap: wrap;
                }

                .lb-cubed-settings-panel {
                    left: 0;
                    right: auto;
                    width: min(340px, calc(100vw - 36px));
                }''',
    "narrow header settings styles",
)

SOURCE.write_text(text, encoding="utf-8")

changelog = CHANGELOG.read_text(encoding="utf-8")
section = '''## 1.12.0-beta.1
- Moved Hide Par, animation controls, Google Drive actions, Export, and Import into a compact Settings menu; added a lightweight Drive status beside Word Log.
- Added an optional draggable TI-to-GB layout-gap handle with a stored precise gap setting.
- Added per-word solved/total Twofer progress to First/Second Hints and strike-through when a positional word is fully exhausted.
- Added configurable chartreuse fade highlights for newly found words and solved Twofers, including the matching Words by Length row.
- Added proportional resize/hide controls and on-page drag handles for NYT's global header and Letter Boxed title area.
- Added Settings toggles to place the byline and a Yesterday proxy beside the date.

'''
if "## 1.12.0-beta.1\n" not in changelog:
    changelog = changelog.replace("# Changelog\n\n", "# Changelog\n\n" + section, 1)
CHANGELOG.write_text(changelog, encoding="utf-8")

# Static release guards for the one-shot workflow.
final = SOURCE.read_text(encoding="utf-8")
required = [
    "// @version      1.12.0-beta.1",
    'Summary.textContent = "⚙ Settings";',
    'DriveStatus.id = GoogleDriveStatusId;',
    '"Adjust layout gap"',
    '"New-item highlight"',
    'lb-cubed-potential-word-progress',
    'lb-cubed-new-highlight',
    'NytHeaderResizeHandleId',
    'NytTitleResizeHandleId',
    '"Put byline next to date"',
    '"Put Yesterday next to date"',
]
missing = [value for value in required if value not in final]
if missing:
    raise SystemExit("Missing expected implementation markers: " + repr(missing))

print("QoL patch applied successfully.")
