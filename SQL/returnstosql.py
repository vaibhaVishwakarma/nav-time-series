import pandas as pd
import os
import logging
import sys
from sqlalchemy import text

from SQL.setup_db import db, create_app
from SQL.models import FundReturns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_existing_isins():
    """Fetches all valid ISINs from the mf_fund table."""
    try:
        result = db.session.execute(text("SELECT isin FROM mf_fund"))
        return {row[0] for row in result}
    except Exception as e:
        logger.error(f"Error fetching ISINs from mf_fund: {e}")
        return set()


def import_returns_data(df, existing_isins=None ,clear_existing=False):
        """
        Import fund returns data from DataFrame using bulk upsert strategy
        
        Args:
            df: DataFrame containing returns data
            existing_isins (set): Set of ISINs that exist in the database for validation
            clear_existing (bool): Whether to clear existing data before import
            
        Returns:
            dict: Statistics about the import operation
        """
        logger.info(f"Importing returns data with {len(df)} records")

        try:
            # Clean data
            df = df.dropna(subset=['ISIN'])

            if clear_existing and len(df) > 0:
                # Get list of ISINs to clear
                isins = df['ISIN'].unique().tolist()

                # Delete existing returns for these ISINs
                FundReturns.query.filter(FundReturns.isin.in_(isins)).delete(
                    synchronize_session=False)

                db.session.commit()
                logger.info(
                    f"Cleared existing returns data for {len(isins)} ISINs")

            # Track statistics
            stats = {
                'returns_created': 0,
                'returns_updated': 0,
                'funds_not_found': 0,
                'total_rows_processed': len(df)
            }

            # Get all valid fund ISINs for validation
            valid_fund_isins = existing_isins

            # Prepare records for bulk upsert
            returns_records = []

            for _, row in df.iterrows():
                isin = str(row['ISIN']).strip()

                if not isin or isin.lower() == 'nan':
                    continue

                # Skip if fund doesn't exist
                if isin not in valid_fund_isins:
                    logger.warning(
                        f"Skipping returns for {isin}: Fund not found in database"
                    )
                    stats['funds_not_found'] += 1
                    continue

                # Create returns record
                returns_record = {
                    'isin':
                    isin,
                    'return_1m':
                    float(row.get('return_1w', 0)),

                    'return_3m':
                    float(row.get('return_3m', 0)),

                    'return_6m':
                    float(row.get('return_6m', 0)),

                    'return_1y':
                    float(row.get('return_1y', 0)),

                    'return_3y':
                    float(row.get('return_3y', 0)),

                    'return_5y':
                    float(row.get('return_5y', 0)),

                    'return_ytd':
                    float(row.get('return_ytd', 0)),

                    'return_3y_cagr':
                    float(row.get('return_3y_cagr', 0)),

                    'return_5y_cagr':
                    float(row.get('return_5y_cagr', 0)),

                    'return_10y_cagr':
                    float(row.get('return_10y_cagr', 0)),

                    'return_since_inception':
                    float(row.get('return_since_inception', 0)),

                    'return_since_inception_cagr':
                    float(row.get('return_since_inception_cagr', 0)),
                    

                }
                returns_records.append(returns_record)

            # Bulk upsert returns using PostgreSQL
            if returns_records:
                from sqlalchemy.dialects.postgresql import insert 

                stmt = insert(FundReturns.__table__).values(returns_records)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['isin'],
                    set_=dict(return_1m=stmt.excluded.return_1m,
                              return_3m=stmt.excluded.return_3m,
                              return_6m=stmt.excluded.return_6m,
                              return_ytd=stmt.excluded.return_ytd,
                              
                              return_1y=stmt.excluded.return_1y,
                              return_3y=stmt.excluded.return_3y,
                              return_5y=stmt.excluded.return_5y,

                              return_3y_cagr=stmt.excluded.return_3y_cagr,
                              return_5y_cagr=stmt.excluded.return_5y_cagr,
                              return_10y_cagr=stmt.excluded.return_10y_cagr,

                              return_since_inception=stmt.excluded.return_since_inception,
                              return_since_inception_cagr=stmt.excluded.return_since_inception_cagr))
                
                db.session.execute(stmt)
                stats['returns_created'] = len(returns_records)

            # Commit all changes
            db.session.commit()
            logger.info(f"Returns import completed: {stats}")

            return stats

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error importing returns data: {e}")
            raise


def upsert(returns_directory="daily_returns"):
    isis_in_db=pd.read_csv(r"c:\Users\vaibh\Downloads\studio_results_20250708_1755.csv")["isin"].to_list()
    
    DELTA_DAYS = int(os.environ.get("DELTA_DAYS"))
    returnsfile = os.path.join(returns_directory,f"returns_as_on {pd.Timestamp.today().date() - pd.Timedelta(days=DELTA_DAYS)}.csv")
    
    df_returns= pd.read_csv(returnsfile, sep=";")

    # Rename the ISIN column
    df_returns.rename(columns={'ISIN Div Payout/ISIN Growth': 'ISIN'}, inplace=True)

    # Drop the 'ISIN Div Reinvestment' column   
    df_returns.drop(columns=['ISIN Div Reinvestment', 'Scheme Code', 'Scheme Name'], inplace=True)

    # Check for duplicates based on ISIN
    duplicate_isins = df_returns[df_returns.duplicated(subset='ISIN', keep=False)]

    if not duplicate_isins.empty:
        print("Found duplicate ISINs:")
        print(duplicate_isins['ISIN'].unique())

    # Drop duplicates, keeping the first occurrence
        df_returns = df_returns.drop_duplicates(subset='ISIN', keep='first')
        print(f"Removed duplicates. New shape: {df_returns.shape}")
    else:
        print("No duplicate ISINs found.")


    stats = import_returns_data(df_returns, existing_isins=isis_in_db, clear_existing=False)
    print(stats)

    return True


if __name__ == "__main__":

    app = create_app()  # Create the Flask app instance
    with app.app_context():  # Push application context 
        upsert()

  


