"""Step 2: per-class logit offsets (bias calibration).

Grid-search offsets for negative and neutral (positive fixed at 0) to maximise macro-F1 on
the VALIDATION split. Test is scored once, at the end.
"""

import numpy as np
from common import cached_logits, load_model, metrics, save_json

tok, model = load_model()
val_logits, val_y = cached_logits("base", model, tok, "validation")
test_logits, test_y = cached_logits("base", model, tok, "test")

grid = np.round(np.arange(-1.0, 1.0001, 0.05), 3)
best = (-1.0, np.zeros(3, dtype=np.float32))
for b_neg in grid:
    for b_neu in grid:
        offs = np.array([b_neg, b_neu, 0.0], dtype=np.float32)
        f1 = metrics(val_y, (val_logits + offs).argmax(1))["macro_f1"]
        if f1 > best[0]:
            best = (f1, offs)

offs = best[1]
print(f"best offsets (neg, neu, pos) = {offs.tolist()}  val macro-F1 {best[0]:.4f}")
print(f"val  baseline {metrics(val_y, val_logits.argmax(1))['macro_f1']:.4f} -> calibrated {best[0]:.4f}")

test_base = metrics(test_y, test_logits.argmax(1))
test_cal = metrics(test_y, (test_logits + offs).argmax(1))
print(f"test baseline macro-F1 {test_base['macro_f1']:.4f}  calibrated {test_cal['macro_f1']:.4f}  "
      f"delta {test_cal['macro_f1'] - test_base['macro_f1']:+.4f}")
print("test calibrated confusion (rows=true neg/neu/pos):")
for row in test_cal["confusion"]:
    print("   ", row)

save_json("step2_calibration", {
    "offsets_neg_neu_pos": offs.tolist(),
    "val_macro_f1_baseline": metrics(val_y, val_logits.argmax(1))["macro_f1"],
    "val_macro_f1_calibrated": best[0],
    "test_baseline": test_base,
    "test_calibrated": test_cal,
})
