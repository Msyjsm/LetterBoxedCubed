from pathlib import Path


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


source_path = Path("LetterBoxedCubed.user.js")
source = source_path.read_text(encoding="utf-8")
source = replace_once(
    source,
    "// @version      1.12.1",
    "// @version      1.12.2",
    "version bump",
)
source = replace_once(
    source,
    """            if (!Canvas?.isConnected) {\n                return;\n            }\n\n            const Context = Canvas.getContext(\"2d\");""",
    """            /*\n                A canvas may be painted before it is connected to the DOM; its\n                bitmap is retained when it is appended later. RenderHeader()\n                intentionally starts PNG decoding while constructing the header,\n                so do not gate drawing on Canvas.isConnected. The previous guard\n                made the async decode race the later DOM append and could leave\n                a permanently transparent logo canvas.\n            */\n            const Context = Canvas.getContext(\"2d\");""",
    "remove premature isConnected guard",
)
source_path.write_text(source, encoding="utf-8")

changelog_path = Path("CHANGELOG.md")
changelog = changelog_path.read_text(encoding="utf-8")
changelog = replace_once(
    changelog,
    "# Changelog\n\n## 1.12.1",
    """# Changelog\n\n## 1.12.2\n- Fixed the embedded-logo canvas remaining transparent when PNG decoding completed before the newly constructed canvas had been attached to the DOM. Canvas pixels can be drawn while detached and persist after insertion, so logo rendering no longer depends on `Canvas.isConnected`.\n\n## 1.12.1""",
    "changelog 1.12.2",
)
changelog_path.write_text(changelog, encoding="utf-8")
