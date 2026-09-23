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
    "// @version      1.12.0",
    "// @version      1.12.1",
    "version bump",
)

source = replace_once(
    source,
    '    const LogoPngDataUrl =\n        "data:image/png;base64,',
    '    const LogoPngBase64 =\n        "',
    "logo data constant",
)

old_logo_creation = '''        const Logo = document.createElement("img");
        Logo.className = "lb-cubed-logo";
        Logo.src = LogoPngDataUrl;
        Logo.alt = "Letter Boxed Cubed";
        Logo.draggable = false;
'''
new_logo_creation = '''        const Logo = document.createElement("canvas");
        Logo.className = "lb-cubed-logo";
        Logo.width = 300;
        Logo.height = 300;
        Logo.setAttribute("role", "img");
        Logo.setAttribute("aria-label", "Letter Boxed Cubed");
        DrawEmbeddedLogo(Logo);
'''
source = replace_once(
    source,
    old_logo_creation,
    new_logo_creation,
    "logo element creation",
)

anchor = '''    function RenderHeader(Panel) {
'''
helper = '''    let LogoBitmapPromise = null;

    function GetEmbeddedLogoBitmap() {
        if (!LogoBitmapPromise) {
            LogoBitmapPromise = (async () => {
                const Binary = atob(LogoPngBase64);
                const Bytes = new Uint8Array(Binary.length);

                for (let Index = 0; Index < Binary.length; Index++) {
                    Bytes[Index] = Binary.charCodeAt(Index);
                }

                const BlobValue = new Blob(
                    [Bytes],
                    { type: "image/png" }
                );

                /*
                    Deliberately decode the embedded PNG as a Blob rather than
                    assigning a data: URL to an <img>. NYT's page CSP can block
                    data-image loads created by page DOM, which Chrome then
                    replaces with its stretched broken-image glyph. Decoding
                    locally with createImageBitmap performs no page image fetch
                    and therefore avoids that CSP path entirely.
                */
                return createImageBitmap(BlobValue);
            })();
        }

        return LogoBitmapPromise;
    }

    async function DrawEmbeddedLogo(Canvas) {
        try {
            const Bitmap = await GetEmbeddedLogoBitmap();

            if (!Canvas?.isConnected) {
                return;
            }

            const Context = Canvas.getContext("2d");
            if (!Context) {
                return;
            }

            if (
                Canvas.width !== Bitmap.width ||
                Canvas.height !== Bitmap.height
            ) {
                Canvas.width = Bitmap.width;
                Canvas.height = Bitmap.height;
            }

            Context.clearRect(
                0,
                0,
                Canvas.width,
                Canvas.height
            );
            Context.drawImage(
                Bitmap,
                0,
                0,
                Canvas.width,
                Canvas.height
            );
        } catch (ErrorValue) {
            console.warn(
                "[Letter Boxed Cubed] Could not decode embedded logo PNG.",
                ErrorValue
            );
        }
    }

'''
source = replace_once(
    source,
    anchor,
    helper + anchor,
    "logo decode helpers",
)

source = replace_once(
    source,
    '''                background: transparent;\n                object-fit: contain;\n                user-select: none;''',
    '''                background: transparent;\n                image-rendering: auto;\n                user-select: none;''',
    "logo canvas CSS",
)

source_path.write_text(source, encoding="utf-8")

changelog_path = Path("CHANGELOG.md")
changelog = changelog_path.read_text(encoding="utf-8")
changelog = replace_once(
    changelog,
    "# Changelog\n\n## 1.12.0",
    """# Changelog\n\n## 1.12.1\n- Fixed the temporary cube logo rendering as Chrome's broken-image placeholder on NYT. The PNG remains embedded byte-for-byte, but LBC now decodes it locally with `createImageBitmap()` and paints it to a canvas instead of assigning a CSP-blockable `data:` URL to an `<img>`.\n- The logo canvas keeps the existing responsive square sizing logic, transparency, and 20-96px display range without external hosting or CORS dependencies.\n\n## 1.12.0""",
    "changelog 1.12.1",
)
changelog_path.write_text(changelog, encoding="utf-8")
