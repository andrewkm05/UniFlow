# db.py

import sqlite3
from pathlib import Path

DB_FILE = Path("instance/uniflow.db")
DB_FILE.parent.mkdir(exist_ok = True)

class SQL:

    def __init__(self, path = DB_FILE):
        self.path = str(path)
    
    def execute(self, query, *params):
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        cur = con.execute(query, params)
        is_write = query.lstrip().split()[0].lower() in {
            "insert", "update", "delete", "delete", "create", "drop", "alter"
        }

        if is_write:
            con.commit()
            last_id = cur.lastrowid
            cur.close(); con.close()
            return last_id
    
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); con.close()
        return rows
    
    
