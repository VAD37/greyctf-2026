#!/usr/bin/env bash
# Fort Knockies (greyctf 2026, ezpz/forensics, id 30)
# Docker-image whiteout carve + git history + .env recovery -> reconstruct seal key -> decrypt flag.
#
# FLAG: grey{jz_some_rookie_mistakesi9v2k}
#
# Dist: OCI image `fortknocks:hard` (Google Drive id 174UqF92-AGfT6niJN-HcPQZsO7Xnfeer),
#       saved as files/fort-knockies.tar.gz. Already unpacked to files/extracted/ (blobs) and
#       files/rootfs/ (merged tree -- which, conveniently, keeps the "deleted" files alongside
#       their .wh. whiteout markers, so no per-layer carve is even strictly required here).
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"     # .../08_fort-knockies
ROOT="$HERE/files/rootfs"                     # merged image tree (whiteouts + originals both present)
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT

# ---------------------------------------------------------------------------
# 1. The image "deletes" three secrets via OCI/AUFS whiteouts in late layers:
#       app/.wh..env                       -> hides app/.env
#       app/.wh..git                       -> hides the git repo
#       var/lib/fortknockies/.wh..staging  -> hides var/lib/fortknockies/.staging
#    Earlier layers (and this merged rootfs) still carry the originals.
# ---------------------------------------------------------------------------

# 2. KEY PART A -- from the recovered dev .env (app/.env). Last line is the seal-key half "pycache":
ENV_HALF="$(tail -n1 "$ROOT/app/.env")"                 # -> pycache

# 3. KEY PART B -- from the recovered git history. tests/test_parts.py held `part2 = "PATH"`,
#    later commit "remove legacy scratch files" replaced it with
#    "# moved into local config during build testing" (i.e. merged into .env).
GITDIR="$ROOT/app/.git"
PATH_HALF="$(GIT_DIR="$GITDIR" git log --all -p 2>/dev/null \
             | grep -oE 'part2 = "[^"]+"' | head -n1 | sed -E 's/.*"([^"]+)".*/\1/')"  # -> PATH

# 4. Reconstruct the legacy seal key = <env half> + <git half>
SEAL_KEY="${ENV_HALF}${PATH_HALF}"                       # -> pycachePATH
echo "[*] reconstructed seal key: $SEAL_KEY"

# 5. The flag lives in .staging/README -- a password-protected 7z. The 7z password is the
#    literal env-var NAME used by the app: FORTKNOCKIES_SEAL_KEY (app.py).
7z x -p"FORTKNOCKIES_SEAL_KEY" -y -o"$WORK" "$ROOT/var/lib/fortknockies/.staging/README" >/dev/null
#    -> yields flag.enc (FKENC0: PBKDF2-HMAC-SHA1/64000, AES-256-CBC) + sample-upload.enc (FKENC1)

# 6. Decrypt flag.enc (FKENC0, the "legacy import handoff bundle") with the reconstructed seal key.
uv run --with cryptography python - "$WORK/flag.enc" "$SEAL_KEY" <<'PY'
import sys, base64, json
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
e = json.load(open(sys.argv[1])); pw = sys.argv[2]
salt = base64.b64decode(e['salt_b64']); iv = base64.b64decode(e['iv_b64']); ct = base64.b64decode(e['ciphertext_b64'])
key = PBKDF2HMAC(algorithm=hashes.SHA1(), length=32, salt=salt, iterations=e['iterations']).derive(pw.encode())
dec = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
pt  = padding.PKCS7(128).unpadder()
flag = (pt.update(dec.update(ct) + dec.finalize()) + pt.finalize()).decode().strip()
print("[+] FLAG:", flag)
PY
