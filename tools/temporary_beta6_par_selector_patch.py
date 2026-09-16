from pathlib import Path

source_path = Path("LetterBoxedCubed.user.js")
text = source_path.read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {count}")
    text = text.replace(old, new, 1)


replace_once(
    "// @version      1.12.0-beta.5",
    "// @version      1.12.0-beta.6",
    "version",
)

replace_once(
    """            .lb-game-container.lb-cubed-hide-par
            .lb-word-container .lb-par {
                display: none !important;
            }""",
    """            /*
                Hide only NYT's actual par prompt. Validation messages such as
                \"Too short\" and \"Not a valid word\" can also use lb-par,
                so a blanket descendant selector incorrectly suppresses them.

                NYT has two prompt DOM shapes:
                - zero words: nested .lb-par.no-words in the text wrapper
                - accepted words: direct-child .lb-par in the word container
            */
            .lb-game-container.lb-cubed-hide-par
            > .lb-word-container
            > .lb-par,
            .lb-game-container.lb-cubed-hide-par
            > .lb-word-container
            > .lb-text-field-wrapper
            > .lb-par.no-words {
                display: none !important;
            }""",
    "Hide par selector",
)

source_path.write_text(text, encoding="utf-8")

changelog_path = Path("CHANGELOG.md")
changelog = changelog_path.read_text(encoding="utf-8")
marker = "# Changelog\n\n"
entry = """## 1.12.0-beta.6
- Narrowed Hide par to the two actual NYT par-prompt DOM shapes so validation feedback such as \"Too short\" and \"Not a valid word\" remains visible.

"""

if entry not in changelog:
    if marker not in changelog:
        raise SystemExit("changelog heading not found")
    changelog = changelog.replace(marker, marker + entry, 1)
    changelog_path.write_text(changelog, encoding="utf-8")
