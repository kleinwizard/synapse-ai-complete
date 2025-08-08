#!/usr/bin/env python3
"""
Database Migration Script for Synapse AI
Handles database initialization and migrations for both SQLite and PostgreSQL.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
import asyncio

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent.parent))

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

from app.database import Base, User, create_tables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./synapse_ai.db")
        self.is_postgresql = self.database_url.startswith("postgresql://")
        self.migrations_dir = Path(__file__).parent
        
    def parse_postgresql_url(self, url: str) -> dict:
        """Parse PostgreSQL URL into components."""
        # postgresql://user:password@host:port/database
        if not url.startswith("postgresql://"):
            raise ValueError("Invalid PostgreSQL URL")
            
        # Remove postgresql:// prefix
        url = url[13:]
        
        # Split user:password@host:port/database
        if "@" in url:
            auth_part, host_part = url.split("@", 1)
            if ":" in auth_part:
                username, password = auth_part.split(":", 1)
            else:
                username, password = auth_part, ""
        else:
            username, password = "", ""
            host_part = url
            
        if "/" in host_part:
            host_port, database = host_part.split("/", 1)
        else:
            host_port, database = host_part, ""
            
        if ":" in host_port:
            host, port = host_port.split(":", 1)
            port = int(port)
        else:
            host, port = host_port, 5432
            
        return {
            "username": username,
            "password": password,
            "host": host,
            "port": port,
            "database": database
        }
    
    def create_postgresql_database(self) -> bool:
        """Create PostgreSQL database if it doesn't exist."""
        if not POSTGRESQL_AVAILABLE:
            logger.error("psycopg2 not available. Install with: pip install psycopg2-binary")
            return False
            
        try:
            db_config = self.parse_postgresql_url(self.database_url)
            
            # Connect to postgres database to create the target database
            conn = psycopg2.connect(
                host=db_config["host"],
                port=db_config["port"],
                user=db_config["username"],
                password=db_config["password"],
                database="postgres"  # Connect to default postgres database
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (db_config["database"],)
            )
            
            if cursor.fetchone():
                logger.info(f"Database '{db_config['database']}' already exists")
            else:
                # Create database
                cursor.execute(f"CREATE DATABASE \"{db_config['database']}\"")
                logger.info(f"Created database '{db_config['database']}'")
                
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL database: {e}")
            return False
    
    def run_sql_migration(self, migration_file: Path) -> bool:
        """Run a SQL migration file."""
        try:
            engine = create_engine(self.database_url)
            
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            with engine.connect() as conn:
                # Use a transaction for the entire migration
                trans = conn.begin()
                try:
                    for statement in statements:
                        if statement:  # Skip empty statements
                            logger.info(f"Executing: {statement[:100]}...")
                            conn.execute(text(statement))
                    
                    trans.commit()
                    logger.info(f"Successfully executed migration: {migration_file.name}")
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    logger.error(f"Error executing statement in {migration_file.name}: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to run migration {migration_file.name}: {e}")
            return False
    
    def check_database_exists(self) -> bool:
        """Check if database and tables exist."""
        try:
            engine = create_engine(self.database_url)
            inspector = inspect(engine)
            
            # Check if users table exists (primary table)
            tables = inspector.get_table_names()
            has_users = 'users' in tables
            
            if has_users:
                logger.info("Database appears to be initialized (users table exists)")
                return True
            else:
                logger.info("Database needs initialization (users table missing)")
                return False
                
        except OperationalError as e:
            if "database" in str(e).lower() and "does not exist" in str(e).lower():
                logger.info("Database does not exist")
                return False
            else:
                logger.error(f"Database connection error: {e}")
                return False
        except Exception as e:
            logger.error(f"Error checking database: {e}")
            return False
    
    def migrate(self, force: bool = False) -> bool:
        """Run database migrations."""
        logger.info(f"Starting database migration...")
        logger.info(f"Database URL: {self.database_url}")
        logger.info(f"Database type: {'PostgreSQL' if self.is_postgresql else 'SQLite'}")
        
        # For PostgreSQL, create database if it doesn't exist
        if self.is_postgresql:
            if not self.create_postgresql_database():
                return False
        
        # Check if database is already initialized
        if not force and self.check_database_exists():
            logger.info("Database already initialized. Use --force to re-run migrations.")
            return True
        
        success = True
        
        if self.is_postgresql:
            # Run PostgreSQL SQL migration
            sql_migration = self.migrations_dir / "001_initial_schema.sql"
            if sql_migration.exists():
                logger.info("Running PostgreSQL SQL migration...")
                if not self.run_sql_migration(sql_migration):
                    success = False
            else:
                logger.warning("PostgreSQL migration file not found, falling back to SQLAlchemy")
                create_tables()
        else:
            # For SQLite, use SQLAlchemy
            logger.info("Creating SQLite tables with SQLAlchemy...")
            try:
                create_tables()
                logger.info("SQLite tables created successfully")
            except Exception as e:
                logger.error(f"Failed to create SQLite tables: {e}")
                success = False
        
        if success:
            logger.info("✅ Database migration completed successfully!")
        else:
            logger.error("❌ Database migration failed!")
            
        return success

def main():
    """Main migration entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Synapse AI Database Migration Tool")
    parser.add_argument("--force", action="store_true", 
                       help="Force re-run migrations even if database exists")
    parser.add_argument("--check", action="store_true",
                       help="Only check database status, don't run migrations")
    
    args = parser.parse_args()
    
    migrator = DatabaseMigrator()
    
    if args.check:
        exists = migrator.check_database_exists()
        print(f"Database initialized: {exists}")
        return 0 if exists else 1
    
    success = migrator.migrate(force=args.force)
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())