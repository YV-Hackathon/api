# Flutter Onboarding Flow Implementation Summary

## Quick Reference

### API Base URL
Replace `YOUR_CLOUD_RUN_URL` with your actual Cloud Run service URL:
```
https://YOUR_CLOUD_RUN_URL/api/v1
```

### API Endpoints
- **User Creation**: `POST /api/v1/users/`
- **Get Questions**: `GET /api/v1/onboarding/questions`
- **Submit Answers**: `POST /api/v1/onboarding/submit`
- **Get Recommendations**: `GET /api/v1/onboarding/recommendations/{user_id}`

### Required Files for Flutter Clients
1. `CLIENT_IMPLEMENTATION_GUIDE.md` - Complete Flutter implementation guide
2. `flutter_example.dart` - Working Flutter/Dart example
3. `example_client_flow.py` - Python reference example
4. `curl_examples.sh` - Command-line testing examples

## Flow Overview

```
1. Create User → 2. Get Questions → 3. Submit Answers → 4. Get Recommendations
     ↓              ↓                ↓                  ↓
   User ID     4 Questions      Save Preferences    Personalized Results
```

## Onboarding Questions

| Question | Type | Purpose |
|----------|------|---------|
| **Speaker Selection** | Multi-select | Choose preferred speakers |
| **Bible Reading** | Single-select | More Scripture / Life Application / Balanced |
| **Teaching Style** | Single-select | Academic / Relatable / Balanced |
| **Environment** | Single-select | Traditional / Contemporary / Blended |

## Data Flow

### 1. User Creation
```json
POST /api/v1/users/
{
  "username": "john_doe",
  "email": "john@example.com", 
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe"
}
```

### 2. Get Questions
```json
GET /api/v1/onboarding/questions
→ Returns 4 questions with dynamic speaker options
```

### 3. Submit Answers
```json
POST /api/v1/onboarding/submit
{
  "user_id": 1,
  "answers": {
    "speakers": [1, 2, 3],
    "bible_reading_preference": "BALANCED",
    "teaching_style_preference": "RELATABLE", 
    "environment_preference": "CONTEMPORARY"
  }
}
```

### 4. Get Results
```json
{
  "user": { /* user data with preferences */ },
  "recommended_speakers": [ /* personalized recommendations */ ]
}
```

## Flutter Implementation Examples

### Complete Flutter Flow
```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class OnboardingService {
  static const String baseUrl = 'https://YOUR_CLOUD_RUN_URL/api/v1';
  
  static Future<Map<String, dynamic>> completeOnboarding({
    required Map<String, dynamic> userData,
    required Map<String, dynamic> answers,
  }) async {
    // 1. Create user
    final user = await http.post(
      Uri.parse('$baseUrl/users/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(userData),
    ).then((r) => jsonDecode(r.body));
    
    // 2. Get questions
    final questions = await http.get(Uri.parse('$baseUrl/onboarding/questions'))
        .then((r) => jsonDecode(r.body));
    
    // 3. Submit answers
    final result = await http.post(
      Uri.parse('$baseUrl/onboarding/submit'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'user_id': user['id'],
        'answers': answers,
      }),
    ).then((r) => jsonDecode(r.body));
    
    return result;
  }
}
```

### Python Reference
```python
import requests

def complete_onboarding(user_data, answers):
    base_url = "https://YOUR_CLOUD_RUN_URL/api/v1"
    
    # 1. Create user
    user = requests.post(f"{base_url}/users/", json=user_data).json()
    
    # 2. Get questions  
    questions = requests.get(f"{base_url}/onboarding/questions").json()
    
    # 3. Submit answers
    result = requests.post(f"{base_url}/onboarding/submit", json={
        "user_id": user["id"],
        "answers": answers
    }).json()
    
    return result
```

### cURL Testing
```bash
# 1. Create user
curl -X POST "https://YOUR_CLOUD_RUN_URL/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"pass","first_name":"Test","last_name":"User"}'

# 2. Get questions
curl "https://YOUR_CLOUD_RUN_URL/api/v1/onboarding/questions"

# 3. Submit answers (replace USER_ID with actual ID)
curl -X POST "https://YOUR_CLOUD_RUN_URL/api/v1/onboarding/submit" \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"answers":{"speakers":[1,2],"bible_reading_preference":"BALANCED","teaching_style_preference":"RELATABLE","environment_preference":"CONTEMPORARY"}}'
```

## Error Handling

### Common HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid data)
- `404` - Not Found (user doesn't exist)
- `422` - Validation Error (invalid enum values)
- `500` - Internal Server Error

### Validation Rules
- **Username**: Required, unique
- **Email**: Required, valid format, unique
- **Password**: Required
- **Names**: Required strings
- **Preferences**: Must match enum values exactly

## Testing

### Quick Test
```bash
# Run the curl examples (replace YOUR_CLOUD_RUN_URL first)
./curl_examples.sh

# Or run the Python example
python example_client_flow.py

# Or run the Flutter example
dart flutter_example.dart
```

### Manual Testing
1. Deploy your FastAPI server to Cloud Run
2. Get your Cloud Run URL from the deployment output
3. Replace `YOUR_CLOUD_RUN_URL` in all examples with your actual URL
4. Open browser to `https://YOUR_CLOUD_RUN_URL/docs` for interactive API docs
5. Use the provided examples to test each endpoint

## Next Steps After Onboarding

Once onboarding is complete, clients can:

1. **Display Recommendations**: Show personalized speaker recommendations
2. **Browse Content**: Use other API endpoints to browse churches and speakers
3. **Update Preferences**: Allow users to modify their preferences later
4. **Track Progress**: Use the `onboarding_completed` flag to track user state

## Support

For implementation questions or issues:
1. Check the interactive API docs at `/docs`
2. Review the example files provided
3. Test with the curl examples
4. Examine the database models in `app/db/models.py`

The system is designed to be simple and straightforward - most clients should be able to implement the full flow in under 100 lines of code.
