import json
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalDatasetGenerator:
    """Generate realistic 10k+ incident dataset for local testing"""
    
    def __init__(self):
        # Bengaluru-specific data
        self.event_types = {
            "traffic_accident": [
                "vehicle_collision", "pedestrian_accident", "motorcycle_accident", 
                "bus_accident", "hit_and_run", "road_rage"
            ],
            "pothole": [
                "major_pothole", "road_damage", "surface_deterioration",
                "water_logging", "road_cave_in"
            ],
            "power_outage": [
                "transformer_failure", "cable_fault", "scheduled_maintenance",
                "overload_trip", "weather_damage"
            ],
            "water_supply": [
                "pipe_burst", "low_pressure", "contamination", 
                "pump_failure", "tank_overflow"
            ],
            "construction": [
                "unauthorized_construction", "road_digging", "building_collapse",
                "noise_complaint", "dust_pollution"
            ],
            "waste_management": [
                "garbage_overflow", "illegal_dumping", "collection_delay",
                "burning_waste", "blocked_drain"
            ],
            "street_lighting": [
                "light_not_working", "damaged_pole", "cable_theft",
                "insufficient_lighting", "flickering_lights"
            ],
            "tree_fall": [
                "fallen_tree", "branch_fall", "tree_uprooting",
                "storm_damage", "maintenance_required"
            ],
            "flooding": [
                "road_flooding", "drain_overflow", "rainwater_stagnation",
                "basement_flooding", "bridge_waterlogging"
            ],
            "fire_emergency": [
                "building_fire", "vehicle_fire", "electrical_fire",
                "forest_fire", "gas_leak"
            ]
        }
        
        # Bengaluru locations with realistic coordinates
        self.locations = [
            # Central Bengaluru
            {"name": "MG Road", "lat": 12.9716, "lon": 77.5946, "ward": 132, "area": "central", "pincode": 560001},
            {"name": "Brigade Road", "lat": 12.9719, "lon": 77.6037, "ward": 132, "area": "central", "pincode": 560001},
            {"name": "Commercial Street", "lat": 12.9833, "lon": 77.6089, "ward": 132, "area": "central", "pincode": 560001},
            
            # South Bengaluru
            {"name": "Koramangala", "lat": 12.9352, "lon": 77.6245, "ward": 150, "area": "south", "pincode": 560034},
            {"name": "BTM Layout", "lat": 12.9165, "lon": 77.6101, "ward": 176, "area": "south", "pincode": 560029},
            {"name": "Jayanagar", "lat": 12.9279, "lon": 77.5937, "ward": 167, "area": "south", "pincode": 560011},
            {"name": "JP Nagar", "lat": 12.9081, "lon": 77.5831, "ward": 180, "area": "south", "pincode": 560078},
            {"name": "Banashankari", "lat": 12.9248, "lon": 77.5562, "ward": 188, "area": "south", "pincode": 560070},
            
            # North Bengaluru
            {"name": "Rajajinagar", "lat": 12.9991, "lon": 77.5554, "ward": 10, "area": "north", "pincode": 560010},
            {"name": "Malleswaram", "lat": 13.0031, "lon": 77.5647, "ward": 76, "area": "north", "pincode": 560003},
            {"name": "Seshadripuram", "lat": 12.9893, "lon": 77.5709, "ward": 91, "area": "north", "pincode": 560020},
            {"name": "Yeshwantpur", "lat": 13.0284, "lon": 77.5544, "ward": 43, "area": "north", "pincode": 560022},
            
            # East Bengaluru
            {"name": "Indiranagar", "lat": 12.9784, "lon": 77.6408, "ward": 86, "area": "east", "pincode": 560038},
            {"name": "Whitefield", "lat": 12.9698, "lon": 77.7500, "ward": 84, "area": "east", "pincode": 560066},
            {"name": "Marathahalli", "lat": 12.9591, "lon": 77.6974, "ward": 84, "area": "east", "pincode": 560037},
            {"name": "HSR Layout", "lat": 12.9116, "lon": 77.6473, "ward": 165, "area": "east", "pincode": 560102},
            {"name": "Electronic City", "lat": 12.8456, "lon": 77.6603, "ward": 195, "area": "east", "pincode": 560100},
            
            # West Bengaluru
            {"name": "Vijayanagar", "lat": 12.9634, "lon": 77.5216, "ward": 108, "area": "west", "pincode": 560040},
            {"name": "Rajajinagar", "lat": 12.9991, "lon": 77.5554, "ward": 10, "area": "west", "pincode": 560010},
            {"name": "Basavanagudi", "lat": 12.9423, "lon": 77.5737, "ward": 155, "area": "west", "pincode": 560004},
            {"name": "Kengeri", "lat": 12.9081, "lon": 77.4851, "ward": 198, "area": "west", "pincode": 560060},
            
            # Outer Bengaluru
            {"name": "Yelahanka", "lat": 13.1007, "lon": 77.5963, "ward": 1, "area": "north", "pincode": 560064},
            {"name": "Hebbal", "lat": 13.0358, "lon": 77.5970, "ward": 8, "area": "north", "pincode": 560024},
            {"name": "Sarjapur", "lat": 12.9010, "lon": 77.6874, "ward": 183, "area": "east", "pincode": 560035},
            {"name": "Bannerghatta", "lat": 12.8007, "lon": 77.5773, "ward": 196, "area": "south", "pincode": 560083}
        ]
        
        # Department assignments based on incident type
        self.department_mapping = {
            "traffic_accident": ["Traffic Police", "Emergency Services"],
            "pothole": ["BBMP", "BWSSB"],
            "power_outage": ["BESCOM", "BBMP"],
            "water_supply": ["BWSSB", "BBMP"],
            "construction": ["BBMP", "BDA"],
            "waste_management": ["BBMP"],
            "street_lighting": ["BBMP", "BESCOM"],
            "tree_fall": ["BBMP", "Forest Department"],
            "flooding": ["BBMP", "BWSSB"],
            "fire_emergency": ["Fire Department", "Emergency Services"]
        }
        
        # Weather conditions affecting incidents
        self.weather_conditions = [
            "clear", "cloudy", "light_rain", "heavy_rain", 
            "thunderstorm", "fog", "hot", "humid"
        ]
        
        # Traffic density levels
        self.traffic_density = ["low", "medium", "high", "very_high"]
        
        # Realistic descriptions for different incident types
        self.description_templates = {
            "traffic_accident": [
                "Two-wheeler collision at {location} junction causing traffic jam",
                "Car accident near {location} metro station, ambulance required",
                "Bus breakdown at {location} main road blocking traffic",
                "Hit and run case reported at {location}, victim hospitalized",
                "Multi-vehicle collision on {location} flyover during rush hour"
            ],
            "pothole": [
                "Large pothole on {location} main road causing vehicle damage",
                "Road cave-in at {location} after heavy rainfall",
                "Multiple potholes on {location} causing traffic slowdown",
                "Water-filled pothole at {location} junction creating hazard",
                "Road surface deterioration at {location} needs immediate repair"
            ],
            "power_outage": [
                "Transformer failure at {location} affecting 500+ households",
                "Power cable fault in {location} area, restoration in progress",
                "Scheduled maintenance causing power outage in {location}",
                "Electrical overload trip at {location} substation",
                "Storm damage to power lines in {location} vicinity"
            ],
            "water_supply": [
                "Water pipe burst at {location} causing road flooding",
                "Low water pressure complaints from {location} residents",
                "Water contamination reported in {location} area",
                "Pump failure at {location} water treatment plant",
                "Water tank overflow at {location} causing wastage"
            ],
            "construction": [
                "Unauthorized construction activity at {location}",
                "Road digging work at {location} without proper permits",
                "Building collapse risk at {location} construction site",
                "Excessive noise from construction at {location}",
                "Dust pollution from construction work in {location}"
            ]
        }
    
    def generate_incident(self, incident_id: str, base_time: datetime) -> Dict[str, Any]:
        """Generate a single realistic incident"""
        
        # Select random event type and location
        event_type = random.choice(list(self.event_types.keys()))
        sub_category = random.choice(self.event_types[event_type])
        location = random.choice(self.locations)
        
        # Generate realistic timestamp (spread over last 90 days)
        days_ago = random.randint(0, 90)
        hours_offset = random.randint(0, 23)
        minutes_offset = random.randint(0, 59)
        
        timestamp = base_time - timedelta(
            days=days_ago, 
            hours=hours_offset, 
            minutes=minutes_offset
        )
        
        # Generate description
        description_template = random.choice(
            self.description_templates.get(event_type, [
                "Incident reported at {location} requiring attention"
            ])
        )
        description = description_template.format(location=location["name"])
        
        # Generate keywords
        keywords = [
            event_type.replace("_", " "),
            location["name"],
            location["area"],
            sub_category.replace("_", " ")
        ]
        
        # Add contextual keywords
        if event_type == "traffic_accident":
            keywords.extend(["traffic", "accident", "collision"])
        elif event_type == "power_outage":
            keywords.extend(["electricity", "power", "outage"])
        elif event_type == "water_supply":
            keywords.extend(["water", "supply", "pipe"])
        
        # Determine severity and priority
        severity_weights = {"low": 0.5, "medium": 0.3, "high": 0.2}
        severity_level = random.choices(
            list(severity_weights.keys()), 
            weights=list(severity_weights.values())
        )[0]
        
        # Priority score based on severity, location, and event type
        base_priority = {"low": 3, "medium": 6, "high": 8}[severity_level]
        
        # Adjust priority based on location (central areas get higher priority)
        if location["area"] == "central":
            base_priority += 1
        
        # Adjust priority based on event type
        high_priority_events = ["fire_emergency", "traffic_accident", "flooding"]
        if event_type in high_priority_events:
            base_priority += 1
        
        # Add some randomness
        priority_score = min(10, max(1, base_priority + random.uniform(-1, 1)))
        
        # Determine department
        possible_departments = self.department_mapping.get(event_type, ["BBMP"])
        assigned_department = random.choice(possible_departments)
        
        # Generate durations
        estimated_duration = random.randint(30, 480)  # 30 minutes to 8 hours
        
        # Sometimes actual duration differs from estimated
        if random.random() < 0.3:  # 30% chance of duration variance
            actual_duration = int(estimated_duration * random.uniform(0.5, 2.0))
        else:
            actual_duration = None
        
        # Peak hours detection (7-10 AM, 5-8 PM)
        hour = timestamp.hour
        peak_hours = (7 <= hour <= 10) or (17 <= hour <= 20)
        
        # Event status
        status_weights = {"reported": 0.4, "in_progress": 0.3, "resolved": 0.3}
        event_status = random.choices(
            list(status_weights.keys()),
            weights=list(status_weights.values())
        )[0]
        
        # Media information (some incidents have media)
        media_type = None
        media_url = None
        if random.random() < 0.2:  # 20% have media
            media_type = random.choice(["image", "video"])
            media_url = f"gs://city-pulse-media/{incident_id}.{media_type}"
        
        # Verification information
        verified = random.random() < 0.7  # 70% are verified
        verification_count = random.randint(1, 5) if verified else 0
        
        # Generate coordinates with some variance
        latitude = location["lat"] + random.uniform(-0.005, 0.005)
        longitude = location["lon"] + random.uniform(-0.005, 0.005)
        
        # Impact radius based on severity and event type
        base_radius = {"low": 0.5, "medium": 1.0, "high": 2.0}[severity_level]
        if event_type in ["flooding", "fire_emergency", "power_outage"]:
            base_radius *= 1.5
        impact_radius = base_radius + random.uniform(-0.2, 0.3)
        
        return {
            "id": incident_id,
            "event_type": event_type,
            "sub_category": sub_category,
            "description": description,
            "keywords": keywords,
            "language": "en",
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
            "location_name": location["name"],
            "area_category": location["area"],
            "ward_number": location["ward"],
            "pincode": location["pincode"],
            "timestamp": timestamp.isoformat() + "Z",
            "estimated_duration": estimated_duration,
            "actual_duration": actual_duration,
            "peak_hours": peak_hours,
            "severity_level": severity_level,
            "priority_score": round(priority_score, 2),
            "impact_radius": round(impact_radius, 2),
            "source": random.choice(["citizen_report", "sensor", "patrol", "emergency_call"]),
            "verified": verified,
            "reporter_id": f"user_{random.randint(1000, 9999)}" if verified else None,
            "verification_count": verification_count,
            "media_type": media_type,
            "media_url": media_url,
            "event_status": event_status,
            "assigned_department": assigned_department,
            "resolution_notes": f"Resolved by {assigned_department}" if event_status == "resolved" else None,
            "weather_condition": random.choice(self.weather_conditions),
            "traffic_density": random.choice(self.traffic_density)
        }
    
    def generate_dataset(self, count: int = 10000, output_file: str = "historical_incidents.json") -> List[Dict[str, Any]]:
        """Generate complete dataset of incidents"""
        
        logger.info(f"🏗️  Generating {count} realistic Bengaluru incidents...")
        
        base_time = datetime.utcnow()
        incidents = []
        
        for i in range(count):
            incident_id = f"BLR_HIST_{str(i+1).zfill(6)}"
            incident = self.generate_incident(incident_id, base_time)
            incidents.append(incident)
            
            # Progress logging
            if (i + 1) % 1000 == 0:
                logger.info(f"✅ Generated {i+1}/{count} incidents")
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(incidents, f, indent=2)
        
        logger.info(f"💾 Dataset saved to {output_file}")
        
        # Generate statistics
        self.print_dataset_statistics(incidents)
        
        return incidents
    
    def print_dataset_statistics(self, incidents: List[Dict[str, Any]]):
        """Print dataset statistics"""
        
        print("\n" + "="*60)
        print("📊 DATASET STATISTICS")
        print("="*60)
        
        # Basic stats
        print(f"📋 Total Incidents: {len(incidents)}")
        
        # Event type distribution
        event_types = {}
        for incident in incidents:
            event_type = incident["event_type"]
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        print("\n🏷️  Event Type Distribution:")
        for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(incidents)) * 100
            print(f"   {event_type}: {count} ({percentage:.1f}%)")
        
        # Severity distribution
        severity_levels = {}
        for incident in incidents:
            severity = incident["severity_level"]
            severity_levels[severity] = severity_levels.get(severity, 0) + 1
        
        print("\n⚠️  Severity Distribution:")
        for severity, count in severity_levels.items():
            percentage = (count / len(incidents)) * 100
            print(f"   {severity}: {count} ({percentage:.1f}%)")
        
        # Department distribution
        departments = {}
        for incident in incidents:
            dept = incident["assigned_department"]
            departments[dept] = departments.get(dept, 0) + 1
        
        print("\n🏢 Department Distribution:")
        for dept, count in sorted(departments.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(incidents)) * 100
            print(f"   {dept}: {count} ({percentage:.1f}%)")
        
        # Priority statistics
        priorities = [incident["priority_score"] for incident in incidents]
        high_priority = len([p for p in priorities if p >= 8.0])
        medium_priority = len([p for p in priorities if 6.0 <= p < 8.0])
        low_priority = len([p for p in priorities if p < 6.0])
        
        print("\n🎯 Priority Distribution:")
        print(f"   High (≥8.0): {high_priority} ({(high_priority/len(incidents)*100):.1f}%)")
        print(f"   Medium (6.0-7.9): {medium_priority} ({(medium_priority/len(incidents)*100):.1f}%)")
        print(f"   Low (<6.0): {low_priority} ({(low_priority/len(incidents)*100):.1f}%)")
        
        # Area distribution
        areas = {}
        for incident in incidents:
            area = incident["area_category"]
            areas[area] = areas.get(area, 0) + 1
        
        print("\n🗺️  Area Distribution:")
        for area, count in areas.items():
            percentage = (count / len(incidents)) * 100
            print(f"   {area}: {count} ({percentage:.1f}%)")
        
        print("="*60)

def main():
    """Main function to generate dataset"""
    parser = argparse.ArgumentParser(description="Generate realistic Bengaluru incident dataset")
    parser.add_argument("--count", type=int, default=10000,
                       help="Number of incidents to generate (default: 10000)")
    parser.add_argument("--output", default="historical_incidents.json",
                       help="Output file name (default: historical_incidents.json)")
    
    args = parser.parse_args()
    
    # Generate dataset
    generator = LocalDatasetGenerator()
    incidents = generator.generate_dataset(count=args.count, output_file=args.output)
    
    print(f"\n✅ Successfully generated {len(incidents)} incidents!")
    print(f"📁 Dataset saved to: {args.output}")
    print(f"💡 Use this file with the local simulator:")
    print(f"   python local_dev/realtime_simulator.py --dataset {args.output}")

if __name__ == "__main__":
    main()
