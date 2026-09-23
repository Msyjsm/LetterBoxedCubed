/*
    PREVIEW-ONLY RUNTIME
    This file is injected into LetterBoxedCubed.preview.user.js by
    tools/build_preview.py. It is intentionally absent from the production
    userscript distributed from main.
*/

    const PreviewDebugPanelId = "lb-cubed-preview-debug";
    const PreviewDebugStyleId = "lb-cubed-preview-debug-styles";
    const PreviewDebugToggleButtonId = "lb-cubed-preview-debug-toggle";
    const PreviewVersionLabelId = "lb-cubed-preview-version";

    let PreviewDebugObserver = null;
    let PreviewDebugRenderTimer = null;
    let PreviewDebugNextElementId = 1;
    let PreviewDebugPaneVisible = false;
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
            Target.closest(`#${PreviewDebugPanelId}`)
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
                z-index: 99999;
                color: rgba(92, 92, 92, 0.78);
                font: 10px/1.2 Consolas, "Courier New", monospace;
                white-space: nowrap;
                pointer-events: none;
                user-select: none;
            }

            #${PreviewDebugToggleButtonId} {
                position: absolute;
                z-index: 100001;
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

            #${PreviewDebugToggleButtonId}:hover {
                background: #303038;
            }

            #${PreviewDebugPanelId} {
                position: fixed;
                z-index: 100000;
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

        window.addEventListener(
            "resize",
            PositionPreviewDebugPane
        );
    }

