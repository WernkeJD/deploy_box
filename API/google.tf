variable "MONGO_URI" {
  type = string
}

variable "FRONTEND_IMAGE" {
  description = "Docker image for frontend"
  type        = string
}

variable "BACKEND_IMAGE" {
  description = "Docker image for backend"
  type        = string
}

provider "google" {
  project = "deploy-box"
  region  = "us-central1"
}

resource "google_cloud_run_service" "default_backend" {
  name     = "my-cloud-run-backend"
  location = "us-central1"

  template {
    spec {
      containers {
        image = var.BACKEND_IMAGE
        ports {
          container_port = 8080
        }
        env {
          name  = "MONGO_URI"
          value = var.MONGO_URI
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "noauth_backend" {
  location = google_cloud_run_service.default_backend.location
  service  = google_cloud_run_service.default_backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "backend_url" {
  value = google_cloud_run_service.default_backend.status[0].url
}

resource "google_cloud_run_service" "default_frontend" {
  name     = "my-cloud-run-frontend"
  location = "us-central1"

  template {
    spec {
      containers {
        image = var.FRONTEND_IMAGE
        ports {
          container_port = 8080
        }
        env {
          name  = "REACT_APP_BACKEND_URL"
          value = google_cloud_run_service.default_backend.status[0].url
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

depends_on = [google_cloud_run_service.default_backend]
}

resource "google_cloud_run_service_iam_member" "noauth_frontend" {
  location = google_cloud_run_service.default_frontend.location
  service  = google_cloud_run_service.default_frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "url_frontend" {
  value = google_cloud_run_service.default_frontend.status[0].url
}