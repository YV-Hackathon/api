# Sermon Preferences API

This API allows users to provide thumbs up/down feedback on recommended sermons.

## Endpoints

### 1. Create a Single Sermon Preference

**POST** `/api/v1/sermon-preferences/`

Create a thumbs up or thumbs down preference for a specific sermon.

**Request Body:**
```json
{
  "user_id": 1,
  "sermon_id": 5,
  "preference": "thumbs_up"
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "sermon_id": 5,
  "preference": "thumbs_up",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": null
}
```

### 2. Create Multiple Sermon Preferences (Batch)

**POST** `/api/v1/sermon-preferences/batch`

Create multiple sermon preferences in a single request. This is ideal for when a user provides feedback on all 10 recommended sermons at once.

**Request Body:**
```json
{
  "user_id": 1,
  "preferences": [
    {"sermon_id": 1, "preference": "thumbs_up"},
    {"sermon_id": 2, "preference": "thumbs_down"},
    {"sermon_id": 3, "preference": "thumbs_up"},
    {"sermon_id": 4, "preference": "thumbs_up"},
    {"sermon_id": 5, "preference": "thumbs_down"},
    {"sermon_id": 6, "preference": "thumbs_up"},
    {"sermon_id": 7, "preference": "thumbs_down"},
    {"sermon_id": 8, "preference": "thumbs_up"},
    {"sermon_id": 9, "preference": "thumbs_up"},
    {"sermon_id": 10, "preference": "thumbs_down"}
  ]
}
```

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "sermon_id": 1,
    "preference": "thumbs_up",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": null
  },
  {
    "id": 2,
    "user_id": 1,
    "sermon_id": 2,
    "preference": "thumbs_down",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": null
  }
  // ... more preferences
]
```

### 3. Get User's Sermon Preferences

**GET** `/api/v1/sermon-preferences/user/{user_id}`

Get all sermon preferences for a specific user.

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100, max: 1000)
- `preference` (optional): Filter by preference type ("thumbs_up" or "thumbs_down")

**Example:**
```
GET /api/v1/sermon-preferences/user/1?preference=thumbs_up&limit=10
```

### 4. Get Sermon's Preferences

**GET** `/api/v1/sermon-preferences/sermon/{sermon_id}`

Get all preferences for a specific sermon.

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100, max: 1000)
- `preference` (optional): Filter by preference type ("thumbs_up" or "thumbs_down")

### 5. Get Specific User-Sermon Preference

**GET** `/api/v1/sermon-preferences/user/{user_id}/sermon/{sermon_id}`

Get a specific user's preference for a specific sermon.

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "sermon_id": 5,
  "preference": "thumbs_up",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": null,
  "sermon": {
    "id": 5,
    "title": "The Power of Faith",
    "description": "A sermon about faith",
    "gcs_url": "https://storage.googleapis.com/bucket/sermon5.mp4",
    "speaker_id": 2,
    "created_at": "2024-01-10T10:00:00Z",
    "updated_at": null
  },
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "onboarding_completed": true,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": null
  }
}
```

### 6. Update Sermon Preference

**PUT** `/api/v1/sermon-preferences/{preference_id}`

Update an existing sermon preference.

**Request Body:**
```json
{
  "preference": "thumbs_down"
}
```

### 7. Delete Sermon Preference

**DELETE** `/api/v1/sermon-preferences/{preference_id}`

Delete a sermon preference.

**Response:**
```json
{
  "message": "Sermon preference deleted successfully"
}
```

## Usage Example

Here's how you might use this API in a frontend application:

```javascript
// Submit preferences for 10 recommended sermons
async function submitSermonPreferences(userId, sermonPreferences) {
  const response = await fetch('/api/v1/sermon-preferences/batch', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      preferences: sermonPreferences.map(sermon => ({
        sermon_id: sermon.id,
        preference: sermon.userPreference // "thumbs_up" or "thumbs_down"
      }))
    })
  });
  
  if (!response.ok) {
    throw new Error('Failed to submit preferences');
  }
  
  return await response.json();
}

// Example usage
const sermonPreferences = [
  { id: 1, userPreference: "thumbs_up" },
  { id: 2, userPreference: "thumbs_down" },
  { id: 3, userPreference: "thumbs_up" },
  // ... more sermons
];

submitSermonPreferences(1, sermonPreferences)
  .then(result => console.log('Preferences saved:', result))
  .catch(error => console.error('Error:', error));
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid data)
- `404`: Not Found (user, sermon, or preference not found)
- `422`: Validation Error (invalid preference value)

## Database Schema

The `user_sermon_preferences` table includes:

- `id`: Primary key
- `user_id`: Foreign key to users table
- `sermon_id`: Foreign key to sermons table
- `preference`: Either "thumbs_up" or "thumbs_down"
- `created_at`: Timestamp when preference was created
- `updated_at`: Timestamp when preference was last updated
- Unique constraint on (user_id, sermon_id) to prevent duplicate preferences
