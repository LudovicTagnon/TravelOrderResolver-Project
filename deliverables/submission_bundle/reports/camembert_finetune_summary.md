# Benchmark CamemBERT fine-tune

Source: `reports/camembert_finetune_metrics.json`

## Setup
- Base model: `camembert-base`
- Cible: deux classifieurs separes (`origin` et `destination`)
- Train rapide: `4000` phrases, `1` epoch, batch `16`, max_len `64`

## Resultats
- Dev: accuracy `0.733`, valid_f1 `0.753`
- Test: accuracy `0.735`, valid_f1 `0.751`

## Reference rapide
- Rule-based test accuracy: `0.993` (`reports/metrics.json`)
- ML baseline test accuracy: `0.418` (`reports/ml_metrics.json`)
- spaCy test accuracy: `0.693` (`reports/spacy_camembert_metrics.json`)

Conclusion courte: ce fine-tuning CamemBERT depasse les baselines ML et spaCy tests, mais reste en dessous du rule-based principal.
