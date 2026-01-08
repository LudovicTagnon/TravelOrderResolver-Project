# Travel Order Resolver

## Contenu
- `src/travel_order_resolver.py` : extracteur CLI (origine/destination).
- `data/places.txt` : gazetteer de lieux.
- `students_project/sample_nlp_input.txt` : entrées d'exemple.
- `students_project/sample_nlp_output.txt` : sorties attendues.
- `project.pdf` : sujet et contraintes.

## Format des données
- Entrée : `id,phrase`.
- Sortie : `id,origine,destination` ou `id,INVALID,`.
- Encodage : UTF-8.

## Exemple
- `1,je voudrais aller de Toulouse a bordeaux`
- `1,Toulouse,Bordeaux`

## Exemples de commandes
- `python3 src/travel_order_resolver.py --places data/places.txt < students_project/sample_nlp_input.txt`
- `python3 src/travel_order_resolver.py --places data/places.txt students_project/sample_nlp_input.txt`
