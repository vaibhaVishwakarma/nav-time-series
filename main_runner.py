from core.daily_calc import task
from SQL.setup_db import db, create_app
import psycopg2

def main():



    app = create_app()  # Create the Flask app instance


    status = True#task()
    if not status:
        print("[Error]: Task Failed")
        return
    
main()
