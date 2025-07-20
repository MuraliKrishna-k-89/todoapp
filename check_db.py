import sqlite3

# Connect to the database
conn = sqlite3.connect('todo.db')
cursor = conn.cursor()

# Get list of tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print('Tables in database:')
for table in tables:
    print(f"  - {table[0]}")

# Get schema for each table
for table in tables:
    table_name = table[0]
    print(f"\nSchema for {table_name}:")
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} {col[2]}")

conn.close()
