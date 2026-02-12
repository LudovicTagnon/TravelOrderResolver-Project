# Benchmark spaCy vs CamemBERT

Source: `reports/spacy_camembert_metrics.json`

## spaCy (`fr_core_news_sm`)
- Dev: accuracy `0.694`, valid_f1 `0.775`
- Test: accuracy `0.693`, valid_f1 `0.771`

## CamemBERT (`camembert-base` + embeddings figes + LinearSVC)
- Train setup: `4000` phrases (`models/camembert/metadata.json`)
- Dev: accuracy `0.482`, valid_f1 `0.409`
- Test: accuracy `0.498`, valid_f1 `0.418`

## Reference
- Rule-based test accuracy: `0.993` (`reports/metrics.json`)
- ML baseline test accuracy: `0.418` (`reports/ml_metrics.json`)

Conclusion courte: dans cet etat, spaCy est le meilleur des deux nouveaux tests, CamemBERT non fine-tune n'apporte pas encore de gain décisif.
