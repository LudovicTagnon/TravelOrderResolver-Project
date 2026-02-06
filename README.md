# Travel Order Resolver

## Contenu
- `src/travel_order_resolver.py` : extracteur CLI (origine/destination).
- `data/places.txt` : gazetteer de lieux.
- `data/places_imported.txt` : liste de gares importées (SNCF).
- `data/places_stops.txt` : liste générée depuis `stops.xlsx`.
- `data/stops_areas.csv` : arrêts (stop_id, stop_name, normalized).
- `data/stops_index.json` : index normalisé -> stop_ids.
- `students_project/sample_nlp_input.txt` : entrées d'exemple.
- `students_project/sample_nlp_output.txt` : sorties attendues.
- `project.pdf` : sujet et contraintes.
- `tests/test_sample.py` : test de cohérence sur les exemples fournis.
- `scripts/evaluate.py` : métriques simples sur le jeu d'exemple.
- `scripts/generate_dataset.py` : génération de jeux synthétiques (entrées + sorties attendues).
- `scripts/dataset_report.py` : statistiques sur un jeu (volumétrie, lieux, tokens).
- `scripts/split_dataset.py` : découpage train/dev/test.
- `datasets/` : jeu synthétique (all/train/dev/test, variantes avec fautes).
- `scripts/run_benchmarks.py` : exécution des métriques sur train/dev/test.
- `reports/metrics.json` : résultats des métriques par split.
- `scripts/import_places.py` : import CSV de lieux (option d'alias gare).
- `scripts/build_stop_index.py` : extraction des stop areas + index JSON depuis `stops.xlsx`.
- `scripts/build_graph.py` : construction du graphe depuis un fichier `stop_times` GTFS.
- `scripts/pathfind.py` : plus court chemin entre deux gares à partir d'un triplet `id,origin,destination`.
- `scripts/fetch_gtfs.py` : téléchargement/extraction du GTFS SNCF.
- `data/graph.json` : graphe généré (liaisons entre stop areas).
- `scripts/sample_triplets.py` : génération de triplets connectés pour test pathfinding.
- `scripts/validate_pathfinding.py` : validation des trajets attendus.
- `docs/report_outline.md` : plan de rapport (NLP + métriques).
- `scripts/train_ml.py` : entraînement baseline ML (origine/destination).
- `scripts/evaluate_ml.py` : évaluation baseline ML.
- `docs/annotation_guide.md` : guide d'annotation manuel.
- `docs/manual_dataset_template.md` : modèle de format pour dataset manuel.
- `scripts/validate_manual_dataset.py` : contrôle rapide d'un dataset annoté.
- `data/places.txt` : lignes simples ou format `alias|canonique`.

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
- `python3 src/travel_order_resolver.py --places data/places_imported.txt students_project/sample_nlp_input.txt`
- `python3 scripts/import_places.py --input stops.xlsx --column stop_name --add-gare-alias --output data/places_stops.txt`
- `python3 scripts/build_stop_index.py --input stops.xlsx --output-csv data/stops_areas.csv --output-json data/stops_index.json`
- `python3 scripts/build_graph.py --stop-times path/to/stop_times.txt --output data/graph.json`
- `python3 scripts/pathfind.py --graph data/graph.json --stops-index data/stops_index.json --input path/to/triplets.csv`
- `python3 scripts/fetch_gtfs.py --extract`
- `python3 src/travel_order_resolver.py --places data/places.txt input.txt | python3 scripts/pathfind.py --graph data/graph.json --stops-index data/stops_index.json`
- `python3 scripts/sample_triplets.py --graph data/graph.json --stops-areas data/stops_areas.csv --output-triplets datasets/path_triplets.csv --output-expected datasets/path_expected.csv`
- `python3 scripts/validate_pathfinding.py --graph data/graph.json --stops-index data/stops_index.json --triplets datasets/path_triplets.csv --expected datasets/path_expected.csv`
- `python3 scripts/train_ml.py --train-input datasets/train_input.txt --train-output datasets/train_output.txt --model-dir models`
- `python3 scripts/evaluate_ml.py --input datasets/dev_input.txt --expected datasets/dev_output.txt --model-dir models`
- `python3 scripts/validate_manual_dataset.py --input datasets/manual/input.csv --output datasets/manual/output.csv`
