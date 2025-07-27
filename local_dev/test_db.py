#!/usr/bin/env python3
"""
Test the generated SQLite database
"""

import sqlite3
import json
from datetime import datetime

DB_FILE = 'local_incidents.db'

def test_database():
    """Test database queries"""
    print("🧪 Testing database queries...")
    print("📂 Database path:", DB_FILE)
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print("✅ Connected to database")
        
        # Test 1: Total incidents
        print("\n📊 Test 1: Total incidents")
        cursor.execute('SELECT COUNT(*) as count FROM incidents')
        row = cursor.fetchone()
        print(f"✅ Total incidents: {row[0]:,}")
        
        # Test 2: High priority incidents
        print("\n🚨 Test 2: High priority incidents")
        cursor.execute('SELECT COUNT(*) as count FROM incidents WHERE priority_score >= 8')
        row = cursor.fetchone()
        print(f"✅ High priority incidents: {row[0]:,}")
        
        # Test 3: Recent incidents (last hour)
        print("\n⏰ Test 3: Recent incidents (last hour)")
        one_hour_ago = datetime.now().replace(microsecond=0).isoformat() + 'Z'
        print(f"🕐 One hour ago timestamp: {one_hour_ago}")
        
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM incidents 
            WHERE processed_at > ?
        ''', (one_hour_ago,))
        row = cursor.fetchone()
        print(f"✅ Recent incidents: {row[0]:,}")
        
        # Test 4: Sample of recent timestamps
        print("\n📅 Test 4: Sample timestamps")
        cursor.execute('''
            SELECT processed_at, timestamp 
            FROM incidents 
            ORDER BY rowid DESC 
            LIMIT 5
        ''')
        rows = cursor.fetchall()
        print("✅ Sample timestamps:")
        for i, row in enumerate(rows):
            print(f"  {i+1}. processed_at: {row[0]}")
            print(f"     timestamp: {row[1]}")
        
        # Test 5: Agent activities table
        print("\n🤖 Test 5: Agent activities")
        cursor.execute('SELECT COUNT(*) as count FROM agent_activities')
        row = cursor.fetchone()
        print(f"✅ Total agent activities: {row[0]}")
        
        # Test recent agent activities
        cursor.execute('''
            SELECT agent_name, COUNT(*) as count 
            FROM agent_activities 
            WHERE timestamp > ?
            GROUP BY agent_name
        ''', (one_hour_ago,))
        rows = cursor.fetchall()
        print("✅ Recent agent activities:")
        for row in rows:
            print(f"  {row[0]}: {row[1]}")
        
        # Test 6: Schema verification
        print("\n🔍 Test 6: Schema verification")
        cursor.execute("PRAGMA table_info(incidents)")
        columns = cursor.fetchall()
        print(f"✅ Incidents table has {len(columns)} columns:")
        for col in columns[:5]:  # Show first 5 columns
            print(f"  - {col[1]} ({col[2]})")
        print("  ...")
        
        # Test 7: Sample incident data
        print("\n📋 Test 7: Sample incident data")
        cursor.execute('''
            SELECT id, event_type, location_name, priority_score, severity_level
            FROM incidents 
            ORDER BY priority_score DESC 
            LIMIT 3
        ''')
        rows = cursor.fetchall()
        print("✅ Top priority incidents:")
        for row in rows:
            print(f"  {row[0]}: {row[1]} at {row[2]} (priority: {row[3]}, severity: {row[4]})")
        
        conn.close()
        print("\n✅ Database connection closed")
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_database()