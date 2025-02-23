import os
import time
from sqlalchemy import create_engine, Column, Integer, Float, String, Date, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

# Get database URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL', '')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://')

# Add SSL mode to prevent SSL connection issues
if '?' not in DATABASE_URL:
    DATABASE_URL += '?sslmode=require'
elif 'sslmode=' not in DATABASE_URL:
    DATABASE_URL += '&sslmode=require'

# Create database engine with connection pooling and retry settings
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
    pool_pre_ping=True,  # Enable connection health checks
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    municipality = Column(String)
    image_url = Column(String)
    description_en = Column(String)
    description_fil = Column(String)

    surveys = relationship("Survey", back_populates="site")

class Survey(Base):
    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"))
    date = Column(Date)
    season = Column(String)
    hard_coral_cover = Column(Float)
    fleshy_macro_algae_cover = Column(Float)
    rubble = Column(Float)
    bleaching = Column(Float)
    total_density = Column(Float)
    commercial_density = Column(Float)
    herbivore_density = Column(Float)
    carnivore_density = Column(Float)
    omnivore_density = Column(Float)
    corallivore_density = Column(Float)
    commercial_biomass = Column(Float)

    site = relationship("Site", back_populates="surveys")

# Create all tables
Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session with automatic retry on connection failure"""
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            db = SessionLocal()
            # Test the connection using proper SQLAlchemy text() function
            db.execute(text("SELECT 1"))
            yield db
            break
        except Exception as e:
            retry_count += 1
            print(f"Database connection attempt {retry_count} failed: {str(e)}")
            if db:
                db.close()
            if retry_count >= max_retries:
                print("Max retries reached, failing...")
                raise
            # Wait before retrying, with exponential backoff
            time.sleep(2 ** retry_count)
    try:
        yield db
    finally:
        db.close()

# Modify the DataProcessor to handle connection failures
@contextmanager
def get_db_session():
    """Context manager for database sessions with automatic retry"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

def init_sample_data():
    """Initialize sample data for sites"""
    db = SessionLocal()
    try:
        # Check if sites already exist
        if db.query(Site).first():
            return

        # Sites in Siaton
        siaton_sites = ["Andulay", "Antulang", "Kookoos", "Salag"]
        for site in siaton_sites:
            db.add(Site(name=site, municipality="Siaton"))

        # Sites in Zamboanguita
        zamboanguita_sites = [
            "Basak", "Dalakit", "Guinsuan", "Latason", 
            "Lutoban North", "Lutoban South", "Lutoban Pier", 
            "Malatapay", "Mahon"
        ]
        for site in zamboanguita_sites:
            db.add(Site(name=site, municipality="Zamboanguita"))

        # Sites in Santa Catalina
        santa_catalina_sites = ["Cawitan", "Manalongon"]
        for site in santa_catalina_sites:
            db.add(Site(name=site, municipality="Santa Catalina"))

        db.commit()
    except Exception as e:
        print(f"Error initializing sample data: {str(e)}")
        db.rollback()
    finally:
        db.close()