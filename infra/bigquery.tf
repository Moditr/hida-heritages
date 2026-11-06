# Les trois couches du médaillon : un dataset BigQuery chacune.
resource "google_bigquery_dataset" "couches" {
  for_each   = toset(["bronze", "silver", "gold"])
  dataset_id = each.key
  location   = var.region
}

# Les tables bronze : chacune lit directement les fichiers bruts d'une source dans le bucket.
locals {
  tables_bronze = {
    wikidata_auteurs    = { source = "wikidata", fichier = "auteurs.json" }
    wordpress_articles  = { source = "wordpress", fichier = "articles.json" }
    wordpress_rubriques = { source = "wordpress", fichier = "rubriques.json" }
  }
}

resource "google_bigquery_table" "bronze" {
  for_each            = local.tables_bronze
  dataset_id          = google_bigquery_dataset.couches["bronze"].dataset_id
  table_id            = each.key
  deletion_protection = false

  external_data_configuration {
    source_format = "NEWLINE_DELIMITED_JSON"
    autodetect    = true
    source_uris   = ["gs://${google_storage_bucket.brut.name}/source=${each.value.source}/*/${each.value.fichier}"]

    hive_partitioning_options {
      mode              = "AUTO"
      source_uri_prefix = "gs://${google_storage_bucket.brut.name}/source=${each.value.source}/"
    }
  }
}