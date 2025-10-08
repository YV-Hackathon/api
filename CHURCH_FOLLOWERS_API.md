# Church Followers API Documentation

This document describes the church followers functionality that allows users to follow churches and manage their church subscriptions.

## Database Model

### ChurchFollowers Table
- `id` (Primary Key): Unique identifier
- `church_id` (Foreign Key): References churches.id
- `user_id` (Foreign Key): References users.id  
- `created_at` (DateTime): When the follow relationship was created
- Unique constraint on (church_id, user_id) to prevent duplicate follows

## API Endpoints

All endpoints are prefixed with `/api/v1/church-followers`

### 1. Get All Church Followers
**GET** `/`

Query Parameters:
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum number of records to return (default: 100, max: 1000)
- `church_id` (int, optional): Filter by church ID
- `user_id` (int, optional): Filter by user ID

Response: List of ChurchFollowersWithDetails objects

### 2. Get Specific Church Follower
**GET** `/{follow_id}`

Response: ChurchFollowersWithDetails object

### 3. Follow a Church
**POST** `/`

Request Body:
```json
{
  "church_id": 1,
  "user_id": 2
}
```

Response: ChurchFollowers object

### 4. Unfollow a Church (by follow ID)
**DELETE** `/{follow_id}`

Response: Success message

### 5. Unfollow a Church (by church and user IDs)
**DELETE** `/church/{church_id}/user/{user_id}`

Response: Success message

### 6. Get User's Followed Churches
**GET** `/user/{user_id}/churches`

Query Parameters:
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum number of records to return (default: 100, max: 1000)

Response: List of Church objects

### 7. Get Church Followers
**GET** `/church/{church_id}/followers`

Query Parameters:
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum number of records to return (default: 100, max: 1000)

Response: List of User objects

### 8. Check Follow Status
**GET** `/user/{user_id}/church/{church_id}/status`

Response:
```json
{
  "is_following": true,
  "follow_id": 123
}
```

## Data Models

### ChurchFollowersBase
```json
{
  "church_id": 1,
  "user_id": 2
}
```

### ChurchFollowers
```json
{
  "id": 1,
  "church_id": 1,
  "user_id": 2,
  "created_at": "2025-01-27T18:00:00Z"
}
```

### ChurchFollowersWithDetails
```json
{
  "id": 1,
  "church_id": 1,
  "user_id": 2,
  "created_at": "2025-01-27T18:00:00Z",
  "church": { /* Church object */ },
  "user": { /* User object */ }
}
```

## Error Handling

- **404 Not Found**: When church, user, or follow relationship doesn't exist
- **400 Bad Request**: When trying to follow a church that's already being followed
- **422 Unprocessable Entity**: When request validation fails

## Usage Examples

### Follow a Church
```bash
curl -X POST "http://localhost:8000/api/v1/church-followers/" \
  -H "Content-Type: application/json" \
  -d '{"church_id": 1, "user_id": 2}'
```

### Get User's Followed Churches
```bash
curl "http://localhost:8000/api/v1/church-followers/user/2/churches"
```

### Check if User is Following a Church
```bash
curl "http://localhost:8000/api/v1/church-followers/user/2/church/1/status"
```

### Unfollow a Church
```bash
curl -X DELETE "http://localhost:8000/api/v1/church-followers/church/1/user/2"
```

## Testing

Run the test script to verify all endpoints work correctly:

```bash
python test_church_followers.py
```

Make sure the FastAPI server is running on `http://localhost:8000` before running the tests.
