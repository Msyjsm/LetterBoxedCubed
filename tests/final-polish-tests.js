const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'LetterBoxedCubed.user.js'), 'utf8');
const preview = fs.readFileSync(path.join(root, 'tools', 'preview_runtime.js'), 'utf8');
function assert(condition, message) { if (!condition) throw new Error(message); }

assert(source.includes('// @version      1.13.1-beta.35'), 'beta.35 version missing');
assert(source.includes('const ExportFormatVersion = 4;'), 'backup schema v4 missing');
assert(source.includes('const ThemeStateVersion = 2;'), 'ThemeState v2 compatibility missing');
assert(source.includes('MergeThemeStates'), 'theme merge missing');
assert(source.includes('Name: "NYT Light"'), 'Light preset missing');
assert(source.includes('Name: "NYT Dark"'), 'Dark preset missing');
assert(source.includes('/* Native NYT Light is the zero-override baseline. */\n            ApplyNative: false'), 'NYT Light should be native/un-themed');
assert(source.includes('LbBackground: "#E3A5A3"'), 'Light Background calibration missing');
assert(source.includes('LbForeground: "#000000"'), 'Light Foreground missing');
assert(source.includes('LbActive: "#FFFFFF"'), 'Light Highlight missing');
assert(source.includes('LbBackground: "#121212"'), 'Dark Background missing');
assert(source.includes('LbForeground: "#F8F8F8"'), 'Dark Foreground missing');
assert(source.includes('LbActive: "#DA5D57"'), 'Dark Highlight missing');
assert(source.includes('GetLbThemeSemantics'), 'semantic derivation missing');
assert(source.includes('const Background = Palette.LbBackground;'), 'Background semantic missing');
assert(source.includes('const Foreground = Palette.LbForeground;'), 'Foreground semantic missing');
assert(source.includes('const Highlight = Palette.LbActive;'), 'Highlight semantic missing');
assert(source.includes('CreateThemeColorRow("Background", "LbBackground")'), 'Background editor missing');
assert(source.includes('CreateThemeColorRow("Foreground", "LbForeground")'), 'Foreground editor missing');
assert(source.includes('CreateThemeColorRow("Highlight", "LbActive")'), 'Highlight editor missing');
assert(!source.includes('CreateThemeBoardColorRow('), 'obsolete board-link UI remains');
assert((source.match(/Use Letter Boxed color/g) || []).length >= 3, 'unified LBC color-link labels missing');
assert(source.includes('LbcHighlightMatchesLbHighlight'), 'LBC Highlight link state missing');
assert(source.includes('UpdateActiveCustomThemeLbcHighlightMatch'), 'LBC Highlight link action missing');
assert(source.includes('CreateThemeColorRow("New word highlight", "NewHighlight")'), 'New word highlight label missing');
assert(source.includes('CreateThemeColorRow("Headings", "LbcHeadingBackground")'), 'Headings label missing');
assert(!source.includes('\n            "Highlights",\n'), 'obsolete Highlights subgroup remains');
assert(source.includes('const LayoutSection = CreatePanelLayoutSettingsSection();'), 'top-level Layout section missing');
assert(source.includes('function CreatePanelLayoutSettingsSection()'), 'Layout section constructor missing');
assert(source.includes('AnimationSection,\n            ThemeSection,\n            LayoutSection,\n            DisplaySection,\n            SyncSection'), 'settings section order is wrong');
assert(!source.includes('Palette.LbForeground = GetThemeContrastPole(Palette.LbBackground)'), 'Foreground is still derived from Background');
assert(source.includes('Root.classList.toggle("lb-cubed-native-theme", ApplyNative)'), 'native-theme opt-in missing');
assert(source.includes('Root.classList.toggle("lb-cubed-board-themed", ApplyNative)'), 'board-theme opt-in missing');
assert(source.includes('function UninstallBoardTextSourceHook()'), 'native Light board-hook restore missing');
assert(source.includes('QueueBoardThemeRendererRefresh(true)'), 'native Light repaint restore missing');
assert(source.includes('lb-cubed-theme-dark'), 'dark semantic class missing');
assert(source.includes('--lb-cubed-success-toast-bg'), 'success toast vars missing');
assert(source.includes('--lb-cubed-error-toast-bg'), 'error toast vars missing');
assert(source.includes('SuccessToastForeground: IsDark ? Background : Foreground'), 'success foreground triad mapping missing');
assert(source.includes('SuccessToastBackground: IsDark ? Foreground : Highlight'), 'success background triad mapping missing');
assert(source.includes('ErrorToastForeground: IsDark ? Background : Highlight'), 'error foreground triad mapping missing');
assert(source.includes('ErrorToastBackground: IsDark ? Highlight : Foreground'), 'error background triad mapping missing');
assert(source.includes('BuildBoardThemeAffineMatrix'), 'board affine matrix missing');
assert(source.includes('LbSemantics.BoardBackground'), 'board semantic background mapping missing');
assert(source.includes('LbSemantics.Connector'), 'connector semantic mapping missing');
assert(source.includes('NativeBoardStroke = Prototype.stroke'), 'used-node stroke hook missing');
assert(source.includes('GetDarkLetterSource'), 'dark letter source mapping missing');
assert(source.includes('IsNativeBoardBlack'), 'black source detector missing');
assert(source.includes('IsNativeBoardActive'), 'active source detector missing');
assert(source.includes('this.strokeStyle = NativeBoardActiveSourceColor'), 'used-node outline promotion missing');
assert(source.includes('.lb-cubed-potential-word-empty,'), 'Hints empty foreground missing');
assert(source.includes('font-size: calc(1em + 5px)'), 'NYT solution star size missing');
assert(!source.includes('#${PanelId} .lb-cubed-nyt-solution * {'), 'solution still recolors all descendants');
assert(source.includes('-webkit-text-fill-color: var(--lb-cubed-redacted)'), 'redaction fill guard missing');
assert(source.includes('button[data-testid="modal-close"]'), 'win modal close override missing');
assert(source.includes('ApplyCompactNumberInputWidth'), 'number sizing missing');
assert(source.includes('DigitCount + 1}ch + 22px'), 'number breathing room missing');
assert(source.includes('Google Drive bridge returned HTML instead of JSON'), 'Drive HTML guard missing');
assert(source.includes('lb-cubed-toast-proxy lb-cubed-valid-feedback-proxy'), 'valid feedback proxy missing');
assert(source.includes('lb-cubed-toast-proxy lb-cubed-error-feedback-proxy'), 'error feedback proxy missing');
assert(source.includes('function GetNativeErrorWordFeedbackSource()'), 'native error capture missing');
assert(source.includes('PositionValidWordFeedbackProxy(\n            Proxy,'), 'shared toast positioning missing');
assert(source.includes('transition: opacity ${ToastFadeMs}ms ease !important;'), 'whole-toast opacity fade missing');
assert(source.includes('.lb-cubed-toast-proxy.lb-cubed-toast-visible'), 'toast visible state missing');
assert(source.includes('.lb-cubed-error-feedback-source'), 'native error suppression missing');
assert(!source.includes('html.lb-cubed-native-theme .lb-message-box,\n            html.lb-cubed-native-theme button'), 'broad native message-box recolor remains');
assert(source.includes('ValidFeedbackProxyMinimumVisibleMs = 600'), 'valid toast lifetime missing');
assert(source.includes('InternalPanelLayoutBreakpoints = ['), 'responsive breakpoints missing');
for (const breakpoint of ['340', '390', '520', '650', '860', '1180']) assert(source.includes(breakpoint), `breakpoint missing ${breakpoint}`);
for (const label of ['Copy Board Source Snapshot','Start Board Canvas Trace','Stop + Copy Board Trace','Copy Full Debug Bundle']) assert(preview.includes(label), `preview diagnostic missing ${label}`);
assert(source.includes('function CaptureNativeLightTriad(Palette)'), 'native Light live calibration missing');
assert(source.includes('Palette = CaptureNativeLightTriad(Palette);'), 'custom Light capture missing');
assert(source.includes('const ThemeModeChanged ='), 'theme mode transition detection missing');
assert(source.includes('function RepairBoardLetterSourceForThemeModeSwitch(WasDark, IsDark)'), 'cross-mode letter source repair missing');
assert(source.includes('const EdgeX = Math.floor(Width * 0.15);'), 'letter-only perimeter guard missing');
assert(source.includes('Context.getImageData(0, 0, Width, Height)'), 'letter source pixel read missing');
assert(source.includes('Context.putImageData(Image, 0, 0);'), 'letter source pixel write missing');
assert(source.includes('RepairBoardLetterSourceForThemeModeSwitch(\n                WasDarkTheme,'), 'theme transition does not invoke letter repair');
assert(source.includes('const NudgedWidth = `${Rect.width + 1}px`;'), 'real board resize nudge missing');
assert(source.includes('function ActivateToastType(Kind)'), 'cross-type toast arbitration missing');
assert(source.includes('RemoveToastProxyImmediately(Previous)'), 'older toast immediate kill missing');
assert(source.includes('padding: 6px 10px !important;'), 'toast padding missing');

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
assert(source.includes('CompactTitleLayout &&') && source.includes('!HideNytGameTitle;'), 'compact title hidden-state guard missing');
assert(source.includes('document.getElementById(NytHeaderResizeHandleId)?.remove();'), 'header grip removal missing');
assert(source.includes('document.getElementById(NytTitleResizeHandleId)?.remove();'), 'title grip removal missing');
assert(!source.includes('\"Header size\"'), 'Header size control still present');
assert(!source.includes('\"Game title size\"'), 'Game title size control still present');
assert(!source.includes('\"Footer size\"'), 'Footer size control still present');


assert(source.includes('const CollapseTitleSectionMargin ='), 'hidden-title margin collapse state missing');
assert(source.includes('CompactTitleActive ||\n            HideNytGameTitle'), 'hidden title does not collapse section margin');
assert(source.includes('ReadPanelSectionScrollStates'), 'subsection scroll snapshot missing');
assert(source.includes('RestorePanelSectionScrollStates'), 'subsection scroll restore missing');
assert(source.includes('data-cubed-scroll-key'), 'subsection scroll keys missing');
assert(source.includes('ConfigureLongestFoundTicker(LongestCard)'), 'Longest Found ticker hookup missing');
assert(source.includes('SpeedPixelsPerSecond = 16'), 'Longest Found gentle autoscroll missing');
assert(source.includes('Viewport.addEventListener(\n            "wheel"'), 'Longest Found wheel control missing');
assert(source.includes('.lb-cubed-longest-ticker {'), 'Longest Found one-line CSS missing');
assert(source.includes('white-space: nowrap;\n                overflow-wrap: normal;'), 'Longest Found can still wrap');
assert(source.includes('#${PanelContentId} {\n                display: flex;\n                flex-direction: column;'), 'panel shell is not fixed-header flex layout');
assert(source.includes('overflow: hidden;\n                background: rgb(216, 132, 130);'), 'outer LBC scroller still active');
assert(source.includes('.lb-cubed-potential-word-list {\n                display: grid;\n                flex: 1 1 auto;'), 'Hints do not own list scrollers');
assert(source.includes('.lb-cubed-twofer-body {\n                flex: 1 1 auto;'), 'Twofers body scroller missing');
assert(source.includes('.lb-cubed-length-grid {\n                display: grid;\n                flex: 1 1 auto;'), 'Words by Length fallback scroller missing');
assert(source.includes('.lb-cubed-word-grid {\n                display: grid;\n                flex: 1 1 auto;'), 'Found/Unfound scrollers missing');
assert(source.includes('grid-template-rows: auto repeat(5, minmax(0, 1fr));'), 'narrow responsive section rows are not bounded');
assert(source.includes('\"stats stats stats stats stats\"') && source.includes('\"hints twofers length found unfound\"'), 'wide responsive section rows are not bounded');



// beta.28: section-owned scrolling + full-height allocation.
assert(source.includes('const GameContainerVerticalPaddingTrimPx = 30;'), '30px game-container padding trim missing');
assert(source.includes('ApplyGameContainerVerticalPaddingTrim(GameContainer);'), 'game-container padding trim is not applied');
assert(source.includes('flex: 1 1 0;\n                min-width: 0;\n                min-height: 0;\n                height: auto;\n                max-height: 100%;'), 'dashboard does not own remaining panel height');
assert(source.includes('.lb-cubed-dashboard-grid > .lb-cubed-tree {\n                height: 100%;'), 'dashboard sections do not stretch to their grid tracks');
assert(source.includes('flex: 1 1 0 !important;\n                min-height: 0 !important;\n                overflow-x: hidden !important;\n                overflow-y: auto !important;'), 'section scroll lanes are not explicit scrollports');
assert(source.includes('scrollbar-gutter: stable;'), 'section scrollbar gutter missing');
assert(source.includes('Entry.Definition.Selector === ".lb-cubed-stat-grid"'), 'Completion/Longest are not forced into the first row');
assert(source.includes('grid-template-rows: auto;\n                grid-auto-rows: minmax(0, 1fr);'), 'custom layout does not keep row 1 static and divide later rows evenly');
assert(source.includes('"stats stats stats stats stats"') && source.includes('"hints twofers length found unfound"'), 'wide automatic layout no longer pins stats above scrollable sections');



// beta.29: bounded subsection scrollports, document-owned page scrolling,
// conditional footer padding, and independently adjustable lower LB gap.
assert(source.includes('const BottomLayoutGapHandleId = "lb-cubed-bottom-layout-gap-handle";'), 'bottom gap handle id missing');
assert(source.includes('let BottomLayoutGapPx = 0;'), 'bottom gap state missing');
assert(source.includes('"Set top gap"'), 'top gap label missing');
assert(source.includes('"Set bottom gap"'), 'bottom gap label missing');
assert(source.includes('"Enable draggable grip lines"'), 'plural grip label missing');
assert(source.includes('GapHeading.textContent = "Letter box layout gaps";'), 'gap section label missing');
assert(source.includes('function ApplyBottomLayoutGap(SquareContainer)'), 'bottom gap application missing');
assert(source.includes('function HandleBottomLayoutGapPointerMove(Event)'), 'bottom gap drag behavior missing');
assert(source.includes('NativeSquareHeight + BottomLayoutGapPx'), 'lower gap does not expand square lane');
assert(source.includes('const BottomPadding = HideNytFooter'), 'footer-hidden zero bottom padding missing');
assert(source.includes('function ApplyOuterPageScrollOwnership(GameContainer)'), 'outer scroll ownership helper missing');
assert(source.includes('.lb-cubed-native-scroll-passthrough {'), 'native inner-scroll passthrough CSS missing');
assert(source.includes('display: grid;\n                grid-template-rows: auto minmax(0, 1fr);\n                overflow: hidden;'), 'top-level details are not bounded grid scroll hosts');
assert(source.includes('.lb-cubed-potential-word-tree[open] {\n                display: grid;'), 'hint subtrees are not bounded grid scroll hosts');
assert(source.includes('scrollbar-color:\n                    var(--lb-cubed-lbc-text, #301818)'), 'section scrollbar colors missing');


// beta.30: Chromium <details> internal content wrapper must be bounded so
// subsection bodies can actually shrink below intrinsic content height.
assert(source.includes('.lb-cubed-dashboard-grid > .lb-cubed-tree[open]::details-content,'), 'top-level details-content wrapper constraint missing');
assert(source.includes('.lb-cubed-potential-word-tree[open]::details-content {'), 'hint details-content wrapper constraint missing');


// beta.31: nested Hints columns must stretch through the full available row height.
assert(source.includes('.lb-cubed-hint-counter-grid {') && source.includes('height: 100%;'), 'Hints counter grid full-height stretch missing');
assert(source.includes('.lb-cubed-potential-word-tree {') && source.includes('align-self: stretch;'), 'Hints subtrees are not stretched');

console.log('PASS: beta.31 Hints full-height fill static checks');

// beta.33: Help stacking-context lift + robust ticker motion/test input.
assert(source.includes('[class*="Game-module_toolbarContainer__"]:has(#help-dialog)'), 'Help toolbar stacking-context lift missing');
assert(source.includes('cursor: ew-resize;'), 'Longest Found horizontal cursor missing');
assert(source.includes('let Position = Viewport.scrollLeft;'), 'ticker floating position accumulator missing');
assert(source.includes('Position = Next;'), 'ticker does not persist fractional progress');
assert(preview.includes('LongestInput.setSelectionRange(SanitizedStart, SanitizedEnd);'), 'Test Beds input caret preservation missing');
assert(preview.includes('["keydown", "keyup", "keypress", "beforeinput"]'), 'Test Beds input key propagation guard missing');

console.log('PASS: beta.33 Help/ticker/Test Beds static checks');

// beta.34: Test Beds placeholder polish + reveal newly highlighted rows in their owned scrollports.
assert(source.includes('function QueueHighlightedElementScrollIntoView(Element)'), 'highlight scroll helper missing');
assert(source.includes('ScrollHost.scrollTo({'), 'highlight scroll action missing');
assert(source.includes('behavior: "smooth"'), 'highlight scroll should be smooth');
assert((source.match(/QueueHighlightedElementScrollIntoView\(Element\);/g) || []).length >= 3, 'not all recent highlight paths reveal their rows');
assert(preview.includes('LongestInput.placeholder = "Enter a long string of text here";'), 'Longest Words placeholder text missing');
assert(preview.includes('.lbc-longest-words-test-input::placeholder'), 'Longest Words placeholder styling missing');
assert(preview.includes('font-style: italic;'), 'Longest Words placeholder italics missing');
assert(preview.includes('opacity: 0.55;'), 'Longest Words placeholder dimming missing');

console.log('PASS: beta.34 final scroll/placeholder static checks');
assert(preview.includes('? \"Test Beds (ACTIVE)\"'), 'Test Beds button missing');
assert(preview.includes('HistoricalHeading.textContent = \"Historical Word Sandbox\";'), 'Historical section missing');
assert(preview.includes('LongestHeading.textContent = \"Longest Words Scrolling\";'), 'Longest Words section missing');
assert(preview.includes('.replace(/[^A-Z ,]/g, \"\")'), 'Longest Words sanitizer missing');

assert(source.includes('flex: 1 1 0;\n                grid-template-rows: auto minmax(0, 1fr);'), 'Hints body flex fill missing');
assert(source.includes('#help-dialog {\n                z-index: 100050 !important;'), 'Help dropdown layering fix missing');



// beta.35: Preview-only, non-destructive highlight-continuity Test Bed and trace.
assert(preview.includes('HighlightHeading.textContent = "New Word Highlights"'), 'new highlights Test Bed missing');
assert(preview.includes('function ResetPreviewNewWordHighlights()'), 'highlight reset missing');
assert(preview.includes('RecentWordHighlights.clear();'), 'word highlight reset missing');
assert(preview.includes('RecentTwoferHighlights.clear();'), 'twofer highlight reset missing');
assert(preview.includes('function CopyPreviewHighlightTrace()'), 'highlight trace copy missing');
assert(preview.includes('["animationcancel", "animation-cancel"]'), 'CSS cancel trace missing');
assert(preview.includes('"animation-start"'), 'CSS animation start trace missing');
assert(preview.includes('"render-start"'), 'redraw trace missing');
assert(preview.includes('"submission-attempt"'), 'submission trace missing');
assert(preview.includes('"twofer-check"'), 'twofer trace missing');
assert(preview.includes('InstallPreviewHighlightDiagnostics();'), 'diagnostics not installed');
console.log('PASS: beta.35 highlight-continuity diagnostic checks');
