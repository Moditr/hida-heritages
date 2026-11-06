"""Ingestion Wikidata : auteurs africains et leurs influences.

Ce que fait ce script :
1. il envoie une requête SPARQL à Wikidata ;
2. il enregistre la réponse telle quelle (la « photo exacte ») dans un fichier JSON,
   rangé par source et par date, comme dans Cloud Storage plus tard.

Lancement, depuis la racine du dépôt :  python ingestion/wikidata.py
"""

import json
import time
from datetime import date
from pathlib import Path

import requests

# --- Réglages -----------------------------------------------------------------

# L'adresse publique où Wikidata reçoit les requêtes SPARQL.
URL_SPARQL = "https://query.wikidata.org/sparql"

# Wikimedia demande aux programmes de se présenter, avec un moyen de contact.
# Remplace Moditr par ton nom d'utilisateur GitHub.
USER_AGENT = "HidaHeritagesBot/0.1 (https://github.com/Moditr/hida-heritages) python-requests"

# La requête testée dans le navigateur. DISTINCT retire les doublons parasites
# (un auteur avec deux nationalités africaines sortirait deux fois).
REQUETE = """
SELECT DISTINCT ?auteur ?auteurLabel ?influence ?influenceLabel WHERE {
  ?auteur wdt:P31 wd:Q5 ;
          wdt:P106 wd:Q36180 ;
          wdt:P27 ?pays ;
          wdt:P737 ?influence .
  ?pays wdt:P30 wd:Q15 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en". }
}
"""

# Nombre d'essais avant d'abandonner, et attente de départ (en secondes).
ESSAIS = 3
ATTENTE_DEPART = 5

# Où ranger le fichier brut. Même logique que le futur chemin dans Cloud Storage :
# source=wikidata/date=AAAA-MM-JJ/auteurs.json
DOSSIER_BRUT = Path("data/raw")


# --- Étape 1 : extraire ---------------------------------------------------------

def extraire() -> dict:
    """Interroge Wikidata et renvoie la réponse JSON.

    Si Wikidata ne répond pas (panne, surcharge, délai dépassé), on réessaie
    en attendant de plus en plus longtemps : 5 s, puis 10 s. C'est le backoff
    exponentiel : on laisse la source se rétablir sans la bombarder.
    """
    for tentative in range(1, ESSAIS + 1):
        try:
            reponse = requests.get(
                URL_SPARQL,
                params={"query": REQUETE, "format": "json"},
                headers={"User-Agent": USER_AGENT},
                timeout=90,  # Wikidata coupe à 60 s : on attend un peu plus pour recevoir son message d'erreur
            )
            reponse.raise_for_status()  # transforme une réponse d'erreur (500, 429...) en exception
            return reponse.json()
        except requests.RequestException as erreur:
            if tentative == ESSAIS:
                raise  # dernier essai raté : on arrête et on montre l'erreur
            attente = ATTENTE_DEPART * 2 ** (tentative - 1)
            print(f"Essai {tentative} raté ({erreur}). Nouvel essai dans {attente} s...")
            time.sleep(attente)


# --- Étape 2 : sauvegarder ------------------------------------------------------

def sauvegarder(donnees: dict) -> Path:
    """Écrit la réponse brute dans un fichier daté.

    Le nom du fichier est fixe pour une date donnée : relancer le script le même
    jour REMPLACE le fichier au lieu d'en ajouter un deuxième. C'est l'idempotence.
    """
    chemin = DOSSIER_BRUT / "source=wikidata" / f"date={date.today().isoformat()}" / "auteurs.json"
    chemin.parent.mkdir(parents=True, exist_ok=True)  # crée les dossiers s'ils n'existent pas
    with chemin.open("w", encoding="utf-8") as fichier:
        json.dump(donnees, fichier, ensure_ascii=False, indent=2)
    return chemin


# --- Lancement ------------------------------------------------------------------

if __name__ == "__main__":
    donnees = extraire()
    lignes = donnees["results"]["bindings"]  # la liste des résultats, une entrée par lien auteur -> influence
    chemin = sauvegarder(donnees)

    auteurs = {ligne["auteur"]["value"] for ligne in lignes}
    print(f"{len(lignes)} liens d'héritage récupérés, pour {len(auteurs)} auteurs différents.")
    print(f"Fichier brut : {chemin}")