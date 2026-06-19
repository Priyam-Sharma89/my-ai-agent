# that file have job to connect fast API with the PostgresSQl 

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Now we use the connectionstring - connection with the help of name

DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@database:5432/{os.getenv('POSTGRES_DB')}"

#creating engine the is the actual connection to PostgresSQL

engine = create_engine(DATABASE_URL)

#session local - How we talk database per request

sessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base = declarative_base() # parent class for all table definitions

#now Create a funtion that givbe the every request to own session 

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close() # i missed the closing brack