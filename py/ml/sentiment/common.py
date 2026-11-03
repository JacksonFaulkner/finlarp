"""Shared helpers for the cardiffnlp/twitter-roberta-base-sentiment experiments.

Data: cardiffnlp/tweet_eval, config "sentiment" (labels 0=neg, 1=neu, 2=pos).
Weights: data/models/<model>/ (downloaded by hand from the Hugging Face hub).
Outputs: data/ml/sentiment/{cache,results}/ (gitignored).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from datasets import load_dataset
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer

REPO = Path(__file__).resolve().parents[3]
MODEL_DIR = REPO / "data/models/cardiffnlp-twitter-roberta-base-sentiment"
OUT = REPO / "data/ml/sentiment"
CACHE = OUT / "cache"
RESULTS = OUT / "results"
LABELS = ["negative", "neutral", "positive"]
MAX_LEN = 128
N_HEADS = 12
HEAD_DIM = 64

for _d in (CACHE, RESULTS):
    _d.mkdir(parents=True, exist_ok=True)


def device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def preprocess(text: str) -> str:
    """Same normalisation as the model card: @mentions -> @user, URLs -> http."""
    out = []
    for tok in text.split(" "):
        if tok.startswith("@") and len(tok) > 1:
            tok = "@user"
        elif tok.startswith("http"):
            tok = "http"
        out.append(tok)
    return " ".join(out)


def load_split(split: str) -> tuple[list[str], np.ndarray]:
    """Raw tweet texts and integer labels for a tweet_eval sentiment split."""
    ds = load_dataset("cardiffnlp/tweet_eval", "sentiment", split=split)
    return list(ds["text"]), np.array(ds["label"])


def load_model(model_dir: Path = MODEL_DIR):
    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir, attn_implementation="eager")
    model.eval().to(device())
    return tok, model


@torch.inference_mode()
def predict_logits(model, tok, texts: list[str], bs: int = 128) -> np.ndarray:
    """Logits for raw texts, batched by length to limit padding. Order preserved."""
    proc = [preprocess(t) for t in texts]
    order = np.argsort([len(t) for t in proc])
    out = np.zeros((len(texts), model.config.num_labels), dtype=np.float32)
    dev = next(model.parameters()).device
    for start in range(0, len(order), bs):
        idx = order[start : start + bs]
        enc = tok([proc[i] for i in idx], padding=True, truncation=True, max_length=MAX_LEN, return_tensors="pt")
        enc = {k: v.to(dev) for k, v in enc.items()}
        out[idx] = model(**enc).logits.float().cpu().numpy()
    return out


def cached_logits(name: str, model, tok, split: str) -> tuple[np.ndarray, np.ndarray]:
    """Logits + labels for a split, cached under data/ml/sentiment/cache/<name>_<split>.npz."""
    path = CACHE / f"{name}_{split}.npz"
    texts, y = load_split(split)
    if path.exists():
        z = np.load(path)
        return z["logits"], z["y"]
    logits = predict_logits(model, tok, texts)
    np.savez(path, logits=logits, y=y)
    return logits, y


def metrics(y: np.ndarray, pred: np.ndarray) -> dict:
    return {
        "macro_f1": float(f1_score(y, pred, average="macro")),
        "accuracy": float(accuracy_score(y, pred)),
        "confusion": confusion_matrix(y, pred, labels=[0, 1, 2]).tolist(),
        "n": int(len(y)),
    }


def save_json(name: str, obj) -> Path:
    path = RESULTS / f"{name}.json"
    path.write_text(json.dumps(obj, indent=2))
    return path
