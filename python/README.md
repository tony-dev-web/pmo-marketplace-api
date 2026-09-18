# piecemotooccasion

Client Python de l'API vendeur [PieceMotoOccasion](https://piecemotooccasion.eu) :
catalogue, stock, commandes, expédition, et vérification des notifications signées.

Une seule dépendance, `requests`.

## Installation

```bash
pip install piecemotooccasion
```

## Jeton

Le jeton se génère dans votre espace vendeur, page « Ma boutique en ligne ».
600 requêtes par jeton et par dix minutes ; au-delà l'API répond 429.

## Usage

```python
from piecemotooccasion import Pmo

pmo = Pmo("VOTRE_JETON")

pmo.moi()                       # compte, statut, commission

resultats, erreurs = pmo.envoyer([{
    "reference": "CAR-548",                     # votre identifiant, unique chez vous
    "titre": "Carter embrayage XJ 600 Diversion",
    "prix_ttc": 29.90,
    "categorie": "Carter",
    "marque": "Yamaha",
    "modele": "XJ 600 Diversion",
    "annee_min": 1998, "annee_max": 2003,
    "stock": 1, "poids": 1200,
    "images": ["https://ma-casse.fr/photos/car-548.jpg"],
}])

pmo.stock("CAR-548", 0)         # zéro : la pièce s'affiche « Vendu »
pmo.retirer("CAR-548")          # retirée de la vente, jamais effacée

for commande in pmo.commandes(depuis="2026-09-01"):
    pmo.expedier(commande["id"], "Colissimo", "6A12345678901")
```

`envoyer` accepte une liste de n'importe quelle longueur : elle est découpée en
lots de 200, la limite de l'API. Elle rend `(resultats, erreurs)` — une fiche
refusée n'interrompt pas le lot, elle ressort dans `erreurs` avec son message.

Les champs obligatoires sont **reference**, **titre**, **prix_ttc** et
**categorie**. La référence décide de la création ou de la mise à jour.

Une pièce créée par l'API arrive en brouillon : elle est mise en ligne après
validation, comme une pièce saisie au formulaire.

## Notifications de commande

Si vous renseignez une URL de notification dans votre espace vendeur, chaque
commande payée y est envoyée en POST JSON, signée
`X-Pmo-Signature: sha256=<HMAC-SHA256 du corps, clé = votre jeton>`.

```python
# Django, Flask, FastAPI : le corps brut, en octets
if not pmo.signature_valide(corps_brut, requete.headers.get("X-Pmo-Signature")):
    return "signature invalide", 401
```

Signez le corps **brut**. Le re-sérialiser en JSON change les octets, donc la
signature.

## Erreurs

Toute réponse 4xx ou 5xx lève `ErreurApi` avec le message de l'API.

```python
from piecemotooccasion import ErreurApi

try:
    pmo.expedier(1043, "Colissimo", "6A12345678901")
except ErreurApi as erreur:
    print(erreur)               # « commande introuvable »
```

## Documentation

- API : https://piecemotooccasion.eu/extensions/api
- Extensions et connecteurs : https://piecemotooccasion.eu/extensions

## Licence

MIT
