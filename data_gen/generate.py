import os
import random
import json
import uuid
from datetime import datetime, timedelta
from google.cloud import storage

PROJECT_ID = os.getenv("PROJECT_ID")
BUCKET = f"{PROJECT_ID}-bengaluru-events-media"

client = storage.Client()
bucket = client.bucket(BUCKET)

# Enhanced data for realistic Bengaluru incidents
EVENT_TYPES = {
    "traffic_accident": ["minor_collision", "major_collision", "vehicle_breakdown", "hit_and_run"],
    "pothole": ["minor_pothole", "major_pothole", "road_damage", "crater"],
    "power_outage": ["transformer_failure", "cable_damage", "scheduled_maintenance", "overload"],
    "water_issue": ["pipe_burst", "water_shortage", "contamination", "leakage"],
    "construction": ["road_construction", "building_construction", "metro_work", "utility_work"],
    "flooding": ["street_flooding", "drain_overflow", "rainwater_logging", "sewage_overflow"],
    "fire_incident": ["vehicle_fire", "building_fire", "electrical_fire", "waste_fire"],
    "public_disturbance": ["protest", "gathering", "noise_complaint", "street_vendor_issue"]
}

LOCATIONS = [
    {"name": "MG Road", "coords": [12.9716, 77.5946], "area": "commercial", "ward": 150, "pincode": "560001"},
    {"name": "Silk Board Junction", "coords": [12.9176, 77.6237], "area": "highway", "ward": 174, "pincode": "560102"},
    {"name": "Koramangala 5th Block", "coords": [12.9352, 77.6245], "area": "residential", "ward": 176, "pincode": "560095"},
    {"name": "Indiranagar Metro Station", "coords": [12.9784, 77.6408], "area": "metro_station", "ward": 154, "pincode": "560038"},
    {"name": "Electronic City", "coords": [12.8456, 77.6603], "area": "industrial", "ward": 198, "pincode": "560100"},
    {"name": "Rajajinagar Metro Station", "coords": [12.9932, 77.5426], "area": "metro_station", "ward": 46, "pincode": "560021"},
    {"name": "Whitefield Main Road", "coords": [12.9698, 77.7500], "area": "commercial", "ward": 84, "pincode": "560066"},
    {"name": "HSR Layout", "coords": [12.9082, 77.6476], "area": "residential", "ward": 175, "pincode": "560102"},
    {"name": "Bannerghatta Road", "coords": [12.8988, 77.5951], "area": "highway", "ward": 188, "pincode": "560076"},
    {"name": "Vidhana Soudha", "coords": [12.9794, 77.5912], "area": "government", "ward": 139, "pincode": "560001"}
]

DEPARTMENTS = ["BBMP", "Traffic_Police", "BESCOM", "BWSSB", "Fire_Department", "Metro", "BMTC"]
SOURCES = ["citizen_report", "sensor_feed", "twitter", "government", "cctv", "traffic_camera", "mobile_app"]
WEATHER_CONDITIONS = ["sunny", "rainy", "foggy", "cloudy"]
TRAFFIC_DENSITIES = ["low", "moderate", "high", "congested"]
SEVERITY_LEVELS = ["low", "medium", "high", "critical"]
STATUSES = ["reported", "verified", "in_progress", "resolved", "false_alarm"]
MEDIA_TYPES = ["image", "video", "audio", "text_only"]

def generate_keywords(event_type, sub_category, location_name, description):
    """Generate relevant keywords from incident data"""
    keywords = []
    keywords.extend(event_type.split("_"))
    keywords.extend(sub_category.split("_"))
    keywords.extend(location_name.lower().split())
    
    # Add contextual keywords
    if "accident" in event_type:
        keywords.extend(["collision", "vehicle", "traffic", "injury"])
    elif "pothole" in event_type:
        keywords.extend(["road", "damage", "repair", "infrastructure"])
    elif "power" in event_type:
        keywords.extend(["electricity", "outage", "blackout", "supply"])
    elif "water" in event_type:
        keywords.extend(["supply", "pipe", "leak", "shortage"])
    elif "construction" in event_type:
        keywords.extend(["work", "development", "infrastructure", "diversion"])
    elif "flooding" in event_type:
        keywords.extend(["water", "rain", "drain", "overflow"])
    
    return list(set(keywords))[:10]  # Limit to 10 unique keywords

def is_peak_hours(timestamp):
    """Check if timestamp falls in peak hours (7-10 AM, 5-9 PM)"""
    hour = timestamp.hour
    return (7 <= hour <= 10) or (17 <= hour <= 21)

def calculate_priority_score(severity, peak_hours, area_category, verification_count):
    """Calculate priority score based on multiple factors"""
    base_score = {"low": 0.2, "medium": 0.5, "high": 0.7, "critical": 0.9}[severity]
    
    # Adjust for peak hours
    if peak_hours:
        base_score += 0.1
    
    # Adjust for area category
    area_multiplier = {
        "highway": 1.2, "metro_station": 1.1, "hospital_zone": 1.3,
        "commercial": 1.0, "residential": 0.9, "industrial": 0.8, "government": 1.1
    }
    base_score *= area_multiplier.get(area_category, 1.0)
    
    # Adjust for verification count
    base_score += min(verification_count * 0.05, 0.2)
    
    return min(base_score, 1.0)

# Generate 50 incidents
incidents = []
for i in range(50):
    # Select random event type and subcategory
    event_type = random.choice(list(EVENT_TYPES.keys()))
    sub_category = random.choice(EVENT_TYPES[event_type])
    
    # Select random location
    location = random.choice(LOCATIONS)
    
    # Generate timestamp (last 30 days)
    timestamp = datetime.utcnow() - timedelta(days=random.randint(0, 30), 
                                            hours=random.randint(0, 23), 
                                            minutes=random.randint(0, 59))
    
    # Generate description
    descriptions = {
        "traffic_accident": f"Vehicle collision reported at {location['name']} causing traffic disruption.",
        "pothole": f"Large pothole discovered on {location['name']} affecting vehicle movement.",
        "power_outage": f"Power supply disruption reported in {location['name']} area.",
        "water_issue": f"Water supply issue affecting residents near {location['name']}.",
        "construction": f"Construction work ongoing at {location['name']} with traffic diversions.",
        "flooding": f"Water logging reported at {location['name']} due to heavy rainfall.",
        "fire_incident": f"Fire incident reported near {location['name']} requiring immediate attention.",
        "public_disturbance": f"Public gathering/disturbance reported at {location['name']}."
    }
    
    description = descriptions.get(event_type, f"Incident reported at {location['name']}.")
    
    # Generate other fields
    severity = random.choice(SEVERITY_LEVELS)
    peak_hours = is_peak_hours(timestamp)
    verification_count = random.randint(1, 15)
    
    incident = {
        "id": f"INC_BLR_2025_{str(i+1).zfill(6)}",
        "event_type": event_type,
        "sub_category": sub_category,
        "description": description,
        "keywords": generate_keywords(event_type, sub_category, location['name'], description),
        "language": "en",
        "coordinates": [location['coords'][0] + random.uniform(-0.01, 0.01), 
                       location['coords'][1] + random.uniform(-0.01, 0.01)],
        "location_name": location['name'],
        "area_category": location['area'],
        "ward_number": location['ward'],
        "pincode": location['pincode'],
        "timestamp": timestamp.isoformat() + "Z",
        "estimated_duration": random.randint(30, 480),  # 30 minutes to 8 hours
        "actual_duration": random.randint(15, 600) if random.random() > 0.3 else None,
        "peak_hours": peak_hours,
        "severity_level": severity,
        "priority_score": round(calculate_priority_score(severity, peak_hours, location['area'], verification_count), 2),
        "impact_radius": random.randint(100, 2000),
        "source": random.choice(SOURCES),
        "verified": round(random.uniform(0.5, 1.0), 2),
        "reporter_id": f"RPT_{random.randint(100000, 999999)}",
        "verification_count": verification_count,
        "media_type": random.choice(MEDIA_TYPES),
        "media_url": f"https://storage.googleapis.com/citypulse-media/{event_type}_{i+1}.jpg",
        "event_status": random.choice(STATUSES),
        "assigned_department": random.choice(DEPARTMENTS),
        "resolution_notes": f"Issue resolved by {random.choice(DEPARTMENTS)} team" if random.random() > 0.4 else None,
        "weather_condition": random.choice(WEATHER_CONDITIONS),
        "traffic_density": random.choice(TRAFFIC_DENSITIES)
    }
    
    # Upload dummy media file
    media_filename = f"{event_type}_{i+1}.jpg"
    bucket.blob(media_filename).upload_from_string(b"fake_media_content")
    
    incidents.append(incident)

# Save to JSON file
json.dump(incidents, open("incidents.json", "w"), indent=2)
print(f"Generated {len(incidents)} incidents and uploaded media to gs://{BUCKET}")
print("incidents.json file created with comprehensive incident data")
