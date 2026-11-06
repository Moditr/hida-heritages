"""Écriture des fichiers bruts dans Cloud Storage.

Ce fichier est partagé par tous les scripts d'ingestion : chacun appelle ecrire_brut()
au lieu d'avoir sa propre façon d'enregistrer.
"""

import json
from datetime import date

from google.cloud import storage

PROJET = "hida-heritages"
BUCKET = "hida-heritages-raw"


def ecrire_brut(enregistrements: list, source: str, nom_fichier: str) -> str:
    """Écrit les enregistrements dans le bucket, un par ligne (format JSON Lines),
    rangés par source et par date.

    Le chemin est fixe pour une date donnée : relancer le même jour REMPLACE le fichier.
    """
    chemin = f"source={source}/date={date.today().isoformat()}/{nom_fichier}"
    contenu = "\n".join(json.dumps(enregistrement, ensure_ascii=False) for enregistrement in enregistrements)

    client = storage.Client(project=PROJET)
    fichier = client.bucket(BUCKET).blob(chemin)
    fichier.upload_from_string(contenu, content_type="application/x-ndjson")

    return f"gs://{BUCKET}/{chemin}"