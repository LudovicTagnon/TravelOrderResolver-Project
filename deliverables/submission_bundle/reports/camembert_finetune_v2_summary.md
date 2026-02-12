# Benchmark CamemBERT fine-tune v2

Source: `reports/camembert_finetune_v2_metrics.json`

## Setup
- Base model: `camembert-base`
- Deux classifieurs separes: `origin` et `destination`
- Train: `8000` phrases, `2` epochs, batch `16`, max_len `64`, lr `2e-5`

## Resultats
- Dev: accuracy `0.981`, valid_f1 `0.978`
- Test: accuracy `0.973`, valid_f1 `0.968`

## Comparaison rapide
- CamemBERT fine-tune v1 (rapide): test accuracy `0.735`
- spaCy (`fr_core_news_sm`): test accuracy `0.693`
- ML baseline: test accuracy `0.418`
- Rule-based: test accuracy `0.993`

Conclusion courte: ce setup v2 rapproche fortement CamemBERT du rule-based, tout en restant legerement en dessous sur le test synthetique.
