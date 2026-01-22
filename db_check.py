import psycopg2

try:
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="Nethra@02",
        host="localhost",
        port=5432
    )
    print("✅ Python → PostgreSQL connection successful")
    conn.close()
except Exception as e:
    print("❌ Connection failed:", e)
