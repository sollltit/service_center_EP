import sqlite3
import sys

def create_dump(database_path, output_file):
    conn = sqlite3.connect(database_path)
    
    with open(output_file, 'w') as f:
        for line in conn.iterdump():
            f.write(f'{line}\n')
    
    conn.close()

create_dump('service_center.db', 'dump.sql')