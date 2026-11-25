"""TRM_TEE: the Terms-tab overview for a trusted execution environment (on-die enclave).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_tee.py

Writes assets/term_TRM_TEE.glb. Captions live in specs/terms/TRM_TEE.json (same beat count).

A host CPU die on the AI board, cut open on the bench: the normal world (OS and apps) on one side,
and a sealed enclave with its own walls and keys on the other. Requests cross the enclave's gate
only when it lets them in; the enclave proves its identity to a verifier before a key is released.
Contrast with confidential computing, which protects a whole VM rather than a small sealed region.

Beats:
  0 board     the host CPU package on the AI board; the enclave lives inside it
  1 cut-open  the die on the bench: OS cores, caches and the enclave behind barrier walls
  2 request   the OS asks; the request crosses the gate, a direct poke at the wall is refused
  3 attest    the enclave signs a measurement, the verifier checks it, and the key comes back
  4 where     phones, laptops and server chips all carry one
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_trust as K  # noqa: E402
from sand_overview import F, empty, show  # noqa: E402
from power_vrm_detail import blink, frame, run  # noqa: E402

SLUG = "TRM_TEE"
BEATS = [
    ("A host CPU holds a sealed enclave beside the OS",
     "Modern processors carve out a small trusted execution environment (TEE): an isolated region of the chip that runs "
     "secure code and holds secrets the main operating system cannot read. It sits inside the same CPU package that "
     "runs the rest of the server, so no extra chip is needed."),
    ("Cut open: barrier walls in silicon separate the enclave from the OS",
     "On the die, the enclave is a walled-off block with its own memory and key store. Hardware enforces the wall: "
     "the OS cores and caches sit on the other side and have no path into it. Keys and secrets stay in the enclave, "
     "even when the operating system is fully compromised."),
    ("The OS can ask, but the gate decides who gets in",
     "Requests reach the enclave only through a gate the hardware checks. A direct poke at the wall is refused. The "
     "enclave answers with a result, never with its keys, so an attacker on the OS side learns nothing about what it holds."),
    ("The enclave proves what it runs before it gets a key",
     "The enclave measures its own code and signs that measurement, a remote attestation report. A verifier checks the "
     "signature and the measurement, and only then releases the key the model or payment needs. Code that has been "
     "altered fails the check and gets nothing."),
    ("Phones, laptops and servers all carry one",
     "Arm TrustZone and Apple's Secure Enclave guard payments and biometrics in phones and laptops. Server chips use "
     "the same idea for keys and attestation. Vendors: Arm (ARM), Qualcomm (QCOM), Apple (AAPL), Intel (INTC). A TEE is a "
     "small sealed region; confidential computing, next, protects a whole virtual machine."),
]

# the die on the bench (x 150..248), the enclave and the OS side on it
DIE = (160.0, 238.0, -36.0, -4.0)
ENC = (166.0, 200.0, -30.0, -10.0)
ENC_Y = (4.0, 10.0)
OS = (206.0, 232.0, -30.0, -10.0)
VER = (120.0, 0.0, -60.0)  # the verifier, standing on the board in front of the package


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    b = C.base(m, root, decap=False)
    pk = b["pk"]

    bench = empty("tee_bench", root)
    K.die(m, bench, "tee_die", DIE[0], DIE[1], DIE[2], DIE[3], 0.6, 4.0)
    enc = K.enclave(m, bench, "tee_enc", ENC[0], ENC[1], ENC[2], ENC[3], ENC_Y[0], ENC_Y[1])
    K.die(m, bench, "tee_os", OS[0], OS[1], OS[2], OS[3], 4.0, 10.0, mt="trust_core")
    K.die(m, bench, "tee_cache", ENC[0], OS[1], -36.0, -32.0, 4.0, 6.0, mt="trust_core")
    key = K.key_bar(m, bench, "tee_key", (174.0, 13.0, -20.0), (194.0, 13.0, -20.0), r=0.35, teeth=4)
    show(bench, [(F(1, 0), F(5, 0))])
    show(key, [(F(1, 0), F(5, 0))])

    # the verifier, off to the side on the board
    ver = K.verifier(m, root, "tee_ver", VER, w=14.0)
    show(ver["group"], [(F(3, 0), F(5, 0))])

    # beat 2: a request through the gate; a direct poke at the wall bounces off
    req_path = [(219.0, 12.0, -12.0), (200.0, 14.0, -8.0), enc["gate"]]
    run(root, "req", req_path, 3, 0.8, m["e_blue"], 2, 0.1, 0.4, 40, until=F(3, 0))
    deny_path = [(219.0, 8.0, -20.0), (206.0, 8.0, -20.0), (199.8, 8.0, -20.0)]
    run(root, "deny", deny_path, 2, 0.8, m["warn"], 2, 0.5, 0.8, 30, until=F(3, 0))
    blink(enc["walls"], 2, [4], n=8, on=0.9)

    # beat 3: the report goes out to the verifier, the key comes back in
    rep = [enc["gate"], (165.0, 40.0, -30.0), (130.0, 14.0, -56.0), (VER[0], 6.0, VER[2] + 1.5)]
    run(root, "report", rep, 2, 0.9, m["sig"], 3, 0.1, 0.5, 60)
    back = list(reversed(rep))
    run(root, "keyback", back, 2, 0.9, m["h_amber"], 3, 0.6, 0.95, 60)
    blink(ver["ok"], 3, [6], n=8, on=0.8)

    C.tags(root, {
        0: [("host CPU package", pk["top"]), ("enclave lives inside it", (199.0, 12.0, -20.0)),
            ("AI servers carry them", (-70.0, 2.0, -70.0))],
        1: [("enclave: sealed region", (183.0, 12.0, -20.0)),
            ("OS cores: no path in", (219.0, 12.0, -20.0)),
            ("barrier walls, set in silicon", (199.0, 12.0, -30.0)),
            ("keys stay inside", (184.0, 14.5, -20.0))],
        2: [("OS request, checked at the gate", (200.0, 14.0, -8.0)), ("poke at wall: refused", (199.8, 9.0, -20.0))],
        3: [("signed measurement (attestation)", (165.0, 40.0, -30.0)), ("verifier checks the report", (VER[0], 8.0, VER[2])),
            ("key released only if it passes", (130.0, 14.0, -56.0))],
        4: [("Arm TrustZone (ARM)", pk["top"]), ("Apple Secure Enclave (AAPL)", (199.0, 12.0, -20.0)),
            ("Qualcomm (QCOM), Intel (INTC)", (-70.0, 8.0, -110.0))],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.65, pad=1.0),
        frame((199.0, 6.0, -20.0), 110.0, 0.25, 0.22),
        frame((160.0, 12.0, -40.0), 190.0, 0.30, 0.40, pad=1.0),
        frame((160.0, 12.0, -40.0), 190.0, 0.30, 0.40, pad=1.0),
        frame((60.0, 0.0, -70.0), 330.0, 0.25, 0.45, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
