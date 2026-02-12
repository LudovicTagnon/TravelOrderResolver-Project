# Runbook Soutenance

## Trame 8-10 minutes
1. Problème: transformer une phrase libre en trajet ferroviaire exploitable.
2. Architecture: NLP rule-based + baseline ML + pathfinding GTFS.
3. Données: synthétique train/dev/test + set manuel 120 + gold set.
4. Résultats: rule-based fort, ML baseline de référence, e2e stable.
5. Industrialisation: tests, CI, snapshot, bundle final.

## Démo live (ordre conseillé)
1. Vérification rapide:
```bash
make test
```
2. Pipeline bout-en-bout sur sample:
```bash
make pipeline-sample
```
3. Évaluation gold set:
```bash
make manual-gold-eval
```
4. Snapshot consolidé:
```bash
make snapshot
```
5. Bundle de rendu:
```bash
make bundle
```

## Chiffres à annoncer
- NLP rule-based test: `99.3%` accuracy (`reports/metrics.json`).
- ML baseline test: `41.8%` accuracy (`reports/ml_metrics.json`).
- Gold set manuel:
  - rule-based: `100.0%` (`reports/manual_gold_metrics_rule_based.json`)
  - ML: `55.8%` (`reports/manual_gold_metrics_ml.json`)
- End-to-end gold set: `115/120` (`95.8%`) (`reports/e2e_manual_gold_120_summary.json`).
- Pathfinding validation: `30/30` (`reports/pathfinding_metrics.txt`).

## Questions probables (réponses courtes)
- Pourquoi rule-based > ML ?
  - Le baseline ML est volontairement simple (char n-grams + LinearSVC), utile comme référence.
- Robustesse aux fautes/variantes ?
  - Normalisation accents/casse + fuzzy matching NLP + fallback ville->gares côté pathfinding.
- Où est le risque restant ?
  - Finalisation humaine des corrections manuelles et amélioration modèle NLP avancé (bonus).

## Fichiers jury à ouvrir
- `reports/snapshot.md`
- `reports/manual_gold_dashboard.json`
- `docs/coverage_matrix.md`
- `deliverables/submission_bundle/manifest.json`
