#!/usr/bin/env python3
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class CamembertFineTunePredictor:
    def __init__(
        self,
        origin_model_dir: Path,
        destination_model_dir: Path,
        batch_size: int = 32,
        max_length: int = 64,
    ):
        self.batch_size = batch_size
        self.max_length = max_length
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.origin_tokenizer = AutoTokenizer.from_pretrained(origin_model_dir)
        self.destination_tokenizer = AutoTokenizer.from_pretrained(destination_model_dir)
        self.origin_model = AutoModelForSequenceClassification.from_pretrained(origin_model_dir).to(
            self.device
        )
        self.destination_model = AutoModelForSequenceClassification.from_pretrained(
            destination_model_dir
        ).to(self.device)

    def _predict_labels(
        self,
        model,
        tokenizer,
        sentence_ids: list[str],
        sentences: list[str],
    ) -> dict[str, str]:
        model.eval()
        predicted = {}
        for start in range(0, len(sentences), self.batch_size):
            batch_sentences = sentences[start : start + self.batch_size]
            batch_ids = sentence_ids[start : start + self.batch_size]
            encoded = tokenizer(
                batch_sentences,
                truncation=True,
                padding=True,
                max_length=self.max_length,
                return_tensors="pt",
            )
            encoded = {key: value.to(self.device) for key, value in encoded.items()}
            with torch.no_grad():
                logits = model(**encoded).logits
                predictions = logits.argmax(dim=1).cpu().tolist()
            for sentence_id, prediction in zip(batch_ids, predictions):
                predicted[sentence_id] = model.config.id2label[int(prediction)]
        return predicted

    def predict_batch(self, sentence_ids: list[str], sentences: list[str]) -> dict[str, tuple[str, str]]:
        origins = self._predict_labels(
            model=self.origin_model,
            tokenizer=self.origin_tokenizer,
            sentence_ids=sentence_ids,
            sentences=sentences,
        )
        destinations = self._predict_labels(
            model=self.destination_model,
            tokenizer=self.destination_tokenizer,
            sentence_ids=sentence_ids,
            sentences=sentences,
        )

        predictions = {}
        for sentence_id in sentence_ids:
            origin = origins.get(sentence_id, "INVALID")
            destination = destinations.get(sentence_id, "INVALID")
            if origin == "INVALID" or destination == "INVALID":
                predictions[sentence_id] = ("INVALID", "INVALID")
            else:
                predictions[sentence_id] = (origin, destination)
        return predictions

    def predict_sentence(self, sentence: str) -> tuple[str | None, str | None]:
        prediction = self.predict_batch(["0"], [sentence]).get("0", ("INVALID", "INVALID"))
        if prediction[0] == "INVALID" or prediction[1] == "INVALID":
            return None, None
        return prediction
