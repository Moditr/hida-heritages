"""Ingestion Wikidata : auteurs africains et leurs influences.

Ce que fait ce script :
1. il envoie une requête SPARQL à Wikidata ;
2. il enregistre la réponse telle quelle (la « photo exacte ») dans Cloud Storage,
   rangée par source et par date.

Lancement, depuis la racine du dépôt :  python ingestion/wikidata.py
"""

import time

import requests

from stockage import ecrire_brut

# --- Réglages -----------------------------------------------------------------

URL_SPARQL = "https://query.wikidata.org/sparql"
USER_AGENT = "HidaHeritagesBot/0.1 (https://github.com/Moditr/hida-heritages) python-requests"

# On part du plus petit tas (les personnes qui ont un « influencé par »), puis on filtre.
# DISTINCT retire les doublons parasites (un auteur avec deux nationalités africaines).
REQUETE = """
SELECT DISTINCT ?auteur ?auteurLabel ?influence ?influenceLabel WHERE {
  hint:Query hint:optimizer "None" .
  ?auteur wdt:P737 ?influence .
  ?auteur wdt:P27 ?pays .
  ?pays wdt:P30 wd:Q15 .
  ?auteur wdt:P106 wd:Q36180 .
  ?auteur wdt:P31 wd:Q5 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
}
"""

ESSAIS = 3
ATTENTE_DEPART = 5


# --- Extraire -------------------------------------------------------------------

def extraire() -> dict:
    """Interroge Wikidata. En cas d'échec : 5 s, puis 10 s d'attente (backoff)."""
    for tentative in range(1, ESSAIS + 1):
        try:
            reponse = requests.get(
                URL_SPARQL,
                params={"query": REQUETE, "format": "json"},
                headers={"User-Agent": USER_AGENT},
                timeout=90,  # Wikidata coupe à 60 s : on attend un peu plus pour recevoir son message d'erreur
            )
            reponse.raise_for_status()
            return reponse.json()
        except requests.RequestException as erreur:
            if tentative == ESSAIS:
                raise
            attente = ATTENTE_DEPART * 2 ** (tentative - 1)
            print(f"Essai {tentative} raté ({erreur}). Nouvel essai dans {attente} s...")
            time.sleep(attente)


# --- Lancement ------------------------------------------------------------------

if __name__ == "__main__":
    donnees = extraire()
    lignes = donnees["results"]["bindings"]
    chemin = ecrire_brut(donnees, "wikidata", "auteurs.json")

    auteurs = {ligne["auteur"]["value"] for ligne in lignes}
    print(f"{len(lignes)} liens d'héritage récupérés, pour {len(auteurs)} auteurs différents.")
    print(f"Fichier brut : {chemin}")