import os

# Shared configuration for database connection
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Points to analyst_demo/stocks.db
DB_PATH = os.path.join(BASE_DIR, '..', 'analyst_demo', 'stocks.db')
