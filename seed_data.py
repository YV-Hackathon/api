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
from passlib.context import CryptContext

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
    },
    {
        "name": "St. Mary's Catholic Church",
        "denomination": "Catholic",
        "description": "A vibrant Catholic community dedicated to worship, service, and spiritual growth. We welcome all to join us in faith and fellowship.",
        "address": {
            "street": "321 Church Street",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62704",
            "country": "USA"
        },
        "phone": "(217) 555-0321",
        "email": "office@stmarys.org",
        "website": "https://stmarys.org",
        "founded_year": 1850,
        "membership_count": 1200,
        "service_times": {
            "sunday": ["7:00 AM", "9:00 AM", "11:00 AM", "5:00 PM"],
            "saturday": ["4:00 PM", "6:00 PM"],
            "weekdays": ["6:30 AM", "12:10 PM"]
        },
        "social_media": {
            "facebook": "https://facebook.com/stmarys",
            "instagram": "https://instagram.com/stmarys",
            "youtube": "https://youtube.com/stmarys"
        },
        "is_active": True,
        "sort_order": 4
    },
    {
        "name": "Metropolitan United Methodist Church",
        "denomination": "Methodist",
        "description": "A progressive Methodist congregation committed to social justice, community service, and inclusive worship. All are welcome at God's table.",
        "address": {
            "street": "654 Elm Street",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62705",
            "country": "USA"
        },
        "phone": "(217) 555-0654",
        "email": "info@metroumc.org",
        "website": "https://metroumc.org",
        "founded_year": 1920,
        "membership_count": 380,
        "service_times": {
            "sunday": ["8:00 AM", "10:00 AM", "12:00 PM"],
            "wednesday": ["7:00 PM"]
        },
        "social_media": {
            "facebook": "https://facebook.com/metroumc",
            "instagram": "https://instagram.com/metroumc",
            "twitter": "https://twitter.com/metroumc"
        },
        "is_active": True,
        "sort_order": 5
    },
    {
        "name": "Cornerstone Assembly of God",
        "denomination": "Assembly of God",
        "description": "A Spirit-filled congregation passionate about worship, prayer, and reaching the community with the love of Christ.",
        "address": {
            "street": "987 Faith Drive",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62706",
            "country": "USA"
        },
        "phone": "(217) 555-0987",
        "email": "hello@cornerstoneag.org",
        "website": "https://cornerstoneag.org",
        "founded_year": 1995,
        "membership_count": 220,
        "service_times": {
            "sunday": ["9:00 AM", "11:00 AM"],
            "wednesday": ["7:00 PM"],
            "friday": ["7:00 PM"]
        },
        "social_media": {
            "facebook": "https://facebook.com/cornerstoneag",
            "instagram": "https://instagram.com/cornerstoneag",
            "youtube": "https://youtube.com/cornerstoneag"
        },
        "is_active": True,
        "sort_order": 6
    },
    {
        "name": "Redeemer Lutheran Church",
        "denomination": "Lutheran",
        "description": "A traditional Lutheran congregation grounded in grace, faith, and the Word of God. We celebrate the sacraments and serve our community.",
        "address": {
            "street": "147 Grace Avenue",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62707",
            "country": "USA"
        },
        "phone": "(217) 555-0147",
        "email": "office@redeemerlutheran.org",
        "website": "https://redeemerlutheran.org",
        "founded_year": 1905,
        "membership_count": 180,
        "service_times": {
            "sunday": ["8:00 AM", "10:30 AM"],
            "wednesday": ["6:30 PM"]
        },
        "social_media": {
            "facebook": "https://facebook.com/redeemerlutheran",
            "instagram": "https://instagram.com/redeemerlutheran"
        },
        "is_active": True,
        "sort_order": 7
    },
    {
        "name": "Victory Christian Center",
        "denomination": "Pentecostal",
        "description": "A dynamic Pentecostal church focused on the power of the Holy Spirit, healing, and deliverance. We believe in miracles and God's transforming power.",
        "address": {
            "street": "258 Victory Lane",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62708",
            "country": "USA"
        },
        "phone": "(217) 555-0258",
        "email": "info@victorychristian.org",
        "website": "https://victorychristian.org",
        "founded_year": 1988,
        "membership_count": 350,
        "service_times": {
            "sunday": ["10:00 AM", "6:00 PM"],
            "tuesday": ["7:00 PM"],
            "thursday": ["7:00 PM"]
        },
        "social_media": {
            "facebook": "https://facebook.com/victorychristian",
            "instagram": "https://instagram.com/victorychristian",
            "youtube": "https://youtube.com/victorychristian"
        },
        "is_active": True,
        "sort_order": 8
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
                "category": "PREACHING"
            },
            {
                "name": "Community Building",
                "description": "Building authentic Christian community in the modern world",
                "category": "LEADERSHIP"
            },
            {
                "name": "Prayer Life",
                "description": "Developing a deeper and more meaningful prayer life",
                "category": "PRAYER"
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
                "category": "YOUTH"
            },
            {
                "name": "Mental Health and Faith",
                "description": "Addressing mental health issues from a Christian perspective",
                "category": "COUNSELING"
            },
            {
                "name": "Social Justice",
                "description": "Living out faith through social action and justice",
                "category": "EVANGELISM"
            }
        ],
        "sort_order": 2,
        "teaching_style": TeachingStyle.RELATABLE,
        "bible_approach": BibleApproach.MORE_APPLICATION,
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
                "category": "TEACHING"
            },
            {
                "name": "Church History",
                "description": "Understanding the historical development of Christian doctrine",
                "category": "TEACHING"
            },
            {
                "name": "Pastoral Leadership",
                "description": "Leading and shepherding a congregation effectively",
                "category": "LEADERSHIP"
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
                "category": "WORSHIP"
            },
            {
                "name": "Marriage and Family",
                "description": "Building strong Christian marriages and families",
                "category": "MARRIAGE"
            },
            {
                "name": "Personal Growth",
                "description": "Growing in faith and character as a Christian",
                "category": "TEACHING"
            }
        ],
        "sort_order": 4,
        "teaching_style": TeachingStyle.RELATABLE,
        "bible_approach": BibleApproach.MORE_APPLICATION,
        "environment_style": EnvironmentStyle.CONTEMPORARY,
        "is_recommended": True,
        "church_index": 2
    },
    {
        "name": "Fr. Patrick O'Brien",
        "title": "Parish Priest",
        "bio": "Fr. Patrick has served the Catholic community for 25 years. He is known for his compassionate pastoral care and deep understanding of Catholic tradition and liturgy.",
        "email": "fr.patrick@stmarys.org",
        "phone": "(217) 555-0322",
        "years_of_service": 25,
        "social_media": {
            "facebook": "https://facebook.com/frpatrickobrien",
            "instagram": "https://instagram.com/frpatrickobrien"
        },
        "speaking_topics": [
            {
                "name": "Catholic Sacraments",
                "description": "Understanding the seven sacraments and their significance",
                "category": "TEACHING"
            },
            {
                "name": "Social Justice",
                "description": "Catholic social teaching and its application today",
                "category": "EVANGELISM"
            },
            {
                "name": "Prayer and Devotion",
                "description": "Traditional Catholic prayer practices and devotions",
                "category": "PRAYER"
            }
        ],
        "sort_order": 5,
        "teaching_style": TeachingStyle.ACADEMIC,
        "bible_approach": BibleApproach.MORE_SCRIPTURE,
        "environment_style": EnvironmentStyle.TRADITIONAL,
        "is_recommended": True,
        "church_index": 3
    },
    {
        "name": "Rev. Dr. Maria Rodriguez",
        "title": "Senior Pastor",
        "bio": "Rev. Dr. Rodriguez is a passionate advocate for social justice and community transformation. She holds a Ph.D. in Social Ethics and has been instrumental in community development programs.",
        "email": "maria.rodriguez@metroumc.org",
        "phone": "(217) 555-0655",
        "years_of_service": 12,
        "social_media": {
            "facebook": "https://facebook.com/revmariarodriguez",
            "twitter": "https://twitter.com/revmariarodriguez",
            "linkedin": "https://linkedin.com/in/revmariarodriguez"
        },
        "speaking_topics": [
            {
                "name": "Social Justice",
                "description": "Biblical foundations for social justice and community action",
                "category": "EVANGELISM"
            },
            {
                "name": "Community Development",
                "description": "Building stronger communities through faith-based initiatives",
                "category": "LEADERSHIP"
            },
            {
                "name": "Diversity and Inclusion",
                "description": "Creating inclusive church communities that welcome all",
                "category": "LEADERSHIP"
            }
        ],
        "sort_order": 6,
        "teaching_style": TeachingStyle.RELATABLE,
        "bible_approach": BibleApproach.MORE_APPLICATION,
        "environment_style": EnvironmentStyle.CONTEMPORARY,
        "is_recommended": True,
        "church_index": 4
    },
    {
        "name": "Pastor David Thompson",
        "title": "Lead Pastor",
        "bio": "Pastor David is a Spirit-filled leader with a heart for evangelism and discipleship. He has planted multiple churches and has a passion for reaching the lost.",
        "email": "david.thompson@cornerstoneag.org",
        "phone": "(217) 555-0988",
        "years_of_service": 20,
        "social_media": {
            "facebook": "https://facebook.com/pastordavidthompson",
            "instagram": "https://instagram.com/pastordavidthompson",
            "youtube": "https://youtube.com/pastordavidthompson"
        },
        "speaking_topics": [
            {
                "name": "Evangelism",
                "description": "Sharing the gospel effectively in today's world",
                "category": "EVANGELISM"
            },
            {
                "name": "Holy Spirit",
                "description": "Understanding and walking in the power of the Holy Spirit",
                "category": "TEACHING"
            },
            {
                "name": "Church Planting",
                "description": "Starting and growing new churches and ministries",
                "category": "LEADERSHIP"
            }
        ],
        "sort_order": 7,
        "teaching_style": TeachingStyle.RELATABLE,
        "bible_approach": BibleApproach.MORE_APPLICATION,
        "environment_style": EnvironmentStyle.CONTEMPORARY,
        "is_recommended": True,
        "church_index": 5
    },
    {
        "name": "Pastor Rebecca Mueller",
        "title": "Senior Pastor",
        "bio": "Pastor Rebecca is a dedicated Lutheran minister with a deep love for liturgy and traditional worship. She has served in both urban and rural settings.",
        "email": "rebecca.mueller@redeemerlutheran.org",
        "phone": "(217) 555-0148",
        "years_of_service": 18,
        "social_media": {
            "facebook": "https://facebook.com/pastorrebeccamueller",
            "instagram": "https://instagram.com/pastorrebeccamueller"
        },
        "speaking_topics": [
            {
                "name": "Lutheran Theology",
                "description": "Understanding grace, faith, and the Word in Lutheran tradition",
                "category": "TEACHING"
            },
            {
                "name": "Worship and Liturgy",
                "description": "The importance and beauty of traditional worship",
                "category": "WORSHIP"
            },
            {
                "name": "Pastoral Care",
                "description": "Providing compassionate care to church members",
                "category": "COUNSELING"
            }
        ],
        "sort_order": 8,
        "teaching_style": TeachingStyle.ACADEMIC,
        "bible_approach": BibleApproach.MORE_SCRIPTURE,
        "environment_style": EnvironmentStyle.TRADITIONAL,
        "is_recommended": True,
        "church_index": 6
    },
    {
        "name": "Apostle James Washington",
        "title": "Senior Pastor",
        "bio": "Apostle James is a dynamic Pentecostal leader with a powerful healing ministry. He has traveled internationally and has seen countless miracles and healings.",
        "email": "james.washington@victorychristian.org",
        "phone": "(217) 555-0259",
        "years_of_service": 30,
        "social_media": {
            "facebook": "https://facebook.com/apostlejameswashington",
            "instagram": "https://instagram.com/apostlejameswashington",
            "youtube": "https://youtube.com/apostlejameswashington"
        },
        "speaking_topics": [
            {
                "name": "Healing Ministry",
                "description": "Understanding and ministering divine healing",
                "category": "TEACHING"
            },
            {
                "name": "Deliverance",
                "description": "Freedom from spiritual bondage and oppression",
                "category": "COUNSELING"
            },
            {
                "name": "Faith and Miracles",
                "description": "Walking in faith and expecting God's miraculous intervention",
                "category": "PREACHING"
            }
        ],
        "sort_order": 9,
        "teaching_style": TeachingStyle.RELATABLE,
        "bible_approach": BibleApproach.MORE_APPLICATION,
        "environment_style": EnvironmentStyle.CONTEMPORARY,
        "is_recommended": True,
        "church_index": 7
    },
    {
        "name": "Rev. Dr. Jennifer Kim",
        "title": "Associate Pastor",
        "bio": "Rev. Dr. Kim is a gifted teacher and counselor with expertise in family ministry and biblical studies. She has authored several books on Christian living.",
        "email": "jennifer.kim@gracecommunity.org",
        "phone": "(217) 555-0126",
        "years_of_service": 10,
        "social_media": {
            "facebook": "https://facebook.com/revjenniferkim",
            "instagram": "https://instagram.com/revjenniferkim",
            "linkedin": "https://linkedin.com/in/revjenniferkim"
        },
        "speaking_topics": [
            {
                "name": "Family Ministry",
                "description": "Building strong Christian families in today's culture",
                "category": "FAMILY"
            },
            {
                "name": "Women's Ministry",
                "description": "Empowering women in their faith journey and calling",
                "category": "TEACHING"
            },
            {
                "name": "Biblical Studies",
                "description": "Deep study of Scripture and its practical application",
                "category": "TEACHING"
            }
        ],
        "sort_order": 10,
        "teaching_style": TeachingStyle.BALANCED,
        "bible_approach": BibleApproach.BALANCED,
        "environment_style": EnvironmentStyle.BLENDED,
        "is_recommended": True,
        "church_index": 0
    }
]

# Sample user data
users_data = [
    {
        "username": "john_doe",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "password",
        "onboarding_completed": True,
        "bible_reading_preference": BibleApproach.BALANCED,
        "teaching_style_preference": TeachingStyle.BALANCED,
        "environment_preference": EnvironmentStyle.BLENDED,
        "preferred_speaker_ids": [1, 2, 10]  # Will be converted to actual speaker IDs
    },
    {
        "username": "sarah_wilson",
        "email": "sarah.wilson@example.com",
        "first_name": "Sarah",
        "last_name": "Wilson",
        "password": "password",
        "onboarding_completed": True,
        "bible_reading_preference": BibleApproach.MORE_APPLICATION,
        "teaching_style_preference": TeachingStyle.RELATABLE,
        "environment_preference": EnvironmentStyle.CONTEMPORARY,
        "preferred_speaker_ids": [2, 4, 6]
    },
    {
        "username": "michael_brown",
        "email": "michael.brown@example.com",
        "first_name": "Michael",
        "last_name": "Brown",
        "password": "password",
        "onboarding_completed": True,
        "bible_reading_preference": BibleApproach.MORE_SCRIPTURE,
        "teaching_style_preference": TeachingStyle.ACADEMIC,
        "environment_preference": EnvironmentStyle.TRADITIONAL,
        "preferred_speaker_ids": [3, 5, 8]
    },
    {
        "username": "lisa_garcia",
        "email": "lisa.garcia@example.com",
        "first_name": "Lisa",
        "last_name": "Garcia",
        "password": "password",
        "onboarding_completed": False,
        "bible_reading_preference": None,
        "teaching_style_preference": None,
        "environment_preference": None,
        "preferred_speaker_ids": []
    },
    {
        "username": "david_johnson",
        "email": "david.johnson@example.com",
        "first_name": "David",
        "last_name": "Johnson",
        "password": "password",
        "onboarding_completed": True,
        "bible_reading_preference": BibleApproach.MORE_APPLICATION,
        "teaching_style_preference": TeachingStyle.RELATABLE,
        "environment_preference": EnvironmentStyle.CONTEMPORARY,
        "preferred_speaker_ids": [4, 7, 9]
    }
]

# Sample onboarding questions data
onboarding_questions_data = {
    "questions": [
        {
            "id": "bible_reading_preference",
            "title": "How do you prefer to approach Bible study?",
            "description": "This helps us recommend speakers who match your learning style",
            "type": "single-select",
            "options": [
                {
                    "value": "MORE_SCRIPTURE",
                    "label": "More Scripture-focused",
                    "description": "I prefer deep, verse-by-verse study of the Bible"
                },
                {
                    "value": "MORE_APPLICATION",
                    "label": "More Life Application",
                    "description": "I prefer practical, life-focused teaching"
                },
                {
                    "value": "BALANCED",
                    "label": "Balanced Approach",
                    "description": "I like a mix of both Scripture study and practical application"
                }
            ]
        },
        {
            "id": "teaching_style_preference",
            "title": "What teaching style resonates with you?",
            "description": "Choose the style that best matches how you like to learn",
            "type": "single-select",
            "options": [
                {
                    "value": "ACADEMIC",
                    "label": "Academic",
                    "description": "I enjoy scholarly, in-depth theological discussions"
                },
                {
                    "value": "RELATABLE",
                    "label": "Relatable",
                    "description": "I prefer speakers who share personal stories and experiences"
                },
                {
                    "value": "BALANCED",
                    "label": "Balanced",
                    "description": "I like a mix of academic depth and personal relatability"
                }
            ]
        },
        {
            "id": "environment_preference",
            "title": "What worship environment do you prefer?",
            "description": "This helps us match you with speakers from similar church environments",
            "type": "single-select",
            "options": [
                {
                    "value": "TRADITIONAL",
                    "label": "Traditional",
                    "description": "I prefer traditional hymns, liturgy, and formal worship"
                },
                {
                    "value": "CONTEMPORARY",
                    "label": "Contemporary",
                    "description": "I prefer modern music, casual atmosphere, and contemporary worship"
                },
                {
                    "value": "BLENDED",
                    "label": "Blended",
                    "description": "I enjoy a mix of traditional and contemporary elements"
                }
            ]
        },
        {
            "id": "speaking_topics",
            "title": "What topics interest you most?",
            "description": "Select all topics that interest you (you can choose multiple)",
            "type": "multi-select",
            "options": [
                {
                    "value": "preaching",
                    "label": "Preaching & Sermons",
                    "description": "General preaching and sermon topics"
                },
                {
                    "value": "teaching",
                    "label": "Biblical Teaching",
                    "description": "Deep biblical study and theology"
                },
                {
                    "value": "counseling",
                    "label": "Counseling & Care",
                    "description": "Pastoral care and Christian counseling"
                },
                {
                    "value": "leadership",
                    "label": "Leadership",
                    "description": "Church leadership and ministry development"
                },
                {
                    "value": "evangelism",
                    "label": "Evangelism & Outreach",
                    "description": "Sharing faith and community outreach"
                },
                {
                    "value": "worship",
                    "label": "Worship & Music",
                    "description": "Worship leadership and music ministry"
                },
                {
                    "value": "youth",
                    "label": "Youth Ministry",
                    "description": "Ministry to children, teens, and young adults"
                },
                {
                    "value": "marriage",
                    "label": "Marriage & Family",
                    "description": "Marriage counseling and family ministry"
                },
                {
                    "value": "family",
                    "label": "Family Life",
                    "description": "Christian family living and parenting"
                },
                {
                    "value": "prayer",
                    "label": "Prayer & Devotion",
                    "description": "Prayer life and spiritual disciplines"
                }
            ]
        }
    ]
}

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    try:
        # Truncate password to 72 bytes if it's too long
        if len(password.encode('utf-8')) > 72:
            password = password[:72]
        return pwd_context.hash(password)
    except Exception as e:
        # Fallback to a simple hash if bcrypt fails
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

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
        existing_users = db.query(models.User).count()
        existing_questions = db.query(models.OnboardingQuestion).count()
        
        if existing_churches > 0 or existing_speakers > 0 or existing_users > 0 or existing_questions > 0:
            print(f"⚠️  Database already contains {existing_churches} churches, {existing_speakers} speakers, {existing_users} users, and {existing_questions} onboarding questions")
            try:
                response = input("Do you want to clear existing data and reseed? (y/N): ")
            except EOFError:
                # Handle non-interactive environments (like CI/CD)
                print("Running in non-interactive mode. Clearing existing data...")
                response = 'y'
            
            if response.lower() != 'y':
                print("❌ Seeding cancelled")
                return
            
            # Clear existing data
            db.query(models.UserSpeakerPreference).delete()
            db.query(models.User).delete()
            db.query(models.Speaker).delete()
            db.query(models.Church).delete()
            db.query(models.OnboardingQuestion).delete()
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
        created_speakers = []
        for speaker_data in speakers_data:
            # Remove church_index from speaker data
            church_index = speaker_data.pop('church_index')
            church_id = created_churches[church_index].id
            speaker_data['church_id'] = church_id
            
            speaker = models.Speaker(**speaker_data)
            db.add(speaker)
            db.commit()
            db.refresh(speaker)
            created_speakers.append(speaker)
            print(f"✅ Created speaker: {speaker.name} ({speaker.title})")
        
        # Create users
        print("👤 Creating users...")
        created_users = []
        for user_data in users_data:
            # Hash password and remove preferred_speaker_ids
            password = user_data.pop('password')
            preferred_speaker_ids = user_data.pop('preferred_speaker_ids', [])
            user_data['hashed_password'] = get_password_hash(password)
            
            user = models.User(**user_data)
            db.add(user)
            db.commit()
            db.refresh(user)
            created_users.append(user)
            print(f"✅ Created user: {user.username} ({user.first_name} {user.last_name})")
            
            # Create user speaker preferences
            for speaker_id in preferred_speaker_ids:
                if speaker_id <= len(created_speakers):
                    preference = models.UserSpeakerPreference(
                        user_id=user.id,
                        speaker_id=created_speakers[speaker_id - 1].id
                    )
                    db.add(preference)
            db.commit()
        
        # Create onboarding questions
        print("❓ Creating onboarding questions...")
        onboarding_question = models.OnboardingQuestion(
            questions=onboarding_questions_data
        )
        db.add(onboarding_question)
        db.commit()
        db.refresh(onboarding_question)
        print("✅ Created onboarding questions")
        
        print("🎉 Database seeding completed successfully!")
        print(f"📊 Created {len(created_churches)} churches, {len(created_speakers)} speakers, {len(created_users)} users, and 1 onboarding question set")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
