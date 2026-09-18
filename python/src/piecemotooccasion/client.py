"""Client de l'API vendeur PieceMotoOccasion.

Aucune dependance hors « requests ». Le jeton se genere dans l'espace
vendeur, page « Ma boutique en ligne ».

    from piecemotooccasion import Pmo
    pmo = Pmo("VOTRE_JETON")
    pmo.envoyer([{"reference": "CAR-548", "titre": "Carter embrayage",
                  "prix_ttc": 29.90, "categorie": "Carter"}])
"""
import hashlib
import hmac

import requests

API = "https://piecemotooccasion.eu/api/v1"
LOT = 200          # fiches par appel PUT, limite de l'API
ENTETE_SIGNATURE = "X-Pmo-Signature"


class ErreurApi(RuntimeError):
    pass


class Pmo:
    def __init__(self, jeton, api=API, timeout=60):
        self.jeton = jeton
        self.api = api
        self.timeout = timeout

    def _appel(self, methode, chemin, corps=None):
        reponse = requests.request(
            methode, self.api + chemin, timeout=self.timeout, json=corps,
            headers={"Authorization": "Bearer " + self.jeton,
                     "User-Agent": "pmo-client/1.0"})
        try:
            donnees = reponse.json()
        except ValueError:
            raise ErreurApi("reponse illisible (HTTP %d)" % reponse.status_code)
        if reponse.status_code >= 400:
            raise ErreurApi(donnees.get("erreur", "HTTP %d" % reponse.status_code))
        return donnees

    # ------------------------------------------------------------- compte
    def moi(self):
        return self._appel("GET", "/moi")

    # ------------------------------------------------------------ catalogue
    def produits(self):
        return self._appel("GET", "/produits")["produits"]

    def envoyer(self, fiches):
        """Cree ou met a jour des pieces, par lots. Rend (resultats, erreurs)."""
        resultats, erreurs = [], []
        fiches = list(fiches)
        for debut in range(0, len(fiches), LOT):
            reponse = self._appel("PUT", "/produits", {"produits": fiches[debut:debut + LOT]})
            resultats += reponse.get("produits", [])
            erreurs += reponse.get("erreurs", [])
        return resultats, erreurs

    def stock(self, reference, quantite):
        return self._appel("PATCH", "/produits/%s/stock" % requests.utils.quote(reference),
                           {"stock": int(quantite)})

    def retirer(self, reference):
        return self._appel("DELETE", "/produits/%s" % requests.utils.quote(reference))

    # ------------------------------------------------------------ commandes
    def commandes(self, depuis=None):
        chemin = "/commandes" + ("?depuis=%s" % depuis if depuis else "")
        return self._appel("GET", chemin)["commandes"]

    def expedier(self, commande_id, transporteur, suivi):
        return self._appel("POST", "/commandes/%d/expedier" % int(commande_id),
                           {"transporteur": transporteur, "suivi": suivi})

    # -------------------------------------------------------------- webhook
    def signature_valide(self, corps, entete):
        """Verifie l'en-tete X-Pmo-Signature d'une notification de commande.

        « corps » est le corps brut de la requete, en octets : le signer apres
        re-serialisation JSON donnerait une signature differente.
        """
        attendu = "sha256=" + hmac.new(self.jeton.encode(), corps, hashlib.sha256).hexdigest()
        return hmac.compare_digest(attendu, entete or "")
