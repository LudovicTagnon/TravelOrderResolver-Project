# Travel Order Resolver

Projet EPITECH: extraction `origine/destination` depuis des phrases, puis calcul d'itineraire entre gares.

## Contenu du repo
- `src/travel_order_resolver.py`: baseline NLP rule-based (CLI).
- `scripts/`: generation de donnees, entrainements, benchmarks, pipeline complet.
- `datasets/`: jeux synthetiques + jeu manuel (120 phrases).
- `data/`: lieux, index gares, graphe GTFS.
- `reports/`: metriques et dashboards.
- `docs/`: rapport, matrice de couverture, runbook soutenance.
- `deliverables/`: PDFs et bundle final.

## Format d'entree/sortie NLP
- entree: `id,phrase`
- sortie valide: `id,origine,destination`
- sortie invalide: `id,INVALID,`
- encodage: UTF-8

Exemple:
```text
1,je veux aller de toulouse a bordeaux
1,Toulouse,Bordeaux
```

## Commandes principales
- tests unitaires: `make test`
- benchmark rule-based: `make benchmarks`
- baseline ML: `make train-ml && make ml-benchmarks`
- benchmarks spaCy + CamemBERT: `make spacy-camembert-bench`
- fine-tuning CamemBERT: `make train-camembert-ft-v2 && make camembert-ft-v2-bench`
- evaluation gold manuel: `make manual-gold-eval-camembert-v2`
- pipeline sample complet: `make pipeline-sample`
- snapshot global: `make snapshot`
- bundle de rendu: `make bundle`

## Etat actuel (resume)
- rule-based: tres bon sur split test synthetique (`reports/metrics.json`).
- CamemBERT fine-tune v2: proche du rule-based (`reports/camembert_finetune_v2_metrics.json`).
- gold set manuel 120: rule-based `120/120`, CamemBERT v2 `119/120`.
- pathfinding: `30/30` sur echantillon dedie (`reports/pathfinding_metrics.txt`).
- end-to-end manuel 120: `115/120` succes global (`reports/e2e_manual_120_summary.json`).

## Fichiers de rendu
- rapport long: `deliverables/report_final.pdf`
- version jury (20 pages): `deliverables/report_final_jury.pdf`
- bundle final: `deliverables/submission_bundle/`
