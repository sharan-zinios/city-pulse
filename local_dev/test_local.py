#!/usr/bin/env python3
"""
Test script for local development API
"""
import requests
import json
import time

API_URL = "http://localhost:8000"

def test_local_api():
    """Test the local development API"""
    print("🧪 Testing Local Bengaluru Graph-RAG API")
    print(f"🌐 API URL: {API_URL}")
    print()
    
    # Test health endpoint
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the local server is running:")
        print("   python local_dev/run_local.py")
        return
    
    print()
    
    # Test queries
    test_queries = [
        {
            "question": "What events are happening near MG Road?",
            "lat": 12.9716,
            "lon": 77.5946,
            "radius_km": 5
        },
        {
            "question": "Are there any concerts or music events?",
            "lat": 12.9352,
            "lon": 77.6245,
            "radius_km": 10
        },
        {
            "question": "What's the traffic situation in the area?",
            "lat": 12.9698,
            "lon": 77.5986,
            "radius_km": 3
        },
        {
            "question": "Any food festivals happening?",
            "lat": 12.9279,
            "lon": 77.6271,
            "radius_km": 5
        },
        {
            "question": "Tech meetups in Koramangala?",
            "lat": 12.9352,
            "lon": 77.6245,
            "radius_km": 2
        }
    ]
    
    print("🔍 Testing ask endpoint with sample queries...")
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test Query {i} ---")
        print(f"Question: {query['question']}")
        print(f"Location: ({query['lat']}, {query['lon']})")
        print(f"Radius: {query['radius_km']} km")
        
        try:
            response = requests.post(
                f"{API_URL}/ask",
                json=query,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Answer: {result.get('answer', 'No answer')}")
                print(f"Vector Results: {result.get('vector_results', 0)}")
                print(f"Graph Results: {result.get('graph_results', 0)}")
                print(f"Mode: {result.get('mode', 'unknown')}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(0.5)  # Small delay between requests
    
    print("\n🎉 Local testing complete!")
    print("💡 To test the full system, deploy to GCP with: ./deploy.ps1")

if __name__ == "__main__":
    test_local_api()
