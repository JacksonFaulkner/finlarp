"""TRM_POST_QUANTUM_CRYPTOGRAPHY: the Terms-tab overview for post-quantum cryptography.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_post_quantum_cryptography.py

Writes assets/term_TRM_POST_QUANTUM_CRYPTOGRAPHY.glb. Captions live in specs/terms/TRM_POST_QUANTUM_CRYPTOGRAPHY.json.

The board's links and certificates are public-key crypto that a large quantum computer could break.
On the bench: a lattice, the kind of hard problem the new standards (ML-KEM, ML-DSA) rest on, with
the classical RSA key a quantum computer would factor, and the hybrid handshake that holds both keys.

Beats:
  0 board     the links and certificates on the server, and the HSM that holds the signing keys
  1 lattice   the new standards: a lattice where finding the short secret vector is hard
  2 threat    Shor's algorithm factors the RSA key a quantum computer would be given
  3 hybrid    a session that holds both a classical and a post-quantum key, so both must fail
  4 migrate   certificates, chips and HSMs all need a multi-year upgrade
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_trust as K  # noqa: E402
from sand_overview import F, empty, show  # noqa: E402
from power_vrm_detail import blink, frame, run  # noqa: E402

SLUG = "TRM_POST_QUANTUM_CRYPTOGRAPHY"
BEATS = [
    ("Every link and certificate on the server rests on public-key crypto",
     "The TLS links, VPNs, code signatures and certificates on an AI server all depend on RSA and elliptic-curve keys. "
     "Their keys live in hardware security modules (HSMs). Most of that math is what a large quantum computer would "
     "break; the data encrypted today is what it would read later."),
    ("The new standards rest on lattice problems no quantum shortcut is known for",
     "NIST finalized ML-KEM (FIPS 203) for key exchange and ML-DSA (FIPS 204) for signatures in 2024. Both rest on lattice "
     "problems: find a short vector hidden in a grid of points. No known quantum algorithm solves them efficiently, so "
     "they are the replacement."),
    ("Shor's algorithm breaks RSA and elliptic curves outright",
     "Shor's algorithm finds the prime factors of an RSA modulus, and the discrete logs behind elliptic-curve keys, in "
     "polynomial time on a large enough quantum computer. The math that protects today's keys is the math that breaks, "
     "so the threat is to the keys themselves, not to their length."),
    ("Hybrid sessions hold both keys, so one weak link is not enough",
     "During migration a session runs a classical key exchange and a post-quantum one, then combines the secrets. The "
     "session stays secure as long as either holds. That is how browsers and cloud services are rolling out PQC first."),
    ("Certificates, chips and HSMs all need a multi-year upgrade",
     "The cost is in the replacement, not the math: certificates, firmware, HSMs and cloud services all change, and "
     "keys already recorded must be migrated. Vendors: IBM (IBM), Palo Alto Networks (PANW), Cloudflare (NET), Thales (HO.PA)."),
]

LAT_C = (199.0, 22.0, -20.0)
LAT_S = 7.0
RSA_P = (150.0, 0.0, -60.0)
RSA_Q = (162.0, 0.0, -60.0)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    b = C.base(m, root, decap=False)
    pk = b["pk"]
    hsm = K.hsm(m, root, "pq_hsm", (-120.0, 0.0, -40.0), 14.0, 12.0, 6.0)

    bench = empty("pq_bench", root)
    lat = K.lattice(m, bench, "pq_lat", LAT_C, n=4, s=LAT_S, r=0.5)
    show(bench, [(F(1, 0), F(5, 0))])

    # the short secret vector: a glowing path through the lattice, pulsed in beat 1
    nodes = lat["nodes"]
    secret = [nodes[(0, 0, 0)], nodes[(1, 1, 0)], nodes[(2, 1, 1)]]
    run(root, "secret", secret, 2, 0.7, m["trust_gate"], 1, 0.2, 0.8, 35, until=F(2, 0))

    # beat 2: the RSA key on the board, factored by a Shor run
    rsa_p = K.key_bar(m, root, "pq_rsa_p", (RSA_P[0], 6.0, RSA_P[2]), (RSA_P[0], 6.0, RSA_P[2] + 0.1), r=3.0, teeth=1)
    show(rsa_p, [(F(2, 0), F(5, 0))])
    rsa_q = K.key_bar(m, root, "pq_rsa_q", (RSA_Q[0], 6.0, RSA_Q[2]), (RSA_Q[0], 6.0, RSA_Q[2] + 0.1), r=3.0, teeth=1)
    show(rsa_q, [(F(2, 0), F(5, 0))])
    run(root, "shor", [(RSA_P[0] + 6.0, 20.0, RSA_P[2] + 6.0), (RSA_P[0] + 6.0, 9.0, RSA_P[2] + 4.0),
                       (RSA_P[0] + 6.0, 6.0, RSA_P[2] + 2.0)], 3, 0.8, m["warn"], 2, 0.2, 0.7, 30, until=F(3, 0))

    # beat 3: hybrid session: two gold keys meet and combine into one session key
    k1 = K.key_bar(m, root, "pq_hyb_c", (150.0, 10.0, -40.0), (LAT_C[0] - 4.0, 18.0, LAT_C[2]), r=0.7, teeth=3)
    k2 = K.key_bar(m, root, "pq_hyb_p", (248.0, 10.0, -40.0), (LAT_C[0] + 4.0, 18.0, LAT_C[2]), r=0.7, teeth=3)
    show(k1, [(F(3, 0), F(5, 0))])
    show(k2, [(F(3, 0), F(5, 0))])
    run(root, "sess", [(LAT_C[0], 20.0, LAT_C[2]), (LAT_C[0], 30.0, LAT_C[2]), (LAT_C[0], 44.0, LAT_C[2])], 2, 0.9,
        m["trust_ok"], 3, 0.6, 0.9, 40)

    # beat 4: the migration: HSM and verifier light up as they are upgraded
    blink(hsm["light"], 4, [0, 2, 4, 6], n=8, on=0.6)

    C.tags(root, {
        0: [("TLS, VPN, code signing", pk["top"]), ("HSM holds the keys", hsm["top"]),
            ("RSA / ECC: what Shor breaks", (-60.0, 6.0, -110.0))],
        1: [("lattice: short vector is hard", (LAT_C[0], 40.0, LAT_C[2])), ("ML-KEM (FIPS 203): key exchange", LAT_C),
            ("ML-DSA (FIPS 204): signatures", (LAT_C[0] + 8.0, 10.0, LAT_C[2]))],
        2: [("Shor factors the RSA modulus", (RSA_P[0] + 6.0, 6.0, RSA_P[2])), ("ECC: discrete logs fall too", (RSA_Q[0], 8.0, RSA_Q[2] - 6.0))],
        3: [("classical key", (162.0, 10.0, -40.0)), ("post-quantum key", (236.0, 10.0, -40.0)),
            ("session holds both", (LAT_C[0], 44.0, LAT_C[2]))],
        4: [("certs, chips, HSMs: upgrade", hsm["top"]), ("IBM (IBM), Palo Alto (PANW)", (-70.0, 8.0, -110.0)),
            ("Cloudflare (NET), Thales (HO.PA)", (-30.0, 8.0, -150.0))],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.65, pad=1.0),
        frame((LAT_C[0], 22.0, LAT_C[2]), 90.0, 0.25, 0.22),
        frame((LAT_C[0], 22.0, LAT_C[2]), 90.0, 0.25, 0.22),
        frame((LAT_C[0], 24.0, LAT_C[2]), 110.0, 0.25, 0.30),
        frame((60.0, 0.0, -70.0), 330.0, 0.25, 0.45, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
