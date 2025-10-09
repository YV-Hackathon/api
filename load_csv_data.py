#!/usr/bin/env python3
"""
CSV data loading script that safely updates existing data.
This script will update existing records or create new ones without clearing any data.
Safe to run on production databases.

DATABASE CONFIGURATION:
The script uses the FastAPI app's database configuration. Set your database URL using:

1. Environment variable (recommended):
   export DATABASE_URL="postgresql://username:password@localhost:5432/your_database"
   python3 load_csv_data.py

2. Create a .env file in the project root:
   echo "DATABASE_URL=postgresql://username:password@localhost:5432/your_database" > .env

3. Update app/core/config.py directly (not recommended for production)
"""

import csv
import json
import sys
import os
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal, engine
from app.db.models import Church, Speaker
from app.models.schemas import TeachingStyle, BibleApproach, EnvironmentStyle, Gender, SpeakingTopic, TopicCategory

def parse_json_field(json_str: str) -> Optional[dict]:
    """Parse JSON string field, return None if empty or invalid."""
    if not json_str or json_str.strip() == "":
        return None
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse JSON field: {json_str}")
        return None

def parse_enum_field(enum_class, value: str) -> Optional[object]:
    """Parse enum field, return None if empty or invalid."""
    if not value or value.strip() == "":
        return None
    try:
        return enum_class(value)
    except ValueError:
        print(f"Warning: Invalid enum value '{value}' for {enum_class.__name__}")
        return None

def parse_speaking_topics(json_str: str) -> List[SpeakingTopic]:
    """Parse speaking topics from JSON string, return empty list if empty or invalid."""
    if not json_str or json_str.strip() == "":
        return []
    
    try:
        topics_data = json.loads(json_str)
        if not isinstance(topics_data, list):
            print(f"Warning: speaking_topics should be a list, got {type(topics_data)}")
            return []
        
        speaking_topics = []
        for topic_data in topics_data:
            if isinstance(topic_data, dict):
                # Handle both old format (string) and new format (object)
                if isinstance(topic_data.get('name'), str):
                    name = topic_data['name']
                    description = topic_data.get('description')
                    category_str = topic_data.get('category', 'OTHER')
                    
                    try:
                        category = TopicCategory(category_str)
                        speaking_topics.append(SpeakingTopic(
                            name=name,
                            description=description,
                            category=category
                        ))
                    except ValueError:
                        print(f"Warning: Invalid topic category '{category_str}', using OTHER")
                        speaking_topics.append(SpeakingTopic(
                            name=name,
                            description=description,
                            category=TopicCategory.OTHER
                        ))
                else:
                    print(f"Warning: Invalid topic data format: {topic_data}")
            else:
                print(f"Warning: Topic data should be a dict, got {type(topic_data)}")
        
        return speaking_topics
    except json.JSONDecodeError:
        print(f"Warning: Could not parse speaking_topics JSON: {json_str}")
        return []

def load_churches_safe(db: Session, csv_file: str) -> Dict[str, int]:
    """Load churches from CSV, updating existing or creating new ones."""
    church_name_to_id = {}
    
    print("Loading churches (safe mode - updating existing)...")
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Parse JSON fields
                address = parse_json_field(row.get('address', ''))
                service_times = parse_json_field(row.get('service_times', ''))
                social_media = parse_json_field(row.get('social_media', ''))
                
                # Parse integer fields
                founded_year = int(row['founded_year']) if row.get('founded_year') else None
                membership_count = int(row['membership_count']) if row.get('membership_count') else None
                sort_order = int(row['sort_order']) if row.get('sort_order') else 0
                
                # Parse boolean field
                is_active = row.get('is_active', 'true').lower() == 'true'
                
                # Check if church already exists
                existing_church = db.query(Church).filter(Church.name == row['name']).first()
                
                if existing_church:
                    # Update existing church
                    existing_church.denomination = row['denomination']
                    existing_church.description = row.get('description', '')
                    existing_church.address = address
                    existing_church.phone = row.get('phone', '') or None
                    existing_church.email = row.get('email', '') or None
                    existing_church.website = row.get('website', '') or None
                    existing_church.founded_year = founded_year
                    existing_church.membership_count = membership_count
                    existing_church.service_times = service_times
                    existing_church.social_media = social_media
                    existing_church.is_active = is_active
                    existing_church.sort_order = sort_order
                    
                    church_id = existing_church.id
                    church_name = existing_church.name
                    print(f"  Updated church: {church_name} (ID: {church_id})")
                else:
                    # Create new church
                    church = Church(
                        name=row['name'],
                        denomination=row['denomination'],
                        description=row.get('description', ''),
                        address=address,
                        phone=row.get('phone', '') or None,
                        email=row.get('email', '') or None,
                        website=row.get('website', '') or None,
                        founded_year=founded_year,
                        membership_count=membership_count,
                        service_times=service_times,
                        social_media=social_media,
                        is_active=is_active,
                        sort_order=sort_order
                    )
                    
                    db.add(church)
                    db.flush()  # Flush to get the ID
                    church_id = church.id
                    church_name = church.name
                    print(f"  Created church: {church_name} (ID: {church_id})")
                
                church_name_to_id[church_name] = church_id
                
            except Exception as e:
                print(f"Error loading church at row {row_num}: {e}")
                print(f"Row data: {row}")
                continue
    
    try:
        db.commit()
        print(f"Successfully processed {len(church_name_to_id)} churches")
    except IntegrityError as e:
        db.rollback()
        print(f"Error committing churches: {e}")
        return {}
    
    return church_name_to_id

def load_speakers_safe(db: Session, csv_file: str, church_name_to_id: Dict[str, int]) -> int:
    """Load speakers from CSV, updating existing or creating new ones."""
    speakers_processed = 0
    
    print("Loading speakers (safe mode - updating existing)...")
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Parse JSON fields
                social_media = parse_json_field(row.get('social_media', ''))
                speaking_topics = parse_speaking_topics(row.get('speaking_topics', ''))
                
                # Parse enum fields
                teaching_style = parse_enum_field(TeachingStyle, row.get('teaching_style', ''))
                bible_approach = parse_enum_field(BibleApproach, row.get('bible_approach', ''))
                environment_style = parse_enum_field(EnvironmentStyle, row.get('environment_style', ''))
                gender = parse_enum_field(Gender, row.get('gender', ''))
                
                # Parse integer fields
                years_of_service = int(row['years_of_service']) if row.get('years_of_service') else None
                sort_order = int(row['sort_order']) if row.get('sort_order') else 0
                
                # Parse boolean field
                is_recommended = row.get('is_recommended', 'false').lower() == 'true'
                
                # Get church_id from church_name
                church_name = row.get('church_name', '')
                church_id = church_name_to_id.get(church_name)
                
                if not church_id and church_name:
                    print(f"Warning: Church '{church_name}' not found for speaker '{row['name']}'")
                
                # Check if speaker already exists
                existing_speaker = db.query(Speaker).filter(Speaker.name == row['name']).first()
                
                if existing_speaker:
                    # Update existing speaker
                    existing_speaker.title = row.get('title', '')
                    existing_speaker.bio = row.get('bio', '') or None
                    existing_speaker.email = row.get('email', '') or None
                    existing_speaker.phone = row.get('phone', '') or None
                    existing_speaker.years_of_service = years_of_service
                    existing_speaker.social_media = social_media
                    existing_speaker.speaking_topics = speaking_topics
                    existing_speaker.sort_order = sort_order
                    existing_speaker.teaching_style = teaching_style or TeachingStyle.WARM_AND_CONVERSATIONAL
                    existing_speaker.bible_approach = bible_approach or BibleApproach.BALANCED
                    existing_speaker.environment_style = environment_style or EnvironmentStyle.BLENDED
                    existing_speaker.gender = gender
                    existing_speaker.is_recommended = is_recommended
                    existing_speaker.church_id = church_id
                    
                    print(f"  Updated speaker: {existing_speaker.name} (Church ID: {church_id})")
                else:
                    # Create new speaker
                    speaker = Speaker(
                        name=row['name'],
                        title=row.get('title', ''),
                        bio=row.get('bio', '') or None,
                        email=row.get('email', '') or None,
                        phone=row.get('phone', '') or None,
                        years_of_service=years_of_service,
                        social_media=social_media,
                        speaking_topics=speaking_topics,
                        sort_order=sort_order,
                        teaching_style=teaching_style or TeachingStyle.WARM_AND_CONVERSATIONAL,
                        bible_approach=bible_approach or BibleApproach.BALANCED,
                        environment_style=environment_style or EnvironmentStyle.BLENDED,
                        gender=gender,
                        is_recommended=is_recommended,
                        church_id=church_id
                    )
                    
                    db.add(speaker)
                    print(f"  Created speaker: {speaker.name} (Church ID: {church_id})")
                
                speakers_processed += 1
                
            except Exception as e:
                print(f"Error loading speaker at row {row_num}: {e}")
                print(f"Row data: {row}")
                continue
    
    try:
        db.commit()
        print(f"Successfully processed {speakers_processed} speakers")
    except IntegrityError as e:
        db.rollback()
        print(f"Error committing speakers: {e}")
        return 0
    
    return speakers_processed

def main():
    """Main function to safely load CSV data into database."""
    # File paths
    churches_csv = "churches_with_denominations.csv"
    speakers_csv = "speakers.csv"
    
    # Check if files exist
    if not os.path.exists(churches_csv):
        print(f"Error: {churches_csv} not found")
        return 1
    
    if not os.path.exists(speakers_csv):
        print(f"Error: {speakers_csv} not found")
        return 1
    
    # Check database configuration
    from app.core.config import settings
    print(f"Using database: {settings.DATABASE_URL}")
    
    # Test database connection
    try:
        # Create database session
        db = SessionLocal()
        # Test the connection
        db.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nTo fix this, set your DATABASE_URL using one of these methods:")
        print("1. Environment variable: export DATABASE_URL='postgresql://user:pass@host:port/db'")
        print("2. Create .env file: echo 'DATABASE_URL=postgresql://user:pass@host:port/db' > .env")
        print("3. Update app/core/config.py (not recommended for production)")
        return 1
    
    try:
        # Load churches first (safe mode)
        church_name_to_id = load_churches_safe(db, churches_csv)
        
        if not church_name_to_id:
            print("No churches processed, aborting speaker loading")
            return 1
        
        # Load speakers with church relationships (safe mode)
        speakers_processed = load_speakers_safe(db, speakers_csv, church_name_to_id)
        
        print(f"\nData loading completed safely!")
        print(f"Churches processed: {len(church_name_to_id)}")
        print(f"Speakers processed: {speakers_processed}")
        print("Note: Existing data was updated, not cleared")
        
        return 0
        
    except Exception as e:
        print(f"Error during data loading: {e}")
        db.rollback()
        return 1
    
    finally:
        db.close()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
