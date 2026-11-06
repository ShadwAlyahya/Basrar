from app.core.database import engine, Base
from app.models.user import User
from app.models.dataset import Dataset

def init_db():
    print("Creating database tables in SQL Server...")
    # This will create tables for all models that inherit from Base
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    init_db()