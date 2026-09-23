from pathlib import Path
import base64
import hashlib
import re
import struct
import zlib

EXPECTED_BASE64 = """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"""
EXPECTED_SHA256 = "4198a3a363878ed16e09937ccc71a5277bd4fd431ac4cbed1508a5bb70b1402f"
EXPECTED_BYTE_LENGTH = 4406
EXPECTED_BASE64_LENGTH = 5876


def validate_png_bytes(data: bytes) -> None:
    if len(data) != EXPECTED_BYTE_LENGTH:
        raise RuntimeError(f"logo length mismatch: {len(data)}")
    if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
        raise RuntimeError("logo SHA-256 mismatch")
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError("logo is not a PNG")

    pos = 8
    saw_iend = False
    while pos < len(data):
        if pos + 12 > len(data):
            raise RuntimeError("truncated PNG chunk")
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        chunk_type = data[pos + 4:pos + 8]
        end = pos + 12 + length
        if end > len(data):
            raise RuntimeError("PNG chunk extends past EOF")
        payload = data[pos + 8:pos + 8 + length]
        stored_crc = struct.unpack(">I", data[pos + 8 + length:end])[0]
        crc = zlib.crc32(chunk_type)
        crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
        if crc != stored_crc:
            raise RuntimeError(f"PNG CRC failure in {chunk_type!r}")
        pos = end
        if chunk_type == b"IEND":
            saw_iend = True
            break

    if not saw_iend or pos != len(data):
        raise RuntimeError("PNG IEND/EOF mismatch")


if len(EXPECTED_BASE64) != EXPECTED_BASE64_LENGTH:
    raise RuntimeError("embedded source Base64 literal has changed length")
expected_bytes = base64.b64decode(EXPECTED_BASE64, validate=True)
validate_png_bytes(expected_bytes)

source_path = Path("LetterBoxedCubed.user.js")
source = source_path.read_text(encoding="utf-8")

match = re.search(
    r'(const LogoPngBase64\s*=\s*\n\s*")([A-Za-z0-9+/=]+)(";)',
    source,
)
if not match:
    raise RuntimeError("LogoPngBase64 constant not found")

old_base64 = match.group(2)
old_bytes = base64.b64decode(old_base64, validate=True)
old_sha = hashlib.sha256(old_bytes).hexdigest()
print(f"Replacing logo bytes: old SHA-256 {old_sha}, new {EXPECTED_SHA256}")

source = source[:match.start(2)] + EXPECTED_BASE64 + source[match.end(2):]
source = source.replace("// @version      1.12.2", "// @version      1.12.3", 1)
source_path.write_text(source, encoding="utf-8")

# Re-read what was actually written and verify the committed source, not merely
# the Python literal above.
written = source_path.read_text(encoding="utf-8")
written_match = re.search(
    r'const LogoPngBase64\s*=\s*\n\s*"([A-Za-z0-9+/=]+)";',
    written,
)
if not written_match:
    raise RuntimeError("written LogoPngBase64 constant not found")
written_b64 = written_match.group(1)
if len(written_b64) != EXPECTED_BASE64_LENGTH:
    raise RuntimeError("written Base64 length mismatch")
written_bytes = base64.b64decode(written_b64, validate=True)
validate_png_bytes(written_bytes)

changelog_path = Path("CHANGELOG.md")
changelog = changelog_path.read_text(encoding="utf-8")
needle = "# Changelog\n\n## 1.12.2"
replacement = """# Changelog

## 1.12.3
- Replaced the corrupted generated logo Base64 with a mechanical byte-for-byte encoding of the original uploaded `LBC Logo TEMP.png` (4,406 bytes; SHA-256 `4198a3a363878ed16e09937ccc71a5277bd4fd431ac4cbed1508a5bb70b1402f`).
- Added release validation for Base64 length, decoded byte length, SHA-256, PNG signature/chunk boundaries, and every PNG chunk CRC so future image-byte corruption fails CI instead of shipping.

## 1.12.2"""
if needle not in changelog:
    raise RuntimeError("CHANGELOG insertion point not found")
changelog = changelog.replace(needle, replacement, 1)
changelog_path.write_text(changelog, encoding="utf-8")
