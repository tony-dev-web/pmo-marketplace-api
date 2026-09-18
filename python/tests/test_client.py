"""Le client sans reseau : « requests.request » est remplace par un double.

On verifie ce que le client envoie — methode, adresse, corps, decoupage en
lots — et ce qu'il fait des reponses. Le serveur, lui, a ses propres tests.
"""
import hashlib
import hmac
import json
import unittest
from unittest import mock

from piecemotooccasion import ErreurApi, Pmo

JETON = "jeton-de-test-0123456789"


class Reponse:
    def __init__(self, donnees, statut=200, illisible=False):
        self._donnees = donnees
        self.status_code = statut
        self._illisible = illisible

    def json(self):
        if self._illisible:
            raise ValueError("pas du JSON")
        return self._donnees


class Double:
    """Retient les appels et rend les reponses preparees, dans l'ordre."""

    def __init__(self, *reponses):
        self.appels = []
        self.reponses = list(reponses)

    def __call__(self, methode, url, **kw):
        self.appels.append({"methode": methode, "url": url, **kw})
        return self.reponses.pop(0) if self.reponses else Reponse({})


def client(*reponses):
    double = Double(*reponses)
    pmo = Pmo(JETON)
    return pmo, double, mock.patch("piecemotooccasion.client.requests.request", double)


class Appel(unittest.TestCase):
    def test_le_jeton_part_en_bearer(self):
        pmo, double, patch = client(Reponse({"vendeur": "Casse du Nord"}))
        with patch:
            pmo.moi()
        self.assertEqual(double.appels[0]["headers"]["Authorization"], "Bearer " + JETON)

    def test_le_compte_est_un_get_sur_moi(self):
        pmo, double, patch = client(Reponse({"vendeur_id": 9}))
        with patch:
            self.assertEqual(pmo.moi()["vendeur_id"], 9)
        self.assertEqual(double.appels[0]["methode"], "GET")
        self.assertTrue(double.appels[0]["url"].endswith("/moi"))

    def test_une_erreur_de_l_api_devient_une_exception(self):
        pmo, _, patch = client(Reponse({"erreur": "jeton invalide"}, 401))
        with patch, self.assertRaises(ErreurApi) as leve:
            pmo.moi()
        self.assertIn("jeton invalide", str(leve.exception))

    def test_une_reponse_illisible_ne_passe_pas_pour_un_succes(self):
        pmo, _, patch = client(Reponse(None, 502, illisible=True))
        with patch, self.assertRaises(ErreurApi) as leve:
            pmo.moi()
        self.assertIn("502", str(leve.exception))


class Catalogue(unittest.TestCase):
    def test_deux_cent_une_fiches_font_deux_appels(self):
        fiches = [{"reference": "R%d" % i, "titre": "T", "prix_ttc": 1, "categorie": "C"}
                  for i in range(201)]
        pmo, double, patch = client(Reponse({"produits": [], "erreurs": []}),
                                    Reponse({"produits": [], "erreurs": []}))
        with patch:
            pmo.envoyer(fiches)
        self.assertEqual(len(double.appels), 2)
        self.assertEqual(len(double.appels[0]["json"]["produits"]), 200)
        self.assertEqual(len(double.appels[1]["json"]["produits"]), 1)

    def test_un_generateur_est_accepte_comme_une_liste(self):
        pmo, double, patch = client(Reponse({"produits": [{"reference": "R0"}]}))
        with patch:
            resultats, _ = pmo.envoyer({"reference": "R%d" % i} for i in range(3))
        self.assertEqual(len(double.appels[0]["json"]["produits"]), 3)
        self.assertEqual(len(resultats), 1)

    def test_les_fiches_refusees_sont_rendues_a_part(self):
        pmo, _, patch = client(Reponse({
            "produits": [{"reference": "R1"}],
            "erreurs": [{"reference": "R2", "erreur": "prix_ttc doit etre positif"}]}))
        with patch:
            resultats, erreurs = pmo.envoyer([{"reference": "R1"}, {"reference": "R2"}])
        self.assertEqual(len(resultats), 1)
        self.assertEqual(erreurs[0]["reference"], "R2")

    def test_aucune_fiche_n_appelle_pas_l_api(self):
        pmo, double, patch = client()
        with patch:
            self.assertEqual(pmo.envoyer([]), ([], []))
        self.assertEqual(double.appels, [])

    def test_la_reference_est_echappee_dans_l_adresse(self):
        pmo, double, patch = client(Reponse({"reference": "REF /1", "stock": 3}))
        with patch:
            pmo.stock("REF /1", 3)
        self.assertEqual(double.appels[0]["methode"], "PATCH")
        self.assertTrue(double.appels[0]["url"].endswith("/produits/REF%20/1/stock"),
                        double.appels[0]["url"])

    def test_le_stock_est_transmis_en_entier(self):
        pmo, double, patch = client(Reponse({"stock": 3}))
        with patch:
            pmo.stock("R1", "3")
        self.assertEqual(double.appels[0]["json"], {"stock": 3})

    def test_retirer_est_un_delete(self):
        pmo, double, patch = client(Reponse({"retire": True}))
        with patch:
            self.assertTrue(pmo.retirer("R1")["retire"])
        self.assertEqual(double.appels[0]["methode"], "DELETE")


class Commandes(unittest.TestCase):
    def test_lister_rend_la_liste_pas_l_enveloppe(self):
        pmo, _, patch = client(Reponse({"commandes": [{"id": 1}, {"id": 2}]}))
        with patch:
            self.assertEqual(len(pmo.commandes()), 2)

    def test_le_filtre_depuis_passe_en_parametre(self):
        pmo, double, patch = client(Reponse({"commandes": []}))
        with patch:
            pmo.commandes(depuis="2026-09-01")
        self.assertTrue(double.appels[0]["url"].endswith("/commandes?depuis=2026-09-01"))

    def test_sans_filtre_l_adresse_reste_nue(self):
        pmo, double, patch = client(Reponse({"commandes": []}))
        with patch:
            pmo.commandes()
        self.assertTrue(double.appels[0]["url"].endswith("/commandes"))

    def test_expedier_poste_transporteur_et_suivi(self):
        pmo, double, patch = client(Reponse({"expedition": "EXPEDIEE"}))
        with patch:
            pmo.expedier(1043, "Colissimo", "6A12345678901")
        self.assertEqual(double.appels[0]["methode"], "POST")
        self.assertTrue(double.appels[0]["url"].endswith("/commandes/1043/expedier"))
        self.assertEqual(double.appels[0]["json"]["suivi"], "6A12345678901")


class Signature(unittest.TestCase):
    @staticmethod
    def signer(corps, jeton=JETON):
        return "sha256=" + hmac.new(jeton.encode(), corps, hashlib.sha256).hexdigest()

    def test_la_signature_de_la_marketplace_est_acceptee(self):
        corps = json.dumps({"evenement": "commande.payee"}).encode()
        self.assertTrue(Pmo(JETON).signature_valide(corps, self.signer(corps)))

    def test_un_autre_jeton_est_refuse(self):
        corps = b'{"evenement":"commande.payee"}'
        self.assertFalse(Pmo(JETON).signature_valide(corps, self.signer(corps, "autre")))

    def test_un_corps_modifie_apres_signature_est_refuse(self):
        signature = self.signer(b'{"total":"10.00"}')
        self.assertFalse(Pmo(JETON).signature_valide(b'{"total":"0.01"}', signature))

    def test_une_signature_absente_est_refusee_sans_exception(self):
        corps = b"{}"
        self.assertFalse(Pmo(JETON).signature_valide(corps, None))
        self.assertFalse(Pmo(JETON).signature_valide(corps, ""))


if __name__ == "__main__":
    unittest.main()
