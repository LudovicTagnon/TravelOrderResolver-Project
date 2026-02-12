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
- Prefill annotation :
  - `datasets/manual/output_prefill_120.csv` (a corriger manuellement)
  - `reports/manual_prefill_invalid_ids.txt` (IDs detectes INVALID)
- Relecture assistee :
  - `datasets/manual/review_sheet_120.csv` (vue complete)
  - `datasets/manual/review_actionable_120.csv` (priorites high/medium)
  - `reports/manual_review_summary.json` (22 cas actionnables / 120)

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

## 7. Controle prefill 120 (coherence)
Sources : `reports/manual_prefill_metrics_rule_based.json`, `reports/manual_prefill_metrics_ml.json`.

- Rule-based : accuracy `1.000`
- ML baseline : accuracy `0.550`

Note : ces metriques utilisent le prefill comme pseudo-reference technique. Elles ne remplacent pas une annotation humaine finale.

## 8. Pathfinding
- Donnees d'entree : GTFS (`stops.txt`, `stop_times.txt`).
- Index gares : `data/stops_index.json`.
- Graphe genere : `data/graph.json` (fichier derive, non versionne).
- Jeux de validation :
  - `datasets/path_triplets.csv`
  - `datasets/path_expected.csv`
- Metriques : `reports/pathfinding_metrics.txt` (`accuracy=1.000` sur 30 trajets echantillonnes).
- Validation :
  - unit tests `tests/test_pathfind.py`
  - scripts `scripts/sample_triplets.py` et `scripts/validate_pathfinding.py`

## 9. Evaluation bout-en-bout
Source : `reports/e2e_manual_120_summary.json`.

- Total phrases : `120`
- NLP valide : `115` (`95.8%`)
- Pathfinding valide sur NLP valide : `104/115` (`90.4%`)
- Succes global NLP+pathfinding : `104/120` (`86.7%`)

Export detail : `datasets/manual/e2e_manual_120.csv`.

## 10. Snapshot global
- Script : `scripts/run_snapshot.py`
- Sortie consolidee : `reports/snapshot.json`
- Objectif : figer l'etat des metriques (NLP rule-based, ML, manuel, pathfinding, end-to-end) en un seul artefact.

## 11. Limites et suite
- Corriger/valider humainement le prefill 120 lignes et viser une double annotation.
- Baseline ML a remplacer par un modele plus adapte (ex: CamemBERT fine-tuning).
- Pathfinding actuellement non pondere (pas de temps d'attente/horaires fins).
