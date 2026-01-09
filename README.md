# Travel Order Resolver

## Contenu
- `src/travel_order_resolver.py` : extracteur CLI (origine/destination).
- `data/places.txt` : gazetteer de lieux.
- `students_project/sample_nlp_input.txt` : entrées d'exemple.
- `students_project/sample_nlp_output.txt` : sorties attendues.
- `project.pdf` : sujet et contraintes.
- `tests/test_sample.py` : test de cohérence sur les exemples fournis.
- `scripts/evaluate.py` : métriques simples sur le jeu d'exemple.
- `scripts/generate_dataset.py` : génération de jeux synthétiques (entrées + sorties attendues).
- `scripts/dataset_report.py` : statistiques sur un jeu (volumétrie, lieux, tokens).
- `scripts/split_dataset.py` : découpage train/dev/test.
- `datasets/` : jeu synthétique (all/train/dev/test).
- `scripts/run_benchmarks.py` : exécution des métriques sur train/dev/test.
- `reports/metrics.json` : résultats des métriques par split.

## Format des données
- Entrée : `id,phrase`.
- Sortie : `id,origine,destination` ou `id,INVALID,`.
- Encodage : UTF-8.
- Entrées possibles : fichier, stdin (`-`), URL HTTP(S).

## Exemple
- `1,je voudrais aller de Toulouse a bordeaux`
- `1,Toulouse,Bordeaux`

## Exemples de commandes
- `python3 src/travel_order_resolver.py --places data/places.txt < students_project/sample_nlp_input.txt`
- `python3 src/travel_order_resolver.py --places data/places.txt students_project/sample_nlp_input.txt`
