"""Intent classifier for Cognitive Layer v1.

Implements bootstrapped local fine-tuning on top of DistilBERT.

Runtime behavior:
- loads a locally fine-tuned checkpoint if present
- otherwise falls back to keyword-based intent routing

This keeps the system LLM-free.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

from scripts.cognitive_layer.dataset_builder import build_intent_dataset

logger = logging.getLogger(__name__)


DEFAULT_CHECKPOINT_DIR = os.getenv(
    "NEURONIX_INTENT_MODEL_DIR", "data/cognitive_layer/intent_distilbert"
)


@dataclass
class IntentPrediction:
    intent: str
    confidence: float


class LocalIntentClassifier:
    """Local intent classifier (no external LLMs)."""

    def __init__(
        self,
        model_dir: str = DEFAULT_CHECKPOINT_DIR,
        base_model: str = "distilbert-base-uncased",
    ):
        self.model_dir = model_dir
        self.base_model = base_model

        self.intent_labels = [
            "mental_health",
            "learning",
            "crisis",
            "general",
        ]

        self._tokenizer = None
        self._model = None

        self._load_if_available()

    def _load_if_available(self) -> None:
        if not os.path.isdir(self.model_dir):
            logger.info(f"[IntentClassifier] No local checkpoint at {self.model_dir}; using fallback rules.")
            return
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_dir)
            self._model.eval()
            logger.info(f"[IntentClassifier] Loaded local checkpoint from {self.model_dir}")
        except Exception as e:
            logger.warning(f"[IntentClassifier] Failed to load checkpoint; fallback rules. Error: {e}")
            self._tokenizer = None
            self._model = None

    def train_bootstrap(self, output_dir: Optional[str] = None, epochs: int = 3) -> str:
        """Fine-tune using the bootstrapping dataset.

        Returns the output directory used.
        """
        output_dir = output_dir or self.model_dir

        dataset = build_intent_dataset()

        label_to_id = {lab: i for i, lab in enumerate(self.intent_labels)}

        # Tokenization
        self._tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        model = AutoModelForSequenceClassification.from_pretrained(
            self.base_model,
            num_labels=len(self.intent_labels),
            id2label={i: lab for lab, i in label_to_id.items()},
            label2id=label_to_id,
        )

        texts = [d.text for d in dataset]
        labels = [label_to_id[d.label] for d in dataset]

        enc = self._tokenizer(texts, padding=True, truncation=True, max_length=128)

        class _Dataset(torch.utils.data.Dataset):
            def __init__(self, encodings, labels):
                self.encodings = encodings
                self.labels = labels

            def __len__(self):
                return len(self.labels)

            def __getitem__(self, idx):
                item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
                item["labels"] = torch.tensor(self.labels[idx])
                return item

        ds = _Dataset(enc, labels)

        args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=8,
            save_strategy="epoch",
            logging_steps=10,
            learning_rate=2e-5,
            weight_decay=0.01,
            fp16=False,
            report_to=[],
        )

        trainer = Trainer(model=model, args=args, train_dataset=ds)
        trainer.train()

        trainer.save_model(output_dir)
        self._model = AutoModelForSequenceClassification.from_pretrained(output_dir)
        self._model.eval()
        logger.info(f"[IntentClassifier] Trained model saved to {output_dir}")

        return output_dir

    def predict(self, text: str) -> IntentPrediction:
        """Predict intent with confidence. No LLM calls."""
        # If model available, use it.
        if self._model is not None and self._tokenizer is not None:
            with torch.no_grad():
                batch = self._tokenizer(
                    [text], padding=True, truncation=True, max_length=128, return_tensors="pt"
                )
                logits = self._model(**batch).logits
                probs = torch.softmax(logits, dim=-1).squeeze(0).tolist()
                best_i = int(torch.argmax(logits, dim=-1).item())
                return IntentPrediction(intent=self.intent_labels[best_i], confidence=float(probs[best_i]))

        # Fallback: use existing keyword router
        from scripts.intent_router import IntentRouter

        router = IntentRouter()
        res = router.classify_intent(text)
        return IntentPrediction(intent=res["intent"].value, confidence=float(res["confidence"]))

