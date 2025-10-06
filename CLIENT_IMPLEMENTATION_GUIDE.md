# Flutter Client Implementation Guide: User Creation to Onboarding Flow

This guide walks through the complete user creation and onboarding flow for Flutter clients implementing the FastAPI CMS system.

## Overview

The flow consists of 3 main steps:
1. **User Registration** - Create a new user account
2. **Get Onboarding Questions** - Retrieve the questions to present to the user
3. **Submit Onboarding Preferences** - Save user's answers and get recommendations

## API Base URL

Replace `YOUR_CLOUD_RUN_URL` with your actual Cloud Run service URL:
```
https://YOUR_CLOUD_RUN_URL/api/v1
```

**Example**: `https://fastapi-cms-dev-abc123-uc.a.run.app/api/v1`

## Step 1: User Registration

### Endpoint
```
POST /api/v1/users/
```

### Request Body
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password_123",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Response
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "onboarding_completed": false,
  "bible_reading_preference": null,
  "teaching_style_preference": null,
  "environment_preference": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": null
}
```

### Flutter Implementation Example

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'https://YOUR_CLOUD_RUN_URL/api/v1';
  
  // Create a new user
  static Future<Map<String, dynamic>> createUser(Map<String, dynamic> userData) async {
    final response = await http.post(
      Uri.parse('$baseUrl/users/'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode(userData),
    );
    
    if (response.statusCode != 200) {
      throw Exception('User creation failed: ${response.statusCode} - ${response.body}');
    }
    
    return jsonDecode(response.body);
  }
}

// Usage
void main() async {
  try {
    final newUser = await ApiService.createUser({
      'username': 'john_doe',
      'email': 'john@example.com',
      'password': 'secure_password_123',
      'first_name': 'John',
      'last_name': 'Doe',
    });
    
    print('User created with ID: ${newUser['id']}');
  } catch (e) {
    print('Error: $e');
  }
}
```

## Step 2: Get Onboarding Questions

### Endpoint
```
GET /api/v1/onboarding/questions
```

### Response
```json
[
  {
    "id": "speakers",
    "title": "Select Speakers That Interest You",
    "description": "Choose speakers whose messages resonate with you",
    "type": "multi-select",
    "options": [
      {
        "value": "1",
        "label": "Pastor John Smith",
        "subtitle": "Senior Pastor",
        "church": "Grace Community Church"
      },
      {
        "value": "2", 
        "label": "Dr. Sarah Johnson",
        "subtitle": "Teaching Pastor",
        "church": "Hope Fellowship"
      }
    ]
  },
  {
    "id": "bibleReadingPreference",
    "title": "When you read the Bible, what's most helpful for you?",
    "description": "Select the approach that helps you most",
    "type": "single-select",
    "options": [
      {
        "value": "More Scripture",
        "label": "Focused on reading large sections of the text"
      },
      {
        "value": "Life Application", 
        "label": "Practical guidance for everyday life"
      },
      {
        "value": "Balanced",
        "label": "A mix of both Scripture and life application"
      }
    ]
  },
  {
    "id": "teachingStylePreference",
    "title": "What style of teaching do you connect with most?",
    "description": "Choose the teaching style that resonates with you",
    "type": "single-select",
    "options": [
      {
        "value": "Academic",
        "label": "In-depth explanations and context"
      },
      {
        "value": "Relatable",
        "label": "Everyday examples that connect to your life"
      },
      {
        "value": "Balanced",
        "label": "A balance of depth and accessibility"
      }
    ]
  },
  {
    "id": "environmentPreference",
    "title": "What kind of environment are you hoping to find?",
    "description": "Select the church environment that appeals to you",
    "type": "single-select",
    "options": [
      {
        "value": "Traditional",
        "label": "Hymns, liturgy and structured services"
      },
      {
        "value": "Contemporary",
        "label": "Modern worship and casual style"
      },
      {
        "value": "Blended",
        "label": "A mix of traditional and modern services"
      }
    ]
  }
]
```

### Flutter Implementation Example

```dart
// Add to ApiService class
static Future<List<Map<String, dynamic>>> getOnboardingQuestions() async {
  final response = await http.get(
    Uri.parse('$baseUrl/onboarding/questions'),
  );
  
  if (response.statusCode != 200) {
    throw Exception('Failed to get questions: ${response.statusCode} - ${response.body}');
  }
  
  return List<Map<String, dynamic>>.from(jsonDecode(response.body));
}

// Usage
void main() async {
  try {
    final questions = await ApiService.getOnboardingQuestions();
    print('Found ${questions.length} onboarding questions');
    
    // Render questions in your UI
    for (var question in questions) {
      print('Question: ${question['title']}');
      print('Type: ${question['type']}');
      print('Options: ${question['options']}');
    }
  } catch (e) {
    print('Error: $e');
  }
}
```

## Step 3: Submit Onboarding Preferences

### Endpoint
```
POST /api/v1/onboarding/submit
```

### Request Body
```json
{
  "user_id": 1,
  "answers": {
    "speakers": [1, 3, 5],
    "bible_reading_preference": "Balanced",
    "teaching_style_preference": "Relatable",
    "environment_preference": "Contemporary"
  }
}
```

### Response
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "onboarding_completed": true,
    "bible_reading_preference": "Balanced",
    "teaching_style_preference": "Relatable", 
    "environment_preference": "Contemporary",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "preferred_speakers": [
      {
        "id": 1,
        "name": "Pastor John Smith",
        "title": "Senior Pastor",
        "bio": "Experienced pastor with 20 years of ministry...",
        "church_id": 1,
        "teaching_style": "Relatable",
        "bible_approach": "Balanced",
        "environment_style": "Contemporary"
      }
    ]
  },
  "recommended_speakers": [
    {
      "id": 2,
      "name": "Dr. Sarah Johnson", 
      "title": "Teaching Pastor",
      "bio": "Passionate about practical Bible application...",
      "church_id": 2,
      "teaching_style": "Relatable",
      "bible_approach": "Balanced",
      "environment_style": "Contemporary",
      "church": {
        "id": 2,
        "name": "Hope Fellowship",
        "denomination": "Non-denominational"
      }
    }
  ]
}
```

### Flutter Implementation Example

```dart
// Add to ApiService class
static Future<Map<String, dynamic>> submitOnboardingAnswers(int userId, Map<String, dynamic> answers) async {
  final response = await http.post(
    Uri.parse('$baseUrl/onboarding/submit'),
    headers: {
      'Content-Type': 'application/json',
    },
    body: jsonEncode({
      'user_id': userId,
      'answers': answers,
    }),
  );
  
  if (response.statusCode != 200) {
    throw Exception('Onboarding submission failed: ${response.statusCode} - ${response.body}');
  }
  
  return jsonDecode(response.body);
}

// Usage
void main() async {
  try {
    final onboardingResult = await ApiService.submitOnboardingAnswers(1, {
      'speakers': [1, 3, 5], // Array of speaker IDs
      'bible_reading_preference': 'BALANCED',
      'teaching_style_preference': 'RELATABLE',
      'environment_preference': 'CONTEMPORARY',
    });
    
    print('Onboarding completed!');
    print('User preferences saved: ${onboardingResult['user']}');
    print('Recommended speakers: ${onboardingResult['recommended_speakers']}');
  } catch (e) {
    print('Error: $e');
  }
}
```

## Complete Flutter Implementation Example

Here's a complete Flutter example showing the full flow:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class OnboardingFlow {
  static const String baseUrl = 'https://YOUR_CLOUD_RUN_URL/api/v1';
  
  // Step 1: Create user
  static Future<Map<String, dynamic>> createUser(Map<String, dynamic> userData) async {
    final response = await http.post(
      Uri.parse('$baseUrl/users/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(userData),
    );
    
    if (response.statusCode != 200) {
      throw Exception('User creation failed: ${response.statusCode} - ${response.body}');
    }
    
    return jsonDecode(response.body);
  }

  // Step 2: Get questions
  static Future<List<Map<String, dynamic>>> getQuestions() async {
    final response = await http.get(Uri.parse('$baseUrl/onboarding/questions'));
    
    if (response.statusCode != 200) {
      throw Exception('Failed to get questions: ${response.statusCode} - ${response.body}');
    }
    
    return List<Map<String, dynamic>>.from(jsonDecode(response.body));
  }

  // Step 3: Submit answers
  static Future<Map<String, dynamic>> submitAnswers(int userId, Map<String, dynamic> answers) async {
    final response = await http.post(
      Uri.parse('$baseUrl/onboarding/submit'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'user_id': userId,
        'answers': answers,
      }),
    );
    
    if (response.statusCode != 200) {
      throw Exception('Onboarding submission failed: ${response.statusCode} - ${response.body}');
    }
    
    return jsonDecode(response.body);
  }

  // Complete onboarding flow
  static Future<Map<String, dynamic>> completeOnboardingFlow(
    Map<String, dynamic> userData, 
    Map<String, dynamic> userAnswers
  ) async {
    try {
      // Step 1: Create user
      print('Creating user...');
      final user = await createUser(userData);
      print('User created: ${user['id']}');

      // Step 2: Get questions
      print('Getting onboarding questions...');
      final questions = await getQuestions();
      print('Questions loaded: ${questions.length}');

      // Step 3: Submit answers
      print('Submitting onboarding answers...');
      final result = await submitAnswers(user['id'], userAnswers);
      print('Onboarding completed!');

      return result;
    } catch (error) {
      print('Onboarding flow failed: $error');
      rethrow;
    }
  }
}

// Usage
void main() async {
  final userData = {
    'username': 'jane_doe',
    'email': 'jane@example.com',
    'password': 'secure_password_123',
    'first_name': 'Jane',
    'last_name': 'Doe',
  };

  final userAnswers = {
    'speakers': [1, 2, 3],
    'bible_reading_preference': 'MORE_APPLICATION',
    'teaching_style_preference': 'ACADEMIC',
    'environment_preference': 'TRADITIONAL',
  };

  try {
    final result = await OnboardingFlow.completeOnboardingFlow(userData, userAnswers);
    print('Onboarding successful!');
    print('User: ${result['user']}');
    print('Recommended speakers: ${result['recommended_speakers']}');
  } catch (error) {
    print('Onboarding failed: $error');
  }
}
```

## Flutter Dependencies

Add these dependencies to your `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  # Add other dependencies as needed
```

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid data)
- `404` - Not Found (user doesn't exist)
- `422` - Validation Error (invalid enum values)
- `500` - Internal Server Error

Always check the response status and handle errors appropriately:

```dart
Future<T> handleApiCall<T>(Future<http.Response> apiCall) async {
  try {
    final response = await apiCall;
    
    if (response.statusCode != 200) {
      final errorData = jsonDecode(response.body);
      throw Exception('API Error: ${errorData['detail'] ?? response.reasonPhrase}');
    }
    
    return jsonDecode(response.body);
  } catch (error) {
    print('API call failed: $error');
    rethrow;
  }
}
```

## Data Validation

### User Creation Requirements
- `username`: Required, unique string
- `email`: Required, valid email format, unique
- `password`: Required string
- `first_name`: Required string
- `last_name`: Required string

### Onboarding Answer Requirements
- `speakers`: Optional array of integers (speaker IDs)
- `bible_reading_preference`: Optional, must be one of: **"MORE_SCRIPTURE"**, **"MORE_APPLICATION"**, **"BALANCED"**
- `teaching_style_preference`: Optional, must be one of: **"ACADEMIC"**, **"RELATABLE"**, **"BALANCED"**
- `environment_preference`: Optional, must be one of: **"TRADITIONAL"**, **"CONTEMPORARY"**, **"BLENDED"**

### ⚠️ Important: Enum Value Mapping

The onboarding questions display user-friendly values, but the API expects specific enum values:

| Question Display Value | API Enum Value |
|------------------------|----------------|
| "More Scripture" | "MORE_SCRIPTURE" |
| "Life Application" | "MORE_APPLICATION" |
| "Balanced" | "BALANCED" |
| "Academic" | "ACADEMIC" |
| "Relatable" | "RELATABLE" |
| "Traditional" | "TRADITIONAL" |
| "Contemporary" | "CONTEMPORARY" |
| "Blended" | "BLENDED" |

**Always use the API enum values when submitting onboarding answers!**

## Next Steps

After completing onboarding, clients can:

1. **Get User Recommendations**: `GET /api/v1/onboarding/recommendations/{user_id}`
2. **Update Speaker Preferences**: `POST /api/v1/users/{user_id}/preferences/speakers`
3. **Browse Churches**: `GET /api/v1/churches/`
4. **Browse Speakers**: `GET /api/v1/speakers/`

This completes the user creation to onboarding preferences flow. The system will now have a complete user profile with preferences and can provide personalized recommendations.
