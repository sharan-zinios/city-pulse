import os
import json
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from google.cloud import bigquery
from neo4j import GraphDatabase
from vertexai.language_models import ChatModel
import vertexai

# Initialize Vertex AI
vertexai.init(project=os.getenv("PROJECT_ID"), location="asia-south1")

bq = bigquery.Client()
driver = GraphDatabase.driver("bolt://memgraph-service:7687", auth=("", ""))
chat = ChatModel.from_pretrained("gemini-1.5-flash-001").start_chat()

app = FastAPI(title="Bengaluru City Pulse API", version="2.0.0")

class IncidentQuery(BaseModel):
    question: str
    coordinates: List[float]  # [lat, lon]
    radius_km: int = 5
    event_types: Optional[List[str]] = None
    severity_levels: Optional[List[str]] = None
    time_range_hours: Optional[int] = 24

class IncidentFilter(BaseModel):
    event_types: Optional[List[str]] = None
    severity_levels: Optional[List[str]] = None
    area_categories: Optional[List[str]] = None
    ward_numbers: Optional[List[int]] = None
    verified_only: bool = False
    peak_hours_only: bool = False

@app.get("/")
def read_root():
    return {
        "message": "Bengaluru City Pulse API - Incident Management System",
        "version": "2.0.0",
        "features": ["Vector Search", "Graph Analysis", "AI Insights", "Real-time Incident Tracking"]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "bengaluru-city-pulse", "version": "2.0.0"}

@app.post("/incidents/search")
def search_incidents(query: IncidentQuery):
    """Advanced incident search with vector similarity and spatial filtering"""
    try:
        lat, lon = query.coordinates
        
        # Build dynamic WHERE clause
        where_conditions = [
            f"ST_DISTANCE(ST_GEOGPOINT(coordinates[OFFSET(1)], coordinates[OFFSET(0)]), ST_GEOGPOINT({lon}, {lat})) <= {query.radius_km}*1000"
        ]
        
        if query.event_types:
            event_types_str = "', '".join(query.event_types)
            where_conditions.append(f"event_type IN ('{event_types_str}')")
        
        if query.severity_levels:
            severity_str = "', '".join(query.severity_levels)
            where_conditions.append(f"severity_level IN ('{severity_str}')")
        
        if query.time_range_hours:
            where_conditions.append(f"timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {query.time_range_hours} HOUR)")
        
        where_clause = " AND ".join(where_conditions)
        
        # Vector search query
        sql = f"""
            SELECT 
                id, event_type, sub_category, description, location_name, 
                area_category, severity_level, priority_score, event_status,
                coordinates, timestamp, impact_radius, assigned_department,
                verification_count, verified, weather_condition, traffic_density
            FROM `{os.getenv('PROJECT_ID')}.bengaluru_events.embeddings`
            WHERE {where_clause}
            ORDER BY 
                COSINE_DISTANCE(embedding, ML.GENERATE_EMBEDDING(MODEL `{os.getenv('PROJECT_ID')}.bengaluru_events.text_embedding_model`, '{query.question}')),
                priority_score DESC,
                timestamp DESC
            LIMIT 20
        """
        
        results = [dict(row) for row in bq.query(sql).result()]
        
        return {
            "query": query.question,
            "location": {"lat": lat, "lon": lon, "radius_km": query.radius_km},
            "results_count": len(results),
            "incidents": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.post("/incidents/analyze")
def analyze_incidents(query: IncidentQuery):
    """AI-powered incident analysis with insights and predictions"""
    try:
        lat, lon = query.coordinates
        
        # 1. Get recent incidents (vector search)
        vector_sql = f"""
            SELECT 
                id, event_type, sub_category, description, location_name,
                severity_level, priority_score, event_status, timestamp,
                coordinates, impact_radius, verification_count, verified
            FROM `{os.getenv('PROJECT_ID')}.bengaluru_events.embeddings`
            WHERE ST_DISTANCE(ST_GEOGPOINT(coordinates[OFFSET(1)], coordinates[OFFSET(0)]), ST_GEOGPOINT({lon}, {lat})) <= {query.radius_km}*1000
            AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
            ORDER BY priority_score DESC, timestamp DESC
            LIMIT 15
        """
        vector_results = [dict(row) for row in bq.query(vector_sql).result()]
        
        # 2. Graph analysis (spatial relationships)
        with driver.session() as s:
            graph_results = s.run("""
                MATCH (i:Incident)-[:LOCATED_AT]->(l:Location)
                WHERE distance(point({longitude:l.lon, latitude:l.lat}),
                               point({longitude:$lon, latitude:$lat})) < $r*1000
                RETURN i.id, i.event_type, i.severity_level, i.status, 
                       l.name as location, i.timestamp
                ORDER BY i.priority_score DESC
                LIMIT 10
            """, lon=lon, lat=lat, r=query.radius_km).data()
        
        # 3. Generate AI insights
        context = {
            "query_location": {"lat": lat, "lon": lon},
            "radius_km": query.radius_km,
            "recent_incidents": vector_results,
            "spatial_analysis": graph_results,
            "total_incidents": len(vector_results),
            "high_priority_count": len([i for i in vector_results if i.get('priority_score', 0) > 0.7]),
            "event_types": list(set(i.get('event_type', '') for i in vector_results))
        }
        
        # Create detailed prompt for AI analysis
        analysis_prompt = f"""
        Analyze the following incident data for Bengaluru city:
        
        Location: {lat}, {lon} (radius: {query.radius_km}km)
        Question: {query.question}
        
        Recent Incidents ({len(vector_results)}):
        {json.dumps(vector_results[:5], indent=2)}
        
        Provide insights on:
        1. Current situation assessment
        2. Risk patterns and trends
        3. Recommended actions
        4. Predictions for next 24-48 hours
        
        Focus on public safety, traffic impact, and resource allocation.
        """
        
        ai_response = chat.send_message(analysis_prompt)
        
        return {
            "query": query.question,
            "location": {"lat": lat, "lon": lon, "radius_km": query.radius_km},
            "analysis": {
                "ai_insights": ai_response.text,
                "incident_summary": {
                    "total_incidents": len(vector_results),
                    "high_priority": len([i for i in vector_results if i.get('priority_score', 0) > 0.7]),
                    "event_types": list(set(i.get('event_type', '') for i in vector_results)),
                    "average_priority": sum(i.get('priority_score', 0) for i in vector_results) / len(vector_results) if vector_results else 0
                },
                "recent_incidents": vector_results[:10],
                "spatial_relationships": graph_results
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@app.get("/incidents/stats")
def get_incident_stats(
    ward_number: Optional[int] = Query(None),
    area_category: Optional[str] = Query(None),
    hours: int = Query(24, description="Time range in hours")
):
    """Get incident statistics for dashboards"""
    try:
        where_conditions = [
            f"timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)"
        ]
        
        if ward_number:
            where_conditions.append(f"ward_number = {ward_number}")
        
        if area_category:
            where_conditions.append(f"area_category = '{area_category}'")
        
        where_clause = " AND ".join(where_conditions)
        
        stats_sql = f"""
            SELECT 
                event_type,
                severity_level,
                area_category,
                COUNT(*) as incident_count,
                AVG(priority_score) as avg_priority,
                AVG(verification_count) as avg_verification,
                SUM(CASE WHEN event_status = 'resolved' THEN 1 ELSE 0 END) as resolved_count
            FROM `{os.getenv('PROJECT_ID')}.bengaluru_events.embeddings`
            WHERE {where_clause}
            GROUP BY event_type, severity_level, area_category
            ORDER BY incident_count DESC
        """
        
        stats = [dict(row) for row in bq.query(stats_sql).result()]
        
        return {
            "time_range_hours": hours,
            "filters": {"ward_number": ward_number, "area_category": area_category},
            "statistics": stats,
            "summary": {
                "total_incidents": sum(s['incident_count'] for s in stats),
                "resolved_incidents": sum(s['resolved_count'] for s in stats),
                "avg_priority": sum(s['avg_priority'] * s['incident_count'] for s in stats) / sum(s['incident_count'] for s in stats) if stats else 0
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@app.get("/incidents/departments/{department}")
def get_department_incidents(department: str):
    """Get incidents assigned to a specific department"""
    try:
        sql = f"""
            SELECT 
                id, event_type, sub_category, description, location_name,
                severity_level, priority_score, event_status, timestamp,
                estimated_duration, actual_duration, resolution_notes
            FROM `{os.getenv('PROJECT_ID')}.bengaluru_events.embeddings`
            WHERE assigned_department = '{department}'
            AND event_status IN ('reported', 'verified', 'in_progress')
            ORDER BY priority_score DESC, timestamp DESC
            LIMIT 50
        """
        
        incidents = [dict(row) for row in bq.query(sql).result()]
        
        return {
            "department": department,
            "active_incidents": len(incidents),
            "incidents": incidents
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Department query error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
