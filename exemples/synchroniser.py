"""Exemple complet : envoi du catalogue, mise a jour du stock, expedition.

    python synchroniser.py VOTRE_JETON
"""
import sys

from pmo_client import ErreurApi, Pmo

CATALOGUE = [
    {"reference": "CAR-548", "titre": "Carter embrayage XJ 600 Diversion",
     "prix_ttc": 29.90, "categorie": "Carter", "marque": "Yamaha",
     "modele": "XJ 600 Diversion", "annee_min": 1998, "annee_max": 2003,
     "stock": 1, "poids": 1200, "etat_achat": "Occasion",
     "images": ["https://ma-casse.fr/photos/car-548.jpg"]},
]


def principal(jeton):
    pmo = Pmo(jeton)
    compte = pmo.moi()
    print("Vendeur %s, commission %s %%" % (compte["vendeur"], compte["commission"]))

    resultats, erreurs = pmo.envoyer(CATALOGUE)
    print("%d piece(s) envoyee(s), %d refusee(s)" % (len(resultats), len(erreurs)))
    for erreur in erreurs:
        print("  %s : %s" % (erreur.get("reference"), erreur.get("erreur")))

    # Une piece vendue ailleurs : stock a zero, elle sort des flux sans etre effacee.
    pmo.stock("CAR-548", 0)

    for commande in pmo.commandes(depuis="2026-09-01"):
        livraison = commande["livraison"]
        print("Commande %d : %s, %s %s" % (commande["id"], livraison["nom"],
                                           livraison["code_postal"], livraison["ville"]))
        # pmo.expedier(commande["id"], "Colissimo", "6A12345678901")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage : python synchroniser.py VOTRE_JETON")
    try:
        principal(sys.argv[1])
    except ErreurApi as erreur:
        sys.exit("API : %s" % erreur)
