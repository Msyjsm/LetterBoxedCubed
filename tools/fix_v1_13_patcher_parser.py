from pathlib import Path

path = Path("tools/apply_v1_13_global_word_memory.py")
text = path.read_text(encoding="utf-8")
old = '''    brace = text.find("{", start)\n    if brace < 0:\n        raise RuntimeError(f"function {name}: opening brace not found")\n\n    depth = 1\n'''
new = '''    paren = text.find("(", start)\n    if paren < 0:\n        raise RuntimeError(f"function {name}: parameter list not found")\n\n    paren_depth = 0\n    signature_end = None\n    for j in range(paren, len(text)):\n        if text[j] == "(":\n            paren_depth += 1\n        elif text[j] == ")":\n            paren_depth -= 1\n            if paren_depth == 0:\n                signature_end = j\n                break\n\n    if signature_end is None:\n        raise RuntimeError(f"function {name}: parameter list did not close")\n\n    brace = text.find("{", signature_end + 1)\n    if brace < 0:\n        raise RuntimeError(f"function {name}: opening brace not found")\n\n    depth = 1\n'''
if text.count(old) != 1:
    raise RuntimeError(f"parser patch expected one target, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
