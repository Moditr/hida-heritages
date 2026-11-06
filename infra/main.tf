terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.projet
  region  = var.region
}

resource "google_storage_bucket" "brut" {
  name                        = "hida-heritages-raw"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
}