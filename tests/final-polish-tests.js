const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'LetterBoxedCubed.user.js'), 'utf8');
const preview = fs.readFileSync(path.join(root, 'tools', 'preview_runtime.js'), 'utf8');

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(source.includes('// @version      1.13.1-beta.20'), 'beta.20 version missing');
assert(source.includes('const ExportFormatVersion = 4;'), 'backup schema v4 missing');
assert(source.includes('LetterBoxedCubed_ThemeState'), 'theme state storage missing');
assert(source.includes('Name: "NYT Dark"'), 'NYT Dark prebuilt theme missing');
assert(source.includes('MergeThemeStates'), 'theme merge missing');
assert(source.includes('const ThemeStateVersion = 2;'), 'ThemeState v2 missing');
assert(source.includes('LbBackground: "#FAA6A4"'), 'NYT Light page background calibration missing');
assert(source.includes('LbBoard: "#FFFFFF"'), 'NYT Light board color missing');
assert(source.includes('BoardMatchesBackground: false'), 'NYT Light board/background separation missing');
assert(source.includes('BoardMatchesBackground: true'), 'NYT Dark board/background tie missing');
assert(source.includes('LbForeground: "#F8F8F8"'), 'NYT Dark foreground calibration missing');
assert(source.includes('LbActive: "#DA5D57"'), 'NYT Dark active calibration missing');
assert(source.includes('Redacted: "#F8F8F8"'), 'NYT Dark redacted calibration missing');
assert(source.includes('BuildBoardThemeAffineMatrix'), 'semantic affine board transform missing');
assert(source.includes('feColorMatrix'), 'SVG board color matrix missing');
assert(source.includes('NativeBoardActiveSourceColor = "#E8A9A0"'), 'native active source anchor missing');
assert(source.includes('filter: url(#lb-cubed-board-theme-filter)'), 'semantic board filter CSS missing');
assert(source.includes('html.lb-cubed-board-themed .lb-game-container'), 'game-level native source color guard missing');
assert(source.includes('--text: #000000 !important;'), 'inactive GB letter source normalization missing');
assert(source.includes('InstallBoardTextSourceHook'), 'semantic board text source hook missing');
assert(source.includes('IsThemedBoardLetterDraw'), 'board text hook is not restricted to letter draws');
assert(source.includes('IsNativeBoardWhite(this.fillStyle)'), 'white inactive board letters are not normalized before affine mapping');
assert(source.includes('QueueBoardThemeRendererRefresh'), 'already-painted board renderer refresh missing');
assert(source.includes('.lb-text-field__caret'), 'visible NYT caret theme selector missing');
assert(source.includes('#${HistoryOverlayId} .lb-cubed-stat-value'), 'Browse History stat value theming missing');
assert(source.includes('#${HistoryOverlayId} .lb-cubed-stat-label'), 'Browse History stat label theming missing');
assert(source.includes('background-color: var(--lb-cubed-lb-active) !important;'), 'active-color toast background missing');
assert(source.includes('color: var(--lb-cubed-lb-board) !important;'), 'board-color toast foreground missing');
assert(source.includes('> .lb-par:not(.no-words)'), 'validation-message semantic toast selector missing');
assert(!source.includes('invert(1) hue-rotate(180deg)'), 'legacy inversion filter remains');
assert(!source.includes('InstallDarkBoardCanvasHook'), 'legacy canvas text hook remains');
assert(!source.includes('RepairDarkBoardCanvas'), 'legacy bitmap repair remains');
assert(!source.includes('ThemeAppliedOnce'), 'legacy reload-boundary state remains');
assert(!source.includes('Invert Letter Boxed board/canvas'), 'legacy inversion setting remains');
assert(source.includes('Same as Background'), 'board/background tie control missing');
assert(source.includes('Foreground (active)'), 'semantic active foreground control missing');
assert(source.includes('Heading background'), 'LBC heading background control missing');
assert(source.includes('LbcBackgroundMatchesLbBackground'), 'LBC/background semantic link missing');
assert(source.includes('LbcTextMatchesLbForeground'), 'LBC/text semantic link missing');
assert(source.includes('Same as Letter Boxed Background'), 'LBC background link checkbox missing');
assert(source.includes('Same as Letter Boxed Foreground'), 'LBC text link checkbox missing');
assert(source.includes('ApplyCompactNumberInputWidth'), 'compact number input sizing missing');
assert(source.includes('DigitCount + 1}ch + 22px'), 'compact number inputs lack one-character breathing room');
assert(source.includes('--lb-cubed-control-color-scheme'), 'theme-aware native control color scheme missing');
assert(source.includes('scrollbar-color:'), 'theme-aware scrollbar styling missing');
assert(source.includes('.lb-cubed-settings-panel,'), 'settings scrollbar root styling missing');
assert(source.includes('var(--lb-cubed-lbc-bg, #D88482);'), 'LBC scrollbar track is not semantic background');
assert(source.includes('var(--lb-cubed-lbc-text, #301818)'), 'LBC scrollbar still uses stale border/maroon color');
assert(source.includes('::-webkit-inner-spin-button'), 'always-visible number steppers missing');
assert(source.includes('0.6ch !important'), 'number input stepper spacing missing');
assert(source.includes('font-size: calc(1em + 5px)'), 'NYT solution star +5px sizing missing');
assert(source.includes('const TargetLightness = IsDark'), 'NYT solution hue-preserving tint/shade derivation missing');
assert(source.includes('Lightness * 0.55'), 'NYT solution shade is still too close to black/white');
assert(source.includes('.lb-cubed-nyt-solution * {'), 'NYT solution descendants are not forced to the derived shade');
assert(source.includes('-webkit-text-fill-color: var(--lb-cubed-nyt-solution-text)'), 'NYT solution text-fill override missing');
assert(source.includes('Google Drive bridge returned HTML instead of JSON'), 'Drive HTML response retry guard missing');
assert(source.includes('no HTML was imported into LBC data'), 'Drive HTML failure explanation missing');
assert(source.includes('.lb-text-field__caret::before'), 'caret pseudo-element theming missing');
assert(source.includes('color: var(--lb-cubed-lb-active) !important;'), 'current word-entry UI is not mapped to active foreground');
assert(source.includes('-webkit-text-fill-color: var(--lb-cubed-lb-fg)'), 'exact native foreground fill missing');
assert(source.includes('CreateThemeColorRow("Redacted", "Redacted")'), 'redacted theme control missing');
assert(!source.includes('["Muted text", "LbcMuted"]'), 'editable muted text control remains');
assert(!source.includes('["Accent", "LbcAccent"]'), 'editable LBC accent control remains');
assert(!source.includes('["Success", "Success"]'), 'editable success color remains');
assert(!source.includes('["Error", "Danger"]'), 'editable error color remains');
assert(source.includes('FixedSuccessColor = "#2D7D3E"'), 'fixed success color missing');
assert(source.includes('FixedDangerColor = "#AF3636"'), 'fixed error color missing');
assert(source.includes('.lb-text-field-underline'), 'native word-entry underline theme missing');
assert(source.includes('[class*="Game-module_gameContainer__"]'), 'outer NYT game background override missing');
assert(source.includes('lb-cubed-nyt-solution-star'), 'separately sized NYT solution star missing');
assert(source.includes('--lb-cubed-nyt-solution-text'), 'derived NYT solution text color missing');
assert(source.includes('--lb-cubed-redacted'), 'redacted CSS variable missing');
assert(source.includes('lb-message-box success-message lb-cubed-valid-feedback-proxy'), 'valid-word toast no longer reuses native NYT styling classes');
assert(source.includes('ValidFeedbackProxyMinimumVisibleMs = 600'), 'source-independent toast minimum lifetime missing');
assert(source.includes('Source?.textContent || ActiveValidFeedbackText'), 'toast settling still requires live NYT source');
assert(source.includes('Proxy.textContent = MessageText'), 'valid-word toast does not preserve captured praise text');
assert(source.includes('clip-path: none !important;'), 'dark valid-word toast clipping reset missing');
assert(source.includes('InternalPanelLayoutBreakpoints = ['), 'original breakpoint list missing');
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
assert(source.includes('Custom 12-column placement is stored as inline grid-column/grid-row'), 'custom layout is not reapplied after RenderPanel rebuilds dashboard children');
assert(!source.includes('lb-cubed-layout-narrow'), 'rejected narrow/medium/wide layout implementation remains');
assert(!source.includes('@container lbc'), 'state-less container-query cascade should not return');

for (const label of [
  'Copy Geometry Snapshot',
  'Start Transient Element Trace',
  'Stop + Copy Trace',
  'Copy Board Source Snapshot',
  'Start Board Canvas Trace',
  'Stop + Copy Board Trace',
  'Copy Bootstrap Trace',
  'Copy Full Debug Bundle'
]) {
  assert(preview.includes(label), `preview diagnostic missing: ${label}`);
}
assert(preview.includes('GetPreviewDebugBundle'), 'full debug bundle function missing');
assert(preview.includes('InternalPanelLayoutStage'), 'debug bundle does not use current layout stage');
assert(!preview.includes('                InternalPanelLayoutMode,'), 'debug bundle still references stale InternalPanelLayoutMode');
assert(preview.includes('Full debug bundle fallback'), 'debug bundle copy lacks failure fallback');
assert(preview.includes('PreviewTransientTrace'), 'transient trace state missing');
assert(preview.includes('GetPreviewBoardCanvasSnapshot'), 'board source snapshot diagnostic missing');
assert(preview.includes('InstallPreviewBoardCanvasTraceHook'), 'board Canvas2D trace hook missing');
assert(preview.includes('SourcePixelHistogram'), 'board source pixel histogram missing');
assert(preview.includes('TextDraws: structuredClone(PreviewBoardCanvasTrace)'), 'board trace missing from full debug bundle');
assert(preview.includes('!PreviewDebugPaneVisible'), 'hidden debug pane render guard missing');
assert(preview.includes('UpdatePreviewVersionLabelContrast'), 'preview version contrast helper missing');
assert(preview.includes('Luminance < 0.22'), 'preview version darkness threshold missing');

console.log('PASS: final polish static checks');
