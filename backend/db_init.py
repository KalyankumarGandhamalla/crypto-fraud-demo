from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

engine = create_engine("sqlite:///fraud_demo.db", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, future=True)

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Initialized SQLite DB: fraud_demo.db")
