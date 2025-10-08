# CSV Data Loading Scripts

This directory contains scripts to load CSV data into the database with proper foreign key relationships.

## Files

- `load_csv_data.py` - Main script that safely updates existing data without clearing
- `test_data_loading.py` - Validation script for CSV data
- `load_data.sh` - One-command shell script for easy loading
- `churches_with_denominations.csv` - Churches data with proper denominations (40 churches)
- `speakers.csv` - Speakers data with church name references (41 speakers)

## Prerequisites

1. **Database Setup**: Ensure your database is running and accessible
2. **Dependencies**: Install required Python packages:
   ```bash
   pip install sqlalchemy psycopg2-binary
   ```
3. **CSV Files**: Ensure both CSV files are in the same directory as the scripts
4. **Database Configuration**: Set your DATABASE_URL using one of these methods:

### Database Configuration Options

**Option 1: Environment Variable (Recommended)**
```bash
export DATABASE_URL="postgresql://username:password@localhost:5432/your_database"
```

**Option 2: .env File**
```bash
# Copy the example file
cp env.example .env
# Edit .env with your database credentials
```

**Option 3: Direct in Code (Not Recommended)**
Edit `app/core/config.py` and update the DATABASE_URL

## Usage

### Quick Start

```bash
./load_data.sh
```

This will validate the CSV files and load the data safely.

### Manual Loading

```bash
python load_csv_data.py
```

This script **safely updates existing data** without clearing anything. It's safe to run on production databases.

### ⚠️ **Why Safe Mode?**

The database has foreign key constraints that would prevent clearing speakers and churches:

- `sermons` → `speakers.id`
- `user_speaker_preferences` → `speakers.id`
- `speaker_followers` → `speakers.id`
- `church_followers` → `churches.id`
- `user_sermon_preferences` → `sermons.id` (indirectly affected)

The safe script updates existing records instead of clearing them, preserving all user data and relationships.

## Data Loading Process

1. **Load Churches**: Updates existing or creates new churches from `churches_with_denominations.csv`
2. **Map Church Names to IDs**: Creates a mapping for foreign key relationships
3. **Load Speakers**: Updates existing or creates new speakers with proper `church_id` foreign keys

The script will:
- ✅ Update existing churches/speakers if they already exist
- ✅ Create new churches/speakers if they don't exist
- ✅ Preserve all user data, sermons, and relationships
- ✅ Handle foreign key relationships properly

## Data Mapping

### Churches
- **Required Fields**: `name`, `denomination`
- **JSON Fields**: `address`, `service_times`, `social_media`
- **Optional Fields**: `phone`, `email`, `website`, `founded_year`, `membership_count`

### Speakers
- **Required Fields**: `name`
- **Foreign Key**: `church_id` (mapped from `church_name`)
- **Enum Fields**: `teaching_style`, `bible_approach`, `environment_style`, `gender`
- **JSON Fields**: `social_media`, `speaking_topics`
- **Optional Fields**: `title`, `bio`, `email`, `phone`, `years_of_service`

## Error Handling

The scripts include comprehensive error handling:
- **JSON Parsing**: Gracefully handles malformed JSON fields
- **Enum Validation**: Validates enum values against schema definitions
- **Foreign Key Validation**: Warns about missing church references
- **Database Errors**: Rolls back transactions on errors

## Troubleshooting

### Common Issues

1. **Database Connection Error**:
   - Verify `DATABASE_URL` is correct
   - Ensure database server is running
   - Check network connectivity

2. **CSV File Not Found**:
   - Ensure CSV files are in the same directory
   - Check file names match exactly

3. **Foreign Key Errors**:
   - Verify church names in speakers CSV match church names in churches CSV
   - Check for typos or extra spaces in church names

4. **Enum Value Errors**:
   - Check that enum values in CSV match the schema definitions
   - Valid values are defined in the script constants

### Debugging

Enable verbose logging by setting `VERBOSE_LOGGING = True` in the config file.

## Data Verification

After loading, verify the data:

```sql
-- Check churches loaded
SELECT COUNT(*) FROM churches;

-- Check speakers loaded
SELECT COUNT(*) FROM speakers;

-- Check foreign key relationships
SELECT s.name, c.name as church_name 
FROM speakers s 
LEFT JOIN churches c ON s.church_id = c.id;

-- Check denominations
SELECT denomination, COUNT(*) 
FROM churches 
GROUP BY denomination;
```

## Notes

- The script clears existing data by default for a clean load
- Church names must match exactly between the two CSV files
- JSON fields are validated and parsed before insertion
- All timestamps are automatically set to current time
