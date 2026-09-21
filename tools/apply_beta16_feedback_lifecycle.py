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
    '// @version      1.12.0-beta.15',
    '// @version      1.12.0-beta.16',
    'version'
)

source = once(
    source,
    '''    let SquareFeedbackObserver = null;\n    let ValidFeedbackPlacementTimer = null;\n    let RenderedValidFeedbackKey = null;\n    let ScanTimer = null;''',
    '''    let SquareFeedbackObserver = null;\n    let ValidFeedbackPlacementTimer = null;\n    let RenderedValidFeedbackKey = null;\n\n    /*\n        A native success box can appear before NYT commits the accepted word to\n        the history DOM. Do not use the live history count itself as the toast\n        identity: that value changes mid-toast and caused Cubed to recreate the\n        same proxy. Instead, one non-empty native-toast lifecycle owns one\n        monotonic generation.\n    */\n    let ValidFeedbackGeneration = 0;\n    let ActiveValidFeedbackSource = null;\n    let ActiveValidFeedbackText = \"\";\n    let PendingValidFeedbackBaselineChainLength = null;\n    let PendingValidFeedbackStartedAt = 0;\n    const ValidFeedbackSettlePollMs = 30;\n    const ValidFeedbackSettleMaximumMs = 400;\n\n    let ScanTimer = null;''',
    'feedback state declarations'
)

source = once(
    source,
    '''    function ClearValidWordFeedbackProxy(Source = null) {\n        clearTimeout(ValidFeedbackPlacementTimer);\n        ValidFeedbackPlacementTimer = null;\n        RenderedValidFeedbackKey = null;\n\n        document.querySelectorAll(\".lb-cubed-valid-feedback-proxy\")''',
    '''    function ClearValidWordFeedbackProxy(Source = null) {\n        clearTimeout(ValidFeedbackPlacementTimer);\n        ValidFeedbackPlacementTimer = null;\n        RenderedValidFeedbackKey = null;\n        ActiveValidFeedbackSource = null;\n        ActiveValidFeedbackText = \"\";\n        PendingValidFeedbackBaselineChainLength = null;\n        PendingValidFeedbackStartedAt = 0;\n\n        document.querySelectorAll(\".lb-cubed-valid-feedback-proxy\")''',
    'feedback clear state'
)

source = once(
    source,
    '''        /*\n            Accepted count is the stable identity of one valid submission.\n            NYT can mutate/re-render the same toast more than once while that\n            submission settles. Keeping the same key prevents Cubed from\n            recreating the proxy and restarting its fade. The next accepted\n            word increments the count, intentionally creating one fresh toast.\n        */\n        const FeedbackKey =\n            `${ReadCurrentChain().length}\\u001F${MessageText}`;''',
    '''        /*\n            Wait until NYT has committed the accepted word to history before\n            making Cubed's proxy visible. The native box appears first; the\n            history DOM can lag it by a couple hundred milliseconds. Showing\n            the proxy before that commit made it appear in the old normal\n            position and then jump above TI when wrapping finally settled.\n\n            The 400ms ceiling is only a safety fallback for an unexpected NYT\n            state where the history count does not advance.\n        */\n        const CurrentChainLength = ReadCurrentChain().length;\n        const WaitingForHistoryCommit =\n            PendingValidFeedbackBaselineChainLength !== null &&\n            CurrentChainLength <= PendingValidFeedbackBaselineChainLength &&\n            (performance.now() - PendingValidFeedbackStartedAt) <\n                ValidFeedbackSettleMaximumMs;\n\n        if (WaitingForHistoryCommit) {\n            ValidFeedbackPlacementTimer = setTimeout(\n                UpdateValidWordFeedbackPlacement,\n                ValidFeedbackSettlePollMs\n            );\n            return;\n        }\n\n        PendingValidFeedbackBaselineChainLength = null;\n\n        /*\n            One native-toast lifecycle is one submission identity. Unlike the\n            old live-chain-length key, this generation cannot change halfway\n            through NYT's delayed history update.\n        */\n        const FeedbackKey =\n            `${ValidFeedbackGeneration}\\u001F${MessageText}`;''',
    'feedback identity and settle gate'
)

source = once(
    source,
    '''    function QueueValidWordFeedbackPlacement() {\n        const Source = GetNativeValidWordFeedbackSource();\n\n        if (Source) {\n            /*\n                MutationObserver callbacks run before paint, so this is an\n                additional guard on top of the CSS selector that suppresses\n                native praise immediately. The visible proxy is deliberately\n                delayed until NYT has inserted the accepted word and wrapping\n                has settled.\n            */\n            Source.classList.add(\n                \"lb-cubed-valid-feedback-relocated-source\"\n            );\n        }\n\n        clearTimeout(ValidFeedbackPlacementTimer);\n        ValidFeedbackPlacementTimer = setTimeout(\n            UpdateValidWordFeedbackPlacement,\n            60\n        );\n    }''',
    '''    function QueueValidWordFeedbackPlacement() {\n        const Source = GetNativeValidWordFeedbackSource();\n        const MessageText = String(Source?.textContent || \"\").trim();\n\n        if (Source) {\n            /*\n                MutationObserver callbacks run before paint, so this is an\n                additional guard on top of the CSS selector that suppresses\n                native praise immediately.\n            */\n            Source.classList.add(\n                \"lb-cubed-valid-feedback-relocated-source\"\n            );\n        }\n\n        if (Source && MessageText) {\n            const StartsNewLifecycle =\n                ActiveValidFeedbackSource !== Source ||\n                !ActiveValidFeedbackText;\n\n            if (StartsNewLifecycle) {\n                ActiveValidFeedbackSource = Source;\n                ActiveValidFeedbackText = MessageText;\n                ValidFeedbackGeneration++;\n                PendingValidFeedbackBaselineChainLength =\n                    ReadCurrentChain().length;\n                PendingValidFeedbackStartedAt = performance.now();\n            } else {\n                ActiveValidFeedbackText = MessageText;\n            }\n        }\n\n        clearTimeout(ValidFeedbackPlacementTimer);\n        ValidFeedbackPlacementTimer = setTimeout(\n            UpdateValidWordFeedbackPlacement,\n            60\n        );\n    }''',
    'queue feedback lifecycle'
)

changelog = once(
    changelog,
    '# Changelog\n\n',
    '''# Changelog\n\n## 1.12.0-beta.16\n- Fixed the remaining double-toast/re-fade bug: Cubed no longer keys a valid-word toast to the live accepted-word count, which changes while NYT asynchronously commits the same accepted word to history. One non-empty native-toast lifecycle now owns one monotonic proxy generation.\n- Cubed now keeps its praise proxy hidden until the accepted-word history count advances (with a 400ms safety ceiling), then measures the settled history geometry once and reveals the proxy in its final location. This prevents the normal-position flash followed by a jump above TI when a submission creates a new wrapped history line.\n\n''',
    'changelog'
)

docs = once(
    docs,
    'The current source is `1.12.0-beta.15`.',
    'The current source is `1.12.0-beta.16`.',
    'docs version'
)

docs = once(
    docs,
    '''NYT's native praise box is suppressed immediately by DOM location even before NYT adds its later `success-message` class. Cubed waits 60ms for accepted-word wrapping to settle, then either mirrors the hidden native box's final rendered position or moves the proxy above TI if history would collide. One accepted submission owns one proxy/fade even if NYT mutates the native toast repeatedly.''',
    '''NYT's native praise box is suppressed immediately by DOM location even before NYT adds its later `success-message` class. Cubed records one native-toast lifecycle as one submission generation, waits until NYT's accepted-word history count actually advances (up to a 400ms safety ceiling), then either mirrors the hidden native box's final rendered position or moves the proxy above TI if history would collide. The proxy is not recreated merely because the live chain count changes during that same submission.''',
    'docs feedback lifecycle'
)

source_path.write_text(source, encoding='utf-8')
changelog_path.write_text(changelog, encoding='utf-8')
docs_path.write_text(docs, encoding='utf-8')
