#!/usr/bin/env python3
"""Reapply Ignis certificate exclusions after regenerating the tutorial bundles.

Run from any directory with Python 3. The Mozilla input and mk-ca-bundle.pl
provenance remain in each bundle header; this is a local postprocessing step.
"""

import hashlib
from pathlib import Path
import re
import ssl


EXCLUDED = {
    "86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b",
    "d7a7a0fb5d7e2731d771e9484ebcdef71d5f0c3e0a2948782bc83ee0ea699ef4",
}
CERTIFICATE = re.compile(
    r"[^\n]+\n=+\n(?P<pem>-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----)\n",
    re.DOTALL,
)
NOTE = """## Ignis local security exclusions applied after mk-ca-bundle.pl on 2026-10-21.
## The SHA256 above identifies the original Mozilla input, not this modified bundle.
## After regeneration, exclude certificates with these SHA256 DER fingerprints:
## emSign ECC Root CA - G3: 86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b
## Comodo AAA Services root: d7a7a0fb5d7e2731d771e9484ebcdef71d5f0c3e0a2948782bc83ee0ea699ef4
## Use update-ca-bundles.py in the xcode iOS directory to reapply these exclusions.
## Advisory: https://lists.debian.org/debian-security-announce/2026/msg00487.html
##
"""


def exclude(match):
    der = ssl.PEM_cert_to_DER_cert(match.group("pem"))
    return "" if hashlib.sha256(der).hexdigest() in EXCLUDED else match.group(0)


if __name__ == "__main__":
    directory = Path(__file__).resolve().parent
    for tutorial in ("Tutorial 4", "Tutorial 5"):
        bundle = directory / tutorial / "ssl/certs/ca-certificates.crt"
        content = CERTIFICATE.sub(exclude, bundle.read_text())
        if NOTE not in content:
            marker = content.index("## SHA256:")
            marker = content.index("##\n", marker) + 3
            content = content[:marker] + NOTE + content[marker:]
        bundle.write_text(content)
