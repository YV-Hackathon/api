# Church Management System - FastAPI

A modern, fast API for managing churches, speakers, and user onboarding built with FastAPI and PostgreSQL.

## Features

- **Churches Management**: CRUD operations for church data with filtering
- **Speakers Management**: Speaker profiles with church relationships and preferences
- **User Onboarding**: Dynamic onboarding flow with personalized recommendations
- **User Management**: User profiles with preferences and speaker recommendations
- **RESTful API**: Clean, documented API endpoints
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Type Safety**: Full Pydantic model validation

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL
- pip or poetry

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd fastapi-cms
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your database credentials
   ```

5. **Set up the database:**
   ```bash
   # Create a PostgreSQL database
   createdb cms_db
   
   # Update DATABASE_URL in .env file
   DATABASE_URL=postgresql://username:password@localhost:5432/cms_db
   ```

6. **Seed the database:**
   ```bash
   python seed_data.py
   ```

7. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:

- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc documentation**: `http://localhost:8000/redoc`
- **OpenAPI schema**: `http://localhost:8000/api/v1/openapi.json`

## API Endpoints

### Churches
- `GET /api/v1/churches/` - List all churches
- `GET /api/v1/churches/{church_id}` - Get church details with speakers
- `POST /api/v1/churches/` - Create a new church
- `PUT /api/v1/churches/{church_id}` - Update church
- `DELETE /api/v1/churches/{church_id}` - Delete church

### Speakers
- `GET /api/v1/speakers/` - List all speakers with filtering
- `GET /api/v1/speakers/{speaker_id}` - Get speaker details with church
- `POST /api/v1/speakers/` - Create a new speaker
- `PUT /api/v1/speakers/{speaker_id}` - Update speaker
- `DELETE /api/v1/speakers/{speaker_id}` - Delete speaker
- `GET /api/v1/speakers/church/{church_id}/speakers` - Get speakers by church

### Users
- `GET /api/v1/users/` - List all users
- `GET /api/v1/users/{user_id}` - Get user with preferences
- `POST /api/v1/users/` - Create a new user
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user
- `POST /api/v1/users/{user_id}/preferences/speakers` - Update speaker preferences

### Onboarding
- `GET /api/v1/onboarding/questions` - Get onboarding questions
- `POST /api/v1/onboarding/submit` - Submit onboarding answers
- `GET /api/v1/onboarding/recommendations/{user_id}` - Get user recommendations

## Data Models

### Church
- Basic info: name, denomination, description
- Contact: address, phone, email, website
- Details: founded year, membership count, service times
- Social media links
- Active status and sort order

### Speaker
- Basic info: name, title, bio, contact
- Preferences: teaching style, bible approach, environment style
- Speaking topics with categories
- Church relationship
- Recommendation status

### User
- Authentication: username, email, password
- Profile: first name, last name
- Onboarding preferences
- Speaker preferences

## Filtering and Query Parameters

### Churches
- `is_active`: Filter by active status
- `denomination`: Filter by denomination (partial match)
- `skip`, `limit`: Pagination

### Speakers
- `church_id`: Filter by church
- `is_recommended`: Filter by recommendation status
- `teaching_style`: Filter by teaching style
- `bible_approach`: Filter by bible approach
- `environment_style`: Filter by environment style
- `skip`, `limit`: Pagination

## Development

### Project Structure
```
fastapi-cms/
├── app/
│   ├── api/
│   │   └── api_v1/
│   │       ├── endpoints/
│   │       │   ├── churches.py
│   │       │   ├── speakers.py
│   │       │   ├── users.py
│   │       │   └── onboarding.py
│   │       └── api.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   ├── database.py
│   │   └── models.py
│   ├── models/
│   │   └── schemas.py
│   └── main.py
├── requirements.txt
├── seed_data.py
└── README.md
```

### Adding New Features

1. **New Models**: Add to `app/db/models.py` and `app/models/schemas.py`
2. **New Endpoints**: Create in `app/api/api_v1/endpoints/`
3. **Database Migrations**: Use Alembic for schema changes
4. **Tests**: Add tests in a `tests/` directory

### Database Migrations

This project uses Alembic for database migrations. See [MIGRATIONS.md](MIGRATIONS.md) for detailed documentation.

**Quick Start:**
```bash
# Apply all migrations
alembic upgrade head

# Create new migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Or use the helper script
python migrate.py up
python migrate.py create -m "Description of changes"
```

**Migration Commands:**
- `python migrate.py up` - Apply all pending migrations
- `python migrate.py down` - Rollback last migration
- `python migrate.py create -m "message"` - Create new migration
- `python migrate.py history` - Show migration history
- `python migrate.py current` - Show current status

## Environment Variables

```env
DATABASE_URL=postgresql://username:password@localhost:5432/cms_db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
