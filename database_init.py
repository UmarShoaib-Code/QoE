"""
Database initialization script
Run this once to create the database tables
"""
import os
from sqlalchemy import create_engine, text
from app.database.models import init_db, get_database_url

def create_database_if_not_exists():
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "qoe_tool")
    
    connection_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}"
    engine = create_engine(connection_url, pool_pre_ping=True)
    
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}`"))
        conn.commit()
    
    engine.dispose()

if __name__ == "__main__":
    print("Initializing database...")
    print(f"Database URL: {get_database_url()}")
    
    try:
        print("Creating database if it doesn't exist...")
        create_database_if_not_exists()
        print("Creating tables...")
        init_db()
        print("✅ Database initialized successfully!")
        print("\nTables created:")
        print("  - users")
        print("  - projects")
        print("  - project_files")
        print("  - databooks")
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        print("\nMake sure:")
        print("  1. XAMPP MySQL is running (start it from XAMPP Control Panel)")
        print("  2. MySQL is running on port 3306")
        print("  3. Default credentials: user='root', password='' (empty)")
        raise

