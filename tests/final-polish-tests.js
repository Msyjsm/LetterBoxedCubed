const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'LetterBoxedCubed.user.js'), 'utf8');
const preview = fs.readFileSync(path.join(root, 'tools', 'preview_runtime.js'), 'utf8');

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(source.includes('// @version      1.13.1-beta.3'), 'beta.3 version missing');
assert(source.includes('const ExportFormatVersion = 4;'), 'backup schema v4 missing');
assert(source.includes('LetterBoxedCubed_ThemeState'), 'theme state storage missing');
assert(source.includes('NYT Dark (app)'), 'NYT Dark prebuilt theme missing');
assert(source.includes('MergeThemeStates'), 'theme merge missing');
assert(source.includes('lb-cubed-layout-narrow'), 'narrow layout mode missing');
assert(source.includes('lb-cubed-layout-medium'), 'medium layout mode missing');
assert(source.includes('lb-cubed-layout-wide'), 'wide layout mode missing');
assert(source.includes('NarrowToMedium: 500'), 'layout hysteresis enter threshold missing');
assert(source.includes('MediumToNarrow: 440'), 'layout hysteresis exit threshold missing');
assert(source.includes('MediumToWide: 820'), 'wide enter threshold missing');
assert(source.includes('WideToMedium: 740'), 'wide exit threshold missing');
assert(!source.includes('@container lbc'), 'old independent container-query cascade remains');

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
