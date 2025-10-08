# Speaker Followers API Documentation

This document describes the speaker followers functionality that allows users to follow speakers and manage their speaker subscriptions.

## Database Model

### SpeakerFollowers Table
- `id` (Primary Key): Unique identifier
- `speaker_id` (Foreign Key): References speakers.id
- `user_id` (Foreign Key): References users.id  
- `created_at` (DateTime): When the follow relationship was created
- Unique constraint on (speaker_id, user_id) to prevent duplicate follows

## API Endpoints

All endpoints are prefixed with `/api/v1/speaker-followers`

### 1. Get All Speaker Followers
**GET** `/`

Query Parameters:
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum number of records to return (default: 100, max: 1000)
- `speaker_id` (int, optional): Filter by speaker ID
- `user_id` (int, optional): Filter by user ID

Response: List of SpeakerFollowersWithDetails objects

### 2. Get Specific Speaker Follower
**GET** `/{follow_id}`

Response: SpeakerFollowersWithDetails object

### 3. Follow a Speaker
**POST** `/`

Request Body:
```json
{
  "speaker_id": 1,
  "user_id": 2
}
```

Response: SpeakerFollowers object

### 4. Unfollow a Speaker (by follow ID)
**DELETE** `/{follow_id}`

Response: Success message

### 5. Unfollow a Speaker (by speaker and user IDs)
**DELETE** `/speaker/{speaker_id}/user/{user_id}`

Response: Success message

### 6. Get User's Followed Speakers
**GET** `/user/{user_id}/speakers`

Query Parameters:
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum number of records to return (default: 100, max: 1000)

Response: List of Speaker objects

### 7. Get Speaker Followers
**GET** `/speaker/{speaker_id}/followers`

Query Parameters:
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum number of records to return (default: 100, max: 1000)

Response: List of User objects

### 8. Check Follow Status
**GET** `/user/{user_id}/speaker/{speaker_id}/status`

Response:
```json
{
  "is_following": true,
  "follow_id": 123
}
```

## Error Responses

- `400 Bad Request`: User is already following this speaker
- `404 Not Found`: Speaker, user, or follow relationship not found

## Example Usage

### Follow a Speaker
```bash
curl -X POST "http://localhost:8000/api/v1/speaker-followers/" \
  -H "Content-Type: application/json" \
  -d '{
    "speaker_id": 1,
    "user_id": 2
  }'
```

### Get User's Followed Speakers
```bash
curl -X GET "http://localhost:8000/api/v1/speaker-followers/user/2/speakers"
```

### Check Follow Status
```bash
curl -X GET "http://localhost:8000/api/v1/speaker-followers/user/2/speaker/1/status"
```

### Unfollow a Speaker
```bash
curl -X DELETE "http://localhost:8000/api/v1/speaker-followers/speaker/1/user/2"
```
