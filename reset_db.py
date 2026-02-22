from backend.database import Base, engine
from backend.seed_data import seed

def reset_database():
    print("Dropping tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Seeding data...")
    seed()
    print("Done!")

if __name__ == "__main__":
    if input("Reset DB? (yes/no): ").lower() == 'yes':
        reset_database()