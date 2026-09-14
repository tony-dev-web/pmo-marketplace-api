"""Envoie un fichier CSV de catalogue vers l'API PieceMotoOccasion.

Le meme fichier que celui accepte par la console vendeur, mais pousse par
script : utile pour un envoi automatique chaque nuit depuis un logiciel de
casse, sans passer par le navigateur.

    python importer_csv.py VOTRE_JETON modele-catalogue.csv

Colonnes obligatoires : reference, titre, prix_ttc. La categorie est
demandee par l'API : « Piece moto » est envoyee a defaut.
"""
import csv
import sys

from pmo_client import ErreurApi, Pmo

CATEGORIE_DEFAUT = "Pièce moto"
LOT = 200

# Les noms de colonnes acceptes, comme dans la console vendeur.
COLONNES = {
    "reference": ("reference", "ref", "sku", "code"),
    "titre": ("titre", "title", "nom", "designation", "libelle"),
    "prix_ttc": ("prix_ttc", "prix", "price", "prix de vente"),
    "categorie": ("categorie", "category", "famille"),
    "stock": ("stock", "quantite", "qte", "quantity"),
    "description": ("description",),
    "marque": ("marque", "brand"),
    "modele": ("modele", "model"),
    "annee_min": ("annee_min", "annee"),
    "annee_max": ("annee_max",),
    "cylindree": ("cylindree", "cm3"),
    "poids": ("poids", "weight"),
    "etat_achat": ("etat", "etat_achat", "condition"),
    "reference_oem": ("reference_oem", "oem"),
    "images": ("images", "image", "photo"),
}


def normaliser(nom):
    return (nom or "").strip().lower().replace("é", "e").replace("è", "e")


def fiche_de(ligne):
    fiche = {}
    for champ, noms in COLONNES.items():
        for cle, valeur in ligne.items():
            if normaliser(cle) in noms and (valeur or "").strip():
                valeur = valeur.strip()
                fiche[champ] = valeur.replace(",", ".") if champ == "prix_ttc" else valeur
                break
    if "images" in fiche:
        fiche["images"] = [u for u in fiche["images"].replace(",", " ").split() if u.startswith("http")]
    fiche.setdefault("categorie", CATEGORIE_DEFAUT)
    return fiche


def principal(jeton, chemin):
    with open(chemin, encoding="utf-8-sig", newline="") as fichier:
        premiere = fichier.readline()
        fichier.seek(0)
        separateur = max(";,\t", key=premiere.count)
        fiches = [fiche_de(ligne) for ligne in csv.DictReader(fichier, delimiter=separateur)]

    pmo = Pmo(jeton)
    resultats, erreurs = pmo.envoyer(fiches)
    print("%d piece(s) envoyee(s), %d refusee(s)" % (len(resultats), len(erreurs)))
    for erreur in erreurs:
        print("  %s : %s" % (erreur.get("reference"), erreur.get("erreur")))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage : python importer_csv.py VOTRE_JETON catalogue.csv")
    try:
        principal(sys.argv[1], sys.argv[2])
    except ErreurApi as erreur:
        sys.exit("API : %s" % erreur)
