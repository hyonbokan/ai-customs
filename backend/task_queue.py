"""
Task Queue Configuration using Huey

This module provides a simple task queue configuration for background
processing in the AI Customs application using SQLite for persistence.
"""

import os

from huey import MemoryHuey, SqliteHuey

# Check if we're running in a production environment
environment = os.getenv("ENVIRONMENT", "development")

if environment == "production":
    # Use SQLite for production - appropriate for small systems
    database_path = os.getenv("HUEY_DATABASE_PATH", "/app/database/huey.db")
    huey = SqliteHuey("ai-customs-tasks", filename=database_path)
else:
    # Use in-memory queue for development and testing
    huey = MemoryHuey("ai-customs-tasks")

# Export huey instance for use in main.py
__all__ = ["huey"]
