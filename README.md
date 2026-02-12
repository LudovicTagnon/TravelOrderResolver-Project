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
- `docs/` : guide d'annotation + documents du rapport.

## Pre-requis
- Python 3.10+
- Dependances utilisees dans ce repo : `scikit-learn`, `joblib`, `openpyxl`
- `make` (optionnel, raccourcis de commandes)
- Pour tests `spaCy`/`CamemBERT` : utiliser `.venv` (workflow 11)

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

## Workflow 5 - Evaluation bout-en-bout (NLP + pathfinding)
```bash
python3 scripts/evaluate_end_to_end.py --input datasets/manual/input_starter.csv --places data/places.txt --graph data/graph.json --stops-index data/stops_index.json --stops-areas data/stops_areas.csv --output-csv datasets/manual/e2e_manual_120.csv --summary reports/e2e_manual_120_summary.json
```
Sorties :
- detail par phrase : `datasets/manual/e2e_manual_120.csv`
- resume global : `reports/e2e_manual_120_summary.json`

## Workflow 6 - Snapshot global (soutenance)
```bash
python3 scripts/run_snapshot.py --datasets datasets --reports reports --model-dir models --places data/places.txt --graph data/graph.json --stops-index data/stops_index.json --stops-areas data/stops_areas.csv --manual-input datasets/manual/input_starter.csv --manual-output datasets/manual/output_gold_120.csv --output reports/snapshot.json --markdown-output reports/snapshot.md
```
Le snapshot consolide les metriques principales dans `reports/snapshot.json` et `reports/snapshot.md`.
Inclut aussi l'analyse d'erreurs ML : `reports/ml_error_analysis_dev.json` et `reports/ml_error_analysis_test.json`.

## Workflow 7 - Pipeline complet (NLP + path output)
```bash
python3 scripts/run_pipeline.py students_project/sample_nlp_input.txt --places data/places.txt --graph data/graph.json --stops-index data/stops_index.json --stops-areas data/stops_areas.csv --output-nlp students_project/sample_pipeline_nlp_output.txt --output-path students_project/sample_pipeline_path_output.txt
```
Sorties :
- NLP : `students_project/sample_pipeline_nlp_output.txt`
- Pathfinding : `students_project/sample_pipeline_path_output.txt`

## Workflow 8 - Finaliser le gold set manuel
Generer une feuille de corrections (22 lignes prioritaires) :
```bash
python3 scripts/prepare_manual_corrections.py --review-actionable datasets/manual/review_actionable_120.csv --output datasets/manual/corrections_120.csv
```
Appliquer les corrections vers un gold set final :
```bash
python3 scripts/apply_manual_corrections.py --base-output datasets/manual/output_prefill_120.csv --corrections datasets/manual/corrections_120.csv --output datasets/manual/output_gold_120.csv
python3 scripts/validate_manual_dataset.py --input datasets/manual/input_starter.csv --output datasets/manual/output_gold_120.csv
```

## Workflow 9 - Evaluer le gold set manuel
```bash
python3 scripts/run_manual_gold_eval.py --input datasets/manual/input_starter.csv --gold-output datasets/manual/output_gold_120.csv --places data/places.txt --model-dir models --graph data/graph.json --stops-index data/stops_index.json --stops-areas data/stops_areas.csv --reports reports --datasets datasets
```
Sorties:
- `reports/manual_gold_metrics_rule_based.json`
- `reports/manual_gold_metrics_ml.json`
- `reports/e2e_manual_gold_120_summary.json`
- `reports/manual_gold_dashboard.json`

Comparatif avec CamemBERT v2 (dashboard enrichi + leaderboard):
```bash
make manual-gold-eval-camembert-v2
```
Sorties ajoutees:
- `reports/manual_gold_metrics_camembert_v2.json`
- `reports/e2e_manual_gold_120_camembert_v2_summary.json`
- `datasets/manual/e2e_manual_gold_120_camembert_v2.csv`

## Workflow 10 - Construire un bundle de rendu
```bash
python3 scripts/build_submission_bundle.py --output-dir deliverables/submission_bundle --manifest deliverables/submission_bundle/manifest.json
```
Contenu:
- artefacts de rapport (`reports/*`)
- gold set manuel et evaluation e2e
- outputs pipeline sample
- manifeste SHA256 (`deliverables/submission_bundle/manifest.json`)

## Workflow 11 - Tester spaCy et CamemBERT (baselines rapides)
Initialiser `.venv`:
```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install spacy transformers torch sentencepiece scikit-learn joblib
.venv/bin/python -m spacy download fr_core_news_sm
```
Entrainement CamemBERT (embeddings figes + SVC):
```bash
make train-camembert
```
Benchmarks `dev/test`:
```bash
make spacy-camembert-bench
```
Sortie:
- `reports/spacy_camembert_metrics.json`
- `reports/spacy_camembert_summary.md`

## Workflow 12 - Fine-tuner CamemBERT
Entrainement des deux modeles (origine puis destination):
```bash
make train-camembert-ft
```
Benchmarks `dev/test` du duo fine-tune:
```bash
make camembert-ft-bench
```
Sortie:
- `reports/camembert_finetune_metrics.json`
- `reports/camembert_finetune_summary.md`

Version renforcee (train complet + 2 epochs):
```bash
make train-camembert-ft-v2
make camembert-ft-v2-bench
```
Sortie:
- `reports/camembert_finetune_v2_metrics.json`
- `reports/camembert_finetune_v2_summary.md`

## Workflow 13 - E2E avec backend CamemBERT
Evaluation end-to-end sur 120 phrases:
```bash
make e2e-camembert-ft-v2
```
Sorties:
- `datasets/manual/e2e_manual_120_camembert_v2.csv`
- `reports/e2e_manual_120_camembert_v2_summary.json`

Pipeline sample avec CamemBERT:
```bash
python3 scripts/run_pipeline.py students_project/sample_nlp_input.txt --nlp-backend camembert-ft --origin-model-dir models/camembert_finetune_v2/origin --destination-model-dir models/camembert_finetune_v2/destination --graph data/graph.json --stops-index data/stops_index.json --stops-areas data/stops_areas.csv --output-nlp students_project/sample_pipeline_nlp_output_camembert_v2.txt --output-path students_project/sample_pipeline_path_output_camembert_v2.txt
```

## Workflow 14 - Rapport PDF final
Generer la version markdown prete a exporter:
```bash
make report-pdf-ready
```
Exporter en PDF:
```bash
make report-pdf
```
Version compacte soutenance:
```bash
make report-pdf-jury
```
Sorties et sources:
- `docs/report_pdf_ready.md`
- `docs/report_jury_ready.md`
- `deliverables/report_final.pdf`
- `deliverables/report_final_jury.pdf`
- `docs/references.bib`
- `docs/figures/README.md`

## Raccourcis Makefile
```bash
make test
make train-ml
make train-camembert
make spacy-camembert-bench
make train-camembert-ft
make camembert-ft-bench
make train-camembert-ft-v2
make camembert-ft-v2-bench
make e2e-camembert-ft-v2
make manual-gold-eval-camembert-v2
make report-pdf-ready
make report-pdf
make report-pdf-jury-ready
make report-pdf-jury
make snapshot
make manual-gold-eval
make pipeline-sample
make bundle
```

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
- End-to-end manuel 120 : NLP valide `115/120`, succes pathfinding `115/115`, succes global `115/120` (`reports/e2e_manual_120_summary.json`).
- Snapshot global : `reports/snapshot.json` + `reports/snapshot.md`.
- Analyse erreurs ML : `reports/ml_error_analysis_dev.json` + `reports/ml_error_analysis_test.json`.
- Pipeline sample (8 phrases) : `6` succes complets, `2` INVALID NLP, `0` echec pathfinding apres NLP.
- Template de correction manuelle : `datasets/manual/corrections_120.csv` (22 lignes a valider).
- Dashboard gold set : `reports/manual_gold_dashboard.json`.
- Bundle de rendu : `deliverables/submission_bundle/`.
- Benchmarks spaCy/CamemBERT : `reports/spacy_camembert_metrics.json`.
- CamemBERT fine-tune (sequence classification) : dev `0.733`, test `0.735` (`reports/camembert_finetune_metrics.json`).
- CamemBERT fine-tune v2 (train complet, 2 epochs) : dev `0.981`, test `0.973` (`reports/camembert_finetune_v2_metrics.json`).
- CamemBERT v2 sur gold manuel 120 : `119/120` (`reports/manual_gold_metrics_camembert_v2.json`).
- E2E CamemBERT v2 (120 phrases) : succes global `115/120` (`reports/e2e_manual_120_camembert_v2_summary.json`).
- Resume benchmarks fine-tune : `reports/camembert_finetune_summary.md`.
- Resume benchmarks fine-tune v2 : `reports/camembert_finetune_v2_summary.md`.
- Resume gold manuel CamemBERT v2 : `reports/manual_gold_camembert_v2_summary.md`.
- Rapport long (source): `docs/report_draft.md`.
- Version PDF du rapport : `deliverables/report_final.pdf`.
- Version PDF jury (compacte) : `deliverables/report_final_jury.pdf`.
- Matrice sujet->evidence : `docs/coverage_matrix.md`.
- Runbook soutenance : `docs/soutenance_runbook.md`.
