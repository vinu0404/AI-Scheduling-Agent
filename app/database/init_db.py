# schedule/app/database/init_db.py

# Import the engine and Base from your database configuration
from app.database.database import engine, Base

# !!! IMPORTANT: Explicitly import all your models here !!!
# This ensures that SQLAlchemy's Base object knows about them before creating the tables.
from app.database.models import Patient, Doctor, Appointment

def init_database():
    print("Creating database and tables...")
    # Base.metadata.create_all() will now create all tables for the imported models.
    Base.metadata.create_all(bind=engine)
    print("Database and tables created successfully.")

if __name__ == "__main__":
    init_database()