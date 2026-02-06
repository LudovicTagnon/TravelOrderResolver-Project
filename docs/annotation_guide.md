# Guide d'annotation (dataset manuel)

## Format attendu
- Entrée : `id,phrase`
- Sortie : `id,origine,destination` ou `id,INVALID,`
- Encodage : UTF-8

## Règles d'annotation
- Conserver l'ID tel quel.
- Si la phrase n'exprime pas un trajet, sortir `INVALID`.
- Si origine/destination apparaissent, les restituer avec la bonne capitalisation.
- Ne pas inventer de ville non mentionnée.

## Cas difficiles à inclure
- Ambiguïtés (prénoms = villes) : `Albert`, `Paris`.
- Noms composés : `Saint-Jean-de-Luz`, `Marne-la-Vallée`.
- Accents absents / fautes : `toulouse`, `Saint Etienne`, `bordeux`.
- Ordre non standard : destination avant origine.
- Mots parasites : amis, motifs, dates, hors-sujet.

## Exemples
Entrée:
- `1,je voudrais aller de Toulouse a Bordeaux`
- `2,Comment me rendre a Port-Boulet depuis Tours ?`
- `3,Je veux aller voir mon ami Albert a Tours en partant de Bordeaux`
- `4,Une phrase sans origine ni destination`

Sortie:
- `1,Toulouse,Bordeaux`
- `2,Tours,Port-Boulet`
- `3,Bordeaux,Tours`
- `4,INVALID,`
