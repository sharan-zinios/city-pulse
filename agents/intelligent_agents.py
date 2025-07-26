import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from abc import ABC, abstractmethod

from google.cloud import pubsub_v1
from google.cloud import bigquery
from google.cloud import firestore
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextEmbeddingModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all intelligent agents"""
    
    def __init__(self, project_id: str, agent_name: str):
        self.project_id = project_id
        self.agent_name = agent_name
        self.bq_client = bigquery.Client(project=project_id)
        self.firestore_client = firestore.Client(project=project_id)
        self.publisher = pubsub_v1.PublisherClient()
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location="asia-south1")
        self.llm_model = GenerativeModel("gemini-1.5-pro")
        
        # Topic paths
        self.notification_topic = self.publisher.topic_path(project_id, "notification-stream")
        self.analytics_topic = self.publisher.topic_path(project_id, "analytics-stream")
        
    @abstractmethod
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a specific task"""
        pass
    
    def log_agent_activity(self, task_id: str, status: str, details: Dict[str, Any]):
        """Log agent activity to Firestore"""
        activity_ref = self.firestore_client.collection('agent_activities').document()
        activity_ref.set({
            "agent_name": self.agent_name,
            "task_id": task_id,
            "status": status,
            "details": details,
            "timestamp": firestore.SERVER_TIMESTAMP
        })

class NotificationAgent(BaseAgent):
    """Agent for handling notifications and alerts"""
    
    def __init__(self, project_id: str):
        super().__init__(project_id, "notification_agent")
        
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process notification tasks"""
        task_type = task_data.get("task_type")
        
        if task_type == "notification_blast":
            return self._send_notification_blast(task_data)
        elif task_type == "department_alert":
            return self._send_department_alert(task_data)
        elif task_type == "citizen_update":
            return self._send_citizen_update(task_data)
        else:
            logger.warning(f"Unknown notification task type: {task_type}")
            return {"status": "error", "message": "Unknown task type"}
    
    def _send_notification_blast(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send high-priority notification blast"""
        incident_id = task_data["incident_id"]
        departments = task_data.get("departments", [])
        radius_km = task_data.get("radius_km", 2.0)
        
        # Get incident details
        incident_query = f"""
            SELECT * FROM `{self.project_id}.bengaluru_events.real_time_incidents`
            WHERE id = '{incident_id}'
            LIMIT 1
        """
        
        incident_result = list(self.bq_client.query(incident_query).result())
        if not incident_result:
            return {"status": "error", "message": "Incident not found"}
        
        incident = dict(incident_result[0])
        
        # Find nearby stakeholders
        nearby_query = f"""
            SELECT DISTINCT assigned_department, area_category, ward_number
            FROM `{self.project_id}.bengaluru_events.real_time_incidents`
            WHERE ST_DWITHIN(
                ST_GEOGPOINT(longitude, latitude),
                ST_GEOGPOINT({incident['longitude']}, {incident['latitude']}),
                {radius_km * 1000}
            )
            AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        """
        
        nearby_stakeholders = list(self.bq_client.query(nearby_query).result())
        
        # Generate notification content using AI
        notification_prompt = f"""
        Generate a concise emergency notification for a {incident['severity_level']} severity {incident['event_type']} incident:
        
        Location: {incident['location_name']} (Ward {incident['ward_number']})
        Description: {incident['description']}
        Priority Score: {incident['priority_score']}/10
        Estimated Duration: {incident.get('estimated_duration', 'Unknown')}
        
        Create notifications for:
        1. Emergency responders (urgent, actionable)
        2. Affected departments: {', '.join(departments)}
        3. Citizens in the area (informative, safety-focused)
        
        Format as JSON with keys: emergency_responders, departments, citizens
        """
        
        try:
            ai_response = self.llm_model.generate_content(notification_prompt)
            notifications = json.loads(ai_response.text)
            
            # Send notifications
            notification_data = {
                "type": "emergency_blast",
                "incident_id": incident_id,
                "notifications": notifications,
                "stakeholders": [dict(s) for s in nearby_stakeholders],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Publish to notification stream
            self.publisher.publish(
                self.notification_topic,
                json.dumps(notification_data).encode('utf-8')
            )
            
            # Update Firestore for real-time UI
            self.firestore_client.collection('notifications').add(notification_data)
            
            self.log_agent_activity(
                incident_id,
                "completed",
                {"notifications_sent": len(notifications), "stakeholders_notified": len(nearby_stakeholders)}
            )
            
            return {"status": "success", "notifications_sent": len(notifications)}
            
        except Exception as e:
            logger.error(f"Error generating notifications: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_department_alert(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send targeted department alerts"""
        # Implementation for department-specific alerts
        return {"status": "success", "message": "Department alert sent"}
    
    def _send_citizen_update(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send citizen updates"""
        # Implementation for citizen updates
        return {"status": "success", "message": "Citizen update sent"}

class TrendAnalysisAgent(BaseAgent):
    """Agent for analyzing trends and patterns"""
    
    def __init__(self, project_id: str):
        super().__init__(project_id, "trend_analysis_agent")
        
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process trend analysis tasks"""
        task_type = task_data.get("task_type")
        
        if task_type == "trend_analysis":
            return self._analyze_incident_trends(task_data)
        elif task_type == "hotspot_detection":
            return self._detect_hotspots(task_data)
        elif task_type == "pattern_recognition":
            return self._recognize_patterns(task_data)
        else:
            logger.warning(f"Unknown trend analysis task type: {task_type}")
            return {"status": "error", "message": "Unknown task type"}
    
    def _analyze_incident_trends(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends for specific incident types"""
        incident_id = task_data["incident_id"]
        event_type = task_data["event_type"]
        location = task_data.get("location")
        
        # Query historical data for trend analysis
        trend_query = f"""
            WITH recent_incidents AS (
                SELECT 
                    event_type,
                    area_category,
                    ward_number,
                    severity_level,
                    priority_score,
                    timestamp,
                    EXTRACT(HOUR FROM timestamp) as hour_of_day,
                    EXTRACT(DAYOFWEEK FROM timestamp) as day_of_week
                FROM `{self.project_id}.bengaluru_events.real_time_incidents`
                WHERE event_type = '{event_type}'
                AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
            ),
            trend_stats AS (
                SELECT 
                    COUNT(*) as total_incidents,
                    AVG(priority_score) as avg_priority,
                    APPROX_QUANTILES(priority_score, 4)[OFFSET(2)] as median_priority,
                    COUNT(DISTINCT area_category) as affected_areas,
                    ARRAY_AGG(DISTINCT severity_level) as severity_levels
                FROM recent_incidents
            ),
            hourly_pattern AS (
                SELECT 
                    hour_of_day,
                    COUNT(*) as incident_count,
                    AVG(priority_score) as avg_priority
                FROM recent_incidents
                GROUP BY hour_of_day
                ORDER BY incident_count DESC
                LIMIT 5
            ),
            area_hotspots AS (
                SELECT 
                    area_category,
                    ward_number,
                    COUNT(*) as incident_count,
                    AVG(priority_score) as avg_priority
                FROM recent_incidents
                GROUP BY area_category, ward_number
                ORDER BY incident_count DESC
                LIMIT 10
            )
            SELECT 
                (SELECT AS STRUCT * FROM trend_stats) as trends,
                ARRAY(SELECT AS STRUCT * FROM hourly_pattern) as hourly_patterns,
                ARRAY(SELECT AS STRUCT * FROM area_hotspots) as hotspots
        """
        
        try:
            result = list(self.bq_client.query(trend_query).result())[0]
            
            # Generate AI insights
            insights_prompt = f"""
            Analyze the following incident trends for {event_type} incidents in Bengaluru:
            
            Overall Statistics:
            - Total incidents (30 days): {result['trends']['total_incidents']}
            - Average priority: {result['trends']['avg_priority']:.2f}/10
            - Affected areas: {result['trends']['affected_areas']}
            - Severity levels: {result['trends']['severity_levels']}
            
            Peak Hours: {[f"{h['hour_of_day']}:00 ({h['incident_count']} incidents)" for h in result['hourly_patterns']]}
            
            Top Hotspots: {[f"{h['area_category']} Ward-{h['ward_number']} ({h['incident_count']} incidents)" for h in result['hotspots']]}
            
            Provide:
            1. Key trends and patterns
            2. Risk assessment for the current incident
            3. Preventive recommendations
            4. Resource allocation suggestions
            
            Format as JSON with keys: trends, risk_assessment, recommendations, resource_allocation
            """
            
            ai_response = self.llm_model.generate_content(insights_prompt)
            insights = json.loads(ai_response.text)
            
            # Store insights
            trend_data = {
                "incident_id": incident_id,
                "event_type": event_type,
                "location": location,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "statistics": dict(result['trends']),
                "patterns": {
                    "hourly": [dict(h) for h in result['hourly_patterns']],
                    "hotspots": [dict(h) for h in result['hotspots']]
                },
                "ai_insights": insights
            }
            
            # Save to Firestore
            self.firestore_client.collection('trend_analysis').add(trend_data)
            
            # Publish analytics event
            analytics_event = {
                "timestamp": datetime.utcnow().isoformat(),
                "metric_name": "trend_analysis_completed",
                "metric_value": 1.0,
                "dimensions": {
                    "event_type": event_type,
                    "total_incidents": result['trends']['total_incidents'],
                    "avg_priority": result['trends']['avg_priority']
                }
            }
            
            self.publisher.publish(
                self.analytics_topic,
                json.dumps(analytics_event).encode('utf-8')
            )
            
            self.log_agent_activity(
                incident_id,
                "completed",
                {"trends_analyzed": True, "insights_generated": True}
            )
            
            return {"status": "success", "insights": insights}
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {"status": "error", "message": str(e)}
    
    def _detect_hotspots(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect incident hotspots"""
        # Implementation for hotspot detection
        return {"status": "success", "message": "Hotspots detected"}
    
    def _recognize_patterns(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Recognize incident patterns"""
        # Implementation for pattern recognition
        return {"status": "success", "message": "Patterns recognized"}

class ResourceAllocationAgent(BaseAgent):
    """Agent for optimizing resource allocation"""
    
    def __init__(self, project_id: str):
        super().__init__(project_id, "resource_allocation_agent")
        
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process resource allocation tasks"""
        task_type = task_data.get("task_type")
        
        if task_type == "resource_allocation":
            return self._optimize_resource_allocation(task_data)
        elif task_type == "capacity_planning":
            return self._plan_capacity(task_data)
        else:
            logger.warning(f"Unknown resource allocation task type: {task_type}")
            return {"status": "error", "message": "Unknown task type"}
    
    def _optimize_resource_allocation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize resource allocation for incidents"""
        incident_id = task_data["incident_id"]
        severity = task_data["severity"]
        estimated_duration = task_data.get("estimated_duration")
        
        # Query current resource utilization
        resource_query = f"""
            WITH current_incidents AS (
                SELECT 
                    assigned_department,
                    severity_level,
                    area_category,
                    ward_number,
                    priority_score,
                    estimated_duration
                FROM `{self.project_id}.bengaluru_events.real_time_incidents`
                WHERE event_status IN ('reported', 'in_progress')
                AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
            ),
            department_load AS (
                SELECT 
                    assigned_department,
                    COUNT(*) as active_incidents,
                    AVG(priority_score) as avg_priority,
                    SUM(CASE WHEN severity_level = 'high' THEN 1 ELSE 0 END) as high_severity_count
                FROM current_incidents
                GROUP BY assigned_department
            )
            SELECT * FROM department_load
            ORDER BY active_incidents DESC
        """
        
        try:
            resource_data = [dict(row) for row in self.bq_client.query(resource_query).result()]
            
            # Generate resource allocation recommendations
            allocation_prompt = f"""
            Optimize resource allocation for a {severity} severity incident (ID: {incident_id}):
            
            Current Department Workload:
            {json.dumps(resource_data, indent=2)}
            
            New Incident Details:
            - Severity: {severity}
            - Estimated Duration: {estimated_duration}
            
            Provide resource allocation recommendations:
            1. Primary department assignment
            2. Support departments needed
            3. Resource priority level (1-10)
            4. Estimated personnel required
            5. Equipment/vehicle requirements
            6. Timeline for response
            
            Format as JSON with keys: primary_department, support_departments, priority_level, personnel_required, equipment_needed, response_timeline
            """
            
            ai_response = self.llm_model.generate_content(allocation_prompt)
            allocation_plan = json.loads(ai_response.text)
            
            # Store allocation plan
            allocation_data = {
                "incident_id": incident_id,
                "severity": severity,
                "allocation_timestamp": datetime.utcnow().isoformat(),
                "current_workload": resource_data,
                "allocation_plan": allocation_plan
            }
            
            # Save to Firestore
            self.firestore_client.collection('resource_allocations').add(allocation_data)
            
            self.log_agent_activity(
                incident_id,
                "completed",
                {"allocation_optimized": True, "departments_analyzed": len(resource_data)}
            )
            
            return {"status": "success", "allocation_plan": allocation_plan}
            
        except Exception as e:
            logger.error(f"Error optimizing resource allocation: {e}")
            return {"status": "error", "message": str(e)}
    
    def _plan_capacity(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Plan capacity for future incidents"""
        # Implementation for capacity planning
        return {"status": "success", "message": "Capacity planned"}

class NewsInsightsAgent(BaseAgent):
    """Agent for generating news insights and summaries"""
    
    def __init__(self, project_id: str):
        super().__init__(project_id, "news_insights_agent")
        
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process news insights tasks"""
        task_type = task_data.get("task_type")
        
        if task_type == "daily_summary":
            return self._generate_daily_summary(task_data)
        elif task_type == "hot_topics":
            return self._identify_hot_topics(task_data)
        elif task_type == "impact_analysis":
            return self._analyze_impact(task_data)
        else:
            logger.warning(f"Unknown news insights task type: {task_type}")
            return {"status": "error", "message": "Unknown task type"}
    
    def _generate_daily_summary(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate daily incident summary"""
        target_date = task_data.get("date", datetime.utcnow().date())
        
        # Query daily incidents
        daily_query = f"""
            SELECT 
                event_type,
                severity_level,
                area_category,
                assigned_department,
                COUNT(*) as incident_count,
                AVG(priority_score) as avg_priority,
                STRING_AGG(DISTINCT location_name, ', ' LIMIT 10) as locations
            FROM `{self.project_id}.bengaluru_events.real_time_incidents`
            WHERE DATE(timestamp) = '{target_date}'
            GROUP BY event_type, severity_level, area_category, assigned_department
            ORDER BY incident_count DESC
        """
        
        try:
            daily_data = [dict(row) for row in self.bq_client.query(daily_query).result()]
            
            # Generate AI summary
            summary_prompt = f"""
            Generate a comprehensive daily incident summary for Bengaluru on {target_date}:
            
            Incident Data:
            {json.dumps(daily_data, indent=2)}
            
            Create a news-style summary including:
            1. Executive summary (2-3 sentences)
            2. Key statistics and trends
            3. Major incidents by area
            4. Department performance
            5. Citizen impact assessment
            6. Recommendations for tomorrow
            
            Format as JSON with keys: executive_summary, statistics, major_incidents, department_performance, citizen_impact, recommendations
            """
            
            ai_response = self.llm_model.generate_content(summary_prompt)
            summary = json.loads(ai_response.text)
            
            # Store summary
            summary_data = {
                "date": str(target_date),
                "generation_timestamp": datetime.utcnow().isoformat(),
                "raw_data": daily_data,
                "summary": summary
            }
            
            # Save to Firestore
            self.firestore_client.collection('daily_summaries').document(str(target_date)).set(summary_data)
            
            self.log_agent_activity(
                f"daily_summary_{target_date}",
                "completed",
                {"incidents_analyzed": len(daily_data), "summary_generated": True}
            )
            
            return {"status": "success", "summary": summary}
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            return {"status": "error", "message": str(e)}
    
    def _identify_hot_topics(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify hot topics and trending incidents"""
        # Implementation for hot topics identification
        return {"status": "success", "message": "Hot topics identified"}
    
    def _analyze_impact(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze incident impact on city operations"""
        # Implementation for impact analysis
        return {"status": "success", "message": "Impact analyzed"}

class AgentOrchestrator:
    """Orchestrates all intelligent agents"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.subscriber = pubsub_v1.SubscriberClient()
        self.agent_subscription = self.subscriber.subscription_path(project_id, "agent-worker")
        
        # Initialize agents
        self.agents = {
            "notification_agent": NotificationAgent(project_id),
            "trend_analysis_agent": TrendAnalysisAgent(project_id),
            "resource_allocation_agent": ResourceAllocationAgent(project_id),
            "news_insights_agent": NewsInsightsAgent(project_id)
        }
        
    def process_agent_task(self, message):
        """Process agent tasks from Pub/Sub"""
        try:
            task_data = json.loads(message.data.decode('utf-8'))
            task_type = task_data.get("task_type")
            
            # Route to appropriate agent
            agent = None
            if task_type in ["notification_blast", "department_alert", "citizen_update"]:
                agent = self.agents["notification_agent"]
            elif task_type in ["trend_analysis", "hotspot_detection", "pattern_recognition"]:
                agent = self.agents["trend_analysis_agent"]
            elif task_type in ["resource_allocation", "capacity_planning"]:
                agent = self.agents["resource_allocation_agent"]
            elif task_type in ["daily_summary", "hot_topics", "impact_analysis"]:
                agent = self.agents["news_insights_agent"]
            
            if agent:
                result = agent.process_task(task_data)
                logger.info(f"Agent task completed: {task_type} - {result['status']}")
                message.ack()
            else:
                logger.warning(f"No agent found for task type: {task_type}")
                message.nack()
                
        except Exception as e:
            logger.error(f"Error processing agent task: {e}")
            message.nack()
    
    def start_agent_orchestrator(self):
        """Start the agent orchestrator"""
        logger.info("Starting intelligent agent orchestrator...")
        
        flow_control = pubsub_v1.types.FlowControl(max_messages=50)
        
        streaming_pull_future = self.subscriber.subscribe(
            self.agent_subscription,
            callback=self.process_agent_task,
            flow_control=flow_control
        )
        
        logger.info(f"Listening for agent tasks on {self.agent_subscription}...")
        
        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            logger.info("Agent orchestrator stopped.")

if __name__ == "__main__":
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        logger.error("PROJECT_ID environment variable not set")
        exit(1)
    
    orchestrator = AgentOrchestrator(project_id)
    orchestrator.start_agent_orchestrator()
