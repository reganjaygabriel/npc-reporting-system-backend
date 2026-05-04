"""
Simple SQLite Database Viewer
Run this script to view tables and data in db.sqlite3
"""
import sqlite3
import sys

def view_database():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print("\n" + "="*60)
    print("DATABASE TABLES")
    print("="*60)
    for idx, (table,) in enumerate(tables, 1):
        print(f"{idx}. {table}")
    
    print("\n" + "="*60)
    print("TABLE DATA PREVIEW")
    print("="*60)
    
    # Show data from key tables
    key_tables = ['reports_plant', 'reports_unit', 'reports_generationreport', 'reports_uploadedfile']
    
    for table in key_tables:
        if any(table == t[0] for t in tables):
            print(f"\n--- {table} ---")
            try:
                cursor.execute(f"SELECT * FROM {table} LIMIT 5")
                rows = cursor.fetchall()
                
                # Get column names
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                
                print(f"Columns: {', '.join(columns)}")
                print(f"Total rows: ", end="")
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                print(cursor.fetchone()[0])
                
                if rows:
                    print("\nFirst 5 rows:")
                    for row in rows:
                        print(row)
                else:
                    print("(No data)")
            except Exception as e:
                print(f"Error reading table: {e}")
    
    conn.close()
    print("\n" + "="*60)
    print("Done!")
    print("="*60 + "\n")

if __name__ == "__main__":
    view_database()
