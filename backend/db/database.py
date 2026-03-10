from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from core.config import settings

engine = create_engine(
    settings.DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Give us access to a database and ensure that we don't have multiple sessions open at one time
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# When we first create the application, we need to create all the tables based on, the data models that we've defined
def create_tables():
    Base.metadata.create_all(bind=engine)
