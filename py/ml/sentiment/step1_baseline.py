"""Step 1: baseline macro-F1 of the base checkpoint on tweet_eval sentiment."""

from common import LABELS, cached_logits, load_model, metrics, predict_logits, save_json

tok, model = load_model()

# Label-mapping sanity check: the config only says LABEL_0..2, the model card says 0=neg 1=neu 2=pos.
probe = ["I absolutely love this, best day ever!", "This is awful and I hate it.", "The meeting is at 3pm."]
probe_pred = predict_logits(model, tok, probe).argmax(1)
for t, p in zip(probe, probe_pred):
    print(f"  {LABELS[p]:<9} <- {t}")

results = {}
for split in ("validation", "test"):
    logits, y = cached_logits("base", model, tok, split)
    pred = logits.argmax(1)
    results[split] = metrics(y, pred)
    print(f"{split}: macro-F1={results[split]['macro_f1']:.4f} acc={results[split]['accuracy']:.4f} n={len(y)}")
    print("  confusion (rows=true neg/neu/pos, cols=pred):")
    for row in results[split]["confusion"]:
        print("   ", row)

print("wrote", save_json("step1_baseline", results))
