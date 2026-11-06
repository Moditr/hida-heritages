"""Ingestion WordPress : les articles et les rubriques du site de HIDA.

Ce que fait ce script :
1. il récupère tous les articles du site, page par page, via l'API de WordPress ;
2. il récupère la liste des rubriques ;
3. il enregistre les deux réponses telles quelles dans Cloud Storage, rangées par source et par date.

Lancement, depuis la racine du dépôt :  python ingestion/wordpress.py
"""

import time

import requests

from stockage import ecrire_brut

# --- Réglages -----------------------------------------------------------------

URL_API = "https://hida-media.com/wp-json/wp/v2"
USER_AGENT = "HidaHeritagesBot/0.1 (https://github.com/Moditr/hida-heritages) python-requests"

# Les champs utiles des articles. Le reste (réglages Jetpack, liens techniques) est du bruit.
CHAMPS_ARTICLES = "id,date,modified,slug,link,title,excerpt,content,categories,author"

PAR_PAGE = 100  # le maximum autorisé par WordPress
ESSAIS = 3
ATTENTE_DEPART = 5


# --- Une demande à l'API, avec relances ------------------------------------------

def appeler(chemin: str, parametres: dict) -> requests.Response:
    """Envoie une demande à l'API. En cas d'échec : 5 s, puis 10 s d'attente (backoff)."""
    for tentative in range(1, ESSAIS + 1):
        try:
            reponse = requests.get(
                f"{URL_API}/{chemin}",
                params=parametres,
                headers={"User-Agent": USER_AGENT},
                timeout=30,
            )
            reponse.raise_for_status()
            return reponse
        except requests.RequestException as erreur:
            if tentative == ESSAIS:
                raise
            attente = ATTENTE_DEPART * 2 ** (tentative - 1)
            print(f"Essai {tentative} raté ({erreur}). Nouvel essai dans {attente} s...")
            time.sleep(attente)


# --- Extraire -------------------------------------------------------------------

def extraire_articles() -> list:
    """Récupère tous les articles, page par page."""
    articles = []
    page = 1
    while True:
        reponse = appeler("posts", {"per_page": PAR_PAGE, "page": page, "_fields": CHAMPS_ARTICLES})
        articles.extend(reponse.json())
        total_pages = int(reponse.headers["X-WP-TotalPages"])
        print(f"Page {page}/{total_pages} récupérée.")
        if page >= total_pages:
            return articles
        page += 1


def extraire_rubriques() -> list:
    """Récupère toutes les rubriques (il y en a moins de 100 : une seule page suffit)."""
    return appeler("categories", {"per_page": PAR_PAGE}).json()


# --- Lancement --------------------------------------------------------------------

if __name__ == "__main__":
    articles = extraire_articles()
    rubriques = extraire_rubriques()
    chemin_articles = ecrire_brut(articles, "wordpress", "articles.json")
    chemin_rubriques = ecrire_brut(rubriques, "wordpress", "rubriques.json")

    en_anglais = sum(1 for article in articles if "/en/" in article["link"])
    print(f"{len(articles)} articles ({len(articles) - en_anglais} en français, {en_anglais} en anglais).")
    print(f"{len(rubriques)} rubriques.")
    print(f"Fichiers bruts : {chemin_articles} et {chemin_rubriques}")