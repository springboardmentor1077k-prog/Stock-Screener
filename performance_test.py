"""
Simple performance test for stock screener queries.
Tests common screening patterns and measures query performance.
"""
import time
import statistics
from backend.database import get_db
from backend.ai.compiler import compile_and_run

def time_query(func, *args, **kwargs):
    """Time a query function and return execution time."""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return end_time - start_time, result

def run_performance_tests():
    """Run performance tests on common screening queries."""
    print("=" * 50)
    print("STOCK SCREENER PERFORMANCE TEST")
    print("=" * 50)
    test_queries = [
        {
            "name": "PE Ratio Filter",
            "dsl": {
                "conditions": [
                    {"field": "pe_ratio", "operator": ">", "value": 15}
                ],
                "logic": "AND"
            }
        },
        {
            "name": "Multiple Filters",
            "dsl": {
                "conditions": [
                    {"field": "pe_ratio", "operator": ">", "value": 10},
                    {"field": "pe_ratio", "operator": "<", "value": 30},
                    {"field": "dividend_yield", "operator": ">", "value": 0.02}
                ],
                "logic": "AND"
            }
        },
        {
            "name": "Quarterly Profit Filter",
            "dsl": {
                "conditions": [
                    {"field": "pe_ratio", "operator": ">", "value": 5},
                    {"type": "quarterly", "field": "net_profit", "condition": "positive", "last_n": 4}
                ],
                "logic": "AND"
            }
        }
    ]
    
    results = []
    
    for test in test_queries:
        print(f"\nTesting: {test['name']}")
        print("-" * 30)
        times = []
        iterations = 3
        
        for i in range(iterations):
            try:
                query_time, result = time_query(compile_and_run, test['dsl'])
                times.append(query_time)
                result_count = len(result.get('stocks', []))
            except Exception as e:
                print(f"  Error: {str(e)}")
                times.append(float('inf'))
                result_count = 0
        
        valid_times = [t for t in times if t != float('inf')]
        avg_time = statistics.mean(valid_times) if valid_times else float('inf')
        
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Results: {result_count} stocks")
        
        results.append({
            'name': test['name'],
            'time': avg_time,
            'count': result_count
        })
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    for result in results:
        if result['time'] != float('inf'):
            print(f"{result['name']:<25} {result['time']:.4f}s ({result['count']} results)")
        else:
            print(f"{result['name']:<25} FAILED")
    
    return results

def check_indexes():
    """Check if performance indexes are created."""
    print("\n" + "=" * 50)
    print("INDEX STATUS CHECK")
    print("=" * 50)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        
        cursor.execute("""
            SELECT 
                TABLE_NAME,
                INDEX_NAME,
                COLUMN_NAME
            FROM information_schema.STATISTICS 
            WHERE TABLE_SCHEMA = 'stock_db' 
            AND INDEX_NAME LIKE 'idx_%'
            ORDER BY TABLE_NAME, INDEX_NAME
        """)
        
        indexes = cursor.fetchall()
        
        if indexes:
            print("Performance indexes found:")
            current_table = ""
            for idx in indexes:
                if idx['TABLE_NAME'] != current_table:
                    current_table = idx['TABLE_NAME']
                    print(f"\n{current_table}:")
                print(f"  {idx['INDEX_NAME']} on {idx['COLUMN_NAME']}")
        else:
            print("⚠️  No performance indexes found!")
            print("Run add_indexes.sql to create performance indexes")
        
    except Exception as e:
        print(f"Error checking indexes: {str(e)}")
    
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    print("Starting performance test...")
    check_indexes()
    run_performance_tests()
    