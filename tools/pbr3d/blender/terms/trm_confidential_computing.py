"""TRM_CONFIDENTIAL_COMPUTING: the Terms-tab overview for confidential computing (whole-VM, data in use).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_confidential_computing.py

Writes assets/term_TRM_CONFIDENTIAL_COMPUTING.glb. Captions live in specs/terms/TRM_CONFIDENTIAL_COMPUTING.json.

Where a TEE is a small sealed region inside a chip, confidential computing wraps a whole virtual
machine: its memory is encrypted, the hypervisor and host see only ciphertext, and the data is
decrypted only inside the CPU while it is being processed. The bench shows the stack: host
hypervisor underneath, the encrypted VM on top, and the data in use inside it.

Beats:
  0 board     the host CPU and GPU of an AI server share the board with other tenants' hardware
  1 cut-open  the stack on the bench: hypervisor below, one encrypted VM block above
  2 in use    a prompt enters encrypted, is decrypted inside the VM, and only ciphertext leaves
  3 GPU       the CPU-to-GPU link is encrypted and the GPU runs in a protected mode
  4 vendors   Intel TDX, AMD SEV-SNP and NVIDIA confidential GPU modes
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_trust as K  # noqa: E402
from sand_overview import F, empty, show  # noqa: E402
from power_vrm_detail import blink, frame, run  # noqa: E402

SLUG = "TRM_CONFIDENTIAL_COMPUTING"
BEATS = [
    ("An AI server's CPU and GPU run other tenants' work on shared hardware",
     "In a cloud AI server, many customers' jobs share the same machines. Model weights and customer prompts sit in memory "
     "that the cloud operator's hypervisor and host software control. Confidential computing removes that operator from "
     "the trust boundary for data while it is being used."),
    ("The whole virtual machine is the protected unit",
     "The CPU encrypts the memory of one virtual machine with a key the hypervisor never sees. Below it, the host "
     "hypervisor and operating system manage the hardware, but everything they read from guest memory is ciphertext. "
     "A TEE protects a small sealed region; this protects a whole VM, so existing software runs without changes."),
    ("Data is decrypted only inside the CPU, while it is being processed",
     "A prompt arrives encrypted and is decrypted inside the protected VM, where the model can use it. Anything that "
     "leaves the VM, to memory or back to the host, is encrypted again. That is the 'data in use' gap this closes: "
     "encryption at rest and in transit were already standard."),
    ("The CPU-to-GPU link and the GPU memory are protected too",
     "Newer accelerators add a confidential mode: the bus between CPU and GPU is encrypted, and model weights in GPU memory "
     "are shielded from the host. Without this, the weights would be exposed the moment they reach the accelerator."),
    ("Intel, AMD and NVIDIA ship it; clouds sell it",
     "Intel TDX and AMD SEV-SNP protect the VM on the CPU, and NVIDIA's confidential GPU mode covers the accelerator. "
     "Microsoft (MSFT) and other clouds offer it as a product. Vendors: Intel (INTC), AMD (AMD), NVIDIA (NVDA), Microsoft (MSFT). "
     "Performance cost and attestation work are the trade-offs."),
]

BENCH_Y = (0.6, 3.0)
HV = (160.0, 238.0, -36.0, -4.0)
VM = (166.0, 232.0, -32.0, -8.0)
VM_Y = (3.0, 20.0)
CLEAR = (178.0, 220.0, -26.0, -14.0)
CLEAR_Y = (4.0, 12.0)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    b = C.base(m, root, decap=False)
    pk = b["pk"]

    bench = empty("cc_bench", root)
    K.die(m, bench, "cc_hyp", HV[0], HV[1], HV[2], HV[3], BENCH_Y[0], BENCH_Y[1], mt="trust_core")
    vm_enc = K.vm_box(m, bench, "cc_vm_enc", (VM[0], VM_Y[0], VM[2]), (VM[1], VM_Y[1], VM[3]), encrypted=True)
    vm_clr = K.vm_box(m, bench, "cc_vm_clr", (CLEAR[0], CLEAR_Y[0], CLEAR[2]), (CLEAR[1], CLEAR_Y[1], CLEAR[3]),
                      encrypted=False)
    show(bench, [(F(1, 0), F(5, 0))])
    show(vm_enc["group"], [(F(1, 0), F(2, 0)), (F(3, 0), F(5, 0))])
    show(vm_clr["group"], [(F(2, 0), F(3, 0))])

    # beat 2: encrypted prompt in, plaintext inside, ciphertext out
    run(root, "p_in", [(250.0, 8.0, -20.0), (234.0, 9.0, -20.0), (232.0, 10.0, -20.0)], 2, 0.8, m["trust_cipher"],
        2, 0.1, 0.4, 25, until=F(3, 0))
    run(root, "p_clear", [(216.0, 14.0, -20.0), (196.0, 14.0, -20.0), (180.0, 10.0, -20.0)], 3, 0.8,
        m["trust_clear"], 2, 0.3, 0.7, 35, until=F(3, 0))
    run(root, "p_out", [(234.0, 8.0, -20.0), (250.0, 8.0, -20.0)], 2, 0.8, m["trust_cipher"], 2, 0.8, 0.95, 25,
        until=F(3, 0))

    # beat 3: encrypted CPU-to-GPU link, the GPU in protected mode
    run(root, "bus", [(190.0, 8.0, -20.0), (150.0, 40.0, -20.0), (120.0, 30.0, -20.0), pk["top"]], 4, 0.9,
        m["trust_cipher"], 3, 0.1, 0.8, 70)
    show(b["die_glow"], [(F(3, 0.3), F(5, 0))])

    C.tags(root, {
        0: [("host CPU + GPU, shared", pk["top"]), ("hypervisor sits outside", (-70.0, 2.0, -70.0)),
            ("operator outside the trust boundary", (-20.0, 6.0, -40.0))],
        1: [("whole VM encrypted: one unit", (199.0, 14.0, -20.0)), ("hypervisor: ciphertext only", (200.0, 2.0, -34.0)),
            ("key the host never sees", (232.0, 20.0, -20.0))],
        2: [("prompt in, encrypted", (240.0, 9.0, -20.0)), ("decrypted only inside the VM", (196.0, 14.0, -20.0)),
            ("ciphertext leaves", (240.0, 8.0, -28.0))],
        3: [("encrypted CPU-to-GPU bus", (150.0, 40.0, -20.0)), ("GPU memory shielded", pk["top"]),
            ("weights never in the clear", (-70.0, 8.0, -110.0))],
        4: [("Intel TDX (INTC), AMD SEV-SNP (AMD)", (199.0, 14.0, -20.0)), ("NVIDIA GPU mode (NVDA)", pk["top"]),
            ("clouds: Microsoft (MSFT)", (-70.0, 8.0, -110.0))],
    })
    C.done(SLUG, BEATS, [
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.65, pad=1.0),
        frame((199.0, 10.0, -20.0), 110.0, 0.25, 0.22),
        frame((199.0, 10.0, -20.0), 110.0, 0.25, 0.22),
        frame((150.0, 20.0, -20.0), 280.0, 0.30, 0.45, pad=1.0),
        frame((60.0, 0.0, -70.0), 330.0, 0.25, 0.45, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()
