import sqlite3

def check_sqlite_data(db_path):
    print(f"Checking data in: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        has_data = False
        for table in tables:
            table_name = table[0]
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"- Table '{table_name}' has {count} rows.")
                has_data = True
                
        if not has_data:
            print("The SQLite database is completely empty (no data in any tables).")
            
    except Exception as e:
        print(f"Error reading SQLite database: {e}")

if __name__ == "__main__":
    db1 = r"C:\Users\eladiong\Desktop\OJT Intern_v2\backend\db.sqlite3"
    check_sqlite_data(db1)
    
    print("\n")
    db2 = r"C:\Users\eladiong\Desktop\OJT Intern_v2\npc-reporting-system\backend\db.sqlite3"
    check_sqlite_data(db2)
