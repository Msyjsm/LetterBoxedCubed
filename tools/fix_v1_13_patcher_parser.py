from pathlib import Path

path = Path("tools/apply_v1_13_global_word_memory.py")
text = path.read_text(encoding="utf-8")

old_parser = '''    brace = text.find("{", start)\n    if brace < 0:\n        raise RuntimeError(f"function {name}: opening brace not found")\n\n    depth = 1\n'''
new_parser = '''    paren = text.find("(", start)\n    if paren < 0:\n        raise RuntimeError(f"function {name}: parameter list not found")\n\n    paren_depth = 0\n    signature_end = None\n    for j in range(paren, len(text)):\n        if text[j] == "(":\n            paren_depth += 1\n        elif text[j] == ")":\n            paren_depth -= 1\n            if paren_depth == 0:\n                signature_end = j\n                break\n\n    if signature_end is None:\n        raise RuntimeError(f"function {name}: parameter list did not close")\n\n    brace = text.find("{", signature_end + 1)\n    if brace < 0:\n        raise RuntimeError(f"function {name}: opening brace not found")\n\n    depth = 1\n'''
if text.count(old_parser) != 1:
    raise RuntimeError(f"parser patch expected one target, found {text.count(old_parser)}")
text = text.replace(old_parser, new_parser, 1)

old_test_block = '''    "      CustomDictionaryStorageKey, CustomWordsPrefix, PuzzleMetadataPrefix\\n",\n    "      CustomDictionaryStorageKey, CustomWordsPrefix, PuzzleMetadataPrefix,\\n"\n    "      GlobalWordHistoryStorageKey, GlobalWordHistoryVersion,\\n"\n    "      BuildGlobalWordRecord, MergeGlobalWordHistoryValues,\\n"\n    "      RebuildGlobalWordHistoryFromTrackerStorage\\n",\n'''
new_test_block = '''    "      CustomDictionaryStorageKey, CustomWordsPrefix, PuzzleMetadataPrefix\\\\n",\n    "      CustomDictionaryStorageKey, CustomWordsPrefix, PuzzleMetadataPrefix,\\\\n"\n    "      GlobalWordHistoryStorageKey, GlobalWordHistoryVersion,\\\\n"\n    "      BuildGlobalWordRecord, MergeGlobalWordHistoryValues,\\\\n"\n    "      RebuildGlobalWordHistoryFromTrackerStorage\\\\n",\n'''
if text.count(old_test_block) != 1:
    raise RuntimeError(f"test escaping patch expected one target, found {text.count(old_test_block)}")
text = text.replace(old_test_block, new_test_block, 1)

path.write_text(text, encoding="utf-8")
