# Database Migrations Guide

This project uses Alembic for database migrations, providing version control for your database schema.

## Quick Start

### Apply Migrations
```bash
# Apply all pending migrations
alembic upgrade head

# Or use the helper script
python migrate.py up
```

### Create New Migration
```bash
# Create a new migration after making model changes
alembic revision --autogenerate -m "Description of changes"

# Or use the helper script
python migrate.py create -m "Description of changes"
```

## Migration Commands

### Using Alembic Directly

```bash
# Show current migration status
alembic current

# Show migration history
alembic history

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific migration
alembic downgrade <revision_id>

# Create new migration
alembic revision --autogenerate -m "Description"

# Show help
alembic --help
```

### Using the Migration Helper Script

```bash
# Apply migrations
python migrate.py up

# Rollback last migration
python migrate.py down

# Create new migration
python migrate.py create -m "Add new table"

# Show migration history
python migrate.py history

# Show current status
python migrate.py current

# Reset database (WARNING: destroys all data)
python migrate.py reset
```

## Development Workflow

### 1. Making Schema Changes

1. **Modify Models**: Update your SQLAlchemy models in `app/db/models.py`
2. **Create Migration**: Run `alembic revision --autogenerate -m "Description"`
3. **Review Migration**: Check the generated migration file in `alembic/versions/`
4. **Apply Migration**: Run `alembic upgrade head`
5. **Test Changes**: Verify your application works correctly

### 2. Example: Adding a New Column

```python
# In app/db/models.py
class Church(Base):
    __tablename__ = "churches"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    # ... existing columns ...
    
    # New column
    phone_extension = Column(String(10))  # Add this line
```

```bash
# Create migration
alembic revision --autogenerate -m "Add phone_extension to churches"

# Apply migration
alembic upgrade head
```

### 3. Example: Creating a New Table

```python
# In app/db/models.py
class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    event_date = Column(DateTime(timezone=True))
    church_id = Column(Integer, ForeignKey("churches.id"))
    
    # Relationships
    church = relationship("Church")
```

```bash
# Create migration
alembic revision --autogenerate -m "Add events table"

# Apply migration
alembic upgrade head
```

## Production Deployment

### 1. Before Deployment

```bash
# Check current migration status
alembic current

# Show pending migrations
alembic history --verbose

# Test migrations on staging environment first
```

### 2. During Deployment

```bash
# Apply migrations
alembic upgrade head

# Verify migration was applied
alembic current
```

### 3. Rollback if Needed

```bash
# Rollback to previous migration
alembic downgrade -1

# Or rollback to specific migration
alembic downgrade <revision_id>
```

## Migration Files

- **Location**: `alembic/versions/`
- **Naming**: `{revision_id}_{description}.py`
- **Format**: Each migration has `upgrade()` and `downgrade()` functions

### Example Migration File

```python
"""Add phone_extension to churches

Revision ID: abc123def456
Revises: 88681f158517
Create Date: 2025-09-29 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123def456'
down_revision = '88681f158517'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('churches', sa.Column('phone_extension', sa.String(10), nullable=True))

def downgrade():
    op.drop_column('churches', 'phone_extension')
```

## Best Practices

### 1. Always Review Generated Migrations
- Check the generated migration file before applying
- Ensure the changes match your intentions
- Test migrations on a copy of production data

### 2. Use Descriptive Migration Messages
```bash
# Good
alembic revision --autogenerate -m "Add user preferences table"

# Bad
alembic revision --autogenerate -m "Update"
```

### 3. Test Migrations
- Always test migrations on development/staging first
- Test both upgrade and downgrade paths
- Verify data integrity after migrations

### 4. Backup Before Major Changes
- Always backup your database before applying migrations
- Especially important for data migrations or schema changes

### 5. Coordinate with Team
- Commit migration files to version control
- Communicate about breaking changes
- Use feature branches for migration development

## Troubleshooting

### Migration Conflicts
If you have migration conflicts:
```bash
# Check current status
alembic current

# Show history
alembic history

# Merge branches if needed
alembic merge -m "Merge branches" <revision1> <revision2>
```

### Failed Migration
If a migration fails:
```bash
# Check the error message
# Fix the issue in the migration file
# Try again
alembic upgrade head
```

### Database Out of Sync
If your database is out of sync:
```bash
# Mark current state as specific revision
alembic stamp <revision_id>

# Then apply remaining migrations
alembic upgrade head
```

## Docker Integration

### Running Migrations in Docker

```bash
# Apply migrations in running container
docker exec -it <container_name> alembic upgrade head

# Or with podman
podman exec <container_name> alembic upgrade head
```

### Adding Migration to Dockerfile

```dockerfile
# Add to your Dockerfile
COPY alembic.ini .
COPY alembic/ ./alembic/

# Run migrations on container start
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

## Environment Variables

Make sure these environment variables are set:
- `DATABASE_URL`: PostgreSQL connection string
- `PYTHONPATH`: Should include the app directory

## Files Structure

```
fastapi-cms/
├── alembic/
│   ├── versions/
│   │   └── 88681f158517_initial_migration.py
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── migrate.py
└── app/
    └── db/
        ├── database.py
        └── models.py
```

This migration system provides a robust, version-controlled way to manage your database schema changes safely and efficiently.
