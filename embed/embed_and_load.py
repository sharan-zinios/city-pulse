import os
import json
from datetime import datetime
from google.cloud import aiplatform, bigquery
from vertexai.language_models import TextEmbeddingModel
from google.cloud import storage

aiplatform.init(project=os.getenv("PROJECT_ID"), location="asia-south1")
model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
bq = bigquery.Client()

incidents = json.load(open("incidents.json"))
rows = []

for incident in incidents:
    # Create text for embedding (combine description and keywords)
    embedding_text = f"{incident['description']} {' '.join(incident['keywords'])}"
    
    # Generate text embedding
    txt_emb = model.get_embeddings([embedding_text])[0].values  # 768-dim for gecko
    
    # Convert timestamp to proper format
    timestamp = datetime.fromisoformat(incident['timestamp'].replace('Z', '+00:00'))
    
    row = {
        "id": incident["id"],
        "event_type": incident["event_type"],
        "sub_category": incident["sub_category"],
        "description": incident["description"],
        "keywords": incident["keywords"],
        "language": incident["language"],
        "coordinates": incident["coordinates"],
        "location_name": incident["location_name"],
        "area_category": incident["area_category"],
        "ward_number": incident["ward_number"],
        "pincode": incident["pincode"],
        "timestamp": timestamp.isoformat(),
        "estimated_duration": incident["estimated_duration"],
        "actual_duration": incident["actual_duration"],
        "peak_hours": incident["peak_hours"],
        "severity_level": incident["severity_level"],
        "priority_score": incident["priority_score"],
        "impact_radius": incident["impact_radius"],
        "source": incident["source"],
        "verified": incident["verified"],
        "reporter_id": incident["reporter_id"],
        "verification_count": incident["verification_count"],
        "media_type": incident["media_type"],
        "media_url": incident["media_url"],
        "event_status": incident["event_status"],
        "assigned_department": incident["assigned_department"],
        "resolution_notes": incident["resolution_notes"],
        "weather_condition": incident["weather_condition"],
        "traffic_density": incident["traffic_density"],
        "embedding": [{"value": float(x)} for x in txt_emb]
    }
    rows.append(row)

# Load into BigQuery
table_id = f"{os.getenv('PROJECT_ID')}.bengaluru_events.embeddings"
job = bq.load_table_from_json(rows, table_id)
job.result()  # Wait for completion
print(f"Loaded {len(rows)} incident records with embeddings into {table_id}")

# Print some statistics
print(f"\nData Statistics:")
print(f"Total incidents: {len(rows)}")
print(f"Event types: {len(set(r['event_type'] for r in rows))}")
print(f"Locations: {len(set(r['location_name'] for r in rows))}")
print(f"Severity levels: {set(r['severity_level'] for r in rows)}")
print(f"Average priority score: {sum(r['priority_score'] for r in rows) / len(rows):.2f}")
print(f"Peak hours incidents: {sum(1 for r in rows if r['peak_hours'])}")
print(f"Verified incidents: {sum(1 for r in rows if r['verified'] > 0.8)}")
