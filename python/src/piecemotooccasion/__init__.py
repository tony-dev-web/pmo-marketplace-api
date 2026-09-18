"""Client Python de l'API vendeur PieceMotoOccasion.

    from piecemotooccasion import Pmo

    pmo = Pmo("VOTRE_JETON")
    pmo.envoyer([{"reference": "CAR-548", "titre": "Carter embrayage",
                  "prix_ttc": 29.90, "categorie": "Carter"}])

Documentation : https://piecemotooccasion.eu/extensions/api
"""
from piecemotooccasion.client import API, ENTETE_SIGNATURE, LOT, ErreurApi, Pmo

__all__ = ["Pmo", "ErreurApi", "API", "LOT", "ENTETE_SIGNATURE"]
__version__ = "1.0.0"
