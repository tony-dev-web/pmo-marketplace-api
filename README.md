# API vendeur PieceMotoOccasion

Reliez n'importe quel logiciel — logiciel de gestion de casse, ERP, script maison — à la marketplace française [PieceMotoOccasion](https://piecemotooccasion.eu) : votre catalogue et vos stocks montent, les commandes payées redescendent, vous renseignez l'expédition. C'est la même API que parlent les extensions PrestaShop, WooCommerce, Drupal et Magento.

**Documentation** : https://piecemotooccasion.eu/extensions/api
**Collection Postman** : https://www.postman.com/tony-d7b3346b-8131745/piece-moto-occasion/collection/9d8okfr/api-vendeur-piecemotooccasion
**Jeton** : espace vendeur, page « Ma boutique en ligne »
**Base** : `https://piecemotooccasion.eu/api/v1`

## Authentification

En-tête `Authorization: Bearer <jeton>`, réponses JSON. 600 requêtes par jeton et par dix minutes ; au-delà, `429`.

## Points d'entrée

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/moi` | Compte, statut, commission, boutique reliée |
| `GET` | `/produits` | Vos pièces chez PieceMotoOccasion |
| `PUT` | `/produits` | Création ou mise à jour par référence, 200 fiches par appel |
| `PATCH` | `/produits/<reference>/stock` | `{"stock": 3}` |
| `DELETE` | `/produits/<reference>` | Retire de la vente (stock 0), sans effacer |
| `GET` | `/commandes?depuis=AAAA-MM-JJ` | Commandes payées, lignes et adresse de livraison |
| `POST` | `/commandes/<id>/expedier` | `{"transporteur": "Colissimo", "suivi": "6A…"}` |

Description complète dans [`openapi.yaml`](openapi.yaml), utilisable pour générer un client dans votre langage.

## La fiche d'une pièce

Obligatoires : `reference` (votre identifiant, unique chez vous), `titre`, `prix_ttc`, `categorie` (texte libre : Carénage, Selle, Jante…).

Facultatifs : `stock` (1 par défaut), `description`, `information`, `marque`, `modele`, `annee_min`, `annee_max`, `cylindree`, `poids` en grammes, `etat_achat` (Occasion ou Neuf), `reference_oem`, `url_boutique`, `images` (jusqu'à six adresses http ; les photos sont converties en WebP et AVIF).

Une pièce nouvelle est vérifiée avant sa mise en ligne ; une mise à jour ne change pas son statut.

```bash
curl -X PUT https://piecemotooccasion.eu/api/v1/produits \
  -H "Authorization: Bearer VOTRE_JETON" -H "Content-Type: application/json" \
  -d '{"produits": [{"reference": "CAR-548", "titre": "Carter embrayage XJ 600 Diversion",
        "prix_ttc": 29.90, "categorie": "Carter", "marque": "Yamaha",
        "modele": "XJ 600 Diversion", "stock": 1}]}'
```

## Notification des commandes

Renseignez une URL de notification dans votre espace vendeur : chaque commande payée y est envoyée en `POST` JSON, signée par l'en-tête `X-Pmo-Signature: sha256=<HMAC-SHA256 du corps avec votre jeton>`. Vérifiez la signature sur le corps **brut** : re-sérialiser le JSON change les octets, donc la signature.

Exemple de charge utile : [`exemple-webhook-commande.json`](exemple-webhook-commande.json).

## Exemples

- [`exemples/pmo_client.py`](exemples/pmo_client.py) — client Python complet, sans dépendance hors `requests`.
- [`exemples/synchroniser.py`](exemples/synchroniser.py) — envoi du catalogue, stock, commandes, expédition.
- [`exemples/recevoir_commande.py`](exemples/recevoir_commande.py) — réception du webhook en Flask, signature vérifiée.
- [`pmo-api.postman_collection.json`](pmo-api.postman_collection.json) — collection Postman : importez-la, collez votre jeton dans la variable `jeton`, les sept requêtes sont prêtes. Elle est aussi [publiée sur Postman](https://www.postman.com/tony-d7b3346b-8131745/piece-moto-occasion/collection/9d8okfr/api-vendeur-piecemotooccasion).

```python
from pmo_client import Pmo

pmo = Pmo("VOTRE_JETON")
pmo.envoyer([{"reference": "CAR-548", "titre": "Carter embrayage",
              "prix_ttc": 29.90, "categorie": "Carter"}])
pmo.stock("CAR-548", 0)
for commande in pmo.commandes(depuis="2026-09-01"):
    print(commande["id"], commande["total_ttc"])
```

Licence MIT.

## Les extensions PieceMotoOccasion

- [PrestaShop](https://github.com/tony-dev-web/pmo-marketplace-prestashop)
- [WooCommerce](https://github.com/tony-dev-web/pmo-marketplace-woocommerce)
- [WordPress](https://github.com/tony-dev-web/pmo-marketplace-wordpress)
- [Shopify](https://github.com/tony-dev-web/pmo-marketplace-shopify)
- [Drupal](https://github.com/tony-dev-web/pmo-marketplace-drupal)
- [Magento](https://github.com/tony-dev-web/pmo-marketplace-magento)
- Toutes les extensions : https://piecemotooccasion.eu/extensions/
