#!/usr/bin/env python3
"""
Generate SQLite database from incidents JSON data
Creates both incidents and agent_activities tables
"""

import sqlite3
import json
import os
from datetime import datetime

# Paths
JSON_FILE = 'incidents_data.json'
DB_FILE = 'local_incidents.db'

def create_database():
    """Create the SQLite database with proper schema"""
    
    # Remove existing database if it exists
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"🗑️  Removed existing {DB_FILE}")
    
    # Connect to database (creates new file)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create incidents table
    cursor.execute('''
        CREATE TABLE incidents (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            sub_category TEXT,
            description TEXT,
            keywords TEXT,  -- JSON array as text
            language TEXT,
            latitude REAL,
            longitude REAL,
            location_name TEXT,
            area_category TEXT,
            ward_number INTEGER,
            pincode TEXT,
            timestamp TEXT,  -- ISO format
            processed_at TEXT,  -- ISO format, when inserted into DB
            estimated_duration INTEGER,
            actual_duration INTEGER,
            peak_hours BOOLEAN,
            severity_level TEXT,
            priority_score REAL,
            impact_radius REAL,
            source TEXT,
            verified BOOLEAN,
            reporter_id TEXT,
            verification_count INTEGER,
            media_type TEXT,
            media_url TEXT,
            event_status TEXT,
            assigned_department TEXT,
            resolution_notes TEXT,
            weather_condition TEXT,
            traffic_density TEXT
        )
    ''')
    print("✅ Created incidents table")
    
    # Create agent_activities table
    cursor.execute('''
        CREATE TABLE agent_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            incident_id TEXT,
            action TEXT,
            details TEXT,  -- JSON as text
            FOREIGN KEY (incident_id) REFERENCES incidents (id)
        )
    ''')
    print("✅ Created agent_activities table")
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX idx_incidents_timestamp ON incidents(timestamp)')
    cursor.execute('CREATE INDEX idx_incidents_priority ON incidents(priority_score)')
    cursor.execute('CREATE INDEX idx_incidents_location ON incidents(latitude, longitude)')
    cursor.execute('CREATE INDEX idx_incidents_status ON incidents(event_status)')
    cursor.execute('CREATE INDEX idx_agent_activities_timestamp ON agent_activities(timestamp)')
    cursor.execute('CREATE INDEX idx_agent_activities_agent ON agent_activities(agent_name)')
    print("✅ Created database indexes")
    
    conn.commit()
    return conn, cursor

def load_incidents_data():
    """Load incidents from JSON file"""
    try:
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)
        print(f"✅ Loaded {len(data)} incidents from {JSON_FILE}")
        return data
    except Exception as e:
        print(f"❌ Error loading JSON data: {e}")
        return []

def insert_incidents(cursor, incidents_data):
    """Insert incidents into database"""
    current_time = datetime.utcnow().isoformat() + 'Z'
    
    for incident in incidents_data:
        try:
            # Prepare data
            keywords_json = json.dumps(incident.get('keywords', []))
            
            # Convert coordinates array to separate lat/lng if needed
            if 'coordinates' in incident and isinstance(incident['coordinates'], list):
                latitude = incident['coordinates'][0]
                longitude = incident['coordinates'][1]
            else:
                latitude = incident.get('latitude')
                longitude = incident.get('longitude')
            
            # Convert verified to boolean if it's a float
            verified = incident.get('verified', True)
            if isinstance(verified, float):
                verified = verified >= 0.5
            
            cursor.execute('''
                INSERT INTO incidents (
                    id, event_type, sub_category, description, keywords, language,
                    latitude, longitude, location_name, area_category, ward_number, pincode,
                    timestamp, processed_at, estimated_duration, actual_duration, peak_hours,
                    severity_level, priority_score, impact_radius, source, verified,
                    reporter_id, verification_count, media_type, media_url, event_status,
                    assigned_department, resolution_notes, weather_condition, traffic_density
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                incident.get('id'),
                incident.get('event_type'),
                incident.get('sub_category'),
                incident.get('description'),
                keywords_json,
                incident.get('language', 'en'),
                latitude,
                longitude,
                incident.get('location_name'),
                incident.get('area_category'),
                incident.get('ward_number'),
                str(incident.get('pincode', '')),
                incident.get('timestamp'),
                current_time,  # processed_at
                incident.get('estimated_duration'),
                incident.get('actual_duration'),
                incident.get('peak_hours', False),
                incident.get('severity_level'),
                incident.get('priority_score'),
                incident.get('impact_radius'),
                incident.get('source'),
                verified,
                incident.get('reporter_id'),
                incident.get('verification_count'),
                incident.get('media_type'),
                incident.get('media_url'),
                incident.get('event_status'),
                incident.get('assigned_department'),
                incident.get('resolution_notes'),
                incident.get('weather_condition'),
                incident.get('traffic_density')
            ))
        except Exception as e:
            print(f"❌ Error inserting incident {incident.get('id', 'unknown')}: {e}")
            continue
    
    print(f"✅ Inserted {len(incidents_data)} incidents")

def create_sample_agent_activities(cursor):
    """Create some sample agent activities"""
    current_time = datetime.utcnow().isoformat() + 'Z'
    
    agent_activities = [
        {
            'agent_name': 'notification_agent',
            'timestamp': current_time,
            'incident_id': 'BLR_HIST_000001',
            'action': 'notification_sent',
            'details': json.dumps({'priority_score': 7.42, 'notification_type': 'email'})
        },
        {
            'agent_name': 'trend_analysis_agent',
            'timestamp': current_time,
            'incident_id': None,
            'action': 'trend_analysis',
            'details': json.dumps({'insight': 'Water supply issues increasing in South Bangalore'})
        },
        {
            'agent_name': 'resource_allocation_agent',
            'timestamp': current_time,
            'incident_id': 'BLR_HIST_000001',
            'action': 'resource_allocated',
            'details': json.dumps({'allocation': {'teams': 2, 'vehicles': 1}})
        },
        {
            'agent_name': 'news_insights_agent',
            'timestamp': current_time,
            'incident_id': None,
            'action': 'news_summary',
            'details': json.dumps({'news_impact': 'Water shortage reported in local news'})
        }
    ]
    
    for activity in agent_activities:
        cursor.execute('''
            INSERT INTO agent_activities (agent_name, timestamp, incident_id, action, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            activity['agent_name'],
            activity['timestamp'],
            activity['incident_id'],
            activity['action'],
            activity['details']
        ))
    
    print(f"✅ Created {len(agent_activities)} sample agent activities")

def main():
    """Main function to generate the database"""
    print("🚀 Starting database generation...")
    print("=" * 50)
    
    # Create database and tables
    conn, cursor = create_database()
    
    # Load and insert incidents data
    incidents_data = load_incidents_data()
    if incidents_data:
        insert_incidents(cursor, incidents_data)
    
    # Create sample agent activities
    create_sample_agent_activities(cursor)
    
    # Commit and close
    conn.commit()
    conn.close()
    
    # Verify database creation
    if os.path.exists(DB_FILE):
        file_size = os.path.getsize(DB_FILE)
        print(f"✅ Database created successfully: {DB_FILE} ({file_size:,} bytes)")
        
        # Quick verification
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM incidents")
        incident_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM agent_activities")
        activity_count = cursor.fetchone()[0]
        
        print(f"📊 Database contains:")
        print(f"   - {incident_count:,} incidents")
        print(f"   - {activity_count} agent activities")
        
        conn.close()
    else:
        print("❌ Database creation failed")
    
    print("=" * 50)
    print("🎉 Database generation complete!")

if __name__ == "__main__":
    main()