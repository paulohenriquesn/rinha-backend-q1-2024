from sqlalchemy import create_engine
from sqlalchemy.engine import URL

url = URL.create(
    drivername='postgresql',
    username='dev',
    password='dev',
    host='db',
    database='dev'
)

engine = create_engine(url)
