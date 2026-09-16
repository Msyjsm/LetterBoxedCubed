# Preview testing channel

Letter Boxed Cubed has two distribution channels:

- **Production:** `main` -> Greasy Fork -> Tampermonkey (`Letter Boxed Cubed`)
- **Preview:** latest pushed non-`preview` branch -> GitHub Actions -> `preview` branch -> Tampermonkey (`Letter Boxed Cubed [PREVIEW]`)

The preview build is generated from the same canonical `LetterBoxedCubed.user.js`. Its userscript identity and update URLs are rewritten so Tampermonkey installs it beside production rather than replacing production.

## One-time installation

Install the preview script from:

`https://raw.githubusercontent.com/Msyjsm/LetterBoxedCubed/preview/LetterBoxedCubed.preview.user.js`

After installation, leave **both** Production and Preview enabled.

## Choosing Production vs Preview with the URL hash

Tampermonkey does not use URL hash fragments in `@match`/`@include` matching. Therefore both installed scripts technically match the Letter Boxed page. A tiny runtime router in the canonical source makes only one copy continue past startup:

- `https://www.nytimes.com/puzzles/letter-boxed` -> Production runs, Preview exits immediately.
- `https://www.nytimes.com/puzzles/letter-boxed#lbc-preview` -> Preview runs, Production exits immediately.

Changing the hash does not normally reload a page, so the router listens for `hashchange` and forces one reload when you enter or leave preview mode. That gives the newly selected copy a clean startup and avoids trying to tear down a live LBC instance in-place.

Useful bookmarks:

- Production: `https://www.nytimes.com/puzzles/letter-boxed`
- Preview: `https://www.nytimes.com/puzzles/letter-boxed#lbc-preview`

## Why the router lives in source code

The URL fragment (`#lbc-preview`) is client-side state; browsers do not send it to the server, and Tampermonkey's matching layer deliberately ignores it. The scripts therefore cannot be separated by metadata alone. The canonical production source contains `UserscriptBuildChannel = "production"`. The generated preview copy changes only that marker to `"preview"`.

## Preview versioning

Each workflow run appends the monotonically increasing `github.run_number` to the source version. For example, source `1.10.3` may become preview `1.10.3.22`. This means every pushed test build has a newer Tampermonkey version even when the production `@version` has not yet been bumped.

## v1.12 QoL bundle checks

The `feature/qol-4-10-12-13-14` preview bundles issues #4, #5, #10, #12, #13, #14, #16, #17, and #18. The current source is `1.12.0-beta.5`.

- **Adjust layout gap between text input and letter box** now reserves a fixed-height history lane below the text input. Accepted words, the par, and feedback consume this already-reserved space instead of increasing TI height. Entering enough words to wrap onto additional rows must not move GB.
- If accepted-word history exceeds the reserved lane, `.lb-list-container` scrolls vertically inside that lane; GB remains fixed.
- The initial `.lb-par.no-words` is removed from normal flow so NYT's zero-word DOM variant cannot alter the measured input height.
- **Hide par** is independent of LBC layout classes and should hide both the zero-word nested par and the later direct-child par.
- The temporary square logo placeholder must no longer collapse to 0x0 for one animation frame when a word is accepted. Its size measurement is synchronous and should not cause the visible LBC blink seen in beta.4.
- Preview exposes bootstrap diagnostics for issue #1 in `window.__LetterBoxedCubedBootstrapTrace` and `sessionStorage["LetterBoxedCubed_PreviewBootstrapTrace"]`. The trace records `document.wasDiscarded`, navigation type, readiness milestones, and timeout/initialization completion.
- Settings sections remain **FEEDBACK & ANIMATION**, **DISPLAY**, **SYNC** and ordinary settings text/buttons are 12px. Chrome number steppers use a narrower spinner area where supported.
- `Word Log` is temporarily replaced by a bordered square logo placeholder. It displays its current side length in pixels and should remain a perfect square sized to the natural available header height.
- The main LBC header otherwise contains the custom-dictionary control, **Browse History**, and **Settings**. Google Drive state remains light-gray header text.
- Settings copy uses **Hide par**, **Line animation speed**, **New word highlight**, **Compact title layout**, and **Hide Yesterday/Help row**.
- First/Second Hint entries show solved/total Twofer progress for that word in that position, and completed entries are struck through.
- Newly discovered words briefly fade from chartreuse in Found Words and Hints. Their exact Words-by-Length row highlights as well, and newly solved Twofers receive the same effect.
- Completion highlights for every newly discovered dictionary word. Longest Found highlights when the new word establishes a new maximum or ties the current maximum length.
- Words by Length contains one row for every exact word length present in the current dictionary; absent lengths are omitted rather than rolled into `7+`.
- The NYT global header and Letter Boxed title area each have an on-page vertical resize grip. Their Settings values are percentages of native size; 0% hides the region and Reset returns it to 100%.
- **Compact title layout** keeps the game title, date, and byline on a single left-justified row with vertical centers aligned, including when the title region is scaled down.
- **Hide Yesterday/Help row** simply hides the native row containing those controls; it does not clone or proxy Yesterday.

## Automated source commits and stale previews

A normal push to the active development branch triggers the preview workflow automatically. There is one important GitHub Actions edge case: if another workflow commits a source change using the repository's built-in `GITHUB_TOKEN`, GitHub intentionally does not start a second `push` workflow from that generated commit. That prevents accidental workflow recursion, but it also means a preview can become one commit stale after a workflow-authored source patch.

Our rule is therefore:

- Direct human/API commits to the source branch rely on the normal `push` trigger.
- Any workflow that itself commits a source-code change must explicitly dispatch the preview workflow afterward, or the preview must otherwise be rebuilt from the new branch head.
- `PREVIEW_SOURCE.txt` is the audit trail. Its `Source commit` should equal the active source branch head after the preview workflow finishes.

If Tampermonkey says "no updates found" while the source branch contains a newer change, first compare `PREVIEW_SOURCE.txt` with the branch head. In that case Tampermonkey may be completely correct: it is already running the newest file on the `preview` branch, while the `preview` branch itself is stale.

## What the `preview` branch is

The `preview` branch is a generated distribution branch. Do not develop on it and do not merge it into `main`. It contains only:

- `LetterBoxedCubed.preview.user.js`
- `PREVIEW_SOURCE.txt`, recording the source branch and commit

With the current one-active-development-branch convention, the last push becomes the preview. After a PR is merged, the resulting push to `main` rebuilds preview from `main`, so the preview URL automatically falls back to production-equivalent code instead of remaining stale.

## GitHub Actions permissions

The workflow needs permission to write the generated `preview` branch and, on its first LBC run, to commit the tiny hash router into the source branch. If it reports a permissions error, open:

**Repository Settings -> Actions -> General -> Workflow permissions**

and select **Read and write permissions**.

## Data isolation

Production and Preview have different Tampermonkey identities (`@name` + `@namespace`), so their `GM_*` storage is separate. Preview therefore starts with its own LBC data. To test against realistic player history or migrations, use LBC's Export button in Production and Import that backup while running Preview.
