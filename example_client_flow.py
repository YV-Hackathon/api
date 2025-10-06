#!/usr/bin/env python3
"""
Example client implementation showing the complete user creation to onboarding flow.
This demonstrates how clients should interact with the API.
"""

import requests
import json
import time
from typing import Dict, List, Any

class OnboardingClient:
    def __init__(self, base_url: str = "https://YOUR_CLOUD_RUN_URL/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Create a new user"""
        print("🔄 Creating user...")
        
        response = self.session.post(f"{self.base_url}/users/", json=user_data)
        
        if response.status_code != 200:
            raise Exception(f"User creation failed: {response.status_code} - {response.text}")
        
        user = response.json()
        print(f"✅ User created successfully: {user['first_name']} {user['last_name']} (ID: {user['id']})")
        return user

    def get_onboarding_questions(self) -> List[Dict[str, Any]]:
        """Step 2: Get onboarding questions"""
        print("🔄 Fetching onboarding questions...")
        
        response = self.session.get(f"{self.base_url}/onboarding/questions")
        
        if response.status_code != 200:
            raise Exception(f"Failed to get questions: {response.status_code} - {response.text}")
        
        questions = response.json()
        print(f"✅ Retrieved {len(questions)} onboarding questions")
        
        # Display questions for reference
        for i, question in enumerate(questions, 1):
            print(f"   {i}. {question['title']} ({question['type']})")
            if question['options']:
                print(f"      Options: {len(question['options'])} available")
        
        return questions

    def submit_onboarding_answers(self, user_id: int, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3: Submit onboarding answers"""
        print("🔄 Submitting onboarding answers...")
        
        payload = {
            "user_id": user_id,
            "answers": answers
        }
        
        response = self.session.post(f"{self.base_url}/onboarding/submit", json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Onboarding submission failed: {response.status_code} - {response.text}")
        
        result = response.json()
        print("✅ Onboarding completed successfully!")
        return result

    def get_user_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """Get personalized recommendations for a user"""
        print(f"🔄 Getting recommendations for user {user_id}...")
        
        response = self.session.get(f"{self.base_url}/onboarding/recommendations/{user_id}")
        
        if response.status_code != 200:
            raise Exception(f"Failed to get recommendations: {response.status_code} - {response.text}")
        
        recommendations = response.json()
        print(f"✅ Retrieved {len(recommendations)} recommended speakers")
        return recommendations

    def complete_onboarding_flow(self, user_data: Dict[str, Any], user_answers: Dict[str, Any]) -> Dict[str, Any]:
        """Complete the entire onboarding flow"""
        print("🚀 Starting complete onboarding flow...")
        print("=" * 50)
        
        try:
            # Step 1: Create user
            user = self.create_user(user_data)
            user_id = user['id']
            
            # Step 2: Get questions
            questions = self.get_onboarding_questions()
            
            # Step 3: Submit answers
            result = self.submit_onboarding_answers(user_id, user_answers)
            
            # Step 4: Get recommendations
            recommendations = self.get_user_recommendations(user_id)
            
            print("=" * 50)
            print("🎉 Onboarding flow completed successfully!")
            print(f"User: {result['user']['first_name']} {result['user']['last_name']}")
            print(f"Preferred speakers: {len(result['user']['preferred_speakers'])}")
            print(f"Recommended speakers: {len(result['recommended_speakers'])}")
            
            return {
                'user': result['user'],
                'recommendations': recommendations,
                'questions': questions
            }
            
        except Exception as e:
            print(f"❌ Onboarding flow failed: {e}")
            raise

def main():
    """Example usage of the onboarding client"""
    
    # Initialize client
    client = OnboardingClient()
    
    # Example user data
    user_data = {
        "username": "test_user_123",
        "email": "test@example.com",
        "password": "secure_password_123",
        "first_name": "John",
        "last_name": "Doe"
    }
    
    # Example user answers (these would come from your UI)
    user_answers = {
        "speakers": [1, 2, 3],  # Speaker IDs - adjust based on available speakers
        "bible_reading_preference": "BALANCED",
        "teaching_style_preference": "RELATABLE",
        "environment_preference": "CONTEMPORARY"
    }
    
    try:
        # Complete the onboarding flow
        result = client.complete_onboarding_flow(user_data, user_answers)
        
        # Display detailed results
        print("\n📊 Detailed Results:")
        print("-" * 30)
        
        user = result['user']
        print(f"User ID: {user['id']}")
        print(f"Username: {user['username']}")
        print(f"Email: {user['email']}")
        print(f"Onboarding Completed: {user['onboarding_completed']}")
        print(f"Bible Reading Preference: {user['bible_reading_preference']}")
        print(f"Teaching Style Preference: {user['teaching_style_preference']}")
        print(f"Environment Preference: {user['environment_preference']}")
        
        print(f"\nPreferred Speakers ({len(user['preferred_speakers'])}):")
        for speaker in user['preferred_speakers']:
            print(f"  - {speaker['name']} ({speaker['title']})")
        
        print(f"\nRecommended Speakers ({len(result['recommendations'])}):")
        for speaker in result['recommendations']:
            church_name = speaker.get('church', {}).get('name', 'No Church') if speaker.get('church') else 'No Church'
            print(f"  - {speaker['name']} ({speaker['title']}) from {church_name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
