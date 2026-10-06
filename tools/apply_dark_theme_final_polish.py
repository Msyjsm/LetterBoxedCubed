from pathlib import Path

SOURCE = Path("LetterBoxedCubed.user.js")
PREVIEW = Path("tools/preview_runtime.js")
TESTS = Path("tests/final-polish-tests.js")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


source = SOURCE.read_text(encoding="utf-8")
source = replace_once(
    source,
    "// @version      1.13.1-beta.11",
    "// @version      1.13.1-beta.12",
    "version"
)

source = replace_once(
    source,
    '''            Proxy = document.createElement("div");
            Proxy.className =
                "lb-message-box success-message lb-cubed-valid-feedback-proxy";
            Proxy.replaceChildren(
                ...[...Source.childNodes].map(Node => Node.cloneNode(true))
            );
            GameContainer.appendChild(Proxy);''',
    '''            Proxy = document.createElement("div");
            Proxy.className = "lb-cubed-valid-feedback-proxy";

            /*
                Do not inherit NYT's lb-message-box/success-message classes on
                the relocated copy. Those classes own a transient animation
                lifecycle and can leave a cloned node permanently transparent
                or clipped, especially after dark-theme overrides. Cubed only
                needs the authoritative visible message text; the hidden native
                source still determines creation/removal timing.
            */
            Proxy.textContent = String(Source.textContent || "").trim();
            GameContainer.appendChild(Proxy);''',
    "self-owned valid feedback proxy"
)

source = replace_once(
    source,
    '''            .lb-cubed-valid-feedback-proxy {
                position: absolute !important;
                right: auto !important;
                bottom: auto !important;
                margin: 0 !important;
                transform: none !important;
                visibility: visible !important;
                display: block !important;
                z-index: 60 !important;
                pointer-events: none !important;
            }

            /*
                Cubed mirrors NYT's valid-word toast into an independently
                positioned proxy. In dark mode that proxy must not inherit the
                native success-message animation's transient opacity/clip state
                or child colors. The native source still owns the lifecycle;
                the proxy only needs to remain visibly styled while that source
                exists.
            */
            html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy {
                opacity: 1 !important;
                visibility: visible !important;
                clip-path: none !important;
                filter: none !important;
                animation: none !important;
                transition: none !important;
                background:
                    color-mix(
                        in srgb,
                        var(--lb-cubed-lb-text) 10%,
                        var(--lb-cubed-lb-surface)
                    ) !important;
                color: var(--lb-cubed-lb-text) !important;
                border: 1px solid
                    color-mix(
                        in srgb,
                        var(--lb-cubed-lb-border) 75%,
                        transparent
                    ) !important;
            }

            html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy,
            html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy * {
                color: var(--lb-cubed-lb-text) !important;
                fill: currentColor !important;
                text-shadow: none !important;
            }''',
    '''            /*
                Cubed owns the relocated valid-word toast completely. Keeping
                NYT's transient success-message classes on the clone proved
                fragile because their animation lifecycle can leave the clone
                clipped/transparent even after the native source becomes
                visible. Use a small theme-aware Cubed surface instead while
                retaining the hidden NYT node only as the lifecycle source.
            */
            .lb-cubed-valid-feedback-proxy {
                position: absolute !important;
                right: auto !important;
                bottom: auto !important;
                min-width: 72px;
                max-width: min(260px, calc(100vw - 24px));
                margin: 0 !important;
                padding: 5px 10px;
                transform: none !important;
                visibility: visible !important;
                display: block !important;
                opacity: 1 !important;
                clip-path: none !important;
                filter: none !important;
                z-index: 60 !important;
                pointer-events: none !important;
                animation: none !important;
                transition: none !important;
                background:
                    color-mix(
                        in srgb,
                        var(--lb-cubed-lb-text, #111111) 10%,
                        var(--lb-cubed-lb-surface, #FFFFFF)
                    ) !important;
                color: var(--lb-cubed-lb-text, #111111) !important;
                border: 1px solid
                    color-mix(
                        in srgb,
                        var(--lb-cubed-lb-border, #000000) 75%,
                        transparent
                    ) !important;
                border-radius: 4px;
                box-shadow: 0 2px 7px rgba(0, 0, 0, 0.16);
                font: 700 12px/1.25 Arial, Helvetica, sans-serif;
                text-align: center;
                text-shadow: none !important;
                white-space: nowrap;
            }''',
    "self-owned valid feedback CSS"
)

source = replace_once(
    source,
    '''            /*
                NYT's visible entry rule is not reliably the text field's own
                border. Guarantee the themed underline without changing layout
                by painting it as an inset edge on the existing wrapper. This
                also survives the dark-mode page reload used for board themes.
            */
            html.lb-cubed-native-theme .lb-text-field-wrapper {
                box-shadow:
                    inset 0 -2px 0 var(--lb-cubed-lb-text) !important;
            }''',
    '''            /*
                NYT's visible entry rule is not reliably the text field's own
                border. Paint a centered theme-aware rule on the existing
                wrapper without changing layout. Match the board/surrounding
                letter footprint rather than spanning the whole TI column.
            */
            html.lb-cubed-native-theme .lb-text-field-wrapper {
                box-shadow: none !important;
                background-image:
                    linear-gradient(
                        var(--lb-cubed-lb-text),
                        var(--lb-cubed-lb-text)
                    ) !important;
                background-repeat: no-repeat !important;
                background-position: center bottom !important;
                background-size:
                    min(var(--lb-cubed-square-width, 100%), 100%) 2px !important;
            }''',
    "entry underline width"
)

SOURCE.write_text(source, encoding="utf-8")

preview = PREVIEW.read_text(encoding="utf-8")
preview = replace_once(
    preview,
    "    let PreviewDebugRenderTimer = null;\n",
    "    let PreviewDebugRenderTimer = null;\n    let PreviewVersionContrastObserver = null;\n",
    "preview contrast observer state"
)
preview = replace_once(
    preview,
    "                color: rgba(92, 92, 92, 0.78);",
    "                color: var(--lb-cubed-preview-version-color, rgba(92, 92, 92, 0.78));",
    "preview version CSS variable"
)
preview = replace_once(
    preview,
    '''    function CreatePreviewVersionLabel() {''',
    '''    function UpdatePreviewVersionLabelContrast() {
        const Label = document.getElementById(PreviewVersionLabelId);
        if (!Label) {
            return;
        }

        const Raw = getComputedStyle(document.documentElement)
            .getPropertyValue("--lb-cubed-lb-page-bg")
            .trim();
        const Hex = /^#([0-9a-f]{6})$/i.exec(Raw);

        if (!Hex) {
            Label.style.removeProperty("--lb-cubed-preview-version-color");
            return;
        }

        const Value = Hex[1];
        const Channels = [0, 2, 4].map(Index =>
            parseInt(Value.slice(Index, Index + 2), 16) / 255
        );
        const Linear = Channels.map(Channel =>
            Channel <= 0.04045
                ? Channel / 12.92
                : Math.pow((Channel + 0.055) / 1.055, 2.4)
        );
        const Luminance =
            0.2126 * Linear[0] +
            0.7152 * Linear[1] +
            0.0722 * Linear[2];

        Label.style.setProperty(
            "--lb-cubed-preview-version-color",
            Luminance < 0.22
                ? "rgba(210, 210, 210, 0.74)"
                : "rgba(92, 92, 92, 0.78)"
        );
    }

    function CreatePreviewVersionLabel() {''',
    "preview contrast helper"
)
preview = replace_once(
    preview,
    '''        Label.textContent = GetRunningUserscriptVersion();
        document.body.appendChild(Label);
        PositionPreviewVersionLabel();''',
    '''        Label.textContent = GetRunningUserscriptVersion();
        document.body.appendChild(Label);
        UpdatePreviewVersionLabelContrast();

        PreviewVersionContrastObserver?.disconnect();
        PreviewVersionContrastObserver = new MutationObserver(
            UpdatePreviewVersionLabelContrast
        );
        PreviewVersionContrastObserver.observe(
            document.documentElement,
            {
                attributes: true,
                attributeFilter: ["style", "class"]
            }
        );

        PositionPreviewVersionLabel();''',
    "preview contrast observer hookup"
)
PREVIEW.write_text(preview, encoding="utf-8")

tests = TESTS.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    "assert(source.includes('// @version      1.13.1-beta.11'), 'beta.11 version missing');",
    "assert(source.includes('// @version      1.13.1-beta.12'), 'beta.12 version missing');",
    "test version"
)
tests = replace_once(
    tests,
    "assert(source.includes('inset 0 -2px 0 var(--lb-cubed-lb-text)'), 'dark text-entry underline guarantee missing');",
    "assert(source.includes('min(var(--lb-cubed-square-width, 100%), 100%) 2px'), 'board-width dark text-entry underline missing');",
    "underline regression test"
)
tests = replace_once(
    tests,
    "assert(source.includes('html.lb-cubed-native-theme .lb-cubed-valid-feedback-proxy'), 'dark valid-word toast theme override missing');",
    "assert(source.includes('Proxy.className = \"lb-cubed-valid-feedback-proxy\"'), 'self-owned valid-word toast proxy missing');\nassert(source.includes('Proxy.textContent = String(Source.textContent || \"\").trim()'), 'valid-word toast still depends on NYT child markup');",
    "toast regression tests"
)
tests = replace_once(
    tests,
    "assert(preview.includes('!PreviewDebugPaneVisible'), 'hidden debug pane render guard missing');\n",
    "assert(preview.includes('!PreviewDebugPaneVisible'), 'hidden debug pane render guard missing');\nassert(preview.includes('UpdatePreviewVersionLabelContrast'), 'preview version contrast helper missing');\nassert(preview.includes('Luminance < 0.22'), 'preview version darkness threshold missing');\n",
    "preview contrast tests"
)
TESTS.write_text(tests, encoding="utf-8")
