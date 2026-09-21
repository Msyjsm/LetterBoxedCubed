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
    "// @version      1.12.0-beta.17",
    "// @version      1.12.0-beta.18",
    "version bump",
)

source = replace_once(
    source,
    """    let NytHeaderScale = 1.0;\n    let NytTitleScale = 1.0;\n    let CompactTitleLayout = false;""",
    """    let NytHeaderScale = 1.0;\n    let NytTitleScale = 1.0;\n    let NytFooterScale = 1.0;\n    let CompactTitleLayout = false;""",
    "footer scale state",
)

source = replace_once(
    source,
    """            NytHeaderScale,\n            NytTitleScale,\n            CompactTitleLayout,""",
    """            NytHeaderScale,\n            NytTitleScale,\n            NytFooterScale,\n            CompactTitleLayout,""",
    "footer scale diagnostics",
)

source = replace_once(
    source,
    """        NytTitleScale = GetFiniteGuiNumber(\n            \"NytTitleScale\",\n            1.0,\n            MinimumNytPageScale,\n            MaximumNytPageScale\n        );\n\n        CompactTitleLayout = Boolean(""",
    """        NytTitleScale = GetFiniteGuiNumber(\n            \"NytTitleScale\",\n            1.0,\n            MinimumNytPageScale,\n            MaximumNytPageScale\n        );\n\n        NytFooterScale = GetFiniteGuiNumber(\n            \"NytFooterScale\",\n            1.0,\n            MinimumNytPageScale,\n            MaximumNytPageScale\n        );\n\n        CompactTitleLayout = Boolean(""",
    "load footer scale",
)

source = replace_once(
    source,
    """        DisplaySection.appendChild(GapGroup);\n\n        const SyncSection = CreateSettingsSection(\"Sync\");""",
    """        DisplaySection.appendChild(GapGroup);\n        DisplaySection.appendChild(\n            CreateSettingsNumberWithReset(\n                \"Footer size\",\n                Math.round(NytFooterScale * 100),\n                0,\n                200,\n                1,\n                \"%\",\n                100,\n                \"NytFooterScale\",\n                Value => {\n                    NytFooterScale = Clamp(Value / 100, MinimumNytPageScale, MaximumNytPageScale);\n                    SetGuiSetting(\"NytFooterScale\", NytFooterScale);\n                    ApplyNytPagePreferences();\n                }\n            )\n        );\n\n        const SyncSection = CreateSettingsSection(\"Sync\");""",
    "footer size setting",
)

source = replace_once(
    source,
    """    function GetNytPageTargets() {\n        return {\n            Header: document.querySelector(\"header.pz-header.pz-game-header\"),\n            Title: document.querySelector(\"#letter-boxed-container .pz-game-title-bar\")\n        };\n    }""",
    """    function GetNytPageTargets() {\n        return {\n            Header: document.querySelector(\"header.pz-header.pz-game-header\"),\n            Title: document.querySelector(\"#letter-boxed-container .pz-game-title-bar\"),\n            Footer: document.querySelector(\"footer.pz-footer\")\n        };\n    }""",
    "footer target",
)

source = replace_once(
    source,
    """        ApplyNytElementScale(Targets.Header, NytHeaderScale);\n        ApplyNytElementScale(Targets.Title, NytTitleScale);\n\n        /*\n            NYT normally centers the title bar with auto margins. CSS zoom then\n            changes its used width, so the whole title region appears to shrink\n            toward the middle. Preserve the title bar's native left edge within\n            its parent and let all scaling grow/shrink to the right from there.\n        */\n        if (Targets.Title && NytOriginalTitleLeftOffset !== null) {\n            Targets.Title.style.setProperty(\n                \"margin-left\",\n                `${NytOriginalTitleLeftOffset}px`,\n                \"important\"\n            );\n            Targets.Title.style.setProperty(\n                \"margin-right\",\n                \"auto\",\n                \"important\"\n            );\n        }\n\n        ApplyNytTitleArrangement();""",
    """        ApplyNytElementScale(Targets.Header, NytHeaderScale);\n        ApplyNytElementScale(Targets.Title, NytTitleScale);\n        ApplyNytElementScale(Targets.Footer, NytFooterScale);\n\n        /*\n            NYT normally centers the title bar with auto margins. CSS zoom also\n            scales the margin itself, so a fixed captured margin drifts right as\n            zoom increases. Divide the native offset by the active zoom so its\n            rendered left edge remains fixed while the region grows/shrinks only\n            to the right.\n        */\n        if (Targets.Title && NytOriginalTitleLeftOffset !== null) {\n            const NormalizedTitleScale = Clamp(\n                Number(NytTitleScale) || 0,\n                MinimumNytPageScale,\n                MaximumNytPageScale\n            );\n            const CompensatedLeftOffset = NormalizedTitleScale > 0.001\n                ? NytOriginalTitleLeftOffset / NormalizedTitleScale\n                : 0;\n\n            Targets.Title.style.setProperty(\n                \"margin-left\",\n                `${CompensatedLeftOffset}px`,\n                \"important\"\n            );\n            Targets.Title.style.setProperty(\n                \"margin-right\",\n                \"auto\",\n                \"important\"\n            );\n        }\n\n        ApplyNytTitleArrangement();\n\n        /*\n            Header/title resizing moves LBC vertically without resizing the TI or\n            GB themselves, so their ResizeObserver does not fire. Re-anchor the\n            document-absolute preview controls after the browser has applied the\n            new page geometry.\n        */\n        requestAnimationFrame(() => {\n            PositionPreviewDebugPane();\n            PositionPreviewVersionLabel();\n        });""",
    "title anchor, footer scale, and preview reposition",
)

source = replace_once(
    source,
    """            #letter-boxed-container\n            .pz-section.lb-cubed-compact-title-section {\n                margin-top: 0 !important;\n            }""",
    """            #letter-boxed-container.lb-cubed-compact-title-section {\n                margin-top: 0 !important;\n            }""",
    "compact title section selector",
)

source_path.write_text(source, encoding="utf-8")

changelog_path = Path("CHANGELOG.md")
changelog = changelog_path.read_text(encoding="utf-8")
changelog = replace_once(
    changelog,
    "# Changelog\n\n## 1.12.0-beta.17",
    """# Changelog\n\n## 1.12.0-beta.18\n- Corrected title scaling so the captured native left offset is divided by CSS zoom, keeping the title bar's rendered left edge stationary while it grows/shrinks to the right.\n- Fixed Compact title layout's 24px gap override by targeting the actual `#letter-boxed-container.pz-section` element rather than a nonexistent descendant `.pz-section`.\n- Reposition the preview version label and Show/Hide Debug Pane control after header/title scaling changes so they stay attached to LBC as page geometry moves.\n- Added a bottom-of-Display **Footer size** control (0%-200%, Reset = 100%) that proportionally scales the native `footer.pz-footer` and hides it at 0%.\n\n## 1.12.0-beta.17""",
    "changelog beta.18",
)
changelog_path.write_text(changelog, encoding="utf-8")

docs_path = Path("docs/PREVIEW_TESTING.md")
docs = docs_path.read_text(encoding="utf-8")
docs = replace_once(
    docs,
    "The `feature/qol-4-10-12-13-14` preview bundles issues #4, #5, #10, #12, #13, #14, #16, #17, #18, and #19. The current source is `1.12.0-beta.17`.",
    "The `feature/qol-4-10-12-13-14` preview bundles issues #4, #5, #10, #12, #13, #14, #16, #17, #18, and #19. The current source is `1.12.0-beta.18`.",
    "preview docs source version",
)
docs = replace_once(
    docs,
    "- The NYT global header and Letter Boxed title area each have an on-page vertical resize grip. Their Settings values are percentages of native size; 0% hides the region and Reset returns it to 100%.\n- **Compact title layout** keeps the game title, date, and byline on a single left-justified row with vertical centers aligned, removes the title section's native top margin, and preserves the title bar's native left edge while the region is scaled up or down.",
    "- The NYT global header and Letter Boxed title area each have an on-page vertical resize grip. Their Settings values are percentages of native size; 0% hides the region and Reset returns it to 100%. **Footer size** appears at the bottom of Display and applies the same 0%-200%/Reset behavior to the native NYT Games footer.\n- **Compact title layout** keeps the game title, date, and byline on a single left-justified row with vertical centers aligned, removes the title section's native top margin, and preserves the title bar's rendered native left edge while the region is scaled up or down.",
    "preview docs resize behavior",
)
docs = replace_once(
    docs,
    "- Settings copy uses **Hide par**, **Line animation speed**, **New word highlight**, **Compact title layout**, and **Hide Yesterday/Help row**.",
    "- Settings copy uses **Hide par**, **Line animation speed**, **New word highlight**, **Compact title layout**, **Hide Yesterday/Help row**, and **Footer size**.",
    "preview docs settings copy",
)
docs_path.write_text(docs, encoding="utf-8")
