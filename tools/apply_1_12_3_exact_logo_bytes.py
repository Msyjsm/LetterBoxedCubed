from pathlib import Path
import base64
import hashlib
import re
import struct
import zlib

EXPECTED_SHA256 = "4198a3a363878ed16e09937ccc71a5277bd4fd431ac4cbed1508a5bb70b1402f"
EXPECTED_BYTE_LENGTH = 4406
EXPECTED_BASE64_LENGTH = 5876
CHUNK_SIZE = 256
EXPECTED_HASHES = [
    "f54bf72277c5411c377c716af98b18636bd9427cc0abb8ca95c22e2413208555",
    "57d39d29b8f4e5f32a2e289c7f43f5e3b7998bd22b1bd5acf10315539e0646f4",
    "e862de26e43be20ee582c7542d68b924a8af26282db0382f7b2fcac772ff7788",
    "078cb3f484798e24a93476e6ade9693300fc09ab1a97ba1f3ce70d443c2c5a6d",
    "ad595144d5dfd90f03f3535ff1a7196314b72915a4ae1cf7933a88d4f5146906",
    "10b892104d36559d8831687dce3b8f6a3737c1bd44df00c646272e948239c58d",
    "8c27e672b48683527e9653b187105b421b48472bb7c71d86caf2cfff463ad578",
    "e75a7537c9c8f2a4f1812470718105e56ccd3bffee7af5e3dd9627ba006e675f",
    "9298766ca4d883eb182a2dedb7563525299821571f7c6f66e3eb5e8a6f4baec5",
    "4c04fbd3c98eea19b6bde9995db89632c6e090575a057cec21e589776fdf0b1f",
    "4fb5f5c7cda96c05829c738f677614a0ac448c135359ba0b92aab116ad27469e",
    "17ea19df7e02a568a5c42be68742679d6471f98e1d934240a2ba971c074f67be",
    "9c7645c0ad37bad6034b471df5295536d5fb827397f4c6d0acabb90b732a2219",
    "4132422f8bc1e80e0c81dbb8d1cd97cefd14e481eb4ca2080022b9809625ae59",
    "a525365de3c7aefe2453db62b01bc122e6e3e5fc8fcbc3cd67e9d3dc1b81fc99",
    "2c69b041e5410c480a61a041a7749cf6dd67b928a1947c2108ba6810c87714b8",
    "cb0f0ca8546532e7dd117d3edcbf18fed64a591ef0e8c5892d5d46291f4def94",
    "6b9226abfe86461c55ddd10b54a6c8aa4c01c084a5811e03bb77077657efa716",
    "fdae8d3d25fa74f80cf6ac647eadd488d92b47a836b8833ae56c5d7905cdf438",
    "a32ed45b0b844260dbd4172e697961464d1217804bc5142e61d4e3e9d668d140",
    "c0fa03907006a7044779a7ec04180290c50be625d31966ed60f4ba9760e11f8d",
    "8503fa3fb8fd7ab605858c719feecde26cb54a9c4853941618d6cc9b95d2dbb5",
    "98ed5cd22b4d6b84e2e66a629d0b9065bacdd2b7ad9946f7a51fbed126a95d9d",
]

# These are the only three 256-character regions that differ from the original
# uploaded PNG. Keeping replacements small prevents opaque long-string mutation
# in the repository-update path, while the whole-file digest below proves that
# the reconstructed image is exact.
CORRECT_CHUNKS = {
    4: "W7dutYxVh8zNnSlIwelvyUA2hWEgh96ZlluePCgvHZ+RNhGZNV8UEcFKSLKxArItDAP52zvTMjh+UF56N55YiYiE5gNwVyqViBW8NR+rJ+ONlRCs+LltVsQKulVj9a0YLwNrcUkYIy4D4bMkNisT37BiQqzgs+o3q1vGo8Wqrea/O5r4+kSwYsBmBZ8tuAyMsFlVX7fpwnPl8c2Xy7nh0sUiWI4mJibYrOCt2lgdiPjNalZE+ro65VfXfkHWffI8",
    9: "VINVLpe5DIS32KzcpRYsNiv4jM0qHqkEi80KPmOzik/iwWKzgs/YrOKVaLDYrOAzNqv4JRYsNiv4jM0qGYkEi80KPmOzSk7swWKzgs/YrJIVa7DYrOCl4NQ/RspmlbzYgsVmBZ+xWaUjlmCxWcFnYSBsVilxDhabFXzGZpUup2CxWcFn85eBbFapsQ5WqVQiVvBWNVaDbFapsgpWqVTiMhDe4j6r1okcLDYr+IzNqrUiBYvNCj5js2q9poPFZgWf",
    20: "BoIFJMAmVtXNamxsjM1qEQQLiJltrIrF4t6xsbEtK1asIFaLIFhAjFxiNTIyQqyWQLCAmNjEis0qGoIFxMAmVmxW0REswJFtrNisoiNYgAOXWLFZRUewgMUEgYgE5qPzbGLFZuWGYAGLqVREpHGBbGLFZuWOYAER2caKzcodwQIicIkVm5U7ggU0ySZWbFbxIlhAE2xjxWYVL4IFLMUiVrUDO5eB8SFYwCIqInJWGMjbFrFis0oGwQIW0dXeJuX3",
}


def validate_png_bytes(data: bytes) -> None:
    if len(data) != EXPECTED_BYTE_LENGTH:
        raise RuntimeError(f"logo byte length mismatch: {len(data)}")
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"logo SHA-256 mismatch: {digest}")
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


source_path = Path("LetterBoxedCubed.user.js")
source = source_path.read_text(encoding="utf-8")
match = re.search(
    r'(const LogoPngBase64\s*=\s*\n\s*")([A-Za-z0-9+/=]+)(";)',
    source,
)
if not match:
    raise RuntimeError("LogoPngBase64 constant not found")

current = match.group(2)
if len(current) != EXPECTED_BASE64_LENGTH:
    raise RuntimeError(f"current Base64 length mismatch: {len(current)}")
chunks = [current[i:i + CHUNK_SIZE] for i in range(0, len(current), CHUNK_SIZE)]
if len(chunks) != len(EXPECTED_HASHES):
    raise RuntimeError(f"unexpected chunk count: {len(chunks)}")

mismatches = [
    i for i, expected in enumerate(EXPECTED_HASHES)
    if hashlib.sha256(chunks[i].encode()).hexdigest() != expected
]
if mismatches != [4, 9, 20]:
    raise RuntimeError(f"unexpected corrupt chunks before repair: {mismatches}")

for index, value in CORRECT_CHUNKS.items():
    if len(value) != CHUNK_SIZE:
        raise RuntimeError(f"replacement chunk {index} has length {len(value)}")
    digest = hashlib.sha256(value.encode()).hexdigest()
    if digest != EXPECTED_HASHES[index]:
        raise RuntimeError(f"replacement chunk {index} hash mismatch: {digest}")
    chunks[index] = value

repaired = "".join(chunks)
if len(repaired) != EXPECTED_BASE64_LENGTH:
    raise RuntimeError("repaired Base64 length mismatch")
repaired_bytes = base64.b64decode(repaired, validate=True)
validate_png_bytes(repaired_bytes)

source = source[:match.start(2)] + repaired + source[match.end(2):]
if "// @version      1.12.2" not in source:
    raise RuntimeError("expected 1.12.2 version marker not found")
source = source.replace("// @version      1.12.2", "// @version      1.12.3", 1)
source_path.write_text(source, encoding="utf-8")

# Verify the actual file text after writing, not merely the in-memory value.
written = source_path.read_text(encoding="utf-8")
written_match = re.search(
    r'const LogoPngBase64\s*=\s*\n\s*"([A-Za-z0-9+/=]+)";',
    written,
)
if not written_match:
    raise RuntimeError("written LogoPngBase64 constant not found")
validate_png_bytes(base64.b64decode(written_match.group(1), validate=True))

changelog_path = Path("CHANGELOG.md")
changelog = changelog_path.read_text(encoding="utf-8")
needle = "# Changelog\n\n## 1.12.2"
replacement = """# Changelog

## 1.12.3
- Replaced the corrupted generated logo Base64 with a byte-for-byte encoding of the original uploaded temporary logo (4,406 bytes; SHA-256 `4198a3a363878ed16e09937ccc71a5277bd4fd431ac4cbed1508a5bb70b1402f`).
- Added release validation for Base64 length, decoded byte length, SHA-256, PNG signature/chunk boundaries, and every PNG chunk CRC so future image-byte corruption fails CI instead of shipping.

## 1.12.2"""
if needle not in changelog:
    raise RuntimeError("CHANGELOG insertion point not found")
changelog = changelog.replace(needle, replacement, 1)
changelog_path.write_text(changelog, encoding="utf-8")

print("Exact original logo restored and verified:", EXPECTED_SHA256)
