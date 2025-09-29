#!/usr/bin/env python3
"""
Seed data script for the Church Management System FastAPI application.
This script populates the database with sample churches and speakers.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db import models
from app.models.schemas import (
    Address, ServiceTimes, SocialMedia, SpeakingTopic,
    TeachingStyle, BibleApproach, EnvironmentStyle, TopicCategory
)

# Sample church data
churches_data = [
    {
        "name": "Grace Community Church",
        "denomination": "Baptist",
        "description": "A welcoming community focused on faith, fellowship, and service to others. We believe in the power of God's love to transform lives.",
        "address": {
            "street": "123 Main Street",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62701",
            "country": "USA"
        },
        "phone": "(217) 555-0123",
        "email": "info@gracecommunity.org",
        "website": "https://gracecommunity.org",
        "founded_year": 1985,
        "membership_count": 450,
        "service_times": {
            "sunday": ["9:00 AM", "11:00 AM"],
            "wednesday": ["7:00 PM"]
        },
        "social_media": {
            "facebook": "https://facebook.com/gracecommunity",
            "instagram": "https://instagram.com/gracecommunity",
            "twitter": "https://twitter.com/gracecommunity"
        },
        "is_active": True,
        "sort_order": 1
    },
    {
        "name": "First Presbyterian Church",
        "denomination": "Presbyterian",
        "description": "A historic church serving the community for over 150 years. We are committed to traditional worship and modern outreach.",
        "address": {
            "street": "456 Oak Avenue",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62702",
            "country": "USA"
        },
        "phone": "(217) 555-0456",
        "email": "office@firstpres.org",
        "website": "https://firstpres.org",
        "founded_year": 1872,
        "membership_count": 320,
        "service_times": {
            "sunday": ["8:30 AM", "10:30 AM"],
            "wednesday": ["6:30 PM"]
        },
        "social_media": {
            "facebook": "https://facebook.com/firstpres",
            "instagram": "https://instagram.com/firstpres"
        },
        "is_active": True,
        "sort_order": 2
    },
    {
        "name": "New Life Fellowship",
        "denomination": "Non-denominational",
        "description": "A contemporary church focused on authentic relationships and practical biblical teaching. All are welcome here.",
        "address": {
            "street": "789 Pine Street",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62703",
            "country": "USA"
        },
        "phone": "(217) 555-0789",
        "email": "hello@newlifefellowship.org",
        "website": "https://newlifefellowship.org",
        "founded_year": 2005,
        "membership_count": 280,
        "service_times": {
            "sunday": ["9:30 AM", "11:30 AM"],
            "saturday": ["6:00 PM"]
        },
        "social_media": {
            "facebook": "https://facebook.com/newlifefellowship",
            "instagram": "https://instagram.com/newlifefellowship",
            "youtube": "https://youtube.com/newlifefellowship"
        },
        "is_active": True,
        "sort_order": 3
    }
]

# Sample speaker data
speakers_data = [
    {
        "name": "Pastor John Smith",
        "title": "Senior Pastor",
        "bio": "Pastor John has been serving in ministry for over 20 years. He holds a Master of Divinity from Trinity Seminary and is passionate about biblical teaching and community outreach.",
        "email": "john.smith@gracecommunity.org",
        "phone": "(217) 555-0124",
        "years_of_service": 8,
        "social_media": {
            "facebook": "https://facebook.com/pastorjohnsmith",
            "twitter": "https://twitter.com/pastorjohnsmith"
        },
        "speaking_topics": [
            {
                "name": "Faith and Doubt",
                "description": "Exploring the relationship between faith and doubt in the Christian journey",
                "category": "preaching"
            },
            {
                "name": "Community Building",
                "description": "Building authentic Christian community in the modern world",
                "category": "leadership"
            },
            {
                "name": "Prayer Life",
                "description": "Developing a deeper and more meaningful prayer life",
                "category": "prayer"
            }
        ],
        "sort_order": 1,
        "teaching_style": TeachingStyle.BALANCED,
        "bible_approach": BibleApproach.BALANCED,
        "environment_style": EnvironmentStyle.BLENDED,
        "is_recommended": True,
        "church_index": 0
    },
    {
        "name": "Rev. Sarah Johnson",
        "title": "Associate Pastor",
        "bio": "Rev. Sarah brings a fresh perspective to ministry with her background in counseling and youth work. She has a heart for social justice and community service.",
        "email": "sarah.johnson@gracecommunity.org",
        "phone": "(217) 555-0125",
        "years_of_service": 5,
        "social_media": {
            "instagram": "https://instagram.com/revsarahjohnson",
            "twitter": "https://twitter.com/revsarahjohnson"
        },
        "speaking_topics": [
            {
                "name": "Youth Ministry",
                "description": "Engaging and ministering to the next generation",
                "category": "youth"
            },
            {
                "name": "Mental Health and Faith",
                "description": "Addressing mental health issues from a Christian perspective",
                "category": "counseling"
            },
            {
                "name": "Social Justice",
                "description": "Living out faith through social action and justice",
                "category": "evangelism"
            }
        ],
        "sort_order": 2,
        "teaching_style": TeachingStyle.RELATABLE,
        "bible_approach": BibleApproach.LIFE_APPLICATION,
        "environment_style": EnvironmentStyle.CONTEMPORARY,
        "is_recommended": True,
        "church_index": 0
    },
    {
        "name": "Dr. Michael Chen",
        "title": "Senior Pastor",
        "bio": "Dr. Chen has served as Senior Pastor for 15 years and holds a Ph.D. in Theology. He is known for his scholarly approach to biblical interpretation and practical application.",
        "email": "michael.chen@firstpres.org",
        "phone": "(217) 555-0457",
        "years_of_service": 15,
        "social_media": {
            "facebook": "https://facebook.com/drmichaelchen",
            "linkedin": "https://linkedin.com/in/drmichaelchen"
        },
        "speaking_topics": [
            {
                "name": "Biblical Theology",
                "description": "Deep dive into biblical theology and systematic theology",
                "category": "teaching"
            },
            {
                "name": "Church History",
                "description": "Understanding the historical development of Christian doctrine",
                "category": "teaching"
            },
            {
                "name": "Pastoral Leadership",
                "description": "Leading and shepherding a congregation effectively",
                "category": "leadership"
            }
        ],
        "sort_order": 3,
        "teaching_style": TeachingStyle.ACADEMIC,
        "bible_approach": BibleApproach.MORE_SCRIPTURE,
        "environment_style": EnvironmentStyle.TRADITIONAL,
        "is_recommended": True,
        "church_index": 1
    },
    {
        "name": "Pastor Lisa Williams",
        "title": "Lead Pastor",
        "bio": "Pastor Lisa is a dynamic speaker and leader who founded New Life Fellowship. She has a gift for making complex biblical concepts accessible to everyone.",
        "email": "lisa.williams@newlifefellowship.org",
        "phone": "(217) 555-0790",
        "years_of_service": 18,
        "social_media": {
            "facebook": "https://facebook.com/pastorlisawilliams",
            "instagram": "https://instagram.com/pastorlisawilliams",
            "youtube": "https://youtube.com/pastorlisawilliams"
        },
        "speaking_topics": [
            {
                "name": "Contemporary Worship",
                "description": "Creating meaningful worship experiences for today's church",
                "category": "worship"
            },
            {
                "name": "Marriage and Family",
                "description": "Building strong Christian marriages and families",
                "category": "marriage"
            },
            {
                "name": "Personal Growth",
                "description": "Growing in faith and character as a Christian",
                "category": "teaching"
            }
        ],
        "sort_order": 4,
        "teaching_style": TeachingStyle.RELATABLE,
        "bible_approach": BibleApproach.LIFE_APPLICATION,
        "environment_style": EnvironmentStyle.CONTEMPORARY,
        "is_recommended": True,
        "church_index": 2
    }
]

def seed_database():
    """Seed the database with sample data"""
    print("🚀 Starting database seeding...")
    
    # Note: Database tables should be created using Alembic migrations
    # Run 'alembic upgrade head' before seeding data
    
    db = SessionLocal()
    try:
        # Check for existing data
        existing_churches = db.query(models.Church).count()
        existing_speakers = db.query(models.Speaker).count()
        
        if existing_churches > 0 or existing_speakers > 0:
            print(f"⚠️  Database already contains {existing_churches} churches and {existing_speakers} speakers")
            response = input("Do you want to clear existing data and reseed? (y/N): ")
            if response.lower() != 'y':
                print("❌ Seeding cancelled")
                return
            
            # Clear existing data
            db.query(models.UserSpeakerPreference).delete()
            db.query(models.Speaker).delete()
            db.query(models.Church).delete()
            db.commit()
            print("🗑️  Cleared existing data")
        
        # Create churches
        print("📊 Creating churches...")
        created_churches = []
        for church_data in churches_data:
            church = models.Church(**church_data)
            db.add(church)
            db.commit()
            db.refresh(church)
            created_churches.append(church)
            print(f"✅ Created church: {church.name}")
        
        # Create speakers
        print("👥 Creating speakers...")
        for speaker_data in speakers_data:
            # Remove church_index from speaker data
            church_index = speaker_data.pop('church_index')
            church_id = created_churches[church_index].id
            speaker_data['church_id'] = church_id
            
            speaker = models.Speaker(**speaker_data)
            db.add(speaker)
            db.commit()
            db.refresh(speaker)
            print(f"✅ Created speaker: {speaker.name} ({speaker.title})")
        
        print("🎉 Database seeding completed successfully!")
        print(f"📊 Created {len(created_churches)} churches and {len(speakers_data)} speakers")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
