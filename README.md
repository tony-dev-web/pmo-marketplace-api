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

## Codes et erreurs

Toute erreur revient en JSON : `{"erreur": "…"}`.

| Code | Quand | Que faire |
|---|---|---|
| `200` | Appel accepté, même si certaines fiches sont refusées | Lire le tableau `erreurs` de la réponse |
| `400` | JSON invalide, aucune fiche valide, date mal formée | Corriger l'appel, ne pas réessayer tel quel |
| `401` | Jeton absent, mal formé ou révoqué | Regénérer le jeton dans l'espace vendeur |
| `404` | Référence ou commande inconnue chez vous | La recherche est limitée à votre catalogue |
| `405` | Méthode non autorisée sur ce chemin | Voir le tableau des points d'entrée |
| `429` | Plus de 600 requêtes en dix minutes | Attendre, puis grouper : 200 fiches par `PUT` |

## Limites

- 600 requêtes par jeton et par tranche de dix minutes, tous chemins confondus.
- 200 fiches par appel `PUT /produits`. Mille pièces tiennent en cinq appels.
- `GET /commandes` rend les 500 dernières commandes payées, de la plus récente à la plus ancienne. Utilisez `depuis` pour les synchronisations régulières.
- Six images par pièce, 8 Mo chacune. Une adresse injoignable ou qui ne renvoie pas une image est ignorée : la pièce est créée sans elle.
- Un seul jeton par vendeur ; en regénérer un coupe immédiatement l'ancien.

## Mettre en place en quatre étapes

1. Générez le jeton dans l'espace vendeur et vérifiez-le avec `GET /moi`.
2. Envoyez le catalogue par lots de 200 en `PUT /produits`, corrigez les fiches listées dans `erreurs`.
3. À chaque changement de stock, `PATCH /produits/<reference>/stock`. Prévoyez un envoi complet quotidien : il rattrape ce que vos évènements ont manqué.
4. Recevez les commandes par webhook ou par `GET /commandes?depuis=…`, expédiez, puis déclarez le suivi par `POST /commandes/<id>/expedier`.

## Notification des commandes

Renseignez une URL de notification dans votre espace vendeur : chaque commande payée y est envoyée en `POST` JSON, signée par l'en-tête `X-Pmo-Signature: sha256=<HMAC-SHA256 du corps avec votre jeton>`. Vérifiez la signature sur le corps **brut** : re-sérialiser le JSON change les octets, donc la signature.

Répondez `200` dès réception et traitez ensuite ; le même contenu reste lisible par `GET /commandes`, donc rien n'est perdu si votre serveur était hors ligne.

Exemple de charge utile : [`exemple-webhook-commande.json`](exemple-webhook-commande.json).

## Exemples

- [`exemples/pmo_client.py`](exemples/pmo_client.py) — client Python complet, sans dépendance hors `requests`.
- [`exemples/synchroniser.py`](exemples/synchroniser.py) — envoi du catalogue, stock, commandes, expédition.
- [`modele-catalogue.csv`](modele-catalogue.csv) — le modèle de fichier accepté par la console vendeur et par `importer_csv.py`.
- [`exemples/importer_csv.py`](exemples/importer_csv.py) — envoie un CSV de catalogue vers l'API, pour un envoi automatique chaque nuit.
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

## Documentation Fern

Le dossier `fern/` produit un site de documentation et des SDK à partir de `openapi.yaml`.

```bash
npm install -g fern-api
fern check          # valide la description
fern docs dev       # aperçu local du site
fern generate --docs   # publie le site
fern generate --group clients   # genere les SDK Python et TypeScript
```

Licence MIT.

## Les plateformes prises en charge

Les extensions officielles parlent cette API. Chaque plateforme reste éditée par son propre projet :

| Plateforme | Site officiel | Code source de la plateforme |
|---|---|---|
| PrestaShop | https://www.prestashop.com | https://github.com/PrestaShop/PrestaShop |
| WooCommerce | https://woocommerce.com | https://github.com/woocommerce/woocommerce |
| WordPress | https://wordpress.org | https://github.com/WordPress/WordPress |
| Shopify | https://www.shopify.com | https://github.com/Shopify/shopify-app-js |
| Drupal | https://www.drupal.org | https://github.com/drupal/drupal |
| Magento, Adobe Commerce | https://business.adobe.com/products/magento/magento-commerce.html | https://github.com/magento/magento2 |
| Odoo | https://www.odoo.com | https://github.com/odoo/odoo |
| Dolibarr | https://www.dolibarr.org | https://github.com/Dolibarr/dolibarr |

## Les extensions PieceMotoOccasion

- [PrestaShop](https://github.com/tony-dev-web/pmo-marketplace-prestashop)
- [WooCommerce](https://github.com/tony-dev-web/pmo-marketplace-woocommerce)
- [WordPress](https://github.com/tony-dev-web/pmo-marketplace-wordpress)
- [Shopify](https://github.com/tony-dev-web/pmo-marketplace-shopify)
- [Odoo](https://github.com/tony-dev-web/pmo-marketplace-odoo)
- [Dolibarr](https://github.com/tony-dev-web/pmo-marketplace-dolibarr)
- [Drupal](https://github.com/tony-dev-web/pmo-marketplace-drupal)
- [Magento](https://github.com/tony-dev-web/pmo-marketplace-magento)
- Toutes les extensions : https://piecemotooccasion.eu/extensions/
