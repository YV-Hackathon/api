#!/usr/bin/env python3
"""
Generate AI embeddings for all speakers in the database.
This script should be run once to initialize the embedding cache.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.ai_embedding_service import get_ai_service


def generate_embeddings():
    """Generate and cache AI embeddings for all speakers"""
    print("🚀 Starting AI embedding generation...")
    
    # Get database session
    db = next(get_db())
    
    # Get AI service
    ai_service = get_ai_service()
    
    if not ai_service.is_available():
        print("❌ AI service not available. Make sure sentence-transformers is installed.")
        return False
    
    try:
        # Generate embeddings for all speakers
        embeddings = ai_service.generate_speaker_embeddings(db)
        
        if embeddings:
            print(f"✅ Successfully generated {len(embeddings)} speaker embeddings")
            print("💾 Embeddings cached for future use")
            return True
        else:
            print("❌ No embeddings were generated")
            return False
            
    except Exception as e:
        print(f"❌ Error generating embeddings: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = generate_embeddings()
    sys.exit(0 if success else 1)
