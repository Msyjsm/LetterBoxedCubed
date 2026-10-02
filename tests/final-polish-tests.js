const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'LetterBoxedCubed.user.js'), 'utf8');
const preview = fs.readFileSync(path.join(root, 'tools', 'preview_runtime.js'), 'utf8');

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(source.includes('// @version      1.13.1-beta.7'), 'beta.7 version missing');
assert(source.includes('const ExportFormatVersion = 4;'), 'backup schema v4 missing');
assert(source.includes('LetterBoxedCubed_ThemeState'), 'theme state storage missing');
assert(source.includes('Name: "NYT Dark"'), 'NYT Dark prebuilt theme missing');
assert(source.includes('MergeThemeStates'), 'theme merge missing');
assert(source.includes('LbPageBackground: "#121212"'), 'NYT Dark mobile background calibration missing');
assert(source.includes('LbText: "#F8F8F8"'), 'NYT Dark mobile text calibration missing');
assert(source.includes('LbAccent: "#DA5D57"'), 'NYT Dark mobile accent calibration missing');
assert(source.includes('--text: #000000 !important;'), 'canvas source-letter dark-mode correction missing');
assert(source.includes('lb-cubed-board-inverted'), 'board inversion theme class missing');
assert(source.includes('Game-module_toolbarContainer__'), 'NYT post-start toolbar dark surface override missing');
assert(source.includes('#js-global-nav'), 'NYT pre-start/global nav dark surface override missing');
assert(source.includes('#js-logo-nav .pz-nav__logo rect'), 'NYT logo background dark-mode override missing');
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
assert(preview.includes('PreviewTransientTrace'), 'transient trace state missing');
assert(preview.includes('!PreviewDebugPaneVisible'), 'hidden debug pane render guard missing');

console.log('PASS: final polish static checks');
