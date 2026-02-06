# Dataset manuel - modèle de saisie

## Entrées
Format: `id,phrase`

Exemple:
```
1,je voudrais aller de Toulouse a Bordeaux
2,Comment me rendre a Port-Boulet depuis Tours ?
3,Je veux aller voir mon ami Albert a Tours en partant de Bordeaux
4,Une phrase sans origine ni destination
```

## Sorties
Format: `id,origine,destination` ou `id,INVALID,`

Exemple:
```
1,Toulouse,Bordeaux
2,Tours,Port-Boulet
3,Bordeaux,Tours
4,INVALID,
```

## Checklist rapide
- IDs uniques
- Même nombre de lignes input/output
- Pas d'espaces parasites
- UTF-8
