import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv(Path(__file__).with_name('.env'))
logger = logging.getLogger('complain.database')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./complain_system.db')
Base = declarative_base()
engine = None
SessionLocal = None


def configure_database() -> None:
    """Prefer Supabase, but use a local SQLite database when it is unreachable."""
    global engine, SessionLocal
    try:
        database_url = DATABASE_URL
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
        connect_args = {'connect_timeout': 8, 'sslmode': 'require'} if database_url.startswith('postgresql') else {'check_same_thread': False}
        candidate = create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)
        with candidate.connect() as connection:
            connection.exec_driver_sql('SELECT 1')
        engine = candidate
        logger.info('Connected to configured PostgreSQL database.')
    except Exception as exc:
        logger.warning('Could not connect to configured database (%s). Falling back to local SQLite.', exc)
        fallback = Path(__file__).with_name('complain_system.db')
        engine = create_engine(f'sqlite:///{fallback}', connect_args={'check_same_thread': False}, pool_pre_ping=True)
        with engine.connect() as connection:
            connection.exec_driver_sql('SELECT 1')
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    if SessionLocal is None:
        configure_database()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
