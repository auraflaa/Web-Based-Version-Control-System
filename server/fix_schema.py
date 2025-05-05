import pymysql

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
                # Check if repo_id column exists in files table
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.columns 
                    WHERE table_schema = 'codehub'
                    AND table_name = 'files'
                    AND column_name = 'repo_id';
                """)
                
                if cursor.fetchone()[0] == 0:
                    # Add repo_id column to files table
                    print("Adding repo_id column to files table...")
                    cursor.execute("""
                        ALTER TABLE files 
                        ADD COLUMN repo_id INT,
                        ADD FOREIGN KEY (repo_id) REFERENCES repositories(id);
                    """)
                    connection.commit()
                    print("Successfully added repo_id column to files table")
                else:
                    print("Column repo_id already exists in files table")

                # Check if repository_id column exists in branches table
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.columns 
                    WHERE table_schema = 'codehub'
                    AND table_name = 'branches'
                    AND column_name = 'repository_id';
                """)
                
                if cursor.fetchone()[0] == 0:
                    # Add repository_id column to branches table
                    print("Adding repository_id column to branches table...")
                    cursor.execute("""
                        ALTER TABLE branches 
                        ADD COLUMN repository_id INT,
                        ADD FOREIGN KEY (repository_id) REFERENCES repositories(id);
                    """)
                    connection.commit()
                    print("Successfully added repository_id column to branches table")
                else:
                    print("Column repository_id already exists in branches table")
                    
        finally:
            connection.close()
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    update_schema()