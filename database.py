from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.ext.declarative import declarative_base

# SQLite database connection using SQLAlchemy
DATABASE_URL = "sqlite:///user_info.db"
engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    status = Column(String)  # user || admin
    balance = Column(Float)
    problem_ans = Column(Integer, default=0)
    total_answered = Column(Integer, default=0)
    correct_answered = Column(Integer, default=0)


# Create tables if not exists
Base.metadata.create_all(bind=engine)
