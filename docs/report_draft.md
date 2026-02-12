# Travel Order Resolver - Rapport (draft)

## 1. Architecture
- `src/travel_order_resolver.py` : extraction NLP baseline (origin/destination) rule-based.
- `scripts/train_ml.py` + `scripts/evaluate_ml.py` : baseline ML (char n-grams + LinearSVC).
- `scripts/build_stop_index.py` : index gares (`stop_name -> stop_ids`) depuis `stops.xlsx`.
- `scripts/build_graph.py` : graphe de connectivite depuis `stop_times.txt` GTFS.
- `scripts/pathfind.py` : plus court chemin (BFS) entre gares.

## 2. Jeux de donnees
- Synthese principale : `datasets/all_input.txt`, `datasets/all_output.txt`.
- Splits : `datasets/train_*`, `datasets/dev_*`, `datasets/test_*`.
- Starter annotation manuelle :
  - `datasets/manual/input_starter.csv` (120 phrases)
  - `datasets/manual/output_template.csv` (template vide)
- Lot annote :
  - `datasets/manual/input_annotated_50.csv`
  - `datasets/manual/output_annotated_50.csv`

## 3. Metriques NLP (baseline rule-based)
Source : `reports/metrics.json`.

- Train : accuracy `0.971`, valid_f1 `0.979`, invalid_accuracy `1.000`
- Dev : accuracy `0.979`, valid_f1 `0.984`, invalid_accuracy `1.000`
- Test : accuracy `0.978`, valid_f1 `0.986`, invalid_accuracy `1.000`

## 4. Metriques NLP (baseline ML)
Source : `reports/ml_metrics.json`.

- Train : accuracy `0.703`, valid_f1 `0.656`, invalid_accuracy `0.950`
- Dev : accuracy `0.404`, valid_f1 `0.328`, invalid_accuracy `0.887`
- Test : accuracy `0.418`, valid_f1 `0.338`, invalid_accuracy `0.876`

Constat : le baseline ML actuel est nettement inferieur au baseline rule-based.

## 5. Exemple de pipeline
- Entree : `id,phrase`
- Sortie NLP : `id,origin,destination` ou `id,INVALID,`
- Sortie pathfinding : `id,Step0,Step1,...,StepN`

## 6. Evaluation sur lot annote (50)
Sources : `reports/manual_metrics_rule_based.json`, `reports/manual_metrics_ml.json`.

- Rule-based : accuracy `1.000`, valid_f1 `1.000`
- ML baseline : accuracy `0.500`, valid_f1 `0.500`

Constat : sur ce lot, le baseline rule-based reste largement devant.

## 7. Pathfinding
- Donnees d'entree : GTFS (`stops.txt`, `stop_times.txt`).
- Index gares : `data/stops_index.json`.
- Graphe genere : `data/graph.json` (fichier derive, non versionne).
- Validation :
  - unit tests `tests/test_pathfind.py`
  - scripts `scripts/sample_triplets.py` et `scripts/validate_pathfinding.py`

## 8. Limites et suite
- Etendre l'annotation manuelle (50 -> 120) et valider a deux annotateurs.
- Baseline ML a remplacer par un modele plus adapte (ex: CamemBERT fine-tuning).
- Pathfinding actuellement non pondere (pas de temps d'attente/horaires fins).
