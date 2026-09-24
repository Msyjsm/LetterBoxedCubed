from pathlib import Path

path = Path("tools/preview_runtime.js")
text = path.read_text(encoding="utf-8")
old = '''        } else {\n            PreviewHistoricalTestModeActive = false;\n            PreviewHistoricalBaseline = null;\n        }\n\n        RenderPanel();\n'''
new = '''        } else {\n            PreviewHistoricalTestModeActive = false;\n            PreviewHistoricalBaseline = null;\n        }\n\n        if (KeepActive) {\n            RecomputePreviewHistoricalSandboxState();\n        }\n\n        RenderPanel();\n'''
count = text.count(old)
if count != 1:
    raise RuntimeError(f"sandbox initial render anchor: expected one match, found {count}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Fixed sandbox initial render to use the neutralized selected-pair state immediately.")
