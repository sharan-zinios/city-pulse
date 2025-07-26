#!/usr/bin/env python3
"""
Local development server for Bengaluru Graph-RAG API
This runs a simplified version without GCP dependencies for testing
"""
import os
import json
import random
import uuid
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Mock data for local testing
MOCK_EVENTS = [
    {
        "id": str(uuid.uuid4()),
        "type": "concert",
        "lat": 12.9716,
        "lon": 77.5946,
        "place": "MG Road",
        "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(),
        "text": "Loud crowd gathering for music festival"
    },
    {
        "id": str(uuid.uuid4()),
        "type": "tech_meetup",
        "lat": 12.9352,
        "lon": 77.6245,
        "place": "Koramangala",
        "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "text": "Peaceful tech community meetup"
    },
    {
        "id": str(uuid.uuid4()),
        "type": "food_fair",
        "lat": 12.9279,
        "lon": 77.6271,
        "place": "Indiranagar",
        "timestamp": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
        "text": "Massive food festival with local vendors"
    },
    {
        "id": str(uuid.uuid4()),
        "type": "accident",
        "lat": 12.9698,
        "lon": 77.5986,
        "place": "MG Road",
        "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
        "text": "Traffic congestion due to minor accident"
    }
]

app = FastAPI(title="Bengaluru Graph-RAG API (Local Dev)", version="1.0.0-dev")

class QueryRequest(BaseModel):
    question: str
    lat: float
    lon: float
    radius_km: int = 5

def calculate_distance(lat1, lon1, lat2, lon2):
    """Simple distance calculation (not geodesic, but good enough for testing)"""
    return ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5

def mock_vector_search(question, lat, lon, radius_km):
    """Mock vector search using keyword matching"""
    results = []
    keywords = question.lower().split()
    
    for event in MOCK_EVENTS:
        # Distance filter
        distance = calculate_distance(lat, lon, event["lat"], event["lon"])
        if distance > radius_km * 0.01:  # Rough conversion
            continue
            
        # Simple keyword matching for "semantic" search
        text_lower = event["text"].lower()
        score = sum(1 for keyword in keywords if keyword in text_lower or keyword in event["type"])
        
        if score > 0:
            results.append({
                "event_id": event["id"],
                "text": event["text"],
                "event_type": event["type"],
                "place": event["place"],
                "timestamp": event["timestamp"],
                "score": score
            })
    
    return sorted(results, key=lambda x: x["score"], reverse=True)[:5]

def mock_graph_search(lat, lon, radius_km):
    """Mock graph traversal"""
    results = []
    
    for event in MOCK_EVENTS:
        distance = calculate_distance(lat, lon, event["lat"], event["lon"])
        if distance <= radius_km * 0.01:  # Rough conversion
            results.append({
                "id": event["id"],
                "type": event["type"],
                "timestamp": event["timestamp"],
                "place": event["place"]
            })
    
    return results

def mock_llm_response(context, question):
    """Mock LLM response based on context"""
    vector_events = context.get("vector_events", [])
    graph_events = context.get("graph_events", [])
    
    if not vector_events and not graph_events:
        return "No relevant events found in the specified area."
    
    # Simple rule-based responses
    event_types = [e.get("event_type", e.get("type", "")) for e in vector_events + graph_events]
    places = list(set([e.get("place", "") for e in vector_events + graph_events]))
    
    if "concert" in event_types or "music" in question.lower():
        return f"Based on recent data, there's a music event near {places[0] if places else 'the area'}. Concert activity typically peaks on weekends in this location."
    
    elif "traffic" in question.lower() or "accident" in event_types:
        return f"Traffic situation in {places[0] if places else 'the area'}: Recent reports show some congestion. Consider alternative routes during peak hours."
    
    elif "food" in question.lower() or "food_fair" in event_types:
        return f"Food events are active in {places[0] if places else 'the area'}. Local food festivals typically run for 2-3 days with peak activity in evenings."
    
    elif "tech" in question.lower() or "tech_meetup" in event_types:
        return f"Tech community is active in {places[0] if places else 'the area'}. Meetups usually happen on weekdays, with networking sessions extending into evenings."
    
    else:
        return f"Found {len(vector_events + graph_events)} events in the area. Activity levels suggest moderate engagement with mixed event types."

@app.get("/")
def read_root():
    return {
        "message": "Bengaluru Graph-RAG API (Local Development Mode)",
        "note": "This is a mock version for local testing. Deploy to GCP for full functionality.",
        "mock_data_events": len(MOCK_EVENTS)
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "bengaluru-graphrag-local", "mode": "development"}

@app.post("/ask")
def ask(request: QueryRequest):
    try:
        # 1. Mock vector search
        vector_results = mock_vector_search(request.question, request.lat, request.lon, request.radius_km)
        
        # 2. Mock graph traversal
        graph_results = mock_graph_search(request.lat, request.lon, request.radius_km)
        
        # 3. Mock LLM response
        context = {"vector_events": vector_results, "graph_events": graph_results}
        answer = mock_llm_response(context, request.question)
        
        return {
            "answer": answer,
            "vector_results": len(vector_results),
            "graph_results": len(graph_results),
            "mode": "local_development",
            "note": "This is mock data for testing. Deploy to GCP for real Bengaluru event data."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local dev error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Bengaluru Graph-RAG API in LOCAL DEVELOPMENT mode")
    print("📍 Mock data includes events around MG Road, Koramangala, and Indiranagar")
    print("🌐 API will be available at: http://localhost:8000")
    print("📖 API docs at: http://localhost:8000/docs")
    print("🧪 Test with: python test_local.py")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
