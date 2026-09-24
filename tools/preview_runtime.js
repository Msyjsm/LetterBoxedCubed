/*
    PREVIEW-ONLY RUNTIME
    This file is injected into LetterBoxedCubed.preview.user.js by
    tools/build_preview.py. It is intentionally absent from the production
    userscript distributed from main.
*/

    const PreviewDebugPanelId = "lb-cubed-preview-debug";
    const PreviewDebugStyleId = "lb-cubed-preview-debug-styles";
    const PreviewDebugToggleButtonId = "lb-cubed-preview-debug-toggle";
    const PreviewHistoryTestButtonId = "lb-cubed-preview-history-test-toggle";
    const PreviewHistoryTestOverlayId = "lb-cubed-preview-history-test-overlay";
    const PreviewHistoryTestPanelId = "lb-cubed-preview-history-test-panel";
    const PreviewVersionLabelId = "lb-cubed-preview-version";

    let PreviewDebugObserver = null;
    let PreviewChromeObserver = null;
    let PreviewDebugRenderTimer = null;
    let PreviewDebugNextElementId = 1;
    let PreviewDebugPaneVisible = false;
    let PreviewHistoricalTestModeActive = false;
    let PreviewHistoricalInjectedWords = new Set();
    let PreviewHistoricalBaseline = null;
    let PreviewHistoricalSelectedTwoferKey = null;
    const PreviewDebugElementIds = new WeakMap();
    const PreviewDebugElementsById = new Map();
    const PreviewDebugOriginalDisplay = new WeakMap();
    const PreviewDebugOverriddenElements = new Set();
    const PreviewDebugMutationLog = [];

    const BootstrapDiagnostics = [];
    const BootstrapDiagnosticSessionKey =
        "LetterBoxedCubed_PreviewBootstrapTrace";

    function RecordBootstrapDiagnostic(Stage, Details = {}) {
        if (UserscriptBuildChannel !== "preview") {
            return;
        }

        const NavigationEntry =
            typeof performance?.getEntriesByType === "function"
                ? performance.getEntriesByType("navigation")[0]
                : null;

        const Entry = {
            Stage,
            Timestamp: new Date().toISOString(),
            ReadyState: document.readyState,
            WasDiscarded: Boolean(document.wasDiscarded),
            NavigationType: NavigationEntry?.type || null,
            ...Details
        };

        BootstrapDiagnostics.push(Entry);
        const Snapshot = BootstrapDiagnostics.slice(-100);

        try {
            sessionStorage.setItem(
                BootstrapDiagnosticSessionKey,
                JSON.stringify(Snapshot)
            );
        } catch {}

        try {
            PageWindow.__LetterBoxedCubedBootstrapTrace = Snapshot;
        } catch {}

        console.debug("[Letter Boxed Cubed][bootstrap]", Entry);
    }

    RecordBootstrapDiagnostic("userscript-channel-active");

    function IsPreviewDebugTypingContext(Target) {
        return Boolean(
            Target instanceof Element &&
            Target.closest(
                `#${PreviewDebugPanelId}, #${PreviewHistoryTestOverlayId}`
            )
        );
    }

    // -------------------------------------------------------------------------
    // Preview-only DOM inspector
    // -------------------------------------------------------------------------

    function EnsurePreviewDebugStyles() {
        if (
            UserscriptBuildChannel !== "preview" ||
            document.getElementById(PreviewDebugStyleId)
        ) {
            return;
        }

        const Style = document.createElement("style");
        Style.id = PreviewDebugStyleId;
        Style.textContent = `
            #${PreviewVersionLabelId} {
                position: absolute;
                z-index: 20;
                color: rgba(92, 92, 92, 0.78);
                font: 10px/1.2 Consolas, "Courier New", monospace;
                white-space: nowrap;
                pointer-events: none;
                user-select: none;
            }

            #${PreviewDebugToggleButtonId},
            #${PreviewHistoryTestButtonId} {
                position: absolute;
                z-index: 22;
                padding: 4px 7px;
                border: 1px solid rgba(255, 255, 255, 0.45);
                border-radius: 3px;
                background: rgba(20, 20, 24, 0.96);
                color: #f2f2f2;
                box-shadow: 0 3px 12px rgba(0, 0, 0, 0.32);
                font: 700 11px/1.25 Arial, sans-serif;
                white-space: nowrap;
                cursor: pointer;
            }

            #${PreviewDebugToggleButtonId}:hover,
            #${PreviewHistoryTestButtonId}:hover {
                background: #303038;
            }

            #${PreviewHistoryTestButtonId}.lbc-history-test-active {
                border-color: #ffd166;
                background: #4a3510;
                color: #fff3c4;
            }

            #${PreviewHistoryTestOverlayId} {
                position: fixed;
                inset: 0;
                z-index: 40;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 18px;
                background: rgba(0, 0, 0, 0.42);
            }

            #${PreviewHistoryTestPanelId} {
                width: min(620px, calc(100vw - 36px));
                max-height: calc(100vh - 36px);
                overflow: auto;
                padding: 14px;
                border: 1px solid #777;
                border-radius: 6px;
                background: #18181d;
                color: #f4f4f4;
                box-shadow: 0 8px 36px rgba(0, 0, 0, 0.52);
                font: 12px/1.4 Arial, sans-serif;
            }

            #${PreviewHistoryTestPanelId} * {
                box-sizing: border-box;
            }

            #${PreviewHistoryTestPanelId} h2 {
                margin: 0 0 8px;
                font-size: 16px;
            }

            #${PreviewHistoryTestPanelId} .lbc-history-test-warning {
                margin: 0 0 10px;
                padding: 8px;
                border: 1px solid #8b6b1f;
                border-radius: 4px;
                background: #34290f;
                color: #ffe7a3;
            }

            #${PreviewHistoryTestPanelId} .lbc-history-test-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
                margin: 8px 0;
            }

            #${PreviewHistoryTestPanelId} .lbc-history-test-block {
                padding: 8px;
                border: 1px solid #555;
                border-radius: 4px;
                background: #222229;
            }

            #${PreviewHistoryTestPanelId} .lbc-history-test-actions {
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
                margin-top: 6px;
            }

            #${PreviewHistoryTestPanelId} button,
            #${PreviewHistoryTestPanelId} select {
                min-height: 28px;
                border: 1px solid #777;
                border-radius: 3px;
                background: #303038;
                color: #fff;
                font: 12px/1.3 Arial, sans-serif;
            }

            #${PreviewHistoryTestPanelId} button {
                padding: 4px 8px;
                cursor: pointer;
            }

            #${PreviewHistoryTestPanelId} button:disabled,
            #${PreviewHistoryTestPanelId} select:disabled {
                opacity: 0.45;
                cursor: not-allowed;
            }

            #${PreviewHistoryTestPanelId} select {
                width: 100%;
                padding: 3px 5px;
            }

            #${PreviewHistoryTestPanelId} .lbc-history-test-status {
                margin-top: 10px;
                padding: 8px;
                border: 1px solid #555;
                border-radius: 4px;
                background: #101014;
                font: 11px/1.45 Consolas, "Courier New", monospace;
                white-space: pre-wrap;
            }

            @media (max-width: 680px) {
                #${PreviewHistoryTestPanelId} .lbc-history-test-grid {
                    grid-template-columns: 1fr;
                }
            }

            #${PreviewDebugPanelId} {
                position: fixed;
                z-index: 21;
                width: 340px;
                min-width: 280px;
                max-width: min(420px, calc(100vw - 16px));
                padding: 10px;
                overflow: auto;
                background: rgba(20, 20, 24, 0.96);
                color: #f2f2f2;
                border: 1px solid rgba(255, 255, 255, 0.35);
                border-radius: 4px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.38);
                font: 11px/1.35 Consolas, "Courier New", monospace;
                text-align: left;
            }

            #${PreviewDebugPanelId} * {
                box-sizing: border-box;
            }

            #${PreviewDebugPanelId} .lbc-debug-title {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 8px;
                margin-bottom: 8px;
                font: 700 12px/1.2 Arial, sans-serif;
            }

            #${PreviewDebugPanelId} .lbc-debug-tools {
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
                margin-bottom: 8px;
            }

            #${PreviewDebugPanelId} button {
                padding: 2px 5px;
                border: 1px solid #777;
                border-radius: 3px;
                background: #303038;
                color: #fff;
                font: 11px/1.3 Arial, sans-serif;
                cursor: pointer;
            }

            #${PreviewDebugPanelId} .lbc-debug-section-title {
                margin: 8px 0 3px;
                padding-top: 5px;
                border-top: 1px solid #555;
                color: #bfe3ff;
                font-weight: 700;
            }

            #${PreviewDebugPanelId} .lbc-debug-row {
                display: flex;
                align-items: flex-start;
                gap: 4px;
                min-width: 0;
                margin: 1px 0;
            }

            #${PreviewDebugPanelId} .lbc-debug-row input {
                flex: 0 0 auto;
                margin: 2px 0 0;
            }

            #${PreviewDebugPanelId} .lbc-debug-node {
                min-width: 0;
                overflow: hidden;
                color: inherit;
                text-overflow: ellipsis;
                white-space: nowrap;
                cursor: pointer;
            }

            #${PreviewDebugPanelId} .lbc-debug-node:hover {
                color: #fff6a8;
                text-decoration: underline;
            }

            #${PreviewDebugPanelId} .lbc-debug-native-hidden {
                opacity: 0.58;
            }

            #${PreviewDebugPanelId} .lbc-debug-log,
            #${PreviewDebugPanelId} .lbc-debug-html {
                max-height: 180px;
                margin: 3px 0 0;
                padding: 5px;
                overflow: auto;
                border: 1px solid #50505a;
                background: #111116;
                color: #e8e8e8;
                white-space: pre-wrap;
                word-break: break-word;
            }
        `;

        document.head.appendChild(Style);
    }

    function GetPreviewDebugElementId(ElementNode) {
        let Id = PreviewDebugElementIds.get(ElementNode);

        if (!Id) {
            Id = PreviewDebugNextElementId++;
            PreviewDebugElementIds.set(ElementNode, Id);
            PreviewDebugElementsById.set(Id, ElementNode);
        }

        return Id;
    }

    function DescribePreviewDebugNode(Node) {
        if (!(Node instanceof Element)) {
            const Text = String(Node?.textContent || "")
                .replace(/\s+/g, " ")
                .trim()
                .slice(0, 70);
            return `${Node?.nodeName || "node"}${Text ? ` "${Text}"` : ""}`;
        }

        const IdPart = Node.id
            ? `#${Node.id}`
            : "";
        const Classes = [...Node.classList]
            .slice(0, 6)
            .map(Name => `.${Name}`)
            .join("");
        const Text = String(Node.textContent || "")
            .replace(/\s+/g, " ")
            .trim()
            .slice(0, 55);
        const Style = getComputedStyle(Node);
        const Rect = Node.getBoundingClientRect();
        const Hidden =
            Style.display === "none" ||
            Style.visibility === "hidden";

        return `${Node.tagName.toLowerCase()}${IdPart}${Classes}` +
            `${Text ? ` "${Text}"` : ""}` +
            ` [${Math.round(Rect.width)}x${Math.round(Rect.height)}` +
            `${Hidden ? ", hidden" : ""}]`;
    }

    function LogPreviewDebugMutation(Prefix, Node) {
        PreviewDebugMutationLog.push(
            `${new Date().toLocaleTimeString()} ${Prefix} ${DescribePreviewDebugNode(Node)}`
        );

        if (PreviewDebugMutationLog.length > 160) {
            PreviewDebugMutationLog.splice(
                0,
                PreviewDebugMutationLog.length - 160
            );
        }
    }

    function QueuePreviewDebugRender() {
        if (UserscriptBuildChannel !== "preview") {
            return;
        }

        clearTimeout(PreviewDebugRenderTimer);
        PreviewDebugRenderTimer = setTimeout(
            RenderPreviewDebugPane,
            40
        );
    }

    function SetPreviewDebugVisibility(ElementNode, Visible) {
        if (!(ElementNode instanceof Element)) {
            return;
        }

        if (!PreviewDebugOriginalDisplay.has(ElementNode)) {
            PreviewDebugOriginalDisplay.set(ElementNode, {
                Value: ElementNode.style.getPropertyValue("display"),
                Priority: ElementNode.style.getPropertyPriority("display")
            });
        }

        PreviewDebugOverriddenElements.add(ElementNode);
        ElementNode.style.setProperty(
            "display",
            Visible ? "revert" : "none",
            "important"
        );

        QueuePreviewDebugRender();
        QueuePanelLayoutUpdate();
    }

    function ResetPreviewDebugVisibility() {
        for (const ElementNode of PreviewDebugOverriddenElements) {
            if (!ElementNode?.style) {
                continue;
            }

            const Original = PreviewDebugOriginalDisplay.get(ElementNode);

            if (Original?.Value) {
                ElementNode.style.setProperty(
                    "display",
                    Original.Value,
                    Original.Priority || ""
                );
            } else {
                ElementNode.style.removeProperty("display");
            }
        }

        PreviewDebugOverriddenElements.clear();
        QueuePreviewDebugRender();
        QueuePanelLayoutUpdate();
    }

    function CreatePreviewDebugTree(Root, Container) {
        if (!Root) {
            Container.textContent = "(not found)";
            return;
        }

        let RowCount = 0;
        const MaximumRows = 300;

        const AddNode = (ElementNode, Depth) => {
            if (!(ElementNode instanceof Element) || RowCount >= MaximumRows) {
                return;
            }

            RowCount++;
            const ElementId = GetPreviewDebugElementId(ElementNode);
            const Computed = getComputedStyle(ElementNode);
            const NativeVisible =
                Computed.display !== "none" &&
                Computed.visibility !== "hidden";
            const ForcedDisplay = ElementNode.style.getPropertyPriority("display") === "important"
                ? ElementNode.style.getPropertyValue("display")
                : "";

            const Row = document.createElement("div");
            Row.className = "lbc-debug-row" +
                (!NativeVisible ? " lbc-debug-native-hidden" : "");
            Row.style.paddingLeft = `${Depth * 11}px`;

            const Checkbox = document.createElement("input");
            Checkbox.type = "checkbox";
            Checkbox.checked = ForcedDisplay === "revert"
                ? true
                : ForcedDisplay === "none"
                    ? false
                    : NativeVisible;
            Checkbox.title =
                "Debug visibility override. Reset overrides restores NYT/LBC styling.";
            Checkbox.addEventListener("change", () => {
                SetPreviewDebugVisibility(
                    PreviewDebugElementsById.get(ElementId),
                    Checkbox.checked
                );
            });

            const NodeButton = document.createElement("span");
            NodeButton.className = "lbc-debug-node";
            NodeButton.textContent = DescribePreviewDebugNode(ElementNode);
            NodeButton.title = "Click to show current outerHTML and log the live element to DevTools.";
            NodeButton.addEventListener("click", () => {
                const Inspector = document.querySelector(
                    `#${PreviewDebugPanelId} .lbc-debug-html`
                );

                if (Inspector) {
                    Inspector.textContent = ElementNode.outerHTML;
                }

                console.log(
                    "[Letter Boxed Cubed][DOM debug]",
                    ElementNode,
                    ElementNode.outerHTML
                );
            });

            Row.append(
                Checkbox,
                NodeButton
            );
            Container.appendChild(Row);

            for (const Child of ElementNode.children) {
                AddNode(Child, Depth + 1);
            }
        };

        AddNode(Root, 0);

        if (RowCount >= MaximumRows) {
            const Truncated = document.createElement("div");
            Truncated.textContent = "... tree truncated at 300 elements ...";
            Container.appendChild(Truncated);
        }
    }

    function RenderPreviewDebugPane() {
        if (UserscriptBuildChannel !== "preview") {
            return;
        }

        const DebugPanel = document.getElementById(PreviewDebugPanelId);
        if (!DebugPanel) {
            return;
        }

        const TiTree = DebugPanel.querySelector("[data-lbc-debug-tree='ti']");
        const GbTree = DebugPanel.querySelector("[data-lbc-debug-tree='gb']");
        const MutationLog = DebugPanel.querySelector(".lbc-debug-log");

        if (TiTree) {
            TiTree.replaceChildren();
            CreatePreviewDebugTree(
                document.querySelector(".lb-game-container .lb-word-container"),
                TiTree
            );
        }

        if (GbTree) {
            GbTree.replaceChildren();
            CreatePreviewDebugTree(
                document.querySelector(".lb-game-container .lb-square-container"),
                GbTree
            );
        }

        if (MutationLog) {
            MutationLog.textContent = PreviewDebugMutationLog.length
                ? [...PreviewDebugMutationLog].reverse().join("\n")
                : "(no mutations captured yet)";
        }

        PositionPreviewDebugPane();
    }

    function PositionPreviewDebugPane() {
        if (UserscriptBuildChannel !== "preview") {
            return;
        }

        const DebugPanel = document.getElementById(PreviewDebugPanelId);
        const ToggleButton = document.getElementById(PreviewDebugToggleButtonId);
        const HistoryTestButton = document.getElementById(PreviewHistoryTestButtonId);
        const Panel = document.getElementById(PanelId);

        if (!DebugPanel || !ToggleButton || !Panel) {
            return;
        }

        const PanelRect = Panel.getBoundingClientRect();
        const SettingsSummary = document.querySelector(
            `#${SettingsMenuId} > summary`
        );
        const SettingsRect = SettingsSummary?.getBoundingClientRect();
        const ToggleWidth = Math.max(1, ToggleButton.offsetWidth);
        const ToggleHeight = Math.max(1, ToggleButton.offsetHeight);

        /*
            Keep the control outside LBC itself, immediately above the header
            and horizontally just left of the Settings button when possible.
        */
        const ScrollX = window.scrollX || window.pageXOffset || 0;
        const ScrollY = window.scrollY || window.pageYOffset || 0;
        const ToggleLeft = Clamp(
            (SettingsRect?.right ?? PanelRect.right) - ToggleWidth + ScrollX,
            ScrollX + 8,
            Math.max(
                ScrollX + 8,
                ScrollX + window.innerWidth - ToggleWidth - 8
            )
        );
        const ToggleTop = Math.max(
            ScrollY + 8,
            PanelRect.top + ScrollY - ToggleHeight - 4
        );

        ToggleButton.style.left = `${ToggleLeft}px`;
        ToggleButton.style.top = `${ToggleTop}px`;

        if (HistoryTestButton) {
            const HistoryWidth = Math.max(1, HistoryTestButton.offsetWidth);
            const HistoryLeft = Clamp(
                ToggleLeft - HistoryWidth - 4,
                ScrollX + 8,
                Math.max(
                    ScrollX + 8,
                    ScrollX + window.innerWidth - HistoryWidth - 8
                )
            );
            HistoryTestButton.style.left = `${HistoryLeft}px`;
            HistoryTestButton.style.top = `${ToggleTop}px`;
        }

        const ToggleRect = ToggleButton.getBoundingClientRect();
        const DebugWidth = Math.min(
            340,
            Math.max(280, window.innerWidth - 16)
        );

        /*
            The right LBC grip line sits ResizeGripLineOffset px outside LBC.
            Put the debugger another equal offset beyond that line, so the
            grip is visually centered in the gutter between the two panels.
        */
        const Left = Math.max(
            8,
            PanelRect.right + (ResizeGripLineOffset * 2)
        );
        const Top = Math.max(
            8,
            ToggleRect.bottom + 4
        );
        const MaximumHeight = Math.max(
            180,
            window.innerHeight - Top - 8
        );

        DebugPanel.style.width = `${DebugWidth}px`;
        DebugPanel.style.left = `${Left}px`;
        DebugPanel.style.top = `${Top}px`;
        DebugPanel.style.maxHeight = `${MaximumHeight}px`;
    }

    function IsVisiblePreviewNativeDialog() {
        const Candidates = document.querySelectorAll(
            'dialog[open], [role="dialog"], [aria-modal="true"]'
        );

        for (const Candidate of Candidates) {
            if (!(Candidate instanceof Element)) {
                continue;
            }

            if (Candidate.closest(
                `#${PreviewDebugPanelId}, #${PreviewHistoryTestOverlayId}`
            )) {
                continue;
            }

            const Style = getComputedStyle(Candidate);
            const Rect = Candidate.getBoundingClientRect();

            if (
                Style.display !== "none" &&
                Style.visibility !== "hidden" &&
                Number(Style.opacity || 1) !== 0 &&
                Rect.width > 0 &&
                Rect.height > 0
            ) {
                return true;
            }
        }

        return false;
    }

    function UpdatePreviewChromeForNativeDialog() {
        const Hide = IsVisiblePreviewNativeDialog();

        for (const Id of [
            PreviewVersionLabelId,
            PreviewDebugToggleButtonId,
            PreviewHistoryTestButtonId,
            PreviewDebugPanelId
        ]) {
            const ElementNode = document.getElementById(Id);
            if (ElementNode) {
                const DesiredVisibility = Hide ? "hidden" : "";
                if (ElementNode.style.visibility !== DesiredVisibility) {
                    ElementNode.style.visibility = DesiredVisibility;
                }
            }
        }
    }

    function StartPreviewChromeObserver() {
        PreviewChromeObserver?.disconnect();

        PreviewChromeObserver = new MutationObserver(() => {
            UpdatePreviewChromeForNativeDialog();
        });

        PreviewChromeObserver.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: [
                "class",
                "style",
                "open",
                "aria-hidden",
                "aria-modal"
            ]
        });

        UpdatePreviewChromeForNativeDialog();
    }

    function StartPreviewDebugObserver() {
        if (UserscriptBuildChannel !== "preview") {
            return;
        }

        PreviewDebugObserver?.disconnect();

        const Roots = [
            document.querySelector(".lb-game-container .lb-word-container"),
            document.querySelector(".lb-game-container .lb-square-container")
        ].filter(Boolean);

        if (!Roots.length) {
            return;
        }

        PreviewDebugObserver = new MutationObserver(Mutations => {
            for (const Mutation of Mutations) {
                if (Mutation.type === "childList") {
                    for (const Node of Mutation.addedNodes) {
                        LogPreviewDebugMutation("+", Node);
                    }
                    for (const Node of Mutation.removedNodes) {
                        LogPreviewDebugMutation("-", Node);
                    }
                } else if (Mutation.type === "attributes") {
                    LogPreviewDebugMutation(
                        `~ @${Mutation.attributeName}`,
                        Mutation.target
                    );
                } else if (Mutation.type === "characterData") {
                    LogPreviewDebugMutation("~ text", Mutation.target.parentNode);
                }
            }

            QueuePreviewDebugRender();
        });

        for (const Root of Roots) {
            PreviewDebugObserver.observe(Root, {
                childList: true,
                subtree: true,
                characterData: true,
                attributes: true,
                attributeOldValue: true,
                attributeFilter: [
                    "class",
                    "style",
                    "hidden",
                    "disabled",
                    "aria-hidden"
                ]
            });
        }
    }

    function GetRunningUserscriptVersion() {
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
        const ScrollX = window.scrollX || window.pageXOffset || 0;
        const ScrollY = window.scrollY || window.pageYOffset || 0;
        const Left = Clamp(
            (LogoRect?.left ?? (PanelRect.left + 12)) + ScrollX,
            ScrollX + 4,
            Math.max(
                ScrollX + 4,
                ScrollX + window.innerWidth - Label.offsetWidth - 4
            )
        );
        const Top = Math.max(
            ScrollY + 2,
            PanelRect.top + ScrollY - LabelHeight - 4
        );

        Label.style.left = `${Math.round(Left)}px`;
        Label.style.top = `${Math.round(Top)}px`;
    }



    // -------------------------------------------------------------------------
    // Preview-only historical-word sandbox
    // -------------------------------------------------------------------------

    function GetPreviewHistoricalAvailableTwofers() {
        const SolvedKeys =
            PreviewHistoricalBaseline?.FoundTwofers ||
            FoundTwofers;

        return Twofers.filter(
            Twofer => SolvedKeys.has(Twofer.Key)
        );
    }

    function GetPreviewHistoricalSelectedTwofer() {
        if (!PreviewHistoricalSelectedTwoferKey) {
            return null;
        }

        return GetPreviewHistoricalAvailableTwofers().find(
            Twofer => Twofer.Key === PreviewHistoricalSelectedTwoferKey
        ) || null;
    }

    function ChoosePreviewHistoricalDefaultTwofer() {
        const AvailableTwofers =
            GetPreviewHistoricalAvailableTwofers();

        PreviewHistoricalSelectedTwoferKey =
            AvailableTwofers[0]?.Key || null;
    }

    function RecomputePreviewHistoricalSandboxState() {
        if (!PreviewHistoricalTestModeActive || !PreviewHistoricalBaseline) {
            return;
        }

        const HistoricalBaseline = new Set(
            PreviewHistoricalBaseline.PreviouslyFoundWordsForPuzzle
        );
        const SelectedTwofer =
            GetPreviewHistoricalSelectedTwofer();

        /*
            A testable pair necessarily exists in today's real FoundTwofers.
            Remove its two words from the real historical baseline while the
            scenario is active so First/Second/Both/Neither are deterministic.
        */
        if (SelectedTwofer) {
            HistoricalBaseline.delete(SelectedTwofer.First);
            HistoricalBaseline.delete(SelectedTwofer.Second);
        }

        PreviouslyFoundWordsForPuzzle = new Set([
            ...HistoricalBaseline,
            ...PreviewHistoricalInjectedWords
        ]);

        KnownWordsForPuzzle = new Set([
            ...PreviouslyFoundWordsForPuzzle,
            ...FoundWords
        ]);
    }

    function SnapshotPreviewHistoricalBaseline() {
        PreviewHistoricalBaseline = {
            FoundWords: new Set(FoundWords),
            FoundTwofers: new Set(FoundTwofers),
            PreviouslyFoundWordsForPuzzle:
                new Set(PreviouslyFoundWordsForPuzzle),
            KnownWordsForPuzzle: new Set(KnownWordsForPuzzle),
            RecentWordHighlights: new Map(RecentWordHighlights),
            RecentTwoferHighlights: new Map(RecentTwoferHighlights)
        };
    }

    function RestorePreviewHistoricalBaseline({ KeepActive = false } = {}) {
        if (!PreviewHistoricalBaseline) {
            return;
        }

        FoundWords = new Set(PreviewHistoricalBaseline.FoundWords);
        FoundTwofers = new Set(PreviewHistoricalBaseline.FoundTwofers);
        PreviouslyFoundWordsForPuzzle = new Set(
            PreviewHistoricalBaseline.PreviouslyFoundWordsForPuzzle
        );
        KnownWordsForPuzzle = new Set(
            PreviewHistoricalBaseline.KnownWordsForPuzzle
        );

        RecentWordHighlights.clear();
        for (const [Key, Value] of PreviewHistoricalBaseline.RecentWordHighlights) {
            RecentWordHighlights.set(Key, Value);
        }

        RecentTwoferHighlights.clear();
        for (const [Key, Value] of PreviewHistoricalBaseline.RecentTwoferHighlights) {
            RecentTwoferHighlights.set(Key, Value);
        }

        PreviewHistoricalInjectedWords = new Set();

        if (KeepActive) {
            const SelectedTwofer =
                GetPreviewHistoricalSelectedTwofer();

            if (SelectedTwofer) {
                FoundTwofers.delete(SelectedTwofer.Key);
                FoundWords.delete(SelectedTwofer.First);
                FoundWords.delete(SelectedTwofer.Second);
                RecentWordHighlights.delete(SelectedTwofer.First);
                RecentWordHighlights.delete(SelectedTwofer.Second);
                RecentTwoferHighlights.delete(SelectedTwofer.Key);
            }
        } else {
            PreviewHistoricalTestModeActive = false;
            PreviewHistoricalBaseline = null;
        }

        RenderPanel();
        QueuePanelLayoutUpdate();
        UpdatePreviewHistoricalTestButton();
        RenderPreviewHistoricalTestPanel();
    }

    function EnterPreviewHistoricalTestMode() {
        if (PreviewHistoricalTestModeActive) {
            return true;
        }

        if (CloudSyncInFlight) {
            alert(
                "LBC is currently syncing with Google Drive. Wait for that sync to finish, then start History Test mode again."
            );
            return false;
        }

        if (CloudSyncTimer) {
            clearTimeout(CloudSyncTimer);
            CloudSyncTimer = null;
        }
        CloudSyncPending = false;

        SnapshotPreviewHistoricalBaseline();
        PreviewHistoricalTestModeActive = true;
        PreviewHistoricalInjectedWords = new Set();
        ChoosePreviewHistoricalDefaultTwofer();
        RestorePreviewHistoricalBaseline({ KeepActive: true });
        RecomputePreviewHistoricalSandboxState();
        UpdatePreviewHistoricalTestButton();

        console.info(
            "[Letter Boxed Cubed][preview] Historical test mode enabled. " +
            "LBC progress persistence and Google Drive sync are paused."
        );
        return true;
    }

    function ExitPreviewHistoricalTestMode() {
        if (!PreviewHistoricalTestModeActive) {
            return;
        }

        RestorePreviewHistoricalBaseline();

        console.info(
            "[Letter Boxed Cubed][preview] Historical test mode disabled; " +
            "real LBC state restored."
        );
    }

    function SetPreviewHistoricalInjection(Mode) {
        if (!EnterPreviewHistoricalTestMode()) {
            return;
        }

        const Twofer = GetPreviewHistoricalSelectedTwofer();
        if (!Twofer) {
            return;
        }

        PreviewHistoricalInjectedWords = new Set();

        if (Mode === "First" || Mode === "Both") {
            PreviewHistoricalInjectedWords.add(Twofer.First);
        }
        if (Mode === "Second" || Mode === "Both") {
            PreviewHistoricalInjectedWords.add(Twofer.Second);
        }

        RecomputePreviewHistoricalSandboxState();
        RenderPanel();
        QueuePanelLayoutUpdate();
        RenderPreviewHistoricalTestPanel();
    }

    function SimulatePreviewHistoricalWordDiscovery(Position) {
        if (!EnterPreviewHistoricalTestMode()) {
            return;
        }

        const Twofer = GetPreviewHistoricalSelectedTwofer();
        const Word = Position === "Second"
            ? Twofer?.Second
            : Twofer?.First;

        if (!Word || FoundWords.has(Word)) {
            RenderPreviewHistoricalTestPanel();
            return;
        }

        const ShouldHighlight = ShouldHighlightWordDiscovery(Word);
        FoundWords.add(Word);

        if (ShouldHighlight) {
            MarkWordForHighlight(Word);
        }

        RecomputePreviewHistoricalSandboxState();
        RenderPanel();
        QueuePanelLayoutUpdate();
        RenderPreviewHistoricalTestPanel();
    }

    function SimulatePreviewHistoricalTwoferSolve() {
        if (!EnterPreviewHistoricalTestMode()) {
            return;
        }

        const Twofer = GetPreviewHistoricalSelectedTwofer();
        if (!Twofer) {
            return;
        }

        MarkTwoferFound(Twofer.First, Twofer.Second);
        RecomputePreviewHistoricalSandboxState();
        RenderPanel();
        QueuePanelLayoutUpdate();
        RenderPreviewHistoricalTestPanel();
    }

    function UpdatePreviewHistoricalTestButton() {
        const Button = document.getElementById(PreviewHistoryTestButtonId);
        if (!Button) {
            return;
        }

        Button.textContent = PreviewHistoricalTestModeActive
            ? "History Test (ACTIVE)"
            : "History Test";
        Button.classList.toggle(
            "lbc-history-test-active",
            PreviewHistoricalTestModeActive
        );
        Button.title = PreviewHistoricalTestModeActive
            ? "Historical-word sandbox is active. Google Drive sync and LBC progress writes are paused."
            : "Open preview-only historical-word/twofer sandbox";

        /* Keep the Debug button anchored; the longer ACTIVE label grows left. */
        PositionPreviewDebugPane();
    }

    function RenderPreviewHistoricalTestPanel() {
        const Panel = document.getElementById(PreviewHistoryTestPanelId);
        if (!Panel) {
            return;
        }

        const AvailableTwofers =
            GetPreviewHistoricalAvailableTwofers();
        const HasTestableTwofer = AvailableTwofers.length > 0;
        const Select = Panel.querySelector("select[data-lbc-history-test-twofer]");
        if (Select) {
            const ExistingValue = PreviewHistoricalSelectedTwoferKey || "";
            Select.replaceChildren();

            for (const Twofer of AvailableTwofers) {
                const Option = document.createElement("option");
                Option.value = Twofer.Key;
                const Category = GetTwoferCategory(Twofer);
                Option.textContent = `${Twofer.First} -> ${Twofer.Second}  [${Category}]`;
                Select.appendChild(Option);
            }

            if (
                ExistingValue &&
                [...Select.options].some(Option => Option.value === ExistingValue)
            ) {
                Select.value = ExistingValue;
            } else if (Select.options.length) {
                Select.selectedIndex = 0;
                PreviewHistoricalSelectedTwoferKey = Select.value;
            } else {
                PreviewHistoricalSelectedTwoferKey = null;
            }

            Select.disabled = !HasTestableTwofer;
        }

        for (const Button of Panel.querySelectorAll("button")) {
            if (Button.dataset.lbcHistoryTestExit === "true") {
                Button.disabled = false;
                continue;
            }

            Button.disabled = !HasTestableTwofer;
        }

        const Status = Panel.querySelector(".lbc-history-test-status");
        const Twofer = GetPreviewHistoricalSelectedTwofer();

        if (!Status) {
            return;
        }

        if (!Twofer) {
            Status.textContent =
                "No twofers found today are available for safe testing. " +
                "Solve a twofer normally, then reopen History Test.";
            return;
        }

        const Category = GetTwoferCategory(Twofer);
        const Visibility = GetTwoferWordVisibility(Twofer, Category);
        const HintStats = CalculateTwoferHintStats();
        const DescribeWord = Word => {
            const Flags = [];
            if (PreviewHistoricalInjectedWords.has(Word)) {
                Flags.push("TEST historical");
            } else if (PreviewHistoricalBaseline?.PreviouslyFoundWordsForPuzzle.has(Word)) {
                Flags.push("real historical");
            }
            if (FoundWords.has(Word)) {
                Flags.push("found today/in sandbox");
            }
            if (!Flags.length) {
                Flags.push("unknown");
            }
            return `${Word}: ${Flags.join(", ")}`;
        };

        Status.textContent = [
            `Mode: ${PreviewHistoricalTestModeActive ? "ACTIVE - persistence/sync paused" : "inactive"}`,
            DescribeWord(Twofer.First),
            DescribeWord(Twofer.Second),
            `Twofer category: ${Category}`,
            `Visible words: first=${Visibility.FirstVisible}, second=${Visibility.SecondVisible}`,
            `Independent-solution indicator: ${HintStats.HasUnconnectedFoundSolution}`,
            `Exact pair solved in sandbox: ${FoundTwofers.has(Twofer.Key)}`,
            `Word highlights active: first=${RecentWordHighlights.has(Twofer.First)}, second=${RecentWordHighlights.has(Twofer.Second)}`
        ].join("\n");
    }

    function OpenPreviewHistoricalTestPanel() {
        if (!EnterPreviewHistoricalTestMode()) {
            return;
        }

        let Overlay = document.getElementById(PreviewHistoryTestOverlayId);
        if (Overlay) {
            RenderPreviewHistoricalTestPanel();
            return;
        }

        Overlay = document.createElement("div");
        Overlay.id = PreviewHistoryTestOverlayId;

        const Panel = document.createElement("section");
        Panel.id = PreviewHistoryTestPanelId;

        const Heading = document.createElement("h2");
        Heading.textContent = "PREVIEW Historical Word Sandbox";

        const Warning = document.createElement("div");
        Warning.className = "lbc-history-test-warning";
        Warning.textContent =
            "Safe LBC sandbox: progress writes and Google Drive sync are paused. " +
            "This does NOT replace NYT's own internal game state, so use these simulation buttons rather than typing into NYT if you want zero effect on today's real NYT progress.";

        const SelectLabel = document.createElement("label");
        SelectLabel.textContent = "Current-board twofer to test:";
        const Select = document.createElement("select");
        Select.dataset.lbcHistoryTestTwofer = "true";
        Select.addEventListener("change", () => {
            PreviewHistoricalSelectedTwoferKey = Select.value;
            RestorePreviewHistoricalBaseline({ KeepActive: true });
            RecomputePreviewHistoricalSandboxState();
            RenderPanel();
            RenderPreviewHistoricalTestPanel();
        });
        SelectLabel.appendChild(Select);

        const Grid = document.createElement("div");
        Grid.className = "lbc-history-test-grid";

        const HistoricalBlock = document.createElement("div");
        HistoricalBlock.className = "lbc-history-test-block";
        HistoricalBlock.innerHTML = "<strong>Pretend these were found on an earlier day</strong>";
        const HistoricalActions = document.createElement("div");
        HistoricalActions.className = "lbc-history-test-actions";

        for (const [Label, Mode] of [
            ["First only", "First"],
            ["Second only", "Second"],
            ["Both", "Both"],
            ["Neither", "Neither"]
        ]) {
            const Button = document.createElement("button");
            Button.type = "button";
            Button.textContent = Label;
            Button.addEventListener("click", () => SetPreviewHistoricalInjection(Mode));
            HistoricalActions.appendChild(Button);
        }
        HistoricalBlock.appendChild(HistoricalActions);

        const DiscoveryBlock = document.createElement("div");
        DiscoveryBlock.className = "lbc-history-test-block";
        DiscoveryBlock.innerHTML = "<strong>Simulate today's discoveries</strong>";
        const DiscoveryActions = document.createElement("div");
        DiscoveryActions.className = "lbc-history-test-actions";

        const FindFirst = document.createElement("button");
        FindFirst.type = "button";
        FindFirst.textContent = "Find first today";
        FindFirst.addEventListener(
            "click",
            () => SimulatePreviewHistoricalWordDiscovery("First")
        );

        const FindSecond = document.createElement("button");
        FindSecond.type = "button";
        FindSecond.textContent = "Find second today";
        FindSecond.addEventListener(
            "click",
            () => SimulatePreviewHistoricalWordDiscovery("Second")
        );

        const SolvePair = document.createElement("button");
        SolvePair.type = "button";
        SolvePair.textContent = "Solve exact pair";
        SolvePair.addEventListener("click", SimulatePreviewHistoricalTwoferSolve);

        DiscoveryActions.append(
            FindFirst,
            FindSecond,
            SolvePair
        );
        DiscoveryBlock.appendChild(DiscoveryActions);

        Grid.append(
            HistoricalBlock,
            DiscoveryBlock
        );

        const Status = document.createElement("pre");
        Status.className = "lbc-history-test-status";

        const Footer = document.createElement("div");
        Footer.className = "lbc-history-test-actions";

        const Reset = document.createElement("button");
        Reset.type = "button";
        Reset.textContent = "Reset sandbox";
        Reset.addEventListener("click", () => {
            RestorePreviewHistoricalBaseline({ KeepActive: true });
            RecomputePreviewHistoricalSandboxState();
            RenderPanel();
            RenderPreviewHistoricalTestPanel();
        });

        const Close = document.createElement("button");
        Close.type = "button";
        Close.textContent = "Hide panel (keep sandbox active)";
        Close.addEventListener("click", () => Overlay.remove());

        const Exit = document.createElement("button");
        Exit.type = "button";
        Exit.dataset.lbcHistoryTestExit = "true";
        Exit.textContent = "EXIT TEST MODE + restore real state";
        Exit.addEventListener("click", () => {
            Overlay.remove();
            ExitPreviewHistoricalTestMode();
        });

        Footer.append(
            Reset,
            Close,
            Exit
        );

        Panel.append(
            Heading,
            Warning,
            SelectLabel,
            Grid,
            Status,
            Footer
        );
        Overlay.appendChild(Panel);
        document.body.appendChild(Overlay);

        Overlay.addEventListener("click", Event => {
            if (Event.target === Overlay) {
                Overlay.remove();
            }
        });

        RenderPreviewHistoricalTestPanel();
    }

    function CreatePreviewHistoricalTestControls() {
        if (
            UserscriptBuildChannel !== "preview" ||
            document.getElementById(PreviewHistoryTestButtonId)
        ) {
            return;
        }

        const Button = document.createElement("button");
        Button.id = PreviewHistoryTestButtonId;
        Button.type = "button";
        Button.addEventListener("click", OpenPreviewHistoricalTestPanel);
        document.body.appendChild(Button);
        UpdatePreviewHistoricalTestButton();
        PositionPreviewDebugPane();
    }

    function InstallPreviewHistoricalSandboxGuards() {
        const OriginalScheduleCloudSync = ScheduleCloudSync;
        ScheduleCloudSync = function (...Args) {
            if (PreviewHistoricalTestModeActive) {
                return;
            }
            return OriginalScheduleCloudSync(...Args);
        };

        const OriginalSyncWithGoogleDrive = SyncWithGoogleDrive;
        SyncWithGoogleDrive = async function (...Args) {
            if (PreviewHistoricalTestModeActive) {
                console.info(
                    "[Letter Boxed Cubed][preview] Google Drive sync suppressed by History Test mode."
                );
                return;
            }
            return OriginalSyncWithGoogleDrive(...Args);
        };

        const OriginalSaveFoundWords = SaveFoundWords;
        SaveFoundWords = function (...Args) {
            if (PreviewHistoricalTestModeActive) {
                RecomputePreviewHistoricalSandboxState();
                return;
            }
            return OriginalSaveFoundWords(...Args);
        };

        const OriginalSaveFoundTwofers = SaveFoundTwofers;
        SaveFoundTwofers = function (...Args) {
            if (PreviewHistoricalTestModeActive) {
                return;
            }
            return OriginalSaveFoundTwofers(...Args);
        };

        const OriginalSaveGlobalWordHistory = SaveGlobalWordHistory;
        SaveGlobalWordHistory = function (...Args) {
            if (PreviewHistoricalTestModeActive) {
                return;
            }
            return OriginalSaveGlobalWordHistory(...Args);
        };
    }

    function CreatePreviewDebugPane() {
        if (
            UserscriptBuildChannel !== "preview" ||
            document.getElementById(PreviewDebugPanelId)
        ) {
            return;
        }

        EnsurePreviewDebugStyles();

        const ToggleButton = document.createElement("button");
        ToggleButton.id = PreviewDebugToggleButtonId;
        ToggleButton.type = "button";
        ToggleButton.textContent = "Show Debug Pane";
        ToggleButton.setAttribute(
            "aria-controls",
            PreviewDebugPanelId
        );
        ToggleButton.setAttribute("aria-expanded", "false");

        const DebugPanel = document.createElement("aside");
        DebugPanel.id = PreviewDebugPanelId;
        DebugPanel.setAttribute(
            "aria-label",
            "Letter Boxed Cubed Preview DOM debugger"
        );
        DebugPanel.hidden = !PreviewDebugPaneVisible;
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
            );
            ToggleButton.textContent = PreviewDebugPaneVisible
                ? "Hide Debug Pane"
                : "Show Debug Pane";
            ToggleButton.setAttribute(
                "aria-expanded",
                String(PreviewDebugPaneVisible)
            );

            if (PreviewDebugPaneVisible) {
                RenderPreviewDebugPane();
            }

            PositionPreviewDebugPane();
        });

        const Header = document.createElement("div");
        Header.className = "lbc-debug-title";
        Header.innerHTML = "<span>PREVIEW DOM DEBUG</span><span>TI + GB</span>";

        const Tools = document.createElement("div");
        Tools.className = "lbc-debug-tools";

        const Refresh = document.createElement("button");
        Refresh.type = "button";
        Refresh.textContent = "Refresh";
        Refresh.addEventListener("click", RenderPreviewDebugPane);

        const Reset = document.createElement("button");
        Reset.type = "button";
        Reset.textContent = "Reset visibility";
        Reset.addEventListener("click", ResetPreviewDebugVisibility);

        const Clear = document.createElement("button");
        Clear.type = "button";
        Clear.textContent = "Clear mutations";
        Clear.addEventListener("click", () => {
            PreviewDebugMutationLog.length = 0;
            RenderPreviewDebugPane();
        });

        Tools.append(
            Refresh,
            Reset,
            Clear
        );

        const TiTitle = document.createElement("div");
        TiTitle.className = "lbc-debug-section-title";
        TiTitle.textContent = "TI DOM";
        const TiTree = document.createElement("div");
        TiTree.dataset.lbcDebugTree = "ti";

        const GbTitle = document.createElement("div");
        GbTitle.className = "lbc-debug-section-title";
        GbTitle.textContent = "GB DOM";
        const GbTree = document.createElement("div");
        GbTree.dataset.lbcDebugTree = "gb";

        const MutationTitle = document.createElement("div");
        MutationTitle.className = "lbc-debug-section-title";
        MutationTitle.textContent = "Mutation log (newest first)";
        const MutationLog = document.createElement("pre");
        MutationLog.className = "lbc-debug-log";

        const HtmlTitle = document.createElement("div");
        HtmlTitle.className = "lbc-debug-section-title";
        HtmlTitle.textContent = "Selected outerHTML";
        const Html = document.createElement("pre");
        Html.className = "lbc-debug-html";
        Html.textContent = "Click a DOM row to inspect it.";

        DebugPanel.append(
            Header,
            Tools,
            TiTitle,
            TiTree,
            GbTitle,
            GbTree,
            MutationTitle,
            MutationLog,
            HtmlTitle,
            Html
        );

        document.body.append(
            ToggleButton,
            DebugPanel
        );
        StartPreviewDebugObserver();
        RenderPreviewDebugPane();

        CreatePreviewHistoricalTestControls();
        StartPreviewChromeObserver();

        window.addEventListener(
            "resize",
            PositionPreviewDebugPane
        );
    }

    InstallPreviewHistoricalSandboxGuards();

