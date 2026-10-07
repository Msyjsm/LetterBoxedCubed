const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'LetterBoxedCubed.user.js'), 'utf8');
const preview = fs.readFileSync(path.join(root, 'tools', 'preview_runtime.js'), 'utf8');

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(source.includes('// @version      1.13.1-beta.16'), 'beta.16 version missing');
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
assert(source.includes('background-color: var(--lb-cubed-lb-active) !important;'), 'active-color toast background missing');
assert(source.includes('color: var(--lb-cubed-lb-board) !important;'), 'board-color toast foreground missing');
assert(source.includes('> .lb-par:not(.no-words)'), 'validation-message semantic toast selector missing');
assert(!source.includes('invert(1) hue-rotate(180deg)'), 'legacy inversion filter remains');
assert(!source.includes('InstallDarkBoardCanvasHook'), 'legacy canvas text hook remains');
assert(!source.includes('RepairDarkBoardCanvas'), 'legacy bitmap repair remains');
assert(!source.includes('ThemeAppliedOnce'), 'legacy reload-boundary state remains');
assert(!source.includes('Invert Letter Boxed board/canvas'), 'legacy inversion setting remains');
assert(source.includes('Same as background'), 'board/background tie control missing');
assert(source.includes('Foreground (active)'), 'semantic active foreground control missing');
assert(source.includes('Heading background'), 'LBC heading background control missing');
assert(source.includes('CreateThemeColorRow("Redacted", "Redacted")'), 'redacted theme control missing');
assert(!source.includes('["Muted text", "LbcMuted"]'), 'editable muted text control remains');
assert(!source.includes('["Accent", "LbcAccent"]'), 'editable LBC accent control remains');
assert(!source.includes('["Success", "Success"]'), 'editable success color remains');
assert(!source.includes('["Error", "Danger"]'), 'editable error color remains');
assert(source.includes('FixedSuccessColor = "#2D7D3E"'), 'fixed success color missing');
assert(source.includes('FixedDangerColor = "#AF3636"'), 'fixed error color missing');
assert(source.includes('.lb-text-field-underline'), 'native word-entry underline theme missing');
assert(source.includes('[class*="Game-module_gameContainer__"]'), 'outer NYT game background override missing');
assert(source.includes('NytLabel.textContent = "★ NYT Solution"'), 'themeable NYT solution star missing');
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
assert(preview.includes('!PreviewDebugPaneVisible'), 'hidden debug pane render guard missing');
assert(preview.includes('UpdatePreviewVersionLabelContrast'), 'preview version contrast helper missing');
assert(preview.includes('Luminance < 0.22'), 'preview version darkness threshold missing');

console.log('PASS: final polish static checks');
