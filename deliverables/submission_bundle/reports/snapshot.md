# Snapshot Projet

## NLP rule-based (train/dev/test)
- Train accuracy: `98.3%`
- Dev accuracy: `99.1%`
- Test accuracy: `99.3%`

## NLP baseline ML (train/dev/test)
- Train accuracy: `70.2%`
- Dev accuracy: `40.4%`
- Test accuracy: `41.8%`

## Diagnostic ML (confusions)
- Dev exact accuracy: `40.4%`
- Test exact accuracy: `41.8%`
- Dev top confusion origine: `INVALID -> Tours` (`3`)
- Test top confusion origine: `Nice -> Grenoble` (`3`)

## Manuel 120 (reference)
- Rule-based accuracy: `100.0%`
- ML accuracy: `55.8%`

## Pathfinding
- Validation echantillon: `30/30` (`1.000`)

## End-to-end (manuel 120)
- NLP valides: `115/120` (95.8%)
- Pathfinding sur NLP valides: `115/115` (100.0%)
- Succes global: `115/120` (95.8%)
