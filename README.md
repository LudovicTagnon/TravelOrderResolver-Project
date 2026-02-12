# Travel Order Resolver

Projet EPITECH NLP + pathfinding ferroviaire.
Le pipeline vise a :
- extraire `origine/destination` depuis une phrase (`id,phrase`)
- produire `id,origine,destination` ou `id,INVALID,`
- calculer un chemin entre gares a partir des donnees GTFS

## Structure utile
- `src/travel_order_resolver.py` : baseline NLP rule-based (CLI).
- `scripts/` : generation de donnees, evaluation, GTFS, pathfinding, baseline ML.
- `datasets/` : datasets synthetiques (`train/dev/test`) + starter manuel.
- `data/` : listes de lieux, index gares, artefacts derives.
- `reports/` : metriques rule-based et ML.
- `docs/` : guide d'annotation + draft du rapport.

## Pre-requis
- Python 3.10+
- Dependances utilisees dans ce repo : `scikit-learn`, `joblib`, `openpyxl`

## Format de donnees
- Entree NLP : `id,phrase`
- Sortie NLP : `id,origine,destination` ou `id,INVALID,`
- Encodage : UTF-8

Exemple :
```text
1,je voudrais aller de Toulouse a Bordeaux
1,Toulouse,Bordeaux
```

## Workflow 1 - Baseline NLP (rule-based)
```bash
python3 src/travel_order_resolver.py --places data/places.txt < students_project/sample_nlp_input.txt
python3 scripts/evaluate.py --input datasets/dev_input.txt --expected datasets/dev_output.txt
python3 scripts/run_benchmarks.py
```
Resultats consolides : `reports/metrics.json`.

## Workflow 2 - Dataset manuel (annotation humaine)
Generer un starter :
```bash
python3 scripts/bootstrap_manual_dataset.py --source datasets/all_input.txt --count 120 --output-input datasets/manual/input_starter.csv --output-template datasets/manual/output_template.csv
```
Verifier la coherence apres annotation :
```bash
python3 scripts/validate_manual_dataset.py --input datasets/manual/input_starter.csv --output datasets/manual/output_template.csv
```
Guides : `docs/annotation_guide.md`, `docs/manual_dataset_template.md`.

Prefill automatique pour accelerer l'annotation (a relire/corriger manuellement) :
```bash
python3 src/travel_order_resolver.py --places data/places.txt - < datasets/manual/input_starter.csv > datasets/manual/output_prefill_120.csv
python3 scripts/validate_manual_dataset.py --input datasets/manual/input_starter.csv --output datasets/manual/output_prefill_120.csv
```

Construire une feuille de relecture priorisee :
```bash
python3 scripts/build_manual_review_sheet.py --input datasets/manual/input_starter.csv --prefill datasets/manual/output_prefill_120.csv --model-dir models --output datasets/manual/review_sheet_120.csv --output-actionable datasets/manual/review_actionable_120.csv --summary reports/manual_review_summary.json
```
`review_actionable_120.csv` contient uniquement les cas haute/moyenne priorite.

Evaluer sur un lot annote (exemple 50 lignes) :
```bash
python3 scripts/evaluate.py --input datasets/manual/input_annotated_50.csv --expected datasets/manual/output_annotated_50.csv --format json > reports/manual_metrics_rule_based.json
python3 scripts/evaluate_ml.py --input datasets/manual/input_annotated_50.csv --expected datasets/manual/output_annotated_50.csv --model-dir models --format json > reports/manual_metrics_ml.json
```

## Workflow 3 - GTFS et pathfinding
1) Recuperer GTFS :
```bash
python3 scripts/fetch_gtfs.py --extract
```
2) Construire index gares et graphe :
```bash
python3 scripts/build_stop_index.py --input stops.xlsx --output-csv data/stops_areas.csv --output-json data/stops_index.json
python3 scripts/build_graph.py --stop-times data/gtfs/stop_times.txt --stops data/gtfs/stops.txt --output data/graph.json
```
3) Lancer pathfinding :
```bash
python3 scripts/pathfind.py --graph data/graph.json --stops-index data/stops_index.json --input path/to/triplets.csv
```
4) Generer/valider un echantillon de reference :
```bash
python3 scripts/sample_triplets.py --graph data/graph.json --stops-areas data/stops_areas.csv --count 30 --output-triplets datasets/path_triplets.csv --output-expected datasets/path_expected.csv
python3 scripts/validate_pathfinding.py --graph data/graph.json --stops-index data/stops_index.json --triplets datasets/path_triplets.csv --expected datasets/path_expected.csv
```

## Workflow 4 - Baseline ML (reference)
```bash
python3 scripts/train_ml.py --train-input datasets/train_input.txt --train-output datasets/train_output.txt --model-dir models
python3 scripts/run_ml_benchmarks.py --datasets datasets --model-dir models --output reports/ml_metrics.json
```
Resultats : `reports/ml_metrics.json`.

## Tests
```bash
python3 -m unittest discover -s tests
```

## Etat actuel
- Baseline rule-based : solide sur le dataset synthetique (`reports/metrics.json`).
- Baseline ML actuel : inferieur au rule-based (`reports/ml_metrics.json`), sert de reference.
- Lot annote 50 lignes : rule-based `1.00` (`reports/manual_metrics_rule_based.json`), ML `0.50` (`reports/manual_metrics_ml.json`).
- Prefill 120 lignes : `datasets/manual/output_prefill_120.csv` (5 lignes marquees INVALID, IDs dans `reports/manual_prefill_invalid_ids.txt`).
- Relecture 120 lignes : `datasets/manual/review_sheet_120.csv` + shortlist `datasets/manual/review_actionable_120.csv` (22 cas actionnables, `reports/manual_review_summary.json`).
- Metriques "self-check" sur prefill 120 (coherence technique, pas qualite humaine) : `reports/manual_prefill_metrics_rule_based.json`, `reports/manual_prefill_metrics_ml.json`.
- Pathfinding echantillon 30 trajets : `1.00` (`reports/pathfinding_metrics.txt`).
- Draft rapport : `docs/report_draft.md`.
