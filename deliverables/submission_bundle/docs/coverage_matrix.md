# Matrice de Couverture du Sujet

## Modules et I/O
| Exigence | Evidence repo | Statut |
|---|---|---|
| NLP: entree `id,phrase` (fichier/stdin/url) | `src/travel_order_resolver.py` | Fait |
| NLP: sortie `id,origin,destination` ou `id,INVALID,` | `src/travel_order_resolver.py`, `students_project/sample_nlp_output.txt` | Fait |
| Pathfinding: entree triplets NLP | `scripts/pathfind.py` | Fait |
| Pathfinding: sortie sequence d'etapes | `scripts/pathfind.py`, `datasets/path_expected.csv` | Fait |

## NLP
| Exigence | Evidence repo | Statut |
|---|---|---|
| Extraction origine/destination robuste | `src/travel_order_resolver.py`, `tests/test_sample.py`, `tests/test_resolve_typos.py` | Fait |
| Gestion fautes/variantes (`Saint`/`St`, typos) | `src/travel_order_resolver.py`, `tests/test_resolve_typos.py` | Fait |
| Baseline ML de reference | `scripts/train_ml.py`, `scripts/evaluate_ml.py`, `reports/ml_metrics.json` | Fait |
| Benchmark spaCy | `scripts/evaluate_spacy.py`, `reports/spacy_camembert_metrics.json` | Fait |
| Benchmark CamemBERT (embeddings figes + SVC) | `scripts/train_camembert.py`, `scripts/evaluate_camembert.py`, `reports/spacy_camembert_metrics.json` | Fait |
| CamemBERT fine-tune (sequence classification) | `scripts/train_camembert_finetune.py`, `scripts/evaluate_camembert_finetune.py`, `reports/camembert_finetune_metrics.json` | Fait (bonus) |
| CamemBERT fine-tune v2 (train complet) | `models/camembert_finetune_v2/*`, `reports/camembert_finetune_v2_metrics.json` | Fait (bonus) |
| Pipeline multi-backend (`rule-based`/`camembert-ft`) | `scripts/run_pipeline.py`, `scripts/evaluate_end_to_end.py`, `scripts/camembert_finetune_infer.py` | Fait |
| Analyse d'erreurs ML | `scripts/analyze_ml_errors.py`, `reports/ml_error_analysis_*.json` | Fait |

## Donnees
| Exigence | Evidence repo | Statut |
|---|---|---|
| Dataset synthétique train/dev/test | `datasets/train_*`, `datasets/dev_*`, `datasets/test_*` | Fait |
| Dataset manuel + annotation | `datasets/manual/*`, `docs/annotation_guide.md` | Fait |
| Gold set manuel final | `datasets/manual/output_gold_120.csv`, `reports/manual_gold_dashboard.json` | Fait (iteratif) |
| Donnees gares `stops.xlsx` integrees | `scripts/build_stop_index.py`, `data/stops_index.json` | Fait |

## Pathfinding
| Exigence | Evidence repo | Statut |
|---|---|---|
| Graphe depuis GTFS | `scripts/fetch_gtfs.py`, `scripts/build_graph.py` | Fait |
| Validation pathfinding | `scripts/validate_pathfinding.py`, `reports/pathfinding_metrics.txt` | Fait |
| E2E NLP + Pathfinding | `scripts/evaluate_end_to_end.py`, `reports/e2e_manual_gold_120_summary.json` | Fait |

## Industrialisation et Rendu
| Exigence | Evidence repo | Statut |
|---|---|---|
| Tests automatises | `tests/`, `Makefile`, `.github/workflows/ci.yml` | Fait |
| Snapshot metriques consolidees | `scripts/run_snapshot.py`, `reports/snapshot.json`, `reports/snapshot.md` | Fait |
| Bundle de rendu reproductible | `scripts/build_submission_bundle.py`, `deliverables/submission_bundle/manifest.json` | Fait |

## Reste a finaliser avant soutenance
| Item | Evidence cible | Statut |
|---|---|---|
| Validation humaine finale des 22 corrections prioritaires | `datasets/manual/corrections_120.csv` | A finaliser |
| Rapport PDF final (version propre) | export depuis `docs/report_draft.md` | A finaliser |
| Evaluation manuelle et comparaison robuste Rule-based vs CamemBERT v2 | `datasets/manual/*` + rapport metriques comparatives | A finaliser |
