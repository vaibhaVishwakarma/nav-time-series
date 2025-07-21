import os
import logging
from flask import Flask
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, registry
from flask_sqlalchemy import SQLAlchemy
from SQL.config import SQLConfig


load_dotenv = True  # Set to True to load environment variables from .env file
if load_dotenv:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env")
    os.environ["SQLALCHEMY_DATABASE_URI"] =  SQLConfig.get_database_uri()

DB_URL = os.environ.get('SQLALCHEMY_DATABASE_URI', '').strip()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define naming convention for constraints to help with migrations
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Create base metadata with naming convention
metadata = MetaData(naming_convention=convention)
mapper_registry = registry(metadata=metadata)


# Create SQLAlchemy base class
class Base(DeclarativeBase):
    metadata = metadata


# Create SQLAlchemy extension
db = SQLAlchemy(model_class=Base)


def create_app():
    """
    Create Flask application
    
    Returns:
        Flask: The configured Flask application
    """
    # Create Flask application
    app = Flask(__name__)

    # Configure database - prioritize Google Cloud SQL

    database_uri = DB_URL

    # print(f"Database URI: {database_uri}")   #[DEBUG]

    if database_uri:
        logger.info("Attempting to use Google Cloud SQL database")
        # Check if the connection string has the correct PostgreSQL format
        try:
            # Test if the URL can be parsed properly
            from sqlalchemy.engine import make_url
            database_url = make_url(database_uri)
            # print("database url: ",database_url) #[DEBUG]
            
            logger.info("Google Cloud SQL connection string format is valid")

            # Test actual connection with a quick timeout
            import psycopg2
            try:
                conn = psycopg2.connect(database_uri, connect_timeout=10)
                conn.close()
                logger.info("Google Cloud SQL connection test successful")
            except psycopg2.OperationalError as conn_error:
                logger.error(f"Google Cloud SQL connection failed: {conn_error}")
                logger.error("This may be due to:")
                logger.error("1. IP whitelist restrictions in Google Cloud SQL")
                logger.error("2. Firewall settings blocking port 5432")
                logger.error("3. Network connectivity issues")
                logger.error("Please fix the Google Cloud SQL connection issue before proceeding"
                )
                raise RuntimeError(f"Cannot connect to Google Cloud SQL: {conn_error}")

        except Exception as e:
            # logger.error(f"Invalid Google Cloud database URL format: {e}")
            logger.error("The connection string should be in format: postgresql://username:password@host:port/database"
            )
            logger.error("For Google Cloud SQL, use the public IP address, not the connection name"
            )
            raise ValueError(f"Invalid Google Cloud SQL database URL: {e}")
    else:
        logger.error(
            "Google Cloud SQL database URL not found in environment variables")
        logger.error(
            "Please set GOOGLE_CLOUD_DATABASE_URL environment variable")
        raise ValueError("Google Cloud SQL database connection required")

    # Set this in the environment in case any other modules need it
    os.environ['SQLALCHEMY_DATABASE_URI'] = database_uri
    # Configure SQLAlchemy - this is what Flask-SQLAlchemy looks for
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "connect_args": {
            "connect_timeout": 30,
            "sslmode": "enable"
        }
    }

    # Set a secret key for the application
    app.secret_key = 'dev'

    # Initialize database
    db.init_app(app)

    return app
