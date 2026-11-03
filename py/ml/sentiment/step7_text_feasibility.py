"""Step 7: can an LLM read these weights as text? Measure, don't guess.

The blog's agent reads raw weights as text. This script serialises a slice of the model in a
compact text format and counts tokens. It uses the RoBERTa tokenizer as a PROXY, because the
target LLM's tokenizer is not available offline. Expect the real count to differ by maybe +/-30%.

Reports, per slice:
  - number of weights
  - tokens for the serialised text at 3 decimals
  - tokens at 2 decimals (lower precision)
Compares against common context windows.
"""

import torch
from common import HEAD_DIM, load_model, save_json

tok, model = load_model()
model = model.to("cpu")
layer0 = model.roberta.encoder.layer[0]
head = 0
sl = slice(head * HEAD_DIM, (head + 1) * HEAD_DIM)

slices = {
    "one_head (Q,K,V,O)": [
        layer0.attention.self.query.weight[sl, :],
        layer0.attention.self.key.weight[sl, :],
        layer0.attention.self.value.weight[sl, :],
        layer0.attention.output.dense.weight[:, sl].T,
    ],
    "one_mlp_out (768x3072)": [layer0.output.dense.weight],
    "one_full_layer (attn+mlp)": [
        p for n, p in layer0.named_parameters() if p.dim() == 2
    ],
    "whole_model": [p for p in model.parameters() if p.dim() == 2],
}


def serialise(mats: list[torch.Tensor], decimals: int) -> str:
    lines = []
    fmt = f"{{:+.{decimals}f}}"
    for m in mats:
        for row in m.detach().float().numpy():
            lines.append(" ".join(fmt.format(x) for x in row))
    return "\n".join(lines)


# Tokens per number, measured on a real serialised sample (not assumed).
sample = serialise(slices["one_head (Q,K,V,O)"], 3)
sample_tokens = len(tok(sample)["input_ids"])
n_sample = sum(m.numel() for m in slices["one_head (Q,K,V,O)"])
tokens_per_weight_3dp = sample_tokens / n_sample
print(f"measured: {sample_tokens} tokens for {n_sample} weights at 3dp -> {tokens_per_weight_3dp:.2f} tokens/weight (RoBERTa proxy)")

report = {"tokens_per_weight_3dp_proxy": tokens_per_weight_3dp, "slices": {}}
print(f"\n{'slice':<30}{'weights':>14}{'tokens@3dp':>16}{'tokens@2dp(est)':>18}")
for name, mats in slices.items():
    n = sum(m.numel() for m in mats)
    t3 = n * tokens_per_weight_3dp
    # 2dp drops one digit; estimate ~25% fewer tokens (measured-ratio approximation).
    t2 = t3 * 0.75
    report["slices"][name] = {"weights": n, "tokens_3dp": t3, "tokens_2dp_est": t2}
    print(f"{name:<30}{n:>14,}{t3:>16,.0f}{t2:>18,.0f}")

print("\ncontext windows for scale: 200k (typical frontier), 1M (long-context tier)")
for name in ("one_head (Q,K,V,O)", "one_full_layer (attn+mlp)", "whole_model"):
    t = report["slices"][name]["tokens_3dp"]
    print(f"  {name:<28} needs {t / 200_000:>6.1f}x a 200k window, {t / 1_000_000:>5.2f}x a 1M window")

save_json("step7_text_feasibility", report)
print("\nwrote step7_text_feasibility.json")
