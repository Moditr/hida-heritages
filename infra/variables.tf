variable "projet" {
  description = "Identifiant du projet Google Cloud"
  type        = string
  default     = "hida-heritages"
}

variable "region" {
  description = "Région des ressources (offre gratuite de Cloud Storage)"
  type        = string
  default     = "us-central1"
}