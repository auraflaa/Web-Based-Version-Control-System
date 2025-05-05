import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Pritam',
    'database': 'codehub'
}

def update_schema():
    try:
        # Connect to the database
        connection = pymysql.connect(**DB_CONFIG)
        
        try:
            with connection.cursor() as cursor:
                # Check if column exists in files table
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.columns 
                    WHERE table_schema = 'codehub'
                    AND table_name = 'files'
                    AND column_name = 'repo_id';
                """)
                
                if cursor.fetchone()[0] == 0:
                    # Add repo_id column
                    print("Adding repo_id column...")
                    cursor.execute("""
                        ALTER TABLE files 
                        ADD COLUMN repo_id INT,
                        ADD FOREIGN KEY (repo_id) REFERENCES repositories(id);
                    """)
                    connection.commit()
                    print("Successfully added repo_id column to files table")
                else:
                    print("Column repo_id already exists")
                
                # Rename repository_id column in branches table if it doesn't exist
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.columns 
                    WHERE table_schema = 'codehub'
                    AND table_name = 'branches'
                    AND column_name = 'repository_id';
                """)
                
                if cursor.fetchone()[0] == 0:
                    # First check if repo_id exists
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM information_schema.columns 
                        WHERE table_schema = 'codehub'
                        AND table_name = 'branches'
                        AND column_name = 'repo_id';
                    """)
                    
                    if cursor.fetchone()[0] > 0:
                        # Rename repo_id to repository_id
                        print("Renaming repo_id to repository_id...")
                        cursor.execute("""
                            ALTER TABLE branches 
                            CHANGE COLUMN repo_id repository_id INT,
                            DROP FOREIGN KEY IF EXISTS branches_ibfk_1,
                            ADD FOREIGN KEY (repository_id) REFERENCES repositories(id);
                        """)
                    else:
                        # Add repository_id column
                        print("Adding repository_id column...")
                        cursor.execute("""
                            ALTER TABLE branches 
                            ADD COLUMN repository_id INT,
                            ADD FOREIGN KEY (repository_id) REFERENCES repositories(id);
                        """)
                    connection.commit()
                    print("Successfully updated branches table schema")
                else:
                    print("Column repository_id already exists")
                    
        finally:
            connection.close()
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    update_schema()