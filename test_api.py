#!/usr/bin/env python3
"""
Simple test script to verify the API endpoints are working.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test basic API endpoints"""
    print("🧪 Testing FastAPI CMS endpoints...")
    
    # Test health check
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test root endpoint
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Root endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
    
    # Test churches endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/v1/churches/")
        print(f"✅ Churches endpoint: {response.status_code}")
        if response.status_code == 200:
            churches = response.json()
            print(f"   Found {len(churches)} churches")
            if churches:
                print(f"   First church: {churches[0]['name']}")
    except Exception as e:
        print(f"❌ Churches endpoint failed: {e}")
    
    # Test speakers endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/v1/speakers/")
        print(f"✅ Speakers endpoint: {response.status_code}")
        if response.status_code == 200:
            speakers = response.json()
            print(f"   Found {len(speakers)} speakers")
            if speakers:
                print(f"   First speaker: {speakers[0]['name']}")
    except Exception as e:
        print(f"❌ Speakers endpoint failed: {e}")
    
    # Test onboarding questions
    try:
        response = requests.get(f"{BASE_URL}/api/v1/onboarding/questions")
        print(f"✅ Onboarding questions: {response.status_code}")
        if response.status_code == 200:
            questions = response.json()
            print(f"   Found {len(questions)} questions")
    except Exception as e:
        print(f"❌ Onboarding questions failed: {e}")
    
    print("\n🎉 API testing completed!")

if __name__ == "__main__":
    test_endpoints()
