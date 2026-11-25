"""TRM_MRDIMM: the Terms-tab overview for MRDIMM (multiplexed rank DIMM), on a server motherboard.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_mrdimm.py

Writes assets/term_TRM_MRDIMM.glb. Captions live in specs/terms/TRM_MRDIMM.json.

The server board from TRM_DDR_SDRAM with tall MRDIMMs: two ranks of DDR5 chips, an MRCD in the
middle and a row of MDB data buffers. Rank A (blue) and rank B (amber) beads arrive at the buffers
together and leave interleaved at twice the rate toward the CPU.

Beats:
  0 server   CPU with tall MRDIMMs in the slots
  1 ranks    two ranks of standard DDR5 chips, MRCD and MDB buffers
  2 mux      both ranks read at once; the MDBs interleave them at double rate
  3 rates    bars: RDIMM 6400 vs MRDIMM 8800 vs 12800 MT/s
  4 market   buffer-chip makers and who uses it
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_dram as K  # noqa: E402
import trm_ddr_sdram as S  # noqa: E402
from term_common import F  # noqa: E402
from power_vrm_detail import bx, frame, mat, run  # noqa: E402

SLUG = "TRM_MRDIMM"
BEATS = [
    ("MRDIMMs drop into the same DDR5 slots, with more bandwidth",
     "Server CPUs like Intel Xeon 6 and AMD's next EPYC are starved for memory bandwidth as core counts climb past "
     "128. An MRDIMM plugs into a normal DDR5 slot but delivers up to twice the data rate, so each channel feeds "
     "more cores without adding pins to the CPU."),
    ("Two ranks of standard DDR5 chips behind a mux buffer",
     "The module holds two ranks: two independent sets of ordinary DDR5 chips. An MRCD chip in the middle handles "
     "address and command for both, and a row of MDB data-buffer chips sits between the DRAM and the gold fingers."),
    ("Both ranks read at once; the buffers interleave them",
     "On a normal RDIMM only one rank talks at a time. On an MRDIMM both ranks run at their usual speed together, "
     "and the MDB chips merge the two streams, sending one word from rank A, then one from rank B. The CPU side "
     "of the bus runs at twice the DRAM's own rate."),
    ("8800 MT/s now, 12800 MT/s next, from the same DRAM",
     "First-generation MRDIMMs run at 8800 MT/s against 6400 for a standard RDIMM, close to 40% more bandwidth per "
     "channel. The next generation targets 12800 MT/s. Memory-bound jobs like CPU-side AI inference and databases "
     "gain the most."),
    ("The buffer chips are the new content",
     "The DRAM is standard, so the extra value sits in the MRCD and MDB chips, a business led by Rambus and Montage "
     "with Renesas. Memory makers sell the modules at a premium. Related: Rambus (RMBS), Montage Technology "
     "(688008.SS), Micron (MU), SK hynix (000660.KS)."),
]


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    m["rA"] = mat("t_mr_rA", (0.35, 0.70, 1.0), emit=(0.35, 0.70, 1.0), strength=3.5)
    m["rB"] = mat("t_mr_rB", (1.0, 0.62, 0.18), emit=(1.0, 0.62, 0.18), strength=2.5)
    S.mobo(m, root, x1=180.0)
    S.cpu(m, root, hot=[0, 2])
    dp = {}
    for i, x in enumerate(S.LEFT + S.RIGHT):
        _, dp[i] = S.dimm(m, root, f"d{i}", x, chips=8, h=40.0, rows=2)
    d = dp[7]
    x = S.RIGHT[-1]
    mdb = []
    for k in range(8):  # MDB row between chips and fingers
        z = S.DZ0 + 6 + k * 12.0 + (6.0 if k >= 4 else 0.0)
        bx(f"mdb{k}", (x + 0.6, 7.2, z - 2.5), (x + 2.0, 8.8, z + 2.5), m["fet"], root)
        mdb.append((x + 2.0, 8.0, z))
    paths = S.bus(m, root, "busL", S.LEFT) + S.bus(m, root, "busR", S.RIGHT)
    for k, p in enumerate(paths):
        run(root, f"rd{k}", p, 6, 0.8, m["dram_bead"], [0, 2], 0.0, 0.85, 35)
    ch = d["chips"]  # 8 per row, rows 0 (low, rank A) and 1 (high, rank B)
    for k in range(8):
        a, b, t = ch[k], ch[8 + k], mdb[k]
        run(root, f"rA{k}", [a, t], 6, 1.2, m["rA"], 2, 0.0, 0.8, 26)
        run(root, f"rB{k}", [b, t], 6, 1.2, m["rB"], 2, 0.05, 0.85, 26)
        out = [t, (x + 2.0, 6.0, t[2])]
        run(root, f"rO{k}", out, 12, 1.0, m["sig"], 2, 0.1, 0.9, 10)

    tops = [S.bar(m, root, "r0", 95.0, -60.0, 14.0, 6400 / 200.0, "steel", 3, 5),
            S.bar(m, root, "r1", 123.0, -60.0, 14.0, 8800 / 200.0, "copper", 3, 5),
            S.bar(m, root, "r2", 151.0, -60.0, 14.0, 12800 / 200.0, "gold", 3, 5)]

    C.tags(root, {
        0: [("MRDIMMs in standard DDR5 slots", dp[0]["top"]), ("CPU: more cores per channel", (S.CPU[0], 6.4, S.CPU[2]))],
        1: [("rank A: DDR5 chips", ch[2]), ("rank B: DDR5 chips", ch[12]), ("MRCD: command for both", d["buf"]),
            ("MDB data buffers", mdb[6])],
        2: [("rank A and B read together", ch[5]), ("MDB interleaves A, B, A, B", mdb[1]),
            ("CPU bus at 2x DRAM rate", paths[13][2])],
        3: [("RDIMM 6400 MT/s", tops[0]), ("MRDIMM 8800 MT/s", tops[1]), ("next gen 12800 MT/s", tops[2])],
        4: [("buffers: Rambus, Montage", mdb[3]), ("DRAM: Micron, SK hynix", ch[10])],
    })
    C.done(SLUG, BEATS, [
        frame((-50.0, 8.0, -50.0), 200.0, 0.30, 0.65),
        frame((18.0, 22.0, -50.0), 110.0, 0.55, 0.20),
        frame((18.0, 14.0, -50.0), 90.0, 0.60, 0.55),
        frame((123.0, 25.0, -60.0), 100.0, 0.20, 0.30),
        frame((-10.0, 10.0, -50.0), 200.0, 0.45, 0.35),
    ], root)


if __name__ == "__main__":
    build()
