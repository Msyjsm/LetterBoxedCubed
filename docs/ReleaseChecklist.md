# LBC Public Release Readiness

This is a manual checklist, not a declaration that Google has verified the script.

## Distribution
- [ ] Confirm Greasy Fork production URL: https://greasyfork.org/en/scripts/593415-letter-boxed-cubed
- [ ] Promote reviewed source/bridge changes from `perf/drive-sync-event-driven` to the production branch **only after testing**.
- [ ] Verify GPL-3.0-or-later license and accessible source links.
- [ ] Update README and website links from the Preview branch to the tagged production release.
- [ ] Confirm Tampermonkey install/update behavior and cross-browser compatibility.

## Hosted website
- [ ] Upload the contents of `LBC_website_tree.zip/lbc/` to the DreamHost site's `/lbc/` directory.
- [ ] Verify home, Google Drive Sync, Privacy & Security, FAQ, and Troubleshooting pages.
- [ ] Verify invalid `/lbc/whatever` paths redirect to `/lbc/` via `.htaccess` (Apache only).
- [ ] Verify mobile accessibility, working external links, and HTTPS.
- [ ] Confirm the intended userscript settings link `https://nathanburgdorff.com/lbc/google-drive-sync/` is reachable.

## Restricted Google Apps Script
- [ ] Update **the actual read-only reference Apps Script project** to match both `integrations/google-drive/Code.gs` and `integrations/google-drive/appsscript.json`. GitHub updates do NOT change that reference project.
- [ ] Copy the reference to a fresh **second Google account** to test the user-owned setup path.
- [ ] Confirm the authorization dialogue requests `drive.file` and Apps Script external HTTP requests, **not unrestricted Google Drive access**.
- [ ] Confirm Advanced Google Drive API v3 is enabled and any standard Cloud project's API is enabled.
- [ ] Run `Setup()`, deploy as *Execute as me* / *Anyone*, connect from LBC, and test Read/Write/replay/conflict.
- [ ] Inspect the newly created private Drive folder and JSON file.
- [ ] Migrate one existing legacy-`DriveApp` installation after saving LBC's manual Export first; confirm no existing file is overwritten.
- [ ] Confirm a fresh reference copy contains **no** script properties, sync secrets, or personal backup data.
- [ ] Document how to rotate a compromised secret and delete a deployment.

## Local recovery
- [ ] Confirm GM-backed puzzle data survives a Drive disconnect and browser reload.
- [ ] Verify an independent localStorage words-only recovery mirror is written on startup and durable changes.
- [ ] Confirm **no Drive URL or secret** appears in the mirror.
- [ ] Test `Settings > Sync > Recover Local Backup` on a disposable browser profile.
- [ ] Test a full browser storage quota: mirror failure must not interrupt primary storage.
- [ ] Verify manual Export/Import remains a valid lossless recovery path.

## Trust and support
- [ ] Publish the privacy/security claims only after checking the compiled production userscript.
- [ ] Verify metadata `@connect` permissions and any new network destinations.
- [ ] Turn on GitHub dependency/security scans and a vulnerability reporting policy.
- [ ] Make support links, change log, and safe incident-reporting instructions available.
- [ ] Do not claim virus-free certification or Google approval unless actually obtained.

## Automated verification
- Preview source regression tests (including bridge mocks and recovery mirror checks) run in `.github/workflows/preview-channel.yml`.
- These mocks **do not substitute for a real Google OAuth consent and Apps Script deployment test**.
