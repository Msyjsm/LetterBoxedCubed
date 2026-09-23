from pathlib import Path
import re


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


source_path = Path("LetterBoxedCubed.user.js")
source = source_path.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Final release version + exact temporary logo supplied by Nathan.
# The PNG bytes are embedded as a data URL so the userscript is self-contained.
# ---------------------------------------------------------------------------
source = replace_once(
    source,
    "// @version      1.12.0-beta.20",
    "// @version      1.12.0",
    "release version",
)
source = replace_once(
    source,
    "// @grant        GM_info\n",
    "",
    "remove production-only-unused GM_info grant",
)

logo_base64 = "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"
logo_data_url = f"data:image/png;base64,{logo_base64}"

logo_constant = f'''    const LogoPngDataUrl =\n        "{logo_data_url}";\n'''
source = replace_once(
    source,
    '    const PanelId = "lb-cubed-panel";\n',
    logo_constant + '    const PanelId = "lb-cubed-panel";\n',
    "logo constant",
)

# ---------------------------------------------------------------------------
# Move preview-only debugger/version/bootstrap implementation out of the
# production userscript. Production keeps tiny no-op hooks so preview builds
# can inject the full module without littering ordinary releases with it.
# ---------------------------------------------------------------------------
preview_constants = '''    const PreviewDebugPanelId = "lb-cubed-preview-debug";\n    const PreviewDebugStyleId = "lb-cubed-preview-debug-styles";\n    const PreviewDebugToggleButtonId = "lb-cubed-preview-debug-toggle";\n    const PreviewVersionLabelId = "lb-cubed-preview-version";\n'''
source = replace_once(source, preview_constants, "", "preview constants")

preview_vars = '''    let PreviewDebugObserver = null;\n    let PreviewDebugRenderTimer = null;\n    let PreviewDebugNextElementId = 1;\n    let PreviewDebugPaneVisible = false;\n    const PreviewDebugElementIds = new WeakMap();\n    const PreviewDebugElementsById = new Map();\n    const PreviewDebugOriginalDisplay = new WeakMap();\n    const PreviewDebugOverriddenElements = new Set();\n    const PreviewDebugMutationLog = [];\n'''
source = replace_once(source, preview_vars, "", "preview state")

bootstrap_start = source.index("    const BootstrapDiagnostics = [];\n")
bootstrap_end_marker = '    RecordBootstrapDiagnostic("userscript-channel-active");\n'
bootstrap_end = source.index(bootstrap_end_marker, bootstrap_start) + len(bootstrap_end_marker)
bootstrap_block = source[bootstrap_start:bootstrap_end]

preview_start_marker = '''    // -------------------------------------------------------------------------\n    // Preview-only DOM inspector\n    // -------------------------------------------------------------------------\n'''
preview_end_marker = '''    // -------------------------------------------------------------------------\n    // Layout\n    // -------------------------------------------------------------------------\n'''
preview_start = source.index(preview_start_marker)
preview_end = source.index(preview_end_marker, preview_start)
preview_module = source[preview_start:preview_end]

preview_hooks = '''    // Preview-only implementation is injected by tools/build_preview.py.\n    // Production releases contain only these inert hooks.\n    function RecordBootstrapDiagnostic() {}\n    function CreatePreviewDebugPane() {}\n    function CreatePreviewVersionLabel() {}\n    function PositionPreviewDebugPane() {}\n    function PositionPreviewVersionLabel() {}\n    function IsPreviewDebugTypingContext() { return false; }\n\n    // PREVIEW_RUNTIME_INJECTION_POINT\n'''
source = source[:bootstrap_start] + preview_hooks + source[bootstrap_end:]

# The preview module moved after the bootstrap removal, so find it again.
preview_start = source.index(preview_start_marker)
preview_end = source.index(preview_end_marker, preview_start)
source = source[:preview_start] + source[preview_end:]

runtime_text = '''/*\n    PREVIEW-ONLY RUNTIME\n    This file is injected into LetterBoxedCubed.preview.user.js by\n    tools/build_preview.py. It is intentionally absent from the production\n    userscript distributed from main.\n*/\n\n'''
runtime_text += preview_constants + "\n" + preview_vars + "\n" + bootstrap_block + "\n"
runtime_text += '''    function IsPreviewDebugTypingContext(Target) {\n        return Boolean(\n            Target instanceof Element &&\n            Target.closest(`#${PreviewDebugPanelId}`)\n        );\n    }\n\n'''
runtime_text += preview_module
Path("tools/preview_runtime.js").write_text(runtime_text, encoding="utf-8")

source = replace_once(
    source,
    '''        if (Target.closest(\n            `#${SettingsMenuId}, #${HistoryOverlayId}, #${PreviewDebugPanelId}`\n        )) {\n            return true;\n        }\n''',
    '''        if (\n            Target.closest(`#${SettingsMenuId}, #${HistoryOverlayId}`) ||\n            IsPreviewDebugTypingContext(Target)\n        ) {\n            return true;\n        }\n''',
    "preview keyboard context hook",
)

# ---------------------------------------------------------------------------
# Replace the bordered pixel-size placeholder with the actual PNG logo.
# ---------------------------------------------------------------------------
source = replace_once(
    source,
    '''        const LogoPlaceholder = document.createElement("div");\n        LogoPlaceholder.className = "lb-cubed-logo-placeholder";\n        LogoPlaceholder.setAttribute("aria-label", "Letter Boxed Cubed logo placeholder");\n\n        const LogoSize = document.createElement("span");\n        LogoSize.className = "lb-cubed-logo-placeholder-size";\n        LogoPlaceholder.appendChild(LogoSize);\n''',
    '''        const Logo = document.createElement("img");\n        Logo.className = "lb-cubed-logo";\n        Logo.src = LogoPngDataUrl;\n        Logo.alt = "Letter Boxed Cubed";\n        Logo.draggable = false;\n''',
    "render real logo",
)
source = replace_once(
    source,
    "        TitleRow.append(LogoPlaceholder, TitleMeta);\n",
    "        TitleRow.append(Logo, TitleMeta);\n",
    "title-row logo",
)
source = replace_once(
    source,
    "        UpdateLogoPlaceholderSize(Header, LogoPlaceholder, HeaderActions, LogoSize);\n",
    "        UpdateLogoSize(Header, Logo, HeaderActions);\n",
    "initial logo sizing call",
)

old_logo_function = '''    function UpdateLogoPlaceholderSize(\n        Header = document.querySelector(".lb-cubed-header"),\n        Placeholder = document.querySelector(".lb-cubed-logo-placeholder"),\n        HeaderActions = document.querySelector(".lb-cubed-header-actions"),\n        SizeText = document.querySelector(".lb-cubed-logo-placeholder-size")\n    ) {\n        if (!Header || !Placeholder || !HeaderActions || !SizeText) {\n            return;\n        }\n        if (!Header.isConnected || !Placeholder.isConnected) {\n            return;\n        }\n\n        Placeholder.classList.add("lb-cubed-logo-placeholder-measuring");\n        const HeaderHeight = Math.ceil(Header.getBoundingClientRect().height);\n        const ActionHeight = Math.ceil(HeaderActions.getBoundingClientRect().height);\n        const Side = Math.max(20, Math.min(96, Math.max(HeaderHeight, ActionHeight)));\n        Placeholder.classList.remove("lb-cubed-logo-placeholder-measuring");\n\n        Placeholder.style.width = `${Side}px`;\n        Placeholder.style.height = `${Side}px`;\n        SizeText.textContent = `${Side}px`;\n    }\n'''
new_logo_function = '''    function UpdateLogoSize(\n        Header = document.querySelector(".lb-cubed-header"),\n        Logo = document.querySelector(".lb-cubed-logo"),\n        HeaderActions = document.querySelector(".lb-cubed-header-actions")\n    ) {\n        if (!Header || !Logo || !HeaderActions) {\n            return;\n        }\n        if (!Header.isConnected || !Logo.isConnected) {\n            return;\n        }\n\n        /*\n            Temporarily remove the logo from header sizing so its previous size\n            cannot feed back into the next measurement. The image then takes\n            the natural height required by the surrounding header content,\n            clamped to the same practical 20-96px range used by the prototype.\n        */\n        Logo.classList.add("lb-cubed-logo-measuring");\n        const HeaderHeight = Math.ceil(Header.getBoundingClientRect().height);\n        const ActionHeight = Math.ceil(HeaderActions.getBoundingClientRect().height);\n        const Side = Math.max(20, Math.min(96, Math.max(HeaderHeight, ActionHeight)));\n        Logo.classList.remove("lb-cubed-logo-measuring");\n\n        Logo.style.width = `${Side}px`;\n        Logo.style.height = `${Side}px`;\n    }\n'''
source = replace_once(source, old_logo_function, new_logo_function, "logo sizing function")
source = source.replace("UpdateLogoPlaceholderSize();", "UpdateLogoSize();")

source = replace_once(
    source,
    '''            .lb-cubed-logo-placeholder-measuring {\n                position: absolute !important;\n                visibility: hidden !important;\n                width: 0 !important;\n                height: 0 !important;\n                pointer-events: none !important;\n            }\n''',
    '''            .lb-cubed-logo-measuring {\n                position: absolute !important;\n                visibility: hidden !important;\n                width: 0 !important;\n                height: 0 !important;\n                pointer-events: none !important;\n            }\n''',
    "logo measuring CSS",
)
source = replace_once(
    source,
    '''            .lb-cubed-logo-placeholder {\n                flex: 0 0 auto;\n                display: grid;\n                place-items: center;\n                width: 28px;\n                height: 28px;\n                border: 1px solid rgba(76, 34, 34, 0.78);\n                background: rgba(255, 255, 255, 0.08);\n                color: rgba(48, 24, 24, 0.78);\n                font-family: Consolas, "Courier New", monospace;\n                font-size: 9px;\n                font-weight: 700;\n                line-height: 1;\n                white-space: nowrap;\n            }\n\n            .lb-cubed-logo-placeholder-size {\n                pointer-events: none;\n            }\n''',
    '''            .lb-cubed-logo {\n                flex: 0 0 auto;\n                display: block;\n                width: 28px;\n                height: 28px;\n                max-width: 96px;\n                max-height: 96px;\n                border: 0;\n                background: transparent;\n                object-fit: contain;\n                user-select: none;\n            }\n''',
    "real logo CSS",
)

# Source-level release assertions.
for forbidden in [
    'lb-cubed-logo-placeholder',
    'PreviewDebugObserver',
    'PreviewDebugMutationLog',
    'lb-cubed-preview-debug',
    'LetterBoxedCubed_PreviewBootstrapTrace',
]:
    if forbidden in source:
        raise RuntimeError(f"production source still contains preview/test implementation: {forbidden}")

if "// @version      1.12.0\n" not in source:
    raise RuntimeError("release version assertion failed")
if "data:image/png;base64," not in source or "lb-cubed-logo" not in source:
    raise RuntimeError("logo embedding assertion failed")

source_path.write_text(source, encoding="utf-8")

# ---------------------------------------------------------------------------
# Teach preview builder to inject the separated runtime and preview-only grant.
# ---------------------------------------------------------------------------
build_path = Path("tools/build_preview.py")
build = build_path.read_text(encoding="utf-8")
build = replace_once(
    build,
    'HEADER_END = "// ==/UserScript=="\n',
    'HEADER_END = "// ==/UserScript=="\nPREVIEW_RUNTIME_MARKER = "    // PREVIEW_RUNTIME_INJECTION_POINT"\n',
    "preview runtime marker constant",
)
build = replace_once(
    build,
    '    parser.add_argument("--build-number", required=True)\n',
    '    parser.add_argument("--build-number", required=True)\n    parser.add_argument(\n        "--preview-runtime",\n        type=Path,\n        default=Path("tools/preview_runtime.js"),\n        help="Preview-only JS fragment injected at PREVIEW_RUNTIME_INJECTION_POINT.",\n    )\n',
    "preview runtime argument",
)

helper_anchor = '''def remove_meta(text: str, key: str) -> str:\n    return re.sub(\n        rf"^// @{re.escape(key)}\\s+.*\\n?",\n        "",\n        text,\n        flags=re.MULTILINE,\n    )\n\n\n'''
helper_code = '''def ensure_grant(text: str, grant: str) -> str:\n    if re.search(\n        rf"^// @grant\\s+{re.escape(grant)}\\s*$",\n        text,\n        flags=re.MULTILINE,\n    ):\n        return text\n\n    if HEADER_END not in text:\n        raise ValueError("Userscript metadata block is missing its closing marker.")\n\n    return text.replace(\n        HEADER_END,\n        f"// @grant        {grant}\\n{HEADER_END}",\n        1,\n    )\n\n\ndef inject_preview_runtime(text: str, runtime_path: Path) -> str:\n    if text.count(PREVIEW_RUNTIME_MARKER) != 1:\n        raise ValueError(\n            "Canonical source must contain exactly one PREVIEW_RUNTIME_INJECTION_POINT."\n        )\n\n    runtime = runtime_path.read_text(encoding="utf-8").rstrip()\n    return text.replace(\n        PREVIEW_RUNTIME_MARKER,\n        PREVIEW_RUNTIME_MARKER + "\\n\\n" + runtime,\n        1,\n    )\n\n\n'''
build = replace_once(build, helper_anchor, helper_anchor + helper_code, "preview helper functions")

build = replace_once(
    build,
    '''    preview_text = add_preview_metadata(\n        source_text,\n        preview_url=args.preview_url,\n        build_number=args.build_number,\n    )\n\n    if args.preview_hash:\n''',
    '''    preview_text = add_preview_metadata(\n        source_text,\n        preview_url=args.preview_url,\n        build_number=args.build_number,\n    )\n    preview_text = ensure_grant(preview_text, "GM_info")\n    preview_text = inject_preview_runtime(\n        preview_text,\n        args.preview_runtime,\n    )\n\n    if args.preview_hash:\n''',
    "inject preview-only runtime",
)
build_path.write_text(build, encoding="utf-8")

# ---------------------------------------------------------------------------
# Release notes / preview docs.
# ---------------------------------------------------------------------------
changelog_path = Path("CHANGELOG.md")
changelog = changelog_path.read_text(encoding="utf-8")
changelog = replace_once(
    changelog,
    "# Changelog\n\n## 1.12.0-beta.20",
    '''# Changelog\n\n## 1.12.0\n- Released the completed v1.12 QoL/layout bundle after the beta.1-beta.20 preview cycle.\n- Replaced the bordered pixel-size logo prototype with Nathan's temporary cube PNG. The exact image is embedded in the userscript and scales with the natural LBC header height while preserving its square aspect ratio.\n- Moved the preview version label, TI/GB DOM debugger, and bootstrap diagnostics out of the production userscript into `tools/preview_runtime.js`. `tools/build_preview.py` now injects that module (and its `GM_info` grant) only into preview builds, so official releases do not ship the debugger implementation or UI.\n\n## 1.12.0-beta.20''',
    "final changelog entry",
)
changelog_path.write_text(changelog, encoding="utf-8")

docs_path = Path("docs/PREVIEW_TESTING.md")
docs = docs_path.read_text(encoding="utf-8")
docs = replace_once(
    docs,
    "The `feature/qol-4-10-12-13-14` preview bundles issues #4, #5, #10, #12, #13, #14, #16, #17, #18, and #19. The current source is `1.12.0-beta.20`.",
    "The `feature/qol-4-10-12-13-14` preview bundles issues #4, #5, #10, #12, #13, #14, #16, #17, #18, and #19. The current source is `1.12.0`.",
    "preview docs release version",
)
docs = replace_once(
    docs,
    "- The temporary square logo placeholder must no longer collapse to 0x0 for one animation frame when a word is accepted. Its size measurement is synchronous and should not cause the visible LBC blink seen in beta.4. Preview builds show the exact `GM_info.script.version` in gray just above LBC, left-aligned with the logo; that label scrolls with LBC. Drive status and the puzzle date form two lines beside the logo.",
    "- Nathan's temporary cube PNG is the LBC header logo. It should preserve its square aspect ratio, scale synchronously with the natural header height, and never collapse to 0x0 during gameplay. Preview builds show the exact `GM_info.script.version` in gray just above LBC, left-aligned with the logo; that label scrolls with LBC. Drive status and the puzzle date form two lines beside the logo.",
    "preview docs real logo",
)
docs = replace_once(
    docs,
    "- `Word Log` is temporarily replaced by a bordered square logo placeholder. It displays its current side length in pixels and should remain a perfect square sized to the natural available header height.",
    "- `Word Log` is replaced by the current temporary cube logo, which remains a perfect square sized to the natural available header height. The old bordered `#px` prototype is gone.",
    "preview docs remove logo prototype",
)
docs_path.write_text(docs, encoding="utf-8")
