"""Exemple de reception du webhook des commandes, en Flask.

PieceMotoOccasion envoie un POST JSON signe a l'URL de notification
renseignee dans l'espace vendeur. La signature se verifie sur le corps
BRUT : re-serialiser le JSON change les octets, donc la signature.
"""
from flask import Flask, request

from pmo_client import Pmo

JETON = "VOTRE_JETON"
app = Flask(__name__)
pmo = Pmo(JETON)


@app.post("/pmo/commande")
def commande():
    if not pmo.signature_valide(request.get_data(), request.headers.get("X-Pmo-Signature")):
        return {"erreur": "signature invalide"}, 403
    donnees = request.get_json(silent=True) or {}
    if donnees.get("evenement") != "commande.payee":
        return {"ok": True, "ignore": True}
    commande = donnees["commande"]
    # A vous de jouer : enregistrer la commande, imprimer le bon de preparation…
    print("Commande %s, %s EUR" % (commande["id"], commande["total_ttc"]))
    return {"ok": True}
