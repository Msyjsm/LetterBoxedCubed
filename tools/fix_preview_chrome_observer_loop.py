from pathlib import Path

path = Path("tools/preview_runtime.js")
text = path.read_text(encoding="utf-8")
old = '''            const ElementNode = document.getElementById(Id);\n            if (ElementNode) {\n                ElementNode.style.visibility = Hide ? "hidden" : "";\n            }\n'''
new = '''            const ElementNode = document.getElementById(Id);\n            if (ElementNode) {\n                const DesiredVisibility = Hide ? "hidden" : "";\n                if (ElementNode.style.visibility !== DesiredVisibility) {\n                    ElementNode.style.visibility = DesiredVisibility;\n                }\n            }\n'''
count = text.count(old)
if count != 1:
    raise RuntimeError(f"modal observer visibility guard: expected one match, found {count}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Hardened preview native-modal observer against self-trigger loops.")
