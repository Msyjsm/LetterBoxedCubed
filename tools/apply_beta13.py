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
    '// @version      1.12.0-beta.12',
    '// @version      1.12.0-beta.13',
    'version'
)

start = source.index('    function GetVisibleHistoryContentBottom(ListContainer) {')
end = source.index('    function QueueValidWordFeedbackPlacement() {', start)
replacement = '''    function GetVisibleHistoryContentBottom(ListContainer) {
        if (!ListContainer) {
            return null;
        }

        /*
            The count label is intentionally outside the scrolling viewport.
            Collision detection therefore measures only the actually visible
            accepted-word content inside .lb-word-list-container.
        */
        const HistoryViewport = ListContainer.querySelector(
            ":scope > .lb-word-list-container"
        );
        const HistoryList = HistoryViewport?.querySelector(
            ":scope > .lb-word-list"
        );

        if (!HistoryViewport || !HistoryList) {
            return null;
        }

        const ViewportRect = HistoryViewport.getBoundingClientRect();
        const ListRect = HistoryList.getBoundingClientRect();

        if (
            ViewportRect.height <= 0 ||
            ListRect.height <= 0 ||
            ListRect.bottom <= ViewportRect.top ||
            ListRect.top >= ViewportRect.bottom
        ) {
            return null;
        }

        return Math.min(
            ListRect.bottom,
            ViewportRect.bottom
        );
    }

    function ClearValidWordFeedbackProxy(Source = null) {
        document.querySelectorAll(".lb-cubed-valid-feedback-proxy")
            .forEach(Element => Element.remove());

        if (Source) {
            Source.classList.remove(
                "lb-cubed-valid-feedback-relocated-source"
            );
        } else {
            document.querySelectorAll(
                ".lb-cubed-valid-feedback-relocated-source"
            ).forEach(Element => Element.classList.remove(
                "lb-cubed-valid-feedback-relocated-source"
            ));
        }
    }

    function UpdateValidWordFeedbackPlacement() {
        ValidFeedbackPlacementFrame = null;

        const GameContainer = document.querySelector(
            ".lb-game-container"
        );
        const WordContainer = GameContainer?.querySelector(
            ":scope > .lb-word-container"
        );
        const TextFieldWrapper = WordContainer?.querySelector(
            ":scope > .lb-text-field-wrapper"
        );
        const ListContainer = WordContainer?.querySelector(
            ":scope > .lb-list-container"
        );
        const SquareContainer = GameContainer?.querySelector(
            ":scope > .lb-square-container"
        );
        const Source = SquareContainer?.querySelector(
            ":scope > .lb-message-box"
        );

        if (
            !GameContainer ||
            !TextFieldWrapper ||
            !ListContainer ||
            !Source
        ) {
            ClearValidWordFeedbackProxy();
            return;
        }

        const MessageText = String(Source.textContent || "").trim();
        if (!MessageText) {
            ClearValidWordFeedbackProxy(Source);
            return;
        }

        const HistoryBottom = GetVisibleHistoryContentBottom(ListContainer);
        if (!Number.isFinite(HistoryBottom)) {
            ClearValidWordFeedbackProxy(Source);
            return;
        }

        const SourceRect = Source.getBoundingClientRect();
        const ShouldRelocate =
            SourceRect.width > 0 &&
            SourceRect.height > 0 &&
            SourceRect.top <
                HistoryBottom + ValidFeedbackHistoryClearance;

        if (!ShouldRelocate) {
            ClearValidWordFeedbackProxy(Source);
            return;
        }

        let Proxy = GameContainer.querySelector(
            ":scope > .lb-cubed-valid-feedback-proxy"
        );

        if (!Proxy) {
            Proxy = document.createElement("div");
            Proxy.className =
                "lb-message-box success-message lb-cubed-valid-feedback-proxy";
            GameContainer.appendChild(Proxy);
        }

        Proxy.replaceChildren(
            ...[...Source.childNodes].map(Node => Node.cloneNode(true))
        );

        /*
            Do not reuse NYT's parent-relative top/bottom coordinates.
            The proxy is a direct child of the positioned game container,
            so place it from live viewport geometry immediately above TI.
        */
        const GameRect = GameContainer.getBoundingClientRect();
        const InputRect = TextFieldWrapper.getBoundingClientRect();
        const ProxyRect = Proxy.getBoundingClientRect();
        const Left =
            ((InputRect.left + InputRect.right) / 2) -
            GameRect.left -
            (ProxyRect.width / 2);
        const Top = Math.max(
            0,
            InputRect.top -
            GameRect.top -
            ProxyRect.height -
            8
        );

        Proxy.style.setProperty(
            "left",
            `${Math.round(Left)}px`,
            "important"
        );
        Proxy.style.setProperty(
            "top",
            `${Math.round(Top)}px`,
            "important"
        );

        Source.classList.add(
            "lb-cubed-valid-feedback-relocated-source"
        );
    }

'''
source = source[:start] + replacement + source[end:]

old_proxy_css = '''            .lb-cubed-valid-feedback-proxy {
                position: absolute !important;
                left: 50% !important;
                right: auto !important;
                top: auto !important;
                bottom: calc(100% + 8px) !important;
                margin: 0 !important;
                transform: translateX(-50%) !important;
                z-index: 5 !important;
                pointer-events: none !important;
            }
'''
new_proxy_css = '''            .lb-cubed-valid-feedback-proxy {
                position: absolute !important;
                right: auto !important;
                bottom: auto !important;
                margin: 0 !important;
                transform: none !important;
                visibility: visible !important;
                display: block !important;
                z-index: 60 !important;
                pointer-events: none !important;
            }
'''
source = once(source, old_proxy_css, new_proxy_css, 'feedback proxy css')

old_scroll_css = '''                overflow-x: hidden !important;
                overflow-y: auto !important;
                pointer-events: auto !important;
                scrollbar-width: thin;
            }

            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-par {
'''
new_scroll_css = '''                display: flex !important;
                flex-direction: column !important;
                overflow: hidden !important;
                pointer-events: auto !important;
            }

            /*
                Keep the count pinned. Only the word-history viewport scrolls,
                eliminating the nested outer+inner scrollbar pair.
            */
            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-list-container
            > .lb-word-list-length {
                flex: 0 0 auto !important;
            }

            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-list-container
            > .lb-word-list-container {
                flex: 1 1 auto !important;
                min-height: 0 !important;
                height: auto !important;
                max-height: none !important;
                overflow-x: hidden !important;
                overflow-y: auto !important;
                pointer-events: auto !important;
                scrollbar-width: thin;
            }

            .lb-game-container.${LayoutClass}
            > .lb-word-container
            > .lb-par {
'''
source = once(source, old_scroll_css, new_scroll_css, 'history scroll ownership')

changelog = once(
    changelog,
    '# Changelog\n\n',
    '# Changelog\n\n## 1.12.0-beta.13\n- Replaced the parent-relative relocated success-toast positioning with a game-container-level proxy placed from live viewport geometry immediately above the text-entry wrapper; the native GB toast is hidden only after the proxy is populated and positioned.\n- Removed the nested history scrollbars: `.lb-list-container` is now a non-scrolling fixed-height flex shell, `.lb-word-list-length` stays pinned, and only `.lb-word-list-container` owns vertical scrolling.\n- Updated toast/history collision measurement to use the inner word-history viewport rather than the outer container that also contains the pinned word count.\n\n',
    'changelog'
)

docs = once(
    docs,
    'The current source is `1.12.0-beta.12`.',
    'The current source is `1.12.0-beta.13`.',
    'docs version'
)
docs = once(
    docs,
    '- `.lb-list-container` is an exact-height scroll viewport matching the reserved history lane. Cubed explicitly re-enables pointer events on that scroller, and the TI grid track includes NYT\'s native TI top/bottom margins so the following GB row starts after the *rendered* TI rather than underneath it. A fixed 22px structural gutter sits between history and GB; the draggable grip line is centered in that gutter.',
    '- `.lb-list-container` is an exact-height non-scrolling flex shell matching the reserved history lane. The word-count label is pinned at the top, while only the nested `.lb-word-list-container` scrolls. The TI grid track includes NYT\'s native TI top/bottom margins so the following GB row starts after the *rendered* TI rather than underneath it. A fixed 22px structural gutter sits between history and GB; the draggable grip line is centered in that gutter.',
    'docs history scroller'
)
docs = once(
    docs,
    '- **Hide par** should hide only the actual `Try to solve in X words` prompt in both NYT DOM states. Invalid-submission feedback injected as `.lb-text-field-wrapper > .lb-message-box` (for example **Too short** and **Not in word list**) must remain visible. Valid-word praise remains native when it has room; if it would crowd visible history, Cubed mirrors it as a `success-message` proxy explicitly positioned above the text-entry wrapper rather than inheriting NYT\'s square-container-relative coordinates.',
    '- **Hide par** should hide only the actual `Try to solve in X words` prompt in both NYT DOM states. Invalid-submission feedback injected as `.lb-text-field-wrapper > .lb-message-box` (for example **Too short** and **Not in word list**) must remain visible. Valid-word praise remains native when it has room; if it would crowd visible history, Cubed mirrors it as a `success-message` proxy attached to the game container and positions that proxy from live geometry immediately above the text-entry wrapper, avoiding NYT\'s parent-relative toast coordinates.',
    'docs toast placement'
)

source_path.write_text(source, encoding='utf-8')
changelog_path.write_text(changelog, encoding='utf-8')
docs_path.write_text(docs, encoding='utf-8')
