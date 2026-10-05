from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DATABASE_URL

# Authorization reads happen before attempt row locks. READ COMMITTED ensures
# subsequent answer queries see the transaction that just released that lock.
options = {"isolation_level": "READ COMMITTED"} if make_url(DATABASE_URL).get_backend_name() == "mysql" else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600, **options)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


