from pathlib import Path

path = Path("LetterBoxedCubed.user.js")
text = path.read_text(encoding="utf-8")

replacements = [
    (
        '''            .lb-cubed-settings-suffix {
                min-width: 14px;
                color: rgba(48, 24, 24, 0.68);
                font-size: 11px;''',
        '''            .lb-cubed-settings-suffix {
                min-width: 14px;
                color: rgba(48, 24, 24, 0.68);
                font-size: 12px;''',
        "suffix"
    ),
    (
        '''                color: rgb(48, 24, 24);
                font: inherit;
                font-size: 11px;
                cursor: pointer;
            }

            .lb-cubed-settings-button-row {''',
        '''                color: rgb(48, 24, 24);
                font: inherit;
                font-size: 12px;
                cursor: pointer;
            }

            .lb-cubed-settings-button-row {''',
        "reset button"
    )
]

for old, new, label in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {count}")
    text = text.replace(old, new, 1)

marker = '''            .lb-cubed-settings-button-row {
                display: flex;'''
insert = '''            .lb-cubed-settings-panel .lb-cubed-header-button {
                font-size: 12px;
            }

'''
if text.count(marker) != 1:
    raise SystemExit("settings button marker mismatch")
text = text.replace(marker, insert + marker, 1)

path.write_text(text, encoding="utf-8")
