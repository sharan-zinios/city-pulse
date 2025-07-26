#!/usr/bin/env python3
"""
Simple local test without external dependencies
Tests the core logic of the Graph-RAG system with new incident schema
"""
import json
import uuid
import random
from datetime import datetime, timedelta

# Mock data using the new comprehensive incident schema
MOCK_INCIDENTS = [
    {
        "id": "INC_BLR_2025_000001",
        "event_type": "traffic_accident",
        "sub_category": "minor_collision",
        "description": "Vehicle collision reported at MG Road causing traffic disruption.",
        "keywords": ["traffic", "accident", "collision", "mg", "road", "vehicle"],
        "language": "en",
        "coordinates": [12.9716, 77.5946],
        "location_name": "MG Road",
        "area_category": "commercial",
        "ward_number": 150,
        "pincode": "560001",
        "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z",
        "estimated_duration": 120,
        "actual_duration": 95,
        "peak_hours": True,
        "severity_level": "medium",
        "priority_score": 0.75,
        "impact_radius": 500,
        "source": "traffic_camera",
        "verified": 0.9,
        "reporter_id": "RPT_123456",
        "verification_count": 5,
        "media_type": "image",
        "media_url": "https://storage.googleapis.com/citypulse-media/accident_001.jpg",
        "event_status": "in_progress",
        "assigned_department": "Traffic_Police",
        "resolution_notes": None,
        "weather_condition": "sunny",
        "traffic_density": "high"
    },
    {
        "id": "INC_BLR_2025_000002",
        "event_type": "pothole",
        "sub_category": "major_pothole",
        "description": "Large pothole discovered on Silk Board Junction affecting vehicle movement.",
        "keywords": ["pothole", "road", "damage", "silk", "board", "junction"],
        "language": "en",
        "coordinates": [12.9176, 77.6237],
        "location_name": "Silk Board Junction",
        "area_category": "highway",
        "ward_number": 174,
        "pincode": "560102",
        "timestamp": (datetime.utcnow() - timedelta(hours=6)).isoformat() + "Z",
        "estimated_duration": 240,
        "actual_duration": None,
        "peak_hours": False,
        "severity_level": "high",
        "priority_score": 0.85,
        "impact_radius": 800,
        "source": "citizen_report",
        "verified": 0.8,
        "reporter_id": "RPT_789012",
        "verification_count": 8,
        "media_type": "video",
        "media_url": "https://storage.googleapis.com/citypulse-media/pothole_002.mp4",
        "event_status": "verified",
        "assigned_department": "BBMP",
        "resolution_notes": None,
        "weather_condition": "rainy",
        "traffic_density": "moderate"
    },
    {
        "id": "INC_BLR_2025_000003",
        "event_type": "power_outage",
        "sub_category": "transformer_failure",
        "description": "Power supply disruption reported in Koramangala area.",
        "keywords": ["power", "outage", "electricity", "transformer", "koramangala"],
        "language": "en",
        "coordinates": [12.9352, 77.6245],
        "location_name": "Koramangala 5th Block",
        "area_category": "residential",
        "ward_number": 176,
        "pincode": "560095",
        "timestamp": (datetime.utcnow() - timedelta(hours=4)).isoformat() + "Z",
        "estimated_duration": 180,
        "actual_duration": 165,
        "peak_hours": False,
        "severity_level": "medium",
        "priority_score": 0.65,
        "impact_radius": 1200,
        "source": "government",
        "verified": 0.95,
        "reporter_id": "RPT_345678",
        "verification_count": 12,
        "media_type": "text_only",
        "media_url": "https://storage.googleapis.com/citypulse-media/power_003.txt",
        "event_status": "resolved",
        "assigned_department": "BESCOM",
        "resolution_notes": "Issue resolved by BESCOM team",
        "weather_condition": "cloudy",
        "traffic_density": "low"
    },
    {
        "id": "INC_BLR_2025_000004",
        "event_type": "construction",
        "sub_category": "metro_work",
        "description": "Metro construction work ongoing at Indiranagar with traffic diversions.",
        "keywords": ["construction", "metro", "work", "indiranagar", "diversion"],
        "language": "en",
        "coordinates": [12.9784, 77.6408],
        "location_name": "Indiranagar Metro Station",
        "area_category": "metro_station",
        "ward_number": 154,
        "pincode": "560038",
        "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z",
        "estimated_duration": 720,
        "actual_duration": None,
        "peak_hours": True,
        "severity_level": "low",
        "priority_score": 0.45,
        "impact_radius": 600,
        "source": "government",
        "verified": 1.0,
        "reporter_id": "RPT_901234",
        "verification_count": 3,
        "media_type": "image",
        "media_url": "https://storage.googleapis.com/citypulse-media/construction_004.jpg",
        "event_status": "in_progress",
        "assigned_department": "Metro",
        "resolution_notes": None,
        "weather_condition": "sunny",
        "traffic_density": "moderate"
    }
]

def calculate_distance(lat1, lon1, lat2, lon2):
    """Simple distance calculation"""
    return ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5

def mock_vector_search(question, coordinates, radius_km, event_types=None, severity_levels=None):
    """Mock vector search using keyword matching with new schema"""
    results = []
    keywords = question.lower().split()
    lat, lon = coordinates
    
    for incident in MOCK_INCIDENTS:
        # Distance filter
        inc_lat, inc_lon = incident["coordinates"]
        distance = calculate_distance(lat, lon, inc_lat, inc_lon)
        if distance > radius_km * 0.01:  # Rough conversion
            continue
        
        # Event type filter
        if event_types and incident["event_type"] not in event_types:
            continue
            
        # Severity filter
        if severity_levels and incident["severity_level"] not in severity_levels:
            continue
            
        # Keyword matching for semantic search
        text_lower = incident["description"].lower()
        keyword_matches = sum(1 for keyword in keywords if keyword in text_lower or keyword in incident["keywords"])
        
        if keyword_matches > 0:
            results.append({
                **incident,
                "relevance_score": keyword_matches + (incident["priority_score"] * 2)
            })
    
    return sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:10]

def mock_graph_search(coordinates, radius_km):
    """Mock graph traversal with spatial relationships"""
    results = []
    lat, lon = coordinates
    
    for incident in MOCK_INCIDENTS:
        inc_lat, inc_lon = incident["coordinates"]
        distance = calculate_distance(lat, lon, inc_lat, inc_lon)
        if distance <= radius_km * 0.01:  # Rough conversion
            results.append({
                "id": incident["id"],
                "event_type": incident["event_type"],
                "severity_level": incident["severity_level"],
                "status": incident["event_status"],
                "location": incident["location_name"],
                "timestamp": incident["timestamp"],
                "priority_score": incident["priority_score"]
            })
    
    return results

def mock_ai_analysis(context, question):
    """Enhanced AI response based on new incident data"""
    vector_incidents = context.get("vector_incidents", [])
    graph_incidents = context.get("graph_incidents", [])
    
    if not vector_incidents and not graph_incidents:
        return "No relevant incidents found in the specified area."
    
    # Analyze incident patterns
    event_types = [i.get("event_type", "") for i in vector_incidents]
    severity_levels = [i.get("severity_level", "") for i in vector_incidents]
    departments = [i.get("assigned_department", "") for i in vector_incidents]
    locations = list(set([i.get("location_name", "") for i in vector_incidents]))
    
    high_priority = [i for i in vector_incidents if i.get("priority_score", 0) > 0.7]
    unresolved = [i for i in vector_incidents if i.get("event_status") != "resolved"]
    
    # Generate contextual response
    if "traffic" in question.lower() or "traffic_accident" in event_types:
        return f"""Traffic Analysis for {locations[0] if locations else 'the area'}:
        
Current Situation:
- {len([e for e in event_types if 'traffic' in e])} traffic-related incidents detected
- {len(high_priority)} high-priority incidents requiring immediate attention
- Primary affected areas: {', '.join(locations[:3])}

Risk Assessment:
- Traffic density: {vector_incidents[0].get('traffic_density', 'unknown') if vector_incidents else 'unknown'}
- Weather conditions: {vector_incidents[0].get('weather_condition', 'unknown') if vector_incidents else 'unknown'}
- Peak hours impact: {'Yes' if any(i.get('peak_hours') for i in vector_incidents) else 'No'}

Recommendations:
- Consider alternative routes for next 2-3 hours
- Monitor {departments[0] if departments else 'Traffic Police'} updates
- Expected resolution time: {vector_incidents[0].get('estimated_duration', 'unknown')} minutes"""

    elif "power" in question.lower() or "power_outage" in event_types:
        return f"""Power Infrastructure Analysis:
        
Current Status:
- {len([e for e in event_types if 'power' in e])} power-related incidents
- Affected areas: {', '.join(locations)}
- Responsible department: {departments[0] if departments else 'BESCOM'}

Impact Assessment:
- Estimated affected radius: {vector_incidents[0].get('impact_radius', 'unknown')} meters
- Verification confidence: {vector_incidents[0].get('verified', 0)*100:.0f}%
- Resolution status: {vector_incidents[0].get('event_status', 'unknown')}

Next Steps:
- Estimated restoration: {vector_incidents[0].get('estimated_duration', 'unknown')} minutes
- Monitor official updates from utility provider"""

    elif "construction" in question.lower() or "construction" in event_types:
        return f"""Construction Activity Analysis:
        
Project Status:
- {len([e for e in event_types if 'construction' in e])} active construction projects
- Locations: {', '.join(locations)}
- Project duration: {vector_incidents[0].get('estimated_duration', 'unknown')} minutes

Traffic Impact:
- Diversions in effect: {'Yes' if any('diversion' in i.get('description', '') for i in vector_incidents) else 'No'}
- Peak hours affected: {'Yes' if any(i.get('peak_hours') for i in vector_incidents) else 'No'}

Planning Recommendations:
- Allow extra travel time during peak hours
- Use alternative routes when possible
- Check for updated diversion routes"""

    else:
        return f"""Incident Summary for {locations[0] if locations else 'the area'}:
        
Overview:
- Total incidents: {len(vector_incidents)}
- High priority: {len(high_priority)}
- Unresolved: {len(unresolved)}
- Event types: {', '.join(set(event_types))}

Severity Distribution:
- Critical: {len([s for s in severity_levels if s == 'critical'])}
- High: {len([s for s in severity_levels if s == 'high'])}
- Medium: {len([s for s in severity_levels if s == 'medium'])}
- Low: {len([s for s in severity_levels if s == 'low'])}

Responsible Departments: {', '.join(set(departments))}
Average Priority Score: {sum(i.get('priority_score', 0) for i in vector_incidents) / len(vector_incidents):.2f}"""

def test_incident_query(question, coordinates, radius_km=5, event_types=None, severity_levels=None):
    """Test a single incident query with new schema"""
    print(f"\n🔍 Query: {question}")
    print(f"📍 Location: ({coordinates[0]}, {coordinates[1]})")
    print(f"📏 Radius: {radius_km} km")
    if event_types:
        print(f"🏷️  Event Types: {event_types}")
    if severity_levels:
        print(f"⚠️  Severity Levels: {severity_levels}")
    
    # 1. Mock vector search
    vector_results = mock_vector_search(question, coordinates, radius_km, event_types, severity_levels)
    
    # 2. Mock graph traversal
    graph_results = mock_graph_search(coordinates, radius_km)
    
    # 3. AI analysis
    context = {"vector_incidents": vector_results, "graph_incidents": graph_results}
    analysis = mock_ai_analysis(context, question)
    
    print(f"🧠 Analysis:\n{analysis}")
    print(f"📊 Vector Results: {len(vector_results)}")
    print(f"🗄️  Graph Results: {len(graph_results)}")
    
    if vector_results:
        print("📋 Top Incidents:")
        for i, incident in enumerate(vector_results[:3], 1):
            print(f"   {i}. {incident['event_type']} ({incident['severity_level']}) at {incident['location_name']}")
            print(f"      Status: {incident['event_status']} | Priority: {incident['priority_score']}")
    
    return {
        "analysis": analysis,
        "vector_results": len(vector_results),
        "graph_results": len(graph_results),
        "incidents": vector_results
    }

def main():
    """Run comprehensive tests with new incident schema"""
    print("🧪 Bengaluru City Pulse - Enhanced Incident Management Testing")
    print("=" * 60)
    print("📍 Mock data includes comprehensive incident data with 23 fields")
    print("🎯 Testing advanced Graph-RAG functionality with city management focus")
    print()
    
    # Test queries with new capabilities
    test_queries = [
        {
            "question": "What traffic incidents are happening near MG Road?",
            "coordinates": [12.9716, 77.5946],
            "radius_km": 5,
            "event_types": ["traffic_accident"],
            "severity_levels": None
        },
        {
            "question": "Are there any high priority incidents in the area?",
            "coordinates": [12.9352, 77.6245],
            "radius_km": 10,
            "event_types": None,
            "severity_levels": ["high", "critical"]
        },
        {
            "question": "What's the power situation in Koramangala?",
            "coordinates": [12.9352, 77.6245],
            "radius_km": 3,
            "event_types": ["power_outage"],
            "severity_levels": None
        },
        {
            "question": "Any construction work affecting traffic?",
            "coordinates": [12.9784, 77.6408],
            "radius_km": 5,
            "event_types": ["construction"],
            "severity_levels": None
        },
        {
            "question": "Show me all incidents in Silk Board area",
            "coordinates": [12.9176, 77.6237],
            "radius_km": 2,
            "event_types": None,
            "severity_levels": None
        }
    ]
    
    results = []
    for query_data in test_queries:
        result = test_incident_query(**query_data)
        results.append(result)
        print("-" * 60)
    
    print("\n🎉 Testing Summary:")
    print(f"✅ Queries tested: {len(results)}")
    print(f"📊 Average incidents found: {sum(r['vector_results'] for r in results) / len(results):.1f}")
    print(f"🗄️  Average spatial matches: {sum(r['graph_results'] for r in results) / len(results):.1f}")
    print(f"🏷️  Event types covered: {len(set(i['event_type'] for r in results for i in r['incidents']))}")
    print("\n💡 This demonstrates the enhanced City Pulse incident management system!")
    print("🚀 Deploy to GCP for full functionality with real Bengaluru incident data and AI models.")

if __name__ == "__main__":
    main()
