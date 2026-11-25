"""TRM_HARDWARE_ROOT_OF_TRUST: the Terms-tab overview for a hardware root of trust.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_hardware_root_of_trust.py

Writes assets/term_TRM_HARDWARE_ROOT_OF_TRUST.glb. Captions live in specs/terms/TRM_HARDWARE_ROOT_OF_TRUST.json.

A small security chip on the AI board that starts first. Its immutable ROM holds the first boot
code, its fuses hold the keys, and its crypto engine measures each firmware stage before it runs.
A buyer checks the signed report before sending model weights.

Beats:
  0 board     the security chip and the HSM sit on the AI server board
  1 cut-open  the chip on the bench: immutable ROM, key fuses and the crypto engine
  2 measure   every boot stage is hashed into the root before it runs
  3 tamper    a modified stage fails its check and the boot halts
  4 attest    the signed report goes out; the buyer verifies before sending weights
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_trust as K  # noqa: E402
from sand_overview import F, empty, show  # noqa: E402
from power_vrm_detail import blink, frame, run  # noqa: E402

SLUG = "TRM_HARDWARE_ROOT_OF_TRUST"
BEATS = [
    ("A small security chip on the board checks everything first",
     "Every AI server carries a hardware root of trust: a separate chip that holds keys and checks the rest of the board "
     "before any of it runs. It is typically a trusted platform module (TPM), a secure element, or an on-die security "
     "processor, and it is the one part the system is told to believe."),
    ("Cut open: unchangeable boot code, fused keys and a crypto engine",
     "On the die, the ROM holds the first boot code and cannot be rewritten. Key fuses are burned once at the factory, "
     "so the keys cannot be read out or changed. The crypto engine does the hashing and signature checks, and keeps the "
     "measurement registers that record what has run."),
    ("Each stage is measured into the root before it runs",
     "The boot runs as a chain: ROM, firmware, bootloader, operating system. Before each stage runs, its hash is folded "
     "into a measurement register in the root. The register can only be extended, never reset, so it records the exact "
     "sequence of code that started."),
    ("A changed stage fails its check, and the boot stops",
     "If a firmware image has been altered, its signature or hash no longer matches and the chain halts. The machine "
     "does not run the bad code, and the mismatch is reported to the verifier. Attackers gain nothing by flashing it."),
    ("The signed report lets a buyer check the hardware before trusting it",
     "The root signs its measurements into a report. The buyer's verifier checks the signature against the chip maker's "
     "certificate and only then releases model weights or keys. Makers: Infineon (IFX.DE), NXP (NXPI), Microchip (MCHP), "
     "and NVIDIA (NVDA) for its accelerator roots."),
]

HV = (160.0, 238.0, -36.0, -4.0)
ROM = (166.0, 186.0, -34.0, -24.0)
ENG = (166.0, 186.0, -20.0, -10.0)
FUSE_X = (166.0, 204.0)
FUSE_Z = -6.0
CHAIN_X, CHAIN_Z = 216.0, -20.0
CHAIN_Y0 = 3.0
VER = (120.0, 0.0, -60.0)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    b = C.base(m, root, decap=False)
    pk = b["pk"]
    hsm = K.hsm(m, root, "hr_hsm", (-120.0, 0.0, -40.0), 14.0, 12.0, 6.0)
    ver = K.verifier(m, root, "hr_ver", VER, w=14.0)
    show(ver["group"], [(F(4, 0), F(5, 0))])

    bench = empty("hr_bench", root)
    K.die(m, bench, "hr_die", HV[0], HV[1], HV[2], HV[3], 0.6, 3.0)
    K.die(m, bench, "hr_rom", ROM[0], ROM[1], ROM[2], ROM[3], 3.0, 9.0, mt="trust_core")
    eng = K.enclave(m, bench, "hr_eng", ENG[0], ENG[1], ENG[2], ENG[3], 3.0, 9.0)
    fuses = K.fuse_row(m, bench, "hr_fuse", FUSE_X[0], FUSE_X[1], FUSE_Z, 3.0, 8, blown=(2, 5))
    ch = K.chain(m, bench, "hr_chain", CHAIN_X, CHAIN_Z, 4, CHAIN_Y0, 12.0, 5.0, 1.6,
                 mt=["trust_hash", "trust_hash", "trust_hash", "trust_hash"])
    show(bench, [(F(1, 0), F(5, 0))])
    show(ch["group"], [(F(2, 0), F(5, 0))])

    # beat 2: each stage's hash rises from the chain into the root's measurement engine
    dst = (176.0, 10.0, -15.0)
    for i, t in enumerate(ch["tops"]):
        run(root, f"meas{i}", [t, (t[0] - 10.0, t[1] + 6.0, t[2] + 4.0), dst], 2, 0.7, m["trust_clear"],
            2, 0.1 + 0.15 * i, 0.4 + 0.15 * i, 40, until=F(3, 0))

    # beat 3: the tampered stage's hash does not match; a red bead is refused at the engine
    run(root, "bad", [ch["tops"][1], (206.0, 14.0, -14.0), (ENG[1] + 0.5, 9.0, -15.0)], 2, 0.8,
        m["trust_deny"], 3, 0.1, 0.6, 40)
    blink(ch["group"], 3, [0], n=4, on=0.5)
    blink(eng["walls"], 3, [1, 3], n=8, on=0.6)

    # beat 4: the signed report goes to the buyer's verifier
    rep = [dst, (150.0, 40.0, -30.0), (130.0, 14.0, -56.0), (VER[0], 6.0, VER[2] + 1.5)]
    run(root, "report", rep, 2, 0.9, m["trust_ok"], 4, 0.1, 0.5, 50)
    blink(ver["ok"], 4, [6], n=8, on=0.8)
    show(hsm["light"], [(F(0, 0), F(5, 0))])

    C.tags(root, {
        0: [("security chip (root of trust)", (-30.0, 8.0, -60.0)), ("HSM beside it", (-120.0, 8.0, -40.0)),
            ("GPU board, one chip checks it all", pk["top"])],
        1: [("ROM: unchangeable boot code", (176.0, 10.0, -30.0)), ("fused keys: burned once", (185.0, 6.0, -6.0)),
            ("crypto engine", (176.0, 10.0, -15.0)), ("measurement registers", (216.0, 24.0, -20.0))],
        2: [("each stage hashed before it runs", (216.0, 14.0, -20.0)), ("hash folded into the root", dst),
            ("extend only, never reset", (216.0, 30.0, -20.0))],
        3: [("altered stage: hash mismatch", (206.0, 14.0, -14.0)), ("boot halts, bad code never runs", (176.0, 12.0, -15.0))],
        4: [("signed report (attestation)", (150.0, 40.0, -30.0)), ("buyer verifies before sending weights", (VER[0], 8.0, VER[2])),
            ("Infineon (IFX.DE), NXP (NXPI)", (-70.0, 8.0, -110.0))],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.65, pad=1.0),
        frame((196.0, 12.0, -20.0), 110.0, 0.25, 0.22),
        frame((196.0, 12.0, -20.0), 110.0, 0.25, 0.22),
        frame((196.0, 12.0, -20.0), 110.0, 0.25, 0.22),
        frame((150.0, 14.0, -40.0), 300.0, 0.30, 0.40, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
