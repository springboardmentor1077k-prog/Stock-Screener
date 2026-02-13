from database import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("PRAGMA table_info(portfolio)")
print(cur.fetchall())

conn.close()
