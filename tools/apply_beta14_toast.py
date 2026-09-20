from pathlib import Path

SOURCE_PATH = Path("LetterBoxedCubed.user.js")
CHANGELOG_PATH = Path("CHANGELOG.md")
DOCS_PATH = Path("docs/PREVIEW_TESTING.md")

source = SOURCE_PATH.read_text(encoding="utf-8")
changelog = CHANGELOG_PATH.read_text(encoding="utf-8")
docs = DOCS_PATH.read_text(encoding="utf-8")


def once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


source = once(
    source,
    "// @version      1.12.0-beta.13",
    "// @version      1.12.0-beta.14",
    "version",
)

source = once(
    source,
    "    let ValidFeedbackPlacementFrame = null;\n",
    "    let ValidFeedbackPlacementTimer = null;\n"
    "    let RenderedValidFeedbackKey = null;\n",
    "feedback state",
)

start = source.index("    function ClearValidWordFeedbackProxy(Source = null) {")
end = source.index("    function StartSubmissionHooks() {", start)
replacement = r'''    function GetNativeValidWordFeedbackSource() {
        return document.querySelector(
            ".lb-game-container > .lb-square-container > .lb-message-box.success-message"
        );
    }

    function ClearValidWordFeedbackProxy(Source = null) {
        clearTimeout(ValidFeedbackPlacementTimer);
        ValidFeedbackPlacementTimer = null;
        RenderedValidFeedbackKey = null;

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

    function PositionValidWordFeedbackProxy(
        Proxy,
        Source,
        GameContainer,
        TextFieldWrapper,
        ListContainer
    ) {
        const GameRect = GameContainer.getBoundingClientRect();
        const InputRect = TextFieldWrapper.getBoundingClientRect();
        const SourceRect = Source.getBoundingClientRect();
        const ProxyRect = Proxy.getBoundingClientRect();
        const HistoryBottom = GetVisibleHistoryContentBottom(ListContainer);

        const ShouldRelocate =
            Number.isFinite(HistoryBottom) &&
            SourceRect.width > 0 &&
            SourceRect.height > 0 &&
            SourceRect.top <
                HistoryBottom + ValidFeedbackHistoryClearance;

        let Left;
        let Top;

        if (ShouldRelocate) {
            Left =
                ((InputRect.left + InputRect.right) / 2) -
                GameRect.left -
                (ProxyRect.width / 2);
            Top = Math.max(
                0,
                InputRect.top -
                GameRect.top -
                ProxyRect.height -
                8
            );
        } else {
            /*
                Native praise is always suppressed while Cubed controls TI/GB.
                When there is no collision, reproduce NYT's final rendered
                position exactly rather than briefly showing NYT's own box.
            */
            Left = SourceRect.left - GameRect.left;
            Top = SourceRect.top - GameRect.top;
        }

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
    }

    function UpdateValidWordFeedbackPlacement() {
        ValidFeedbackPlacementTimer = null;

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
        const Source = GetNativeValidWordFeedbackSource();

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

        /*
            Accepted count is the stable identity of one valid submission.
            NYT can mutate/re-render the same toast more than once while that
            submission settles. Keeping the same key prevents Cubed from
            recreating the proxy and restarting its fade. The next accepted
            word increments the count, intentionally creating one fresh toast.
        */
        const FeedbackKey =
            `${ReadCurrentChain().length}\u001F${MessageText}`;

        let Proxy = GameContainer.querySelector(
            ":scope > .lb-cubed-valid-feedback-proxy"
        );

        if (!Proxy || RenderedValidFeedbackKey !== FeedbackKey) {
            Proxy?.remove();

            Proxy = document.createElement("div");
            Proxy.className =
                "lb-message-box success-message lb-cubed-valid-feedback-proxy";
            Proxy.replaceChildren(
                ...[...Source.childNodes].map(Node => Node.cloneNode(true))
            );
            GameContainer.appendChild(Proxy);
            RenderedValidFeedbackKey = FeedbackKey;
        }

        PositionValidWordFeedbackProxy(
            Proxy,
            Source,
            GameContainer,
            TextFieldWrapper,
            ListContainer
        );

        Source.classList.add(
            "lb-cubed-valid-feedback-relocated-source"
        );
    }

    function QueueValidWordFeedbackPlacement() {
        const Source = GetNativeValidWordFeedbackSource();

        if (Source) {
            /*
                MutationObserver callbacks run before paint, so this is an
                additional guard on top of the CSS selector that suppresses
                native praise immediately. The visible proxy is deliberately
                delayed until NYT has inserted the accepted word and wrapping
                has settled.
            */
            Source.classList.add(
                "lb-cubed-valid-feedback-relocated-source"
            );
        }

        clearTimeout(ValidFeedbackPlacementTimer);
        ValidFeedbackPlacementTimer = setTimeout(
            UpdateValidWordFeedbackPlacement,
            60
        );
    }

    function StartSquareFeedbackObserver() {
        const SquareContainer = document.querySelector(
            ".lb-game-container .lb-square-container"
        );

        if (!SquareContainer) {
            return;
        }

        SquareFeedbackObserver?.disconnect();
        SquareFeedbackObserver = new MutationObserver(
            QueueValidWordFeedbackPlacement
        );
        SquareFeedbackObserver.observe(SquareContainer, {
            childList: true,
            subtree: true,
            characterData: true
        });

        QueueValidWordFeedbackPlacement();
    }

'''
source = source[:start] + replacement + source[end:]

source = once(
    source,
    '''            .lb-cubed-valid-feedback-relocated-source {
                visibility: hidden !important;
                pointer-events: none !important;
            }

            .lb-cubed-valid-feedback-proxy {
''',
    '''            /*
                Cubed is the sole renderer for valid-word praise. Hiding the
                native success box by selector prevents even a single paint in
                NYT's pre-wrap position before the delayed placement decision.
                visibility:hidden preserves its geometry for normal-position
                mirroring.
            */
            .lb-game-container.${LayoutClass}
            > .lb-square-container
            > .lb-message-box.success-message,
            .lb-cubed-valid-feedback-relocated-source {
                visibility: hidden !important;
                pointer-events: none !important;
            }

            .lb-cubed-valid-feedback-proxy {
''',
    "native toast suppression css",
)

changelog = once(
    changelog,
    "# Changelog\n\n",
    '''# Changelog\n\n## 1.12.0-beta.14\n- Made Cubed the sole renderer of valid-word praise while its TI/GB layout is active: NYT's native success box is suppressed before paint, then a proxy appears after a 60ms settle delay so accepted-word wrapping is already final before placement is chosen.\n- Added stable per-submission toast identity using accepted-word count plus message text. Repeated NYT mutations for the same accepted word now reposition the existing proxy instead of recreating it and restarting the fade.\n- When relocation is unnecessary, the proxy mirrors NYT's final rendered toast rectangle; when history would collide, it uses Cubed's above-TI position.\n\n''',
    "changelog",
)

docs = once(
    docs,
    "The current source is `1.12.0-beta.13`.",
    "The current source is `1.12.0-beta.14`.",
    "docs version",
)

docs = once(
    docs,
    "Valid-word praise remains native when it has room; if it would crowd visible history, Cubed mirrors it as a `success-message` proxy attached to the game container and positions that proxy from live geometry immediately above the text-entry wrapper, avoiding NYT's parent-relative toast coordinates.",
    "Valid-word praise is now always rendered through Cubed's game-container-level proxy while the custom TI/GB layout is active. NYT's native success box is hidden before paint, Cubed waits 60ms for accepted-word wrapping to settle, then either mirrors NYT's final rendered position or moves the proxy above TI if history would collide. One accepted submission owns one proxy/fade even if NYT mutates the native toast repeatedly.",
    "docs toast description",
)

for needle in [
    "// @version      1.12.0-beta.14",
    "let ValidFeedbackPlacementTimer = null;",
    "const FeedbackKey =",
    "setTimeout(\n            UpdateValidWordFeedbackPlacement,\n            60",
    "> .lb-message-box.success-message,",
]:
    if needle not in source:
        raise RuntimeError(f"missing expected beta.14 marker: {needle}")

SOURCE_PATH.write_text(source, encoding="utf-8")
CHANGELOG_PATH.write_text(changelog, encoding="utf-8")
DOCS_PATH.write_text(docs, encoding="utf-8")
