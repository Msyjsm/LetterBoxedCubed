from pathlib import Path

path = Path("tools/apply_v1_13_beta2_history_parity.py")
text = path.read_text(encoding="utf-8")
old = '''tests = replace_once(
    tests,
    \'\'\'      BuildGlobalWordRecord, MergeGlobalWordHistoryValues,\n      RebuildGlobalWordHistoryFromTrackerStorage\n\'\'\',
    \'\'\'      BuildGlobalWordRecord, MergeGlobalWordHistoryValues,\n      RebuildGlobalWordHistoryFromTrackerStorage,\n      HistoricalWordProjectionStorageKey, HistoricalWordProjectionVersion,\n      BuildHistoricalWordProjection, MergeHistoricalWordProjectionValues,\n      ShouldHighlightWordDiscovery\n\'\'\',
    "test exports beta2 helpers",
)
'''
new = '''tests = replace_once(
    tests,
    "      BuildGlobalWordRecord, MergeGlobalWordHistoryValues,\\\\n"
    "      RebuildGlobalWordHistoryFromTrackerStorage\\\\n",
    "      BuildGlobalWordRecord, MergeGlobalWordHistoryValues,\\\\n"
    "      RebuildGlobalWordHistoryFromTrackerStorage,\\\\n"
    "      HistoricalWordProjectionStorageKey, HistoricalWordProjectionVersion,\\\\n"
    "      BuildHistoricalWordProjection, MergeHistoricalWordProjectionValues,\\\\n"
    "      ShouldHighlightWordDiscovery\\\\n",
    "test exports beta2 helpers",
)
'''
if text.count(old) != 1:
    raise RuntimeError(f"expected one beta2 test-anchor block, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
