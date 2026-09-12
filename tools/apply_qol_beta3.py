from pathlib import Path
import re

path = Path("LetterBoxedCubed.user.js")
text = path.read_text(encoding="utf-8")


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {count}")
    text = text.replace(old, new, 1)


def sub_once(pattern, replacement, label):
    global text
    text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 regex match, found {count}")


replace_once(
    "// @version      1.12.0-beta.2",
    "// @version      1.12.0-beta.3",
    "version"
)

replace_once(
    '''            .lb-game-container.${SideModeClass} > #${PanelId} {
                grid-column: 2 !important;
                grid-row: 1 / span 2 !important;
                position: relative;
                align-self: stretch;
                width: var(--lb-cubed-panel-width) !important;
                min-width: var(--lb-cubed-panel-width) !important;
                max-width: var(--lb-cubed-panel-width) !important;
                min-height: 0;
            }''',
    '''            .lb-game-container.${SideModeClass} > #${PanelId} {
                grid-column: 2 !important;
                grid-row: 1 / span 2 !important;
                position: absolute !important;
                inset: 0;
                align-self: stretch;
                justify-self: stretch;
                width: var(--lb-cubed-panel-width) !important;
                min-width: var(--lb-cubed-panel-width) !important;
                max-width: var(--lb-cubed-panel-width) !important;
                height: auto !important;
                min-height: 0;
                max-height: none !important;
            }''',
    "side panel decoupling"
)

sub_once(
    r'''        const Title = document\.createElement\("h2"\);\n        Title\.className = "lb-cubed-title";\n        Title\.textContent = "Word Log";\n\n        const DriveStatus''',
    '''        const LogoPlaceholder = document.createElement("div");
        LogoPlaceholder.className = "lb-cubed-logo-placeholder";
        LogoPlaceholder.setAttribute("aria-label", "Letter Boxed Cubed logo placeholder");

        const LogoSize = document.createElement("span");
        LogoSize.className = "lb-cubed-logo-placeholder-size";
        LogoPlaceholder.appendChild(LogoSize);

        const DriveStatus''',
    "header title placeholder"
)

replace_once(
    '''        const TitleRow = document.createElement("div");
        TitleRow.className = "lb-cubed-title-row";
        TitleRow.append(Title, DriveStatus);''',
    '''        const TitleRow = document.createElement("div");
        TitleRow.className = "lb-cubed-title-row";
        TitleRow.append(LogoPlaceholder, DriveStatus);''',
    "header title row"
)

replace_once(
    '''        Panel.appendChild(Header);
        UpdateGoogleDriveButton();
    }''',
    '''        Panel.appendChild(Header);
        UpdateGoogleDriveButton();
        UpdateLogoPlaceholderSize(Header, LogoPlaceholder, HeaderActions, LogoSize);
    }

    function UpdateLogoPlaceholderSize(Header, Placeholder, HeaderActions, SizeText) {
        if (!Header || !Placeholder || !HeaderActions || !SizeText) {
            return;
        }

        const Measure = () => {
            if (!Header.isConnected || !Placeholder.isConnected) {
                return;
            }

            Placeholder.style.width = "0px";
            Placeholder.style.height = "0px";

            requestAnimationFrame(() => {
                if (!Header.isConnected || !Placeholder.isConnected) {
                    return;
                }

                const HeaderHeight = Math.ceil(Header.getBoundingClientRect().height);
                const ActionHeight = Math.ceil(HeaderActions.getBoundingClientRect().height);
                const Side = Math.max(20, Math.min(96, Math.max(HeaderHeight, ActionHeight)));

                Placeholder.style.width = `${Side}px`;
                Placeholder.style.height = `${Side}px`;
                SizeText.textContent = `${Side}px`;
            });
        };

        Measure();

        if (typeof ResizeObserver !== "undefined") {
            const Observer = new ResizeObserver(Measure);
            Observer.observe(HeaderActions);
        }

        window.addEventListener("resize", Measure);
    }''',
    "logo sizing helper"
)

replace_once(
    '''            .lb-cubed-settings-section-title {
                margin-bottom: 5px;
                color: rgb(48, 24, 24);
                font-size: 10px;''',
    '''            .lb-cubed-settings-section-title {
                margin-bottom: 5px;
                color: rgb(48, 24, 24);
                font-size: 12px;''',
    "settings section title size"
)

replace_once(
    '''            .lb-cubed-settings-subgroup-title {
                margin-bottom: 2px;
                color: rgba(48, 24, 24, 0.82);
                font-size: 10px;''',
    '''            .lb-cubed-settings-subgroup-title {
                margin-bottom: 2px;
                color: rgba(48, 24, 24, 0.82);
                font-size: 12px;''',
    "settings subgroup title size"
)

replace_once(
    '''                min-height: 28px;
                color: rgb(48, 24, 24);
                font-size: 10px;
            }

            .lb-cubed-settings-checkbox {''',
    '''                min-height: 30px;
                color: rgb(48, 24, 24);
                font-size: 12px;
            }

            .lb-cubed-settings-checkbox {''',
    "settings row size"
)

replace_once(
    '''            .lb-cubed-settings-number-wrap input {
                width: 62px;
                padding: 2px 3px;''',
    '''            .lb-cubed-settings-number-wrap input {
                width: 62px;
                padding: 2px 2px 2px 3px;''',
    "number input padding"
)

spinner_marker = '''            .lb-cubed-settings-suffix {'''
spinner_css = '''            .lb-cubed-settings-number-wrap input[type="number"]::-webkit-inner-spin-button,
            .lb-cubed-settings-number-wrap input[type="number"]::-webkit-outer-spin-button {
                margin: 0;
                width: 11px;
                height: 16px;
            }

'''
replace_once(spinner_marker, spinner_css + spinner_marker, "spinner styling")

replace_once(
    '''            .lb-cubed-settings-suffix {
                min-width: 14px;
                color: rgba(48, 24, 24, 0.68);
                font-size: 9px;''',
    '''            .lb-cubed-settings-suffix {
                min-width: 14px;
                color: rgba(48, 24, 24, 0.68);
                font-size: 11px;''',
    "suffix size"
)

replace_once(
    '''                color: rgb(48, 24, 24);
                font: inherit;
                font-size: 9px;
                cursor: pointer;
            }

            .lb-cubed-settings-button-row {''',
    '''                color: rgb(48, 24, 24);
                font: inherit;
                font-size: 11px;
                cursor: pointer;
            }

            .lb-cubed-settings-button-row {''',
    "reset button size"
)

sub_once(
    r'''            \.lb-cubed-title \{.*?\n            \}\n\n            \.lb-cubed-subtitle''',
    '''            .lb-cubed-logo-placeholder {
                flex: 0 0 auto;
                display: grid;
                place-items: center;
                width: 28px;
                height: 28px;
                border: 1px solid rgba(76, 34, 34, 0.78);
                background: rgba(255, 255, 255, 0.08);
                color: rgba(48, 24, 24, 0.78);
                font-family: Consolas, "Courier New", monospace;
                font-size: 9px;
                font-weight: 700;
                line-height: 1;
                white-space: nowrap;
            }

            .lb-cubed-logo-placeholder-size {
                pointer-events: none;
            }

            .lb-cubed-subtitle''',
    "logo placeholder styles"
)

path.write_text(text, encoding="utf-8")
