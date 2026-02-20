import psycopg2

DATABASE_CONFIG = {
    "dbname": "stock_screener",
    "user": "postgres",
    "password": "aarya",
    "host": "localhost",
    "port": "5434"
}

def fix_schema():
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cur = conn.cursor()
        
        print("🔧 Fixing Database Schema (Adding updated_at)...")
        
        # Add the missing 'updated_at' column to analysis_target table
        # We use TIMESTAMPTZ (timestamp with time zone) for accuracy
        cur.execute("""
            ALTER TABLE analysis_target 
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Success! Column 'updated_at' added.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_schema()