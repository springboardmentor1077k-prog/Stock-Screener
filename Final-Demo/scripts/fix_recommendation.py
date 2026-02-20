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
        
        print("🔧 Fixing Database Schema (Adding recommendation_key)...")
        
        # Add the missing 'recommendation_key' column to analysis_target table
        cur.execute("""
            ALTER TABLE analysis_target 
            ADD COLUMN IF NOT EXISTS recommendation_key VARCHAR(50);
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Success! Column 'recommendation_key' added.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_schema()