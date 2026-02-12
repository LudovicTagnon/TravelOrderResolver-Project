# Travel Order Resolver - Rapport (draft)

## 1. Architecture
- `src/travel_order_resolver.py` : extraction NLP baseline (origin/destination) rule-based.
- `scripts/train_ml.py` + `scripts/evaluate_ml.py` : baseline ML (char n-grams + LinearSVC).
- `scripts/build_stop_index.py` : index gares (`stop_name -> stop_ids`) depuis `stops.xlsx`.
- `scripts/build_graph.py` : graphe de connectivite depuis `stop_times.txt` GTFS.
- `scripts/pathfind.py` : plus court chemin (BFS) entre gares.
- CI : `.github/workflows/ci.yml` (tests + smoke scripts).

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

- Train : accuracy `0.983`, valid_f1 `0.987`, invalid_accuracy `1.000`
- Dev : accuracy `0.991`, valid_f1 `0.993`, invalid_accuracy `1.000`
- Test : accuracy `0.993`, valid_f1 `0.995`, invalid_accuracy `1.000`

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
- ML baseline : accuracy `0.558`

Note : ces metriques utilisent le prefill comme pseudo-reference technique. Elles ne remplacent pas une annotation humaine finale.

## 8. Pathfinding
- Donnees d'entree : GTFS (`stops.txt`, `stop_times.txt`).
- Index gares : `data/stops_index.json`.
- Graphe genere : `data/graph.json` (fichier derive, non versionne).
- Resolution nom ville -> stop_ids : exact, prefixe, puis fuzzy (gestion `Saint`/`St` et bruit d'encodage).
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
- Pathfinding valide sur NLP valide : `115/115` (`100.0%`)
- Succes global NLP+pathfinding : `115/120` (`95.8%`)

Export detail : `datasets/manual/e2e_manual_120.csv`.

## 10. Snapshot global
- Script : `scripts/run_snapshot.py`
- Sortie consolidee : `reports/snapshot.json` et `reports/snapshot.md`
- Analyse d'erreurs ML : `reports/ml_error_analysis_dev.json` et `reports/ml_error_analysis_test.json`
- Objectif : figer l'etat des metriques (NLP rule-based, ML, manuel, pathfinding, end-to-end) en un seul artefact.

## 11. Pipeline operationnel
- Script d'execution bout-en-bout : `scripts/run_pipeline.py`
- Entree : `id,phrase`
- Sorties :
  - `id,origin,destination` (NLP)
  - `id,Step0,Step1,...` (pathfinding)
- Exemple genere : `students_project/sample_pipeline_nlp_output.txt` et `students_project/sample_pipeline_path_output.txt`.

## 12. Gold set manuel final
- Preparation des corrections : `scripts/prepare_manual_corrections.py`
- Application sur base prefill : `scripts/apply_manual_corrections.py`
- Fichier de travail : `datasets/manual/corrections_120.csv` (22 lignes prioritaires)
- Cible de sortie : `datasets/manual/output_gold_120.csv`

## 13. Evaluation gold set
- Script : `scripts/run_manual_gold_eval.py`
- Sorties :
  - `reports/manual_gold_metrics_rule_based.json`
  - `reports/manual_gold_metrics_ml.json`
  - `reports/manual_gold_metrics_camembert_v2.json` (option `--with-camembert-ft`)
  - `reports/e2e_manual_gold_120_summary.json`
  - `reports/e2e_manual_gold_120_camembert_v2_summary.json` (option `--with-camembert-ft`)
  - `reports/manual_gold_dashboard.json`
- Le dashboard inclut un `nlp_leaderboard` (accuracy/f1) pour comparer rule-based, Camembert v2 et baseline ML.

## 14. Bundle de rendu
- Script : `scripts/build_submission_bundle.py`
- Dossier cible : `deliverables/submission_bundle/`
- Manifest : `deliverables/submission_bundle/manifest.json` (hash SHA256 des fichiers inclus)

## 15. Test spaCy et CamemBERT
Source : `reports/spacy_camembert_metrics.json`.

- spaCy (`fr_core_news_sm`) :
  - Dev accuracy `0.694`, valid_f1 `0.775`
  - Test accuracy `0.693`, valid_f1 `0.771`
- CamemBERT (`camembert-base` embeddings figes + LinearSVC, train=4000) :
  - Dev accuracy `0.482`, valid_f1 `0.409`
  - Test accuracy `0.498`, valid_f1 `0.418`

Constat : spaCy surperforme le baseline ML classique et ce premier setup CamemBERT, mais reste sous le rule-based principal.

## 16. CamemBERT fine-tune (sequence classification)
Sources : `reports/camembert_finetune_metrics.json`, `reports/camembert_finetune_v2_metrics.json`.

- Setup v1 (rapide) :
  - modele de base `camembert-base`
  - entrainement separe `origin` / `destination`
  - configuration rapide : `1` epoch, `4000` phrases, batch `16`, max_len `64`
- Resultats v1 :
  - Dev accuracy `0.733`, valid_f1 `0.753`
  - Test accuracy `0.735`, valid_f1 `0.751`

- Setup v2 (renforce) :
  - entrainement separe `origin` / `destination`
  - train complet `8000` phrases
  - `2` epochs, batch `16`, max_len `64`
- Resultats v2 :
  - Dev accuracy `0.981`, valid_f1 `0.978`
  - Test accuracy `0.973`, valid_f1 `0.968`

Constat : le fine-tuning CamemBERT v2 depasse nettement toutes les baselines ML, et se rapproche du rule-based (test `0.993`).

## 17. Integration E2E backend CamemBERT
Sources : `scripts/run_pipeline.py`, `scripts/evaluate_end_to_end.py`, `reports/e2e_manual_120_camembert_v2_summary.json`, `reports/manual_gold_metrics_camembert_v2.json`.

- Le pipeline supporte maintenant deux backends NLP :
  - `rule-based` (defaut)
  - `camembert-ft` (flag `--nlp-backend camembert-ft`)
- Evaluation E2E sur les 120 phrases manuelles avec CamemBERT v2 :
  - NLP valide `115/120`
  - pathfinding valide `115/115` apres NLP valide
  - succes global `115/120` (`95.8%`)
- Evaluation NLP sur le gold manuel 120 :
  - CamemBERT v2 : `119/120` (accuracy `0.992`)
  - Rule-based : `120/120` (accuracy `1.000`)

## 18. Limites et suite
- Corriger/valider humainement le prefill 120 lignes et viser une double annotation.
- Benchmarker CamemBERT v2 sur un jeu manuel annote plus large pour confirmer la generalisation hors dataset synthetique.
- Pathfinding actuellement non pondere (pas de temps d'attente/horaires fins).
