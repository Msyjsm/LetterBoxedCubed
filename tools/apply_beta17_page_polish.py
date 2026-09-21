from pathlib import Path

source_path = Path('LetterBoxedCubed.user.js')
changelog_path = Path('CHANGELOG.md')
docs_path = Path('docs/PREVIEW_TESTING.md')

source = source_path.read_text(encoding='utf-8')
changelog = changelog_path.read_text(encoding='utf-8')
docs = docs_path.read_text(encoding='utf-8')


def once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 occurrence, found {count}')
    return text.replace(old, new, 1)


source = once(
    source,
    '// @version      1.12.0-beta.16',
    '// @version      1.12.0-beta.17',
    'version'
)

source = once(
    source,
    '''    const NytOriginalHeights = {
        Header: null,
        Title: null
    };
''',
    '''    const NytOriginalHeights = {
        Header: null,
        Title: null
    };
    let NytOriginalTitleLeftOffset = null;
''',
    'title anchor state'
)

source = once(
    source,
    '''    function ApplyNytElementScale(Element, Scale) {
        if (!Element) {
            return;
        }
''',
    '''    function CaptureNytTitleLeftAnchor(Element) {
        if (!Element || NytOriginalTitleLeftOffset !== null) {
            return;
        }

        const Parent = Element.parentElement;
        if (!Parent) {
            return;
        }

        const Rect = Element.getBoundingClientRect();
        const ParentRect = Parent.getBoundingClientRect();
        const Offset = Rect.left - ParentRect.left;

        if (Number.isFinite(Offset)) {
            NytOriginalTitleLeftOffset = Math.max(0, Offset);
        }
    }

    function ApplyNytElementScale(Element, Scale) {
        if (!Element) {
            return;
        }
''',
    'capture title left anchor helper'
)

source = once(
    source,
    '''    function ApplyNytTitleArrangement() {
        const Host = document.querySelector("#portal-game-header");
''',
    '''    function ApplyNytTitleArrangement() {
        const Host = document.querySelector("#portal-game-header");
        const TitleBar = document.querySelector(
            "#letter-boxed-container .pz-game-title-bar"
        );
        const TitleSection = TitleBar?.closest(".pz-section");
''',
    'title arrangement targets'
)

source = once(
    source,
    '''        if (Host) {
            Host.classList.toggle(
                "lb-cubed-compact-title-layout",
                CompactTitleLayout
            );
        }

        document.querySelectorAll(".lb-cubed-yesterday-help-row-hidden")
''',
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
        }

        document.querySelectorAll(".lb-cubed-yesterday-help-row-hidden")
''',
    'compact title parent class'
)

source = once(
    source,
    '''        const Targets = GetNytPageTargets();
        CaptureNytOriginalHeight("Header", Targets.Header);
        CaptureNytOriginalHeight("Title", Targets.Title);

        ApplyNytElementScale(Targets.Header, NytHeaderScale);
        ApplyNytElementScale(Targets.Title, NytTitleScale);
        ApplyNytTitleArrangement();
''',
    '''        const Targets = GetNytPageTargets();
        CaptureNytOriginalHeight("Header", Targets.Header);
        CaptureNytOriginalHeight("Title", Targets.Title);
        CaptureNytTitleLeftAnchor(Targets.Title);

        ApplyNytElementScale(Targets.Header, NytHeaderScale);
        ApplyNytElementScale(Targets.Title, NytTitleScale);

        /*
            NYT normally centers the title bar with auto margins. CSS zoom then
            changes its used width, so the whole title region appears to shrink
            toward the middle. Preserve the title bar's native left edge within
            its parent and let all scaling grow/shrink to the right from there.
        */
        if (Targets.Title && NytOriginalTitleLeftOffset !== null) {
            Targets.Title.style.setProperty(
                "margin-left",
                `${NytOriginalTitleLeftOffset}px`,
                "important"
            );
            Targets.Title.style.setProperty(
                "margin-right",
                "auto",
                "important"
            );
        }

        ApplyNytTitleArrangement();
''',
    'apply title anchor'
)

source = once(
    source,
    '''            #${PreviewVersionLabelId} {
                position: fixed;
''',
    '''            #${PreviewVersionLabelId} {
                position: absolute;
''',
    'preview version scroll positioning'
)

source = once(
    source,
    '''            #${PreviewDebugToggleButtonId} {
                position: fixed;
''',
    '''            #${PreviewDebugToggleButtonId} {
                position: absolute;
''',
    'preview debug toggle scroll positioning'
)

source = once(
    source,
    '''            #letter-boxed-container .pz-game-title-bar {
                justify-content: flex-start !important;
                text-align: left !important;
                transform-origin: left top !important;
            }
''',
    '''            #letter-boxed-container .pz-game-title-bar {
                justify-content: flex-start !important;
                text-align: left !important;
                transform-origin: left top !important;
            }

            /*
                Compact mode removes NYT's otherwise persistent 24px section
                top margin so hiding/shrinking the title region actually
                recovers that vertical space too.
            */
            #letter-boxed-container
            .pz-section.lb-cubed-compact-title-section {
                margin-top: 0 !important;
            }
''',
    'compact title section css'
)

source = once(
    source,
    '''            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-par.no-words {
                position: absolute !important;
                top: 100% !important;
                left: 0 !important;
                right: 0 !important;
                margin-top: 10px !important;
                transform: none !important;
                z-index: 2;
            }
''',
    '''            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-par.no-words {
                position: absolute !important;
                top: 100% !important;
                left: 0 !important;
                right: 0 !important;
                margin-top: 10px !important;
                text-align: center !important;
                transform: none !important;
                z-index: 2;
            }
''',
    'zero-word par centering'
)

source = once(
    source,
    '''        const ToggleLeft = Clamp(
            (SettingsRect?.right ?? PanelRect.right) - ToggleWidth,
            8,
            Math.max(8, window.innerWidth - ToggleWidth - 8)
        );
        const ToggleTop = Math.max(
            8,
            PanelRect.top - ToggleHeight - 4
        );
''',
    '''        const ScrollX = window.scrollX || window.pageXOffset || 0;
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
''',
    'debug toggle page coordinates'
)

source = once(
    source,
    '''        const Left = Clamp(
            LogoRect?.left ?? (PanelRect.left + 12),
            4,
            Math.max(4, window.innerWidth - Label.offsetWidth - 4)
        );
        const Top = Math.max(
            2,
            PanelRect.top - LabelHeight - 4
        );
''',
    '''        const ScrollX = window.scrollX || window.pageXOffset || 0;
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
''',
    'preview version page coordinates'
)

changelog = once(
    changelog,
    '# Changelog\n\n',
    '''# Changelog\n\n## 1.12.0-beta.17\n- Restored centered alignment for the zero-word `Try to solve in X words` par while preserving the alternate nested no-words DOM handling.\n- Anchored the Letter Boxed title region to its captured native left edge before applying CSS zoom, so resize percentages grow/shrink to the right instead of recentering toward the viewport middle.\n- Compact title layout now also removes the parent `.pz-section` top margin, reclaiming NYT's otherwise persistent 24px vertical gap.\n- Preview's version label and Show/Hide Debug Pane button now use document-absolute positioning so they scroll with LBC; the debug pane itself remains fixed to the viewport.\n\n''',
    'changelog beta17'
)

docs = once(
    docs,
    'The current source is `1.12.0-beta.16`.',
    'The current source is `1.12.0-beta.17`.',
    'docs version'
)

docs = once(
    docs,
    '- The initial `.lb-par.no-words` is removed from normal flow so NYT\'s zero-word DOM variant cannot alter the measured input height.',
    '- The initial `.lb-par.no-words` is removed from normal flow so NYT\'s zero-word DOM variant cannot alter the measured input height; when visible, that zero-word prompt remains centered like NYT\'s native presentation.',
    'docs par behavior'
)

docs = once(
    docs,
    '- Preview includes a TI/GB DOM debugger. Its external **Show Debug Pane / Hide Debug Pane** control sits just outside LBC, right-aligned with Settings; the pane opens to the **right** of LBC and below that control. The pane is explicitly hidden/shown by the toggle, and mutation capture continues while hidden. The right LBC resize grip is centered in an equal gutter between LBC and the debugger.',
    '- Preview includes a TI/GB DOM debugger. Its external **Show Debug Pane / Hide Debug Pane** control sits just outside LBC, right-aligned with Settings, and scrolls with LBC. The pane itself remains viewport-fixed to the **right** of LBC. The pane is explicitly hidden/shown by the toggle, and mutation capture continues while hidden. The right LBC resize grip is centered in an equal gutter between LBC and the debugger.',
    'docs debug control scroll behavior'
)

docs = once(
    docs,
    '- The temporary square logo placeholder must no longer collapse to 0x0 for one animation frame when a word is accepted. Its size measurement is synchronous and should not cause the visible LBC blink seen in beta.4. Preview builds show the exact `GM_info.script.version` in gray just above LBC, left-aligned with the logo; Drive status and the puzzle date form two lines beside the logo.',
    '- The temporary square logo placeholder must no longer collapse to 0x0 for one animation frame when a word is accepted. Its size measurement is synchronous and should not cause the visible LBC blink seen in beta.4. Preview builds show the exact `GM_info.script.version` in gray just above LBC, left-aligned with the logo; that label scrolls with LBC. Drive status and the puzzle date form two lines beside the logo.',
    'docs preview version scroll behavior'
)

docs = once(
    docs,
    '- **Compact title layout** keeps the game title, date, and byline on a single left-justified row with vertical centers aligned, including when the title region is scaled down.',
    '- **Compact title layout** keeps the game title, date, and byline on a single left-justified row with vertical centers aligned, removes the title section\'s native top margin, and preserves the title bar\'s native left edge while the region is scaled up or down.',
    'docs compact title behavior'
)

source_path.write_text(source, encoding='utf-8')
changelog_path.write_text(changelog, encoding='utf-8')
docs_path.write_text(docs, encoding='utf-8')
