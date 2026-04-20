import secrets

from sqlalchemy import create_engine, String, Integer, Column, Boolean, update

from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine("sqlite:///test.db")

Base = declarative_base()

class Users(Base):
	__tablename__ = "userki"

	id = Column(Integer, primary_key = True)
	generated_token = Column(String, unique = True,
					 index = True, nullable = False)
	limit = Column(Integer, default=10)
	limit_spent = Column(Integer, default=0)
	login = Column(String, nullable = True, unique = True)
	passwd_hash = Column(String, nullable = True)
	paid = Column(Boolean, default = False)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

