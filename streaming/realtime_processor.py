import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor
import asyncio

from google.cloud import pubsub_v1
from google.cloud import bigquery
from google.cloud import firestore
from google.cloud import storage
from google.cloud import aiplatform
import vertexai
from vertexai.language_models import TextEmbeddingModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTimeIncidentProcessor:
    """Real-time incident data processor with streaming capabilities"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        self.bq_client = bigquery.Client(project=project_id)
        self.firestore_client = firestore.Client(project=project_id)
        self.storage_client = storage.Client(project=project_id)
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location="asia-south1")
        self.embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
        
        # Topic paths
        self.incident_topic = self.publisher.topic_path(project_id, "incident-stream")
        self.notification_topic = self.publisher.topic_path(project_id, "notification-stream")
        self.analytics_topic = self.publisher.topic_path(project_id, "analytics-stream")
        self.agent_topic = self.publisher.topic_path(project_id, "agent-tasks")
        
        # Subscription paths
        self.incident_subscription = self.subscriber.subscription_path(project_id, "incident-processor")
        
        # BigQuery tables
        self.embeddings_table = f"{project_id}.bengaluru_events.embeddings"
        self.realtime_table = f"{project_id}.bengaluru_events.real_time_incidents"
        self.analytics_table = f"{project_id}.bengaluru_events.analytics"
        
    def publish_incident(self, incident_data: Dict[str, Any]) -> str:
        """Publish incident to real-time stream"""
        try:
            # Add processing metadata
            incident_data.update({
                "stream_timestamp": datetime.utcnow().isoformat(),
                "processing_status": "pending",
                "source_type": "real_time"
            })
            
            # Publish to incident stream
            message_data = json.dumps(incident_data).encode('utf-8')
            future = self.publisher.publish(self.incident_topic, message_data)
            message_id = future.result()
            
            logger.info(f"Published incident {incident_data.get('id')} to stream: {message_id}")
            
            # Trigger agent tasks for high-priority incidents
            if incident_data.get("priority_score", 0) >= 8.0:
                self._trigger_high_priority_agents(incident_data)
            
            return message_id
            
        except Exception as e:
            logger.error(f"Error publishing incident: {e}")
            raise
    
    def _trigger_high_priority_agents(self, incident_data: Dict[str, Any]):
        """Trigger intelligent agents for high-priority incidents"""
        agent_tasks = [
            {
                "task_type": "notification_blast",
                "incident_id": incident_data["id"],
                "priority": "high",
                "departments": [incident_data.get("assigned_department")],
                "radius_km": incident_data.get("impact_radius", 2.0)
            },
            {
                "task_type": "trend_analysis",
                "incident_id": incident_data["id"],
                "event_type": incident_data["event_type"],
                "location": incident_data.get("location_name")
            },
            {
                "task_type": "resource_allocation",
                "incident_id": incident_data["id"],
                "severity": incident_data.get("severity_level"),
                "estimated_duration": incident_data.get("estimated_duration")
            }
        ]
        
        for task in agent_tasks:
            task_data = json.dumps(task).encode('utf-8')
            self.publisher.publish(self.agent_topic, task_data)
    
    def process_incident_stream(self, message):
        """Process incoming incident from stream"""
        try:
            incident_data = json.loads(message.data.decode('utf-8'))
            incident_id = incident_data.get("id")
            
            logger.info(f"Processing incident: {incident_id}")
            
            # 1. Generate embeddings
            embedding_text = f"{incident_data['description']} {' '.join(incident_data.get('keywords', []))}"
            embeddings = self.embedding_model.get_embeddings([embedding_text])[0].values
            
            # 2. Prepare data for BigQuery
            bq_row = self._prepare_bigquery_row(incident_data, embeddings)
            
            # 3. Insert into BigQuery (both tables)
            self._insert_to_bigquery([bq_row])
            
            # 4. Update Firestore for real-time UI
            self._update_firestore(incident_data)
            
            # 5. Publish analytics events
            self._publish_analytics_events(incident_data)
            
            # 6. Send notifications if needed
            if incident_data.get("priority_score", 0) >= 7.0:
                self._send_notifications(incident_data)
            
            message.ack()
            logger.info(f"Successfully processed incident: {incident_id}")
            
        except Exception as e:
            logger.error(f"Error processing incident: {e}")
            message.nack()
    
    def _prepare_bigquery_row(self, incident_data: Dict[str, Any], embeddings: List[float]) -> Dict[str, Any]:
        """Prepare incident data for BigQuery insertion"""
        return {
            "id": incident_data["id"],
            "event_type": incident_data["event_type"],
            "sub_category": incident_data["sub_category"],
            "description": incident_data["description"],
            "keywords": incident_data.get("keywords", []),
            "language": incident_data.get("language", "en"),
            "latitude": float(incident_data["latitude"]),
            "longitude": float(incident_data["longitude"]),
            "location_name": incident_data["location_name"],
            "area_category": incident_data["area_category"],
            "ward_number": incident_data["ward_number"],
            "pincode": incident_data["pincode"],
            "timestamp": incident_data["timestamp"],
            "estimated_duration": incident_data.get("estimated_duration"),
            "actual_duration": incident_data.get("actual_duration"),
            "peak_hours": incident_data.get("peak_hours", False),
            "severity_level": incident_data["severity_level"],
            "priority_score": float(incident_data["priority_score"]),
            "impact_radius": float(incident_data.get("impact_radius", 1.0)),
            "source": incident_data["source"],
            "verified": incident_data.get("verified", False),
            "reporter_id": incident_data.get("reporter_id"),
            "verification_count": incident_data.get("verification_count", 0),
            "media_type": incident_data.get("media_type"),
            "media_url": incident_data.get("media_url"),
            "event_status": incident_data.get("event_status", "reported"),
            "assigned_department": incident_data["assigned_department"],
            "resolution_notes": incident_data.get("resolution_notes"),
            "weather_condition": incident_data.get("weather_condition"),
            "traffic_density": incident_data.get("traffic_density"),
            "embedding": [{"value": float(x)} for x in embeddings]
        }
    
    def _insert_to_bigquery(self, rows: List[Dict[str, Any]]):
        """Insert rows into BigQuery tables"""
        # Insert into both embeddings and real-time tables
        for table_id in [self.embeddings_table, self.realtime_table]:
            job = self.bq_client.load_table_from_json(rows, table_id)
            job.result()  # Wait for completion
    
    def _update_firestore(self, incident_data: Dict[str, Any]):
        """Update Firestore for real-time UI updates"""
        doc_ref = self.firestore_client.collection('incidents').document(incident_data["id"])
        
        # Prepare Firestore document
        firestore_data = {
            **incident_data,
            "last_updated": firestore.SERVER_TIMESTAMP,
            "ui_status": "active" if incident_data.get("event_status") in ["reported", "in_progress"] else "resolved"
        }
        
        doc_ref.set(firestore_data, merge=True)
        
        # Update area-wise statistics
        area_ref = self.firestore_client.collection('area_stats').document(incident_data["area_category"])
        area_ref.set({
            "last_incident": firestore.SERVER_TIMESTAMP,
            "incident_count": firestore.Increment(1),
            "priority_sum": firestore.Increment(incident_data.get("priority_score", 0))
        }, merge=True)
    
    def _publish_analytics_events(self, incident_data: Dict[str, Any]):
        """Publish analytics events for real-time dashboards"""
        analytics_events = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "metric_name": "incident_count",
                "metric_value": 1.0,
                "dimensions": {
                    "event_type": incident_data["event_type"],
                    "area_category": incident_data["area_category"],
                    "severity_level": incident_data["severity_level"]
                }
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "metric_name": "priority_score",
                "metric_value": float(incident_data.get("priority_score", 0)),
                "dimensions": {
                    "ward_number": incident_data["ward_number"],
                    "assigned_department": incident_data["assigned_department"]
                }
            }
        ]
        
        for event in analytics_events:
            event_data = json.dumps(event).encode('utf-8')
            self.publisher.publish(self.analytics_topic, event_data)
    
    def _send_notifications(self, incident_data: Dict[str, Any]):
        """Send notifications for high-priority incidents"""
        notification_data = {
            "type": "high_priority_incident",
            "incident_id": incident_data["id"],
            "title": f"High Priority: {incident_data['event_type']} in {incident_data['area_category']}",
            "message": incident_data["description"][:200],
            "priority_score": incident_data.get("priority_score", 0),
            "location": incident_data["location_name"],
            "departments": [incident_data["assigned_department"]],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        notification_json = json.dumps(notification_data).encode('utf-8')
        self.publisher.publish(self.notification_topic, notification_json)
    
    def start_streaming_processor(self):
        """Start the streaming processor"""
        logger.info("Starting real-time incident processor...")
        
        flow_control = pubsub_v1.types.FlowControl(max_messages=100)
        
        streaming_pull_future = self.subscriber.subscribe(
            self.incident_subscription,
            callback=self.process_incident_stream,
            flow_control=flow_control
        )
        
        logger.info(f"Listening for messages on {self.incident_subscription}...")
        
        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            logger.info("Streaming processor stopped.")

class BulkDataLoader:
    """Load bulk historical data (10k+ incidents) efficiently"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.processor = RealTimeIncidentProcessor(project_id)
        self.batch_size = 100
    
    def load_historical_data(self, data_file: str):
        """Load historical incident data in batches"""
        logger.info(f"Loading historical data from {data_file}")
        
        with open(data_file, 'r') as f:
            incidents = json.load(f)
        
        # Process in batches
        total_batches = len(incidents) // self.batch_size + 1
        
        for i in range(0, len(incidents), self.batch_size):
            batch = incidents[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} incidents)")
            
            # Process batch with embeddings
            self._process_batch(batch)
            
        logger.info(f"Successfully loaded {len(incidents)} historical incidents")
    
    def _process_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of incidents"""
        rows = []
        
        for incident in batch:
            # Generate embeddings
            embedding_text = f"{incident['description']} {' '.join(incident.get('keywords', []))}"
            embeddings = self.processor.embedding_model.get_embeddings([embedding_text])[0].values
            
            # Prepare BigQuery row
            row = self.processor._prepare_bigquery_row(incident, embeddings)
            rows.append(row)
        
        # Bulk insert to BigQuery
        self.processor._insert_to_bigquery(rows)
        
        # Update Firestore for recent incidents (last 7 days)
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        for incident in batch:
            incident_time = datetime.fromisoformat(incident["timestamp"].replace('Z', '+00:00'))
            if incident_time > recent_cutoff:
                self.processor._update_firestore(incident)

if __name__ == "__main__":
    import sys
    
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        logger.error("PROJECT_ID environment variable not set")
        sys.exit(1)
    
    if len(sys.argv) > 1 and sys.argv[1] == "load_historical":
        # Load historical data
        data_file = sys.argv[2] if len(sys.argv) > 2 else "historical_incidents.json"
        loader = BulkDataLoader(project_id)
        loader.load_historical_data(data_file)
    else:
        # Start real-time processor
        processor = RealTimeIncidentProcessor(project_id)
        processor.start_streaming_processor()
