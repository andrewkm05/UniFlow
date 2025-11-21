# db.py
# SQLite3 database helper class for simplified query execution
# Used ChatGPT only for ideas on how to structure the class and methods but wrote all code myself

import sqlite3
from pathlib import Path

# Path to the SQLite database file (inside instance/ directory)
DB_FILE = Path("instance/uniflow.db")
DB_FILE.parent.mkdir(exist_ok = True)   # Ensure instance/ directory exists

class SQL:
    
    # Lightweight wrapper around sqlite3 to sipmlify query execution
    # Returns rows as dictionaries and auto-commits write queries
    def __init__(self, path = DB_FILE):
        self.path = str(path)
    
    def execute(self, query, *params):

        # Execute a SQL query with optional parameters
        # Automatically commits write queries and returns results as list of dicts
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        cur = con.execute(query, params)

        # Determine if the query is a write operation
        is_write = query.lstrip().split()[0].lower() in {
            "insert", "update", "delete", "delete", "create", "drop", "alter"
        }

        if is_write:
            con.commit()
            last_id = cur.lastrowid
            cur.close(); con.close()
            return last_id

        # For read queries, fetch all rows as list of dicts
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); con.close()
        return rows
    
    
