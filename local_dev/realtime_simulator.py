import json
import time
import random
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from queue import Queue, Empty
import asyncio
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LocalIncidentDatabase:
    """Local SQLite database for storing incidents during simulation"""
    
    def __init__(self, db_path: str = "local_dev/local_incidents.db"):
        self.db_path = db_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize local database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create incidents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                event_type TEXT,
                sub_category TEXT,
                description TEXT,
                keywords TEXT,
                latitude REAL,
                longitude REAL,
                location_name TEXT,
                area_category TEXT,
                ward_number INTEGER,
                severity_level TEXT,
                priority_score REAL,
                assigned_department TEXT,
                event_status TEXT,
                timestamp TEXT,
                processed_at TEXT
            )
        ''')
        
        # Create agent_activities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                incident_id TEXT,
                task_type TEXT,
                status TEXT,
                details TEXT,
                timestamp TEXT
            )
        ''')
        
        # Create notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT,
                notification_type TEXT,
                title TEXT,
                message TEXT,
                priority_score REAL,
                departments TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_incident(self, incident: Dict[str, Any]):
        """Insert incident into local database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO incidents 
            (id, event_type, sub_category, description, keywords, latitude, longitude,
             location_name, area_category, ward_number, severity_level, priority_score,
             assigned_department, event_status, timestamp, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            incident['id'], incident['event_type'], incident['sub_category'],
            incident['description'], json.dumps(incident.get('keywords', [])),
            incident['latitude'], incident['longitude'], incident['location_name'],
            incident['area_category'], incident['ward_number'], incident['severity_level'],
            incident['priority_score'], incident['assigned_department'],
            incident.get('event_status', 'reported'), incident['timestamp'],
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def log_agent_activity(self, agent_name: str, incident_id: str, task_type: str, 
                          status: str, details: Dict[str, Any]):
        """Log agent activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO agent_activities 
            (agent_name, incident_id, task_type, status, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (agent_name, incident_id, task_type, status, json.dumps(details), 
              datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
    
    def log_notification(self, incident_id: str, notification_type: str, title: str,
                        message: str, priority_score: float, departments: List[str]):
        """Log notification"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications 
            (incident_id, notification_type, title, message, priority_score, departments, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (incident_id, notification_type, title, message, priority_score,
              json.dumps(departments), datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_recent_incidents(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent incidents"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        cursor.execute('''
            SELECT * FROM incidents 
            WHERE processed_at > ? 
            ORDER BY processed_at DESC
        ''', (cutoff_time,))
        
        columns = [desc[0] for desc in cursor.description]
        incidents = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return incidents

class MockAIAgent:
    """Mock AI agent for local testing"""
    
    def __init__(self, agent_name: str, db: LocalIncidentDatabase):
        self.agent_name = agent_name
        self.db = db
        self.processing_delay = random.uniform(1, 3)  # Simulate processing time
    
    def process_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Process incident with mock AI logic"""
        time.sleep(self.processing_delay)  # Simulate processing time
        
        incident_id = incident['id']
        priority_score = incident.get('priority_score', 0)
        event_type = incident['event_type']
        
        if self.agent_name == "notification_agent":
            return self._mock_notification_processing(incident)
        elif self.agent_name == "trend_analysis_agent":
            return self._mock_trend_analysis(incident)
        elif self.agent_name == "resource_allocation_agent":
            return self._mock_resource_allocation(incident)
        elif self.agent_name == "news_insights_agent":
            return self._mock_news_insights(incident)
        
        return {"status": "processed", "agent": self.agent_name}
    
    def _mock_notification_processing(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Mock notification agent processing"""
        priority_score = incident.get('priority_score', 0)
        
        if priority_score >= 8.0:
            # Emergency blast
            notification_type = "emergency_blast"
            title = f"🚨 EMERGENCY: {incident['event_type']} in {incident['area_category']}"
            message = f"High priority incident reported: {incident['description'][:100]}..."
            departments = [incident['assigned_department'], "Emergency Services"]
            
            self.db.log_notification(
                incident['id'], notification_type, title, message, 
                priority_score, departments
            )
            
            logger.warning(f"🚨 EMERGENCY BLAST: {incident['id']} - {title}")
            
        elif priority_score >= 7.0:
            # Department alert
            notification_type = "department_alert"
            title = f"⚠️  HIGH PRIORITY: {incident['event_type']}"
            message = f"Attention required: {incident['description'][:100]}..."
            departments = [incident['assigned_department']]
            
            self.db.log_notification(
                incident['id'], notification_type, title, message,
                priority_score, departments
            )
            
            logger.warning(f"⚠️  DEPT ALERT: {incident['id']} - {title}")
        
        self.db.log_agent_activity(
            self.agent_name, incident['id'], "notification_processing",
            "completed", {"priority_score": priority_score, "notifications_sent": 1}
        )
        
        return {"status": "completed", "notifications_sent": 1}
    
    def _mock_trend_analysis(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Mock trend analysis agent processing"""
        event_type = incident['event_type']
        area = incident['area_category']
        
        # Mock trend insights
        trends = {
            "traffic_accident": f"Traffic accidents in {area} increased 15% this week",
            "pothole": f"Pothole reports in {area} correlate with recent rainfall",
            "power_outage": f"Power outages in {area} show peak during evening hours",
            "water_supply": f"Water supply issues in {area} require infrastructure upgrade"
        }
        
        insight = trends.get(event_type, f"Monitoring {event_type} patterns in {area}")
        
        logger.info(f"📈 TREND ANALYSIS: {incident['id']} - {insight}")
        
        self.db.log_agent_activity(
            self.agent_name, incident['id'], "trend_analysis",
            "completed", {"insight": insight, "event_type": event_type}
        )
        
        return {"status": "completed", "insight": insight}
    
    def _mock_resource_allocation(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Mock resource allocation agent processing"""
        severity = incident['severity_level']
        department = incident['assigned_department']
        
        # Mock resource allocation logic
        resource_plans = {
            "high": {"personnel": 5, "vehicles": 2, "response_time": "15 minutes"},
            "medium": {"personnel": 3, "vehicles": 1, "response_time": "30 minutes"},
            "low": {"personnel": 2, "vehicles": 1, "response_time": "60 minutes"}
        }
        
        allocation = resource_plans.get(severity, resource_plans["medium"])
        
        logger.info(f"🚛 RESOURCE ALLOCATION: {incident['id']} - {allocation}")
        
        self.db.log_agent_activity(
            self.agent_name, incident['id'], "resource_allocation",
            "completed", {"allocation": allocation, "department": department}
        )
        
        return {"status": "completed", "allocation": allocation}
    
    def _mock_news_insights(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Mock news insights agent processing"""
        event_type = incident['event_type']
        priority = incident.get('priority_score', 0)
        
        if priority >= 8.0:
            news_impact = "HIGH - Requires immediate public communication"
        elif priority >= 6.0:
            news_impact = "MEDIUM - Monitor for public interest"
        else:
            news_impact = "LOW - Routine incident logging"
        
        logger.info(f"📰 NEWS INSIGHTS: {incident['id']} - {news_impact}")
        
        self.db.log_agent_activity(
            self.agent_name, incident['id'], "news_insights",
            "completed", {"news_impact": news_impact, "priority": priority}
        )
        
        return {"status": "completed", "news_impact": news_impact}

class LocalIncidentSimulator:
    """Local incident simulator that feeds incidents at realistic intervals"""
    
    def __init__(self, dataset_file: str, incidents_per_batch: int = 7, 
                 batch_interval: int = 20):
        self.dataset_file = dataset_file
        self.incidents_per_batch = incidents_per_batch
        self.batch_interval = batch_interval
        self.db = LocalIncidentDatabase()
        self.incident_queue = Queue()
        self.running = False
        
        # Initialize agents
        self.agents = {
            "notification_agent": MockAIAgent("notification_agent", self.db),
            "trend_analysis_agent": MockAIAgent("trend_analysis_agent", self.db),
            "resource_allocation_agent": MockAIAgent("resource_allocation_agent", self.db),
            "news_insights_agent": MockAIAgent("news_insights_agent", self.db)
        }
        
        # Load dataset
        self.load_dataset()
        
        # Statistics
        self.stats = {
            "incidents_processed": 0,
            "high_priority_incidents": 0,
            "notifications_sent": 0,
            "start_time": None
        }
    
    def load_dataset(self):
        """Load incidents from JSON dataset"""
        try:
            with open(self.dataset_file, 'r') as f:
                self.incidents = json.load(f)
            
            logger.info(f"📚 Loaded {len(self.incidents)} incidents from {self.dataset_file}")
            
            # Shuffle for random feeding
            random.shuffle(self.incidents)
            
        except FileNotFoundError:
            logger.error(f"❌ Dataset file not found: {self.dataset_file}")
            logger.info("💡 Generating sample dataset...")
            self.generate_sample_dataset()
    
    def generate_sample_dataset(self):
        """Generate sample dataset if file not found"""
        from datetime import datetime, timedelta
        
        # Sample incident types and locations
        event_types = ["traffic_accident", "pothole", "power_outage", "water_supply", "construction"]
        locations = [
            {"name": "Koramangala", "lat": 12.9352, "lon": 77.6245, "ward": 150},
            {"name": "Indiranagar", "lat": 12.9784, "lon": 77.6408, "ward": 86},
            {"name": "Whitefield", "lat": 12.9698, "lon": 77.7500, "ward": 84},
            {"name": "Jayanagar", "lat": 12.9279, "lon": 77.5937, "ward": 167},
            {"name": "Marathahalli", "lat": 12.9591, "lon": 77.6974, "ward": 84}
        ]
        
        departments = ["BBMP", "Traffic Police", "BESCOM", "BWSSB", "Fire Department"]
        
        self.incidents = []
        
        for i in range(1000):  # Generate 1000 sample incidents
            event_type = random.choice(event_types)
            location = random.choice(locations)
            
            incident = {
                "id": f"LOCAL_SIM_{str(i+1).zfill(6)}",
                "event_type": event_type,
                "sub_category": f"{event_type}_sub",
                "description": f"Simulated {event_type} incident at {location['name']}",
                "keywords": [event_type, location['name']],
                "latitude": location["lat"] + random.uniform(-0.01, 0.01),
                "longitude": location["lon"] + random.uniform(-0.01, 0.01),
                "location_name": location["name"],
                "area_category": "urban",
                "ward_number": location["ward"],
                "severity_level": random.choice(["low", "medium", "high"]),
                "priority_score": random.uniform(1, 10),
                "assigned_department": random.choice(departments),
                "event_status": "reported",
                "timestamp": (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat()
            }
            
            self.incidents.append(incident)
        
        # Save generated dataset
        with open(self.dataset_file, 'w') as f:
            json.dump(self.incidents, f, indent=2)
        
        logger.info(f"✅ Generated {len(self.incidents)} sample incidents")
    
    def feed_incidents(self):
        """Feed incidents to the queue at specified intervals"""
        incident_index = 0
        
        while self.running and incident_index < len(self.incidents):
            # Select random number of incidents for this batch
            batch_size = random.randint(
                max(1, self.incidents_per_batch - 2),
                self.incidents_per_batch + 3
            )
            
            batch_incidents = []
            for _ in range(min(batch_size, len(self.incidents) - incident_index)):
                if incident_index < len(self.incidents):
                    incident = self.incidents[incident_index].copy()
                    # Update timestamp to current time for realism
                    incident['timestamp'] = datetime.utcnow().isoformat()
                    batch_incidents.append(incident)
                    incident_index += 1
            
            if batch_incidents:
                logger.info(f"🔄 Feeding batch of {len(batch_incidents)} incidents...")
                
                for incident in batch_incidents:
                    self.incident_queue.put(incident)
                
                # Add some randomness to interval
                sleep_time = self.batch_interval + random.uniform(-5, 5)
                time.sleep(max(1, sleep_time))
            
            if incident_index >= len(self.incidents):
                logger.info("📚 All incidents from dataset have been fed")
                break
    
    def process_incidents(self):
        """Process incidents from the queue using agents"""
        with ThreadPoolExecutor(max_workers=4) as executor:
            while self.running:
                try:
                    incident = self.incident_queue.get(timeout=1)
                    
                    # Store incident in local database
                    self.db.insert_incident(incident)
                    
                    # Update statistics
                    self.stats["incidents_processed"] += 1
                    if incident.get("priority_score", 0) >= 8.0:
                        self.stats["high_priority_incidents"] += 1
                    
                    logger.info(f"🔍 Processing incident: {incident['id']} - {incident['event_type']} (Priority: {incident.get('priority_score', 0):.1f})")
                    
                    # Process with agents based on priority
                    priority_score = incident.get("priority_score", 0)
                    
                    # All incidents get basic processing
                    futures = []
                    
                    # High priority incidents get full agent processing
                    if priority_score >= 8.0:
                        logger.warning(f"🚨 HIGH PRIORITY INCIDENT: {incident['id']}")
                        for agent_name, agent in self.agents.items():
                            future = executor.submit(agent.process_incident, incident)
                            futures.append((agent_name, future))
                    
                    # Medium priority gets selective processing
                    elif priority_score >= 6.0:
                        selected_agents = ["notification_agent", "resource_allocation_agent"]
                        for agent_name in selected_agents:
                            future = executor.submit(self.agents[agent_name].process_incident, incident)
                            futures.append((agent_name, future))
                    
                    # Low priority gets minimal processing
                    else:
                        future = executor.submit(self.agents["resource_allocation_agent"].process_incident, incident)
                        futures.append(("resource_allocation_agent", future))
                    
                    # Wait for agent processing to complete
                    for agent_name, future in futures:
                        try:
                            result = future.result(timeout=10)
                            logger.debug(f"✅ {agent_name} completed: {result}")
                        except Exception as e:
                            logger.error(f"❌ {agent_name} failed: {e}")
                    
                    self.incident_queue.task_done()
                    
                except Empty:
                    continue
                except Exception as e:
                    logger.error(f"❌ Error processing incident: {e}")
    
    def print_statistics(self):
        """Print real-time statistics"""
        while self.running:
            time.sleep(30)  # Print stats every 30 seconds
            
            if self.stats["start_time"]:
                elapsed = datetime.utcnow() - self.stats["start_time"]
                elapsed_seconds = elapsed.total_seconds()
                
                rate = self.stats["incidents_processed"] / max(elapsed_seconds, 1) * 60  # per minute
                
                print("\n" + "="*60)
                print("📊 REAL-TIME SIMULATION STATISTICS")
                print("="*60)
                print(f"⏱️  Runtime: {elapsed}")
                print(f"📋 Incidents Processed: {self.stats['incidents_processed']}")
                print(f"🚨 High Priority: {self.stats['high_priority_incidents']}")
                print(f"📈 Processing Rate: {rate:.1f} incidents/minute")
                print(f"📊 Queue Size: {self.incident_queue.qsize()}")
                
                # Recent incidents
                recent_incidents = self.db.get_recent_incidents(hours=1)
                print(f"🕐 Last Hour: {len(recent_incidents)} incidents")
                
                # Agent activity summary
                print("\n🤖 AGENT ACTIVITY:")
                for agent_name in self.agents.keys():
                    print(f"   {agent_name}: Active")
                
                print("="*60)
    
    def start_simulation(self):
        """Start the local incident simulation"""
        logger.info("🚀 Starting Local City Pulse Simulation")
        logger.info(f"📊 Configuration: {self.incidents_per_batch} incidents every {self.batch_interval} seconds")
        
        self.running = True
        self.stats["start_time"] = datetime.utcnow()
        
        # Start threads
        feeder_thread = threading.Thread(target=self.feed_incidents, daemon=True)
        processor_thread = threading.Thread(target=self.process_incidents, daemon=True)
        stats_thread = threading.Thread(target=self.print_statistics, daemon=True)
        
        feeder_thread.start()
        processor_thread.start()
        stats_thread.start()
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Stopping simulation...")
            self.running = False
            
            # Wait for threads to finish
            feeder_thread.join(timeout=5)
            processor_thread.join(timeout=5)
            
            # Final statistics
            print("\n" + "="*60)
            print("📊 FINAL SIMULATION STATISTICS")
            print("="*60)
            print(f"📋 Total Incidents Processed: {self.stats['incidents_processed']}")
            print(f"🚨 High Priority Incidents: {self.stats['high_priority_incidents']}")
            print(f"⏱️  Total Runtime: {datetime.utcnow() - self.stats['start_time']}")
            print("="*60)
            
            logger.info("✅ Simulation completed successfully")

def main():
    """Main function to run the local simulation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Local City Pulse Incident Simulator")
    parser.add_argument("--dataset", default="historical_incidents.json", 
                       help="Path to incidents JSON dataset")
    parser.add_argument("--batch-size", type=int, default=7,
                       help="Number of incidents per batch (default: 7)")
    parser.add_argument("--interval", type=int, default=20,
                       help="Interval between batches in seconds (default: 20)")
    parser.add_argument("--generate-sample", action="store_true",
                       help="Generate sample dataset if file not found")
    
    args = parser.parse_args()
    
    # Create simulator
    simulator = LocalIncidentSimulator(
        dataset_file=args.dataset,
        incidents_per_batch=args.batch_size,
        batch_interval=args.interval
    )
    
    # Start simulation
    simulator.start_simulation()

if __name__ == "__main__":
    main()
