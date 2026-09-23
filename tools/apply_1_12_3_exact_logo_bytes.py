from pathlib import Path
import base64
import hashlib
import re

EXPECTED_LENGTH = 5876
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

source = Path("LetterBoxedCubed.user.js").read_text(encoding="utf-8")
m = re.search(r'const LogoPngBase64\s*=\s*\n\s*"([A-Za-z0-9+/=]+)";', source)
if not m:
    raise RuntimeError("LogoPngBase64 not found")
current = m.group(1)
print("CURRENT_LENGTH", len(current))
print("CURRENT_DECODED_LENGTH", len(base64.b64decode(current, validate=True)))
print("CURRENT_DECODED_SHA256", hashlib.sha256(base64.b64decode(current, validate=True)).hexdigest())
chunks = [current[i:i + CHUNK_SIZE] for i in range(0, len(current), CHUNK_SIZE)]
print("CURRENT_CHUNK_COUNT", len(chunks))
mismatches = []
for i, expected in enumerate(EXPECTED_HASHES):
    actual = hashlib.sha256(chunks[i].encode()).hexdigest() if i < len(chunks) else "MISSING"
    if actual != expected:
        mismatches.append(i)
        print("MISMATCH", i, "LEN", len(chunks[i]) if i < len(chunks) else 0, "SHA", actual)
print("MISMATCH_INDICES", ",".join(map(str, mismatches)))
raise RuntimeError("diagnostic stop")
