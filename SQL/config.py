import os# SQLonfig.py
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

class SQLConfig:
  DB_USER = os.getenv("DB_USER")
  DB_PASSWORD = os.getenv("DB_PASSWORD")
  DB_HOST = os.getenv("DB_HOST")
  DB_PORT = os.getenv("DB_PORT")
  DB_NAME = os.getenv("DB_NAME")

  @classmethod
  def get_database_uri(cls) -> str:
    """Constructs and returns the PostgreSQL URI."""
    conn_string = f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    print(conn_string)
    return conn_string
  



