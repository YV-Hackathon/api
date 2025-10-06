#!/bin/bash
# Example curl commands for testing the user creation to onboarding flow

BASE_URL="https://fastapi-cms-dev-dy22v5r4xa-uc.a.run.app/api/v1"

echo "🚀 Testing User Creation to Onboarding Flow with curl"
echo "=================================================="

# Step 1: Create a new user
echo "Step 1: Creating a new user..."
TIMESTAMP=$(date +%s)
USER_RESPONSE=$(curl -s -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"curl_test_user_$TIMESTAMP\",
    \"email\": \"curl_test_$TIMESTAMP@example.com\",
    \"password\": \"secure_password_123\",
    \"first_name\": \"Curl\",
    \"last_name\": \"Tester\"
  }")

echo "User creation response:"
echo "$USER_RESPONSE" | jq '.'

# Extract user ID from response
USER_ID=$(echo "$USER_RESPONSE" | jq -r '.id // empty')
if [ -z "$USER_ID" ]; then
    echo "❌ Failed to extract user ID from response"
    exit 1
fi
echo "Created user with ID: $USER_ID"

echo ""
echo "Step 2: Getting onboarding questions..."
QUESTIONS_RESPONSE=$(curl -s -X GET "$BASE_URL/onboarding/questions")

echo "Onboarding questions:"
echo "$QUESTIONS_RESPONSE" | jq '.'

echo ""
echo "Step 3: Submitting onboarding answers..."

# First, let's get available speakers to use in our submission
echo "Getting available speakers for reference..."
SPEAKERS_RESPONSE=$(curl -s -X GET "$BASE_URL/speakers/")
echo "Available speakers:"
echo "$SPEAKERS_RESPONSE" | jq '.[] | {id, name, title}'

# Extract first few speaker IDs as JSON array
SPEAKER_IDS_JSON=$(echo "$SPEAKERS_RESPONSE" | jq -r '.[0:3] | map(.id)')
echo "Using speaker IDs: $SPEAKER_IDS_JSON"

# Submit onboarding answers
ONBOARDING_RESPONSE=$(curl -s -X POST "$BASE_URL/onboarding/submit" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $USER_ID,
    \"answers\": {
      \"speakers\": $SPEAKER_IDS_JSON,
      \"bible_reading_preference\": \"BALANCED\",
      \"teaching_style_preference\": \"RELATABLE\",
      \"environment_preference\": \"CONTEMPORARY\"
    }
  }")

echo "Onboarding submission response:"
echo "$ONBOARDING_RESPONSE" | jq '.'

echo ""
echo "Step 4: Getting user recommendations..."
RECOMMENDATIONS_RESPONSE=$(curl -s -X GET "$BASE_URL/onboarding/recommendations/$USER_ID")

echo "User recommendations:"
echo "$RECOMMENDATIONS_RESPONSE" | jq '.'

echo ""
echo "Step 5: Getting user details with preferences..."
USER_DETAILS_RESPONSE=$(curl -s -X GET "$BASE_URL/users/$USER_ID")

echo "User details with preferences:"
echo "$USER_DETAILS_RESPONSE" | jq '.'

echo ""
echo "✅ Complete onboarding flow tested successfully!"
echo "User ID: $USER_ID"
echo "Check the responses above for detailed information."
