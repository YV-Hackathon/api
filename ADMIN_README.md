# Database Admin Interface

This project includes a web-based admin interface for viewing and editing database records.

## Quick Start

## Quick Start

The admin interface is integrated into the main FastAPI application.

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Access the admin interface:**
   - Main API: http://localhost:8000
   - Admin Interface: http://localhost:8000/admin
   - **Login credentials:**
     - Username: `admin`
     - Password: `admin123`

## Features

The admin interface provides:

- **View Records**: Browse all records in each table
- **Create Records**: Add new churches, speakers, users, etc.
- **Edit Records**: Modify existing records
- **Delete Records**: Remove records from the database
- **Search & Filter**: Find specific records quickly
- **Relationships**: View related data (e.g., speakers for each church)

## Available Models

- **Churches**: Church information and details
- **Speakers**: Speaker profiles and preferences
- **Users**: User accounts and preferences
- **User Speaker Preferences**: User-speaker relationships
- **Onboarding Questions**: Dynamic onboarding questions

## Security

⚠️ **Important**: This admin interface provides full database access and currently has NO authentication. In production:
- Add authentication/authorization
- Use HTTPS
- Restrict access to authorized users only
- Consider IP whitelisting

## Troubleshooting

If you encounter issues:

1. **Database Connection**: Ensure your database is running and accessible
2. **Dependencies**: Make sure all requirements are installed
3. **Port Conflicts**: Change ports if 8000/8001 are in use
4. **Environment**: Check your `.env` file has correct database credentials
