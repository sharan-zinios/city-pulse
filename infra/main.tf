provider "google" {
  project = var.project_id
  region  = "asia-south1"
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "pubsub.googleapis.com",
    "cloudfunctions.googleapis.com",
    "firestore.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "eventarc.googleapis.com",
    "workflows.googleapis.com"
  ])
  
  service = each.value
  disable_on_destroy = false
}

# 1. GKE Autopilot cluster for Memgraph
resource "google_container_cluster" "memgraph" {
  name     = "memgraph-ap"
  location = "asia-south1"
  enable_autopilot = true
  
  depends_on = [google_project_service.required_apis]
}

# 2. Cloud Storage buckets
resource "google_storage_bucket" "media" {
  name          = "${var.project_id}-bengaluru-events-media"
  location      = "ASIA-SOUTH1"
  force_destroy = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "data_lake" {
  name          = "${var.project_id}-city-pulse-data-lake"
  location      = "ASIA-SOUTH1"
  force_destroy = true
  
  versioning {
    enabled = true
  }
}

# 3. BigQuery dataset & tables
resource "google_bigquery_dataset" "events" {
  dataset_id = "bengaluru_events"
  location   = "asia-south1"
  
  depends_on = [google_project_service.required_apis]
}

resource "google_bigquery_table" "embeddings" {
  dataset_id = google_bigquery_dataset.events.dataset_id
  table_id   = "embeddings"
  schema     = file("embeddings_schema.json")
  
  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }
  
  clustering = ["area_category", "event_type", "severity_level"]
}

resource "google_bigquery_table" "real_time_incidents" {
  dataset_id = google_bigquery_dataset.events.dataset_id
  table_id   = "real_time_incidents"
  schema     = file("embeddings_schema.json")
  
  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }
  
  clustering = ["priority_score", "event_status", "assigned_department"]
}

resource "google_bigquery_table" "analytics" {
  dataset_id = google_bigquery_dataset.events.dataset_id
  table_id   = "analytics"
  
  schema = jsonencode([
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "metric_name"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "metric_value"
      type = "FLOAT"
      mode = "REQUIRED"
    },
    {
      name = "dimensions"
      type = "JSON"
      mode = "NULLABLE"
    }
  ])
  
  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }
}

# 4. Pub/Sub Topics for Real-time Streaming
resource "google_pubsub_topic" "incident_stream" {
  name = "incident-stream"
  
  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_topic" "notification_stream" {
  name = "notification-stream"
}

resource "google_pubsub_topic" "analytics_stream" {
  name = "analytics-stream"
}

resource "google_pubsub_topic" "agent_tasks" {
  name = "agent-tasks"
}

# Pub/Sub Subscriptions
resource "google_pubsub_subscription" "incident_processor" {
  name  = "incident-processor"
  topic = google_pubsub_topic.incident_stream.name
  
  ack_deadline_seconds = 60
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }
}

resource "google_pubsub_subscription" "notification_processor" {
  name  = "notification-processor"
  topic = google_pubsub_topic.notification_stream.name
  
  ack_deadline_seconds = 30
}

resource "google_pubsub_subscription" "analytics_processor" {
  name  = "analytics-processor"
  topic = google_pubsub_topic.analytics_stream.name
  
  ack_deadline_seconds = 120
}

resource "google_pubsub_subscription" "agent_worker" {
  name  = "agent-worker"
  topic = google_pubsub_topic.agent_tasks.name
  
  ack_deadline_seconds = 300
}

resource "google_pubsub_topic" "dead_letter" {
  name = "dead-letter-topic"
}

# 5. Firestore for Real-time UI Updates
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = "asia-south1"
  type        = "FIRESTORE_NATIVE"
  
  depends_on = [google_project_service.required_apis]
}

# 6. Cloud Functions for Event Processing
resource "google_storage_bucket" "functions_source" {
  name     = "${var.project_id}-functions-source"
  location = "ASIA-SOUTH1"
}

# 7. Vertex AI Vector Search
resource "google_vertex_ai_index" "incident_embeddings" {
  display_name = "incident-embeddings-index"
  description  = "Vector index for incident embeddings"
  region       = "asia-south1"
  
  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.data_lake.name}/embeddings/"
    config {
      dimensions = 768
      approximate_neighbors_count = 150
      distance_measure_type = "COSINE_DISTANCE"
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count = 500
          leaf_nodes_to_search_percent = 7
        }
      }
    }
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_vertex_ai_index_endpoint" "incident_endpoint" {
  display_name = "incident-endpoint"
  description  = "Endpoint for incident vector search"
  region       = "asia-south1"
  
  depends_on = [google_vertex_ai_index.incident_embeddings]
}

# 8. Cloud Monitoring and Alerting
resource "google_monitoring_notification_channel" "email" {
  display_name = "City Pulse Alerts"
  type         = "email"
  
  labels = {
    email_address = "admin@citypulse.com"
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_monitoring_alert_policy" "high_priority_incidents" {
  display_name = "High Priority Incidents"
  combiner     = "OR"
  
  conditions {
    display_name = "High priority incident rate"
    
    condition_threshold {
      filter          = "resource.type=\"pubsub_topic\" AND resource.labels.topic_id=\"incident-stream\""
      duration        = "300s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 10
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
  
  alert_strategy {
    auto_close = "1800s"
  }
}

# 9. Cloud Scheduler for Periodic Tasks
resource "google_cloud_scheduler_job" "analytics_aggregation" {
  name     = "analytics-aggregation"
  schedule = "0 */6 * * *"  # Every 6 hours
  
  http_target {
    http_method = "POST"
    uri         = "https://asia-south1-${var.project_id}.cloudfunctions.net/analytics-aggregator"
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({
      "task": "aggregate_analytics"
    }))
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_cloud_scheduler_job" "trend_analysis" {
  name     = "trend-analysis"
  schedule = "0 8,14,20 * * *"  # 8 AM, 2 PM, 8 PM
  
  http_target {
    http_method = "POST"
    uri         = "https://asia-south1-${var.project_id}.cloudfunctions.net/trend-analyzer"
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({
      "task": "analyze_trends"
    }))
  }
}

# 10. Service Accounts and IAM
resource "google_service_account" "city_pulse_agents" {
  account_id   = "city-pulse-agents"
  display_name = "City Pulse Intelligent Agents"
}

resource "google_project_iam_member" "agents_permissions" {
  for_each = toset([
    "roles/pubsub.publisher",
    "roles/pubsub.subscriber",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/storage.objectAdmin",
    "roles/firestore.user",
    "roles/aiplatform.user",
    "roles/monitoring.metricWriter"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.city_pulse_agents.email}"
}

# Outputs
output "pubsub_topics" {
  value = {
    incident_stream     = google_pubsub_topic.incident_stream.name
    notification_stream = google_pubsub_topic.notification_stream.name
    analytics_stream    = google_pubsub_topic.analytics_stream.name
    agent_tasks         = google_pubsub_topic.agent_tasks.name
  }
}

output "storage_buckets" {
  value = {
    media     = google_storage_bucket.media.name
    data_lake = google_storage_bucket.data_lake.name
  }
}

output "bigquery_tables" {
  value = {
    embeddings        = "${google_bigquery_dataset.events.dataset_id}.${google_bigquery_table.embeddings.table_id}"
    real_time_incidents = "${google_bigquery_dataset.events.dataset_id}.${google_bigquery_table.real_time_incidents.table_id}"
    analytics         = "${google_bigquery_dataset.events.dataset_id}.${google_bigquery_table.analytics.table_id}"
  }
}