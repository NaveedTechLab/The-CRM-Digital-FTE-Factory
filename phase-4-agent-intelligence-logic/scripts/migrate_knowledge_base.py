#!/usr/bin/env python3
"""
Script to initialize and populate the knowledge base with articles
"""

import asyncio
import sys
import os
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models.knowledge_base_article import KnowledgeBaseArticle, Base
from app.services.rag_service import rag_service
from app.config.settings import settings

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_sample_knowledge_base():
    """Setup sample knowledge base articles"""
    engine = create_engine(settings.DATABASE_URL)

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if knowledge base already has articles
        existing_count = db.query(KnowledgeBaseArticle).count()
        if existing_count > 0:
            print(f"Knowledge base already has {existing_count} articles. Skipping sample data.")
            return

        # Sample knowledge base articles
        sample_articles = [
            {
                "title": "Troubleshooting Login Issues",
                "content": "If you're experiencing login issues, first try clearing your browser cache and cookies. Make sure you're using the correct email and password. If you've forgotten your password, use the 'Forgot Password' link to reset it. If issues persist, try using a different browser or device.",
                "summary": "Steps to resolve common login problems",
                "category": "account",
                "tags": ["login", "authentication", "password", "troubleshooting"]
            },
            {
                "title": "Setting Up Two-Factor Authentication",
                "content": "To enhance your account security, we recommend enabling two-factor authentication. Go to Account Settings > Security > Two-Factor Authentication. Choose your preferred method (SMS or authenticator app) and follow the setup instructions. Once enabled, you'll need to provide a verification code in addition to your password when logging in.",
                "summary": "How to secure your account with 2FA",
                "category": "security",
                "tags": ["security", "2fa", "authentication", "account"]
            },
            {
                "title": "Managing Subscriptions and Billing",
                "content": "To manage your subscription, visit the Billing section in your account dashboard. From there you can upgrade or downgrade your plan, update payment methods, and download invoices. For refunds, please contact our support team directly as refund policies vary by subscription type.",
                "summary": "Guide to subscription and billing management",
                "category": "billing",
                "tags": ["billing", "subscription", "payment", "refunds"]
            },
            {
                "title": "Using the Dashboard Features",
                "content": "The dashboard provides an overview of your activity and important metrics. Use the navigation menu to access different sections. Customize your dashboard by adding widgets that matter most to you. You can save custom views and share them with team members who have appropriate permissions.",
                "summary": "Overview of dashboard capabilities",
                "category": "features",
                "tags": ["dashboard", "features", "navigation", "widgets"]
            },
            {
                "title": "Creating and Managing Projects",
                "content": "Projects help organize your work. To create a project, click the 'New Project' button and provide a name and description. Add team members by inviting them via email. Set permissions for different roles. Track project progress using the built-in reporting tools and timeline views.",
                "summary": "Project organization and management guide",
                "category": "features",
                "tags": ["projects", "team", "collaboration", "organization"]
            }
        ]

        # Add sample articles to the database
        for article_data in sample_articles:
            article = KnowledgeBaseArticle(
                title=article_data["title"],
                content=article_data["content"],
                summary=article_data["summary"],
                category=article_data["category"],
                tags=article_data["tags"],
                status="published",
                author="System Administrator"
            )
            db.add(article)

        db.commit()
        print(f"Added {len(sample_articles)} sample articles to the knowledge base.")

        # Generate embeddings for the articles
        print("Generating embeddings for knowledge base articles...")
        rag_service.index_knowledge_base()
        print("Embeddings generated successfully.")

    except Exception as e:
        print(f"Error setting up knowledge base: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting knowledge base migration...")
    setup_sample_knowledge_base()
    print("Knowledge base migration completed successfully!")